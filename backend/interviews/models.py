from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

# ============ Question Models ============

class Question(BaseModel):
    """Modèle pour une question d'entretien"""
    order: int
    question_ar: str
    question_en: str
    question_fr: str = ""
    max_duration_seconds: int = 120
    evaluation_criteria: List[str] = []

    def get_text(self, language: str) -> str:
        if language == "ar":
            return self.question_ar
        elif language == "fr":
            return self.question_fr if self.question_fr else self.question_en
        else:
            return self.question_en

# ============ Job Position Models ============

class JobPositionBase(BaseModel):
    title: str
    department: str
    location: Optional[str] = None       # Ex: "Tunis", "Sfax", "Remote"
    is_active: bool = True               # Offre active ou archivée
    questions: List[Question] = []

class JobPositionCreate(JobPositionBase):
    pass

class JobPositionUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    questions: Optional[List[Question]] = None

class JobPosition(JobPositionBase):
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

# ============ Answer Evaluation (embedded in Answer) ============

class AnswerEvaluationData(BaseModel):
    """
    Évaluation LLM d'une réponse — document embarqué dans Answer.
    Contient les scores initiaux ET finaux (après question de suivi si applicable).

    Structure MongoDB : interview_sessions.answers[n].evaluation
    """
    score: float = Field(0.0, ge=0, le=10)        # Score final LLM 0-10
    verdict: str = ""                               # Ex: "Très bien", "Acceptable"
    feedback: str = ""                              # Commentaire détaillé final
    strengths: List[str] = []                       # Points forts identifiés
    improvements: List[str] = []                    # Axes d'amélioration
    llm_model: str = ""                             # Modèle utilisé (ex: "llama3")
    evaluated_at: Optional[datetime] = None         # Timestamp d'évaluation
    # ── Suivi (rempli uniquement si une question de suivi a été posée) ─────────
    had_followup: bool = False                      # True si une question de suivi a été posée
    initial_score: Optional[float] = None           # Score avant clarification
    initial_verdict: Optional[str] = None           # Verdict avant clarification
    followup_question: Optional[str] = None         # Question de clarification posée par le LLM
    followup_transcript: Optional[str] = None       # Réponse vocale du candidat au suivi

# ============ Answer Models ============

class Answer(BaseModel):
    """
    Réponse vocale d'un candidat.

    Pipeline de remplissage :
      1. WebSocket reçoit l'audio PCM → Whisper → `transcript` sauvegardé en base
      2. LLM évalue le transcript → `evaluation` sauvegardé dans answers[n].evaluation
      3. Si score < 8 → question de suivi posée → réponse transcrite et réévaluation finale
         Les champs followup_* dans evaluation stockent tout le contexte du suivi.
    """
    question_order: int
    question_text: str
    transcript: str = ""                        # Transcription Whisper de la réponse principale
    audio_file_path: Optional[str] = None       # Chemin WAV réponse principale
    audio_followup_path: Optional[str] = None   # Chemin WAV réponse de suivi
    duration_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evaluation: Optional[AnswerEvaluationData] = None  # ← Score LLM (rempli en async)

# ============ Interview Session Models ============

class InterviewSessionBase(BaseModel):
    candidate_id: str
    job_position_id: str
    language: str = "ar"
    scheduled_at: Optional[datetime] = None   # Date/heure planifiée de l'entretien

class InterviewSessionCreate(InterviewSessionBase):
    pass

class InterviewSession(InterviewSessionBase):
    id: str = Field(..., alias="_id")
    session_id: str
    status: str = "pending"
    current_question_index: int = 0
    answers: List[Answer] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Scores agrégés — mis à jour par EvaluationService après l'entretien complet
    scheduled_at: Optional[datetime] = None         # Date/heure planifiée
    late_access_deadline: Optional[datetime] = None  # scheduled_at + 30 min (calculé)
    evaluation_score: Optional[float] = None
    evaluation_verdict: Optional[str] = None
    evaluation_recommendation: Optional[str] = None
    evaluation_decision: Optional[str] = None        # accepted | pending | rejected
    evaluation_decision_label: Optional[str] = None  # libellé localisé
    evaluation_decision_color: Optional[str] = None  # couleur hex
    evaluation_decision_reason: Optional[str] = None # justification

    model_config = {"populate_by_name": True}

# ============ API Response Models ============

class AnswerWithEvalResponse(BaseModel):
    """
    Réponse enrichie retournée par :
      GET /interviews/sessions/{session_id}/answers
    """
    question_order: int
    question_text: str
    transcript: str
    duration_seconds: float
    timestamp: datetime
    evaluated: bool = False
    score: Optional[float] = None
    verdict: Optional[str] = None
    feedback: Optional[str] = None
    strengths: List[str] = []
    improvements: List[str] = []
    llm_model: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    # ── Suivi LLM ──────────────────────────────────────────────────────────────
    had_followup: bool = False
    initial_score: Optional[float] = None
    initial_verdict: Optional[str] = None
    followup_question: Optional[str] = None      # Question de clarification du LLM
    followup_transcript: Optional[str] = None    # Réponse vocale du candidat au suivi

    @classmethod
    def from_answer(cls, answer: Answer) -> "AnswerWithEvalResponse":
        ev = answer.evaluation
        return cls(
            question_order=answer.question_order,
            question_text=answer.question_text,
            transcript=answer.transcript,
            duration_seconds=answer.duration_seconds,
            timestamp=answer.timestamp,
            evaluated=ev is not None,
            score=ev.score if ev else None,
            verdict=ev.verdict if ev else None,
            feedback=ev.feedback if ev else None,
            strengths=ev.strengths if ev else [],
            improvements=ev.improvements if ev else [],
            llm_model=ev.llm_model if ev else None,
            evaluated_at=ev.evaluated_at if ev else None,
            had_followup=ev.had_followup if ev else False,
            initial_score=ev.initial_score if ev else None,
            initial_verdict=ev.initial_verdict if ev else None,
            followup_question=ev.followup_question if ev else None,
            followup_transcript=ev.followup_transcript if ev else None,
        )

class AnswersSummaryResponse(BaseModel):
    """Résumé des évaluations pour GET /answers/summary"""
    session_id: str
    total_answers: int
    evaluated_count: int
    average_score: Optional[float] = None
    answers: List[AnswerWithEvalResponse] = []

# ============ WebSocket Messages ============

class WebSocketMessage(BaseModel):
    type: str
    data: dict = {}

class QuestionMessage(BaseModel):
    text: str
    order: int
    max_duration: int
    progress: dict
    audio_url: Optional[str] = None

class AnswerMessage(BaseModel):
    transcript: str
    duration: float
    question_order: int