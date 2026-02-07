# 🎤 Stark Recruitment - AI-Powered Voice Interview System

Complete recruitment platform with automated voice interviews via AI avatar.

## 🎯 Features

- ✅ **Automated voice interviews** with ASR (Vosk/Whisper)
- ✅ **Predefined questions** per position (20 questions/position)
- ✅ **Speaking avatar** with TTS (pyttsx3/Coqui-TTS)
- ✅ **Automatic transcription** of responses
- ✅ **Real-time WebSocket** for fluid communication
- ✅ **Modern client interface** (PySide6)
- ✅ **Complete REST API** (FastAPI)
- ✅ **MongoDB database**

## 📋 Prerequisites

- Python 3.10+
- MongoDB 4.4+
- Redis (optional, for cache)
- PyAudio (requires PortAudio)

### PortAudio Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

**macOS:**
```bash
brew install portaudio
```

**Windows:**
```bash
# PyAudio will be installed via pip
```

## 🚀 Installation

### 1. Clone the project
```bash
git clone <repo-url>
cd hr_avatar_platform
```

### 2. Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Download Arabic Vosk model
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-ar-0.22-linto-1.1.0.zip
unzip vosk-model-ar-0.22-linto-1.1.0.zip
mv vosk-model-ar-0.22-linto-1.1.0 vosk-model-ar
cd ..

# Configure .env
cp .env.example .env
# Edit .env with your parameters
```

### 3. Client
```bash
cd client
pip install -r requirements.txt
```

### 4. Database
```bash
# Start MongoDB
mongod --dbpath ./data/db

# Create admin (in another terminal)
python scripts/create_admin.py

# Seed positions with questions
python scripts/seed_job_positions.py
```

## ▶️ Launch

### Backend
```bash
# Terminal 1 - Backend API
python backend/main.py

# API will be available at http://localhost:8000
# Documentation: http://localhost:8000/docs
```

### Client
```bash
# Terminal 2 - PySide6 Client
cd client
python main.py
```

## 📝 Usage

### 1. Create an interview (via API)
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -d "username=rh@stark.tn&password=admin123"

# Create a candidate
curl -X POST http://localhost:8000/candidates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ahmed",
    "last_name": "Ben Ali",
    "contact": {"email": "ahmed@example.com"},
    "skills": ["Python", "JavaScript"]
  }'

# Create an interview session
curl -X POST http://localhost:8000/interviews/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "<candidate_id>",
    "job_position_id": "<position_id>",
    "language": "ar"
  }'
```

### 2. Take the interview (Client)

1. Launch the client: `python client/main.py`
2. Enter the `session_id` provided by the API
3. Click "Connect"
4. Listen to the avatar's questions
5. Answer vocally
6. Responses are automatically transcribed and saved

### 3. View results
```bash
# Via API
curl http://localhost:8000/interviews/sessions/<session_id>

# You will see:
# - All questions asked
# - Response transcriptions
# - Audio files of responses
# - Duration of each response
```

## 🧪 Tests
```bash
# Complete flow test
python scripts/test_interview.py
```

## 📂 Structure
```
hr_avatar_platform/
├── backend/           # FastAPI API
│   ├── auth/          # Authentication
│   ├── candidates/    # Candidate management
│   ├── jobs/          # Job postings
│   ├── matches/       # CV/Job matching
│   ├── interviews/    # Voice interviews
│   ├── websocket/     # Real-time communication
│   └── services/      # ASR, TTS, Avatar
│
├── client/            # PySide6 Interface
│   ├── core/          # Business logic
│   └── ui/            # Graphical interface
│
└── scripts/           # Utilities
```

## 🔧 Configuration

### Environment variables (.env)
```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=stark_recruitment

# ASR
ASR_ENGINE=vosk  # or faster-whisper
VOSK_MODEL_PATH=./models/vosk-model-ar

# TTS
TTS_ENGINE=pyttsx3  # or coqui

# Avatar
AVATAR_PROVIDER=simple  # or wav2lip, did
```

## 🛠️ Technologies

- **Backend:** FastAPI, WebSocket, MongoDB
- **ASR:** Vosk / Whisper
- **TTS:** pyttsx3 / Coqui-TTS
- **Client:** PySide6, PyAudio
- **Database:** MongoDB

## 📄 License

Proprietary - Stark Solutions © 2026

## 👥 Support

For any questions: rh@stark.tn