# 👤 Candidates — SparkHire AI Backend

CRUD management for candidate profiles. A candidate is the entity that takes the voice interview and whose profile data (skills, experience, education) is used as context for LLM evaluation.

---

## Files

| File | Description |
|---|---|
| `models.py` | Pydantic models for the full candidate profile |
| `crud.py` | `CandidateCRUD` — all database operations |
| `routes.py` | REST endpoints |

---

## Data Model

A `Candidate` document aggregates all professional profile information:

| Section | Model | Minimum required |
|---|---|---|
| Identity | `first_name`, `last_name`, `Contact` | ✅ |
| Technical skills | `List[TechnicalSkill]` | 1+ |
| Work experience | `List[Experience]` | 1+ |
| Education | `List[Education]` | 1+ |
| Languages | `List[Language]` | 1+ |
| Soft skills | `List[SoftSkill]` | 1+ |
| Certifications | `List[Certification]` | 1+ |

### Embedded Models

**`TechnicalSkill`**

```python
{ "name": "Python", "level": "Advanced", "years_experience": 3 }
```

**`Experience`**

```python
{
  "title": "Data Engineer",
  "company": "ENET'Com Sfax",
  "start_date": "2024-09",
  "currently_working": True,
  "technologies": ["FastAPI", "MongoDB"]
}
```

**`Contact`**

```python
{ "email": "user@example.com", "phone": "+216 55 000 000", "linkedin": "..." }
```

---

## API Endpoints

All routes require `Authorization: Bearer <token>`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/candidates/` | Create a candidate |
| `GET` | `/candidates/` | List all (pagination: `skip`, `limit`) |
| `GET` | `/candidates/{id}` | Get by MongoDB `_id` |
| `PATCH` | `/candidates/{id}` | Partial update (only provided fields) |
| `DELETE` | `/candidates/{id}` | Delete |
| `GET` | `/candidates/search/email?email=` | Search by email |
| `GET` | `/candidates/search/skills?skills=` | Search by skill names |
| `POST` | `/candidates/{id}/consents` | Append a consent record |

---

## `CandidateCRUD`

| Method | Description |
|---|---|
| `create(candidate)` | Inserts a new candidate document |
| `get_all(skip, limit)` | Returns paginated list sorted by `created_at` desc |
| `get_by_id(id)` | Returns one candidate or raises 404 |
| `search_by_email(email)` | Searches `contact.email` field |
| `search_by_skills(skills, min_match)` | Filters by skill overlap, sorted by match count |
| `update(id, update)` | Partial `$set` update |
| `delete(id)` | Hard delete |
| `add_consent(id, consent)` | Appends to `consents[]` array |

---

## MongoDB Collection

**Collection:** `candidates`

Indexes recommended:
- `contact.email` (unique)
- `technical_skills.name` (for skill search)
- `created_at` (for listing)