"""
Service Avatar
Gère l'animation et la génération vidéo de l'avatar.
Tous les providers non-implémentés tombent en mode simple (pas d'erreur au démarrage).
"""

import logging
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AvatarProvider(ABC):
    """Interface abstraite pour les fournisseurs d'avatar"""

    @abstractmethod
    def generate_video(
        self,
        audio_path: Path,
        output_path: Path,
        text: Optional[str] = None
    ) -> bool:
        pass


class SimpleAvatarProvider(AvatarProvider):
    """Provider simple sans génération vidéo"""

    def generate_video(
        self,
        audio_path: Path,
        output_path: Path,
        text: Optional[str] = None
    ) -> bool:
        logger.info("Mode simple: pas de génération vidéo")
        return True


class Wav2LipProvider(AvatarProvider):
    """Provider utilisant Wav2Lip pour lip-sync"""

    def __init__(self, model_path: Path, face_image: Path):
        self.model_path = model_path
        self.face_image = face_image

        if not model_path.exists():
            raise FileNotFoundError(f"Modèle Wav2Lip introuvable: {model_path}")
        if not face_image.exists():
            raise FileNotFoundError(f"Image de visage introuvable: {face_image}")

    def generate_video(
        self,
        audio_path: Path,
        output_path: Path,
        text: Optional[str] = None
    ) -> bool:
        try:
            logger.warning("Wav2Lip non implémenté, mode simple activé")
            return True
        except Exception as e:
            logger.error(f"Erreur génération Wav2Lip: {e}")
            return False


class DIDProvider(AvatarProvider):
    """Provider utilisant D-ID API"""

    def __init__(self, api_key: str, presenter_id: str):
        self.api_key      = api_key
        self.presenter_id = presenter_id

    def generate_video(
        self,
        audio_path: Path,
        output_path: Path,
        text: Optional[str] = None
    ) -> bool:
        try:
            logger.warning("D-ID non implémenté, mode simple activé")
            return True
        except Exception as e:
            logger.error(f"Erreur génération D-ID: {e}")
            return False


class AvatarService:
    """Service avatar unifié"""

    def __init__(self, provider: AvatarProvider):
        self.provider = provider

    def generate_video(
        self,
        audio_path: Path,
        output_path: Path,
        text: Optional[str] = None
    ) -> bool:
        return self.provider.generate_video(audio_path, output_path, text)


# ── Providers non-implémentés qui tombent silencieusement en mode simple ─────
_SIMPLE_FALLBACK_PROVIDERS = {
    "simple",
    "liveportrait",   # non implémenté → simple
    "wav2lip",        # non implémenté → simple
    "did",            # non implémenté → simple
}


def get_avatar_service() -> AvatarService:
    """
    Factory pour créer le service avatar.
    Tous les providers non implémentés tombent en SimpleAvatarProvider
    sans lever d'exception au démarrage.
    """
    from backend.config import settings

    provider_name = settings.AVATAR_PROVIDER.lower().strip()

    if provider_name in _SIMPLE_FALLBACK_PROVIDERS:
        if provider_name != "simple":
            logger.info(
                f"ℹAvatar provider '{provider_name}' non implémenté "
                f"→ mode simple activé (vidéos statiques)"
            )
        provider = SimpleAvatarProvider()
    else:
        logger.warning(
            f"Provider avatar inconnu : '{provider_name}' → mode simple activé"
        )
        provider = SimpleAvatarProvider()

    return AvatarService(provider)