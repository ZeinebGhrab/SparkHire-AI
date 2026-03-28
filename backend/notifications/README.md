# 🔔 Notifications — SparkHire AI Backend

In-app notification system for recruiters. Notifications are created automatically when an interview completes and are listed in the HR dashboard.

---

## Files

| File | Description |
|---|---|
| `models.py` | `Notification`, `NotificationCreate`, `NotificationUpdate` Pydantic models |
| `routes.py` | REST CRUD endpoints |
| `service.py` | `NotificationService` — async helpers for programmatic creation |

---

## Notification Document

```json
{
  "_id": "...",
  "recipient_email": "rh@stark.tn",
  "type": "interview_completed",
  "title": "Interview completed",
  "message": "Candidate Ahmed Ben Ali completed the Data Scientist interview.",
  "data": {
    "session_id": "session_abc123",
    "candidate_name": "Ahmed Ben Ali",
    "position_title": "Data Scientist",
    "total_answers": 3
  },
  "priority": "high",
  "read": false,
  "created_at": "2026-03-25T10:30:00Z"
}
```

### Priority Levels

| Value | Usage |
|---|---|
| `low` | Informational |
| `normal` | Standard events |
| `high` | Interview completed |
| `urgent` | System alerts |

---

## Automatic Notifications

When `InterviewSessionCRUD.update_status("completed")` is called, `_send_completion_notification()` in `crud.py` automatically inserts a notification without any additional action required.

**Recipient resolution:**
1. `session.created_by` (recruiter email stored at session creation time)
2. Fallback → all registered recruiters (if `created_by` is missing)

**Multilingual messages** — the notification text is generated in the session's interview language (`ar` / `fr` / `en`).

---

## API Endpoints

All routes require `Authorization: Bearer <token>`. Each endpoint is scoped to the authenticated recruiter's email.

| Method | Path | Description |
|---|---|---|
| `POST` | `/notifications/` | Manually create a notification |
| `GET` | `/notifications/` | List notifications (`?unread_only=true` filter) |
| `GET` | `/notifications/unread-count` | Count of unread notifications (for badge) |
| `PATCH` | `/notifications/{id}` | Mark as read (`{"read": true}`) |
| `POST` | `/notifications/mark-all-read` | Mark all as read |
| `DELETE` | `/notifications/{id}` | Delete one notification |

---

## `NotificationService`

Async helper methods for programmatic notification creation from other services.

| Method | Trigger |
|---|---|
| `notify_interview_started(session_id, email)` | Interview begins |
| `notify_interview_completed(session_id, email, ...)` | Interview ends |
| `notify_new_match(email, candidate, job, score)` | Match score ≥ 0.8 |
| `notify_new_candidate(email, name, email, skills)` | Candidate created |
| `notify_system_alert(email, type, message)` | System-level alerts |

> Note: In the current implementation, automatic notifications are handled directly in `InterviewSessionCRUD`. `NotificationService` is available for extending the system with additional notification triggers.

---

## MongoDB Collection

**Collection:** `notifications`

Recommended indexes:
- `recipient_email` + `read` (for efficient unread count queries)
- `created_at` (for sorted listing)