# 🖥️ Backend — SparkHire AI

**FastAPI** server exposing the REST API, interview WebSockets, and orchestrating the entire AI pipeline.

---

## Structure

```
backend/
├── main.py              ← FastAPI entry point + lifespan (service warmup)
├── config.py            ← Pydantic settings (loaded from .env)
├── database.py          ← MongoDB connection (synchronous PyMongo)
├── middlewares.py       ← logging, error handling, rate limiting
│
├── auth/
│   ├── models.py        ← Recruiter, Token (Pydantic)
│   ├── routes.py        ← POST /auth/login · GET /auth/me
│   └── security.py      ← JWT (python-jose) · bcrypt · OAuth2PasswordBearer
│
├── candidates/
│   ├── models.py        ← Candidate, Contact, TechnicalSkill, Experience…
│   ├── crud.py          ← CandidateCRUD (create / get / update / delete)
│   └── routes.py        ← CRUD REST + email/skills search
│
├── interviews/
│   ├── models.py        ← Question, JobPosition, Answer, InterviewSession…
│   ├── crud.py          ← JobPositionCRUD · InterviewSessionCRUD
│   │                       + _send_completion_notification()
│   └── routes.py        ← positions + sessions CRUD + scheduling
│
├── evaluation/
│   ├── models.py        ← AnswerEvaluation, GlobalEvaluation, decision
│   ├── service.py       ← EvaluationService (LLM + facial orchestration)
│   └── routes.py        ← trigger / get / list / delete evaluations
│
├── services/            ← see backend/services/README.md
│   ├── asr_service.py
│   ├── tts_service.py
│   ├── edge_tts_engine.py
│   ├── llm_service.py
│   ├── facial_analysis_service.py
│   └── avatar_service.py
│
├── websocket/           ← see backend/websocket/README.md
│   ├── connection_manager.py
│   └── interview_handler.py
│
├── notifications/
│   ├── models.py        ← Notification (Pydantic)
│   ├── routes.py        ← CRUD + unread-count + mark-all-read
│   └── service.py       ← NotificationService (async helpers)
│
├── analytics/
│   ├── models.py        ← CandidateStats, InterviewStats, ScoreStats…
│   └── routes.py        ← /dashboard · /candidates · /interviews · /scores
│                           /positions/scores · /scheduling · /system
│
└── export/
    └── routes.py        ← CSV (candidates / interviews / evaluations)
                            JSON (full report per session)
```

---

## Configuration (.env)

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sparkhire_ai
SECRET_KEY=<32 hex chars>

# ASR
ASR_ENGINE=faster-whisper
WHISPER_MODEL_SIZE=medium
WHISPER_DEVICE=cuda            # cpu if no GPU
WHISPER_COMPUTE_TYPE=float16   # int8 on CPU

# TTS
TTS_ENGINE=edge-tts
TTS_LANGUAGE=fr

# LLM
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120.0

# Facial Analysis
FACIAL_ANALYSIS_ENABLED=true
FACIAL_CAPTURE_FPS=2.0
FACIAL_DEVICE=cpu

# Misc
KMP_DUPLICATE_LIB_OK=TRUE      # Windows only
```

---

## API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Recruiter login → JWT |
| `GET` | `/auth/me` | Connected recruiter profile |

### Candidates

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/candidates/` | Create a candidate |
| `GET` | `/candidates/` | List (pagination) |
| `GET` | `/candidates/{id}` | Detail |
| `PATCH` | `/candidates/{id}` | Partial update |
| `DELETE` | `/candidates/{id}` | Delete |
| `GET` | `/candidates/search/email` | Search by email |
| `GET` | `/candidates/search/skills` | Search by skills |

