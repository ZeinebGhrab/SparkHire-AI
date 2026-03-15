# 🎤 SparkHire AI — Intelligent Voice Interview Platform

Complete recruitment platform with automated voice interviews via AI avatar.

> **Pipeline:** Candidate speaks → Whisper ASR (GPU) → Llama 3.2 LLM (GPU) → Score + Real-time Feedback

---

## ✨ Features

- 🎙️ **Automated voice interviews** with animated HR avatar
- 🌍 **Trilingual** support: Arabic / French / English
- 🧠 **AI transcription** via Whisper (faster-whisper) — GPU-accelerated, ~0.3s per answer
- 📝 **Strict AI evaluation** via Ollama + Llama 3.2 (score 0–10, rigorous grading scale)
- 🔁 **Intelligent follow-up questions** if the answer is insufficient (score < 8)
- 📊 **Global interview report** with final hiring decision (Accepted / On Hold / Rejected)
- 🔔 **Automatic recruiter notification** when an interview is completed
- 🗓️ **Interview scheduling** with 30-minute late access window
- 🔊 **Text-to-speech** via Edge-TTS (Microsoft) — primary engine, instant
- 🔁 **Automatic TTS fallback** via gTTS (Google) if Edge-TTS is unavailable
- ⚡ **Real-time WebSocket** (chunked PCM audio)
- ⚡ **TTS prefetch** — next question audio generated while candidate answers current one
- 🚀 **Non-blocking LLM evaluation** — transition between questions is immediate
- 🔐 **JWT authentication** for recruiters
- 🖥️ **PySide6 client interface** (light professional design)
- 🗃️ **MongoDB** — candidates, positions, sessions, evaluations, notifications
- 📤 **CSV / JSON export** + analytics dashboard
- 🖥️ **Cross-platform** — Windows, Linux, macOS

---

## 📋 Prerequisites

