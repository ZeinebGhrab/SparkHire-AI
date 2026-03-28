# 📈 Analytics — SparkHire AI Backend

Dashboard statistics and KPI aggregations for the recruiter interface. All analytics are computed in real time from MongoDB collections on each request.

---

## Files

| File | Description |
|---|---|
| `models.py` | Pydantic response models for all stat endpoints |
| `routes.py` | REST endpoints returning aggregated statistics |

---

## API Endpoints

All routes require `Authorization: Bearer <token>`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/analytics/dashboard?days=30` | All KPIs in one call |
| `GET` | `/analytics/candidates?days=30` | Candidate statistics |
| `GET` | `/analytics/interviews?days=30` | Interview statistics |
| `GET` | `/analytics/scores` | Score distribution and hiring funnel |
| `GET` | `/analytics/scheduling` | Weekly scheduling breakdown |
| `GET` | `/analytics/positions/scores` | Per-position score stats |
| `GET` | `/analytics/positions/scores?position_id=` | Stats for one position |
| `GET` | `/analytics/system` | System health and resource usage |

---

## Response Models

### `CandidateStats`

```python
{
  "total_candidates": 42,
  "recent_candidates": 7,          # within the period
  "top_skills": [{"skill": "Python", "count": 15}, ...],
  "candidates_by_skill": {...},
  "candidates_by_status": {...}
}
```

### `InterviewStats`

```python
{
  "total_interviews": 18,
  "interviews_by_status": {"completed": 10, "pending": 5, ...},
  "completion_rate": 55.6,
  "average_duration_minutes": 8.4,
  "average_score": 6.8
}
```

### `ScoreStats`

Full hiring funnel with monthly trends, status distribution, score histogram, and department performance.

```python
{
  "accepted": 6,        "accepted_pct_change": +20.0,
  "rejected": 2,        "rejected_pct_change": -10.0,
  "in_interview": 3,
  "pending": 7,
  "monthly_trend": [{"month": "Jan", "applications": 5, "hires": 2}, ...],
  "status_distribution": {"hired": 6, "rejected": 2, "in_interview": 3, "pending": 7},
  "score_distribution": [{"range": "60-80", "count": 4}, ...],
  "department_performance": [{"department": "Tech", "candidates": 10, "rate": 60.0}]
}
```

### `SchedulingStats`

```python
{
  "total_scheduled": 18,
  "this_week": 4,
  "confirmed": 10,
  "pending": 5,
  "cancelled": 2,
  "by_day_this_week": {"Lun": 1, "Mar": 0, "Mer": 2, ...},
  "by_position": {"Data Scientist": 6, ...},
  "by_language": {"ar": 4, "fr": 8, "en": 6},
  "upcoming_7_days": 3
}
```

### `AllPositionsStats` / `PositionScoreStats`

Score breakdown per job position using `/100` scale (LLM score × 10):

```python
{
  "total_candidates": 18,
  "average_score": 68.5,
  "excellent": 4,   # score ≥ 80
  "good": 7,        # 60–79
  "average": 5,     # 40–59
  "weak": 2,        # < 40
  "positions": [...]
}
```

### `SystemStats`

```python
{
  "total_recruiters": 1,
  "total_job_positions": 5,
  "active_sessions": 2,
  "storage_used_mb": 142.3
}
```

---

## Score Normalization

LLM scores are on a **0–10** scale. Analytics endpoints convert to **0–100** for display:

```
score_100 = average_llm_score × 10
```

Hiring decision thresholds (used in score buckets):
- **Excellent** — score ≥ 80 (LLM ≥ 8.0)
- **Good** — 60–79 (LLM 6.0–7.9)
- **Average** — 40–59 (LLM 4.0–5.9)
- **Weak** — < 40 (LLM < 4.0)
- **Hired** — completed session with LLM avg ≥ 7.0

---

## Caching

All aggregations are computed on request with no caching layer. For high-traffic deployments, consider adding a Redis cache with TTL of 5–10 minutes for `/analytics/dashboard`.