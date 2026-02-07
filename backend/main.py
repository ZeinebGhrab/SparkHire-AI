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
    description="API pour le système de recrutement intelligent avec IA vocale",
    version=settings.API_VERSION
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
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )