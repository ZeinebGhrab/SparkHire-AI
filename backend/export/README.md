# 📤 Export — SparkHire AI Backend

Data export routes for downloading interview data in CSV and JSON formats. All endpoints stream content directly without writing to disk.

---

## Files

| File | Description |
|---|---|
| `routes.py` | Four export endpoints |

---

## API Endpoints

All routes require `Authorization: Bearer <token>`. Responses stream as file downloads.

### `GET /export/candidates/csv`

Exports all candidate profiles as a CSV file.

**Columns:**

```
ID, First Name, Last Name, Email, Phone, Technical Skills, Languages, Soft Skills, Certifications, Created At
```

**Skills** are joined as comma-separated strings (e.g. `Python, FastAPI, MongoDB`).

---

### `GET /export/interviews/csv`

Exports all interview sessions as a CSV file.

**Columns:**

```
Session ID, Candidate ID, Position ID, Status, Language, Questions Asked, Answers, Average Score, Created At
```

The `Average Score` is computed on the fly from `answers[n].evaluation.score` fields.

---

### `GET /export/interviews/{session_id}/json`

Exports the full HR report for one session as a JSON file.

**Structure:**

```json
{
  "session": { "session_id", "status", "language", "average_score", "created_at", "started_at", "completed_at" },
  "candidate": { "id", "first_name", "last_name", "email" },
  "position": { "id", "title", "department" },
  "answers": [ ... full answer + evaluation + facial data ... ]
}
```

This is the most complete export format and includes all LLM evaluation details and facial metrics.

---

### `GET /export/evaluations/csv`

Exports all per-answer LLM evaluations across all sessions as a CSV file.

**Columns:**

```
Session ID, Candidate ID, Position ID, Language, Question Order, Question Text, Transcript, Score, Verdict, Feedback
```

---

## File Naming

All downloads use timestamped filenames:

| Endpoint | Filename |
|---|---|
| `/candidates/csv` | `candidates_YYYYMMDD_HHMMSS.csv` |
| `/interviews/csv` | `interviews_YYYYMMDD_HHMMSS.csv` |
| `/interviews/{id}/json` | `interview_{session_id}_YYYYMMDD_HHMMSS.json` |
| `/evaluations/csv` | `evaluations_YYYYMMDD_HHMMSS.csv` |

---

## Implementation Notes

- All exports use Python's `csv.writer` writing to an `io.StringIO` buffer streamed via `StreamingResponse`
- The JSON export uses `json.dumps(..., default=str)` to safely serialize `datetime` objects
- No temporary files are created on disk — content is fully buffered in memory
- Empty collections return a `404` response rather than an empty file