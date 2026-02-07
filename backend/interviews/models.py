from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# ============ Question Models ============

class Question(BaseModel):
    """Modèle pour une question d'entretien"""
    order: int  # Ordre de la question (1, 2, 3...)
    question_ar: str  # Question en arabe
    question_en: str  # Question en anglais
    max_duration_seconds: int = 120  # Durée max de réponse (secondes)
    evaluation_criteria: List[str] = []  # Critères d'évaluation optionnels

# ============ Job Position Models ============

class JobPositionBase(BaseModel):
    """Modèle de base pour un poste"""
    title: str
    department: str
    questions: List[Question] = []

class JobPositionCreate(JobPositionBase):
    """Modèle pour créer un poste"""
    pass

class JobPosition(JobPositionBase):
    """Modèle complet d'un poste"""
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}

# ============ Answer Models ============

class Answer(BaseModel):
    """Modèle pour une réponse de candidat"""
    question_order: int  # Numéro de la question
    question_text: str  # Texte de la question posée
    transcript: str = ""  # Transcription de la réponse
    audio_file_path: Optional[str] = None  # Chemin du fichier audio
    duration_seconds: float = 0.0  # Durée de la réponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============ Interview Session Models ============

class InterviewSessionBase(BaseModel):
    """Modèle de base pour une session d'entretien"""
    candidate_id: str  # ID du candidat
    job_position_id: str  # ID du poste
    language: str = "ar"  # Langue de l'entretien (ar ou en)

class InterviewSessionCreate(InterviewSessionBase):
    """Modèle pour créer une session"""
    pass

class InterviewSession(InterviewSessionBase):
    """Modèle complet d'une session d'entretien"""
    id: str = Field(..., alias="_id")
    session_id: str  # ID unique de session pour le WebSocket
    status: str = "pending"  # pending, in_progress, completed, cancelled
    current_question_index: int = 0  # Index de la question actuelle
    answers: List[Answer] = []  # Liste des réponses
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}

# ============ WebSocket Messages ============

class WebSocketMessage(BaseModel):
    """Message WebSocket générique"""
    type: str  # welcome, question, answer_saved, error, etc.
    data: dict = {}

class QuestionMessage(BaseModel):
    """Message pour envoyer une question"""
    text: str
    order: int
    max_duration: int
    progress: dict  # {current: 1, total: 20, percentage: 5}
    audio_url: Optional[str] = None

class AnswerMessage(BaseModel):
    """Message pour une réponse sauvegardée"""
    transcript: str
    duration: float
    question_order: int