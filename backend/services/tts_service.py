"""
Service TTS (Text-to-Speech)
Support pour pyttsx3 et Coqui-TTS
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
        """Synthétiser texte en audio"""
        pass


class Pyttsx3TTS(TTSEngine):
    """Moteur TTS utilisant pyttsx3"""
    
    def __init__(self):
        try:
            import pyttsx3
            
            logger.info("Initialisation pyttsx3 TTS")
            self.engine = pyttsx3.init()
            
            # Configuration
            self.engine.setProperty('rate', 150)  # Vitesse
            self.engine.setProperty('volume', 0.9)  # Volume
            
            logger.info("pyttsx3 TTS initialisé")
            
        except ImportError:
            raise ImportError("pyttsx3 n'est pas installé. pip install pyttsx3")
        except Exception as e:
            logger.error(f"Erreur initialisation pyttsx3: {e}")
            raise
    
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        """Synthétiser texte en audio WAV"""
        import tempfile
        import os
        
        try:
            # Créer fichier temporaire
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            # Synthétiser
            self.engine.save_to_file(text, tmp_path)
            self.engine.runAndWait()
            
            # Lire le fichier
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # Nettoyer
            os.unlink(tmp_path)
            
            logger.info(f"✅ Audio synthétisé: {len(audio_data)} bytes")
            return audio_data
        
        except Exception as e:
            logger.error(f"Erreur synthèse pyttsx3: {e}")
            return b""


class CoquiTTS(TTSEngine):
    """Moteur TTS utilisant Coqui-TTS"""
    
    def __init__(self, model_name: str = "tts_models/ar/cv/vits"):
        try:
            from TTS.api import TTS
            
            logger.info(f"Chargement du modèle Coqui-TTS: {model_name}")
            self.tts = TTS(model_name=model_name)
            logger.info("✅ Coqui-TTS chargé avec succès")
            
        except ImportError:
            raise ImportError("Coqui-TTS n'est pas installé. pip install TTS")
        except Exception as e:
            logger.error(f"Erreur chargement Coqui-TTS: {e}")
            # Fallback vers un modèle par défaut
            logger.info("Utilisation du modèle par défaut")
            from TTS.api import TTS
            self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
    
    def synthesize(self, text: str, language: str = "ar") -> bytes:
        """Synthétiser texte en audio WAV"""
        import tempfile
        import os
        
        try:
            # Créer fichier temporaire
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            # Synthétiser
            self.tts.tts_to_file(text=text, file_path=tmp_path)
            
            # Lire le fichier
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # Nettoyer
            os.unlink(tmp_path)
            
            logger.info(f"✅ Audio synthétisé (Coqui): {len(audio_data)} bytes")
            return audio_data
        
        except Exception as e:
            logger.error(f"Erreur synthèse Coqui-TTS: {e}")
            return b""


class TTSService:
    """Service TTS unifié avec cache"""
    
    def __init__(self, engine: TTSEngine, cache_dir: Optional[Path] = None):
        self.engine = engine
        self.cache_dir = cache_dir
        
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
    
    def synthesize(self, text: str, language: str = "ar", use_cache: bool = True) -> bytes:
        """Synthétiser texte en audio avec cache"""
        
        # Vérifier le cache
        if use_cache and self.cache_dir:
            cache_key = self._get_cache_key(text, language)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            
            if cache_path.exists():
                logger.info(f"Cache hit: {cache_path.name}")
                with open(cache_path, 'rb') as f:
                    return f.read()
        
        # Synthétiser
        audio_data = self.engine.synthesize(text, language)
        
        # Sauvegarder en cache
        if use_cache and self.cache_dir and audio_data:
            cache_key = self._get_cache_key(text, language)
            cache_path = self.cache_dir / f"{cache_key}.wav"
            
            with open(cache_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"Cache saved: {cache_path.name}")
        
        return audio_data
    
    def synthesize_to_file(
        self, 
        text: str, 
        output_path: Path, 
        language: str = "ar",
        use_cache: bool = True
    ) -> bool:
        """Synthétiser et sauvegarder directement dans un fichier"""
        audio_data = self.synthesize(text, language, use_cache)
        
        if not audio_data:
            return False
        
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        return True
    
    @staticmethod
    def _get_cache_key(text: str, language: str) -> str:
        """Générer clé de cache"""
        content = f"{text}_{language}"
        return hashlib.md5(content.encode()).hexdigest()


def get_tts_service() -> TTSService:
    """Factory pour créer le service TTS"""
    from backend.config import settings
    
    if settings.TTS_ENGINE == "pyttsx3":
        engine = Pyttsx3TTS()
    elif settings.TTS_ENGINE == "coqui":
        engine = CoquiTTS()
    else:
        raise ValueError(f"Moteur TTS inconnu: {settings.TTS_ENGINE}")
    
    return TTSService(engine, cache_dir=settings.TTS_CACHE_DIR)