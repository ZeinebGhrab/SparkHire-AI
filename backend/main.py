from contextlib import asynccontextmanager
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("DÉMARRAGE RAPIDE - Chargement des services...")
    logger.info("=" * 60)

    from backend.websocket import interview_handler as ih

    # ── ASR (Vosk est rapide à charger) ──
    try:
        from backend.services import get_asr_service
        ih._asr_service = get_asr_service()
        logger.info("✅ ASR chargé")
    except Exception as e:
        logger.error(f"❌ ASR: {e}")
        ih._asr_service = None

    # ── TTS : INSTANTANÉ (Edge-TTS démarre, Coqui charge en arrière-plan) ──
    try:
        from backend.services import get_tts_service
        ih._tts_service = get_tts_service()
        logger.info("✅ TTS actif (Coqui se charge en arrière-plan...)")
    except Exception as e:
        logger.error(f"❌ TTS: {e}")
        ih._tts_service = None

    # ── Avatar ──
    try:
        from backend.services import get_avatar_service
        ih._avatar_service = get_avatar_service()
        logger.info("✅ Avatar chargé")
    except Exception as e:
        logger.error(f"❌ Avatar: {e}")
        ih._avatar_service = None

    logger.info("=" * 60)
    logger.info("✅ Serveur prêt IMMÉDIATEMENT - Coqui TTS charge en fond")
    logger.info("   (qualité Coqui disponible après ~60s)")
    logger.info("=" * 60)

    yield

    logger.info("Arrêt du serveur...")


app = FastAPI(
    title=settings.API_TITLE,
    description="API complète pour le système de recrutement intelligent avec IA vocale",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
Path(settings.TTS_CACHE_DIR).mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/audio", StaticFiles(directory=settings.TTS_CACHE_DIR), name="audio")

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(matches_router)
app.include_router(interviews_router)
app.include_router(media_router)
app.include_router(analytics_router)
app.include_router(notifications_router)
app.include_router(export_router)


@app.websocket("/ws/interview/{session_id}")
async def websocket_interview(websocket: WebSocket, session_id: str):
    await handle_interview_websocket(websocket, session_id)


@app.get("/")
async def root():
    return {
        "message": "Stark Recruitment AI API",
        "version": settings.API_VERSION,
        "documentation": "/docs",
    }


@app.get("/health")
async def health():
    from backend.websocket import interview_handler as ih
    tts_status = "unavailable"
    if ih._tts_service:
        if hasattr(ih._tts_service, 'is_coqui_ready') and ih._tts_service.is_coqui_ready():
            tts_status = "coqui_ready"
        else:
            tts_status = "edge_tts_active_coqui_loading"
    return {
        "status": "ok",
        "api_version": settings.API_VERSION,
        "services": {
            "database": "connected",
            "asr": "ready" if ih._asr_service else "unavailable",
            "tts": tts_status,
            "avatar": "ready" if ih._avatar_service else "unavailable",
        }
    }


@app.get("/api/info")
async def api_info():
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
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )