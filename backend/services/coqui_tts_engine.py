"""
Moteur TTS Coqui-TTS (Open Source / XTTS-v2)

CORRECTIFS APPLIQUÉS (par ordre d'exécution) :

1. PATCH torch.load — PyTorch 2.6
   PyTorch 2.6 passe `weights_only` de False → True par défaut.
   On monkey-patche avant tout import de TTS.

2. PATCH torchvision stub avec __spec__ valide
   torchvision plante à l'import (operator nms does not exist).
   On supprime le module cassé et on injecte un stub propre avec
   __spec__ != None pour que importlib.util.find_spec() fonctionne.

3. PATCH transformers.GPT2PreTrainedModel manquant
   Les versions récentes de transformers (≥ 4.45) ont retiré
   GPT2PreTrainedModel du __init__ public.
   TTS/XTTS en a besoin → on le réinjecte dans le namespace transformers.
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
    logger.info("✅ Patch torch.load appliqué (weights_only=False pour PyTorch 2.6)")

except ImportError:
    logger.warning("⚠️ PyTorch non disponible, patch torch.load non appliqué")


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
    logger.info("✅ torchvision importé normalement")

except Exception as _tv_err:
    logger.warning(
        f"⚠️ torchvision non disponible ({_tv_err}) — création d'un stub"
    )

    # Purger le module cassé (__spec__ = None) du cache
    for _k in list(sys.modules.keys()):
        if _k == "torchvision" or _k.startswith("torchvision."):
            del sys.modules[_k]

    # Injecter les stubs
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

    # InterpolationMode utilisé par transformers.
    # On utilise un objet dynamique plutôt qu'un Enum figé pour être
    # compatible avec toutes les versions de torchvision (0.15 → 0.20+).
    class _DynamicInterpolationMode:
        """Stub dynamique : retourne un objet nommé pour n'importe quel attribut."""
        BILINEAR = "bilinear"
        NEAREST = "nearest"
        BICUBIC = "bicubic"
        NEAREST_EXACT = "nearest_exact"
        BOX = "box"
        HAMMING = "hamming"
        LANCZOS = "lanczos"

        def __getattr__(self, name: str):
            # Pour tout autre attribut inconnu, retourner la chaîne elle-même
            return name

    sys.modules["torchvision.transforms"].InterpolationMode = _DynamicInterpolationMode()
    logger.info("✅ Stub torchvision injecté (avec __spec__ valide)")


# ==================================================================
# PATCH 3 : GPT2PreTrainedModel manquant dans transformers récents
# transformers ≥ 4.45 ne l'exporte plus depuis le __init__ global.
# TTS.tts.layers.xtts.gpt_inference l'importe directement depuis
# `transformers`, donc on le remet en place avant l'import TTS.
# ==================================================================
try:
    import transformers  # noqa: F401

    if not hasattr(transformers, "GPT2PreTrainedModel"):
        from transformers.models.gpt2.modeling_gpt2 import GPT2PreTrainedModel as _GPT2PT
        transformers.GPT2PreTrainedModel = _GPT2PT
        logger.info(
            "✅ Patch transformers.GPT2PreTrainedModel appliqué "
            "(absent du __init__ public dans cette version)"
        )
    else:
        logger.info("✅ transformers.GPT2PreTrainedModel déjà disponible")

except Exception as _tf_err:
    logger.warning(f"⚠️ Impossible de patcher transformers: {_tf_err}")


# ==================================================================
# MOTEUR COQUI TTS
# ==================================================================


class CoquiTTSEngine:
    """Moteur TTS utilisant Coqui-TTS (Open Source / XTTS-v2)"""

    def __init__(self):
        try:
            from TTS.api import TTS

            model_path = "models/xtts_v2"

            if os.path.exists(model_path) and os.path.exists(
                os.path.join(model_path, "model.pth")
            ):
                logger.info(f"⏳ Chargement du modèle Coqui-TTS depuis: {model_path}")
                logger.info("   ✅ Modèle local détecté (pas de téléchargement)")
                self.tts = TTS(
                    model_path=model_path,
                    config_path=os.path.join(model_path, "config.json"),
                )
            else:
                logger.info("⏳ Chargement XTTS-v2 depuis HuggingFace...")
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

            logger.info("✅ Coqui-TTS XTTS-v2 chargé avec succès")

            self.languages = {"ar": "ar", "en": "en", "fr": "fr"}
            self.voices = {
                "ar": "coqui-xtts-ar",
                "en": "coqui-xtts-en",
                "fr": "coqui-xtts-fr",
            }
            self.generation_params = {"temperature": 0.7, "speed": 1.0}
            logger.info(f"   Langues supportées: {list(self.languages.keys())}")

        except ImportError as e:
            logger.error("❌ Coqui-TTS non installé — Solution: pip install TTS")
            raise ImportError("Installez Coqui-TTS: pip install TTS") from e

        except Exception as e:
            logger.error(f"❌ Erreur initialisation Coqui-TTS: {e}")
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
                logger.error("❌ Texte vide fourni à Coqui-TTS")
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
                }

                if speaker_wav and os.path.exists(speaker_wav):
                    kwargs["speaker_wav"] = speaker_wav
                    logger.info("   Mode: clonage de voix")
                else:
                    logger.info("   Mode: voix par défaut")

                self.tts.tts_to_file(**kwargs)

                with open(tmp_path, "rb") as f:
                    audio_data = f.read()

                if audio_data:
                    logger.info(f"✅ Audio généré: {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.error("❌ Audio vide généré")
                    return b""

            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"❌ Erreur synthèse Coqui-TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return b""