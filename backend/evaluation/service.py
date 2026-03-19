"""
Service d'évaluation — orchestre le pipeline
Audio → Whisper (ASR) → Ollama/Llama3 (LLM) → Score + Feedback

Moyenne pondérée :
  average_score = Σ(score_i × weight_i) / Σ(weight_i)
  
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.evaluation.models import (
    AnswerEvaluation, GlobalEvaluation,
    FacialSummary, GlobalFacialSummary,
    compute_decision, DECISION_LABELS, DECISION_COLORS
)
from backend.services.llm_service import OllamaLLMService
from backend.database import db
from bson import ObjectId

logger = logging.getLogger(__name__)


def _weighted_avg(scores_weights: list[tuple[float, float]]) -> float:
    """Calcule la moyenne pondérée. Retourne 0.0 si la liste est vide."""
    if not scores_weights:
        return 0.0
    total_w = sum(w for _, w in scores_weights)
    if total_w == 0:
        return 0.0
    return round(sum(s * w for s, w in scores_weights) / total_w, 2)


class EvaluationService:

    def __init__(self, llm_service: OllamaLLMService, asr_service=None):
        self.llm = llm_service
        self.asr = asr_service

    # ── Évaluation réponse par réponse ────────────────────────────────────

    async def evaluate_single_answer(
        self,
        question_text: str,
        answer_transcript: str,
        question_order: int,
        language: str = "fr",
        position_title: str = "",
        audio_path: Optional[str] = None,
        weight: float = 1.0,
    ) -> AnswerEvaluation:
        transcript = answer_transcript.strip()
        if not transcript and audio_path and self.asr:
            transcript = await self._retranscribe(audio_path, language)
            logger.info(f"Re-transcription Whisper Q{question_order}: '{transcript}'")

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
            weight=weight,
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
        # ── Charger les données ────────────────────────────────────────────
        session = db.interview_sessions.find_one({"session_id": session_id})
        if not session:
            logger.error(f"Session introuvable : {session_id}")
            return None

        position = db.job_positions.find_one({"_id": ObjectId(session["job_position_id"])})
        if not position:
            logger.error(f"Poste introuvable pour session {session_id}")
            return None

        candidate = db.candidates.find_one({"_id": ObjectId(session["candidate_id"])})
        candidate_name = (
            f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()
            if candidate else "Candidat"
        )

        lang    = language or session.get("language", "fr")
        answers = session.get("answers", [])
        questions: dict[int, dict] = {
            q["order"]: q for q in position.get("questions", [])
        }

        logger.info(
            f"Évaluation session {session_id} | "
            f"{len(answers)} réponse(s) | langue={lang}"
        )

        # ── Évaluation par réponse en parallèle ───────────────────────────
        tasks = []
        for ans in answers:
            q_order = ans.get("question_order", 0)
            q_data  = questions.get(q_order, {})
            q_text  = ans.get("question_text") or self._get_question_text(q_data, lang)
            weight  = float(q_data.get("weight", 1.0))
            tasks.append(
                self.evaluate_single_answer(
                    question_text=q_text,
                    answer_transcript=ans.get("transcript", ""),
                    question_order=q_order,
                    language=lang,
                    position_title=position.get("title", ""),
                    audio_path=ans.get("audio_file_path"),
                    weight=weight,
                )
            )

        per_answer: list[AnswerEvaluation] = await asyncio.gather(*tasks)

        # ── Injection métriques faciales depuis BD ────────────────────────
        # Les métriques ont déjà été analysées et sauvegardées pendant l'entretien
        # dans answers[n].evaluation.facial_analysis — on les récupère ici
        facial_map: dict[int, dict] = {}
        for ans in answers:
            q_order  = ans.get("question_order", 0)
            eval_doc = ans.get("evaluation", {}) or {}
            facial   = eval_doc.get("facial_analysis")
            if facial:
                facial_map[q_order] = facial

        # Injecter dans chaque AnswerEvaluation
        enriched_answers = []
        for ae in per_answer:
            f = facial_map.get(ae.question_order)
            if f:
                try:
                    facial_obj = FacialSummary(
                        dominant_emotion  = f.get("dominant_emotion",  "neutral"),
                        emotion_scores    = f.get("emotion_scores",    {}),
                        eye_contact_ratio = f.get("eye_contact_ratio", 0.0),
                        head_stability    = f.get("head_stability",    1.0),
                        smile_ratio       = f.get("smile_ratio",       0.0),
                        confidence_score  = f.get("confidence_score",  5.0),
                        stress_score      = f.get("stress_score",      5.0),
                        engagement_score  = f.get("engagement_score",  5.0),
                        frames_analyzed   = f.get("frames_analyzed",   0),
                        frames_with_face  = f.get("frames_with_face",  0),
                        face_detection_rate = f.get("face_detection_rate", 0.0),
                    )
                    ae = ae.model_copy(update={"facial": facial_obj})
                except Exception as e:
                    logger.warning(f"Injection faciale Q{ae.question_order} : {e}")
            enriched_answers.append(ae)
        per_answer = enriched_answers

        # ── Calcul GlobalFacialSummary ────────────────────────────────────
        facial_answers = [ae for ae in per_answer if ae.facial is not None]
        global_facial: Optional[GlobalFacialSummary] = None
        if facial_answers:
            def _avg(vals): return round(sum(vals) / len(vals), 3) if vals else 0.0
            emotion_counts: dict[str, int] = {}
            for ae in facial_answers:
                e = ae.facial.dominant_emotion
                emotion_counts[e] = emotion_counts.get(e, 0) + 1
            dominant = max(emotion_counts, key=emotion_counts.get)
            global_facial = GlobalFacialSummary(
                avg_confidence     = _avg([ae.facial.confidence_score  for ae in facial_answers]),
                avg_stress         = _avg([ae.facial.stress_score       for ae in facial_answers]),
                avg_engagement     = _avg([ae.facial.engagement_score   for ae in facial_answers]),
                avg_eye_contact    = _avg([ae.facial.eye_contact_ratio  for ae in facial_answers]),
                avg_head_stability = _avg([ae.facial.head_stability     for ae in facial_answers]),
                dominant_emotion   = dominant,
                facial_available   = True,
            )
            logger.info(
                f"GlobalFacialSummary | "
                f"confiance={global_facial.avg_confidence}/10 | "
                f"stress={global_facial.avg_stress}/10 | "
                f"engagement={global_facial.avg_engagement}/10 | "
                f"contact={round(global_facial.avg_eye_contact*100)}% | "
                f"émotion={dominant}"
            )

        # ── Moyenne pondérée ───────────────────────────────────────────────
        avg_score = _weighted_avg([(a.score, a.weight) for a in per_answer])
        logger.info(
            "Scores : "
            + ", ".join(f"Q{a.question_order}={a.score}/10 (×{a.weight})" for a in per_answer)
            + f" → weighted_avg={avg_score}/10"
        )

        # ── Résumé global LLM ─────────────────────────────────────────────
        global_raw = await self.llm.generate_global_summary(
            answers_eval=[a.model_dump() for a in per_answer],
            position_title=position.get("title", ""),
            candidate_name=candidate_name,
            language=lang,
            weighted_avg=avg_score,
        )

        decision = compute_decision(avg_score)

        evaluation = GlobalEvaluation(
            session_id=session_id,
            candidate_name=candidate_name,
            position_title=position.get("title", ""),
            language=lang,
            total_questions=len(position.get("questions", [])),
            answered_questions=len(answers),
            average_score=avg_score,
            decision=decision,
            decision_label=DECISION_LABELS.get(lang, DECISION_LABELS["fr"]).get(decision, decision),
            decision_color=DECISION_COLORS.get(decision, "#F59E0B"),
            decision_reason=global_raw.get("decision_reason", ""),
            recommendation=global_raw.get("recommendation", ""),
            key_strengths=global_raw.get("key_strengths", []),
            key_improvements=global_raw.get("key_improvements", []),
            summary=global_raw.get("summary", ""),
            per_answer=per_answer,
            llm_model=self.llm.model,
            facial_summary=global_facial,
        )

        evaluation = self._fill_missing_fields(evaluation, per_answer, lang)
        self._save_evaluation(session_id, evaluation)

        logger.info(
            f"✅ Évaluation terminée {session_id} | "
            f"average_score={avg_score}/10 | "
            f"decision={evaluation.decision} | "
            f"recommendation={evaluation.recommendation!r}"
        )
        return evaluation

    # ── Garantie de complétude ────────────────────────────────────────────

    def _fill_missing_fields(
        self,
        ev: GlobalEvaluation,
        per_answer: list[AnswerEvaluation],
        lang: str,
    ) -> GlobalEvaluation:
        score = ev.average_score

        if not ev.recommendation:
            if lang == "fr":
                reco = "Embaucher" if score >= 7 else ("En attente" if score >= 5 else "Refuser")
            elif lang == "ar":
                reco = "توظيف" if score >= 7 else ("قيد الانتظار" if score >= 5 else "رفض")
            else:
                reco = "Hire" if score >= 7 else ("On Hold" if score >= 5 else "Reject")
            ev = ev.model_copy(update={"recommendation": reco})

        if not ev.decision_reason:
            n = len(per_answer)
            if lang == "fr":
                reason = (
                    f"Moyenne pondérée de {score}/10 sur {n} question(s). "
                    f"Barème : ≥7 = Embaucher, 5–7 = En attente, <5 = Refuser."
                )
            elif lang == "ar":
                reason = f"متوسط مرجح {score}/10 على {n} سؤال. المعايير : ≥7 = توظيف، 5-7 = انتظار، <5 = رفض."
            else:
                reason = (
                    f"Weighted average {score}/10 across {n} question(s). "
                    f"Scale: ≥7 = Hire, 5–7 = On Hold, <5 = Reject."
                )
            ev = ev.model_copy(update={"decision_reason": reason})

        if not ev.key_strengths:
            seen, result = set(), []
            for a in per_answer:
                for s in a.strengths:
                    if s and s not in seen:
                        seen.add(s); result.append(s)
            ev = ev.model_copy(update={"key_strengths": result[:4]})

        if not ev.key_improvements:
            seen, result = set(), []
            for a in per_answer:
                for imp in a.improvements:
                    if imp and imp not in seen:
                        seen.add(imp); result.append(imp)
            ev = ev.model_copy(update={"key_improvements": result[:4]})

        if not ev.summary:
            scores_str = ", ".join(
                f"Q{a.question_order}: {a.score}/10 (×{a.weight})" for a in per_answer
            )
            if lang == "fr":
                summary = (
                    f"Entretien de {len(per_answer)} question(s) — "
                    f"moyenne pondérée {score}/10. {scores_str}. "
                    f"Recommandation : {ev.recommendation}."
                )
            elif lang == "ar":
                summary = f"مقابلة {len(per_answer)} سؤال — متوسط مرجح {score}/10. {scores_str}. التوصية : {ev.recommendation}."
            else:
                summary = (
                    f"{len(per_answer)}-question interview — "
                    f"weighted average {score}/10. {scores_str}. "
                    f"Recommendation: {ev.recommendation}."
                )
            ev = ev.model_copy(update={"summary": summary})

        return ev

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _retranscribe(self, audio_path: str, language: str) -> str:
        try:
            path = Path(audio_path)
            if not path.exists():
                return ""
            audio_bytes = path.read_bytes()
            loop        = asyncio.get_event_loop()
            transcript  = await loop.run_in_executor(
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
        doc = evaluation.model_dump()
        try:
            db.evaluations.update_one(
                {"session_id": session_id},
                {"$set": doc},
                upsert=True,
            )
            db.interview_sessions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "evaluation_score":           evaluation.average_score,
                    "evaluation_recommendation":  evaluation.recommendation,
                    "evaluation_decision":        evaluation.decision,
                    "evaluation_decision_label":  evaluation.decision_label,
                    "evaluation_decision_color":  evaluation.decision_color,
                    "evaluation_decision_reason": evaluation.decision_reason,
                }},
            )
            logger.info(
                f"💾 Évaluation persistée | session={session_id} | "
                f"average_score={evaluation.average_score}/10 | decision={evaluation.decision}"
            )
        except Exception as e:
            logger.error(f"Erreur sauvegarde évaluation : {e}")