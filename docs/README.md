# ⚡ SparkHire AI — Intelligent Vocal Interview Platform

> **Final Year Engineering Project (PFA)** · Data Engineering & Decisional Systems · ENET'Com Sfax · 2025–2026  
> **Author:** Zeineb Ghrab · `zeineb.ghrab@enetcom.u-sfax.tn`  
> **Stack:** FastAPI · MongoDB · Whisper · Llama 3.2 · MediaPipe · HSEmotion · PySide6

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Technology Stack](#4-technology-stack)
5. [Prerequisites & System Requirements](#5-prerequisites--system-requirements)
6. [Installation Guide](#6-installation-guide)
7. [Configuration Reference](#7-configuration-reference)
8. [Backend Modules](#8-backend-modules)
   - 8.1 [Entry Point — `main.py`](#81-entry-point--mainpy)
   - 8.2 [Configuration — `config.py`](#82-configuration--configpy)
   - 8.3 [Database — `database.py`](#83-database--databasepy)
   - 8.4 [Auth Module](#84-auth-module)
   - 8.5 [Candidates Module](#85-candidates-module)
   - 8.6 [Interviews Module](#86-interviews-module)
   - 8.7 [Evaluation Module](#87-evaluation-module)
   - 8.8 [Analytics Module](#88-analytics-module)
   - 8.9 [Notifications Module](#89-notifications-module)
   - 8.10 [Export Module](#810-export-module)
   - 8.11 [Media Module](#811-media-module)
   - 8.12 [Middlewares](#812-middlewares)
9. [AI Services](#9-ai-services)
   - 9.1 [ASR Service — Whisper](#91-asr-service--whisper)
   - 9.2 [TTS Service — Edge-TTS + gTTS](#92-tts-service--edge-tts--gtts)
   - 9.3 [LLM Service — Ollama + Llama 3.2](#93-llm-service--ollama--llama-32)
   - 9.4 [Facial Analysis Service](#94-facial-analysis-service)
   - 9.5 [Avatar Service](#95-avatar-service)
10. [WebSocket Protocol](#10-websocket-protocol)
11. [Desktop Client (PySide6)](#11-desktop-client-pyside6)
    - 11.1 [Core Modules](#111-core-modules)
    - 11.2 [UI Components](#112-ui-components)
    - 11.3 [Design System](#113-design-system)
12. [Data Models & MongoDB Schema](#12-data-models--mongodb-schema)
13. [API Reference](#13-api-reference)
14. [Scoring & Decision Logic](#14-scoring--decision-logic)
15. [Privacy & Security Design](#15-privacy--security-design)
16. [Performance Benchmarks](#16-performance-benchmarks)
17. [Troubleshooting](#17-troubleshooting)
18. [Academic Context](#18-academic-context)

---

## 1. Project Overview

SparkHire AI is a voice-based AI recruitment interview system that automates first-round candidate screening. A candidate connects through the desktop client, answers questions delivered by a text-to-speech avatar, and the platform evaluates responses using a locally hosted large language model (Llama 3.2 via Ollama).

In parallel, a computer-vision pipeline analyzes the candidate's facial behavior — recording metrics such as eye contact, head stability, dominant emotion, and composite behavioral scores. All behavioral metrics are stored exclusively on the recruiter's side and are **never disclosed to the candidate** (privacy by design).

### Core Capabilities

| Capability | Description |
|---|---|
| Voice interview | Trilingual (Arabic / French / English) automated interview with TTS avatar |
| ASR transcription | faster-whisper (GPU), ~1–3 s per answer |
| LLM evaluation | Ollama + Llama 3.2, strict 0–10 scale with follow-up generation |
| Facial analysis | MediaPipe FaceMesh (478 landmarks) + HSEmotion EfficientNet-B0 (~82%) |
| Smart follow-ups | Automatically triggered when answer score < 8 |
| Weighted scoring | Per-question weights configurable by the recruiter |
| Privacy by design | Behavioral scores never sent to the candidate |
| HR dashboard | Analytics, notifications, CSV/JSON export |
| Reconnection | Resumes at the current question if connection drops mid-interview |
| Scheduling | 30-minute late-access window after scheduled start time |

---

## 2. System Architecture

### High-Level Data Pipeline

```
+------------------------------------------------------------------+
|                     PySide6 Desktop Client                        |
|                                                                    |
|  +--------------+  +----------------+  +----------------------+   |
|  | AudioRecorder|  |VideoFrameCollec|  |   WebSocketClient    |   |
|  |  (PyAudio)   |  |tor (OpenCV 2fps|  | (websockets+QThread) |   |
|  +------+-------+  +-------+--------+  +-----------+----------+   |
|         |  PCM chunks      |  JPEG frames           |  JSON msgs   |
+---------|------------------|-----------------------|---------------+
          |                  |                       |
          +------------------+-----------------------+
                                   | WebSocket (ws://)
                       +-----------v-----------+
                       |    FastAPI Backend     |
                       |                       |
                       |  +------------------+ |
                       |  | InterviewHandler | |
                       |  +--------+---------+ |
                       |           |           |
                       |  asyncio.gather()     |
                       |  +--------+--------+  |
                       |  v                 v  |
                       | Whisper ASR  FacialAnalysis|
                       | (ThreadPool) (ThreadPool)  |
                       |        |          |        |
                       |        +----+-----+        |
                       |             v              |
                       |       Llama 3.2 LLM        |
                       |             |              |
                       |             v              |
                       |          MongoDB           |
                       +-----------------------+----+
```

### Score & Decision Thresholds

```
               Weighted Average Score /10
                          |
        +-----------------+-----------------+
        |                 |                 |
    score < 5.0    5.0 <= score < 7.0   score >= 7.0
        |                 |                 |
   REJECTED           PENDING           ACCEPTED
   #EF4444            #F59E0B           #10B981
```

### Follow-Up Logic

```
LLM evaluates answer
         |
    score < 8 ?
    +----+----+
   YES       NO
    |         |
  Generate   Next question
  follow-up
    |
  Candidate answers follow-up
    |
  LLM evaluates BOTH answers combined
    |
  Final score replaces initial score
```

---

## 3. Repository Structure

```
sparkhire-ai/
|
+-- README.md                          <- This file
+-- requirements.txt                   <- Backend Python dependencies
+-- .env.example                       <- Environment template
+-- .gitignore
|
+-- backend/                           <- FastAPI server
|   +-- main.py                        <- App entry point + service lifespan
|   +-- config.py                      <- Pydantic settings (from .env)
|   +-- database.py                    <- MongoDB connection (PyMongo)
|   +-- middlewares.py                 <- Logging, error handling, rate limiting
|   |
|   +-- auth/                          <- JWT authentication for recruiters
|   |   +-- models.py                  <- Recruiter, Token Pydantic models
|   |   +-- routes.py                  <- POST /auth/login, GET /auth/me
|   |   +-- security.py               <- JWT creation/verification, bcrypt
|   |
|   +-- candidates/                    <- Candidate CRUD
|   |   +-- models.py                  <- Candidate, Education, Experience...
|   |   +-- crud.py                    <- CandidateCRUD static methods
|   |   +-- routes.py                  <- REST endpoints
|   |
|   +-- interviews/                    <- Sessions and job positions
|   |   +-- models.py                  <- Question, JobPosition, Answer, Session...
|   |   +-- crud.py                    <- JobPositionCRUD, InterviewSessionCRUD
|   |   +-- routes.py                  <- Scheduling, status updates, answers
|   |
|   +-- evaluation/                    <- LLM evaluation pipeline
|   |   +-- models.py                  <- AnswerEvaluation, GlobalEvaluation
|   |   +-- service.py                 <- EvaluationService (orchestration)
|   |   +-- routes.py                  <- Trigger, retrieve, delete evaluations
|   |
|   +-- services/                      <- AI services
|   |   +-- asr_service.py             <- Whisper + Vosk fallback
|   |   +-- tts_service.py             <- TTS facade + cache
|   |   +-- edge_tts_engine.py         <- Edge-TTS engine with retry
|   |   +-- llm_service.py             <- Ollama LLM evaluation & summarization
|   |   +-- facial_analysis_service.py <- MediaPipe + HSEmotion + DeepFace
|   |   +-- avatar_service.py          <- Static video avatar provider
|   |
|   +-- websocket/                     <- Real-time interview channel
|   |   +-- connection_manager.py      <- Active connection registry
|   |   +-- interview_handler.py       <- Business logic + audio/video routing
|   |
|   +-- analytics/                     <- Dashboard statistics
|   |   +-- models.py                  <- Stats Pydantic models
|   |   +-- routes.py                  <- KPI aggregation endpoints
|   |
|   +-- notifications/                 <- Recruiter notifications
|   |   +-- models.py
|   |   +-- routes.py
|   |   +-- service.py
|   |
|   +-- export/                        <- CSV & JSON export
|   |   +-- routes.py
|   |
|   +-- media/                         <- File upload/download
|   |   +-- models.py
|   |   +-- routes.py
|   |
|   +-- utils/
|       +-- audio_utils.py             <- WAV encode/decode helpers
|
+-- client/                            <- PySide6 desktop application
|   +-- main.py                        <- QApplication entry point
|   +-- config.py                      <- Client-side settings
|   +-- requirements.txt               <- Client Python dependencies
|   |
|   +-- core/
|   |   +-- models.py                  <- Lightweight dataclasses
|   |   +-- audio_recorder.py          <- PyAudio PCM recorder
|   |   +-- video_recorder.py          <- OpenCV + QTimer frame collector
|   |   +-- websocket_client.py        <- Thread-safe WebSocket wrapper
|   |
|   +-- ui/
|       +-- stark_theme.py             <- Design tokens (T) + stylesheet helpers
|       +-- icons.py                   <- SVG Lucide icons + logos
|       +-- main_window.py             <- Main window + interview flow logic
|       +-- interview_widget.py        <- Right-panel interview controls
|       +-- video_player_widget.py     <- Avatar video player
|       +-- camera_preview_widget.py  <- PiP webcam overlay + real-time analysis
|
+-- scripts/
|   +-- create_admin.py                <- Bootstrap recruiter account
|   +-- download_whisper.py            <- Download Whisper model
|   +-- seed_job_positions.py          <- Seed example positions
|
+-- models/                            <- Downloaded AI model weights (gitignored)
+-- uploads/                           <- Recorded audio + TTS cache (gitignored)
+-- assets/
|   +-- videos/                        <- HR avatar videos
+-- docs/                              <- Architecture diagrams (PNG)
```

---

## 4. Technology Stack

### Backend

| Layer | Technology | Version | Role |
|---|---|---|---|
| Web framework | FastAPI + Uvicorn | 0.115 / 0.32 | REST API + WebSocket server |
| Database | MongoDB + Motor | 7.x / 3.5 | Persistent storage |
| ORM layer | PyMongo (sync) | 4.10 | Synchronous CRUD operations |
| Auth | python-jose + bcrypt | 3.3 / 4.2 | JWT tokens + password hashing |
| ASR | faster-whisper | 1.0.3 | GPU-accelerated speech recognition |
| TTS primary | Edge-TTS | 7.2.7 | Microsoft neural TTS |
| TTS fallback | gTTS | 2.5.3 | Google TTS fallback |
| LLM | Ollama + Llama 3.2 | latest | Local large language model |
| Facial landmarks | MediaPipe | 0.10.14 | 478-point FaceMesh + iris tracking |
| Facial emotions | HSEmotion EfficientNet-B0 | latest | ~82% emotion recognition |
| Facial fallback | DeepFace VGG | 0.0.99 | ~73% emotion recognition |
| Audio conversion | pydub + FFmpeg | — | MP3 to WAV conversion |
| HTTP client | httpx | 0.27 | Async HTTP calls to Ollama |

### Client

| Layer | Technology | Version | Role |
|---|---|---|---|
| GUI framework | PySide6 (Qt 6) | 6.7 | Desktop application |
| WebSocket | websockets | 13.0.1 | Real-time server communication |
| Audio playback | pygame.mixer | 2.6 | WAV audio playback |
| Audio capture | PyAudio | 0.2.14 | PCM microphone recording |
| Video capture | OpenCV | 4.10 | Webcam frame capture |
| Audio processing | pydub | 0.25.1 | Audio format conversion |

---

## 5. Prerequisites & System Requirements

### Mandatory Software

| Software | Version | Purpose |
|---|---|---|
| Python | 3.10 or 3.11 | Main runtime (3.12 not supported by some dependencies) |
| MongoDB | 7.x Community | Data persistence |
| Ollama | latest | Local LLM server |
| FFmpeg | 6.0+ | Audio conversion (gTTS MP3 to WAV) |
| CUDA Toolkit | 11.x or 12.x | GPU acceleration (optional but recommended) |

> **Windows only:** Visual Studio C++ Build Tools 2022 are required to compile PyAudio from source.

### Hardware Recommendations

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB | 16 GB |
| GPU VRAM | — | 6 GB (RTX 3060 or better) |
| Disk (models) | 3 GB | 8 GB (Whisper medium + Llama 3.2) |
| Webcam | — | 720p or higher |

---

## 6. Installation Guide

### Step 1 — Clone the repository

```bash
git clone https://github.com/ZeinebGhrab/sparkhire-ai.git
cd sparkhire-ai
```

### Step 2 — Create and activate virtual environment

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### Step 3 — Install PyTorch (GPU or CPU)

```bash
# CUDA 12.x (recommended for RTX 40xx series)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.x
pip install torch --index-url https://download.pytorch.org/whl/cu118

# CPU only
pip install torch
```

### Step 4 — Install backend dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Install client dependencies

```bash
pip install -r client/requirements.txt
```

### Step 6 — Install facial analysis stack (mandatory order)

The installation order matters due to protobuf version conflicts on Windows Python 3.11.

```bash
pip install timm==0.9.2
pip install efficientnet_pytorch
pip install hsemotion
pip install mediapipe==0.10.14
pip install "protobuf>=4.25.3,<5.0.0"
```

> **Why this order?** `mediapipe==0.10.14` requires `protobuf>=4.25.3,<5.0.0`. Installing it after `timm` and `hsemotion` prevents version conflicts with TensorFlow's protobuf dependency (see Section 8.1 for the technical explanation).

### Step 7 — Configure environment

```bash
cp .env.example .env
# Edit .env with your settings (see Section 7 for full reference)
```

### Step 8 — Download Whisper model

```bash
python scripts/download_whisper.py medium
```

Available sizes: `tiny` (75 MB) · `base` (145 MB) · `small` (483 MB) · `medium` (1.5 GB, recommended) · `large-v3` (3.1 GB)

### Step 9 — Start Ollama and pull the model

```bash
# Terminal 1
ollama serve

# Terminal 2
ollama pull llama3.2
```

### Step 10 — Initialize database

```bash
# Create the default recruiter account (email: rh@stark.tn, password: admin123)
python scripts/create_admin.py

# Seed example job positions (optional)
python scripts/seed_job_positions.py
```

### Step 11 — Launch the application

```bash
# Terminal 1: Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start desktop client
python -m client.main
```

Open the interactive API documentation at: `http://localhost:8000/docs`

---

## 7. Configuration Reference

All configuration is managed via a `.env` file in the project root. The `Settings` class in `backend/config.py` uses Pydantic-Settings to load and validate these values.

### Full `.env` Reference

```env
# -- MongoDB ---------------------------------------------------------------
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sparkhire_ai

# -- Security --------------------------------------------------------------
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your-32-byte-hex-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60

# -- ASR (Whisper) ---------------------------------------------------------
ASR_ENGINE=faster-whisper          # faster-whisper | vosk
WHISPER_MODEL_SIZE=medium          # tiny | base | small | medium | large-v3
WHISPER_DEVICE=cuda                # cuda | cpu
WHISPER_COMPUTE_TYPE=float16       # float16 (GPU) | int8 (CPU)

# -- TTS -------------------------------------------------------------------
TTS_ENGINE=edge-tts                # edge-tts | gtts
TTS_LANGUAGE=fr                    # ar | fr | en

# -- LLM -------------------------------------------------------------------
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120.0               # Increase for slower hardware

# -- Facial Analysis -------------------------------------------------------
FACIAL_ANALYSIS_ENABLED=true
FACIAL_CAPTURE_FPS=2.0             # Frames per second from client camera
FACIAL_DEVICE=cuda                 # cuda | cpu
FACIAL_DETECTOR_BACKEND=retinaface # retinaface | mtcnn | opencv | mediapipe

# -- File Paths ------------------------------------------------------------
UPLOAD_DIR=./uploads

# -- Avatar ----------------------------------------------------------------
AVATAR_PROVIDER=simple             # simple | did

# -- Windows fix -----------------------------------------------------------
KMP_DUPLICATE_LIB_OK=TRUE
```

### CPU-Only Configuration

```env
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
FACIAL_DEVICE=cpu
OLLAMA_TIMEOUT=180.0
```

---

## 8. Backend Modules

### 8.1 Entry Point — `main.py`

The application entry point performs several critical tasks in a precise order that **must not be changed**.

#### MediaPipe Pre-loading (Critical on Windows)

On Windows with Python 3.11, TensorFlow (required by DeepFace) loads protobuf >= 5 during import, which breaks MediaPipe's compatibility with protobuf 4.x. The solution involves two steps executed before any other imports:

```python
# Step 1: Inject stub modules for mediapipe.tasks BEFORE any TF import
for _mod_name in ["mediapipe.tasks", "mediapipe.tasks.python", ...]:
    sys.modules[_mod_name] = types.ModuleType(_mod_name)

# Step 2: Preload mediapipe.python.solutions.face_mesh NOW (before TF loads)
import mediapipe as _mp_preload
import mediapipe.python.solutions.face_mesh as _fm_preload
```

This technique ensures MediaPipe loads its C++ extensions against protobuf 4, preventing the `FieldDescriptor has no attribute 'label'` error when DeepFace later imports TensorFlow.

#### Lifespan Event Handler

The `lifespan` async context manager initializes all AI services at startup with warm-up calls to avoid cold-start latency during the first interview:

1. **ASR (Whisper)** — model loaded into GPU/CPU memory
2. **TTS (Edge-TTS)** — engine initialized and voice configuration verified
3. **Avatar** — video file paths verified
4. **Facial Analysis** — MediaPipe FaceMesh initialized; DeepFace/HSEmotion warm-up loads CNN weights to prevent a 15–20 s delay on the first question
5. **LLM (Ollama)** — availability check via `/api/tags`

#### Special Import Order in `facial_analysis_service.py`

The same MediaPipe pre-loading pattern is replicated in `facial_analysis_service.py` to ensure it works even when imported as a standalone module (e.g., in tests or the WebSocket handler's direct import):

```python
# At the top of facial_analysis_service.py and interview_handler.py:
for _m in ["mediapipe.tasks", "mediapipe.tasks.python", ...]:
    if _m not in sys.modules:
        sys.modules[_m] = types.ModuleType(_m)
```

#### Key Routes

| Route | Description |
|---|---|
| `GET /` | API info card |
| `GET /health` | Full health check for all services |
| `GET /api/info` | Pipeline summary and endpoint map |
| `WS /ws/interview/{session_id}` | Main interview WebSocket |

---

### 8.2 Configuration — `config.py`

Uses Pydantic-Settings with `@lru_cache` for singleton access throughout the application:

```python
from backend.config import settings
print(settings.WHISPER_MODEL_SIZE)   # "medium"
print(settings.UPLOAD_DIR)           # Path object, resolved from project root
```

Key design choices:
- `extra = "ignore"` — silently ignores unknown `.env` keys (e.g., `KMP_DUPLICATE_LIB_OK`)
- `case_sensitive = True` — environment key names must match exactly
- `Path` fields automatically resolve paths relative to the project root
- `@lru_cache` ensures the settings object is created only once per process

---

### 8.3 Database — `database.py`

Provides a synchronous PyMongo connection exposed as a global `db` object:

```python
from backend.database import db

# Direct collection access anywhere in the backend
sessions = list(db.interview_sessions.find({"status": "completed"}))
db.candidates.insert_one({...})
db.evaluations.update_one({"session_id": sid}, {"$set": doc}, upsert=True)
```

**Why synchronous PyMongo instead of Motor (async)?**  
Most backend CRUD operations are simple enough that the overhead of async MongoDB is unnecessary. The WebSocket handler and evaluation service do use `asyncio.gather()` for parallelism, but the underlying MongoDB calls are fast enough in a thread-pool context. Motor remains a dependency for future migration.

**Collections:**

| Collection | Purpose |
|---|---|
| `recruiters` | Recruiter accounts (email + bcrypt hash) |
| `candidates` | Full candidate profiles |
| `job_positions` | Job offers with question sets and weights |
| `interview_sessions` | Sessions with embedded answers and evaluations |
| `evaluations` | Global LLM HR reports (GlobalEvaluation documents) |
| `notifications` | Recruiter real-time notifications |

---

### 8.4 Auth Module

**Files:** `auth/models.py` · `auth/routes.py` · `auth/security.py`

#### Authentication Flow

```
POST /auth/login
  Body: form-encoded {username: email, password: plain_text}
    |
    +-- Lookup recruiter by email in db.recruiters
    +-- bcrypt.checkpw(plain_text, stored_binary_hash)
    +-- Create JWT: {sub: email, exp: now + 60min}
    +-- Return: {access_token: "...", token_type: "bearer"}

GET /protected-endpoint
  Header: Authorization: Bearer <token>
    |
    +-- OAuth2PasswordBearer extracts token from header
    +-- jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    +-- Returns recruiter email string (used as identity throughout)
```

#### Security Implementation Details

- **Password hashing:** bcrypt with auto-generated salt; the binary hash is stored directly in MongoDB (not as a string)
- **Tokens:** HS256 JWT with configurable expiry (default 60 minutes)
- **Dependency injection:** `get_current_recruiter` is a FastAPI dependency used via `Depends()` on every protected route — returns the recruiter's email string
- **Login endpoint:** Uses `OAuth2PasswordRequestForm` for standards-compliant form-body submission

#### Models

```python
class Recruiter(BaseModel):
    email: EmailStr
    password_hash: bytes      # bcrypt binary hash stored as BSON Binary

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

---

### 8.5 Candidates Module

**Files:** `candidates/models.py` · `candidates/crud.py` · `candidates/routes.py`

#### Data Model Hierarchy

A `Candidate` document is structured and rich. All list fields require at least one item (enforced via `Field(min_length=1)`):

```
Candidate
+-- first_name, last_name
+-- contact (Contact)
|   +-- email (EmailStr), phone
|   +-- linkedin, github, portfolio
+-- technical_skills: List[TechnicalSkill]   (min 1)
|   +-- name, level (Beginner/Intermediate/Advanced/Expert)
|   +-- years_experience
+-- experiences: List[Experience]             (min 1)
|   +-- title, company, location
|   +-- start_date, end_date, currently_working
|   +-- description, technologies: List[str]
+-- education: List[Education]                (min 1)
|   +-- degree, field, institution
|   +-- start_date, end_date, currently_studying
+-- languages: List[Language]                 (min 1)
|   +-- name, level (A1 to C2 / Native)
+-- soft_skills: List[SoftSkill]              (min 1)
+-- certifications: List[Certification]       (min 1)
|   +-- name, issuer, issue_date, expiry_date
|   +-- credential_id, credential_url
+-- cv_raw: Optional[str]                     <- raw CV text for future embedding
+-- consents: List[Consent]                   <- GDPR tracking
|   +-- type, granted, timestamp, ip_address
+-- embeddings: Optional[List[float]]         <- reserved for future vector search
```

#### CRUD Operations (`CandidateCRUD`)

| Method | Operation | Notes |
|---|---|---|
| `create(CandidateCreate)` | Insert document | Auto-sets `created_at`, `updated_at` |
| `get_all(skip, limit)` | Paginated list | Sorted by `created_at` descending |
| `get_by_id(id)` | Single lookup | Validates ObjectId, raises 400/404 |
| `search_by_email(email)` | Find by contact email | Returns `None` if not found |
| `search_by_skills(skills, min_match)` | Skill-based search | Sorted by match count descending |
| `update(id, CandidateUpdate)` | Partial update | Only provided fields updated via `$set` |
| `delete(id)` | Hard delete | Returns bool |
| `add_consent(id, consent)` | Append consent | Uses MongoDB `$push` operator |

---

### 8.6 Interviews Module

**Files:** `interviews/models.py` · `interviews/crud.py` · `interviews/routes.py`

#### Job Positions and Questions

A `JobPosition` contains a list of `Question` objects. Each question is trilingual and carries a `weight` parameter used in the weighted average calculation:

```python
class Question(BaseModel):
    order: int
    question_ar: str                  # Arabic version (mandatory)
    question_en: str                  # English version (mandatory)
    question_fr: str = ""             # French version (optional, falls back to EN)
    max_duration_seconds: int = 90    # Recording time limit per question
    evaluation_criteria: List[str] = []
    weight: float = 1.0               # Range: 0.1 to 10.0
```

The `get_text(language)` method handles language fallback (FR falls back to EN if empty).

#### Interview Session Lifecycle

```
PENDING ────────────────────────► IN_PROGRESS ───────────────► COMPLETED
   |        (candidate connects)        |                          |
   |                                    |                          v
   |                                    |                 Notification sent to
   |                                    |                 recruiter automatically
   |                                    |
   +──────────────────────────────────► CANCELLED
              (timeout / voluntary end)
```

**Session expiry model:**
- Without scheduling: `expires_at = created_at + 30 minutes`
- With scheduling: `expires_at = scheduled_at + 30 minutes` (late access window)

**`validate_session_access(session_id)` returns `(session, is_valid, error_message)`:**
1. Session must exist and not be `cancelled`
2. If `scheduled_at` is set: current time must be between `scheduled_at` and `late_access_deadline`
3. Without scheduling: current time must be before `expires_at`

**Automatic notification on completion:**  
`update_status("completed")` calls `_send_completion_notification()` which inserts a notification document for the `created_by` recruiter (falls back to all recruiters if `created_by` is absent). This is all synchronous and does not require any async infrastructure.

#### Embedded Answer + Evaluation Document

The `answers` array within each session document embeds evaluation data directly:

```python
class AnswerEvaluationData(BaseModel):
    score: float                         # 0.0 to 10.0
    verdict: str                         # Excellent / Very Good / ...
    feedback: str                        # Detailed LLM comment
    strengths: List[str]
    improvements: List[str]
    llm_model: str                       # e.g. "llama3.2"
    evaluated_at: Optional[datetime]
    weight: float                        # Copied from Question.weight at eval time
    had_followup: bool = False
    initial_score: Optional[float]       # Score before follow-up (if any)
    initial_verdict: Optional[str]
    followup_question: Optional[str]
    followup_transcript: Optional[str]
    facial_analysis: Optional[FacialAnalysisData]   # MediaPipe + HSEmotion metrics
```

Embedding evaluation data inside the answer document (rather than a separate collection) enables fast retrieval of complete session data in a single MongoDB query.

---

### 8.7 Evaluation Module

**Files:** `evaluation/models.py` · `evaluation/service.py` · `evaluation/routes.py`

#### Full Evaluation Pipeline

```
EvaluationService.evaluate_full_session(session_id, language)
|
+-- 1. Load session, position, candidate from MongoDB
|
+-- 2. asyncio.gather() -- evaluate each answer in parallel
|      +-- evaluate_single_answer(question, transcript, weight, ...)
|             +-- llm.evaluate_answer(question, transcript, language)
|             +-- Re-transcribe via Whisper if transcript is empty
|
+-- 3. Inject facial metrics from DB answers[n].evaluation.facial_analysis
|      +-- Build FacialSummary objects for each answer
|
+-- 4. Compute GlobalFacialSummary
|      +-- avg_confidence, avg_stress, avg_engagement, avg_eye_contact
|      +-- dominant_emotion: most frequent across all answers
|
+-- 5. Weighted average
|      Σ(score_i * weight_i) / Σ(weight_i)
|
+-- 6. LLM global summary
|      generate_global_summary() -> recommendation, decision_reason,
|                                    key_strengths, key_improvements, summary
|
+-- 7. _fill_missing_fields() -- deterministic fallback
|      Ensures all fields populated even if LLM returned empty/malformed JSON
|
+-- 8. Persist
       evaluations collection (upsert GlobalEvaluation)
       interview_sessions (denormalized: score + decision + recommendation)
```

#### Decision Thresholds

```python
DECISION_THRESHOLD_ACCEPT = 7.0   # score >= 7.0 -> accepted
DECISION_THRESHOLD_REJECT = 5.0   # score <  5.0 -> rejected
                                  # 5.0 <= score < 7.0 -> pending
```

#### Completeness Guarantee (`_fill_missing_fields`)

If the LLM returns empty or malformed JSON (timeout, network error), deterministic values are generated:
- `recommendation`: derived from the average score using threshold rules
- `decision_reason`: formatted string "Weighted average X/10 across N question(s)"
- `key_strengths`: aggregated from individual answer evaluations (deduplicated, max 4)
- `key_improvements`: same approach (max 4)
- `summary`: built from per-question scores with weights

This guarantees that every evaluation has a complete HR report regardless of LLM reliability.

#### Score Normalization for Display

The `GlobalEvaluation` model provides a computed property:

```python
@property
def score_100(self) -> float:
    """Normalize /10 to /100 for graphical display."""
    return round(self.average_score * 10, 1)
```

---

### 8.8 Analytics Module

**Files:** `analytics/models.py` · `analytics/routes.py`

Provides aggregated statistics for the HR dashboard. All endpoints require JWT authentication and perform MongoDB aggregation pipelines in real time.

#### Available Endpoints

| Endpoint | Key Metrics |
|---|---|
| `GET /analytics/dashboard?days=30` | All KPIs combined in a single call |
| `GET /analytics/candidates` | Total candidates, recent signups, top 10 skills |
| `GET /analytics/interviews` | By status, average duration, completion rate, average LLM score |
| `GET /analytics/system` | Recruiter count, active sessions, disk storage used |
| `GET /analytics/scheduling` | This week, by day/position/language, upcoming 7 days |
| `GET /analytics/scores` | Accepted/rejected KPIs with month-over-month change, 6-month trend |
| `GET /analytics/positions/scores?position_id=` | Per-position score breakdown |

#### Score Buckets (Analytics)

For analytics, LLM scores (/10) are multiplied by 10 and classified:

| Bucket | Range (/100) | Label |
|---|---|---|
| Excellent | >= 80 | Strong hire |
| Good | 60–79 | Solid candidate |
| Average | 40–59 | Borderline |
| Weak | < 40 | Not recommended |

#### Monthly Trend Computation

The `/analytics/scores` endpoint computes 6 months of historical data by iterating over month ranges:
- `applications`: interview sessions created in that month
- `interviews`: sessions with status `in_progress` or `completed`
- `hires`: completed sessions with weighted average >= 7.0

---

### 8.9 Notifications Module

**Files:** `notifications/models.py` · `notifications/routes.py` · `notifications/service.py`

Notifications are automatically created when `InterviewSessionCRUD.update_status("completed")` is called. The notification document is inserted synchronously (no queue or background task needed).

#### Notification Document

```json
{
  "recipient_email": "rh@example.com",
  "type": "interview_completed",
  "title": "Interview completed",
  "message": "Candidate Ahmed Ben Ali completed Data Scientist interview.",
  "data": {
    "session_id": "session_abc123",
    "candidate_name": "Ahmed Ben Ali",
    "position_title": "Data Scientist",
    "total_answers": 3
  },
  "priority": "high",
  "read": false,
  "created_at": "2026-03-26T10:30:00Z"
}
```

#### Notification Types

| Type | Trigger | Priority |
|---|---|---|
| `interview_completed` | Session status -> completed (automatic) | high |
| `interview_started` | Session status -> in_progress (via NotificationService) | normal |
| `match_found` | Score >= 80% (via NotificationService) | high |
| `new_candidate` | Candidate created (via NotificationService) | normal |
| `system_alert_*` | Custom system events | urgent |

Notifications are scoped to the logged-in recruiter's email — the `GET /notifications/` endpoint automatically filters by `recipient_email`.

---

### 8.10 Export Module

**File:** `export/routes.py`

All endpoints use FastAPI's `StreamingResponse` for memory-efficient streaming — no temp files are created server-side.

| Endpoint | Format | Contents |
|---|---|---|
| `GET /export/candidates/csv` | CSV | All candidates: name, email, skills, languages, certifications |
| `GET /export/interviews/csv` | CSV | All sessions: status, question count, average score |
| `GET /export/evaluations/csv` | CSV | Per-question: transcript, score, verdict, feedback |
| `GET /export/interviews/{id}/json` | JSON | Full session: candidate + position + all answers |

Files are streamed with timestamped filenames in `Content-Disposition` headers (e.g., `candidates_20260326_103045.csv`).

---

### 8.11 Media Module

**Files:** `media/models.py` · `media/routes.py`

Handles general file upload and download. Files are stored on disk under `UPLOAD_DIR/{category}/` with UUID-generated filenames to prevent collisions.

Allowed MIME types:
- **Audio:** `audio/wav`, `audio/mpeg`, `audio/ogg`, `audio/flac`
- **Video:** `video/mp4`, `video/webm`, `video/ogg`
- **Image:** `image/jpeg`, `image/png`, `image/gif`, `image/webp`

Interview audio recordings (from the WebSocket handler) are **not** routed through this module — they are saved directly to `uploads/interviews/` by `_process_answer()`.

---

### 8.12 Middlewares

**File:** `middlewares.py`

Three middleware classes are provided:

**`RequestLoggingMiddleware`**  
Logs every request: method, path, HTTP status, and processing time in milliseconds. Adds the `X-Process-Time` header to all responses.

**`ErrorHandlingMiddleware`**  
Catches unhandled exceptions and returns a structured `{"error": "...", "detail": "..."}` JSON 500 response instead of a raw Python traceback. In debug mode, the full error message is included; in production, a generic message is returned.

**`RateLimitMiddleware`**  
In-memory sliding window rate limiter. Default: 100 requests per 60 seconds per client IP. Adds `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers.

---

## 9. AI Services

### 9.1 ASR Service — Whisper

**File:** `services/asr_service.py`

#### Architecture

```
ASRService (unified facade)
+-- WhisperASR (faster-whisper)    <- Primary engine, GPU recommended
+-- VoskASR                         <- Offline fallback (Arabic only)
```

#### GPU Detection and Fallback

The service automatically detects GPU availability:

```python
if device == "cuda":
    if not torch.cuda.is_available():
        actual_device = "cpu"
        actual_compute_type = "int8"    # float16 requires GPU
    else:
        if actual_compute_type == "int8":
            actual_compute_type = "float16"  # Auto-upgrade on GPU
```

#### VAD Parameters

Voice Activity Detection filters silence from the recording:

```python
vad_parameters=dict(
    min_silence_duration_ms=500,  # Minimum silence to split segments
    threshold=0.5,                 # Speech probability threshold
)
```

Setting `condition_on_previous_text=False` prevents the model from hallucinating continuation of previous answers.

#### Supported Languages

| Code | Language | Whisper Internal Code |
|---|---|---|
| `ar` | Arabic | `ar` |
| `fr` | French | `fr` |
| `en` | English | `en` |

#### Performance (RTX 4050 Laptop)

| Model | CPU | GPU |
|---|---|---|
| tiny (75 MB) | ~2 s | ~0.5 s |
| medium (1.5 GB) | 5–10 s | ~1–3 s |
| large-v3 (3.1 GB) | 20–40 s | ~2–5 s |

---

### 9.2 TTS Service — Edge-TTS + gTTS

**Files:** `services/tts_service.py` · `services/edge_tts_engine.py`

#### Architecture

```
TTSService
+-- EdgeEngine (primary)
|   +-- EdgeTTSEngine
|         +-- Synthesize in dedicated thread (avoids asyncio conflicts)
|         +-- Retry x3 on 403 / WebSocket / network errors (backoff 1.5s base)
|         +-- MP3 -> WAV conversion via pydub
+-- GoogleEngine (automatic fallback)
    +-- gTTS -> MP3 -> WAV via pydub
```

#### Voice Configuration

| Language | Edge-TTS Voice | Character |
|---|---|---|
| Arabic | `ar-LB-LaylaNeural` | Lebanese female, natural intonation |
| French | `fr-FR-DeniseNeural` | French female, professional tone |
| English | `en-US-AriaNeural` | American female, clear diction |

#### MD5 Caching System

The service computes `MD5(text + language + voice_name)` and stores WAV files in `uploads/tts_cache/`. This means:
- Fixed phrases (welcome message, question text that doesn't change) are synthesized exactly once
- All subsequent interviews reuse cached audio at disk speed
- Cache survives server restarts and accumulates over time

#### TTS Prefetch Optimization

While the candidate records their answer to question N, the backend silently pre-generates audio for question N+1:

```python
# In InterviewHandler.handle()
next_tts_task = asyncio.create_task(
    self._synthesize_bytes(next_question_text)
)
# [wait for answer processing...]
prefetched = await asyncio.wait_for(next_tts_task, timeout=30.0)
self._prefetched_audio = prefetched  # Used in next _send_current_question()
```

This reduces the perceived gap between questions from several seconds to near zero on GPU setups.

---

### 9.3 LLM Service — Ollama + Llama 3.2

**File:** `services/llm_service.py`

#### Evaluation Method Overview

| Method | Use Case | Follow-up Output |
|---|---|---|
| `evaluate_answer()` | Simple grading | No |
| `evaluate_with_followup()` | Main interview flow | Yes (needs_followup + question) |
| `evaluate_final_with_followup()` | After follow-up collected | Combined score |
| `evaluate_with_facial()` | Full enriched evaluation | Yes + facial + duration context |
| `generate_global_summary()` | End-of-session HR report | Recommendation + summary |

#### Strict Grading Scale (System Prompt)

| Score | Verdict | Criteria |
|---|---|---|
| 9–10 | Excellent | Precise, structured, concrete examples, rare technical mastery |
| 7–8 | Very Good | Good answer, lacks depth or specific examples |
| 5–6 | Acceptable | Superficial or vague, notable inaccuracies |
| 3–4 | Insufficient | Errors or partial understanding |
| 0–2 | Poor | Off-topic, empty, or incorrect |

The system prompt includes the explicit warning: *"Do NOT be lenient. A generic or vague answer scores no more than 5/10."*

#### Duration Context Block

When `duration_seconds > 0` and `max_duration_seconds > 0`, a context block is appended to the system prompt:

```
Answer duration: 1m23s (allowed limit: 1m30s)
Usage ratio: 92%

Instructions:
  - < 20% of allocated time -> penalize -1 to -2 pts if content is poor
  - 40-90% -> neutral (ideal range)
  - > 90% with rich content -> possible +0.5 pt bonus
  - Do NOT penalize if the answer is short but complete and precise
```

#### Facial Context Block (80/20 Rule)

When `face_detection_rate >= 0.3`, a behavioral context block is appended:

```
Body language observed (automated camera analysis):
  * Dominant emotion: Neutral
  * Visual confidence: 7.2/10
  * Apparent stress: 3.8/10
  * Eye contact with camera: 81%
  * Posture stability: Good (stable posture)
  * Capture quality: 21/22 frames with face detected

Integration instructions:
  Answer content weighs 80%, non-verbal behavior 20%.
  If eye contact < 30%, mention it in improvement areas.
  If apparent stress > 7/10, be slightly more supportive in feedback.
  If capture quality < 30%, IGNORE facial data entirely.
```

#### JSON Parsing Robustness

The LLM response parser tries three patterns in fallback order:
1. Markdown code block: ` ```json ... ``` `
2. Plain code block: ` ``` ... ``` `
3. Any `{...}` object anywhere in the response

If all patterns fail, a deterministic fallback result is returned (score 5.0, verdict based on score, error message in feedback field). This ensures the system never crashes due to a malformed LLM response.

#### Global Summary Output Format

```json
{
  "recommendation": "Hire",
  "decision_reason": "Weighted average 7.33/10 across 3 questions.",
  "key_strengths": ["Clear communication", "Python proficiency"],
  "key_improvements": ["Deepen ML knowledge"],
  "summary": "Strong candidate with solid technical background. Recommended."
}
```

---

### 9.4 Facial Analysis Service

**File:** `services/facial_analysis_service.py`

#### Emotion Backend Priority Chain

```
Priority 1: HSEmotion EfficientNet-B0 (~82% accuracy)
   +-- Primary model: enet_b0_8_best_afew (lightweight, in-the-wild)
   +-- Fallback model: enet_b2_8_best_vgaf (heavier, AffectNet)
   +-- Dependencies: timm==0.9.2, efficientnet_pytorch, hsemotion
         |
         If HSEmotion fails (ImportError or missing timm.layers):
         |
Priority 2: DeepFace VGG CNN (~73% accuracy, AffectNet)
   +-- Dependencies: deepface, tf-keras
   +-- Warm-up at startup to preload CNN weights
         |
         If DeepFace fails:
         |
Priority 3: FACS Heuristics (geometric from landmarks, ~60%)
   +-- No additional ML dependency
   +-- Always available as final fallback
```

#### MediaPipe FaceMesh Metrics (per frame)

| Metric | Computation Method | Landmarks |
|---|---|---|
| Eye Aspect Ratio (EAR) | `vertical / horizontal eye distance` | 159, 145, 33, 133 |
| Blink detection | `(EAR_L + EAR_R) / 2 < 0.22` | Both eyes |
| Iris offset X | `(iris.x - eye_center.x) / eye_width` | 468, 473 |
| Eye contact | `abs(yaw) < 25deg AND abs(pitch) < 20deg AND not blink` | solvePnP |
| Head pose (yaw/pitch/roll) | OpenCV solvePnP + decomposeProjectionMatrix | 6 anchor points |
| Smile ratio | Lip corner elevation above lip midpoint | 13, 14, 61, 291 |
| Brow frown | Gap between inner brows vs. eye distance | 107, 336 |
| Brow raise | Vertical distance brow-to-eye | 107, 336, 159, 386 |

**Pitch/Yaw normalization:** `decomposeProjectionMatrix` can return pitch ~165-180° for a face-on view. The service normalizes both angles to the [-90, +90] range:

```python
if pitch > 90: pitch -= 180
elif pitch < -90: pitch += 180
```

#### Batch Processing Pipeline

```
N received JPEG frames
|
+-- Sample: select up to 25 evenly-spaced frames
|
+-- MediaPipe: process each frame sequentially (CPU-only in v0.10.14)
|   +-- Compute all landmark metrics per frame
|   +-- Cache face ROI crop from landmark bounding box (30% padding)
|
+-- Emotion backend: single batch call
|   +-- If HSEmotion: single PyTorch forward pass on all 25 crops (GPU)
|   +-- If DeepFace: sequential predict() calls
|   +-- If FACS: geometric computation from landmarks (no CNN)
|
+-- Merge results: inject emotion scores into FrameResult objects
```

#### Composite Score Formulas

**Confidence Score (0–10):**
```
= eye_contact_ratio * 2.5
+ head_stability * 2.0
+ emo_positive * 2.0       (happy*1.2 + surprise*0.3)
+ smile_ratio * 1.0
+ 2.5                       (base offset)
- emo_negative * 2.5        (angry + fear + sad*0.8 + disgust*0.5)
- neutral * 0.3             (neutral penalty)
- abs(avg_yaw / 45) * 0.5  (posture penalty)
```

**Stress Score (0–10):**
```
= brow_frown_avg * 3.5
+ (1 - head_stability) * 2.0
+ (1 - eye_contact_ratio) * 1.0
+ fear * 1.5 + angry * 1.0 + sad * 1.0 + surprise * 0.5
- happy * 1.5
```

**Engagement Score (0–10):**
```
= eye_contact_ratio * 3.0
+ (1 - neutral) * 2.0       (expressiveness)
+ smile_ratio * 1.5
+ head_stability * 1.5
+ brow_raise_avg * 0.5
+ happy * 1.0
- sad * 1.5 - disgust * 1.0
```

#### Reliability Flag

`behavioral_metrics_reliable = True` when more than 50% of face-detected frames had valid MediaPipe landmarks. When `False`, all behavioral scores use fallback formulas based on emotion scores only, and eye contact / head stability / smile values are not meaningful.

---

### 9.5 Avatar Service

**File:** `services/avatar_service.py`

| Provider | Description | Status |
|---|---|---|
| `simple` | Reads pre-recorded MP4 files from `assets/videos/` | Active, default |
| `did` | D-ID API stub | Not implemented (falls back to `simple`) |

Avatar video files and their associated application states:

| File | Client State | Trigger |
|---|---|---|
| `rh_idle.mp4` | `set_idle()` | Between questions, after answer saved |
| `rh_speaking.mp4` | `set_speaking()` | TTS audio playing / processing |
| `rh_listening.mp4` | `set_listening()` | Candidate actively recording |

If any video file is missing, `VideoPlayerWidget` displays a gradient placeholder showing the state name.

---

## 10. WebSocket Protocol

**Files:** `websocket/connection_manager.py` · `websocket/interview_handler.py`

### Connection URL

```
ws://localhost:8000/ws/interview/{session_id}?lang=fr
```

- `session_id`: format `session_xxxxxxxxxxxxxxxx` (provided by recruiter when creating the session)
- `lang`: `ar` / `fr` / `en` (optional; overrides session's stored language preference)

### Thread Pool Architecture

The handler uses four dedicated thread pools to prevent I/O-bound and CPU-bound work from blocking the asyncio event loop:

| Executor | Workers | Purpose |
|---|---|---|
| `_tts_executor` | 1 | Edge-TTS synthesis (synchronous blocking I/O) |
| `_llm_executor` | 2 | Reserved for httpx async calls to Ollama |
| `_asr_executor` | 2 | Whisper transcription (synchronous CPU/GPU) |
| `_facial_executor` | 1 | MediaPipe + HSEmotion batch analysis |

### Audio Chunk Transmission

Audio is transmitted as raw **PCM Int16, 16 kHz, mono**, split into 64 KB chunks encoded in base64:

```
Server sends:
  {type: "question", data: {audio_mode: "chunked", total_chunks: 12,
                             sample_rate: 22050, channels: 2, ...}}
  {type: "audio_chunk_data", data: {chunk_index: 0, total: 12, data: "<base64>"}}
  ... (chunks 1 through 11) ...
  {type: "audio_chunk_end", data: {msg_type: "question"}}
```

The client uses the metadata to reconfigure `pygame.mixer` and reassemble the complete WAV before playback.

### Complete Message Reference

#### Server to Client

| Message Type | Trigger | Key Fields Sent |
|---|---|---|
| `welcome` | New session connected | total_questions, facial_analysis_enabled, language |
| `welcome_back` | Reconnected to in_progress | current_question_index, is_reconnection: true |
| `question_loading` | TTS synthesis started | progress |
| `question` | TTS audio ready to stream | order, weight, max_duration |
| `audio_chunk_data` | Each PCM chunk | chunk_index, total, data (base64) |
| `audio_chunk_end` | All chunks sent | msg_type |
| `answer_saved` | Server received answer | duration, question_order, evaluation: "processing" |
| `answer_evaluated` | LLM grading complete | question_order, had_followup |
| `followup_incoming` | Follow-up triggered | initial_score, followup_text |
| `followup_question` | Follow-up audio streaming | question_order |
| `answer_followup_completed` | Follow-up processed | question_order, had_followup: true |
| `interview_completed` | All questions answered | total_questions, total_answers |
| `global_evaluation` | Full evaluation done | decision, decision_label, decision_color |
| `error` | Any error | message, error_type |
| `heartbeat` | Sent every 15s during TTS | (empty) |

> Note: Score, feedback, and facial metrics are **never included** in any client-facing message.

#### Client to Server

| Message Type | When Sent | Payload |
|---|---|---|
| `audio_chunk` | During recording | audio_data (base64 PCM Int16) |
| `video_frame` | During recording | data.frame (base64 JPEG, 640px max) |
| `answer_complete` | Record button stopped | (none) |
| `audio_finished` | Playback ended locally | (none) |
| `end_interview` | Voluntary termination | (none) |

### Parallel Answer Processing

When `answer_complete` is received, ASR and facial analysis run concurrently:

```python
transcript, facial_metrics = await asyncio.gather(
    _transcribe_audio(wav_bytes),           # Whisper in thread pool
    _analyze_facial_frames(frames_snapshot) # MediaPipe + HSEmotion in thread pool
)

# LLM evaluation with full context
result = await llm.evaluate_with_facial(
    question=question_text,
    answer=transcript,
    facial_metrics=facial_metrics,
    duration_seconds=duration,
    max_duration_seconds=question.max_duration_seconds,
)
```

### Heartbeat During Long Operations

When TTS synthesis takes more than a few seconds (e.g., for long questions or on CPU), `send_heartbeat_during()` keeps the WebSocket alive:

```python
audio = await manager.send_heartbeat_during(
    self.session_id,
    loop.run_in_executor(_tts_executor, synthesize_fn),
    interval=15.0,   # heartbeat every 15 seconds
)
```

### Session Reconnection

If `session.status == "in_progress"` when a new WebSocket connection arrives for the same `session_id`, the handler sends `welcome_back` instead of `welcome`, skipping the status update to `in_progress` and resuming at `current_question_index`.

---

## 11. Desktop Client (PySide6)

### 11.1 Core Modules

#### `AudioRecorder` (`core/audio_recorder.py`)

Uses **PyAudio** in non-blocking callback mode. The callback emits each chunk as a Qt signal, which is connected to the WebSocket send method in the main window:

```python
recorder = AudioRecorder()
recorder.audio_chunk_ready.connect(on_chunk)   # bytes -> websocket.send()
recorder.recording_started.connect(on_start)
recorder.stop_recording()
```

Configuration from `client/config.py`:
- Format: `paInt16` (16-bit signed PCM)
- Channels: 1 (mono)
- Sample rate: 16000 Hz
- Chunk size: 1024 frames per callback (~64ms at 16kHz)

#### `VideoFrameCollector` (`core/video_recorder.py`)

Uses **OpenCV + QTimer** in the Qt main thread (no separate QThread). This avoids OpenCV's thread-safety issues on Windows:

```python
collector = VideoFrameCollector(
    camera_index=0,
    target_fps=2.0,        # from FACIAL_CAPTURE_FPS in .env
    jpeg_quality=70,       # approximately 50 KB/s at 640x480
    max_width=640,         # resize if camera is wider
)
collector.frame_captured.connect(on_frame)   # JPEG bytes
collector.camera_ready.connect(on_ready)      # bool
collector.camera_error.connect(on_error)      # str
```

The QTimer interval is `int(1000 / target_fps)` ms. OpenCV's `CAP_PROP_BUFFERSIZE=1` ensures each capture gets the most recent frame rather than a buffered older one.

#### `WebSocketClient` (`core/websocket_client.py`)

Wraps `websockets` in a `QThread` to prevent blocking the Qt main thread:

```
Main Qt Thread                    Worker QThread (WebSocketWorker)
      |                                 |
  send_message(data)                    |
      +- run_coroutine_threadsafe() --> |-- asyncio: worker.send(data)
      |                                 |
      |  message_received signal <------+-- async for message in ws:
      |                                 |       message_received.emit(parsed)
      |                                 |
  disconnect_from_server()              |
      +- run_coroutine_threadsafe() --> |-- asyncio: ws.close()
      |  thread.quit() [non-blocking]   |   (loop closes, thread ends)
```

**Key design choice:** `disconnect_from_server()` does **not** call `thread.wait()`. Blocking the Qt event loop with `wait()` would freeze the UI. The thread terminates naturally when the asyncio loop closes after the WebSocket connection is closed.

---

### 11.2 UI Components

#### `MainWindow` (`ui/main_window.py`)

Organized as a `QStackedWidget` with an overlay for the interview:

| Layer | Visibility | Contents |
|---|---|---|
| Stack index 0 | Pre-connection | Language selection (3 LanguageCard widgets) |
| Stack index 1 | Pre-connection | Session ID input + connect |
| Interview overlay | During interview | VideoPlayerWidget (left) + InterviewWidget (right) |

**Audio playback pipeline:**
1. `audio_chunk_data` messages append base64-decoded bytes to `_audio_chunks` list
2. `audio_chunk_end` triggers: join chunks -> write WAV to temp file -> play via `pygame.mixer.music`
3. `QTimer` polls `pygame.mixer.music.get_busy()` every 200 ms
4. On playback end: delete temp file, send `audio_finished` to server, enable record button

**Audio format adaptation:**  
`_ensure_audio_format(sr, ch, bits)` compares new format to current `pygame.mixer` settings and reinitializes only if they differ (avoids unnecessary restarts):

```python
pygame.mixer.quit()
pygame.mixer.init(frequency=sr, size=-bits, channels=ch, buffer=4096)
```

#### `InterviewWidget` (`ui/interview_widget.py`)

The right panel consists of three sub-components:

**`_SectionHeader`** — An animated pulsing dot (indigo at rest, red during recording) with the section label (e.g., "VOICE INTERVIEW").

**`_ProgressCard`** — Shows:
- `Question X / Y` label + percentage badge (indigo pill)
- 4px-height gradient progress bar
- Dot indicators: one per question, filled indigo as questions complete

**`_InfoCard`** — The central information card with:
- Gradient bubble with microphone emoji
- Status pill with 4 states: `waiting` (gray) / `playing` (amber) / `ready` (green) / `recording` (red)
- Duration badge (amber pill showing max recording time)
- Countdown timer (turns amber at <30s, red at <10s)

**Record button auto-stop:** When the countdown reaches 0, `_stop_rec(auto=True)` is called, which stops the recording and sends `answer_complete` to the server.

**Localization:** All text strings are in `TEXTS = {"ar": {...}, "fr": {...}, "en": {...}}`. Arabic mode sets `Qt.LayoutDirection.RightToLeft` on the widget.

#### `VideoPlayerWidget` (`ui/video_player_widget.py`)

Plays avatar MP4 files using OpenCV for frame reading, pygame for surface conversion, and QLabel for display. The render loop runs at ~30 fps via QTimer.

Three states with distinct visual feedback:

| State | Video | Icon | Status Badge |
|---|---|---|---|
| `set_idle()` | `rh_idle.mp4` | user-check (green) | Disponible |
| `set_speaking()` | `rh_speaking.mp4` | message-circle (indigo) | En cours |
| `set_listening()` | `rh_listening.mp4` | headphones (amber) | Enregistrement |

The top bar shows a LIVE badge with an animated pulsing dot and the agent name/status.

#### `CameraPreviewWidget` (`ui/camera_preview_widget.py`)

Fixed 200x170 px Picture-in-Picture overlay positioned in the bottom-left corner of `VideoPlayerWidget`. Key behaviors:

- Receives JPEG frames via the `on_frame(bytes)` slot
- Runs real-time MediaPipe analysis in a daemon thread (does not block the Qt timer)
- Draws a green border when a face is detected, gray otherwise
- Animates the REC badge (blinks at 600ms interval) during recording
- Client-side metrics are used for the local visual overlay only — **they are not transmitted to the server**; raw frames are sent instead

The same MediaPipe pre-loading stub injection is applied at the top of this file to ensure compatibility with the Windows protobuf constraint.

---

### 11.3 Design System

**File:** `ui/stark_theme.py`

#### Token Namespace `T`

All visual constants are centralized as class attributes:

```python
# Colors
T.INDIGO_500    # "#6366F1"  -- primary brand color
T.BG_CARD       # "#FFFFFF"  -- all card backgrounds
T.BORDER        # "#E5E7EB"  -- single border color (gray-200)
T.TEXT_900      # "#111827"  -- headings

# Typography
T.FONT          # "'DM Sans', 'Inter', 'Segoe UI', system-ui, sans-serif"
T.FONT_MONO     # "'JetBrains Mono', 'Fira Code', monospace"
T.FS_SM         # 12 -- small
T.FS_MD         # 15 -- medium (default body)
T.FS_LG         # 18 -- large

# Spacing (8px grid)
T.SP_2          # 8
T.SP_4          # 16
T.SP_6          # 24

# Border radius
T.R_LG          # 14
T.R_XL          # 16
T.R_2XL         # 20
T.R_FULL        # 9999 (pill shape)
```

#### `StarkTheme` Component Styles

| Method | Variant | Description |
|---|---|---|
| `get_button_style("primary")` | Indigo to Violet gradient | Main CTA buttons |
| `get_button_style("accent")` | Same gradient | Session screen connect button |
| `get_button_style("ghost")` | Outline, gray | Back / secondary actions |
| `get_button_style("danger")` | Red outline, fills on hover | End interview button |
| `get_button_style("record")` | Primary variant | Record button base style |
| `progress_style()` | Indigo gradient, 4px | Progress bar in ProgressCard |
| `input_style()` | White, focus ring | Session ID text input |
| `global_stylesheet()` | App-wide | QMainWindow, scrollbars, tooltips |

The design follows a Stripe/Linear-inspired aesthetic: white cards on off-white background, single neutral border color, indigo-to-violet gradient for primary actions, generous border radius, soft shadows with no color cast.

---

## 12. Data Models & MongoDB Schema

### `interview_sessions` — Full Embedded Answer with Evaluation

```json
{
  "_id": "ObjectId",
  "session_id": "session_abc123def456ghi",
  "candidate_id": "64abc000000000000000",
  "job_position_id": "64def000000000000000",
  "language": "fr",
  "status": "completed",
  "current_question_index": 3,
  "created_by": "rh@company.com",
  "scheduled_at": null,
  "late_access_deadline": null,
  "expires_at": "2026-03-26T11:00:00Z",
  "created_at": "2026-03-26T10:00:00Z",
  "started_at": "2026-03-26T10:05:00Z",
  "completed_at": "2026-03-26T10:35:00Z",
  "evaluation_score": 7.33,
  "evaluation_decision": "accepted",
  "evaluation_decision_label": "Accepte",
  "evaluation_decision_color": "#10B981",
  "evaluation_recommendation": "Embaucher",
  "evaluation_decision_reason": "Moyenne ponderee de 7.33/10 sur 3 question(s).",
  "answers": [
    {
      "question_order": 1,
      "question_text": "Decrivez votre experience en Python.",
      "transcript": "J'ai 3 ans d'experience en Python, notamment avec FastAPI...",
      "audio_file_path": "uploads/interviews/answer_session_abc123_1.wav",
      "duration_seconds": 52.3,
      "timestamp": "2026-03-26T10:06:00Z",
      "evaluation": {
        "score": 8.0,
        "verdict": "Tres bien",
        "feedback": "Reponse claire avec des exemples concrets.",
        "strengths": ["Exemples concrets", "Bonne structure"],
        "improvements": ["Approfondir les frameworks ML"],
        "llm_model": "llama3.2",
        "evaluated_at": "2026-03-26T10:07:30Z",
        "weight": 1.0,
        "had_followup": false,
        "initial_score": null,
        "initial_verdict": null,
        "followup_question": null,
        "followup_transcript": null,
        "facial_analysis": {
          "dominant_emotion": "neutral",
          "emotion_scores": {
            "angry": 2.1, "disgust": 0.8, "fear": 1.2,
            "happy": 15.3, "sad": 3.4, "surprise": 5.1, "neutral": 72.1
          },
          "eye_contact_ratio": 0.82,
          "head_stability": 0.91,
          "smile_ratio": 0.23,
          "confidence_score": 7.4,
          "stress_score": 3.2,
          "engagement_score": 7.8,
          "frames_analyzed": 22,
          "frames_with_face": 21,
          "face_detection_rate": 0.95
        }
      }
    }
  ]
}
```

### `evaluations` — Global HR Report

```json
{
  "session_id": "session_abc123def456ghi",
  "candidate_name": "Ahmed Ben Ali",
  "position_title": "Data Scientist",
  "language": "fr",
  "total_questions": 3,
  "answered_questions": 3,
  "average_score": 7.33,
  "decision": "accepted",
  "decision_label": "Accepte",
  "decision_color": "#10B981",
  "decision_reason": "Moyenne ponderee de 7.33/10 sur 3 question(s).",
  "recommendation": "Embaucher",
  "key_strengths": ["Communication claire", "Maitrise Python"],
  "key_improvements": ["Approfondir le ML"],
  "summary": "Candidat solide avec une bonne maitrise technique. Recommande.",
  "llm_model": "llama3.2",
  "evaluated_at": "2026-03-26T10:36:00Z",
  "per_answer": ["...AnswerEvaluation objects..."],
  "facial_summary": {
    "avg_confidence": 7.1,
    "avg_stress": 3.5,
    "avg_engagement": 7.6,
    "avg_eye_contact": 0.79,
    "avg_head_stability": 0.88,
    "dominant_emotion": "neutral",
    "facial_available": true
  }
}
```

---

## 13. API Reference

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/login` | None | Get JWT token (form-encoded) |
| `GET` | `/auth/me` | JWT | Get current recruiter email |

### Candidates

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/candidates/` | JWT | Create candidate |
| `GET` | `/candidates/?skip=0&limit=100` | JWT | List with pagination |
| `GET` | `/candidates/{id}` | JWT | Get by ID |
| `PATCH` | `/candidates/{id}` | JWT | Partial update |
| `DELETE` | `/candidates/{id}` | JWT | Hard delete |
| `GET` | `/candidates/search/email?email=` | JWT | Find by email |
| `GET` | `/candidates/search/skills?skills=&min_match=1` | JWT | Find by skills |
| `POST` | `/candidates/{id}/consents` | JWT | Add GDPR consent |

### Interviews

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/interviews/positions` | JWT | Create position with questions |
| `GET` | `/interviews/positions` | JWT | List (dept, location, is_active, period_days, sort) |
| `GET` | `/interviews/positions/{id}` | JWT | Position detail |
| `DELETE` | `/interviews/positions/{id}` | JWT | Delete position |
| `GET` | `/interviews/positions/meta/departments` | JWT | Distinct departments list |
| `GET` | `/interviews/positions/meta/locations` | JWT | Distinct locations list |
| `POST` | `/interviews/sessions` | JWT | Create session |
| `GET` | `/interviews/sessions?status=` | JWT | List sessions |
| `GET` | `/interviews/sessions/{id}` | JWT | Session detail + answers |
| `GET` | `/interviews/sessions/{id}/answers` | JWT | Answers + evaluations |
| `GET` | `/interviews/sessions/{id}/answers/summary` | JWT | Score summary |
| `PATCH` | `/interviews/sessions/{id}/status?status=` | JWT | Update status |
| `PATCH` | `/interviews/sessions/{id}/schedule?scheduled_at=` | JWT | Schedule or reschedule |
| `DELETE` | `/interviews/sessions/{id}` | JWT | Delete session |
| `WS` | `/ws/interview/{session_id}?lang=fr` | None | Real-time interview |

### Evaluations

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/evaluations/trigger` | JWT | Launch background evaluation |
| `GET` | `/evaluations/{session_id}` | JWT | Get full HR report |
| `GET` | `/evaluations/?skip=0&limit=50` | JWT | List evaluations |
| `DELETE` | `/evaluations/{session_id}` | JWT | Delete evaluation |
| `GET` | `/evaluations/health/llm` | JWT | Ollama availability check |

### Analytics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/analytics/dashboard?days=30` | JWT | All KPIs combined |
| `GET` | `/analytics/candidates?days=30` | JWT | Candidate statistics |
| `GET` | `/analytics/interviews?days=30` | JWT | Interview statistics |
| `GET` | `/analytics/system` | JWT | System health |
| `GET` | `/analytics/scheduling` | JWT | Scheduling statistics |
| `GET` | `/analytics/scores` | JWT | Score distribution and 6-month trends |
| `GET` | `/analytics/positions/scores?position_id=` | JWT | Per-position breakdown |

### Export

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/export/candidates/csv` | JWT | All candidates (streamed CSV) |
| `GET` | `/export/interviews/csv` | JWT | All sessions (streamed CSV) |
| `GET` | `/export/evaluations/csv` | JWT | Per-question evaluations (streamed CSV) |
| `GET` | `/export/interviews/{id}/json` | JWT | Full session report (streamed JSON) |

### Notifications

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/notifications/?unread_only=true` | JWT | List (scoped to current recruiter) |
| `GET` | `/notifications/unread-count` | JWT | Badge count |
| `PATCH` | `/notifications/{id}` | JWT | Mark as read |
| `POST` | `/notifications/mark-all-read` | JWT | Bulk mark as read |
| `DELETE` | `/notifications/{id}` | JWT | Delete |

---

## 14. Scoring & Decision Logic

### Weighted Average Formula

```
average_score = Σ(score_i * weight_i) / Σ(weight_i)
```

**Worked example — 3 questions with weights 1, 2, 3:**

| Question | Score /10 | Weight | Weighted Points |
|---|---|---|---|
| Q1 | 8.0 | 1.0 | 8.0 |
| Q2 | 6.0 | 2.0 | 12.0 |
| Q3 | 7.5 | 3.0 | 22.5 |
| **Result** | — | **6.0 total** | **42.5 / 6 = 7.08 -> ACCEPTED** |

### Decision Table

| Score Range | Decision | Localized Label (FR) | Display Color |
|---|---|---|---|
| score >= 7.0 | `accepted` | Accepte | `#10B981` (green-500) |
| 5.0 <= score < 7.0 | `pending` | En attente | `#F59E0B` (amber-500) |
| score < 5.0 | `rejected` | Refuse | `#EF4444` (red-500) |

### Follow-Up Trigger Rule

A follow-up question is asked when ALL of the following are true:
1. `initial_score < 8` — the LLM returned `needs_followup: true`
2. `followup_question` string is non-empty
3. The client is still connected when `answer_evaluated` is processed

After collecting the follow-up answer:
- `evaluate_final_with_followup()` evaluates both initial and follow-up together
- Final score replaces initial score in `answers[n].evaluation`
- `had_followup: true`, `initial_score`, `initial_verdict`, `followup_question`, and `followup_transcript` are stored for the HR report

---

## 15. Privacy & Security Design

### Data Visibility Matrix

| Data | Candidate Sees | Recruiter Sees |
|---|---|---|
| Score /10 | Never | Full report |
| LLM feedback | Never | Full report |
| Individual question scores | Never | Full report |
| Facial metrics (confidence, stress, engagement) | Never | Full report |
| Decision label (Accepted/Pending/Rejected) | Yes (in global_evaluation message) | Yes + reason |
| Question text | Audio only (no text displayed) | Text in report |
| Follow-up initial score | Never | Both initial + final |
| Average score | Never | Full report |

### JWT Security

- Tokens expire after 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- `SECRET_KEY` must be a 32-byte cryptographically random hex string in production
- All recruiter-facing REST endpoints use `Depends(get_current_recruiter)`
- Invalid or expired tokens return HTTP 401 with detail "Token invalide"

### GDPR Features

- The `consents` array on each candidate tracks explicit consents with type, granted status, timestamp, and IP address
- Three consent types are used: `data_processing`, `voice_recording`, `ai_analysis`
- Candidates can be fully removed via `DELETE /candidates/{id}` (hard delete)
- Behavioral metrics are never exposed through any client-facing channel

---

## 16. Performance Benchmarks

Measured on ASUS laptop with **NVIDIA RTX 4050 (6 GB VRAM):**

| Component | CPU Time | GPU Time | Notes |
|---|---|---|---|
| Whisper medium (ASR) | 5–10 s | ~1–3 s | Per 45-second answer |
| Llama 3.2 (LLM evaluation) | 15–30 s | ~2–8 s | Depends on answer length |
| Edge-TTS synthesis | ~1 s | ~1 s | Network-bound, not GPU |
| HSEmotion per frame (batch 25) | ~40 ms | ~8 ms | Full batch |
| MediaPipe FaceMesh per frame | ~8 ms | ~8 ms | CPU-only in v0.10.14 |
| **Total per question (GPU)** | — | **~5–12 s** | ASR + LLM + Facial parallel |
| **Total per question (CPU)** | **25–45 s** | — | — |

**TTS prefetch impact:** By pre-generating question N+1 audio during answer processing for question N, the perceived inter-question delay drops from ~5–12 s to near zero on GPU setups.

---

## 17. Troubleshooting

| Error | Root Cause | Fix |
|---|---|---|
| `FieldDescriptor has no attribute 'label'` | protobuf >= 5 loaded before MediaPipe | `pip install "protobuf>=4.25.3,<5.0.0"` then restart |
| `cudnn_ops_infer64_8.dll not found` | cuDNN 8 missing for ctranslate2 | `pip install nvidia-cudnn-cu12==8.9.7.29` |
| `float16 not supported on device cpu` | CPU mode with float16 compute type | Set `WHISPER_COMPUTE_TYPE=int8` in `.env` |
| `Connection refused on :11434` | Ollama not running | Run `ollama serve` in a terminal |
| `ServerSelectionTimeoutError` | MongoDB service stopped | Windows: `net start MongoDB` / Linux: `sudo systemctl start mongod` |
| `No module named 'timm.layers'` | timm < 0.9.2 installed | `pip install timm==0.9.2` |
| `No module named 'efficientnet_pytorch'` | Missing HSEmotion dependency | `pip install efficientnet_pytorch` |
| PyAudio installation fails | Missing system C++ build tools | Windows: install VS Build Tools 2022 first |
| `WebSocket 4003 SESSION_INVALID` | Session expired or not found | Check session_id format; recreate session |
| Edge-TTS 403 error | Microsoft API rate limit | Automatic retry x3 handles this; wait 30s if it persists |
| `pygame.error: No available audio device` | No audio output device | Ensure audio drivers installed and device connected |
| Camera not detected | Wrong index or driver issue | Try `camera_index=1` or reinstall camera drivers |
| Whisper returns empty string | Recording too short or pure silence | Minimum ~2 seconds of speech required |
| LLM score always 5.0 | Ollama timeout / malformed JSON | Increase `OLLAMA_TIMEOUT`, check Ollama logs |
| `HSEmotion warm-up failed` | Model not downloaded yet | First inference auto-downloads; ensure internet access |

---

## 18. Academic Context

SparkHire AI integrates concepts from the following domains of the Data Engineering & Decision Systems curriculum:

| Domain | Concepts Applied |
|---|---|
| **Data Engineering** | Real-time streaming pipeline (audio/video), MongoDB document schema design, embedded vs. referenced documents, FastAPI REST and WebSocket architecture, asynchronous Python (asyncio + ThreadPoolExecutor) |
| **Artificial Intelligence** | Whisper ASR (CTC + beam search + VAD), Llama 3.2 (decoder-only Transformer, prompt engineering, multilingual instruction following), Edge-TTS (neural TTS with voice cloning), HSEmotion (EfficientNet-B0 fine-tuned on AffectNet8) |
| **Computer Vision** | MediaPipe FaceMesh (478 3D landmarks), Eye Aspect Ratio (blink detection), OpenCV solvePnP (head pose estimation), iris gaze estimation, FACS action units heuristics |
| **Decision Systems** | Weighted scoring model, multi-threshold hiring decision (accept/pending/reject), follow-up question generation logic, 80/20 content/behavior integration, completeness guarantees for decision reports |
| **Software Engineering** | WebSocket real-time protocol, JWT stateless authentication, privacy by design, async/sync hybrid architecture, singleton pattern (services), dependency injection (FastAPI Depends) |
| **Human-Computer Interaction** | Trilingual UI (Arabic / French / English), RTL layout support (Qt LayoutDirection), real-time visual feedback (PulseDot, countdown), audio-only privacy mode |

### Ethical Notes on Facial Analysis

The behavioral analysis component is framed as a **supplementary observational indicator** with important methodological caveats:

- Verbal content always carries **80%** of the evaluation weight; non-verbal behavior contributes at most **20%**
- `face_detection_rate < 0.3` triggers automatic exclusion of facial context from the LLM prompt to prevent bias from unreliable captures
- HSEmotion accuracy (~82%) is measured under controlled conditions; real-world accuracy varies with lighting, camera quality, makeup, glasses, and individual facial anatomy
- Behavioral scores are presented to recruiters alongside this disclaimer — no hiring decision is made solely on facial metrics
- The gap between lab-condition and real-world accuracy for emotion recognition models is explicitly acknowledged in the project defense materials

---

## License & Contact

**Proprietary** — SparkHire AI © 2026  
ENET'Com Sfax — Data Engineering & Decisional Systems

**Author:** Zeineb Ghrab  
**Email:** `zeineb.ghrab@enetcom.u-sfax.tn`  
**GitHub:** [ZeinebGhrab/sparkhire-ai](https://github.com/ZeinebGhrab/sparkhire-ai)

---

*Documentation generated from complete source code analysis — March 2026*