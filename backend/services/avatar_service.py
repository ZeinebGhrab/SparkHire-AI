"""
Service Avatar
Providers disponibles : simple | did
"""

import logging
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AvatarProvider(ABC):
    @abstractmethod
    def generate_video(self, audio_path: Path, output_path: Path, text: Optional[str] = None) -> bool:
        pass


class SimpleAvatarProvider(AvatarProvider):
    """Provider simple — pas de génération vidéo, utilise les vidéos statiques."""

    def generate_video(self, audio_path: Path, output_path: Path, text: Optional[str] = None) -> bool:
        logger.info("Avatar : mode simple (vidéos statiques)")
        return True


class DIDProvider(AvatarProvider):
    """Provider D-ID API — non implémenté, tombe en mode simple."""

    def __init__(self, api_key: str, presenter_id: str):
        self.api_key      = api_key
        self.presenter_id = presenter_id

    def generate_video(self, audio_path: Path, output_path: Path, text: Optional[str] = None) -> bool:
        logger.warning("D-ID non implémenté → mode simple activé")
        return True


class AvatarService:
    def __init__(self, provider: AvatarProvider):
        self.provider = provider

    def generate_video(self, audio_path: Path, output_path: Path, text: Optional[str] = None) -> bool:
        return self.provider.generate_video(audio_path, output_path, text)


_SUPPORTED_PROVIDERS = {"simple", "did"}


def get_avatar_service() -> AvatarService:
    from backend.config import settings

    provider_name = settings.AVATAR_PROVIDER.lower().strip()

    if provider_name not in _SUPPORTED_PROVIDERS:
        logger.warning(
            f"Provider avatar inconnu : '{provider_name}' "
            f"(valides : {', '.join(sorted(_SUPPORTED_PROVIDERS))}) → mode simple activé"
        )
        provider_name = "simple"

    if provider_name == "did":
        logger.info("Avatar provider : D-ID (non implémenté → simple)")
        provider = DIDProvider(api_key="", presenter_id="")
    else:
        provider = SimpleAvatarProvider()

    logger.info(f"Avatar prêt | provider={provider_name}")
    return AvatarService(provider)