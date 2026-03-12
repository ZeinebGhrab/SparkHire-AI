from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


# ── Education ─────────────────────────────────────────────────────────────────

class Education(BaseModel):
    degree: str                          # Ex: "Licence", "Master", "Ingénieur"
    field: str                           # Ex: "Informatique", "Data Science"
    institution: str
    start_date: Optional[str] = None     # Format: "2018-09" ou "2018"
    end_date: Optional[str] = None
    currently_studying: bool = False


# ── Experience ────────────────────────────────────────────────────────────────

class Experience(BaseModel):
    title: str                           # Ex: "Développeur Full Stack"
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    currently_working: bool = False
    description: Optional[str] = None
    technologies: List[str] = []


# ── Technical Skill ───────────────────────────────────────────────────────────

class TechnicalSkill(BaseModel):
    name: str                            # Ex: "Python", "FastAPI", "MongoDB"
    level: Optional[str] = None          # "Beginner"|"Intermediate"|"Advanced"|"Expert"
    years_experience: Optional[float] = None


# ── Language ──────────────────────────────────────────────────────────────────

class Language(BaseModel):
    name: str                            # Ex: "Arabic", "French", "English"
    level: str                           # "A1"|"A2"|"B1"|"B2"|"C1"|"C2"|"Native"


# ── Soft Skill ────────────────────────────────────────────────────────────────

class SoftSkill(BaseModel):
    name: str                            # Ex: "Teamwork", "Leadership", "Communication"


# ── Certification ─────────────────────────────────────────────────────────────

class Certification(BaseModel):
    name: str                            # Ex: "AWS Certified Developer", "PMP"
    issuer: str                          # Ex: "Amazon Web Services", "PMI"
    issue_date: Optional[str] = None     # Format: "2023-06"
    expiry_date: Optional[str] = None    # None = pas d'expiration
    credential_id: Optional[str] = None  # ID ou numéro de certification
    credential_url: Optional[str] = None # Lien de vérification


# ── Contact ───────────────────────────────────────────────────────────────────

class Contact(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


# ── Consent ───────────────────────────────────────────────────────────────────

class Consent(BaseModel):
    type: str                            # Ex: "data_processing", "voice_recording", "ai_analysis"
    granted: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None


# ── Candidate Base ────────────────────────────────────────────────────────────

class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    contact: Contact

    # ✅ Compétences techniques — obligatoire, min 1
    technical_skills: List[TechnicalSkill] = Field(
        ...,
        min_length=1,
        description="Technical skills — at least one required"
    )

    # ✅ Expérience professionnelle — obligatoire, min 1
    experiences: List[Experience] = Field(
        ...,
        min_length=1,
        description="Work experience — at least one required"
    )

    # ✅ Formation — obligatoire, min 1
    education: List[Education] = Field(
        ...,
        min_length=1,
        description="Education background — at least one required"
    )

    # ✅ Langues — obligatoire, min 1
    languages: List[Language] = Field(
        ...,
        min_length=1,
        description="Spoken languages — at least one required"
    )

    # ✅ Soft skills — obligatoire, min 1
    soft_skills: List[SoftSkill] = Field(
        ...,
        min_length=1,
        description="Soft skills — at least one required"
    )

    # ✅ Certifications — obligatoire, min 1
    certifications: List[Certification] = Field(
        ...,
        min_length=1,
        description="Certifications — at least one required"
    )

    # Optionnel
    cv_raw: Optional[str] = None
    consents: List[Consent] = []
    embeddings: Optional[List[float]] = None


# ── Create ────────────────────────────────────────────────────────────────────

class CandidateCreate(CandidateBase):
    pass


# ── Response ──────────────────────────────────────────────────────────────────

class Candidate(CandidateBase):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


# ── Partial Update ────────────────────────────────────────────────────────────

class CandidateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    contact: Optional[Contact] = None
    technical_skills: Optional[List[TechnicalSkill]] = None
    experiences: Optional[List[Experience]] = None
    education: Optional[List[Education]] = None
    languages: Optional[List[Language]] = None
    soft_skills: Optional[List[SoftSkill]] = None
    certifications: Optional[List[Certification]] = None
    cv_raw: Optional[str] = None
    consents: Optional[List[Consent]] = None
    embeddings: Optional[List[float]] = None