# 🎤 Stark Recruitment - Système d'Entretien Vocal avec IA

Plateforme complète de recrutement avec entretiens vocaux automatisés via avatar IA.

## 🎯 Fonctionnalités

- ✅ **Entretiens vocaux automatisés** avec ASR (Vosk/Whisper)
- ✅ **Questions prédéfinies** par poste (20 questions/poste)
- ✅ **Avatar parlant** avec TTS (pyttsx3/Coqui-TTS)
- ✅ **Transcription automatique** des réponses
- ✅ **WebSocket temps réel** pour communication fluide
- ✅ **Interface client** moderne (PySide6)
- ✅ **API REST complète** (FastAPI)
- ✅ **Base de données MongoDB**

## 📋 Prérequis

- Python 3.10+
- MongoDB 4.4+
- Redis (optionnel, pour cache)
- PyAudio (nécessite PortAudio)

### Installation PortAudio

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
# PyAudio sera installé via pip
```

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone <repo-url>
cd hr_avatar_platform
```

### 2. Backend
```bash
# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt

# Télécharger modèle Vosk arabe
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-ar-0.22-linto-1.1.0.zip
unzip vosk-model-ar-0.22-linto-1.1.0.zip
mv vosk-model-ar-0.22-linto-1.1.0 vosk-model-ar
cd ..

# Configurer .env
cp .env.example .env
# Éditer .env avec vos paramètres
```

### 3. Client
```bash
cd client
pip install -r requirements.txt
```

### 4. Base de données
```bash
# Démarrer MongoDB
mongod --dbpath ./data/db

# Créer admin (dans un autre terminal)
python scripts/create_admin.py

# Seed les postes avec questions
python scripts/seed_job_positions.py
```

## ▶️ Lancement

### Backend
```bash
# Terminal 1 - Backend API
python backend/main.py

# L'API sera disponible sur http://localhost:8000
# Documentation: http://localhost:8000/docs
```

### Client
```bash
# Terminal 2 - Client PySide6
cd client
python main.py
```

## 📝 Utilisation

### 1. Créer un entretien (via API)
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -d "username=rh@stark.tn&password=admin123"

# Créer un candidat
curl -X POST http://localhost:8000/candidates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ahmed",
    "last_name": "Ben Ali",
    "contact": {"email": "ahmed@example.com"},
    "skills": ["Python", "JavaScript"]
  }'

# Créer une session d'entretien
curl -X POST http://localhost:8000/interviews/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "<candidate_id>",
    "job_position_id": "<position_id>",
    "language": "ar"
  }'
```

### 2. Passer l'entretien (Client)

1. Lancer le client: `python client/main.py`
2. Entrer le `session_id` fourni par l'API
3. Cliquer sur "Se connecter"
4. Écouter les questions de l'avatar
5. Répondre vocalement
6. Les réponses sont automatiquement transcrites et sauvegardées

### 3. Consulter les résultats
```bash
# Via API
curl http://localhost:8000/interviews/sessions/<session_id>

# Vous verrez:
# - Toutes les questions posées
# - Transcriptions des réponses
# - Fichiers audio des réponses
# - Durée de chaque réponse
```

## 🧪 Tests
```bash
# Test complet du flow
python scripts/test_interview.py
```

## 📂 Structure
```
hr_avatar_platform/
├── backend/           # API FastAPI
│   ├── auth/          # Authentification
│   ├── candidates/    # Gestion candidats
│   ├── jobs/          # Offres d'emploi
│   ├── matches/       # Matching CV/Jobs
│   ├── interviews/    # Entretiens vocaux
│   ├── websocket/     # Communication temps réel
│   └── services/      # ASR, TTS, Avatar
│
├── client/            # Interface PySide6
│   ├── core/          # Logique métier
│   └── ui/            # Interface graphique
│
└── scripts/           # Utilitaires
```

## 🔧 Configuration

### Variables d'environnement (.env)
```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=stark_recruitment

# ASR
ASR_ENGINE=vosk  # ou faster-whisper
VOSK_MODEL_PATH=./models/vosk-model-ar

# TTS
TTS_ENGINE=pyttsx3  # ou coqui

# Avatar
AVATAR_PROVIDER=simple  # ou wav2lip, did
```

## 🛠️ Technologies

- **Backend:** FastAPI, WebSocket, MongoDB
- **ASR:** Vosk / Whisper
- **TTS:** pyttsx3 / Coqui-TTS
- **Client:** PySide6, PyAudio
- **Base de données:** MongoDB

## 📄 Licence

Propriétaire - Stark Solutions © 2025

## 👥 Support

Pour toute question: rh@stark.tn