# 🎤 SparkHire AI — Intelligent Voice Interview Platform

Complete recruitment platform with automated voice interviews via AI avatar.

> **Pipeline:** Candidate speaks → Whisper ASR (GPU CUDA) → Llama 3.2 LLM (GPU) → Weighted Score + Real-time Feedback

---

## ✨ Features

- 🎙️ **Automated voice interviews** with animated HR avatar
- 🌍 **Trilingual** support: Arabic / French / English
- 🧠 **AI transcription** via Whisper (faster-whisper) — GPU-accelerated ~1–3 s per answer
- ⚖️ **Weighted questions** — each question carries a configurable weight for a fair weighted average score
- 📝 **Strict AI evaluation** via Ollama + Llama 3.2 (score 0–10, rigorous grading scale)
- 🔁 **Intelligent follow-up questions** if the answer is insufficient (score < 8) — synchronous pipeline
- 📊 **Global interview report** with final hiring decision (Accepted / On Hold / Rejected)
- 🔔 **Automatic recruiter notification** — one notification per completed interview
- 🗓️ **Interview scheduling** with 30-minute late access window
- 🔄 **Welcome back on reconnection** — session resumes at the current question if `in_progress`
- 🎛️ **Auto-start recording** — recording begins automatically after each question audio ends; candidate stops when ready
- ⏱️ **Per-question response timer** — configurable max duration (default 1 min 30 s) with countdown and auto-stop
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

### 5. Client dependencies

```bash
pip install -r client/requirements.txt
```

### 6. Verify GPU support

```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| Version:', torch.version.cuda)"
python -c "import ctranslate2; print('cuDNN compute types:', ctranslate2.get_supported_compute_types('cuda'))"
```

### 7. Configure `.env`

```bash
cp .env.example .env
```

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

### 9. Ollama LLM model

```bash
ollama serve
ollama pull llama3.2
```

### 10. Database setup

```bash
python scripts/create_admin.py
python scripts/seed_job_positions.py
```

---

## ▶️ Running the App

### Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### PySide6 Client

```bash
python -m client.main
```

---

## ⚡ Performance (RTX 4050 Laptop 6.4 GB)

| Component | CPU mode | GPU mode |
|---|---|---|
| Whisper ASR (medium) | 5–10 s | **~1–3 s** |
| Ollama LLM (llama3.2) | 15–30 s | **~2–8 s** |
| Edge-TTS | ~1 s | ~1 s (network) |
| **Total per question** | **25–45 s** | **~5–12 s** |

---

## ⚖️ Weighted Scoring

Each question carries a configurable `weight` (default `1.0`, range `0.1–10.0`).

The final `average_score` is the **weighted average**:

```
average_score = Σ(score_i × weight_i) / Σ(weight_i)
```

The weight is defined per question when creating a job position and is stored in each answer evaluation for full auditability.

**Example with 3 questions (weights 1, 2, 3) :**

| Question | Score | Weight | Contribution |
|---|---|---|---|
| Q1 — Presentation | 8/10 | 1.0 | 8 |
| Q2 — ML tools | 6/10 | 2.0 | 12 |
| Q3 — Missing data | 7/10 | 3.0 | 21 |
| **Total** | | **6.0** | **41** |
| **Weighted avg** | | | **41/6 = 6.83** |

---

## ⏱️ Response Timer

Each question has a configurable `max_duration_seconds` (default **90 seconds = 1 min 30 s**).

- Recording **starts automatically** when the question audio finishes
- A countdown is displayed during recording (grey → orange ≤ 30 s → red ≤ 10 s)
- Recording **stops automatically** at 0 s
- The candidate can **stop manually at any time** by clicking the stop button
- The duration badge is shown only when a question is active (hidden during welcome / welcome back)

---

## 📝 Usage

### 1. Create a job position with weighted questions (API)

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=rh@stark.tn&password=admin123"

curl -X POST http://localhost:8000/interviews/positions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Data Scientist",
    "department": "Tech",
    "location": "Sfax",
    "is_active": true,
    "questions": [
      {
        "order": 1,
        "weight": 1.0,
        "max_duration_seconds": 90,
        "question_fr": "Parlez-moi de vous et de votre expérience en data science.",
        "question_en": "Tell me about yourself and your data science experience.",
        "question_ar": "أخبرني عن نفسك وعن تجربتك في علم البيانات.",
        "evaluation_criteria": ["clarté", "expérience", "motivation"]
      },
      {
        "order": 2,
        "weight": 2.0,
        "max_duration_seconds": 90,
        "question_fr": "Quels outils ML avez-vous utilisés ? Donnez un exemple concret.",
        "question_en": "What ML tools have you used? Give a concrete example.",
        "question_ar": "ما هي أدوات تعلم الآلة التي استخدمتها؟",
        "evaluation_criteria": ["maîtrise technique", "exemples concrets"]
      },
      {
        "order": 3,
        "weight": 3.0,
        "max_duration_seconds": 90,
        "question_fr": "Comment gérez-vous les données manquantes ?",
        "question_en": "How do you handle missing data?",
        "question_ar": "كيف تتعامل مع البيانات المفقودة؟",
        "evaluation_criteria": ["méthodes", "justification"]
      }
    ]
  }'
