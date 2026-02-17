"""
Service TTS - CHARGEMENT LAZY (non-bloquant)
Le modèle Coqui est chargé dans un thread en arrière-plan,
pendant ce temps Edge-TTS ou gTTS prend le relais.
"""

import logging
import hashlib
import os
import threading
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ==================== CONFIGURATION FFMPEG ====================

def configure_ffmpeg_local():
    project_root = Path(__file__).resolve().parent.parent.parent
    ffmpeg_dir = project_root / "models" / "ffmpeg-8.0.1-essentials_build" / "bin"
    if ffmpeg_dir.exists():
        ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            os.environ["PATH"] = f"{ffmpeg_dir};{os.environ.get('PATH', '')}"
            try:
                from pydub import AudioSegment
                AudioSegment.converter = str(ffmpeg_exe)
                AudioSegment.ffmpeg = str(ffmpeg_exe)
                ffprobe_exe = ffmpeg_dir / "ffprobe.exe"
                if ffprobe_exe.exists():
                    AudioSegment.ffprobe = str(ffprobe_exe)
                logger.info(f"✅ ffmpeg configuré: {ffmpeg_dir}")
                return True
            except ImportError:
                pass
    return False

configure_ffmpeg_local()


# ==================== MOTEURS TTS ====================

class TTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        pass


class CoquiTTSEngine(TTSEngine):
    def __init__(self):
        from backend.services.coqui_tts_engine import CoquiTTSEngine as CoquiEngine
        self.engine = CoquiEngine()
        self.voices = self.engine.voices
        logger.info("✅ Coqui TTS prêt")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        return self.engine.synthesize(text, language)


class EdgeTTSEngine(TTSEngine):
    def __init__(self):
        from backend.services.edge_tts_engine import EdgeTTSEngine as EdgeEngine
        self.engine = EdgeEngine()
        self.voices = self.engine.voices
        logger.info("✅ Edge-TTS prêt")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        return self.engine.synthesize(text, language)


class GoogleTTS(TTSEngine):
    def __init__(self):
        from gtts import gTTS
        self.gTTS = gTTS
        self.voices = {"ar": "gtts-ar", "en": "gtts-en", "fr": "gtts-fr"}
        logger.info("✅ gTTS prêt")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        import tempfile, os
        try:
            from pydub import AudioSegment
        except ImportError:
            return b""
        try:
            lang_code = language if language in ['ar', 'en', 'fr'] else 'ar'
            tts = self.gTTS(text=text, lang=lang_code, slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_mp3 = tmp.name
            tts.save(tmp_mp3)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_wav = tmp.name
            try:
                audio = AudioSegment.from_mp3(tmp_mp3)
                audio.export(tmp_wav, format="wav")
                with open(tmp_wav, 'rb') as f:
                    return f.read()
            finally:
                for p in [tmp_mp3, tmp_wav]:
                    try: os.unlink(p)
                    except: pass
        except Exception as e:
            logger.error(f"❌ gTTS: {e}")
            return b""


# ==================== SERVICE TTS AVEC CHARGEMENT LAZY ====================

class TTSService:
    """
    Service TTS avec chargement Coqui en arrière-plan.

    Au démarrage: utilise Edge-TTS ou gTTS (instantané).
    En parallèle: charge Coqui TTS dans un thread.
    Une fois Coqui prêt: bascule automatiquement sur lui.
    """

    def __init__(self, fast_engine: TTSEngine, cache_dir: Optional[Path] = None):
        self._fast_engine = fast_engine        # Moteur rapide (Edge-TTS / gTTS)
        self._coqui_engine: Optional[TTSEngine] = None  # Sera chargé en arrière-plan
        self._coqui_ready = False
        self._loading_lock = threading.Lock()
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def engine(self) -> TTSEngine:
        """Retourne Coqui si prêt, sinon le moteur rapide."""
        if self._coqui_ready and self._coqui_engine:
            return self._coqui_engine
        return self._fast_engine

    def start_coqui_background_loading(self):
        """Lance le chargement de Coqui dans un thread daemon."""
        def _load():
            logger.info("🔄 Chargement Coqui TTS en arrière-plan...")
            try:
                engine = CoquiTTSEngine()
                with self._loading_lock:
                    self._coqui_engine = engine
                    self._coqui_ready = True
                logger.info("✅ Coqui TTS chargé et actif (remplacement Edge-TTS)")
            except Exception as e:
                logger.warning(f"⚠️ Coqui TTS non disponible: {e}")

        t = threading.Thread(target=_load, daemon=True, name="coqui-loader")
        t.start()

    def is_coqui_ready(self) -> bool:
        return self._coqui_ready

    def synthesize(self, text: str, language: str = "ar", use_cache: bool = True) -> bytes:
        if not text or not text.strip():
            return b""

        active_engine = self.engine
        voice_name = "unknown"
        if hasattr(active_engine, 'voices') and isinstance(active_engine.voices, dict):
            voice_name = active_engine.voices.get(language, "unknown")

        logger.info(f"🎙️ TTS | moteur={'coqui' if self._coqui_ready else 'fast'} | langue={language} | voix={voice_name}")

        if use_cache and self.cache_dir:
            cache_key = self._get_cache_key(text, language, voice_name)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            if cache_path.exists():
                logger.info(f"✅ Cache hit: {cache_path.name}")
                with open(cache_path, 'rb') as f:
                    return f.read()

        audio_data = active_engine.synthesize(text, language)

        if use_cache and self.cache_dir and audio_data:
            cache_key = self._get_cache_key(text, language, voice_name)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            try:
                with open(cache_path, 'wb') as f:
                    f.write(audio_data)
            except Exception as e:
                logger.warning(f"⚠️ Cache save: {e}")

        return audio_data

    def synthesize_to_file(self, text: str, output_path: Path, language: str = "ar", use_cache: bool = True) -> bool:
        audio_data = self.synthesize(text, language, use_cache)
        if not audio_data:
            return False
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            return True
        except Exception as e:
            logger.error(f"❌ Sauvegarde: {e}")
            return False

    @staticmethod
    def _get_cache_key(text: str, language: str, voice: str = "") -> str:
        content = f"{text}_{language}_{voice}"
        return hashlib.md5(content.encode()).hexdigest()


def get_tts_service() -> TTSService:
    """
    Crée le service TTS INSTANTANÉMENT.
    - Démarre avec Edge-TTS (rapide, disponible immédiatement)
    - Lance Coqui en arrière-plan
    - Bascule sur Coqui automatiquement une fois chargé
    """
    from backend.config import settings

    # ── Moteur rapide de secours (démarre instantanément) ──
    fast_engine = None

    try:
        fast_engine = EdgeTTSEngine()
        logger.info("✅ Edge-TTS actif (démarrage instantané)")
    except Exception as e:
        logger.warning(f"⚠️ Edge-TTS indisponible: {e}")

    if fast_engine is None:
        try:
            fast_engine = GoogleTTS()
            logger.info("✅ gTTS actif (fallback)")
        except Exception as e:
            logger.error(f"❌ gTTS indisponible: {e}")
            raise ValueError("Aucun moteur TTS rapide disponible!")

    # ── Créer le service avec le moteur rapide ──
    service = TTSService(fast_engine, cache_dir=settings.TTS_CACHE_DIR)

    # ── Lancer Coqui en arrière-plan (non-bloquant) ──
    service.start_coqui_background_loading()

    return service