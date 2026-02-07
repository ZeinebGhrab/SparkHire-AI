from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Modèle pour les justifications du match
class MatchRationale(BaseModel):
    criterion: str  # Ex: "skills_match", "experience_level", "education"
    score: float  # Score de 0 à 1
    explanation: str  # Explication textuelle
    matching_items: List[str] = []  # Items qui matchent (ex: ["Python", "FastAPI"])
    missing_items: List[str] = []  # Items manquants

# Modèle de base pour les matches
class MatchBase(BaseModel):
    candidate_id: str  # Référence au candidat
    job_id: str  # Référence à l'offre d'emploi
    score: float = Field(..., ge=0, le=1)  # Score global de 0 à 1
    rationales: List[MatchRationale] = []  # Détails des justifications
    status: str = "pending"  # "pending", "reviewed", "accepted", "rejected"
    recruiter_notes: Optional[str] = None

# Modèle pour la création
class MatchCreate(MatchBase):
    pass

# Modèle pour la réponse
class Match(MatchBase):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

# Modèle pour la mise à jour partielle
class MatchUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=1)
    rationales: Optional[List[MatchRationale]] = None
    status: Optional[str] = None
    recruiter_notes: Optional[str] = None