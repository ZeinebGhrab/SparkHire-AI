# 🔐 Auth — SparkHire AI Backend

JWT-based authentication for recruiter accounts. All protected API routes require a valid Bearer token obtained from this module.

---

## Files

| File | Description |
|---|---|
| `models.py` | Pydantic models: `Recruiter`, `RecruiterCreate`, `Token` |
| `routes.py` | REST endpoints: login and current user |
| `security.py` | JWT creation/verification, bcrypt password hashing, OAuth2 dependency |

---

## API Endpoints

### `POST /auth/login`

Authenticates a recruiter and returns a JWT access token.

**Request** (`application/x-www-form-urlencoded`):

```
username=rh@stark.tn&password=admin123
```

**Response:**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

**Errors:**

| Code | Reason |
|---|---|
| 401 | Invalid email or password |

---

### `GET /auth/me`

Returns the email of the currently authenticated recruiter.

**Headers:** `Authorization: Bearer <token>`

**Response:**

```json
{ "email": "rh@stark.tn" }
```

---

## Security

| Parameter | Value |
|---|---|
| Algorithm | `HS256` |
| Token expiry | 60 minutes |
| Password hashing | bcrypt (via `passlib`) |
| Secret key | `SECRET_KEY` in `.env` |

### Key Functions (`security.py`)

| Function | Description |
|---|---|
| `verify_password(plain, hash)` | Compares a plain password against a bcrypt hash |
| `get_password_hash(password)` | Generates a bcrypt hash (returns `bytes`) |
| `create_access_token(data)` | Signs a JWT with a 60-minute expiry |
| `get_current_recruiter(token)` | FastAPI dependency — decodes token, returns email |

### Usage in Protected Routes

```python
from backend.auth.security import get_current_recruiter
from fastapi import Depends

@router.get("/protected")
def my_route(_: str = Depends(get_current_recruiter)):
    ...
```

---

## Configuration

Set the following in your `.env` file:

```env
SECRET_KEY=<32+ random hex characters>
```

> ⚠️ Never use the default key `"change-me-in-production"` in a production environment.