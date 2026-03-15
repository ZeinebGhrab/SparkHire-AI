"""
Service ASR — Whisper (faster-whisper) + Vosk
Whisper recommandé : meilleure précision multilingue AR/FR/EN.
GPU auto-détecté avec fallback CPU si CUDA non disponible.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import io
import wave
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Mapping langues → codes Whisper
WHISPER_LANG_MAP = {
    "ar": "ar",
    "fr": "fr",
    "en": "en",
}


class ASREngine(ABC):
    @abstractmethod
    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        pass


# ── Faster-Whisper ────────────────────────────────────────────────────────────

class WhisperASR(ASREngine):
    """
    Moteur ASR Whisper local via faster-whisper.
    GPU auto-détecté — fallback CPU automatique si CUDA non disponible.
    """

    def __init__(self, model_size: str = "medium", device: str = "cpu", compute_type: str = "int8"):
        try:
            from faster_whisper import WhisperModel

            # ── Détection GPU et fallback automatique ─────────────────────────
            actual_device       = device
            actual_compute_type = compute_type

            if device == "cuda":
                try:
                    import torch
                    if not torch.cuda.is_available():
                        logger.warning(
                            "⚠️  CUDA demandé mais non disponible → fallback CPU/int8"
                        )
                        actual_device       = "cpu"
                        actual_compute_type = "int8"
                    else:
                        gpu_name = torch.cuda.get_device_name(0)
                        vram_gb  = torch.cuda.get_device_properties(0).total_memory / 1e9
                        logger.info(
                            f"🎮 GPU détecté : {gpu_name} | VRAM={vram_gb:.1f} GB"
                        )
                        # float16 requis sur GPU — forcer si oublié
                        if actual_compute_type == "int8":
                            actual_compute_type = "float16"
                            logger.info(
                                "ℹ️  compute_type int8 → float16 (GPU)"
                            )
                except ImportError:
                    logger.warning(
                        "⚠️  torch non installé — impossible de vérifier CUDA → fallback CPU"
                    )
                    actual_device       = "cpu"
                    actual_compute_type = "int8"

            logger.info(
                f"Chargement Whisper '{model_size}' | "
                f"device={actual_device} | compute={actual_compute_type}"
            )
            self.model = WhisperModel(
                model_size,
                device=actual_device,
                compute_type=actual_compute_type,
                download_root=str(
                    Path(__file__).parent.parent.parent / "models" / "whisper"
                ),
            )
            self.model_size   = model_size
            self.actual_device = actual_device
            logger.info(
                f"✅ Whisper '{model_size}' prêt sur {actual_device.upper()}"
            )

        except ImportError:
            raise ImportError(
                "faster-whisper non installé : pip install faster-whisper"
            )

    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        """
        Transcrit des bytes audio (WAV de préférence) en texte.
        Retourne une chaîne vide en cas d'erreur.
        """
        if not audio_data or len(audio_data) < 100:
            return ""

        lang = WHISPER_LANG_MAP.get(language, language)

        # Écriture dans un fichier temporaire WAV
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            if audio_data[:4] == b"RIFF":
                tmp.write(audio_data)
            else:
                # Encapsuler en WAV si c'est du PCM brut
                with wave.open(tmp, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(audio_data)

        try:
            segments, info = self.model.transcribe(
                tmp_path,
                language=lang,
                beam_size=5,
                best_of=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    threshold=0.5,
                ),
                condition_on_previous_text=False,
            )
            transcript = " ".join(seg.text.strip() for seg in segments).strip()

            logger.info(
                f"✅ Whisper [{lang}] [{self.actual_device.upper()}] "
                f"| durée={info.duration:.1f}s "
                f"| '{transcript[:80]}'"
            )
            return transcript

        except Exception as e:
            logger.error(f"Whisper transcription : {e}")
            return ""
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── Vosk (fallback offline) ───────────────────────────────────────────────────

class VoskASR(ASREngine):
    """Moteur ASR Vosk — entièrement hors-ligne, modèle arabe uniquement."""

    def __init__(self, model_path: Path):
        try:
            from vosk import Model, KaldiRecognizer

            if not model_path.exists():
                raise FileNotFoundError(f"Modèle Vosk introuvable : {model_path}")

            logger.info(f"Chargement Vosk : {model_path}")
            self.model = Model(str(model_path))
            self.KaldiRecognizer = KaldiRecognizer
            logger.info("Vosk prêt")

        except ImportError:
            raise ImportError("Vosk non installé : pip install vosk")

    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        try:
            recognizer = self.KaldiRecognizer(self.model, 16000)
            recognizer.SetWords(True)

            with io.BytesIO(audio_data) as buf:
                with wave.open(buf, "rb") as wf:
                    while True:
                        data = wf.readframes(4000)
                        if not data:
                            break
                        recognizer.AcceptWaveform(data)

            result = json.loads(recognizer.FinalResult())
            transcript = result.get("text", "")
            logger.info(f"Vosk : '{transcript}'")
            return transcript

        except Exception as e:
            logger.error(f"Vosk : {e}")
            return ""


# ── Service unifié ────────────────────────────────────────────────────────────

class ASRService:
    def __init__(self, engine: ASREngine):
        self.engine = engine

    def transcribe(self, audio_data: bytes, language: str = "ar") -> str:
        return self.engine.transcribe(audio_data, language)


def get_asr_service() -> ASRService:
    """Factory — crée le service ASR selon la config."""
    from backend.config import settings

    if settings.ASR_ENGINE == "faster-whisper":
        engine = WhisperASR(
            model_size=settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
    elif settings.ASR_ENGINE == "vosk":
        engine = VoskASR(settings.VOSK_MODEL_PATH)
    else:
        raise ValueError(f"Moteur ASR inconnu : {settings.ASR_ENGINE}")

    return ASRService(engine)