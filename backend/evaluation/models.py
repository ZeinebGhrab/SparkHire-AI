"""
Modèles Pydantic pour l'évaluation LLM des réponses d'entretien.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AnswerEvaluation(BaseModel):
    """Évaluation LLM d'une réponse unique."""
    question_order: int
    question_text: str
    transcript: str
    score: float = Field(0.0, ge=0, le=10)
    verdict: str = ""
    strengths: List[str] = []
    improvements: List[str] = []
    feedback: str = ""
    llm_model: str = ""
    evaluated: bool = False
    evaluated_at: Optional[datetime] = None


class GlobalEvaluation(BaseModel):
    """Résumé global d'un entretien évalué par le LLM."""
    session_id: str
    candidate_name: str
    position_title: str
    language: str = "fr"
    total_questions: int
    answered_questions: int
    average_score: float = 0.0
    global_score: float = 0.0
    global_verdict: str = ""
    recommendation: str = ""          # Embaucher / À considérer / Refuser
    key_strengths: List[str] = []
    key_improvements: List[str] = []
    summary: str = ""
    per_answer: List[AnswerEvaluation] = []
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    llm_model: str = ""

    # Score normalisé 0–100
    @property
    def score_100(self) -> float:
        return round(self.global_score * 10, 1)

    # Couleur verdict (pour le front)
    @property
    def verdict_color(self) -> str:
        if self.global_score >= 8:
            return "#10B981"   # vert
        if self.global_score >= 6:
            return "#F59E0B"   # ambre
        return "#EF4444"       # rouge


class EvaluationRequest(BaseModel):
    """Déclencheur manuel d'évaluation depuis l'API."""
    session_id: str
    language: Optional[str] = None     # surcharge la langue de la session


class EvaluationSummaryResponse(BaseModel):
    """Réponse allégée pour le listing."""
    session_id: str
    candidate_name: str
    position_title: str
    average_score: float
    global_score: float
    global_verdict: str
    recommendation: str
    evaluated_at: datetime