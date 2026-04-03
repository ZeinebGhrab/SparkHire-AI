"""
HR Correction & Calibration Pipeline — SparkHire AI
=====================================================
Permet au RH de corriger les évaluations LLM (score, forces, améliorations).
Les corrections sont stockées dans `evaluation_corrections` et injectées
dans le system prompt lors des prochaines évaluations du même poste.

Collection MongoDB : evaluation_corrections
Index recommandés  : position_id + language (pour fetch calibration)
                     session_id (pour lister corrections d'une session)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel, Field

from backend.database import db

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
#  PYDANTIC MODELS
# ═════════════════════════════════════════════════════════════════════════════

class EvaluationCorrection(BaseModel):
    """
    Correction RH sur une réponse évaluée.
    Stockée dans la collection `evaluation_corrections`.
    """
    id: Optional[str] = Field(None, alias="_id")

    # Contexte
    session_id:         str
    question_order:     int
    position_id:        str
    question_text:      str
    transcript_excerpt: str   # max 250 chars — pour le few-shot prompt
    language:           str = "fr"

    # Évaluation LLM originale
    original_score:        float
    original_verdict:      str
    original_strengths:    List[str] = []
    original_improvements: List[str] = []

    # Correction RH
    corrected_score:          float
    corrected_verdict:        str = ""
    strengths_validated:      List[str] = []   # forces LLM que le RH confirme
    strengths_added:          List[str] = []   # nouvelles forces détectées par le RH
    improvements_validated:   List[str] = []   # axes d'amélioration confirmés
    improvements_removed:     List[str] = []   # faux axes supprimés
    hr_comment:               str = ""         # justification libre

    corrected_by: str
    corrected_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class CorrectionCreate(BaseModel):
    """Payload POST /evaluations/corrections."""
    session_id:    str
    question_order: int = Field(..., ge=1)

    corrected_score:          float = Field(..., ge=0, le=10)
    corrected_verdict:        str = ""
    strengths_validated:      List[str] = []
    strengths_added:          List[str] = []
    improvements_validated:   List[str] = []
    improvements_removed:     List[str] = []
    hr_comment:               str = ""


class CorrectionStats(BaseModel):
    """Résumé des corrections disponibles pour un poste."""
    position_id:       str
    position_title:    str = ""
    total_corrections: int
    avg_delta_score:   float   # écart moyen LLM → RH (positif = LLM sous-note)
    language:          str = "fr"


# ═════════════════════════════════════════════════════════════════════════════
#  CRUD
# ═════════════════════════════════════════════════════════════════════════════

class CorrectionCRUD:

    # ── Création ─────────────────────────────────────────────────────────────

    @staticmethod
    def create(payload: CorrectionCreate, recruiter_email: str) -> EvaluationCorrection:
        """
        Crée une correction RH en résolvant automatiquement le contexte
        (position_id, question_text, transcript, évaluation originale)
        depuis la session existante.
        """
        session = db.interview_sessions.find_one({"session_id": payload.session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session introuvable")

        answer = next(
            (a for a in session.get("answers", [])
             if a.get("question_order") == payload.question_order),
            None,
        )
        if not answer:
            raise HTTPException(
                status_code=404,
                detail=f"Réponse Q{payload.question_order} introuvable dans la session",
            )

        ev = answer.get("evaluation") or {}
        transcript = answer.get("transcript", "")

        doc = {
            "session_id":    payload.session_id,
            "question_order": payload.question_order,
            "position_id":   session.get("job_position_id", ""),
            "question_text": answer.get("question_text", ""),
            "transcript_excerpt": transcript[:250],
            "language":      session.get("language", "fr"),

            # Original
            "original_score":        float(ev.get("score", 0)),
            "original_verdict":      ev.get("verdict", ""),
            "original_strengths":    ev.get("strengths", []),
            "original_improvements": ev.get("improvements", []),

            # Correction RH
            "corrected_score":        payload.corrected_score,
            "corrected_verdict":      payload.corrected_verdict or ev.get("verdict", ""),
            "strengths_validated":    payload.strengths_validated,
            "strengths_added":        payload.strengths_added,
            "improvements_validated": payload.improvements_validated,
            "improvements_removed":   payload.improvements_removed,
            "hr_comment":             payload.hr_comment,

            "corrected_by": recruiter_email,
            "corrected_at": datetime.utcnow(),
        }

        result = db.evaluation_corrections.insert_one(doc)
        doc["_id"] = str(result.inserted_id)

        logger.info(
            f"Correction créée | session={payload.session_id} "
            f"Q{payload.question_order} | "
            f"{doc['original_score']:.1f} → {payload.corrected_score:.1f} | "
            f"by={recruiter_email}"
        )
        return EvaluationCorrection(**doc)

    # ── Lecture ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_for_session(session_id: str) -> List[dict]:
        docs = list(
            db.evaluation_corrections
            .find({"session_id": session_id})
            .sort("question_order", 1)
        )
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    @staticmethod
    def get_calibration_for_position(
        position_id: str,
        language: str = "fr",
        limit: int = 5,
    ) -> List[dict]:
        """
        Retourne les `limit` corrections les plus récentes pour un poste donné.
        Utilisé pour construire le contexte de calibration injecté dans le prompt.
        Priorité : corrections avec le plus grand écart absolu de score
        (les cas les plus instructifs pour le LLM).
        """
        pipeline = [
            {"$match": {"position_id": position_id, "language": language}},
            {"$addFields": {
                "score_delta_abs": {
                    "$abs": {"$subtract": ["$corrected_score", "$original_score"]}
                }
            }},
            {"$sort": {"score_delta_abs": -1, "corrected_at": -1}},
            {"$limit": limit},
        ]
        docs = list(db.evaluation_corrections.aggregate(pipeline))
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    @staticmethod
    def get_stats_for_position(position_id: str) -> Optional[CorrectionStats]:
        docs = list(
            db.evaluation_corrections.find({"position_id": position_id})
        )
        if not docs:
            return None

        deltas = [d["corrected_score"] - d["original_score"] for d in docs]
        avg_delta = round(sum(deltas) / len(deltas), 2)

        # Résoudre le titre du poste
        title = ""
        try:
            pos = db.job_positions.find_one(
                {"_id": ObjectId(position_id)}, {"title": 1}
            )
            if pos:
                title = pos.get("title", "")
        except Exception:
            pass

        language = docs[-1].get("language", "fr") if docs else "fr"
        return CorrectionStats(
            position_id=position_id,
            position_title=title,
            total_corrections=len(docs),
            avg_delta_score=avg_delta,
            language=language,
        )


# ═════════════════════════════════════════════════════════════════════════════
#  CALIBRATION PROMPT BUILDER
# ═════════════════════════════════════════════════════════════════════════════

_CALIB_HEADER = {
    "fr": (
        "\n\nCALIBRAGE RH — L'équipe RH a validé les évaluations suivantes pour ce poste. "
        "Adapte ton barème en conséquence :"
    ),
    "en": (
        "\n\nHR CALIBRATION — The HR team has validated the following evaluations for this position. "
        "Adjust your grading scale accordingly:"
    ),
    "ar": (
        "\n\nمعايرة الموارد البشرية — قام فريق الموارد البشرية بالتحقق من التقييمات التالية لهذا المنصب. "
        "اضبط معايير تقييمك وفقاً لذلك :"
    ),
}

_CALIB_EXAMPLE = {
    "fr": (
        "\nمثال {n} :\n"   # placeholders filled below
        "Exemple {n} :\n"
        "  Question           : {question}\n"
        "  Extrait réponse    : « {excerpt} »\n"
        "  Score LLM initial  : {orig}/10 ({orig_verdict})\n"
        "  Score RH validé    : {corr}/10 — {direction}\n"
        "  Forces retenues    : {strengths}\n"
        "  Améliorations      : {improvements}\n"
        "  Commentaire RH     : {comment}"
    ),
    "en": (
        "\nExample {n}:\n"
        "  Question           : {question}\n"
        "  Answer excerpt     : « {excerpt} »\n"
        "  Initial LLM score  : {orig}/10 ({orig_verdict})\n"
        "  HR validated score : {corr}/10 — {direction}\n"
        "  Strengths retained : {strengths}\n"
        "  Improvements       : {improvements}\n"
        "  HR comment         : {comment}"
    ),
    "ar": (
        "\nمثال {n} :\n"
        "  السؤال                : {question}\n"
        "  مقتطف الإجابة          : « {excerpt} »\n"
        "  درجة النموذج الأولية   : {orig}/10 ({orig_verdict})\n"
        "  الدرجة المعتمدة من RH  : {corr}/10 — {direction}\n"
        "  نقاط القوة             : {strengths}\n"
        "  محاور التحسين          : {improvements}\n"
        "  تعليق فريق التوظيف     : {comment}"
    ),
}

_DIRECTION_LABELS = {
    "fr": {
        "up":   "LLM avait sous-évalué",
        "down": "LLM avait sur-évalué",
        "same": "score confirmé",
    },
    "en": {
        "up":   "LLM had underscored",
        "down": "LLM had overscored",
        "same": "score confirmed",
    },
    "ar": {
        "up":   "النموذج أعطى درجة أقل من اللازم",
        "down": "النموذج أعطى درجة أعلى من اللازم",
        "same": "الدرجة مؤكدة",
    },
}

_CALIB_FOOTER = {
    "fr": (
        "\n→ Ces exemples définissent le niveau d'exigence RH pour ce poste. "
        "Si une réponse ressemble à ces extraits, applique le même niveau de score."
    ),
    "en": (
        "\n→ These examples define the HR expectation level for this position. "
        "If an answer resembles these excerpts, apply the same scoring level."
    ),
    "ar": (
        "\n→ هذه الأمثلة تحدد مستوى التوقعات لهذا المنصب. "
        "إذا كانت الإجابة مشابهة لهذه المقتطفات، طبّق نفس مستوى التقييم."
    ),
}


def build_calibration_context(corrections: List[dict], language: str) -> str:
    """
    Construit le bloc de calibration à injecter dans le system prompt LLM.

    Retourne une chaîne vide si :
      - corrections est vide
      - aucune correction n'a de delta significatif (>= 0.5 pt)

    Le bloc est conçu pour être concaténé directement à la fin du system prompt
    existant (`_SYSTEM_PROMPT_FOLLOWUP`) dans llm_service.py.
    """
    if not corrections:
        return ""

    # Ne conserver que les corrections avec un delta instructif (>= 0.5 pt)
    meaningful = [
        c for c in corrections
        if abs(c.get("corrected_score", 0) - c.get("original_score", 0)) >= 0.5
        or c.get("hr_comment", "").strip()
        or c.get("strengths_added", [])
    ]
    if not meaningful:
        return ""

    lang = language if language in _CALIB_HEADER else "fr"
    dir_labels = _DIRECTION_LABELS[lang]
    example_tpl = _CALIB_EXAMPLE[lang]

    lines = [_CALIB_HEADER[lang]]

    for i, c in enumerate(meaningful, 1):
        orig  = c.get("original_score", 0)
        corr  = c.get("corrected_score", 0)
        delta = corr - orig

        direction = (
            dir_labels["up"]   if delta >= 0.5  else
            dir_labels["down"] if delta <= -0.5 else
            dir_labels["same"]
        )

        strengths = (
            c.get("strengths_validated", []) + c.get("strengths_added", [])
        )[:3]
        improvements = c.get("improvements_validated", [])[:3]

        # Tronquer les textes longs pour ne pas gonfler le prompt inutilement
        question = (c.get("question_text", "") or "")[:120]
        excerpt  = (c.get("transcript_excerpt", "") or "")[:150]
        comment  = (c.get("hr_comment", "") or "")[:120]

        # Le template contient une ligne en arabe en tête pour "fr" — nettoyer
        tpl = example_tpl
        if lang == "fr":
            tpl = "\n".join(
                line for line in example_tpl.splitlines()
                if not line.startswith("مثال")
            )

        lines.append(tpl.format(
            n=i,
            question=question or "—",
            excerpt=excerpt or "—",
            orig=round(orig, 1),
            orig_verdict=c.get("original_verdict", ""),
            corr=round(corr, 1),
            direction=direction,
            strengths=", ".join(strengths) if strengths else "—",
            improvements=", ".join(improvements) if improvements else "—",
            comment=comment or "—",
        ))

    lines.append(_CALIB_FOOTER[lang])
    return "\n".join(lines)