| Software | Version | Link | Notes |
|---|---|---|---|
| Python | 3.10 or 3.11 | [python.org](https://python.org) | Check **Add to PATH** |
| Git | latest | [git-scm.com](https://git-scm.com) | To clone the repo |
| MongoDB | 7.x Community | [mongodb.com](https://www.mongodb.com) | Install as a service |
| Ollama | latest | [ollama.com](https://ollama.com/download) | Required for LLM evaluation |
| FFmpeg | 6.0+ | [ffmpeg.org](https://ffmpeg.org) | Only needed if gTTS fallback is used |
| CUDA Toolkit | 11.x or 12.x | [nvidia.com](https://developer.nvidia.com/cuda-downloads) | Optional — for GPU acceleration |

> **FFmpeg installation by OS:**
> - **Windows** — Extract to `models/ffmpeg-8.0.1-essentials_build/` (auto-detected) or add to PATH
> - **Linux** — `sudo apt install ffmpeg`
> - **macOS** — `brew install ffmpeg`

> **Windows only:** VS C++ Build Tools 2022 required to compile PyAudio → [visualstudio.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

---

## 🚀 Installation

### 1. Clone the project

```bash
git clone https://github.com/ZeinebGhrab/sparkhire-ai.git
cd sparkhire-ai
```

### 2. Virtual environment (optional but recommended)

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

### 3. Backend dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Windows — PyAudio:** if `pip install` fails on PyAudio:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

> ⚠️ **Linux — PyAudio:** if PortAudio error:
> ```bash
> sudo apt install portaudio19-dev python3-dev
> pip install pyaudio
> ```

### 4. Client dependencies

```bash
pip install -r client/requirements.txt
```

### 5. GPU support — PyTorch + CTranslate2 (recommended)

If you have an NVIDIA GPU, install the CUDA-enabled versions for maximum performance:

```bash
# Check your CUDA version first
nvidia-smi

# Install PyTorch with CUDA 12.1 support
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install CTranslate2 with CUDA support (for Whisper GPU)
pip install ctranslate2==4.4.0 faster-whisper==1.0.3
```

> **Verify GPU support:**
> ```bash
> python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
> python -c "import ctranslate2; print(ctranslate2.get_supported_compute_types('cuda'))"
> ```

### 6. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Configuration](#%EF%B8%8F-configuration) below).

### 7. Download the Whisper model

```bash
python scripts/download_whisper.py medium
```

| Size | Weight | Recommended |
|---|---|---|
| tiny | 75 MB | quick tests |
| base | 145 MB | — |
| small | 483 MB | — |
| **medium** | **1.5 GB** | ✅ **recommended** |
| large-v3 | 3.1 GB | GPU only (6 GB+ VRAM) |

The model is saved automatically in `models/whisper/`.

### 8. Ollama LLM model

```bash
# Start the Ollama server (separate terminal)
ollama serve

# Download Llama 3.2 (recommended — 2.8 GB GPU)
ollama pull llama3.2

# Alternative: Llama 3 full size (4.7 GB)
ollama pull llama3

# Alternative if RAM < 8 GB
ollama pull llama3:8b-instruct-q4_0   # 2.3 GB
```

> Verify Ollama is using GPU:
> ```bash
> ollama ps
> # Should show: 100% GPU
> ```

> If you use a different model, update `OLLAMA_MODEL` in `.env`.

### 9. Database setup

```bash
# Create the admin recruiter account
python scripts/create_admin.py

# Insert demo positions and questions
python scripts/seed_job_positions.py
```

---

## ▶️ Running the App

### Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected startup logs (GPU mode):**
```
🎮 GPU détecté : NVIDIA GeForce RTX XXXX | VRAM=X.X GB
✅ Whisper 'medium' prêt sur CUDA
🎙️ TTS Service prêt | primaire=EdgeEngine | fallback=GoogleEngine
LLM Ollama disponible | modèle=llama3.2
```

- API: [http://localhost:8000](http://localhost:8000)
- Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### PySide6 Client

```bash
python -m client.main
```

---

## ⚡ Performance

| Component | CPU mode | GPU mode (RTX 4050+) |
|---|---|---|
| Whisper ASR (medium) | 5–10s | **~0.3–0.5s** |
| Ollama LLM (llama3.2) | 15–30s | **~2–4s** |
| Edge-TTS | ~1s | ~1s (network) |
| **Total inter-question** | **25–45s** | **~3–7s** |

**VRAM usage (RTX 4050 6.4 GB):**
- Whisper medium: ~1.5 GB
- llama3.2: ~2.8 GB
- Total: ~4.3 GB / 6.4 GB

---

## 📝 Usage

### 1. Create an interview (API)

```bash
# Login → get JWT token
curl -X POST http://localhost:8000/auth/login \
  -d "username=rh@stark.tn&password=admin123"

# Create a candidate (all 6 fields are required)
curl -X POST http://localhost:8000/candidates/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ahmed",
    "last_name": "Ben Ali",
    "contact": { "email": "ahmed@example.com", "phone": "+216 55 000 000" },
    "technical_skills": [{ "name": "Python", "level": "Advanced" }],
    "experiences":  [{ "title": "Data Scientist", "company": "TechCorp" }],
    "education":    [{ "degree": "Engineer", "field": "Data Engineering", "institution": "ENETCOM" }],
    "languages":    [{ "name": "French", "level": "C1" }],
    "soft_skills":  [{ "name": "Teamwork" }],
    "certifications": [{ "name": "AWS Developer", "issuer": "Amazon" }]
  }'

# Create an interview session
curl -X POST http://localhost:8000/interviews/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "<id>",
    "job_position_id": "<id>",
    "language": "fr",
    "scheduled_at": "2026-03-20T10:00:00Z"
  }'
```

### 2. Take the interview (Client)

1. `python -m client.main`
2. Select the interview language
3. Enter the `session_id` (format: `session_xxxxxxxxxxxxxxxx`)
4. Click **Start Interview**
5. Listen to the avatar ask questions
6. Click **Record** → speak → **Stop**
7. Score and feedback appear in real time after each answer
8. A global report with hiring decision is displayed at the end

### 3. View results & notifications

```bash
# Full session details
GET http://localhost:8000/interviews/sessions/<session_id>

# LLM evaluation + hiring decision
GET http://localhost:8000/evaluations/<session_id>

# Recruiter notifications (unread badge)
GET http://localhost:8000/notifications/unread-count

# List all unread notifications
GET http://localhost:8000/notifications/?unread_only=true

# Mark a notification as read
PATCH http://localhost:8000/notifications/<notification_id>
      Body: { "read": true }

# Export all evaluations as CSV
GET http://localhost:8000/export/evaluations/csv

# Automated full-flow test
python scripts/test_interview.py
```

---

## 🔔 Recruiter Notification System

When a candidate completes an interview, the platform automatically notifies the recruiter who created the session.

### How it works

```
Interview ends (last answer submitted)
        │
        ▼
 _complete_interview()
        │
        ├── Status → "completed" in MongoDB
        ├── Closing audio sent to candidate
        │
        ├── _notify_recruiter_completed()  ← non-blocking task
        │         │
        │         ├── Reads created_by from session (recruiter email)
        │         ├── Fallback: notifies ALL recruiters if created_by is empty
        │         └── Inserts into db.notifications
        │
        └── _run_global_evaluation()       ← non-blocking task
                  └── LLM global report + hiring decision
```

### Notification API endpoints

| Endpoint | Description |
|---|---|
| `GET /notifications/unread-count` | Badge counter for the recruiter UI |
| `GET /notifications/` | List all notifications (supports `?unread_only=true`) |
| `PATCH /notifications/{id}` | Mark a single notification as read |
| `POST /notifications/mark-all-read` | Mark all notifications as read |
| `DELETE /notifications/{id}` | Delete a notification |

---

## 📂 Project Structure

```
sparkhire-ai/
│
├── backend/                        ← FastAPI backend
│   ├── main.py                     ← Entry point + lifespan + routes
│   ├── config.py                   ← Pydantic Settings (extra="ignore")
│   ├── database.py                 ← MongoDB connection
│   │
│   ├── auth/                       ← JWT authentication
│   │   ├── models.py               ← Recruiter, Token
│   │   ├── routes.py               ← POST /auth/login · GET /auth/me
│   │   └── security.py             ← bcrypt, JWT, OAuth2
│   │
│   ├── candidates/                 ← Candidate management
│   │   ├── crud.py
│   │   ├── models.py               ← CandidateCreate (strict) · Candidate (response)
│   │   └── routes.py               ← /candidates CRUD + search
│   │
│   ├── interviews/                 ← Sessions and job positions
│   │   ├── crud.py                 ← create(session, created_by=email)
│   │   ├── models.py               ← InterviewSession + created_by field
│   │   └── routes.py               ← created_by auto-filled from JWT
│   │
│   ├── evaluation/                 ← LLM evaluation pipeline
│   │   ├── models.py               ← AnswerEvaluation, GlobalEvaluation + decision
│   │   ├── service.py              ← EvaluationService (ASR → LLM orchestration)
│   │   └── routes.py               ← /evaluations CRUD + trigger + health
│   │
│   ├── services/                   ← Core services
│   │   ├── asr_service.py          ← WhisperASR (GPU auto-detect) + VoskASR + factory
│   │   ├── tts_service.py          ← TTSService (Edge-TTS → gTTS fallback)
│   │   ├── edge_tts_engine.py      ← Microsoft Edge-TTS (Arabic / FR / EN voices)
│   │   ├── llm_service.py          ← OllamaLLMService (Llama 3.2, strict grading)
│   │   └── avatar_service.py       ← AvatarService (simple / liveportrait / wav2lip / did)
│   │
│   ├── websocket/                  ← Real-time communication
│   │   ├── connection_manager.py   ← ConnectionManager + heartbeat keepalive
│   │   └── interview_handler.py    ← Full pipeline + TTS prefetch + non-blocking LLM
│   │
│   ├── notifications/              ← Notification system
│   │   ├── models.py               ← Notification, NotificationCreate
│   │   ├── routes.py               ← /notifications CRUD
│   │   └── service.py              ← notify_interview_completed() + others
│   │
│   ├── media/                      ← File upload / download
│   ├── analytics/                  ← Dashboard stats + scheduling + score KPIs
│   └── export/                     ← CSV (candidates, interviews, evaluations) + JSON
│
├── client/                         ← PySide6 interface
│   ├── config.py                   ← Client settings (extra="ignore")
│   ├── main.py                     ← QApplication entry point
│   ├── core/
│   │   ├── models.py               ← Question, Answer, Progress (dataclasses)
│   │   ├── audio_recorder.py       ← PyAudio → WebSocket chunks
│   │   └── websocket_client.py     ← Thread-safe WebSocketClient
│   └── ui/
│       ├── stark_theme.py          ← Design system (colors, fonts, styles)
│       ├── icons.py                ← Lucide SVG icons + SparkHire logos
│       ├── main_window.py          ← Main window (pygame 24000 Hz)
│       ├── interview_widget.py     ← Interview controls + progress
│       └── video_player_widget.py  ← Avatar video (cv2 + pygame)
│
├── scripts/
│   ├── create_admin.py             ← Create admin recruiter in DB
│   ├── seed_job_positions.py       ← Insert positions + questions (AR/FR/EN)
│   ├── download_whisper.py         ← Download Whisper model
│   └── test_interview.py           ← Full flow automated test
│
├── models/                         ← AI models (gitignored)
├── uploads/                        ← Runtime files (gitignored)
├── assets/videos/                  ← Avatar videos (idle / speaking / listening)
├── .env                            ← Environment variables (gitignored)
├── .env.example                    ← Template to copy
├── requirements.txt                ← Backend dependencies
└── client/requirements.txt         ← Client dependencies
```

---

## 🔌 WebSocket Protocol

```
ws://localhost:8000/ws/interview/{session_id}?lang=ar|fr|en
```

**Client → Server**

| Message | Description |
|---|---|
| `audio_chunk` | Base64 PCM chunk from microphone |
| `answer_complete` | End of recording signal |
| `audio_finished` | End of audio playback on client side |
| `end_interview` | Terminate the interview |

**Server → Client**

| Message | Description |
|---|---|
| `welcome` | Welcome message + chunked PCM audio |
| `question` | Question audio + progress metadata |
| `audio_chunk_data` | Base64 PCM audio chunk |
| `audio_chunk_end` | End of audio stream |
| `heartbeat` | Connection keepalive during long processing |
| `answer_saved` | Save confirmation + transcript |
| `answer_evaluated` | LLM score, verdict, feedback (background) |
| `global_evaluation` | Final report + hiring decision |
| `interview_completed` | Interview ended + closing audio → triggers recruiter notification |
| `error` | Error message + `error_type` |

---

## ⚙️ Configuration

Copy `.env.example` → `.env` and fill in:

```bash
# ── MongoDB ───────────────────────────────
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sparkhire_ai
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">

# ── ASR ───────────────────────────────────
ASR_ENGINE=faster-whisper          # or: vosk
WHISPER_MODEL_SIZE=medium          # tiny | base | small | medium | large-v3

# GPU (NVIDIA CUDA) — recommandé
WHISPER_DEVICE=cuda                # cuda | cpu
WHISPER_COMPUTE_TYPE=float16       # float16 (GPU) | int8 (CPU)

# ── TTS ───────────────────────────────────
TTS_ENGINE=edge-tts                # edge-tts (default) | gtts
TTS_LANGUAGE=fr                    # ar | fr | en

# ── LLM ───────────────────────────────────
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2              # llama3.2 | llama3 | mistral ...
OLLAMA_TIMEOUT=60.0

# ── Avatar ────────────────────────────────
# simple | liveportrait | wav2lip | did
# (liveportrait, wav2lip, did → mode simple automatiquement si non implémenté)
AVATAR_PROVIDER=simple

# ── Client ────────────────────────────────
WEBSOCKET_URL=ws://localhost:8000
API_BASE_URL=http://localhost:8000

# ── Windows only ──────────────────────────
KMP_DUPLICATE_LIB_OK=TRUE
```

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Backend | FastAPI 0.115 + Uvicorn | REST API + WebSocket ASGI |
| Database | MongoDB 7 / PyMongo 4.10 | Data persistence |
| ASR | faster-whisper 1.0.3 | Primary speech transcription (GPU) |
| ASR | Vosk 0.3.45 | Offline transcription fallback |
| TTS | Edge-TTS 6.1 | Microsoft TTS — primary engine |
| TTS | gTTS 2.5.3 | Google TTS — automatic fallback |
| LLM | Ollama + Llama 3.2 | AI answer evaluation (strict grading, GPU) |
| GPU | CTranslate2 4.4.0 + PyTorch CUDA | Whisper GPU acceleration |
| Auth | python-jose + bcrypt 4.2 | JWT + password hashing |
| Client | PySide6 6.7 | Qt GUI framework |
| Client | pygame 2.6 + OpenCV 4.10 | Audio playback (24kHz) + avatar video |
| Audio | PyAudio 0.2 + pydub 0.25 | Microphone capture + MP3→WAV conversion |

---

## 📊 Evaluation Grading Scale

| Score | Verdict | Meaning |
|---|---|---|
| 9–10 | Excellent | Exceptional answer, precise, with concrete examples and rare technical mastery |
| 7–8 | Very Good | Good answer but lacking depth or specific examples |
| 5–6 | Acceptable | Superficial or vague, notable inaccuracies |
| 3–4 | Poor | Weak answer, errors or partial understanding |
| 0–2 | Insufficient | Incorrect, off-topic, or empty |

> A generic or vague answer scores no more than **5/10**. A follow-up question is automatically triggered when the score is below **8**.

---

## ✅ Hiring Decision

| Score /10 | Decision | Color |
|---|---|---|
| ≥ 7.0 | ✅ Accepted | Green |
| 5.0 – 6.9 | 🟡 On Hold | Amber |
| < 5.0 | ❌ Rejected | Red |

---

## 📤 Available Exports

| Endpoint | Format | Content |
|---|---|---|
| `GET /export/candidates/csv` | CSV | All candidates with skills, languages, certifications |
| `GET /export/interviews/csv` | CSV | All sessions with average score |
| `GET /export/interviews/{id}/json` | JSON | Full details of one interview |
| `GET /export/evaluations/csv` | CSV | All LLM evaluations per question |

---

## 📈 Analytics Endpoints

| Endpoint | Description |
|---|---|
| `GET /analytics/dashboard` | All stats combined |
| `GET /analytics/candidates` | Candidate stats + top skills |
| `GET /analytics/interviews` | Interview stats + completion rate |
| `GET /analytics/scheduling` | Total planned / this week / confirmed / pending |
| `GET /analytics/scores` | Accepted / Rejected KPIs + 6-month trend + score distribution |
| `GET /analytics/positions/scores` | Excellent/Good/Average/Weak per job position |
| `GET /analytics/system` | System health + storage |

---

## 🐛 Common Issues

| Error | Cause | Fix |
|---|---|---|
| `float16 compute type not supported` | `WHISPER_DEVICE=cpu` avec `float16` | Mettre `WHISPER_COMPUTE_TYPE=int8` sur CPU, ou `WHISPER_DEVICE=cuda` sur GPU |
| `Extra inputs are not permitted` | Unknown variable in `.env` | Already fixed — `extra = "ignore"` in `Settings.Config` |
| `OMP: Error #15 (libiomp5md)` | OpenMP conflict PyTorch / ctranslate2 | Add `KMP_DUPLICATE_LIB_OK=TRUE` to `.env` |
| `torch.cuda.is_available() = False` | PyTorch installé sans CUDA | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| `CUDA support []` dans ctranslate2 | ctranslate2 sans CUDA | `pip install ctranslate2==4.4.0 faster-whisper==1.0.3` |
| `PyAudio: No module found` | PortAudio not installed | Windows: `pipwin install pyaudio` / Linux: `sudo apt install portaudio19-dev` |
| `ffmpeg not found` | FFmpeg not in PATH | Windows: extract to `models/ffmpeg-*/` / Linux: `sudo apt install ffmpeg` |
| `Connection refused :11434` | Ollama not running | Run `ollama serve` in a separate terminal |
| `MongoDB timeout` | MongoDB service stopped | Windows: `net start MongoDB` / Linux: `sudo systemctl start mongod` |
| `Empty transcription` | Audio too short or silent | VAD filter active — speak clearly for at least 1 second |
| `WebSocket disconnected` | Long TTS processing | Heartbeat maintains the connection automatically |
| `Avatar provider inconnu` | Provider non implémenté | Tous les providers inconnus → mode simple automatiquement |

---

## 🧪 Tests

```bash
python scripts/test_interview.py
```

---

## 🎓 Academic Context

This project was developed as a **Final Year Project** for the **2nd year of an Engineering Degree in Data Engineering & Decisional Systems** at ENET'Com Sfax.

It integrates key competencies from the program:

- **Data Engineering** — real-time audio pipeline, MongoDB data modeling, REST API design with FastAPI
- **AI** — speech recognition (Whisper GPU), large language model evaluation (Llama 3.2 via Ollama GPU), text-to-speech synthesis (Edge-TTS)
- **Decisional Systems** — automated scoring engine with strict grading logic, follow-up question generation, global hiring decision (Accepted / On Hold / Rejected)
- **Software Engineering** — WebSocket communication, TTS prefetch optimization, non-blocking LLM evaluation, cross-platform desktop client (PySide6), JWT authentication, CSV/JSON export, automatic recruiter notifications

---

## 📄 License

Proprietary — SparkHire AI © 2026

## 👥 Support

For any questions: zeineb.ghrab@enetcom.u-sfax.tn