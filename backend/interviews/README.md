# 🎙️ Interviews — SparkHire AI Backend

Core interview domain: job positions, interview sessions, answers, and embedded LLM evaluations. This module is the central data layer for the entire interview pipeline.

---

## Files

| File | Description |
|---|---|
| `models.py` | All Pydantic/MongoDB data models |
| `crud.py` | `JobPositionCRUD` and `InterviewSessionCRUD` |
| `routes.py` | REST endpoints for positions and sessions |

---

## Data Models

### `Question`

A question embedded in a `JobPosition`. Questions support three languages and carry a weight for the final weighted average.

```python
{
  "order": 1,
  "question_ar": "...",
  "question_fr": "...",
  "question_en": "...",
  "max_duration_seconds": 90,   # default: 90 s
  "weight": 1.0,                 # default: 1.0, range: 0.1–10.0
  "evaluation_criteria": ["clarity", "technical depth"]
}
```

### `JobPosition`

A job offer with its list of questions. Questions define what is asked during the interview and how much each answer counts toward the final score.

### `Answer`

An answer embedded inside `InterviewSession.answers[]`. Contains:
- `transcript` — Whisper ASR output
- `audio_file_path` — path to the saved WAV file
- `duration_seconds` — actual recording length
- `evaluation: AnswerEvaluationData` — LLM evaluation result (embedded)

### `AnswerEvaluationData`

LLM evaluation stored directly inside each answer:

| Field | Description |
|---|---|
| `score` | 0–10 (LLM grade) |
| `verdict` | Excellent / Very Good / … |
| `weight` | Copied from `Question.weight` at evaluation time |
| `had_followup` | Whether a follow-up question was asked |
| `initial_score` | Score before follow-up (if applicable) |
| `facial_analysis` | `FacialAnalysisData` or `None` |

### `FacialAnalysisData`

Behavioral metrics stored inside each answer's evaluation:

```python
{
  "dominant_emotion": "neutral",
  "eye_contact_ratio": 0.82,
  "head_stability": 0.91,
  "confidence_score": 7.2,
  "stress_score": 3.8,
  "engagement_score": 7.5,
  "frames_analyzed": 22,
  "face_detection_rate": 0.95
}
```

### `InterviewSession`

| Field | Description |
|---|---|
| `session_id` | Unique string token (format: `session_xxx…`) |
| `status` | `pending` → `in_progress` → `completed` / `cancelled` |
| `language` | `ar` / `fr` / `en` |
| `current_question_index` | Tracks progress for reconnection |
| `answers` | Embedded array of `Answer` |
| `scheduled_at` | Optional scheduled start time |
| `late_access_deadline` | `scheduled_at + 30 min` — last allowed entry |
| `created_by` | Recruiter email (for notifications) |

---

## Session Lifecycle

```
pending
  │
  ├── (validate_session_access) → access allowed?
  │
  └── in_progress
        │
        ├── (answers collected via WebSocket)
        │
        └── completed  ──────────► notification sent
              or
            cancelled
```

### `validate_session_access(session_id)`

Returns `(session, is_valid, error_message)`. Checks:
1. Session exists and is not `completed` / `cancelled`
2. For scheduled sessions: current time is within `[scheduled_at, late_access_deadline]`
3. For immediate sessions: current time is before `expires_at`

### `update_status("completed")` Side Effect

When a session transitions to `completed`, `_send_completion_notification()` is called automatically — it inserts a notification document into `db.notifications` targeting `created_by` (or all recruiters as fallback).

---

## API Endpoints

All routes require `Authorization: Bearer <token>`.

### Positions

| Method | Path | Description |
|---|---|---|
| `POST` | `/interviews/positions` | Create a position with questions |
| `GET` | `/interviews/positions` | List (filter: `department`, `location`, `is_active`, `period_days`) |
| `GET` | `/interviews/positions/{id}` | Get by ID |
| `DELETE` | `/interviews/positions/{id}` | Delete |
| `GET` | `/interviews/positions/meta/departments` | Distinct department list |
| `GET` | `/interviews/positions/meta/locations` | Distinct location list |

### Sessions

| Method | Path | Description |
|---|---|---|
| `POST` | `/interviews/sessions` | Create session (stores `created_by` from JWT) |
| `GET` | `/interviews/sessions` | List (filter by `status`) |
| `GET` | `/interviews/sessions/{id}` | Full session with embedded answers |
| `PATCH` | `/interviews/sessions/{id}/status?status=` | Update status |
| `PATCH` | `/interviews/sessions/{id}/schedule?scheduled_at=` | Schedule / reschedule |
| `GET` | `/interviews/sessions/{id}/answers` | Answers + evaluations |
| `GET` | `/interviews/sessions/{id}/answers/summary` | Score summary |
| `GET` | `/interviews/sessions/candidate/{id}` | Sessions for a candidate |
| `DELETE` | `/interviews/sessions/{id}` | Delete |

---

## MongoDB Collections

| Collection | Role |
|---|---|
| `job_positions` | Job offers with embedded questions |
| `interview_sessions` | Sessions with embedded answers and evaluations |