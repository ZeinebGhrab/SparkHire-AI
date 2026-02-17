"""
Service TTS (Text-to-Speech) - VERSION AVEC COQUI TTS
Support pour Coqui TTS (priorité), Edge-TTS, et gTTS (fallback)
Cache basé sur texte + langue + voix
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
                logger.warning("⚠️ pydub non installé")
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


class CoquiTTSEngine(TTSEngine):
    """Moteur Coqui TTS (Open Source, haute qualité)"""
    
    def __init__(self):
        try:
            from backend.services.coqui_tts_engine import CoquiTTSEngine as CoquiEngine
            self.engine = CoquiEngine()
            # Stocker les voix pour le cache
            self.voices = self.engine.voices
            logger.info("✅ Coqui TTS initialisé - Voix multilingues naturelles")
        except ImportError:
            raise ImportError("Coqui TTS non installé: pip install TTS")
    
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        return self.engine.synthesize(text, language)


class EdgeTTSEngine(TTSEngine):
    """Moteur Edge-TTS avec voix féminine"""
    
    def __init__(self):
        try:
            from backend.services.edge_tts_engine import EdgeTTSEngine as EdgeEngine
            self.engine = EdgeEngine()
            # Stocker les voix pour le cache
            self.voices = self.engine.voices
            logger.info("✅ Edge-TTS (Microsoft) initialisé - Voix féminine")
        except ImportError:
            raise ImportError("Edge-TTS non installé: pip install edge-tts")
    
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        return self.engine.synthesize(text, language)


class GoogleTTS(TTSEngine):
    """Moteur Google TTS (voix par défaut)"""
    
    def __init__(self):
        try:
            from gtts import gTTS
            self.gTTS = gTTS
            # Pas de voix multiples pour gTTS
            self.voices = {"ar": "gtts-ar", "en": "gtts-en", "fr": "gtts-fr"}
            logger.info("✅ gTTS (Google Text-to-Speech) initialisé")
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
                logger.error("❌ Texte vide fourni à gTTS")
                return b""
            
            logger.info(f"🎤 gTTS: Synthèse de '{text[:100]}...' (langue: {language})")
            
            lang_code = language if language in ['ar', 'en', 'fr'] else 'ar'
            
            tts = self.gTTS(text=text, lang=lang_code, slow=False)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                tmp_mp3_path = tmp_mp3.name
            
            tts.save(tmp_mp3_path)
            logger.info(f"✅ Audio MP3 temporaire créé: {tmp_mp3_path}")
            
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
        """
        Synthétiser du texte en audio
        
        Le cache inclut la voix utilisée
        """
        if not text or len(text.strip()) == 0:
            logger.error("❌ TTSService: Texte vide reçu!")
            return b""
        
        # Obtenir le nom de la voix depuis l'engine
        voice_name = "unknown"
        if hasattr(self.engine, 'voices') and isinstance(self.engine.voices, dict):
            voice_name = self.engine.voices.get(language, "unknown")
        
        logger.info(f"🎙️ TTSService.synthesize() appelé:")
        logger.info(f"   Texte: '{text[:100]}...'")
        logger.info(f"   Langue: {language}")
        logger.info(f"   Voix: {voice_name}")
        
        # Vérifier le cache avec le nom de la voix
        if use_cache and self.cache_dir:
            cache_key = self._get_cache_key(text, language, voice_name)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            if cache_path.exists():
                logger.info(f"✅ Cache hit: {cache_path.name} (voix: {voice_name})")
                with open(cache_path, 'rb') as f:
                    return f.read()

        # Générer l'audio
        audio_data = self.engine.synthesize(text, language)

        # Sauvegarder dans le cache avec le nom de la voix
        if use_cache and self.cache_dir and audio_data:
            cache_key = self._get_cache_key(text, language, voice_name)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            try:
                with open(cache_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"✅ Cache saved: {cache_path.name} (voix: {voice_name})")
            except Exception as e:
                logger.warning(f"⚠️ Cache save failed: {e}")

        return audio_data

    def synthesize_to_file(self, text: str, output_path: Path, language: str = "ar", use_cache: bool = True) -> bool:
        """Synthétiser et sauvegarder directement dans un fichier"""
        logger.info(f"🎙️ synthesize_to_file() appelé:")
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
    def _get_cache_key(text: str, language: str, voice: str = "") -> str:
        """
        Générer une clé de cache incluant le texte, la langue ET la voix
        
        Cela permet d'avoir des caches différents pour chaque voix,
        évitant ainsi le problème d'entendre l'ancienne voix quand on change.
        """
        content = f"{text}_{language}_{voice}"
        return hashlib.md5(content.encode()).hexdigest()


def get_tts_service() -> TTSService:
    """Factory pour créer le service TTS avec Coqui TTS en priorité absolue"""
    from backend.config import settings

    # 🎯 PRIORITÉ 1: Coqui TTS (Open Source, meilleure qualité)
    try:
        logger.info("🎤 Initialisation Coqui TTS (priorité 1)...")
        engine = CoquiTTSEngine()
        logger.info("✅ Coqui TTS activé - Voix multilingues naturelles de haute qualité")
        return TTSService(engine, cache_dir=settings.TTS_CACHE_DIR)
    except Exception as e:
        logger.warning(f"⚠️ Coqui TTS indisponible: {e}")
        import traceback
        logger.warning(traceback.format_exc())

    # 🎯 PRIORITÉ 2: Edge-TTS (Microsoft, voix féminine naturelle)
    try:
        logger.warning("🎤 Fallback sur Edge-TTS (priorité 2)...")
        engine = EdgeTTSEngine()
        logger.warning("✅ Edge-TTS activé - Voix féminine Microsoft")
        return TTSService(engine, cache_dir=settings.TTS_CACHE_DIR)
    except Exception as e:
        logger.error(f"⚠️ Edge-TTS indisponible: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # 🎯 PRIORITÉ 3: gTTS (Google, fallback robotique)
    try:
        logger.warning("🎤 Fallback sur gTTS (priorité 3)...")
        engine = GoogleTTS()
        logger.warning("⚠️ gTTS utilisé - Qualité audio limitée (voix robotique)")
        return TTSService(engine, cache_dir=settings.TTS_CACHE_DIR)
    except Exception as e:
        logger.error(f"❌ gTTS indisponible: {e}")

    raise ValueError("❌ Aucun moteur TTS disponible!")