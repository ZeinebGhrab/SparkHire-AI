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


# ── Seuils de décision ───────────────────────────────────────────────────────
# Accepté   : score >= 7.0
# En attente : 5.0 <= score < 7.0
# Refusé    : score < 5.0

DECISION_ACCEPTED  = "accepted"
DECISION_PENDING   = "pending"
DECISION_REJECTED  = "rejected"

DECISION_THRESHOLD_ACCEPT = 7.0
DECISION_THRESHOLD_REJECT = 5.0


def compute_decision(score: float) -> str:
    """Calcule la décision automatique selon le score global /10."""
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
    DECISION_ACCEPTED: "#10B981",   # vert
    DECISION_PENDING:  "#F59E0B",   # ambre
    DECISION_REJECTED: "#EF4444",   # rouge
}


class GlobalEvaluation(BaseModel):
    """Résumé global d'un entretien évalué par le LLM."""
    session_id: str
    candidate_name: str
    position_title: str
    language: str = "fr"
    total_questions: int
    answered_questions: int
    average_score: float = 0.0
    global_score: float = 0.0         # Score LLM final /10
    global_verdict: str = ""          # Libellé court (ex: "Très bien")
    recommendation: str = ""          # Texte libre LLM (Embaucher / Refuser / ...)
    # ── Décision structurée ────────────────────────────────────────────────
    decision: str = DECISION_PENDING  # "accepted" | "pending" | "rejected"
    decision_label: str = ""          # Libellé localisé (Accepté / En attente / Refusé)
    decision_color: str = ""          # Couleur hex pour le frontend
    decision_reason: str = ""         # Justification courte générée par le LLM
    # ── Détail ─────────────────────────────────────────────────────────────
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
        return DECISION_COLORS.get(self.decision, "#F59E0B")


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