### Positions & Sessions

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/interviews/positions` | Create a position with questions |
| `GET` | `/interviews/positions` | List (filters: department, location, is_active) |
| `GET` | `/interviews/positions/{id}` | Detail |
| `DELETE` | `/interviews/positions/{id}` | Delete |
| `POST` | `/interviews/sessions` | Create a session |
| `GET` | `/interviews/sessions` | List (filter by status) |
| `GET` | `/interviews/sessions/{id}` | Detail + answers |
| `PATCH` | `/interviews/sessions/{id}/status` | Change status |
| `PATCH` | `/interviews/sessions/{id}/schedule` | Schedule / reschedule |
| `GET` | `/interviews/sessions/{id}/answers` | Answers + evaluations |
| `GET` | `/interviews/sessions/{id}/answers/summary` | Score summary |
| `WS` | `/ws/interview/{session_id}?lang=fr` | Interview WebSocket |

### Evaluations

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/evaluations/trigger` | Trigger LLM evaluation as background task |
| `GET` | `/evaluations/{session_id}` | Full HR report |
| `GET` | `/evaluations/` | List evaluations |
| `DELETE` | `/evaluations/{session_id}` | Delete |
| `GET` | `/evaluations/health/llm` | Ollama health check |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/dashboard` | All KPIs (param `?days=30`) |
| `GET` | `/analytics/candidates` | Candidate stats |
| `GET` | `/analytics/interviews` | Interview stats |
| `GET` | `/analytics/scores` | Accepted / rejected / trends |
| `GET` | `/analytics/positions/scores` | Scores per position |
| `GET` | `/analytics/scheduling` | Weekly scheduling |
| `GET` | `/analytics/system` | System health |

### Export

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/export/candidates/csv` | All candidates |
| `GET` | `/export/interviews/csv` | All sessions |
| `GET` | `/export/interviews/{id}/json` | Full report (HR) |
| `GET` | `/export/evaluations/csv` | Per-question evaluations |

### Notifications

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/notifications/` | List (param `?unread_only=true`) |
| `GET` | `/notifications/unread-count` | Unread badge count |
| `PATCH` | `/notifications/{id}` | Mark as read |
| `POST` | `/notifications/mark-all-read` | Mark all as read |
| `DELETE` | `/notifications/{id}` | Delete |

---

## MongoDB Data Model

### Collections

| Collection | Role |
|---|---|
| `recruiters` | Recruiter accounts (email + bcrypt hash) |
| `candidates` | Full candidate profiles |
| `job_positions` | Job offers with weighted questions |
| `interview_sessions` | Sessions with embedded answers and evaluations |
| `evaluations` | Global LLM reports (GlobalEvaluation) |
| `notifications` | Recruiter notifications |

### `interview_sessions` Document (simplified)

```json
{
  "session_id": "session_abc123",
  "candidate_id": "...",
  "job_position_id": "...",
  "language": "fr",
  "status": "completed",
  "answers": [
    {
      "question_order": 1,
      "transcript": "...",
      "duration_seconds": 45.2,
      "evaluation": {
        "score": 7.5,
        "verdict": "Very Good",
        "weight": 1.0,
        "had_followup": false,
        "facial_analysis": {
          "dominant_emotion": "neutral",
          "confidence_score": 6.9,
          "stress_score": 4.1,
          "engagement_score": 7.2,
          "eye_contact_ratio": 0.82,
          "frames_analyzed": 22
        }
      }
    }
  ],
  "evaluation_score": 7.2,
  "evaluation_decision": "accepted"
}
```

---

## Starting the Backend

```bash
# Standard start
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Expected startup logs
# ✅ MediaPipe FaceMesh v5.2 | 478 landmarks + iris | CPU
# ✅ HSEmotion | model=enet_b0_8_best_afew | device=CPU
# ✅ Whisper 'medium' ready on CPU
# ✅ Edge-TTS initialized
# ✅ LLM Ollama available | model=llama3.2

# Interactive documentation
open http://localhost:8000/docs
```

---

## Critical Import Order (Windows)

`main.py` injects stub modules for `mediapipe.tasks` **before** any TensorFlow/DeepFace import, to avoid a protobuf conflict on Windows Python 3.11. This order must not be changed.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `FieldDescriptor has no attribute 'label'` | protobuf ≥ 5 | `pip install "protobuf>=4.25.3,<5.0.0"` |
| `cudnn_ops_infer64_8.dll not found` | cuDNN 8 missing | `pip install nvidia-cudnn-cu12==8.9.7.29` |
| `float16 not supported` | CPU + float16 | `WHISPER_COMPUTE_TYPE=int8` |
| `Connection refused :11434` | Ollama stopped | `ollama serve` |
| `MongoDB timeout` | Service stopped | `net start MongoDB` |
| `No module named 'timm.layers'` | timm too old | `pip install timm==0.9.2` |

---

## Diagrams

### Database Schema

<img src="../docs/Database Schema.png" alt="Database Schema"/>