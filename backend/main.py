"""
Stark Recruitment AI — Backend FastAPI
Pipeline : Voix → Whisper → Llama 3 → Score / Feedback
          Vidéo → MediaPipe + DeepFace → Métriques comportementales
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from backend.auth.routes          import router as auth_router
from backend.candidates.routes    import router as candidates_router
from backend.interviews.routes    import router as interviews_router
from backend.media.routes         import router as media_router
from backend.analytics.routes     import router as analytics_router
from backend.notifications.routes import router as notifications_router
from backend.export.routes        import router as export_router
from backend.evaluation.routes    import router as evaluation_router
from backend.websocket.interview_handler import handle_interview_websocket
from backend.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("DÉMARRAGE — Chargement des services...")
    logger.info("=" * 60)

    from backend.websocket import interview_handler as ih

    # ── ASR (Whisper) ─────────────────────────────────────────────────────────
    try:
        from backend.services import get_asr_service
        ih._asr_service = get_asr_service()
        engine = settings.ASR_ENGINE
        model  = settings.WHISPER_MODEL_SIZE if engine == "faster-whisper" else settings.VOSK_MODEL_PATH
        logger.info(f" ASR chargé | moteur={engine} | modèle={model}")
    except Exception as e:
        logger.error(f" ASR : {e}")
        ih._asr_service = None

    # ── TTS ───────────────────────────────────────────────────────────────────
    try:
        from backend.services import get_tts_service
        ih._tts_service = get_tts_service()
        logger.info(" TTS actif")
    except Exception as e:
        logger.error(f" TTS : {e}")
        ih._tts_service = None

    # ── Avatar ────────────────────────────────────────────────────────────────
    try:
        from backend.services import get_avatar_service
        ih._avatar_service = get_avatar_service()
        logger.info(" Avatar chargé")
    except Exception as e:
        logger.error(f" Avatar : {e}")
        ih._avatar_service = None

    # ── Facial Analysis — warm-up au démarrage ────────────────────────────────
    # Le warm-up est CRITIQUE : sans lui, DeepFace charge ses poids (~6 Mo)
    # lors du premier appel en entretien → timeout de 15-20s sur Q1.
    try:
        from backend.services.facial_analysis_service import get_facial_service
        facial_svc = get_facial_service()
        status     = facial_svc.status

        if status["mediapipe"]:
            logger.info(" MediaPipe FaceMesh | 478 landmarks + iris | EAR + solvePnP")
        else:
            logger.warning(
                " MediaPipe indisponible — mode dégradé (émotions DeepFace uniquement)\n"
                "  Fix : pip install \"protobuf>=4.25.3,<5.0.0\""
            )

        if status["deepface"]:
            warmup_ok = facial_svc.warmup_deepface()
            if warmup_ok:
                logger.info(" DeepFace warm-up OK — poids en mémoire")
            else:
                logger.warning(" DeepFace warm-up différé — chargement au 1er appel")
        else:
            logger.warning(
                " DeepFace indisponible — fallback heuristiques FACS\n"
                "  Fix : pip install deepface tf-keras"
            )

        mode = "full (MediaPipe + DeepFace)"      if status["full_pipeline"]  else \
               "dégradé (DeepFace émotions only)" if status["deepface"]       else \
               "minimal (FACS heuristiques)"
        logger.info(f" Facial Analysis | mode={mode}")

    except Exception as e:
        logger.error(f" Facial Analysis : {e}")

    # ── LLM / Ollama ──────────────────────────────────────────────────────────
    try:
        from backend.services.llm_service import get_llm_service
        llm = get_llm_service()
        if await llm.is_available():
            logger.info(
                f" LLM Ollama disponible | modèle={settings.OLLAMA_MODEL} "
                f"| url={settings.OLLAMA_URL}"
            )
        else:
            logger.warning(
                f"  Ollama non disponible ({settings.OLLAMA_URL}). "
                "Démarrez Ollama: `ollama serve` puis `ollama pull llama3`"
            )
    except Exception as e:
        logger.error(f" LLM : {e}")

    logger.info("=" * 60)
    logger.info(
        f" Serveur prêt | AR/FR/EN | Whisper={settings.WHISPER_MODEL_SIZE} "
        f"| LLM={settings.OLLAMA_MODEL}"
    )
    logger.info("=" * 60)

    yield

    logger.info("Arrêt du serveur...")


app = FastAPI(
    title=settings.API_TITLE,
    description=(
        "API recrutement IA avec pipeline vocal+facial : "
        "Voix → Whisper ASR → Llama 3 Évaluation — Multilingue AR/FR/EN\n"
        "Vidéo → MediaPipe FaceMesh + DeepFace CNN → Métriques comportementales"
    ),
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
app.mount("/audio",   StaticFiles(directory=settings.TTS_CACHE_DIR), name="audio")

app.include_router(auth_router)
app.include_router(candidates_router)
app.include_router(interviews_router)
app.include_router(media_router)
app.include_router(analytics_router)
app.include_router(notifications_router)
app.include_router(export_router)
app.include_router(evaluation_router)


@app.websocket("/ws/interview/{session_id}")
async def websocket_interview(
    websocket: WebSocket,
    session_id: str,
    lang: str = "",
):
    await handle_interview_websocket(websocket, session_id, lang=lang)


@app.get("/")
async def root():
    return {
        "message":             "Stark Recruitment AI API",
        "version":             settings.API_VERSION,
        "languages_supported": ["ar", "fr", "en"],
        "documentation":       "/docs",
    }


@app.get("/health")
async def health():
    from backend.websocket import interview_handler as ih
    from backend.services.llm_service import get_llm_service

    tts_status = "unavailable"
    if ih._tts_service:
        engine_name = type(ih._tts_service.engine).__name__.lower()
        tts_status  = engine_name

    llm_ok = False
    try:
        llm_ok = await get_llm_service().is_available()
    except Exception:
        pass

    facial_status = {}
    try:
        from backend.services.facial_analysis_service import get_facial_service
        facial_status = get_facial_service().status
    except Exception:
        pass

    return {
        "status":      "ok",
        "api_version": settings.API_VERSION,
        "languages":   ["ar", "fr", "en"],
        "services": {
            "database":   "connected",
            "asr":        "ready" if ih._asr_service   else "unavailable",
            "tts":        tts_status,
            "avatar":     "ready" if ih._avatar_service else "unavailable",
            "llm_ollama": "ready" if llm_ok             else "unavailable",
            "llm_model":  settings.OLLAMA_MODEL,
            "facial":     facial_status,
        },
    }


@app.get("/api/info")
async def api_info():
    return {
        "api_name": settings.API_TITLE,
        "version":  settings.API_VERSION,
        "pipeline": "Voice → Whisper ASR → Llama3 LLM → Score/Feedback | Video → MediaPipe + DeepFace → Behavioral metrics",
        "endpoints": {
            "auth":          "/auth",
            "candidates":    "/candidates",
            "interviews":    "/interviews",
            "evaluations":   "/evaluations",
            "media":         "/media",
            "analytics":     "/analytics",
            "notifications": "/notifications",
            "export":        "/export",
            "websocket":     "/ws/interview/{session_id}?lang=ar|fr|en",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )