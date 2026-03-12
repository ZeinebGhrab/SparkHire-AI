"""
Moteur TTS Coqui-TTS (Open Source / XTTS-v2)

"""

import importlib.util
import logging
import os
import sys
import tempfile
import types

logger = logging.getLogger(__name__)


# ==================================================================
# PATCH 1 : torch.load — weights_only=False pour PyTorch 2.6
# ==================================================================
try:
    import torch

    _original_torch_load = torch.load

    def _patched_torch_load(f, map_location=None, pickle_module=None, **kwargs):
        kwargs["weights_only"] = False
        if pickle_module is not None:
            return _original_torch_load(
                f, map_location=map_location, pickle_module=pickle_module, **kwargs
            )
        return _original_torch_load(f, map_location=map_location, **kwargs)

    torch.load = _patched_torch_load
    logger.info(" Patch torch.load appliqué (weights_only=False pour PyTorch 2.6)")

except ImportError:
    logger.warning(" PyTorch non disponible, patch torch.load non appliqué")


# ==================================================================
# PATCH 2 : torchvision stub avec __spec__ valide
# ==================================================================

def _make_stub_module(name: str) -> types.ModuleType:
    """Créer un module stub minimal avec __spec__ non-None."""
    mod = types.ModuleType(name)
    mod.__spec__ = importlib.util.spec_from_loader(name, loader=None, origin="stub")
    mod.__version__ = "0.0.0"
    mod.__path__ = []
    mod.__package__ = name
    return mod


try:
    import torchvision  # noqa: F401
    logger.info(" torchvision importé normalement")

except Exception as _tv_err:
    logger.warning(
        f" torchvision non disponible ({_tv_err}) — création d'un stub"
    )

    for _k in list(sys.modules.keys()):
        if _k == "torchvision" or _k.startswith("torchvision."):
            del sys.modules[_k]

    _tv_root = _make_stub_module("torchvision")
    sys.modules["torchvision"] = _tv_root

    for _sub in [
        "torchvision.transforms",
        "torchvision.transforms.functional",
        "torchvision._meta_registrations",
        "torchvision.datasets",
        "torchvision.io",
        "torchvision.models",
        "torchvision.ops",
        "torchvision.utils",
    ]:
        _stub = _make_stub_module(_sub)
        setattr(_tv_root, _sub.split(".")[-1], _stub)
        sys.modules[_sub] = _stub

    class _DynamicInterpolationMode:
        BILINEAR = "bilinear"
        NEAREST = "nearest"
        BICUBIC = "bicubic"
        NEAREST_EXACT = "nearest_exact"
        BOX = "box"
        HAMMING = "hamming"
        LANCZOS = "lanczos"

        def __getattr__(self, name: str):
            return name

    sys.modules["torchvision.transforms"].InterpolationMode = _DynamicInterpolationMode()
    logger.info("✅ Stub torchvision injecté (avec __spec__ valide)")


# ==================================================================
# PATCH 3 : GPT2PreTrainedModel manquant dans transformers récents
# ==================================================================
try:
    import transformers  # noqa: F401

    if not hasattr(transformers, "GPT2PreTrainedModel"):
        from transformers.models.gpt2.modeling_gpt2 import GPT2PreTrainedModel as _GPT2PT
        transformers.GPT2PreTrainedModel = _GPT2PT
        logger.info(" Patch transformers.GPT2PreTrainedModel appliqué")
    else:
        logger.info(" transformers.GPT2PreTrainedModel déjà disponible")

except Exception as _tf_err:
    logger.warning(f" Impossible de patcher transformers: {_tf_err}")


# ==================================================================
# PATCH 4 : GPT2InferenceModel manque GenerationMixin
# Doit être appelé APRES l'import de TTS (dans __init__)
# ==================================================================
def _patch_gpt2_inference_model():
    """
    Injecter GenerationMixin dans GPT2InferenceModel.
    transformers >= 4.50 retire GenerationMixin de PreTrainedModel,
    ce qui prive GPT2InferenceModel de la méthode .generate().
    """
    try:
        from transformers import GenerationMixin
        from TTS.tts.layers.xtts.gpt_inference import GPT2InferenceModel

        if not issubclass(GPT2InferenceModel, GenerationMixin):
            GPT2InferenceModel.__bases__ = (GenerationMixin,) + GPT2InferenceModel.__bases__
            logger.info(" Patch GPT2InferenceModel : GenerationMixin injecté")
        else:
            logger.info(" GPT2InferenceModel hérite déjà de GenerationMixin")

    except ImportError as e:
        logger.warning(f" Patch GPT2InferenceModel impossible (import): {e}")
    except Exception as e:
        logger.warning(f" Patch GPT2InferenceModel impossible: {e}")


# ==================================================================
# MOTEUR COQUI TTS
# ==================================================================


class CoquiTTSEngine:
    """Moteur TTS utilisant Coqui-TTS (Open Source / XTTS-v2)"""

    def __init__(self):
        try:
            from TTS.api import TTS

            # Appliquer PATCH 4 maintenant que TTS est importé
            _patch_gpt2_inference_model()

            model_path = "models/xtts_v2"

            if os.path.exists(model_path) and os.path.exists(
                os.path.join(model_path, "model.pth")
            ):
                logger.info(f" Chargement du modèle Coqui-TTS depuis: {model_path}")
                logger.info("    Modèle local détecté (pas de téléchargement)")
                self.tts = TTS(
                    model_path=model_path,
                    config_path=os.path.join(model_path, "config.json"),
                )
            else:
                logger.info(" Chargement XTTS-v2 depuis HuggingFace...")
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

            logger.info(" Coqui-TTS XTTS-v2 chargé avec succès")

            # FIX 5 : Récupérer les speakers disponibles
            try:
                speakers_raw = getattr(self.tts, "speakers", None)
                if not speakers_raw and hasattr(self.tts, "synthesizer"):
                    sm = getattr(self.tts.synthesizer, "tts_model", None)
                    if sm:
                        smanager = getattr(sm, "speaker_manager", None)
                        if smanager and hasattr(smanager, "speaker_names"):
                            speakers_raw = smanager.speaker_names

                self.available_speakers = list(speakers_raw) if speakers_raw else []
            except Exception as _sp_err:
                logger.warning(f"    Impossible de lister les speakers: {_sp_err}")
                self.available_speakers = []

            # Liste officielle XTTS-v2 si détection échoue
            if not self.available_speakers:
                logger.warning(
                    "    Speakers non détectés — utilisation de la liste XTTS-v2 par défaut"
                )
                self.available_speakers = [
                    "Ana Florence", "Daisy Studious", "Gracie Wise",
                    "Tammie Ema", "Alison Dietlinde", "Viktor Eka",
                    "Royston Min", "Abrahan Mack", "Adde Michal",
                    "Baldur Sanjin", "Craig Gutsy", "Damien Black",
                ]

            self.default_speaker = self.available_speakers[0] if self.available_speakers else None

            logger.info(
                f"   Speakers disponibles ({len(self.available_speakers)}): "
                f"{self.available_speakers[:5]}"
                f"{'...' if len(self.available_speakers) > 5 else ''}"
            )
            logger.info(f"   Speaker par défaut: {self.default_speaker}")

            self.languages = {"ar": "ar", "en": "en", "fr": "fr"}
            self.voices = {
                "ar": "coqui-xtts-ar",
                "en": "coqui-xtts-en",
                "fr": "coqui-xtts-fr",
            }
            self.generation_params = {"temperature": 0.65, "speed": 1.0}
            # XTTS-v2 outputs 24000 Hz — stored here for downstream resampling
            self.sample_rate = 24000
            logger.info(f"   Langues supportées: {list(self.languages.keys())}")

        except ImportError as e:
            logger.error(" Coqui-TTS non installé — Solution: pip install TTS")
            raise ImportError("Installez Coqui-TTS: pip install TTS") from e

        except Exception as e:
            logger.error(f" Erreur initialisation Coqui-TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def synthesize(
        self,
        text: str,
        language: str = "ar",
        speaker_wav: str | None = None,
    ) -> bytes:
        """
        Synthétiser texte en audio WAV.

        Args:
            text: Texte à synthétiser
            language: Code langue (ar, en, fr)
            speaker_wav: Chemin WAV pour clonage de voix (optionnel)

        Returns:
            bytes: Audio WAV
        """
        try:
            if not text or not text.strip():
                logger.error(" Texte vide fourni à Coqui-TTS")
                return b""

            lang = self.languages.get(language, "ar")
            logger.info(f"🎤 Coqui-TTS | langue={lang} | '{text[:80]}'")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                kwargs = {
                    "text": text,
                    "language": lang,
                    "file_path": tmp_path,
                    "speed": self.generation_params["speed"],
                    "temperature": self.generation_params["temperature"],
                }

                if speaker_wav and os.path.exists(speaker_wav):
                    kwargs["speaker_wav"] = speaker_wav
                    logger.info("   Mode: clonage de voix (speaker_wav)")
                elif self.default_speaker:
                    kwargs["speaker"] = self.default_speaker
                    logger.info(f"   Mode: speaker par défaut ({self.default_speaker})")
                else:
                    logger.warning("    Aucun speaker — tentative sans speaker")

                self.tts.tts_to_file(**kwargs)

                # Normalise WAV to 24000 Hz mono 16-bit for consistent playback
                audio_data = self._normalize_wav(tmp_path)

                if audio_data:
                    logger.info(f" Audio généré: {len(audio_data)} bytes @ {self.sample_rate}Hz")
                    return audio_data
                else:
                    logger.error(" Audio vide généré")
                    return b""

            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f" Erreur synthèse Coqui-TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return b""

    def _normalize_wav(self, wav_path: str) -> bytes:
        """
        Relit le WAV généré par XTTS-v2 et le réécrit en :
          - 24 000 Hz (sample rate natif XTTS-v2)
          - Mono
          - 16-bit PCM
        Cela garantit une sortie cohérente quel que soit le moteur amont,
        évitant les grésillements causés par un mauvais taux de rééchantillonnage
        côté client.
        """
        import struct
        import wave as wave_mod

        try:
            with wave_mod.open(wav_path, "rb") as wf:
                n_channels  = wf.getnchannels()
                samp_width  = wf.getsampwidth()   # bytes per sample
                frame_rate  = wf.getframerate()
                n_frames    = wf.getnframes()
                raw_frames  = wf.readframes(n_frames)

            # ── Convert to mono int16 numpy array ──────────────────────────
            import numpy as np

            if samp_width == 2:
                samples = np.frombuffer(raw_frames, dtype=np.int16)
            elif samp_width == 4:
                samples = np.frombuffer(raw_frames, dtype=np.int32)
                samples = (samples >> 16).astype(np.int16)
            elif samp_width == 3:
                # 24-bit — unpack manually
                n = len(raw_frames) // 3
                arr = np.zeros(n, dtype=np.int32)
                for i in range(n):
                    b0, b1, b2 = raw_frames[i*3], raw_frames[i*3+1], raw_frames[i*3+2]
                    val = (b2 << 16) | (b1 << 8) | b0
                    if val & 0x800000:
                        val -= 0x1000000
                    arr[i] = val
                samples = (arr >> 8).astype(np.int16)
            else:
                # Fallback: raw read
                with open(wav_path, "rb") as f:
                    return f.read()

            # ── Downmix to mono if stereo ───────────────────────────────────
            if n_channels > 1:
                samples = samples.reshape(-1, n_channels)
                samples = samples.mean(axis=1).astype(np.int16)

            # ── Resample to target sample_rate if needed ────────────────────
            target_sr = self.sample_rate  # 24000
            if frame_rate != target_sr:
                try:
                    import scipy.signal as sps
                    num_samples = int(len(samples) * target_sr / frame_rate)
                    samples = sps.resample(samples.astype(np.float32), num_samples)
                    samples = np.clip(samples, -32768, 32767).astype(np.int16)
                    logger.info(
                        f"   Resampled {frame_rate}Hz → {target_sr}Hz "
                        f"({n_frames} → {len(samples)} samples)"
                    )
                except ImportError:
                    logger.warning("   scipy absent — pas de rééchantillonnage")

            # ── Re-encode as WAV ────────────────────────────────────────────
            out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            out_path = out.name
            out.close()
            try:
                with wave_mod.open(out_path, "wb") as wout:
                    wout.setnchannels(1)
                    wout.setsampwidth(2)
                    wout.setframerate(target_sr)
                    wout.writeframes(samples.tobytes())
                with open(out_path, "rb") as f:
                    return f.read()
            finally:
                try:
                    os.unlink(out_path)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"   _normalize_wav échoué ({e}) — fallback lecture directe")
            try:
                with open(wav_path, "rb") as f:
                    return f.read()
            except Exception:
                return b""

    def list_speakers(self) -> list:
        """Retourner la liste de tous les speakers disponibles"""
        return self.available_speakers

    def set_default_speaker(self, speaker_name: str) -> bool:
        """
        Changer le speaker par défaut.

        Args:
            speaker_name: Nom exact du speaker
        Returns:
            bool: True si succès
        """
        if speaker_name in self.available_speakers:
            self.default_speaker = speaker_name
            logger.info(f"Speaker par défaut changé: {speaker_name}")
            return True
        else:
            logger.error(
                f" Speaker '{speaker_name}' introuvable. "
                f"Disponibles: {self.available_speakers[:5]}"
            )
            return False