# 🎤 Stark Recruitment — AI-Powered Voice Interview System

Complete recruitment platform with automated voice interviews via AI avatar.

> **Pipeline:** Candidate speaks → Whisper ASR → Llama 3 LLM → Score + Real-time Feedback

---

## ✨ Features

- 🎙️ **Automated voice interviews** with animated HR avatar
- 🌍 **Multilingual** support: Arabic / French / English
- 🧠 **AI transcription** via Whisper (faster-whisper) — high accuracy
- 📝 **Automatic evaluation** via Ollama + Llama 3 (score 0-10, verdict, feedback)
- 📊 **Global interview report** with hiring recommendation
- 🔊 **Text-to-speech** via Edge-TTS (Microsoft) by default, Coqui XTTS-v2 optional
- ⚡ **Real-time WebSocket** (chunked PCM audio)
- 🔐 **JWT authentication** for recruiters
- 🖥️ **PySide6 client interface** (glassmorphism design)
- 🗃️ **MongoDB database** — candidates, positions, sessions, evaluations
- 📤 **CSV / JSON export** + analytics dashboard

---

## 📋 Prerequisites

| Software | Version | Link | Notes |
|---|---|---|---|
| Python | 3.10 or 3.11 | [python.org](https://python.org) | Check **Add to PATH** |
| Git | latest | [git-scm.com](https://git-scm.com) | To clone the repo |
| MongoDB | 7.x Community | [mongodb.com](https://www.mongodb.com) | Install as a service |
| FFmpeg | 6.0+ | [ffmpeg.org](https://ffmpeg.org) | Extract to `C:\ffmpeg\`, add `bin` to PATH |
| Ollama | latest | [ollama.com](https://ollama.com/download) | Required for LLM evaluation |
| VS C++ Build Tools | 2022 | [visualstudio.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/) | To compile PyAudio on Windows |

---

## 🚀 Installation

### 1. Clone the project

```bash
git clone https://github.com/ZeinebGhrab/stark-recruitment-chatbot.git
cd stark-recruitment-chatbot
```

### 2. Virtual environment

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

### 4. Client dependencies

```bash
pip install -r client/requirements.txt
```

### 5. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Configuration](#%EF%B8%8F-configuration) section below).

### 6. Download the Whisper model

```bash
python scripts/download_whisper.py medium
```

| Size | Weight | Recommended |
|---|---|---|
| tiny | 75 MB | quick tests |
| base | 145 MB | — |
| small | 483 MB | — |
| **medium** | **1.5 GB** | ✅ **recommended** |
| large-v3 | 3.1 GB | GPU only |

The model is saved automatically in `models/whisper/`.

### 7. Ollama LLM model

```bash
# Start the Ollama server (separate terminal)
ollama serve

# Download Llama 3 (4.7 GB)
ollama pull llama3

# Alternative if RAM < 8 GB
ollama pull llama3:8b-instruct-q4_0   # 2.3 GB
```

> If you use a different model, update `OLLAMA_MODEL` in `.env`.

### 8. Database

```bash
# Create the admin recruiter account
python scripts/create_admin.py

# Insert demo positions and questions
python scripts/seed_job_positions.py
```

---

## ▶️ Running the app

### Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API: [http://localhost:8000](http://localhost:8000)
- Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### PySide6 Client

```bash
python -m client.main
```

---

## 📝 Usage

### 1. Create an interview (API)

```bash
# Login → get JWT token
curl -X POST http://localhost:8000/auth/login \
  -d "username=rh@stark.tn&password=admin123"

# Create a candidate
curl -X POST http://localhost:8000/candidates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Ahmed","last_name":"Ben Ali",
       "contact":{"email":"ahmed@example.com"},"skills":["Python"]}'

# Create an interview session
curl -X POST http://localhost:8000/interviews/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"candidate_id":"<id>","job_position_id":"<id>","language":"en"}'
```

### 2. Take the interview (Client)

1. `python -m client.main`
2. Select the interview language
3. Enter the `session_id` (format: `session_xxxxxxxxxxxxxxxx`)
4. Click **Start Interview**
5. Listen to the avatar ask questions
6. Click **Start Recording** → speak → **Stop Recording**
7. Score and feedback appear in real time after each answer
8. A global report is displayed at the end of the interview

### 3. View results

```bash
# Full session
GET http://localhost:8000/interviews/sessions/<session_id>

# LLM evaluation
GET http://localhost:8000/evaluations/<session_id>

# Automated full-flow test
python scripts/test_interview.py
```

---

## 📂 Project Structure

```
stark-recruitment-chatbot/
│
├── backend/                        ← FastAPI API
│   ├── main.py                     ← Entry point + lifespan + routes
│   ├── config.py                   ← Pydantic Settings (all parameters)
│   ├── database.py                 ← MongoDB connection
│   ├── middlewares.py              ← Logging, errors, rate-limiting
│   │
│   ├── auth/                       ← JWT authentication
│   │   ├── models.py               ← Recruiter, Token
│   │   ├── routes.py               ← POST /auth/login · GET /auth/me
│   │   └── security.py             ← bcrypt, JWT, OAuth2
│   │
│   ├── candidates/                 ← Candidate management
│   │   ├── crud.py
│   │   ├── models.py               ← Candidate, Education, Experience
│   │   └── routes.py               ← /candidates CRUD + search
│   │
│   ├── interviews/                 ← Sessions and job positions
│   │   ├── crud.py
│   │   ├── models.py               ← Question, JobPosition, Answer, InterviewSession
│   │   └── routes.py               ← /interviews/positions · /interviews/sessions
│   │
│   ├── evaluation/                 ← ★ LLM evaluation pipeline
│   │   ├── models.py               ← AnswerEvaluation, GlobalEvaluation
│   │   ├── service.py              ← EvaluationService (ASR → LLM orchestration)
│   │   └── routes.py               ← /evaluations CRUD + trigger + health
│   │
│   ├── services/                   ← Business services
│   │   ├── asr_service.py          ← WhisperASR + VoskASR + factory
│   │   ├── tts_service.py          ← Lazy TTSService (Edge-TTS → Coqui)
│   │   ├── edge_tts_engine.py      ← Microsoft Edge-TTS (Arabic voices)
│   │   ├── coqui_tts_engine.py     ← Coqui XTTS-v2 (local, optional)
│   │   ├── llm_service.py          ← OllamaLLMService (Llama 3)
│   │   └── avatar_service.py       ← AvatarService (simple / wav2lip / did)
│   │
│   ├── websocket/                  ← Real-time communication
│   │   ├── connection_manager.py   ← ConnectionManager (active sessions)
│   │   └── interview_handler.py    ← Full pipeline per session
│   │
│   ├── jobs/                       ← Job listings
│   ├── matches/                    ← CV / Position matching
│   ├── media/                      ← File upload / download
│   ├── analytics/                  ← Dashboard statistics
│   ├── notifications/              ← Notification system
│   └── export/                     ← CSV / JSON export
│
├── client/                         ← PySide6 interface
│   ├── config.py                   ← Client settings (WEBSOCKET_URL, API_BASE_URL…)
│   ├── main.py                     ← QApplication entry point
│   ├── core/
│   │   ├── models.py               ← Question, Answer, Progress (dataclasses)
│   │   ├── audio_recorder.py       ← PyAudio → WebSocket chunks
│   │   └── websocket_client.py     ← Thread-safe WebSocketClient
│   └── ui/
│       ├── stark_theme.py          ← Design system (colors, fonts, styles)
│       ├── icons.py                ← Lucide SVG icons + Stark logos
│       ├── main_window.py          ← Main window
│       ├── interview_widget.py     ← Interview controls + progress
│       └── video_player_widget.py  ← Avatar video (cv2 + pygame)
│
├── scripts/
│   ├── create_admin.py             ← Create admin recruiter in DB
│   ├── seed_job_positions.py       ← Insert positions + questions
│   ├── download_whisper.py         ← Download Whisper model
│   └── test_interview.py           ← Full flow test
│
├── models/                         ← AI models (gitignored)
│   ├── whisper/                    ← Whisper model
│   ├── vosk-model-ar/              ← Arabic Vosk model (optional)
│   └── xtts_v2/                    ← Coqui XTTS-v2 model (optional)
│
├── uploads/                        ← Runtime files (gitignored)
│   ├── interviews/                 ← WAV recordings of answers
│   └── tts_cache/                  ← TTS audio cache (MD5)
│
├── assets/videos/                  ← Avatar videos (idle / speaking / listening)
│
├── .env                            ← Environment variables (gitignored)
├── .env.example                    ← Template to copy
├── requirements.txt                ← Backend dependencies
└── client/requirements.txt         ← Client dependencies
```

---

## 🔌 WebSocket

```
ws://localhost:8000/ws/interview/{session_id}?lang=ar|fr|en
```

**Client → Server**

| Message | Description |
|---|---|
| `audio_chunk` | Base64 PCM chunk (microphone) |
| `answer_complete` | End of recording signal |
| `audio_finished` | End of audio playback on client side |
| `end_interview` | Terminate the interview |

**Server → Client**

| Message | Description |
|---|---|
| `welcome` | Welcome message + chunked PCM audio |
| `question` | Question audio + progress metadata |
| `audio_chunk_data` | Base64 PCM chunk |
| `audio_chunk_end` | End of audio stream |
| `answer_saved` | Save confirmation + transcript |
| `answer_evaluated` | LLM score, verdict, feedback |
| `global_evaluation` | Final interview report |
| `interview_completed` | Interview ended + audio |
| `error` | Error message + `error_type` |

---

## ⚙️ Configuration

Copy `.env.example` → `.env` and fill in:

```bash
# ── MongoDB ───────────────────────────────
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=stark_recruitment
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">

# ── ASR ───────────────────────────────────
ASR_ENGINE=faster-whisper          # or vosk
WHISPER_MODEL_SIZE=medium          # tiny | base | small | medium | large-v3
WHISPER_DEVICE=cpu                 # cpu | cuda
WHISPER_COMPUTE_TYPE=int8          # int8 (CPU) | float16 (GPU)

# ── TTS ───────────────────────────────────
TTS_ENGINE=edge-tts                # or coqui
TTS_LANGUAGE=ar                    # ar | fr | en

# ── LLM ───────────────────────────────────
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=60.0

# ── Avatar ────────────────────────────────
AVATAR_PROVIDER=simple             # or wav2lip, did

# ── Client ────────────────────────────────
WEBSOCKET_URL=ws://localhost:8000
API_BASE_URL=http://localhost:8000

# ── Windows OpenMP fix ────────────────────
KMP_DUPLICATE_LIB_OK=TRUE
```

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Backend | FastAPI 0.115 + Uvicorn | REST API + WebSocket ASGI |
| Database | MongoDB 7 / PyMongo 4.10 | Data storage |
| ASR | faster-whisper 1.0.3 | Main speech transcription |
| ASR | Vosk 0.3.45 | Offline transcription (fallback) |
| TTS | Edge-TTS 6.1 | Microsoft TTS (default) |
| TTS | Coqui XTTS-v2 | Local TTS (optional) |
| LLM | Ollama + Llama 3 | AI evaluation of answers |
| Auth | python-jose + bcrypt 4.2 | JWT + password hashing |
| Client | PySide6 6.7 | Qt GUI framework |
| Client | pygame 2.6 + OpenCV 4.10 | Audio playback + avatar video |
| Audio | PyAudio 0.2 + pydub 0.25 | Microphone capture + MP3→WAV |

---

## 🐛 Common Issues

| Error | Cause | Fix |
|---|---|---|
| `OMP: Error #15 (libiomp5md)` | OpenMP conflict between PyTorch and ctranslate2 | Add `KMP_DUPLICATE_LIB_OK=TRUE` to `.env` |
| `AttributeError: WEBSOCKET_URL` | Field missing from `client/config.py` | Check `WEBSOCKET_URL=ws://localhost:8000` in `.env` |
| `ValidationError: field WHISPER_DEVICE` | Duplicate field in `backend/config.py` | Remove the duplicate declaration |
| `PyAudio: No module found` | PortAudio not installed | `pip install pipwin` then `pipwin install pyaudio` |
| `ffmpeg not found` | FFmpeg not in PATH | Add `C:\ffmpeg\bin` to system PATH |
| `Connection refused :11434` | Ollama not running | Run `ollama serve` in a separate terminal |
| `MongoDB timeout` | MongoDB service stopped | `net start MongoDB` (admin PowerShell) |
| `Empty transcription` | Audio too short or silent | VAD filter active — speak clearly for at least 1 second |

---

## 🧪 Tests

```bash
python scripts/test_interview.py
```

---

## 📄 License

Proprietary — Stark Solutions © 2026

## 👥 Support

For any questions: rh@stark.tn