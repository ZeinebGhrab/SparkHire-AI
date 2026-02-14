from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from backend.auth.routes import router as auth_router
from backend.jobs.routes import router as jobs_router
from backend.candidates.routes import router as candidates_router
from backend.matches.routes import router as matches_router
from backend.interviews.routes import router as interviews_router
from backend.media.routes import router as media_router
from backend.analytics.routes import router as analytics_router
from backend.notifications.routes import router as notifications_router
from backend.export.routes import router as export_router
from backend.websocket.interview_handler import handle_interview_websocket
from backend.config import settings

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Application
app = FastAPI(
    title=settings.API_TITLE,
    description="API complète pour le système de recrutement intelligent avec IA vocale",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter dossiers statiques
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
Path(settings.TTS_CACHE_DIR).mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/audio", StaticFiles(directory=settings.TTS_CACHE_DIR), name="audio")

# Routes REST
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(matches_router)
app.include_router(interviews_router)
app.include_router(media_router)
app.include_router(analytics_router)
app.include_router(notifications_router)
app.include_router(export_router)

# WebSocket
@app.websocket("/ws/interview/{session_id}")
async def websocket_interview(websocket: WebSocket, session_id: str):
    """WebSocket pour entretien vocal"""
    await handle_interview_websocket(websocket, session_id)

# Endpoints
@app.get("/")
async def root():
    return {
        "message": "Stark Recruitment AI API",
        "version": settings.API_VERSION,
        "documentation": "/docs",
        "features": [
            "Authentication & Authorization",
            "Candidate Management",
            "Job Positions",
            "CV/Job Matching",
            "Voice Interviews",
            "Media Management",
            "Analytics & Statistics",
            "Notifications",
            "Data Export"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_version": settings.API_VERSION,
        "services": {
            "database": "connected",
            "asr": settings.ASR_ENGINE,
            "tts": settings.TTS_ENGINE,
            "avatar": settings.AVATAR_PROVIDER
        }
    }

@app.get("/api/info")
async def api_info():
    """Informations détaillées sur l'API"""
    return {
        "api_name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "endpoints": {
            "auth": "/auth",
            "candidates": "/candidates",
            "jobs": "/jobs",
            "matches": "/matches",
            "interviews": "/interviews",
            "media": "/media",
            "analytics": "/analytics",
            "notifications": "/notifications",
            "export": "/export",
            "websocket": "/ws/interview/{session_id}"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )