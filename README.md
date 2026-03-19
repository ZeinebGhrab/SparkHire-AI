# 🎤 SparkHire AI

**Intelligent Voice Interview Platform** — automated AI-powered interviews with behavioral analysis and weighted LLM scoring.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Running the App](#running-the-app)
6. [Configuration](#configuration)
7. [Architecture](#architecture)
8. [Diagrams](#diagrams)
9. [Facial Behavior Analysis](#facial-behavior-analysis)
10. [Scoring & Decisions](#scoring--decisions)
11. [WebSocket Message Contract](#websocket-message-contract)
12. [API Reference](#api-reference)
13. [Tech Stack](#tech-stack)
14. [Performance](#performance)
15. [Troubleshooting](#troubleshooting)
16. [Academic Context](#academic-context)

---

## Overview

SparkHire AI automates the first-round recruitment interview. A candidate connects via the desktop client, answers spoken questions posed by a TTS avatar, and the platform evaluates responses using a local LLM. Simultaneously, facial behavior is analyzed server-side and stored for the recruiter — the candidate never sees these metrics.

```
Candidate speaks
    │
    ├─► Whisper ASR  ──────────────────► Transcript
    │
    ├─► MediaPipe + HSEmotion  ────────► Behavioral metrics  (backend / HR only)
    │
    └─► Llama 3.2 (Ollama)  ───────────► Score 0–10 + Verdict + Follow-up
                                              │
                                              └─► MongoDB  ──► HR Report
```

**Privacy by design** — scores, feedback, and all behavioral metrics are stored in MongoDB and surfaced only in the HR report. The candidate client receives only session flow signals.

---

## Features

### Core Interview
- 🎙️ Automated voice interview with animated HR avatar
- 🌍 Trilingual: **Arabic / French / English**
- 🔁 Smart follow-up questions when answer score < 8
- ⏱️ Per-question timer (configurable, default 90 s) with auto-stop
- 🎛️ Recording starts automatically after question audio ends
- 🔄 Reconnection support — resumes at current question if `in_progress`
- 🗓️ Interview scheduling with 30-minute late access window

### AI Pipeline
- 🧠 **ASR** — faster-whisper (GPU-accelerated, ~1–3 s/answer)
- 📝 **LLM evaluation** — Ollama + Llama 3.2, strict grading scale 0–10, duration-aware scoring
- 🔊 **TTS** — Edge-TTS 7.x (primary) + gTTS (automatic fallback)
- ⚡ TTS prefetch — next question generated while candidate answers current one
- 😊 **Facial analysis** — HSEmotion EfficientNet-B0 (~82%) + MediaPipe FaceMesh

### Privacy & Data
- 🔒 All behavioral metrics stored in MongoDB — never sent to candidate
- 📊 Global HR report with per-answer facial summary + hiring decision
- 🔔 Automatic recruiter notification on interview completion

### Platform
- 🔐 JWT authentication for recruiters
- 🖥️ PySide6 desktop client (Windows / Linux / macOS)
- 🗃️ MongoDB — candidates, positions, sessions, evaluations, notifications
- 📤 CSV / JSON export + analytics dashboard

---

## Prerequisites

| Software | Version | Notes |
|---|---|---|
| Python | 3.10 or 3.11 | Add to PATH during install |
| MongoDB | 7.x Community | Run as a service |
| Ollama | latest | Required for LLM evaluation |
| FFmpeg | 6.0+ | Required only if gTTS fallback is used |
| CUDA Toolkit | 11.x or 12.x | Optional — GPU acceleration |

> **Windows only:** VS C++ Build Tools 2022 required to compile PyAudio.

---

## Installation

### 1 — Clone

```bash
git clone https://github.com/ZeinebGhrab/sparkhire-ai.git
cd sparkhire-ai
```

### 2 — Virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 3 — PyTorch (GPU recommended)

```bash
# CUDA 12.x
pip install torch --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.x
pip install torch --index-url https://download.pytorch.org/whl/cu118

# CPU only
pip install torch
```

### 4 — Backend dependencies

```bash
pip install -r requirements.txt
```

### 5 — Client dependencies

```bash
pip install -r client/requirements.txt
```

### 6 — Facial analysis stack (install in this order)

```bash
pip install timm==0.9.2
pip install efficientnet_pytorch
pip install hsemotion
pip install mediapipe==0.10.14
pip install "protobuf>=4.25.3,<5.0.0"
```

> **Why `timm==0.9.2`?**
> `timm==0.6.13` is missing `timm.layers` → `ModuleNotFoundError` at model load.
> `timm==0.9.2` is the tested stable version for HSEmotion EfficientNet-B0.

**Verify the install:**
```bash
python -c "
from hsemotion.facial_emotions import HSEmotionRecognizer
fer = HSEmotionRecognizer(model_name='enet_b0_8_best_afew', device='cpu')
print('HSEmotion OK:', fer)
"
```

### 7 — Environment file

```bash
cp .env.example .env
# Edit .env with your values — see Configuration section
```

### 8 — Download Whisper model

```bash
python scripts/download_whisper.py medium
```

| Size | Weight | Use case |
|---|---|---|
| tiny | 75 MB | Quick tests |
| base | 145 MB | — |
| small | 483 MB | — |
| **medium** | **1.5 GB** | ✅ Recommended |
| large-v3 | 3.1 GB | GPU only (6 GB+ VRAM) |

### 9 — Pull LLM

```bash
ollama serve
ollama pull llama3.2
```

### 10 — Seed database

```bash
python scripts/create_admin.py
python scripts/seed_job_positions.py
```

---

## Running the App

### Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Expected startup output:
```
✅ MediaPipe FaceMesh v5.2 | 478 landmarks + iris | CPU
✅ HSEmotion | model=enet_b0_8_best_afew | device=CPU
✅ Whisper 'medium' ready on CPU
✅ Edge-TTS initialized
✅ LLM Ollama available | model=llama3.2
```

### Desktop client

```bash
python -m client.main
```

---

## Configuration

```env
# ── MongoDB ────────────────────────────────────────────────────────────
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sparkhire_ai
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">

# ── ASR ────────────────────────────────────────────────────────────────
ASR_ENGINE=faster-whisper
WHISPER_MODEL_SIZE=medium
WHISPER_DEVICE=cuda           # use cpu if no GPU
WHISPER_COMPUTE_TYPE=float16  # use int8 on CPU

# ── TTS ────────────────────────────────────────────────────────────────
TTS_ENGINE=edge-tts
TTS_LANGUAGE=fr

# ── LLM ────────────────────────────────────────────────────────────────
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120.0

# ── Avatar ─────────────────────────────────────────────────────────────
AVATAR_PROVIDER=simple        # simple | did

# ── Facial Analysis ────────────────────────────────────────────────────
FACIAL_ANALYSIS_ENABLED=true
FACIAL_CAPTURE_FPS=2.0        # frames/s sent from client
FACIAL_DEVICE=cpu             # MediaPipe is always CPU

# ── Client ─────────────────────────────────────────────────────────────
WEBSOCKET_URL=ws://localhost:8000
API_BASE_URL=http://localhost:8000

# ── Windows only ───────────────────────────────────────────────────────
KMP_DUPLICATE_LIB_OK=TRUE
```

---

## Architecture

### Project structure

```
sparkhire-ai/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/
│   ├── candidates/
│   ├── interviews/
│   │   ├── crud.py                    ← completion notification trigger
│   │   ├── models.py                  ← Question.weight, FacialAnalysisData
│   │   └── routes.py
│   ├── evaluation/
│   │   ├── models.py                  ← GlobalEvaluation, FacialSummary, GlobalFacialSummary
│   │   ├── service.py                 ← weighted average + facial injection from DB
│   │   └── routes.py
│   ├── services/
│   │   ├── asr_service.py             ← Whisper GPU/CPU
│   │   ├── tts_service.py             ← Edge-TTS 7.x + gTTS fallback
│   │   ├── edge_tts_engine.py         ← retry ×3, 7.x API
│   │   ├── llm_service.py             ← evaluate_with_facial() + duration context
│   │   ├── facial_analysis_service.py ← v5.2: MediaPipe + HSEmotion
│   │   └── avatar_service.py
│   ├── websocket/
│   │   ├── connection_manager.py
│   │   └── interview_handler.py       ← video_frame handling, metrics backend-only
│   ├── notifications/
│   ├── analytics/
│   └── export/
│
├── client/
│   ├── main.py
│   ├── config.py
│   ├── core/
│   │   ├── audio_recorder.py
│   │   ├── video_recorder.py          ← 2fps JPEG frame collector
│   │   └── websocket_client.py
│   └── ui/
│       ├── main_window.py             ← session flow, no metric display
│       ├── interview_widget.py        ← progress bar + recording controls only
│       ├── video_player_widget.py
│       ├── camera_preview_widget.py   ← PiP camera + REC badge only
│       └── stark_theme.py
│
├── docs/                              ← architecture diagrams (PNG)
├── scripts/
├── models/
├── uploads/
├── assets/videos/
├── requirements.txt
├── client/requirements.txt
└── .env.example
```

### Data flow

```
Client                        Backend                      MongoDB
  │                             │                            │
  │── video_frame (JPEG) ──────►│                            │
  │── audio_chunk (PCM) ────────►│                            │
  │── answer_complete ──────────►│                            │
  │                             ├── MediaPipe + HSEmotion     │
  │                             ├── Whisper ASR               │
  │                             ├── Llama 3.2 evaluation      │
  │                             │   (+ duration context)      │
  │                             └──────────────── save ──────►│
  │                             │                            │
  │◄── answer_evaluated ────────│   { question_order,        │
  │                             │     had_followup }         │
  │                             │   (no scores or metrics)   │
  │                             │                            │
  │◄── global_evaluation ───────│   { decision,              │
  │                             │     decision_label,        │
  │                             │     decision_color,        │
  │                             │     totals }               │
  │                             │   (no average score)       │
```

---

## Diagrams

### Database Schema

<img src="docs/Database Schema.png" alt="Database Schema"/>

---

### Sequence Diagram — Full Interview Flow
<p align="center">
<img src="docs/Sequence Diagram.png" alt="Sequence Diagram"/>
</p>
---

### Flow 1 — Session Access Validation
<p align="center">
<img src="docs/1.3 Session Access Validation.png" width="50%" alt="Session Access Validation"/>
</p>
---

### Flow 2 — Real-Time Interview
<p align="center">
<img src="docs/2.3 Real-Time Interview.png" width="60%" alt="Real-Time Interview"/>
</p>
---

### Flow 3 — Global Evaluation & Hiring Decision
<p align="center">
  <img src="docs/3.3 Global Evaluation & Hiring Decision.png" width="50%" alt="Global Evaluation and Hiring Decision"/>
</p>
---

### Activity A1 — Facial Analysis Pipeline
<p align="center">
  <img src="docs/A1. Facial Analysis Pipeline.png" width="50%" alt="Facial Analysis Pipeline"/>
</p>
---

### Activity A2 — ASR + LLM Evaluation
<p align="center">
  <img src="docs/A2. ASR + LLM Evaluation.png" width="50%" alt="ASR + LLM Evaluation"/>
</p>
---

### Activity A3 — TTS Synthesis
<p align="center">
  <img src="docs/A3. TTS Synthesis.png" width="40%" alt="TTS Synthesis"/>
</p>
---

### Activity A4 — Global Evaluation & HR Report
<p align="center">
  <img src="docs/A4. Global Evaluation & HR Report.png" width="50%" alt="Global Evaluation and HR Report"/>
</p>
---

## Facial Behavior Analysis

### Detection pipeline (v5.2)

```
Webcam frames (2fps, JPEG)
  │
  ├─► MediaPipe FaceMesh
  │     478 landmarks + iris (468–477)
  │     • EAR → blink detection (threshold 0.22)
  │     • Iris offset → eye contact
  │     • solvePnP → yaw / pitch / roll (angle normalization v5.1)
  │     • Lip corners → smile
  │     • Brow raise / frown → Action Units AU1/2/4
  │
  └─► Emotion backend (priority order)
        1. HSEmotion EfficientNet-B0   ~82%   AffectNet8 + AFEW  ← active
        2. DeepFace VGG CNN            ~73%   AffectNet           ← fallback 1
        3. FACS heuristics             ~60%   landmarks only      ← fallback 2
```

### Metrics stored per answer (MongoDB only)

| Metric | Range | Description |
|---|---|---|
| `confidence_score` | 0–10 | Eye contact + stability + positive emotions − negative emotions |
| `stress_score` | 0–10 | Brow frown + instability + fear + angry + sad |
| `engagement_score` | 0–10 | Eye contact + expressiveness + smile − sad − disgust |
| `eye_contact_ratio` | 0–1 | Fraction of frames with gaze on camera |
| `head_stability` | 0–1 | 1 − (yaw_std + pitch_std) / 60 |
| `smile_ratio` | 0–1 | Fraction of frames with smile detected |
| `blink_rate` | bpm | Estimated at 10fps; returns 0.0 if < 5 frames |
| `dominant_emotion` | string | Most frequent emotion across all frames |

### v5.2 formula changes

| Issue in v5.1 | Fix in v5.2 |
|---|---|
| Eye contact dominated confidence (4.0 pts) — staring blankly scored high | Reduced to 2.5 pts; positive emotions contribute 2.0 pts |
| `sad` not penalizing confidence or engagement | `sad` now reduces both confidence and engagement |
| `stress_score` ignored `sad` and `surprise` | Both now contribute to stress |
| `blink_rate` assumed 2fps → 0.0 bpm on short answers | Corrected to 10fps sampling |

### Global facial summary in HR report

```json
{
  "facial_summary": {
    "avg_confidence": 6.2,
    "avg_stress": 4.4,
    "avg_engagement": 6.0,
    "avg_eye_contact": 0.72,
    "avg_head_stability": 0.75,
    "dominant_emotion": "neutral",
    "facial_available": true
  }
}
```

### Per-answer facial data in evaluation report

```json
{
  "per_answer": [
    {
      "question_order": 1,
      "score": 7.0,
      "facial": {
        "dominant_emotion": "neutral",
        "emotion_scores": { "happy": 10.1, "neutral": 74.3, "sad": 8.2 },
        "eye_contact_ratio": 0.87,
        "confidence_score": 6.9,
        "stress_score": 4.6,
        "engagement_score": 6.8,
        "frames_analyzed": 25,
        "frames_with_face": 24,
        "face_detection_rate": 0.96
      }
    }
  ]
}
```

---

## Scoring & Decisions

### Weighted average

Each question has a configurable `weight` (default `1.0`, range `0.1–10.0`):

```
average_score = Σ(score_i × weight_i) / Σ(weight_i)
```

Example — 3 questions, weights 1 / 2 / 3:

| Question | Score | Weight | Points |
|---|---|---|---|
| Q1 | 8 | 1.0 | 8 |
| Q2 | 6 | 2.0 | 12 |
| Q3 | 7 | 3.0 | 21 |
| **Result** | | **6.0** | **41 / 6 = 6.83** |

### Duration-aware scoring

The LLM receives the response duration and the question's allowed maximum as context. The scoring is modulated as follows:

| Usage ratio | Impact |
|---|---|
| < 20% of allocated time | Penalty of −1 to −2 pts if content is also poor |
| 40–90% of allocated time | Neutral — no impact |
| > 90% of allocated time with rich content | Possible bonus of +0.5 pt |
| Short but precise and complete | No penalty |

### Grading scale

| Score | Verdict | Meaning |
|---|---|---|
| 9–10 | Excellent | Precise, concrete, exemplary |
| 7–8 | Very Good | Good but lacking depth or examples |
| 5–6 | Acceptable | Superficial or vague |
| 3–4 | Poor | Errors or partial understanding |
| 0–2 | Insufficient | Off-topic, incorrect, or empty |

> Score < 8 automatically triggers a follow-up question.

### Hiring decision thresholds

| Average /10 | Decision | Color |
|---|---|---|
| ≥ 7.0 | ✅ Accepted | `#10B981` |
| 5.0 – 6.9 | 🟡 On Hold | `#F59E0B` |
| < 5.0 | ❌ Rejected | `#EF4444` |

---

## WebSocket Message Contract

### Server → Client (candidate-facing only)

| Type | Payload fields | Notes |
|---|---|---|
| `welcome` | `total_questions, position_title, candidate_name, expires_at, language` | Session start |
| `welcome_back` | same + `current_question_index, is_reconnection` | On reconnection |
| `question` | `order, weight, max_duration, progress, language` | Question audio |
| `question_loading` | `progress` | Loading indicator |
| `followup_incoming` | `question_order, followup_text` | Follow-up preview |
| `answer_saved` | `duration, question_order, saved` | Acknowledge receipt |
| `answer_evaluated` | `question_order, had_followup, is_initial` | No scores or feedback |
| `answer_followup_completed` | `question_order, had_followup` | No scores or feedback |
| `global_evaluation` | `decision, decision_label, decision_color, candidate_name, position_title, total_questions, answered_questions` | No average score or summary |
| `interview_completed` | `total_questions, total_answers, position_title, candidate_name` | Session end |
| `error` | `message, error_type` | Error signal |

### Client → Server

| Type | Payload | Description |
|---|---|---|
| `audio_chunk` | `audio_data: base64 PCM` | Audio during recording |
| `video_frame` | `data.frame: base64 JPEG` | Camera frame for analysis |
| `answer_complete` | — | Recording stopped |
| `audio_finished` | — | Client finished playing audio |
| `end_interview` | — | Candidate ended early |

---

## API Reference

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Recruiter login → JWT token |

### Interviews
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/interviews/sessions` | Create a session |
| `GET` | `/interviews/sessions` | List all sessions |
| `GET` | `/interviews/sessions/{id}` | Get session details |
| `WS` | `/ws/interview/{session_id}?lang=fr` | WebSocket interview |

### Evaluations
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/evaluations/` | Trigger evaluation |
| `GET` | `/evaluations/{session_id}` | Get HR report |

### Notifications
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/notifications/` | List notifications |
| `GET` | `/notifications/unread-count` | Unread badge count |
| `PATCH` | `/notifications/{id}` | Mark as read |
| `POST` | `/notifications/mark-all-read` | Mark all read |
| `DELETE` | `/notifications/{id}` | Delete |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/dashboard` | All KPIs |
| `GET` | `/analytics/candidates` | Candidate stats |
| `GET` | `/analytics/interviews` | Interview stats |
| `GET` | `/analytics/scores` | Accepted/Rejected KPIs |
| `GET` | `/analytics/positions/scores` | Score by position |
| `GET` | `/analytics/system` | System health |

### Export
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/export/candidates/csv` | All candidates |
| `GET` | `/export/interviews/csv` | All sessions |
| `GET` | `/export/interviews/{id}/json` | Full report (HR only) |
| `GET` | `/export/evaluations/csv` | Per-question evaluations |

---

## Tech Stack

| Layer | Technology | Version | Role |
|---|---|---|---|
| Backend | FastAPI + Uvicorn | 0.115 / 0.32 | REST API + WebSocket |
| Database | MongoDB + Motor | 7.x / 3.5 | Data persistence |
| ASR | faster-whisper + ctranslate2 | 1.0.3 / 4.4.0 | GPU transcription |
| cuDNN | nvidia-cudnn-cu12 | 8.9.7.29 | cuDNN 8 DLLs (Windows) |
| TTS primary | Edge-TTS | 7.2.7 | Microsoft neural TTS |
| TTS fallback | gTTS | 2.5.3 | Google TTS |
| LLM | Ollama + Llama 3.2 | latest | Answer evaluation + duration scoring |
| Landmarks | MediaPipe | 0.10.14 | 478 landmarks + iris |
| Emotions | HSEmotion | latest | EfficientNet-B0 ~82% |
| Emotions fallback | DeepFace | 0.0.99 | VGG CNN ~73% |
| timm | timm | **0.9.2** | Required by HSEmotion |
| EfficientNet | efficientnet_pytorch | latest | Backbone for enet_b0 |
| Auth | python-jose + bcrypt | 3.3 / 4.2 | JWT + hashing |
| Client GUI | PySide6 | 6.7 | Qt framework |
| Audio | pygame + PyAudio + pydub | 2.6 / 0.2 / 0.25 | Playback + capture |
| Video | OpenCV | 4.10 | Frame capture + decode |

---

## Performance

Measured on RTX 4050 Laptop (6.4 GB VRAM):

| Component | CPU | GPU |
|---|---|---|
| Whisper ASR (medium) | 5–10 s | ~1–3 s |
| Llama 3.2 evaluation | 15–30 s | ~2–8 s |
| Edge-TTS synthesis | ~1 s | ~1 s (network) |
| HSEmotion per frame | ~40 ms | ~8 ms |
| MediaPipe per frame | ~8 ms | ~8 ms (CPU only) |
| **Total per question** | **25–45 s** | **~5–12 s** |

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `No module named 'timm.layers'` | timm 0.6.13 too old | `pip install timm==0.9.2` |
| `No module named 'efficientnet_pytorch'` | Missing HSEmotion dep | `pip install efficientnet_pytorch` |
| `Aucun modèle HSEmotion disponible` | Stack not installed | `pip install timm==0.9.2 efficientnet_pytorch hsemotion` |
| `FieldDescriptor has no attribute 'label'` | protobuf ≥ 5 conflict | `pip install "protobuf>=4.25.3,<5.0.0"` |
| `cudnn_ops_infer64_8.dll not found` | cuDNN 8 missing | `nvidia-cudnn-cu12==8.9.7.29` in requirements |
| `float16 not supported` | CPU + float16 | Set `WHISPER_COMPUTE_TYPE=int8` |
| `OMP: Error #15` | OpenMP conflict | Set `KMP_DUPLICATE_LIB_OK=TRUE` in `.env` |
| `torch.cuda.is_available() = False` | No CUDA build | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| `Edge-TTS 403 Forbidden` | edge-tts 6.x old token | `pip install edge-tts==7.2.7` |
| `Facial analysis timeout` | MediaPipe failing | Fix protobuf, restart server |
| `PyAudio not found` | PortAudio missing | `pipwin install pyaudio` (Windows) |
| `ffmpeg not found` | Not in PATH | Extract to `models/ffmpeg-*/` or add to PATH |
| `Connection refused :11434` | Ollama stopped | Run `ollama serve` |
| `MongoDB timeout` | Service stopped | `net start MongoDB` (Windows) |
| `Empty transcription` | Audio too short | Speak for at least 1 second |

---

## Academic Context

Developed as a **Final Year Engineering Project** — 2nd year, Data Engineering & Decisional Systems, ENET'Com Sfax (2025–2026).

| Domain | Applied concepts |
|---|---|
| Data Engineering | Real-time audio/video pipeline, MongoDB modeling, FastAPI REST design |
| Artificial Intelligence | Whisper ASR (GPU), Llama 3.2 LLM, Edge-TTS 7.x, HSEmotion EfficientNet-B0 |
| Computer Vision | MediaPipe FaceMesh (478 landmarks), EAR blink, solvePnP head pose, iris gaze |
| Decisional Systems | Weighted + duration-aware scoring, follow-up generation, hiring decision, behavioral scoring v5.2 |
| Software Engineering | WebSocket, TTS prefetch, JWT auth, recruiter notifications, privacy-by-design |

---

## License

Proprietary — SparkHire AI © 2026

## Contact

zeineb.ghrab@enetcom.u-sfax.tn