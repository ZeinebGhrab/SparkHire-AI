"""
Service d'évaluation : orchestre le pipeline
Audio → Whisper (ASR) → Ollama/Llama3 (LLM) → Score + Feedback
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.evaluation.models import (
    AnswerEvaluation, GlobalEvaluation,
    compute_decision, DECISION_LABELS, DECISION_COLORS
)
from backend.services.llm_service import OllamaLLMService
from backend.database import db
from bson import ObjectId

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Orchestre le pipeline d'évaluation complet :
    1. (optionnel) Re-transcription Whisper si transcript vide
    2. Évaluation LLM par réponse
    3. Synthèse globale LLM
    4. Persistance en base
    """

    def __init__(self, llm_service: OllamaLLMService, asr_service=None):
        self.llm = llm_service
        self.asr = asr_service

    # ── Évaluation réponse par réponse (appelée en temps réel) ────────────

    async def evaluate_single_answer(
        self,
        question_text: str,
        answer_transcript: str,
        question_order: int,
        language: str = "fr",
        position_title: str = "",
        audio_path: Optional[str] = None,
    ) -> AnswerEvaluation:
        """
        Évalue une seule réponse juste après qu'elle a été enregistrée.
        Si le transcript est vide ET qu'un fichier audio existe, tente
        une re-transcription Whisper.
        """
        transcript = answer_transcript.strip()

        # Retry Whisper si transcript vide et audio disponible
        if not transcript and audio_path and self.asr:
            transcript = await self._retranscribe(audio_path, language)
            logger.info(f"Re-transcription Whisper Q{question_order}: '{transcript}'")

        # Évaluation LLM
        eval_result = await self.llm.evaluate_answer(
            question=question_text,
            answer=transcript,
            language=language,
            position_title=position_title,
        )

        return AnswerEvaluation(
            question_order=question_order,
            question_text=question_text,
            transcript=transcript,
            evaluated_at=datetime.utcnow(),
            **{k: eval_result[k] for k in
               ("score", "verdict", "strengths", "improvements",
                "feedback", "llm_model", "evaluated")},
        )

    # ── Évaluation complète d'un entretien terminé ────────────────────────

    async def evaluate_full_session(
        self,
        session_id: str,
        language: Optional[str] = None,
    ) -> Optional[GlobalEvaluation]:
        """
        Évalue toutes les réponses d'une session terminée, puis
        génère un résumé global. Persiste le résultat en base.
        """
        # Charger la session
        session = db.interview_sessions.find_one({"session_id": session_id})
        if not session:
            logger.error(f"Session introuvable : {session_id}")
            return None

        # Charger le poste
        position = db.job_positions.find_one(
            {"_id": ObjectId(session["job_position_id"])}
        )
        if not position:
            logger.error(f"Poste introuvable pour session {session_id}")
            return None

        # Charger le candidat
        candidate = db.candidates.find_one(
            {"_id": ObjectId(session["candidate_id"])}
        )
        candidate_name = (
            f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()
            if candidate else "Candidat"
        )

        lang = language or session.get("language", "fr")
        answers = session.get("answers", [])
        questions = {q["order"]: q for q in position.get("questions", [])}

        logger.info(
            f"Évaluation session {session_id} | "
            f"{len(answers)} réponses | langue={lang}"
        )

        # ── Évaluation par réponse en parallèle ──────────────────────────
        tasks = []
        for ans in answers:
            q_order = ans.get("question_order", 0)
            q_data  = questions.get(q_order, {})
            q_text  = ans.get("question_text") or self._get_question_text(q_data, lang)

            tasks.append(
                self.evaluate_single_answer(
                    question_text=q_text,
                    answer_transcript=ans.get("transcript", ""),
                    question_order=q_order,
                    language=lang,
                    position_title=position.get("title", ""),
                    audio_path=ans.get("audio_file_path"),
                )
            )

        per_answer: list[AnswerEvaluation] = await asyncio.gather(*tasks)

        # ── Résumé global ─────────────────────────────────────────────────
        avg_score = (
            sum(a.score for a in per_answer) / len(per_answer)
            if per_answer else 0.0
        )

        global_raw = await self.llm.generate_global_summary(
            answers_eval=[a.model_dump() for a in per_answer],
            position_title=position.get("title", ""),
            candidate_name=candidate_name,
            language=lang,
        )

        final_score = global_raw.get("global_score", avg_score)
        decision    = compute_decision(final_score)

        evaluation = GlobalEvaluation(
            session_id=session_id,
            candidate_name=candidate_name,
            position_title=position.get("title", ""),
            language=lang,
            total_questions=len(position.get("questions", [])),
            answered_questions=len(answers),
            average_score=round(avg_score, 2),
            global_score=final_score,
            global_verdict=global_raw.get("global_verdict", ""),
            recommendation=global_raw.get("recommendation", ""),
            decision=decision,
            decision_label=DECISION_LABELS.get(lang, DECISION_LABELS["fr"]).get(decision, decision),
            decision_color=DECISION_COLORS.get(decision, "#F59E0B"),
            decision_reason=global_raw.get("decision_reason", ""),
            key_strengths=global_raw.get("key_strengths", []),
            key_improvements=global_raw.get("key_improvements", []),
            summary=global_raw.get("summary", ""),
            per_answer=per_answer,
            llm_model=self.llm.model,
        )

        # ── Persistance ───────────────────────────────────────────────────
        self._save_evaluation(session_id, evaluation)
        logger.info(
            f"✅ Évaluation terminée {session_id} | "
            f"score={evaluation.global_score}/10 | "
            f"verdict={evaluation.global_verdict}"
        )
        return evaluation

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _retranscribe(self, audio_path: str, language: str) -> str:
        """Re-transcription Whisper asynchrone."""
        try:
            path = Path(audio_path)
            if not path.exists():
                return ""
            audio_bytes = path.read_bytes()
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None,
                lambda: self.asr.transcribe(audio_bytes, language=language),
            )
            return transcript or ""
        except Exception as e:
            logger.error(f"Re-transcription échouée : {e}")
            return ""

    @staticmethod
    def _get_question_text(q_data: dict, lang: str) -> str:
        if lang == "ar":
            return q_data.get("question_ar", "")
        if lang == "fr":
            return q_data.get("question_fr") or q_data.get("question_en", "")
        return q_data.get("question_en", "")

    def _save_evaluation(self, session_id: str, evaluation: GlobalEvaluation):
        """Sauvegarde ou met à jour l'évaluation en base."""
        doc = evaluation.model_dump()
        try:
            db.evaluations.update_one(
                {"session_id": session_id},
                {"$set": doc},
                upsert=True,
            )
            # Met aussi à jour le score dans la session
            db.interview_sessions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "evaluation_score":          evaluation.global_score,
                    "evaluation_verdict":        evaluation.global_verdict,
                    "evaluation_recommendation": evaluation.recommendation,
                    "evaluation_decision":       evaluation.decision,
                    "evaluation_decision_label": evaluation.decision_label,
                    "evaluation_decision_color": evaluation.decision_color,
                    "evaluation_decision_reason": evaluation.decision_reason,
                }},
            )
        except Exception as e:
            logger.error(f"Erreur sauvegarde évaluation : {e}")