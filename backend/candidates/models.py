from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Modèles pour l'éducation
class Education(BaseModel):
    degree: str  # Ex: "Licence", "Master", "Ingénieur"
    field: str  # Ex: "Informatique", "Data Science"
    institution: str
    start_date: Optional[str] = None  # Format: "2018-09" ou "2018"
    end_date: Optional[str] = None
    currently_studying: bool = False

# Modèles pour l'expérience
class Experience(BaseModel):
    title: str  # Ex: "Développeur Full Stack"
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    currently_working: bool = False
    description: Optional[str] = None
    technologies: List[str] = []

# Modèles pour les contacts
class Contact(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

# Modèles pour les consentements
class Consent(BaseModel):
    type: str  # Ex: "data_processing", "voice_recording", "ai_analysis"
    granted: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None

# Modèle de base pour les candidats
class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    contact: Contact
    skills: List[str] = []
    experiences: List[Experience] = []
    education: List[Education] = []
    cv_raw: Optional[str] = None  # Texte brut du CV
    consents: List[Consent] = []
    embeddings: Optional[List[float]] = None  # Vecteur d'embeddings pour la recherche sémantique

# Modèle pour la création
class CandidateCreate(CandidateBase):
    pass

# Modèle pour la réponse
class Candidate(CandidateBase):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

# Modèle pour la mise à jour partielle
class CandidateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    contact: Optional[Contact] = None
    skills: Optional[List[str]] = None
    experiences: Optional[List[Experience]] = None
    education: Optional[List[Education]] = None
    cv_raw: Optional[str] = None
    consents: Optional[List[Consent]] = None
    embeddings: Optional[List[float]] = None