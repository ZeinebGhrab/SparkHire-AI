"""
Service TTS (Text-to-Speech) - VERSION CORRIGÉE
Support pour pyttsx3 et Coqui-TTS
Compatible Windows et lecture directe pour tests locaux
"""

import logging
import hashlib
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """Interface abstraite pour les moteurs TTS"""

    @abstractmethod
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        """Transcrire texte en audio"""
        pass


# --------------------------- Pyttsx3 TTS ---------------------------

class Pyttsx3TTS(TTSEngine):
    """Moteur TTS utilisant pyttsx3 - VERSION WINDOWS"""

    def __init__(self):
        try:
            import pyttsx3
            import platform

            self.pyttsx3 = pyttsx3

            logger.info("Initialisation pyttsx3 TTS")
            test_engine = pyttsx3.init()
            voices = test_engine.getProperty('voices')

            # Chercher voix française
            french_voice = None
            for voice in voices:
                if 'french' in voice.name.lower() or 'fr-fr' in voice.id.lower():
                    french_voice = voice.id
                    logger.info(f"✅ Voix française trouvée: {voice.name}")
                    break

            if french_voice:
                test_engine.setProperty('voice', french_voice)
            else:
                logger.warning("⚠️ Aucune voix française trouvée, utilisation de la voix par défaut")

            test_engine.setProperty('rate', 150)
            test_engine.setProperty('volume', 1.0)

            self.voice_id = french_voice
            self.rate = 150
            self.volume = 1.0

            # Libérer le moteur
            del test_engine
            logger.info("✅ pyttsx3 TTS initialisé avec succès")

            # Windows : module pour jouer le son local
            self.is_windows = platform.system().lower() == "windows"
            if self.is_windows:
                try:
                    import simpleaudio
                    self.simpleaudio = simpleaudio
                except ImportError:
                    logger.warning("⚠️ simpleaudio non installé: pip install simpleaudio")
                    self.simpleaudio = None

        except ImportError:
            raise ImportError("pyttsx3 n'est pas installé. pip install pyttsx3")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation pyttsx3: {e}")
            raise

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        """Synthétiser texte en audio WAV et jouer sur Windows"""
        import tempfile
        import os
        import time

        try:
            engine = self.pyttsx3.init()
            if self.voice_id:
                engine.setProperty('voice', self.voice_id)
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            logger.info(f"🔊 Synthèse TTS: '{text[:50]}...'")
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

            # Attendre la création du fichier
            time.sleep(0.5)
            if not os.path.exists(tmp_path):
                logger.error(f"❌ Fichier audio non créé: {tmp_path}")
                return b""

            # Jouer le son sur Windows
            if self.is_windows and self.simpleaudio:
                try:
                    wave_obj = self.simpleaudio.WaveObject.from_wave_file(tmp_path)
                    play_obj = wave_obj.play()
                    play_obj.wait_done()
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de jouer le son: {e}")

            # Lire le fichier pour retourner bytes
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()

            # Nettoyer fichier temporaire
            try:
                os.unlink(tmp_path)
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Impossible de supprimer le fichier temporaire: {cleanup_error}")

            del engine
            logger.info(f"✅ Audio synthétisé avec succès: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"❌ Erreur synthèse pyttsx3: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return b""


# --------------------------- Coqui-TTS ---------------------------

class CoquiTTS(TTSEngine):
    """Moteur TTS utilisant Coqui-TTS"""

    def __init__(self, model_name: str = "tts_models/ar/cv/vits"):
        try:
            from TTS.api import TTS
            logger.info(f"Chargement du modèle Coqui-TTS: {model_name}")
            self.tts = TTS(model_name=model_name)
            logger.info("Coqui-TTS chargé avec succès")
        except ImportError:
            raise ImportError("Coqui-TTS n'est pas installé. pip install TTS")
        except Exception as e:
            logger.error(f"Erreur chargement Coqui-TTS: {e}")
            from TTS.api import TTS
            self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

    def synthesize(self, text: str, language: str = "ar") -> bytes:
        import tempfile
        import os

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            self.tts.tts_to_file(text=text, file_path=tmp_path)
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            os.unlink(tmp_path)
            logger.info(f"Audio synthétisé (Coqui): {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            logger.error(f"Erreur synthèse Coqui-TTS: {e}")
            return b""


# --------------------------- Service TTS unifié ---------------------------

class TTSService:
    """Service TTS avec cache"""

    def __init__(self, engine: TTSEngine, cache_dir: Optional[Path] = None):
        self.engine = engine
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, text: str, language: str = "ar", use_cache: bool = True) -> bytes:
        """Synthétiser texte avec cache"""
        if use_cache and self.cache_dir:
            cache_key = self._get_cache_key(text, language)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            if cache_path.exists():
                logger.info(f"🎯 Cache hit: {cache_path.name}")
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
                logger.warning(f"⚠️ Impossible de sauvegarder en cache: {e}")

        return audio_data

    def synthesize_to_file(self, text: str, output_path: Path, language: str = "ar", use_cache: bool = True) -> bool:
        """Synthétiser et sauvegarder dans un fichier"""
        audio_data = self.synthesize(text, language, use_cache)
        if not audio_data:
            logger.error("❌ Échec de la synthèse audio")
            return False
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"✅ Audio sauvegardé: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde fichier: {e}")
            return False

    @staticmethod
    def _get_cache_key(text: str, language: str) -> str:
        content = f"{text}_{language}"
        return hashlib.md5(content.encode()).hexdigest()


# --------------------------- Factory ---------------------------

def get_tts_service() -> TTSService:
    from backend.config import settings

    if settings.TTS_ENGINE == "pyttsx3":
        engine = Pyttsx3TTS()
    elif settings.TTS_ENGINE == "coqui":
        engine = CoquiTTS()
    else:
        raise ValueError(f"Moteur TTS inconnu: {settings.TTS_ENGINE}")

    return TTSService(engine, cache_dir=settings.TTS_CACHE_DIR)
