# 🎤 SparkHire AI — Intelligent Voice Interview Platform

Complete recruitment platform with automated voice interviews via AI avatar, real-time facial behavior analysis, and weighted LLM scoring.

> **Pipeline:** Candidate speaks → Whisper ASR (GPU CUDA) → Llama 3.2 LLM (GPU) → Weighted Score + Real-time Feedback  
> **Facial Pipeline:** Webcam → MediaPipe FaceMesh (478 landmarks) + DeepFace VGG CNN → Confidence / Stress / Engagement scores

---

## ✨ Features

- 🎙️ **Automated voice interviews** with animated HR avatar
- 🌍 **Trilingual** support: Arabic / French / English
- 🧠 **AI transcription** via Whisper (faster-whisper) — GPU-accelerated ~1–3 s per answer
- ⚖️ **Weighted questions** — each question carries a configurable weight for a fair weighted average score
- 📝 **Strict AI evaluation** via Ollama + Llama 3.2 (score 0–10, rigorous grading scale)
- 🔁 **Intelligent follow-up questions** if the answer is insufficient (score < 8) — synchronous pipeline
- 📊 **Global interview report** with final hiring decision (Accepted / On Hold / Rejected)
- 😊 **Facial behavior analysis** — real-time emotion detection + post-answer metrics
- 🎥 **Camera PiP overlay** — live webcam preview with REC badge + real-time metric bars
- 🔔 **Automatic recruiter notification** — one notification per completed interview
- 🗓️ **Interview scheduling** with 30-minute late access window
- 🔄 **Welcome back on reconnection** — session resumes at the current question if `in_progress`
- 🎛️ **Auto-start recording** — recording begins automatically after each question audio ends
- ⏱️ **Per-question response timer** — configurable max duration (default 1 min 30 s) with countdown and auto-stop
- 🔊 **Text-to-speech** via Edge-TTS 7.x (Microsoft) — primary engine, instant, retry on 403
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

### 6. ⚠️ Critical — Protobuf version for facial analysis

MediaPipe requires `protobuf<5`. Run this **after** all other installs:

```bash
pip install "protobuf>=4.25.3,<5.0.0"
```

> The `pip` resolver will warn about a conflict with TensorFlow — this is safe to ignore.  
> DeepFace works with `tf-keras` only (TensorFlow is not required and can be uninstalled):
> ```bash
> pip uninstall tensorflow -y
> ```

### 7. Verify GPU support

```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| Version:', torch.version.cuda)"
python -c "import ctranslate2; print('cuDNN compute types:', ctranslate2.get_supported_compute_types('cuda'))"
```

### 8. Configure `.env`

```bash
cp .env.example .env
```

### 9. Download the Whisper model

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

### 10. Ollama LLM model

```bash
ollama serve
ollama pull llama3.2
```

### 11. Database setup

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

**Expected startup logs:**
```
✅ Whisper 'medium' prêt sur CUDA
✅ Edge-TTS initialisé avec voix féminine naturelle
✅ MediaPipe FaceMesh | 478 landmarks + iris | EAR + solvePnP | CPU
✅ DeepFace CNN Emotion | VGG ~73% AffectNet | poids chargés
✅ LLM Ollama disponible | modèle=llama3.2
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
| DeepFace (emotion CNN) | ~40 ms/frame | ~15 ms/frame |
| MediaPipe (landmarks) | ~8 ms/frame | ~8 ms/frame (CPU only) |
| **Total per question** | **25–45 s** | **~5–12 s** |

---

## 😊 Facial Behavior Analysis

### Pipeline

```
Webcam (2 fps)
  │
  ├─► MediaPipe FaceMesh ──► 478 landmarks + iris landmarks (468-477)
  │     • EAR — Eye Aspect Ratio → blink detection (threshold 0.20)
  │     • Iris offset (lm 468/473) → precise gaze / eye contact
  │     • solvePnP 6-point → real yaw/pitch/roll angles
  │     • Lip corner ratio → smile detection
  │     • Brow raise/frown → Action Units AU1/2/4
  │
  └─► DeepFace VGG CNN ──► 7 emotions (~73% AffectNet precision)
        angry · disgust · fear · happy · sad · surprise · neutral
        ↓ fallback if unavailable
        FACS heuristics ──► 6 Action Units from landmarks
