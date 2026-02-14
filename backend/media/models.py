from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class MediaFile(BaseModel):
    """Modèle pour un fichier média"""
    id: str = Field(..., alias="_id")
    filename: str
    file_path: str
    file_type: str  # audio, video, image
    mime_type: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    related_entity_type: Optional[str] = None  # interview, candidate, position
    related_entity_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}

class MediaUploadResponse(BaseModel):
    """Réponse après upload d'un fichier"""
    file_id: str
    filename: str
    file_path: str
    file_url: str
    size_bytes: int
    mime_type: str
    message: str = "Fichier uploadé avec succès"