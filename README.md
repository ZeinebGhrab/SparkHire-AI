# ⚡ SparkHire AI — Intelligent Vocal Interview Platform

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)]()
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-47A248?logo=mongodb&logoColor=white)]()
[![Whisper](https://img.shields.io/badge/ASR-Whisper-orange)]()
[![Llama](https://img.shields.io/badge/LLM-Llama%203.2-purple)]()
[![MediaPipe](https://img.shields.io/badge/MediaPipe-FaceMesh-blue)]()
[![HSEmotion](https://img.shields.io/badge/Emotion-HSEmotion-red)]()
[![Edge-TTS](https://img.shields.io/badge/TTS-Edge-TTS-0078D4)]()
[![gTTS](https://img.shields.io/badge/TTS-gTTS-00C0FF?logo=microphone&logoColor=white)]()
[![PySide6](https://img.shields.io/badge/PySide6-Desktop_App-41CD52?logo=qt&logoColor=white)]()
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey.svg)]()
[![Stars](https://img.shields.io/github/stars/ZeinebGhrab/sparkhire-ai?style=social)]()
[![Forks](https://img.shields.io/github/forks/ZeinebGhrab/sparkhire-ai?style=social)]()

> AI-powered voice interview platform with real-time multimodal evaluation (ASR + LLM + Computer Vision)

> **Final Year Engineering Project (PFA)** · Data Engineering & Decisional Systems · ENET'Com Sfax · 2025–2026

---

## Overview

SparkHire AI automates first-round recruitment interviews. A candidate connects through the desktop client, answers questions delivered by a TTS avatar, and the platform evaluates responses using a local LLM. In parallel, a computer vision pipeline analyzes facial behavior and stores metrics exclusively on the HR side.

```
Candidate speaks
    │
    ├─► Whisper ASR ────────────────► Transcript
    │
    ├─► MediaPipe + HSEmotion ──────► Behavioral metrics (backend / HR only)
    │
    └─► Llama 3.2 (Ollama) ─────────► Score 0–10 + Verdict + Follow-up question
                                            │
                                            └─► MongoDB ──► HR Report
```

**Privacy by design** — candidates never see their scores, facial metrics, or feedback.

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

## System Requirements

| Software | Version | Role |
|---|---|---|
| Python | 3.10 or 3.11 | Main runtime |
| MongoDB | 7.x Community | Data persistence |
| Ollama | latest | Local LLM server |
| FFmpeg | 6.0+ | Audio conversion (gTTS fallback) |
| CUDA Toolkit | 11.x or 12.x | GPU acceleration (optional) |

> **Windows only:** VS C++ Build Tools 2022 required to compile PyAudio.

---

## Project Structure

```
sparkhire-ai/
├── README.md                        ← this file (global overview)
├── requirements.txt                 ← backend dependencies
├── .env.example
│
├── backend/                         ← FastAPI server
│   ├── README.md                    ← backend documentation
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/
│   ├── candidates/
│   ├── interviews/
│   ├── evaluation/
│   │   └── README.md               ← LLM evaluation pipeline
│   ├── services/
│   │   └── README.md               ← ASR · TTS · LLM · Facial Analysis
│   ├── websocket/
│   │   └── README.md               ← WebSocket protocol
│   ├── notifications/
│   ├── analytics/
│   └── export/
│
├── client/                          ← PySide6 desktop application
│   ├── README.md                    ← client documentation
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── core/
│   └── ui/
│
├── docs/                            ← PNG diagrams
│   └── README.md                    ← Full Technical Documentation
├── scripts/                         ← initialization scripts
├── models/                          ← Whisper / ffmpeg models
└── assets/videos/                   ← HR avatar videos
```

---

## Quick Installation

```bash
# 1. Clone
git clone https://github.com/ZeinebGhrab/sparkhire-ai.git
cd sparkhire-ai

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate         # Linux / macOS

# 3. PyTorch GPU (CUDA 12.x)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 4. Backend dependencies
pip install -r requirements.txt

# 5. Client dependencies
pip install -r client/requirements.txt

# 6. Facial analysis stack (mandatory order)
pip install timm==0.9.2 efficientnet_pytorch hsemotion
pip install mediapipe==0.10.14
pip install "protobuf>=4.25.3,<5.0.0"

# 7. Configuration
cp .env.example .env   # then edit .env

# 8. Whisper model
python scripts/download_whisper.py medium

# 9. LLM
ollama serve
ollama pull llama3.2

# 10. Database
python scripts/create_admin.py
python scripts/seed_job_positions.py
```

---

## Running the Application

```bash
# Backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Desktop client (in a second terminal)
python -m client.main
```

---

## Global Architecture

### Data Pipeline

```
PySide6 Client                Backend FastAPI               MongoDB
      │                             │                          │
      ├── video_frame (JPEG) ──────►│                          │
      ├── audio_chunk (PCM) ───────►│                          │
      ├── answer_complete ─────────►│                          │
      │                             ├── MediaPipe + HSEmotion  │
      │                             ├── Whisper ASR            │
      │                             ├── Llama 3.2 evaluation   │
      │                             └──────────── save ───────►│
      │                             │                          │
      │◄── answer_evaluated ────────│   { question_order,      │
      │◄── global_evaluation ───────│     decision }           │
```

### Score & Decision

| Average Score | Decision | Color |
|---|---|---|
| ≥ 7.0 | ✅ Accepted | `#10B981` |
| 5.0 – 6.9 | 🟡 Pending | `#F59E0B` |
| < 5.0 | ❌ Rejected | `#EF4444` |

Score is **weighted**: `Σ(score_i × weight_i) / Σ(weight_i)`

### LLM Grading Scale

| Score | Verdict |
|---|---|
| 9–10 | Excellent |
| 7–8 | Very Good |
| 5–6 | Acceptable |
| 3–4 | Insufficient |
| 0–2 | Poor |

> A score below 8 automatically triggers a follow-up question.

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Backend | FastAPI + Uvicorn | 0.115 / 0.32 |
| Database | MongoDB + Motor | 7.x / 3.5 |
| ASR | faster-whisper | 1.0.3 |
| Primary TTS | Edge-TTS | 7.2.7 |
| Fallback TTS | gTTS | 2.5.3 |
| LLM | Ollama + Llama 3.2 | latest |
| Landmarks | MediaPipe | 0.10.14 |
| Emotions | HSEmotion EfficientNet-B0 | latest |
| Emotions fallback | DeepFace VGG | 0.0.99 |
| Auth | python-jose + bcrypt | 3.3 / 4.2 |
| Client GUI | PySide6 | 6.7 |
| Audio | pygame + PyAudio + pydub | — |
| Video | OpenCV | 4.10 |

---

## Measured Performance (RTX 4050 Laptop)

| Component | CPU | GPU |
|---|---|---|
| Whisper ASR (medium) | 5–10 s | ~1–3 s |
| Llama 3.2 evaluation | 15–30 s | ~2–8 s |
| Edge-TTS synthesis | ~1 s | ~1 s |
| HSEmotion per frame | ~40 ms | ~8 ms |
| MediaPipe per frame | ~8 ms | ~8 ms |
| **Total per question** | **25–45 s** | **~5–12 s** |

---

## Diagrams

### Sequence Diagram — Full Interview Flow

<p align="center">
  <img src="docs/Sequence Diagram.png" alt="Sequence Diagram"/>
</p>

---

## Detailed Documentation

| Module | README |
|---|---|
| Full Technical Documentation | [`docs/README.md`](docs/README.md) |
| Backend (API, routes, DB) | [`backend/README.md`](backend/README.md) |
| AI Services (ASR, TTS, LLM, Facial) | [`backend/services/README.md`](backend/services/README.md) |
| Evaluation Pipeline | [`backend/evaluation/README.md`](backend/evaluation/README.md) |
| WebSocket Protocol | [`backend/websocket/README.md`](backend/websocket/README.md) |
| PySide6 Desktop Client | [`client/README.md`](client/README.md) |

---

## Academic Context

| Domain | Applied Concepts |
|---|---|
| Data Engineering | Real-time audio/video pipeline, MongoDB modeling, FastAPI REST API |
| Artificial Intelligence | Whisper ASR (GPU), Llama 3.2 LLM, Edge-TTS 7.x, HSEmotion EfficientNet-B0 |
| Computer Vision | MediaPipe FaceMesh (478 landmarks), EAR, solvePnP, iris gaze |
| Decision Systems | Weighted scoring + duration, follow-up generation, hiring decision |
| Software Engineering | WebSocket, JWT, privacy by design, recruiter notifications |

---

## Support & Contribution

If you like this project, please consider giving it a ⭐.

Contributions are highly welcome!  

Feel free to:
- Fork the repository
- Create a new branch
- Submit a pull request

For major changes, please open an issue first to discuss what you would like to improve.

---

## License & Contact

**Proprietary** — SparkHire AI © 2026  
`zeineb.ghrab@enetcom.u-sfax.tn`