```

### 2. Create a session

```bash
curl -X POST http://localhost:8000/interviews/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "<id>",
    "job_position_id": "<id>",
    "language": "fr"
  }'
```

### 3. Take the interview (Client)

1. `python -m client.main`
2. Select interview language
3. Enter the `session_id`
4. Click **Start Interview**
5. Listen to the avatar — recording starts automatically when the question ends
6. Answer — click **Stop** when done (or let the 90 s timer stop automatically)
7. Score, verdict and feedback appear in real time
8. If score < 8 → a follow-up question is automatically asked
9. Global report with hiring decision displayed at the end

> **Reconnection:** if the connection drops mid-interview, reconnect with the same `session_id`. The platform resumes at the current question with a "Welcome back" message.

---

## 📊 Evaluation Document

```json
{
  "session_id": "session_xxx",
  "candidate_name": "Ahmed Ben Ali",
  "position_title": "Data Scientist",
  "language": "fr",
  "total_questions": 3,
  "answered_questions": 3,
  "average_score": 6.83,
  "decision": "pending",
  "decision_label": "En attente",
  "decision_color": "#F59E0B",
  "decision_reason": "Moyenne pondérée de 6.83/10 sur 3 question(s).",
  "recommendation": "En attente",
  "key_strengths": ["..."],
  "key_improvements": ["..."],
  "summary": "...",
  "per_answer": [
    {
      "question_order": 1,
      "score": 8.0,
      "weight": 1.0,
      "verdict": "Très bien",
      "feedback": "...",
      "had_followup": false
    }
  ]
}
```

> **Note:** `global_verdict` has been removed — `average_score` + `decision` + `decision_label` carry all necessary information without redundancy.

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
> The follow-up "Let's move to the next question" message is **not played after the last question**.

---

## ✅ Hiring Decision

| Score /10 | Decision | Color |
|---|---|---|
| ≥ 7.0 | ✅ Accepted | Green `#10B981` |
| 5.0 – 6.9 | 🟡 On Hold | Amber `#F59E0B` |
| < 5.0 | ❌ Rejected | Red `#EF4444` |

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
│   │   ├── crud.py            ← _send_completion_notification()
│   │   ├── models.py          ← Question.weight + max_duration_seconds=90
│   │   └── routes.py
│   ├── evaluation/
│   │   ├── models.py          ← GlobalEvaluation (no global_verdict)
│   │   ├── service.py         ← weighted average + guaranteed fields
│   │   └── routes.py
│   ├── services/
│   │   ├── asr_service.py
│   │   ├── tts_service.py
│   │   ├── edge_tts_engine.py
│   │   ├── llm_service.py     ← generate_global_summary (weighted, no global_verdict)
│   │   └── avatar_service.py  ← simple | did only (wav2lip/liveportrait removed)
│   ├── websocket/
│   │   ├── connection_manager.py
│   │   └── interview_handler.py  ← welcome_back + no followup_thanks on last Q
│   ├── notifications/
│   ├── analytics/
│   └── export/
│
├── client/
│   ├── config.py
│   ├── main.py
│   ├── core/
│   └── ui/
│       ├── main_window.py         ← pre_init pygame + welcome_back handling
│       ├── interview_widget.py    ← auto-start recording + countdown 90 s
│       └── video_player_widget.py ← no bare pygame.init()
│
├── scripts/
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
# ── MongoDB ───────────────────────────────────────────────
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sparkhire_ai
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">

# ── ASR ───────────────────────────────────────────────────
ASR_ENGINE=faster-whisper
WHISPER_MODEL_SIZE=medium
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# ── TTS ───────────────────────────────────────────────────
TTS_ENGINE=edge-tts
TTS_LANGUAGE=fr

# ── LLM ───────────────────────────────────────────────────
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120.0

# ── Avatar ────────────────────────────────────────────────
# Valeurs valides : simple | did
AVATAR_PROVIDER=simple

