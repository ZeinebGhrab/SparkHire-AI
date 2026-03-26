# 📊 Evaluation Pipeline — SparkHire AI

This module orchestrates LLM evaluation of interviews, weighted average computation, facial metric injection, and final HR report generation.

---

## Structure

```
backend/evaluation/
├── __init__.py
├── models.py      ← data structures (Pydantic)
└── service.py     ← EvaluationService (orchestration logic)
```

The REST API is exposed in `backend/evaluation/routes.py`.

---

## Data Models

### `AnswerEvaluation`

LLM evaluation of a single answer. Produced by `EvaluationService.evaluate_single_answer()`.

| Field | Type | Description |
|---|---|---|
| `question_order` | int | Question number |
| `transcript` | str | Whisper transcription |
| `score` | float 0–10 | Score assigned by the LLM |
| `verdict` | str | Label (Excellent / Very Good / …) |
| `strengths` | list[str] | Strengths |
| `improvements` | list[str] | Areas for improvement |
| `feedback` | str | Detailed comment |
| `weight` | float | Question weight (copied from `Question.weight`) |
| `had_followup` | bool | Follow-up was asked |
| `initial_score` | float \| None | Score before follow-up |
| `facial` | `FacialSummary` \| None | Facial metrics (HR report) |

### `FacialSummary`

Aggregated facial metrics for a single answer, extracted from the DB and injected into the final report.

```python
class FacialSummary(BaseModel):
    dominant_emotion:  str   = "neutral"
    emotion_scores:    dict  = {}
    eye_contact_ratio: float = 0.0
    head_stability:    float = 1.0
    smile_ratio:       float = 0.0
    confidence_score:  float = 5.0
    stress_score:      float = 5.0
    engagement_score:  float = 5.0
    frames_analyzed:   int   = 0
    frames_with_face:  int   = 0
    face_detection_rate: float = 0.0
```

### `GlobalFacialSummary`

Aggregation of facial metrics across the entire session.

```python
class GlobalFacialSummary(BaseModel):
    avg_confidence:     float = 0.0
    avg_stress:         float = 0.0
    avg_engagement:     float = 0.0
    avg_eye_contact:    float = 0.0
    avg_head_stability: float = 0.0
    dominant_emotion:   str   = "neutral"
    facial_available:   bool  = False
```

### `GlobalEvaluation`

Full interview report — stored in the `evaluations` collection.

| Field | Description |
|---|---|
| `session_id` | Session identifier |
| `candidate_name` | Full candidate name |
| `position_title` | Job title |
| `average_score` | Weighted average Σ(score×weight)/Σ(weight) |
| `decision` | `accepted` / `pending` / `rejected` |
| `decision_label` | Localized label |
| `decision_color` | Hex color |
| `decision_reason` | One-sentence justification |
| `recommendation` | Hire / Pending / Reject |
| `key_strengths` | Global strengths |
| `key_improvements` | Global areas for improvement |
| `summary` | 2–3 sentence summary |
| `per_answer` | List of `AnswerEvaluation` |
| `facial_summary` | `GlobalFacialSummary` \| None |

---

## Decision Thresholds

```python
DECISION_THRESHOLD_ACCEPT = 7.0   # score >= 7.0 → accepted
DECISION_THRESHOLD_REJECT = 5.0   # score <  5.0 → rejected
                                  # between both  → pending
```

| Average Score | Decision | Hex Color |
|---|---|---|
| ≥ 7.0 | `accepted` | `#10B981` (green) |
| 5.0 – 6.9 | `pending` | `#F59E0B` (amber) |
| < 5.0 | `rejected` | `#EF4444` (red) |

---

## Weighted Average

Each question has a `weight` attribute (default `1.0`, range `0.1–10.0`) configured when the position is created.

```
average_score = Σ(score_i × weight_i) / Σ(weight_i)
```

**Example** — 3 questions, weights 1 / 2 / 3:

| Question | Score | Weight | Points |
|---|---|---|---|
| Q1 | 8 | 1.0 | 8.0 |
| Q2 | 6 | 2.0 | 12.0 |
| Q3 | 7 | 3.0 | 21.0 |
| **Result** | — | **6.0** | **41 / 6 = 6.83** |

---

## Evaluation Service (`EvaluationService`)

### Main Method: `evaluate_full_session()`