```

### Metrics produced per answer

| Metric | Range | Description |
|---|---|---|
| `confidence_score` | 0–10 | Eye contact + stability + smile − stress |
| `stress_score` | 0–10 | Brow frown + gaze avoidance + blink anomaly |
| `engagement_score` | 0–10 | Eye contact + expressiveness + brow raise |
| `eye_contact_ratio` | 0–1 | % of frames with gaze directed at camera |
| `head_stability` | 0–1 | 1.0 = perfectly stable, based on yaw/pitch std |
| `smile_ratio` | 0–1 | % of frames with detected smile |
| `blink_rate` | /min | Normal 15–20; >30 = stress; <5 = fixation |
| `dominant_emotion` | string | Most frequent emotion across the answer |

### Client-side PiP overlay

The **Camera Preview Widget** displays in the bottom-left corner of the video player:
- Live webcam feed (mirror-flipped) with green face detection border
- 4 real-time progress bars: Confidence · Stress · Eye Contact · Stability
- Emotion emoji updated live
- **● REC** blinking red badge during recording
- Post-evaluation metrics update after each answer

### Emotion accuracy comparison

| Backend | Method | Accuracy |
|---|---|---|
| FACS heuristics (fallback) | 6 Action Units from landmarks | ~60% |
| **DeepFace VGG CNN (active)** | **CNN trained on AffectNet** | **~73%** |

### DeepFace model weights

Downloaded automatically at first launch (~6 MB):
```
~/.deepface/weights/facial_expression_model_weights.h5
```
Or manually from:
```
https://github.com/serengil/deepface_models/releases/download/v1.0/facial_expression_model_weights.h5
```

---

## 🔊 TTS Engine (Edge-TTS 7.x)

Version 7.x fixes the **HTTP 403 errors** that affected version 6.1.x (revoked Microsoft token).

**Changes in 7.x API:**
```python
# 6.x (deprecated)
communicate = edge_tts.Communicate(text, voice)

# 7.x (current)
communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
```

**Retry logic:** automatic retry ×3 with progressive backoff on any network/403 error.

**Fallback chain:** Edge-TTS → gTTS (Google) — transparent, no interruption.

---

## ⚖️ Weighted Scoring

Each question carries a configurable `weight` (default `1.0`, range `0.1–10.0`).

```
average_score = Σ(score_i × weight_i) / Σ(weight_i)
```

**Example with 3 questions (weights 1, 2, 3):**

| Question | Score | Weight | Contribution |
|---|---|---|---|
| Q1 — Presentation | 8/10 | 1.0 | 8 |
| Q2 — ML tools | 6/10 | 2.0 | 12 |
| Q3 — Missing data | 7/10 | 3.0 | 21 |
| **Weighted avg** | | **6.0** | **41/6 = 6.83** |

---

## ⏱️ Response Timer

- Default: **90 seconds** per question (configurable via `max_duration_seconds`)
- Recording **starts automatically** when the question audio finishes
- Countdown: grey → orange (≤30s) → red (≤10s)
- Auto-stop at 0s; candidate can stop manually at any time

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
│   │   ├── models.py          ← Question.weight + FacialAnalysisData
│   │   └── routes.py
│   ├── evaluation/
│   │   ├── models.py          ← GlobalEvaluation + decision labels
│   │   ├── service.py         ← weighted average + facial integration
│   │   └── routes.py
│   ├── services/
│   │   ├── asr_service.py     ← Whisper GPU + CPU fallback
│   │   ├── tts_service.py     ← Edge-TTS 7.x + gTTS fallback
│   │   ├── edge_tts_engine.py ← retry ×3 + 7.x API
│   │   ├── llm_service.py     ← evaluate_with_facial()
│   │   ├── facial_analysis_service.py  ← v3.1 MediaPipe + DeepFace
│   │   └── avatar_service.py
│   ├── websocket/
│   │   ├── connection_manager.py
│   │   └── interview_handler.py  ← video_frame + facial pipeline
│   ├── notifications/
│   ├── analytics/
│   └── export/
│
├── client/
│   ├── config.py
│   ├── main.py
│   ├── core/
│   │   ├── audio_recorder.py
│   │   ├── video_recorder.py  ← VideoFrameCollector 2fps JPEG
│   │   └── websocket_client.py
│   └── ui/
│       ├── main_window.py         ← PiP overlay + facial metrics
│       ├── interview_widget.py    ← facial results panel
│       ├── video_player_widget.py ← resizeEvent → reposition overlay
│       ├── camera_preview_widget.py  ← PiP + real-time analysis
│       └── stark_theme.py
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
# Valid values : simple | did
AVATAR_PROVIDER=simple

# ── Facial Analysis ───────────────────────────────────────
FACIAL_ANALYSIS_ENABLED=true
FACIAL_CAPTURE_FPS=2.0      # frames per second sent from client
FACIAL_DEVICE=cpu           # cpu (MediaPipe is always CPU)

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
| TTS | Edge-TTS **7.2.7** | Microsoft TTS — primary engine (fixed 403) |
| TTS | gTTS 2.5.3 | Google TTS — automatic fallback |
| LLM | Ollama + Llama 3.2 | AI answer evaluation (GPU) |
| Facial | MediaPipe 0.10.14 | 478 landmarks + iris gaze + solvePnP |
| Facial | DeepFace 0.0.99 + tf-keras | CNN emotion detection ~73% AffectNet |
| Auth | python-jose + bcrypt 4.2 | JWT + password hashing |
| Client | PySide6 6.7 | Qt GUI framework |
| Client | pygame 2.6 + OpenCV 4.10 | Audio playback + avatar video + camera |
| Audio | PyAudio 0.2 + pydub 0.25 | Microphone capture + conversion |

---

## 🐛 Common Issues

| Error | Cause | Fix |
|---|---|---|
| `# channels not specified` | Double pygame mixer init | Fixed via `pygame.mixer.pre_init()` at module level |
| `Could not locate cudnn_ops_infer64_8.dll` | cuDNN 8 missing | Included via `nvidia-cudnn-cu12==8.9.7.29` |
| `float16 compute type not supported` | CPU with `float16` | Set `WHISPER_COMPUTE_TYPE=int8` for CPU |
| `OMP: Error #15` | OpenMP conflict | Set `KMP_DUPLICATE_LIB_OK=TRUE` in `.env` |
| `torch.cuda.is_available() = False` | PyTorch without CUDA | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| `Edge-TTS 403 Forbidden` | edge-tts 6.x revoked token | **Upgrade: `pip install edge-tts==7.2.7`** |
| `MediaPipe init: FieldDescriptor has no attribute 'label'` | protobuf>=5 conflict | **`pip install "protobuf>=4.25.3,<5.0.0"`** |
| `Analyse faciale timeout (N frames)` | MediaPipe failing silently | Fix protobuf above, then restart server |
| `données faciales: absentes` | MediaPipe or DeepFace not initialized | Check startup logs for ✅ messages |
| `DeepFace: download weights failed` | No internet at first launch | Download manually to `~/.deepface/weights/` |
| `PyAudio: No module found` | PortAudio missing | Windows: `pipwin install pyaudio` |
| `ffmpeg not found` | FFmpeg absent | Windows: extract to `models/ffmpeg-*/` |
| `Connection refused :11434` | Ollama stopped | Run `ollama serve` in a separate terminal |
| `MongoDB timeout` | Service stopped | Windows: `net start MongoDB` |
| `Empty transcription` | Audio too short | Speak clearly for at least 1 second |

