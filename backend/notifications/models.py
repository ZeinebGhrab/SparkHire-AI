from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Notification(BaseModel):
    """Modèle de notification"""
    id: str = Field(..., alias="_id")
    recipient_email: str
    type: str  # interview_started, interview_completed, match_found, etc.
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    priority: str = "normal"  # low, normal, high, urgent
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}

class NotificationCreate(BaseModel):
    """Créer une notification"""
    recipient_email: str
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    priority: str = "normal"

class NotificationUpdate(BaseModel):
    """Mettre à jour une notification"""
    read: Optional[bool] = None