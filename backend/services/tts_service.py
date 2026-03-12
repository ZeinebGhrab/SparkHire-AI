"""
Service TTS — Architecture simple et rapide :

  1. Edge-TTS  (online Microsoft, instantané, voix naturelles)  ← PRIMAIRE
  2. gTTS      (online Google, ~1-2 s)                          ← FALLBACK
"""

from __future__ import annotations

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── FFMPEG ────────────────────────────────────────────────────────────────────

def _configure_ffmpeg_local() -> bool:
    project_root = Path(__file__).resolve().parent.parent.parent
    ffmpeg_dir   = project_root / "models" / "ffmpeg-8.0.1-essentials_build" / "bin"
    if not ffmpeg_dir.exists():
        return False
    ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        return False
    os.environ["PATH"] = f"{ffmpeg_dir};{os.environ.get('PATH', '')}"
    try:
        from pydub import AudioSegment
        AudioSegment.converter = str(ffmpeg_exe)
        AudioSegment.ffmpeg    = str(ffmpeg_exe)
        ffprobe = ffmpeg_dir / "ffprobe.exe"
        if ffprobe.exists():
            AudioSegment.ffprobe = str(ffprobe)
        logger.info(f"ffmpeg configuré: {ffmpeg_dir}")
        return True
    except ImportError:
        return False

_configure_ffmpeg_local()


# ── INTERFACE ─────────────────────────────────────────────────────────────────

class TTSEngine(ABC):
    voices: dict[str, str] = {}

    @abstractmethod
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        ...


# ── MOTEUR 1 : EDGE-TTS (primaire) ───────────────────────────────────────────

class EdgeEngine(TTSEngine):
    def __init__(self):
        from backend.services.edge_tts_engine import EdgeTTSEngine
        self._engine = EdgeTTSEngine()
        self.voices  = self._engine.voices
        logger.info("Edge-TTS prêt (moteur primaire)")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        return self._engine.synthesize(text, language)


# ── MOTEUR 2 : gTTS (fallback) ────────────────────────────────────────────────

class GoogleEngine(TTSEngine):
    def __init__(self):
        from gtts import gTTS
        self._gTTS = gTTS
        self.voices = {"ar": "gtts-ar", "en": "gtts-en", "fr": "gtts-fr"}
        logger.info("gTTS prêt (fallback)")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        import tempfile
        try:
            from pydub import AudioSegment
        except ImportError:
            return b""
        try:
            lang = language if language in ("ar", "en", "fr") else "ar"
            tts  = self._gTTS(text=text, lang=lang, slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                mp3 = f.name
            tts.save(mp3)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav = f.name
            try:
                AudioSegment.from_mp3(mp3).export(wav, format="wav")
                with open(wav, "rb") as f:
                    return f.read()
            finally:
                for p in (mp3, wav):
                    try: os.unlink(p)
                    except Exception: pass
        except Exception as e:
            logger.error(f"gTTS: {e}")
            return b""


# ── SERVICE PRINCIPAL ─────────────────────────────────────────────────────────

class TTSService:
    def __init__(
        self,
        primary_engine: TTSEngine,
        fallback_engine: Optional[TTSEngine] = None,
        cache_dir: Optional[Path] = None,
    ):
        self._primary  = primary_engine
        self._fallback = fallback_engine
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def engine(self) -> TTSEngine:
        return self._primary

    # Compatibilité avec le reste du code qui appelle is_coqui_ready()
    def is_coqui_ready(self) -> bool:
        return False

    def synthesize(self, text: str, language: str = "ar", use_cache: bool = True) -> bytes:
        if not text or not text.strip():
            return b""

        engine      = self._primary
        engine_name = type(engine).__name__.lower().replace("engine", "")
        voice_name  = engine.voices.get(language, "unknown")

        logger.info(f"TTS | moteur={engine_name} | langue={language} | voix={voice_name}")

        # ── Cache ─────────────────────────────────────────────────────────────
        cache_key  = self._cache_key(text, language, f"{engine_name}_{voice_name}")
        cache_path = (self.cache_dir / f"{cache_key}.wav") if self.cache_dir else None

        if use_cache and cache_path and cache_path.exists():
            logger.info(f"Cache hit: {cache_path.name}")
            return cache_path.read_bytes()

        # ── Synthèse primaire ─────────────────────────────────────────────────
        audio = b""
        try:
            audio = engine.synthesize(text, language)
        except Exception as e:
            logger.warning(f"Edge-TTS échoué: {e}")

        # ── Fallback gTTS ─────────────────────────────────────────────────────
        if not audio and self._fallback:
            logger.info("Fallback → gTTS")
            try:
                audio      = self._fallback.synthesize(text, language)
                fb_name    = type(self._fallback).__name__.lower().replace("engine", "")
                voice_name = self._fallback.voices.get(language, "unknown")
                cache_key  = self._cache_key(text, language, f"{fb_name}_{voice_name}")
                cache_path = (self.cache_dir / f"{cache_key}.wav") if self.cache_dir else None
            except Exception as e:
                logger.error(f"gTTS échoué: {e}")

        # ── Mise en cache ─────────────────────────────────────────────────────
        if use_cache and cache_path and audio:
            try:
                cache_path.write_bytes(audio)
            except Exception as e:
                logger.warning(f"Cache save: {e}")

        return audio

    def synthesize_to_file(self, text: str, output_path: Path, language: str = "ar", use_cache: bool = True) -> bool:
        audio = self.synthesize(text, language, use_cache)
        if not audio:
            return False
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(audio)
            return True
        except Exception as e:
            logger.error(f"Sauvegarde TTS: {e}")
            return False

    @staticmethod
    def _cache_key(text: str, language: str, voice: str = "") -> str:
        return hashlib.md5(f"{text}_{language}_{voice}".encode()).hexdigest()


# ── FACTORY ───────────────────────────────────────────────────────────────────

def get_tts_service() -> TTSService:
    from backend.config import settings

    # ── Edge-TTS (primaire) ───────────────────────────────────────────────────
    primary: Optional[TTSEngine] = None
    try:
        primary = EdgeEngine()
    except Exception as e:
        logger.warning(f"Edge-TTS indisponible: {e}")

    # ── gTTS (fallback ou primaire si Edge absent) ────────────────────────────
    fallback: Optional[TTSEngine] = None
    try:
        gtts = GoogleEngine()
        if primary is None:
            primary = gtts
            logger.warning("Edge-TTS absent — gTTS utilisé comme moteur primaire")
        else:
            fallback = gtts
    except Exception as e:
        logger.warning(f"gTTS indisponible: {e}")

    if primary is None:
        raise RuntimeError("Aucun moteur TTS disponible ! (Edge-TTS et gTTS ont échoué)")

    service = TTSService(primary, fallback, cache_dir=settings.TTS_CACHE_DIR)
    logger.info(
        f"🎙️ TTS Service prêt | primaire={type(primary).__name__} "
        f"| fallback={type(fallback).__name__ if fallback else 'aucun'}"
    )
    return service