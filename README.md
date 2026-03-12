# 🎤 SparkHire AI — Intelligent Voice Interview Platform

Complete recruitment platform with automated voice interviews via AI avatar.

> **Pipeline:** Candidate speaks → Whisper ASR → Llama 3 LLM → Score + Real-time Feedback

---

## ✨ Features

- 🎙️ **Automated voice interviews** with animated HR avatar
- 🌍 **Trilingual** support: Arabic / French / English
- 🧠 **AI transcription** via Whisper (faster-whisper) — high accuracy
- 📝 **Strict AI evaluation** via Ollama + Llama 3 (score 0–10, rigorous grading scale)
- 🔁 **Intelligent follow-up questions** if the answer is insufficient (score < 8)
- 📊 **Global interview report** with hiring recommendation
- 🔊 **Text-to-speech** via Edge-TTS (Microsoft) — primary engine, instant
- 🔁 **Automatic TTS fallback** via gTTS (Google) if Edge-TTS is unavailable
- ⚡ **Real-time WebSocket** (chunked PCM audio)
- 🔐 **JWT authentication** for recruiters
- 🖥️ **PySide6 client interface** (glassmorphism design)
- 🗃️ **MongoDB** — candidates, positions, sessions, evaluations
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

> ⚠️ **Linux — PyAudio:** if PortAudio error:
> ```bash
> sudo apt install portaudio19-dev python3-dev
> pip install pyaudio
> ```

### 4. Client dependencies

```bash
pip install -r client/requirements.txt
```

### 5. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Configuration](#%EF%B8%8F-configuration) below).

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

### 8. Database setup

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
6. Click **Record** → speak → **Stop**
7. Score and feedback appear in real time after each answer
8. A global report is displayed at the end of the interview

### 3. View results

```bash
# Full session details
GET http://localhost:8000/interviews/sessions/<session_id>

# LLM evaluation
GET http://localhost:8000/evaluations/<session_id>

# Export all evaluations as CSV
GET http://localhost:8000/export/evaluations/csv

# Automated full-flow test
python scripts/test_interview.py
```

---

## 📂 Project Structure

```
sparkhire-ai/
│
├── backend/                        ← FastAPI backend
│   ├── main.py                     ← Entry point + lifespan + routes
│   ├── config.py                   ← Pydantic Settings (all parameters)
│   ├── database.py                 ← MongoDB connection
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
│   ├── evaluation/                 ← LLM evaluation pipeline
│   │   ├── models.py               ← AnswerEvaluation, GlobalEvaluation
│   │   ├── service.py              ← EvaluationService (ASR → LLM orchestration)
│   │   └── routes.py               ← /evaluations CRUD + trigger + health
│   │
│   ├── services/                   ← Core services
│   │   ├── asr_service.py          ← WhisperASR + VoskASR + factory
│   │   ├── tts_service.py          ← TTSService (Edge-TTS → gTTS fallback, cross-platform)
│   │   ├── edge_tts_engine.py      ← Microsoft Edge-TTS (Arabic / FR / EN voices)
│   │   ├── llm_service.py          ← OllamaLLMService (Llama 3, strict grading)
│   │   └── avatar_service.py       ← AvatarService (simple / wav2lip / did)
│   │
│   ├── websocket/                  ← Real-time communication
│   │   ├── connection_manager.py   ← ConnectionManager + heartbeat keepalive
│   │   └── interview_handler.py    ← Full pipeline per session
│   │
│   ├── media/                      ← File upload / download
│   ├── analytics/                  ← Dashboard stats (candidates, interviews, system)
│   ├── notifications/              ← Notification system
│   └── export/                     ← CSV (candidates, interviews, evaluations) + JSON
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
│       ├── main_window.py          ← Main window (pygame 24000 Hz)
│       ├── interview_widget.py     ← Interview controls + progress
│       └── video_player_widget.py  ← Avatar video (cv2 + pygame)
│
├── scripts/
│   ├── create_admin.py             ← Create admin recruiter in DB
│   ├── seed_job_positions.py       ← Insert positions + questions
│   ├── download_whisper.py         ← Download Whisper model
│   └── test_interview.py           ← Full flow automated test
│
├── models/                         ← AI models (gitignored)
│   ├── whisper/                    ← Whisper model files
│   └── vosk-model-ar/              ← Arabic Vosk model (optional)
│
├── uploads/                        ← Runtime files (gitignored)
│   ├── interviews/                 ← WAV recordings of answers
│   └── tts_cache/                  ← TTS audio cache (MD5, per engine)
│
├── assets/videos/                  ← Avatar videos (idle / speaking / listening)
│
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
| `answer_evaluated` | LLM score, verdict, feedback |
| `followup_question` | Follow-up question if score < 8 |
| `global_evaluation` | Final interview report |
| `interview_completed` | Interview ended + closing audio |
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
WHISPER_DEVICE=cpu                 # cpu | cuda
WHISPER_COMPUTE_TYPE=int8          # int8 (CPU) | float16 (GPU)

# ── TTS ───────────────────────────────────
TTS_ENGINE=edge-tts                # edge-tts (default) | gtts
TTS_LANGUAGE=ar                    # ar | fr | en

# ── LLM ───────────────────────────────────
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=60.0

# ── Avatar ────────────────────────────────
AVATAR_PROVIDER=simple             # or: wav2lip, did

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
| ASR | faster-whisper 1.0.3 | Primary speech transcription |
| ASR | Vosk 0.3.45 | Offline transcription fallback |
| TTS | Edge-TTS 6.1 | Microsoft TTS — primary engine |
| TTS | gTTS 2.5.3 | Google TTS — automatic fallback |
| LLM | Ollama + Llama 3 | AI answer evaluation (strict grading) |
| Auth | python-jose + bcrypt 4.2 | JWT + password hashing |
| Client | PySide6 6.7 | Qt GUI framework |
| Client | pygame 2.6 + OpenCV 4.10 | Audio playback (24kHz) + avatar video |
| Audio | PyAudio 0.2 + pydub 0.25 | Microphone capture + MP3→WAV conversion |

---

## 📊 Evaluation Grading Scale

The LLM evaluator applies a strict grading scale across all three languages:

| Score | Verdict | Meaning |
|---|---|---|
| 9–10 | Excellent | Exceptional answer, precise, with concrete examples and rare technical mastery |
| 7–8 | Very Good | Good answer but lacking depth or specific examples |
| 5–6 | Acceptable | Superficial or vague, notable inaccuracies |
| 3–4 | Poor | Weak answer, errors or partial understanding |
| 0–2 | Insufficient | Incorrect, off-topic, or empty |

> A generic or vague answer scores no more than **5/10**. A follow-up question is automatically triggered when the score is below **8**.

---

## 📤 Available Exports

| Endpoint | Format | Content |
|---|---|---|
| `GET /export/candidates/csv` | CSV | All candidates |
| `GET /export/interviews/csv` | CSV | All sessions with average score |
| `GET /export/interviews/{id}/json` | JSON | Full details of one interview |
| `GET /export/evaluations/csv` | CSV | All LLM evaluations per question |

---

## 🐛 Common Issues

| Error | Cause | Fix |
|---|---|---|
| `OMP: Error #15 (libiomp5md)` | OpenMP conflict between PyTorch and ctranslate2 (Windows) | Add `KMP_DUPLICATE_LIB_OK=TRUE` to `.env` |
| `AttributeError: WEBSOCKET_URL` | Field missing from `client/config.py` | Check `WEBSOCKET_URL=ws://localhost:8000` in `.env` |
| `PyAudio: No module found` | PortAudio not installed | Windows: `pipwin install pyaudio` / Linux: `sudo apt install portaudio19-dev` |
| `ffmpeg not found` | FFmpeg not in PATH | Windows: extract to `models/ffmpeg-*/` / Linux: `sudo apt install ffmpeg` |
| `Connection refused :11434` | Ollama not running | Run `ollama serve` in a separate terminal |
| `MongoDB timeout` | MongoDB service stopped | Windows: `net start MongoDB` / Linux: `sudo systemctl start mongod` |
| `Empty transcription` | Audio too short or silent | VAD filter active — speak clearly for at least 1 second |
| `WebSocket disconnected` | Long TTS processing | Heartbeat maintains the connection automatically |

---

## 🧪 Tests

```bash
python scripts/test_interview.py
```

---

## 🎓 Academic Context

This project was developed as a **Final Year Project** for the **2nd year of an Engineering Degree in Data Engineering & Decisional Systems**.

It integrates key competencies from the program:

- **Data Engineering** — real-time audio pipeline, MongoDB data modeling, REST API design with FastAPI
- **AI** — speech recognition (Whisper), large language model evaluation (Llama 3 via Ollama), text-to-speech synthesis (Edge-TTS)
- **Decisional Systems** — automated scoring engine with strict grading logic, follow-up question generation, global hiring recommendation
- **Software Engineering** — WebSocket communication, cross-platform desktop client (PySide6), JWT authentication, CSV/JSON export

---

## 📄 License

Proprietary — SparkHire AI © 2026

## 👥 Support

For any questions: zeineb.ghrab@enetcom.u-sfax.tn