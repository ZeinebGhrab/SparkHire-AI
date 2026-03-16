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
    weight: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Poids de la question dans la moyenne pondérée",
    )


# ── Seuils de décision ───────────────────────────────────────────────────────

DECISION_ACCEPTED  = "accepted"
DECISION_PENDING   = "pending"
DECISION_REJECTED  = "rejected"

DECISION_THRESHOLD_ACCEPT = 7.0
DECISION_THRESHOLD_REJECT = 5.0


def compute_decision(score: float) -> str:
    if score >= DECISION_THRESHOLD_ACCEPT:
        return DECISION_ACCEPTED
    if score >= DECISION_THRESHOLD_REJECT:
        return DECISION_PENDING
    return DECISION_REJECTED


DECISION_LABELS = {
    "fr": {
        DECISION_ACCEPTED: "Accepté",
        DECISION_PENDING:  "En attente",
        DECISION_REJECTED: "Refusé",
    },
    "en": {
        DECISION_ACCEPTED: "Accepted",
        DECISION_PENDING:  "On Hold",
        DECISION_REJECTED: "Rejected",
    },
    "ar": {
        DECISION_ACCEPTED: "مقبول",
        DECISION_PENDING:  "قيد الانتظار",
        DECISION_REJECTED: "مرفوض",
    },
}

DECISION_COLORS = {
    DECISION_ACCEPTED: "#10B981",
    DECISION_PENDING:  "#F59E0B",
    DECISION_REJECTED: "#EF4444",
}


class GlobalEvaluation(BaseModel):
    """Résumé global d'un entretien évalué par le LLM."""
    session_id: str
    candidate_name: str
    position_title: str
    language: str = "fr"
    total_questions: int
    answered_questions: int
    # ── Score ───────────────────────────────────────────────────────────────
    average_score: float = 0.0          # Σ(score × weight) / Σ(weight)
    # ── Décision ────────────────────────────────────────────────────────────
    decision: str = DECISION_PENDING    # "accepted" | "pending" | "rejected"
    decision_label: str = ""            # libellé localisé
    decision_color: str = ""            # couleur hex
    decision_reason: str = ""           # justification en une phrase
    # ── Contenu LLM ─────────────────────────────────────────────────────────
    recommendation: str = ""            # "Embaucher" / "En attente" / "Refuser"
    key_strengths: List[str] = []
    key_improvements: List[str] = []
    summary: str = ""
    per_answer: List[AnswerEvaluation] = []
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    llm_model: str = ""

    @property
    def score_100(self) -> float:
        """Score normalisé sur 100 pour affichage graphique."""
        return round(self.average_score * 10, 1)

    @property
    def verdict_color(self) -> str:
        return DECISION_COLORS.get(self.decision, "#F59E0B")


class EvaluationRequest(BaseModel):
    session_id: str
    language: Optional[str] = None


class EvaluationSummaryResponse(BaseModel):
    """Réponse allégée pour le listing."""
    session_id: str
    candidate_name: str
    position_title: str
    average_score: float
    recommendation: str
    evaluated_at: datetime