# ── Client ────────────────────────────────────────────────
WEBSOCKET_URL=ws://localhost:8000
API_BASE_URL=http://localhost:8000

# ── Windows only ──────────────────────────────────────────
KMP_DUPLICATE_LIB_OK=TRUE
```

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|---|---|---|
| Backend | FastAPI 0.115 + Uvicorn | REST API + WebSocket ASGI |
| Database | MongoDB 7 / PyMongo 4.10 | Data persistence |
| ASR | faster-whisper 1.0.3 + ctranslate2 4.4.0 | GPU transcription (~1–3 s) |
| cuDNN | nvidia-cudnn-cu12 8.9.7.29 | cuDNN 8 DLLs for Windows GPU |
| TTS | Edge-TTS 6.1 | Microsoft TTS — primary engine |
| TTS | gTTS 2.5.3 | Google TTS — automatic fallback |
| LLM | Ollama + Llama 3.2 | AI answer evaluation (GPU) |
| Auth | python-jose + bcrypt 4.2 | JWT + password hashing |
| Client | PySide6 6.7 | Qt GUI framework |
| Client | pygame 2.6 + OpenCV 4.10 | Audio playback + avatar video |
| Audio | PyAudio 0.2 + pydub 0.25 | Microphone capture + conversion |

---

## 📤 Available Exports

| Endpoint | Format | Content |
|---|---|---|
| `GET /export/candidates/csv` | CSV | All candidates with skills, languages, certifications |
| `GET /export/interviews/csv` | CSV | All sessions with weighted average score |
| `GET /export/interviews/{id}/json` | JSON | Full details of one interview (includes weights) |
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

## 🔔 Recruiter Notification System

When a candidate completes an interview, the platform automatically notifies the recruiter who created the session — **exactly one notification** per completed interview.

| Endpoint | Description |
|---|---|
| `GET /notifications/unread-count` | Badge counter for the recruiter UI |
| `GET /notifications/` | List all notifications |
| `PATCH /notifications/{id}` | Mark a single notification as read |
| `POST /notifications/mark-all-read` | Mark all notifications as read |
| `DELETE /notifications/{id}` | Delete a notification |

---

## 🐛 Common Issues

| Error | Cause | Fix |
|---|---|---|
| `# channels not specified` | Double pygame mixer init | Fixed via `pygame.mixer.pre_init()` at module level in `main_window.py` |
| `Could not locate cudnn_ops_infer64_8.dll` | cuDNN 8 missing | Included via `nvidia-cudnn-cu12==8.9.7.29` in `requirements.txt` |
| `float16 compute type not supported` | CPU with `float16` | Set `WHISPER_COMPUTE_TYPE=int8` for CPU |
| `OMP: Error #15` | OpenMP conflict | Set `KMP_DUPLICATE_LIB_OK=TRUE` in `.env` |
| `torch.cuda.is_available() = False` | PyTorch without CUDA | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| `PyAudio: No module found` | PortAudio missing | Windows: `pipwin install pyaudio` |
| `ffmpeg not found` | FFmpeg absent | Windows: extract to `models/ffmpeg-*/` |
| `Connection refused :11434` | Ollama stopped | Run `ollama serve` in a separate terminal |
| `MongoDB timeout` | Service stopped | Windows: `net start MongoDB` |
| `Empty transcription` | Audio too short | Speak clearly for at least 1 second |
| `Notification not created` | `created_by` empty (old sessions) | Fallback active — all recruiters notified |
| `LLM JSON parse warning` | llama3.2 truncates response | Set `OLLAMA_TIMEOUT=120.0` in `.env` |

---

## 🧪 Tests

```bash
# Full flow test
python scripts/test_interview.py

# Notification system test
python scripts/test_notification.py

# MongoDB diagnostic
python scripts/debug_notification.py
```

---

## 🎓 Academic Context

This project was developed as a **Final Year Project** for the **2nd year of an Engineering Degree in Data Engineering & Decisional Systems** at ENET'Com Sfax.

- **Data Engineering** — real-time audio pipeline, MongoDB data modeling, REST API design with FastAPI
- **AI** — speech recognition (Whisper GPU), large language model evaluation (Llama 3.2 via Ollama GPU), text-to-speech synthesis (Edge-TTS)
- **Decisional Systems** — weighted scoring engine, follow-up question generation, global hiring decision
- **Software Engineering** — WebSocket communication, TTS prefetch, synchronous follow-up pipeline, JWT authentication, automatic recruiter notifications

---

## 📄 License

Proprietary — SparkHire AI © 2026

## 👥 Support

For any questions: zeineb.ghrab@enetcom.u-sfax.tn