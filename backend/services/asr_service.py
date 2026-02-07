"""
Service ASR (Automatic Speech Recognition)
Support pour Vosk et Faster-Whisper
"""

import io
import wave
import json
import logging
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ASREngine(ABC):
    """Interface abstraite pour les moteurs ASR"""
    
    @abstractmethod
    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        """Transcrire audio en texte"""
        pass


class VoskASR(ASREngine):
    """Moteur ASR utilisant Vosk"""
    
    def __init__(self, model_path: Path):
        try:
            from vosk import Model, KaldiRecognizer
            
            self.model_path = model_path
            
            if not model_path.exists():
                raise FileNotFoundError(f"Modèle Vosk introuvable: {model_path}")
            
            logger.info(f"Chargement du modèle Vosk: {model_path}")
            self.model = Model(str(model_path))
            self.KaldiRecognizer = KaldiRecognizer
            logger.info("Modèle Vosk chargé avec succès")
            
        except ImportError:
            raise ImportError("Vosk n'est pas installé. pip install vosk")
    
    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        """Transcrire audio WAV en texte"""
        try:
            # Créer un recognizer
            recognizer = self.KaldiRecognizer(self.model, 16000)
            recognizer.SetWords(True)
            
            # Lire les données audio
            with io.BytesIO(audio_data) as audio_buffer:
                with wave.open(audio_buffer, 'rb') as wf:
                    # Vérifier le format
                    if wf.getnchannels() != 1:
                        raise ValueError("L'audio doit être mono")
                    if wf.getsampwidth() != 2:
                        raise ValueError("L'audio doit être 16-bit")
                    if wf.getframerate() != 16000:
                        logger.warning(f"Sample rate {wf.getframerate()} != 16000")
                    
                    # Transcrire
                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        recognizer.AcceptWaveform(data)
                    
                    # Résultat final
                    result = json.loads(recognizer.FinalResult())
                    transcript = result.get("text", "")
                    
                    logger.info(f"Transcription Vosk: '{transcript}'")
                    return transcript
        
        except Exception as e:
            logger.error(f"Erreur transcription Vosk: {e}")
            return ""


class WhisperASR(ASREngine):
    """Moteur ASR utilisant Faster-Whisper"""
    
    def __init__(self, model_size: str = "base"):
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Chargement du modèle Whisper: {model_size}")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info("✅ Modèle Whisper chargé avec succès")
            
        except ImportError:
            raise ImportError("Faster-Whisper n'est pas installé. pip install faster-whisper")
    
    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        """Transcrire audio en texte"""
        try:
            # Sauvegarder temporairement
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                # Transcrire
                segments, info = self.model.transcribe(
                    tmp_path,
                    language=language,
                    beam_size=5
                )
                
                # Combiner segments
                transcript = " ".join([segment.text for segment in segments])
                
                logger.info(f"Transcription Whisper: '{transcript}'")
                return transcript.strip()
            
            finally:
                # Nettoyer
                os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"Erreur transcription Whisper: {e}")
            return ""


class ASRService:
    """Service ASR unifié"""
    
    def __init__(self, engine: ASREngine):
        self.engine = engine
    
    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        """Transcrire audio en texte"""
        return self.engine.transcribe(audio_data, language)


def get_asr_service() -> ASRService:
    """Factory pour créer le service ASR"""
    from backend.config import settings
    
    if settings.ASR_ENGINE == "vosk":
        engine = VoskASR(settings.VOSK_MODEL_PATH)
    elif settings.ASR_ENGINE == "faster-whisper":
        engine = WhisperASR(settings.WHISPER_MODEL_SIZE)
    else:
        raise ValueError(f"Moteur ASR inconnu: {settings.ASR_ENGINE}")
    
    return ASRService(engine)