```
evaluate_full_session(session_id, language)
    │
    ├── 1. Load session, position, candidate from MongoDB
    │
    ├── 2. Evaluate each answer in parallel (asyncio.gather)
    │        evaluate_single_answer() → AnswerEvaluation
    │
    ├── 3. Inject facial metrics from DB
    │        answers[n].evaluation.facial_analysis → FacialSummary
    │
    ├── 4. Compute GlobalFacialSummary (averages)
    │
    ├── 5. Compute weighted average
    │
    ├── 6. Generate global LLM summary
    │        generate_global_summary() → recommendation + summary
    │
    ├── 7. Build GlobalEvaluation
    │        compute_decision() → accepted / pending / rejected
    │
    ├── 8. _fill_missing_fields() (deterministic fallback if LLM empty)
    │
    └── 9. Persist in evaluations + update interview_sessions
```

### Completeness Guarantee (`_fill_missing_fields`)

If the LLM returns empty fields (timeout, malformed JSON), the method generates deterministic values:
- `recommendation`: computed from score (`>= 7` → Hire)
- `decision_reason`: formula with score and number of questions
- `key_strengths` / `key_improvements`: aggregated from individual evaluations
- `summary`: built from per-question scores

### Individual Evaluation: `evaluate_single_answer()`

```python
async def evaluate_single_answer(
    question_text,
    answer_transcript,
    question_order,
    language="en",
    position_title="",
    audio_path=None,   # re-transcription if transcript is empty
    weight=1.0,
) -> AnswerEvaluation
```

If `transcript` is empty and `audio_path` is provided, Whisper re-transcribes the audio file.

---

## API Routes

### `POST /evaluations/trigger`

Triggers the evaluation as a **background task** (FastAPI BackgroundTasks).

```json
{ "session_id": "session_abc123", "language": "en" }
```

Immediate response (202): evaluation runs in the background.

### `GET /evaluations/{session_id}`

Returns the full `GlobalEvaluation` (HR report).

**Fields never sent to the candidate:**
- `average_score`
- `decision_reason`
- `facial_summary`
- `per_answer[n].facial`
- `per_answer[n].feedback`

These are visible only in the HR report (`GET /evaluations/`) and JSON export (`GET /export/interviews/{id}/json`).

---

## Example JSON Report

```json
{
  "session_id": "session_abc123",
  "candidate_name": "Ahmed Ben Ali",
  "position_title": "Data Scientist",
  "average_score": 7.17,
  "decision": "accepted",
  "decision_label": "Accepted",
  "decision_color": "#10B981",
  "decision_reason": "Weighted average of 7.17/10 across 3 questions.",
  "recommendation": "Hire",
  "key_strengths": ["Python proficiency", "Concrete examples"],
  "key_improvements": ["Deepen feature engineering"],
  "summary": "Strong candidate, good technical mastery, recommended.",
  "facial_summary": {
    "avg_confidence": 6.8,
    "avg_stress": 4.2,
    "avg_engagement": 7.1,
    "avg_eye_contact": 0.75,
    "dominant_emotion": "neutral",
    "facial_available": true
  },
  "per_answer": [
    {
      "question_order": 1,
      "score": 8.0,
      "verdict": "Very Good",
      "weight": 1.0,
      "had_followup": false,
      "facial": {
        "dominant_emotion": "neutral",
        "confidence_score": 7.2,
        "stress_score": 3.8,
        "eye_contact_ratio": 0.81,
        "frames_analyzed": 22,
        "frames_with_face": 21
      }
    }
  ]
}
```

---

## Persistence

After each complete evaluation, `_save_evaluation()` performs two MongoDB operations:

1. **`evaluations`**: upsert of the `GlobalEvaluation` document
2. **`interview_sessions`**: update of denormalized fields for fast listings:
   - `evaluation_score`
   - `evaluation_decision`
   - `evaluation_decision_label`
   - `evaluation_decision_color`
   - `evaluation_recommendation`
   - `evaluation_decision_reason`

---

## Diagrams

### Flow 3 — Global Evaluation & Hiring Decision

<p align="center">
  <img src="../docs/3.3 Global Evaluation & Hiring Decision.png" width="50%" alt="Global Evaluation and Hiring Decision"/>
</p>

### Activity A4 — Global Evaluation & HR Report

<p align="center">
  <img src="../docs/A4. Global Evaluation & HR Report.png" width="50%" alt="Global Evaluation and HR Report"/>
</p>