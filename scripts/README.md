# 🛠️ Scripts — SparkHire AI

Utility scripts for initializing the database and downloading AI models before the first launch.

---

## Files

| Script | Description |
|---|---|
| `create_admin.py` | Creates the default recruiter account in MongoDB |
| `download_whisper.py` | Downloads and validates a Whisper ASR model |
| `seed_job_positions.py` | *(optional)* Seeds example job positions into the database |

---

## `create_admin.py`

Creates the default admin recruiter account used to log into the backend API.

**Credentials created:**

| Field | Value |
|---|---|
| Email | `rh@stark.tn` |
| Password | `admin123` |

**Usage:**

```bash
python scripts/create_admin.py
```

The script reads `MONGODB_URL` and `MONGODB_DB_NAME` from your `.env` file. If the account already exists, it exits safely without overwriting.

**Expected output:**

```
Connexion à MongoDB : mongodb://localhost:27017
Admin créé ! ID: <ObjectId>
```

---

## `download_whisper.py`

Downloads a Whisper model from Hugging Face into `models/whisper/` and runs a quick transcription test to verify the model works.

**Usage:**

```bash
python scripts/download_whisper.py [size]
```

**Available sizes:**

| Size | Disk | Quality | Recommended |
|---|---|---|---|
| `tiny` | 75 MB | Low | Development only |
| `base` | 145 MB | Fair | — |
| `small` | 483 MB | Good | — |
| `medium` | 1.5 GB | Very good | ✅ Default |
| `large-v2` | 3.1 GB | Excellent | High-end GPU |
| `large-v3` | 3.1 GB | Best | High-end GPU |

**Example:**

```bash
python scripts/download_whisper.py medium
```

After download, update your `.env`:

```env
ASR_ENGINE=faster-whisper
WHISPER_MODEL_SIZE=medium
```

**Requirements:** `faster-whisper` must be installed (`pip install faster-whisper`).

---

## Prerequisites

All scripts require:
- MongoDB running locally (or a configured `MONGODB_URL` in `.env`)
- A valid `.env` file at the project root

Run these scripts **before** starting the backend for the first time:

```bash
# 1. Initialize the database
python scripts/create_admin.py

# 2. Download the Whisper model
python scripts/download_whisper.py medium

# 3. (Optional) Seed example positions
python scripts/seed_job_positions.py
```