---

## 📊 Evaluation Grading Scale

| Score | Verdict | Meaning |
|---|---|---|
| 9–10 | Excellent | Exceptional answer, precise, with concrete examples |
| 7–8 | Very Good | Good answer but lacking depth or specific examples |
| 5–6 | Acceptable | Superficial or vague, notable inaccuracies |
| 3–4 | Poor | Weak answer, errors or partial understanding |
| 0–2 | Insufficient | Incorrect, off-topic, or empty |

> A score below **8** automatically triggers a follow-up question.

---

## 📤 Available Exports

| Endpoint | Format | Content |
|---|---|---|
| `GET /export/candidates/csv` | CSV | All candidates with skills, languages, certifications |
| `GET /export/interviews/csv` | CSV | All sessions with weighted average score |
| `GET /export/interviews/{id}/json` | JSON | Full details of one interview (includes facial metrics) |
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

- **Data Engineering** — real-time audio/video pipeline, MongoDB data modeling, REST API design with FastAPI
- **AI** — speech recognition (Whisper GPU), LLM evaluation (Llama 3.2 via Ollama GPU), TTS synthesis (Edge-TTS 7.x), facial emotion CNN (DeepFace VGG)
- **Computer Vision** — MediaPipe FaceMesh (478 landmarks + iris), Eye Aspect Ratio, solvePnP head pose, gaze estimation
- **Decisional Systems** — weighted scoring engine, follow-up question generation, global hiring decision, behavioral scoring
- **Software Engineering** — WebSocket communication, TTS prefetch, JWT authentication, automatic recruiter notifications, PiP camera overlay

---

## 📄 License

Proprietary — SparkHire AI © 2026

## 👥 Support

For any questions: zeineb.ghrab@enetcom.u-sfax.tn