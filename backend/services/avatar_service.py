"""
Service Avatar
Gère l'animation et la génération vidéo de l'avatar
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
        """Générer vidéo de l'avatar parlant"""
        pass


class SimpleAvatarProvider(AvatarProvider):
    """Provider simple sans génération vidéo"""
    
    def generate_video(
        self, 
        audio_path: Path, 
        output_path: Path,
        text: Optional[str] = None
    ) -> bool:
        """Mode simple: juste retourner l'audio"""
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
        """Générer vidéo avec Wav2Lip"""
        try:
            # TODO: Implémenter Wav2Lip
            logger.warning("Wav2Lip non implémenté, mode simple activé")
            return True
        except Exception as e:
            logger.error(f"Erreur génération Wav2Lip: {e}")
            return False


class DIDProvider(AvatarProvider):
    """Provider utilisant D-ID API"""
    
    def __init__(self, api_key: str, presenter_id: str):
        self.api_key = api_key
        self.presenter_id = presenter_id
    
    def generate_video(
        self, 
        audio_path: Path, 
        output_path: Path,
        text: Optional[str] = None
    ) -> bool:
        """Générer vidéo avec D-ID"""
        try:
            # TODO: Implémenter D-ID API
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
        """Générer vidéo de l'avatar"""
        return self.provider.generate_video(audio_path, output_path, text)


def get_avatar_service() -> AvatarService:
    """Factory pour créer le service avatar"""
    from backend.config import settings
    
    if settings.AVATAR_PROVIDER == "simple":
        provider = SimpleAvatarProvider()
    elif settings.AVATAR_PROVIDER == "wav2lip":
        # TODO: Récupérer les chemins depuis config
        provider = SimpleAvatarProvider()  # Fallback
    elif settings.AVATAR_PROVIDER == "did":
        # TODO: Récupérer API key depuis config
        provider = SimpleAvatarProvider()  # Fallback
    else:
        raise ValueError(f"Provider avatar inconnu: {settings.AVATAR_PROVIDER}")
    
    return AvatarService(provider)