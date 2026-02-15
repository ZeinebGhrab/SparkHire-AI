"""
Service TTS (Text-to-Speech) - VERSION AVEC FFMPEG LOCAL
Support pour gTTS (Google Text-to-Speech)
Configure automatiquement ffmpeg depuis models/ffmpeg-8.0.1-essentials_build
"""

import logging
import hashlib
import os
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ==================== CONFIGURATION AUTOMATIQUE FFMPEG ====================

def configure_ffmpeg_local():
    """Configure automatiquement ffmpeg depuis le dossier local du projet"""
    
    project_root = Path(__file__).resolve().parent.parent.parent
    ffmpeg_dir = project_root / "models" / "ffmpeg-8.0.1-essentials_build" / "bin"
    
    if ffmpeg_dir.exists():
        ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
        ffprobe_exe = ffmpeg_dir / "ffprobe.exe"
        
        if ffmpeg_exe.exists():
            os.environ["PATH"] = f"{ffmpeg_dir};{os.environ.get('PATH', '')}"
            
            try:
                from pydub import AudioSegment
                AudioSegment.converter = str(ffmpeg_exe)
                AudioSegment.ffmpeg = str(ffmpeg_exe)
                if ffprobe_exe.exists():
                    AudioSegment.ffprobe = str(ffprobe_exe)
                
                logger.info(f"✅ ffmpeg configuré depuis: {ffmpeg_dir}")
                return True
            except ImportError:
                logger.warning("pydub non installé")
                return False
        else:
            logger.warning(f"⚠️ ffmpeg.exe non trouvé dans: {ffmpeg_dir}")
            return False
    else:
        logger.warning(f"⚠️ Dossier ffmpeg non trouvé: {ffmpeg_dir}")
        return False

configure_ffmpeg_local()


# ==================== MOTEURS TTS ====================

class TTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        pass


class GoogleTTS(TTSEngine):
    def __init__(self):
        try:
            from gtts import gTTS
            self.gTTS = gTTS
            logger.info("✅ gTTS (Google Text-to-Speech) initialisé avec succès")
        except ImportError:
            raise ImportError("gTTS non installé: pip install gtts")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        import tempfile
        import os
        
        try:
            from pydub import AudioSegment
        except ImportError:
            logger.error("❌ pydub non installé: pip install pydub")
            return b""
        
        try:
            if not text or len(text.strip()) == 0:
                logger.error("❌ ERREUR: Texte vide fourni à gTTS")
                return b""
            
            logger.info(f"🔊 gTTS: Synthèse de '{text[:100]}...' (langue: {language})")
            
            lang_code = language if language in ['ar', 'en', 'fr'] else 'ar'
            
            tts = self.gTTS(text=text, lang=lang_code, slow=False)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                tmp_mp3_path = tmp_mp3.name
            
            tts.save(tmp_mp3_path)
            logger.info(f"📁 Audio MP3 temporaire créé: {tmp_mp3_path}")
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                tmp_wav_path = tmp_wav.name
            
            try:
                audio = AudioSegment.from_mp3(tmp_mp3_path)
                audio.export(tmp_wav_path, format="wav")
                
                with open(tmp_wav_path, 'rb') as f:
                    audio_data = f.read()
                
                logger.info(f"✅ Audio synthétisé avec succès: {len(audio_data)} bytes")
                
                return audio_data
                
            finally:
                try:
                    os.unlink(tmp_mp3_path)
                    os.unlink(tmp_wav_path)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"❌ Erreur synthèse gTTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return b""


class TTSService:
    def __init__(self, engine: TTSEngine, cache_dir: Optional[Path] = None):
        self.engine = engine
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, text: str, language: str = "ar", use_cache: bool = True) -> bytes:
        if not text or len(text.strip()) == 0:
            logger.error("❌ TTSService: Texte vide reçu!")
            return b""
        
        logger.info(f"🎤 TTSService.synthesize() appelé:")
        logger.info(f"   Texte: '{text[:100]}...'")
        logger.info(f"   Langue: {language}")
        
        if use_cache and self.cache_dir:
            cache_key = self._get_cache_key(text, language)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            if cache_path.exists():
                logger.info(f"💾 Cache hit: {cache_path.name}")
                with open(cache_path, 'rb') as f:
                    return f.read()

        audio_data = self.engine.synthesize(text, language)

        if use_cache and self.cache_dir and audio_data:
            cache_key = self._get_cache_key(text, language)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            try:
                with open(cache_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"💾 Cache saved: {cache_path.name}")
            except Exception as e:
                logger.warning(f"Cache save failed: {e}")

        return audio_data

    def synthesize_to_file(self, text: str, output_path: Path, language: str = "ar", use_cache: bool = True) -> bool:
        logger.info(f"📝 synthesize_to_file() appelé:")
        logger.info(f"   Texte: '{text[:100]}...'")
        logger.info(f"   Output: {output_path}")
        
        audio_data = self.synthesize(text, language, use_cache)
        
        if not audio_data:
            logger.error("❌ Aucune donnée audio générée!")
            return False
            
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"✅ Audio sauvegardé: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde: {e}")
            return False

    @staticmethod
    def _get_cache_key(text: str, language: str) -> str:
        content = f"{text}_{language}"
        return hashlib.md5(content.encode()).hexdigest()


def get_tts_service() -> TTSService:
    from backend.config import settings

    if settings.TTS_ENGINE == "gtts":
        logger.info("🌐 Utilisation de gTTS (Google TTS) - Meilleur support arabe")
        engine = GoogleTTS()
    else:
        logger.error(f"❌ Moteur TTS inconnu: {settings.TTS_ENGINE}")
        logger.info("🔄 Fallback sur gTTS...")
        try:
            engine = GoogleTTS()
        except:
            raise ValueError(f"Impossible d'initialiser le moteur TTS")

    return TTSService(engine, cache_dir=settings.TTS_CACHE_DIR)