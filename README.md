# 🎤 SparkHire AI — Intelligent Voice Interview Platform

Complete recruitment platform with automated voice interviews via AI avatar.

> **Pipeline:** Candidate speaks → Whisper ASR (GPU CUDA) → Llama 3.2 LLM (GPU) → Score + Real-time Feedback

---

## ✨ Features

- 🎙️ **Automated voice interviews** with animated HR avatar
- 🌍 **Trilingual** support: Arabic / French / English
- 🧠 **AI transcription** via Whisper (faster-whisper) — GPU-accelerated ~1-3s per answer
- 📝 **Strict AI evaluation** via Ollama + Llama 3.2 (score 0–10, rigorous grading scale)
- 🔁 **Intelligent follow-up questions** if the answer is insufficient (score < 8) — synchronous pipeline
- 📊 **Global interview report** with final hiring decision (Accepted / On Hold / Rejected)
- 🔔 **Automatic recruiter notification** — one notification per completed interview
- 🗓️ **Interview scheduling** with 30-minute late access window
- 🔊 **Text-to-speech** via Edge-TTS (Microsoft) — primary engine, instant
- 🔁 **Automatic TTS fallback** via gTTS (Google) if Edge-TTS is unavailable
- ⚡ **Real-time WebSocket** (chunked PCM audio)
- ⚡ **TTS prefetch** — next question audio generated while candidate answers current one
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

### 3. GPU support — PyTorch CUDA (recommended)

If you have an NVIDIA GPU, install PyTorch with CUDA support **before** running `pip install -r requirements.txt`:

```bash
# Check your CUDA version first
nvidia-smi

# Install PyTorch with CUDA 12.x support
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Or CUDA 11.x
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 4. Backend dependencies

```bash
pip install -r requirements.txt
```

> ✅ `requirements.txt` includes `nvidia-cudnn-cu12==8.9.7.29` which automatically
> provides the `cudnn_ops_infer64_8.dll` required by ctranslate2 on Windows.
> No manual cuDNN installation needed.

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

### 5. Client dependencies

```bash
pip install -r client/requirements.txt
```

### 6. Verify GPU support

```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| Version:', torch.version.cuda)"
python -c "import ctranslate2; print('cuDNN compute types:', ctranslate2.get_supported_compute_types('cuda'))"
```

Expected output:
```
CUDA: True | Version: 12.x
cuDNN compute types: ['int8', 'int8_float16', 'float16', 'bfloat16', 'float32']
```

### 7. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Configuration](#%EF%B8%8F-configuration) below).

### 8. Download the Whisper model

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

### 9. Ollama LLM model

```bash
# Start the Ollama server (separate terminal)
ollama serve

# Download Llama 3.2 (recommended — 2.8 GB)
ollama pull llama3.2

# Alternative if RAM < 8 GB
ollama pull llama3:8b-instruct-q4_0   # 2.3 GB
```

> Verify Ollama is using GPU:
> ```bash
> ollama ps
> # Should show: 100% GPU
> ```

### 10. Database setup

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
GPU détecté : NVIDIA GeForce RTX XXXX | VRAM=X.X GB
Whisper 'medium' prêt sur CUDA
TTS Service prêt | primaire=EdgeEngine | fallback=GoogleEngine
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

## ⚡ Performance (RTX 4050 Laptop 6.4 GB)

| Component | CPU mode | GPU mode |
|---|---|---|
| Whisper ASR (medium) | 5–10s | **~1–3s** |
| Ollama LLM (llama3.2) | 15–30s | **~2–8s** |
| Edge-TTS | ~1s | ~1s (network) |
| **Total per question** | **25–45s** | **~5–12s** |

**VRAM usage:**
- Whisper medium (float16): ~1.5 GB
- llama3.2: ~2.8 GB
- Total: ~4.3 GB / 6.4 GB

---

## 📝 Usage

### 1. Create an interview (API)

```bash
# Login → get JWT token
curl -X POST http://localhost:8000/auth/login \
  -d "username=rh@stark.tn&password=admin123"

# Create a candidate (all 6 fields required)
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
# The recruiter email (from JWT) is automatically stored in created_by
# → one notification will be sent to this email when the interview ends
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
8. If score < 8 → a follow-up question is automatically asked
9. A global report with hiring decision is displayed at the end

### 3. View results & notifications

```bash
# Recruiter notifications (unread badge)
GET http://localhost:8000/notifications/unread-count

# List all unread notifications
GET http://localhost:8000/notifications/?unread_only=true

# Mark a notification as read
PATCH http://localhost:8000/notifications/<notification_id>
      Body: { "read": true }

# Full session details
GET http://localhost:8000/interviews/sessions/<session_id>

# LLM evaluation + hiring decision
GET http://localhost:8000/evaluations/<session_id>

# Test notification system
python scripts/test_notification.py
```

---

## 🔔 Recruiter Notification System

When a candidate completes an interview, the platform automatically notifies the recruiter who created the session — **exactly one notification** per completed interview.

### How it works

```
Interview ends (last answer + follow-up if score < 8)
        │
        ▼
 InterviewSessionCRUD.update_status("completed")
        │
        └── _send_completion_notification(session_id)  ← inside CRUD
                ├── Reads created_by (recruiter email stored at session creation)
                ├── Fallback: notifies ALL recruiters if created_by is empty
                ├── Loads candidate name + position title from MongoDB
                └── INSERT into db.notifications:
                      {
                        "type": "interview_completed",
                        "title": "Entretien complété",
                        "message": "Le candidat Ahmed Ben Ali a complété son
                                    entretien pour le poste Data Scientist.
                                    Veuillez le consulter.",
                        "priority": "high",
                        "read": false
                      }
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
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/
│   ├── candidates/
│   ├── interviews/
│   │   ├── crud.py            ← _send_completion_notification() ici
│   │   ├── models.py
│   │   └── routes.py          ← created_by auto-filled from JWT
│   ├── evaluation/
│   ├── services/
│   │   ├── asr_service.py     ← Whisper GPU + cuDNN path fix
│   │   ├── tts_service.py
│   │   ├── edge_tts_engine.py
│   │   ├── llm_service.py
│   │   └── avatar_service.py
│   ├── websocket/
│   │   ├── connection_manager.py
│   │   └── interview_handler.py  ← pipeline synchrone + follow-up + prefetch TTS
│   ├── notifications/
│   ├── media/
│   ├── analytics/
│   └── export/
│
├── client/
│   ├── config.py
│   ├── main.py
│   ├── core/
│   └── ui/
│
├── scripts/
│   ├── create_admin.py
│   ├── seed_job_positions.py
│   ├── download_whisper.py
│   ├── test_interview.py
│   ├── test_notification.py     ← test automatique du système de notification
│   └── debug_notification.py   ← diagnostic MongoDB
│
├── models/
├── uploads/
├── assets/videos/
├── .env
├── .env.example
├── requirements.txt
└── client/requirements.txt
```

---

## ⚙️ Configuration

```bash
# ── MongoDB ───────────────────────────────
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sparkhire_ai
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">

# ── ASR ───────────────────────────────────
ASR_ENGINE=faster-whisper
WHISPER_MODEL_SIZE=medium

# GPU (NVIDIA CUDA) — recommandé
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# CPU fallback
# WHISPER_DEVICE=cpu
# WHISPER_COMPUTE_TYPE=int8

# ── TTS ───────────────────────────────────
TTS_ENGINE=edge-tts
TTS_LANGUAGE=fr

# ── LLM ───────────────────────────────────
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120.0

# ── Avatar ────────────────────────────────
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
| ASR | faster-whisper 1.0.3 + ctranslate2 4.4.0 | GPU transcription (~1-3s) |
| cuDNN | nvidia-cudnn-cu12 8.9.7.29 | cuDNN 8 DLLs for Windows GPU |
| TTS | Edge-TTS 6.1 | Microsoft TTS — primary engine |
| TTS | gTTS 2.5.3 | Google TTS — automatic fallback |
| LLM | Ollama + Llama 3.2 | AI answer evaluation (GPU) |
| Auth | python-jose + bcrypt 4.2 | JWT + password hashing |
| Client | PySide6 6.7 | Qt GUI framework |
| Client | pygame 2.6 + OpenCV 4.10 | Audio playback + avatar video |
| Audio | PyAudio 0.2 + pydub 0.25 | Microphone capture + conversion |

---

## 📊 Evaluation Grading Scale

| Score | Verdict | Meaning |
|---|---|---|
| 9–10 | Excellent | Exceptional answer, precise, with concrete examples |
| 7–8 | Very Good | Good answer but lacking depth or specific examples |
| 5–6 | Acceptable | Superficial or vague, notable inaccuracies |
| 3–4 | Poor | Weak answer, errors or partial understanding |
| 0–2 | Insufficient | Incorrect, off-topic, or empty |

> A score below **8** automatically triggers a follow-up question (synchronous pipeline).

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
| `GET /analytics/scores` | Accepted / Rejected KPIs + 6-month trend |
| `GET /analytics/positions/scores` | Score distribution per job position |
| `GET /analytics/system` | System health + storage |

---

## 🐛 Common Issues

| Error | Cause | Fix |
|---|---|---|
| `Could not locate cudnn_ops_infer64_8.dll` | cuDNN 8 manquant | Inclus dans `requirements.txt` via `nvidia-cudnn-cu12==8.9.7.29` |
| `float16 compute type not supported` | CPU avec `float16` | `WHISPER_COMPUTE_TYPE=int8` sur CPU |
| `Extra inputs are not permitted` | Variable inconnue dans `.env` | `extra = "ignore"` déjà dans `Settings.Config` |
| `OMP: Error #15` | Conflit OpenMP | `KMP_DUPLICATE_LIB_OK=TRUE` dans `.env` |
| `torch.cuda.is_available() = False` | PyTorch sans CUDA | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| `PyAudio: No module found` | PortAudio manquant | Windows: `pipwin install pyaudio` |
| `ffmpeg not found` | FFmpeg absent | Windows: extraire dans `models/ffmpeg-*/` |
| `Connection refused :11434` | Ollama arrêté | `ollama serve` dans un terminal séparé |
| `MongoDB timeout` | Service arrêté | Windows: `net start MongoDB` |
| `Empty transcription` | Audio trop court | Parler clairement ≥ 1 seconde |
| `Notification not created` | `created_by` vide (anciennes sessions) | Fallback actif — tous les recruteurs notifiés |
| `LLM JSON parse warning` | llama3.2 tronque sa réponse | `OLLAMA_TIMEOUT=120.0` dans `.env` |

---

## 🧪 Tests

```bash
# Test du flow complet
python scripts/test_interview.py

# Test du système de notification uniquement
python scripts/test_notification.py

# Diagnostic MongoDB (connexion, collections, sessions)
python scripts/debug_notification.py
```

---

## 🎓 Academic Context

This project was developed as a **Final Year Project** for the **2nd year of an Engineering Degree in Data Engineering & Decisional Systems** at ENET'Com Sfax.

- **Data Engineering** — real-time audio pipeline, MongoDB data modeling, REST API design with FastAPI
- **AI** — speech recognition (Whisper GPU), large language model evaluation (Llama 3.2 via Ollama GPU), text-to-speech synthesis (Edge-TTS)
- **Decisional Systems** — automated scoring engine, follow-up question generation, global hiring decision (Accepted / On Hold / Rejected)
- **Software Engineering** — WebSocket communication, TTS prefetch, synchronous follow-up pipeline, JWT authentication, automatic recruiter notifications

---

## 📄 License

Proprietary — SparkHire AI © 2026

## 👥 Support

For any questions: zeineb.ghrab@enetcom.u-sfax.tn