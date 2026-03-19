from backend.database import db
from backend.interviews.models import (
    JobPosition, JobPositionCreate,
    InterviewSession, InterviewSessionCreate,
    Answer, AnswerEvaluationData,
)
from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
import secrets
import logging

logger = logging.getLogger(__name__)

# ============ CONSTANTES ============
SESSION_EXPIRATION_MINUTES = 30
LATE_ACCESS_MINUTES = 30

# ── Textes notification trilingues ────────────────────────────────────────────
_NOTIF_TEXTS = {
    "ar": {
        "title":   "مقابلة مكتملة",
        "message": "أكمل المرشح {candidate_name} مقابلته للمنصب {position_title}. يرجى الاطلاع عليها.",
    },
    "fr": {
        "title":   "Entretien complété",
        "message": "Le candidat {candidate_name} a complété son entretien pour le poste {position_title}. Veuillez le consulter.",
    },
    "en": {
        "title":   "Interview completed",
        "message": "Candidate {candidate_name} has completed their interview for the {position_title} position. Please review it.",
    },
}


def _send_completion_notification(session_id: str) -> None:
    """
    Insère une notification dans db.notifications quand une session passe à 'completed'.
    Appelée DIRECTEMENT depuis update_status — aucune dépendance externe.

    Stratégie destinataires :
      1. created_by sur la session  (email du recruteur créateur)
      2. Tous les recruteurs         (fallback si created_by absent)
    """
    try:
        # ── Charger la session ────────────────────────────────────────────────
        session_doc = db.interview_sessions.find_one(
            {"session_id": session_id},
            {"created_by": 1, "candidate_id": 1, "job_position_id": 1,
             "language": 1, "answers": 1},
        )
        if not session_doc:
            logger.error(f"_send_completion_notification: session {session_id} introuvable")
            return

        created_by    = session_doc.get("created_by", "")
        total_answers = len(session_doc.get("answers", []))
        language      = session_doc.get("language", "fr")

        # ── Destinataires ─────────────────────────────────────────────────────
        if created_by and "@" in str(created_by):
            emails = [created_by]
            logger.info(f"Notification → created_by : {created_by}")
        else:
            all_recruiters = list(db.recruiters.find({}, {"email": 1}))
            emails = [r["email"] for r in all_recruiters if r.get("email")]
            logger.warning(
                f"created_by absent pour {session_id} — "
                f"fallback {len(emails)} recruteur(s) : {emails}"
            )

        if not emails:
            logger.error("Aucun recruteur trouvé — notification annulée")
            return

        # ── Candidat ──────────────────────────────────────────────────────────
        candidate_name = "Candidat"
        try:
            cid = session_doc.get("candidate_id", "")
            if cid and ObjectId.is_valid(cid):
                cand = db.candidates.find_one(
                    {"_id": ObjectId(cid)},
                    {"first_name": 1, "last_name": 1},
                )
                if cand:
                    candidate_name = (
                        f"{cand.get('first_name','').strip()} "
                        f"{cand.get('last_name','').strip()}"
                    ).strip() or "Candidat"
        except Exception as e:
            logger.warning(f"Chargement candidat pour notif : {e}")

        # ── Poste ─────────────────────────────────────────────────────────────
        position_title = "Poste"
        try:
            pid = session_doc.get("job_position_id", "")
            if pid and ObjectId.is_valid(pid):
                pos = db.job_positions.find_one(
                    {"_id": ObjectId(pid)},
                    {"title": 1},
                )
                if pos:
                    position_title = pos.get("title", "Poste")
        except Exception as e:
            logger.warning(f"Chargement poste pour notif : {e}")

        # ── Textes ────────────────────────────────────────────────────────────
        lang  = language if language in _NOTIF_TEXTS else "fr"
        texts = _NOTIF_TEXTS[lang]
        title   = texts["title"]
        message = texts["message"].format(
            candidate_name=candidate_name,
            position_title=position_title,
        )

        # ── Insertion ─────────────────────────────────────────────────────────
        ok = 0
        for email in emails:
            doc = {
                "recipient_email": email,
                "type":            "interview_completed",
                "title":           title,
                "message":         message,
                "data": {
                    "session_id":     session_id,
                    "candidate_name": candidate_name,
                    "position_title": position_title,
                    "total_answers":  total_answers,
                },
                "priority":   "high",
                "read":       False,
                "created_at": datetime.utcnow(),
            }
            result = db.notifications.insert_one(doc)
            logger.info(
                f"Notification insérée | _id={result.inserted_id} | "
                f"recipient={email} | message='{message}'"
            )
            ok += 1

        logger.info(
            f"{ok}/{len(emails)} notification(s) créée(s) | session={session_id} | "
            f"candidat={candidate_name} | poste={position_title}"
        )

    except Exception as e:
        logger.error(
            f"_send_completion_notification ERREUR | session={session_id} | {e}",
            exc_info=True,
        )


class JobPositionCRUD:
    """CRUD pour les postes avec questions"""

    @staticmethod
    def create(position: JobPositionCreate) -> JobPosition:
        position_dict = position.model_dump()
        position_dict["created_at"] = datetime.utcnow()
        result = db.job_positions.insert_one(position_dict)
        position_dict["_id"] = str(result.inserted_id)
        return JobPosition(**position_dict)

    @staticmethod
    def get_all(
        skip: int = 0,
        limit: int = 100,
        department: Optional[str] = None,
        location: Optional[str] = None,
        is_active: Optional[bool] = None,
        period_days: Optional[int] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[JobPosition]:
        query: dict = {}
        if department:
            query["department"] = {"$regex": department, "$options": "i"}
        if location:
            query["location"] = {"$regex": location, "$options": "i"}
        if is_active is not None:
            query["is_active"] = is_active
        if period_days:
            since = datetime.utcnow() - timedelta(days=period_days)
            query["created_at"] = {"$gte": since}
        allowed_sort = {"created_at", "title", "department", "location"}
        sort_field = sort_by if sort_by in allowed_sort else "created_at"
        sort_dir   = -1 if order.lower() == "desc" else 1
        positions = list(
            db.job_positions.find(query)
            .skip(skip).limit(limit).sort(sort_field, sort_dir)
        )
        for p in positions:
            p["_id"] = str(p["_id"])
        return [JobPosition(**p) for p in positions]

    @staticmethod
    def get_distinct_departments() -> List[str]:
        return sorted(db.job_positions.distinct("department"))

    @staticmethod
    def get_distinct_locations() -> List[str]:
        return sorted([l for l in db.job_positions.distinct("location") if l])

    @staticmethod
    def get_by_id(position_id: str) -> JobPosition:
        if not ObjectId.is_valid(position_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        position = db.job_positions.find_one({"_id": ObjectId(position_id)})
        if not position:
            raise HTTPException(status_code=404, detail="Poste non trouvé")
        position["_id"] = str(position["_id"])
        return JobPosition(**position)

    @staticmethod
    def delete(position_id: str) -> bool:
        if not ObjectId.is_valid(position_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        result = db.job_positions.delete_one({"_id": ObjectId(position_id)})
        return result.deleted_count > 0


class InterviewSessionCRUD:
    """CRUD pour les sessions d'entretien"""

    @staticmethod
    def create(session: InterviewSessionCreate, created_by: str = "") -> InterviewSession:
        if not ObjectId.is_valid(session.candidate_id):
            raise HTTPException(status_code=400, detail="ID candidat invalide")
        candidate = db.candidates.find_one({"_id": ObjectId(session.candidate_id)})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")

        if not ObjectId.is_valid(session.job_position_id):
            raise HTTPException(status_code=400, detail="ID poste invalide")
        position = db.job_positions.find_one({"_id": ObjectId(session.job_position_id)})
        if not position:
            raise HTTPException(status_code=404, detail="Poste non trouvé")

        session_id   = f"session_{secrets.token_urlsafe(16)}"
        now          = datetime.utcnow()
        scheduled_at = session.scheduled_at if hasattr(session, "scheduled_at") else None

        if scheduled_at:
            late_access_deadline = scheduled_at + timedelta(minutes=LATE_ACCESS_MINUTES)
            expires_at           = late_access_deadline
        else:
            late_access_deadline = None
            expires_at           = now + timedelta(minutes=SESSION_EXPIRATION_MINUTES)

        session_dict = session.model_dump()
        session_dict.update({
            "session_id":            session_id,
            "status":                "pending",
            "current_question_index": 0,
            "answers":               [],
            "created_at":            now,
            "expires_at":            expires_at,
            "updated_at":            now,
            "scheduled_at":          scheduled_at,
            "late_access_deadline":  late_access_deadline,
            "created_by":            created_by,
        })

        result = db.interview_sessions.insert_one(session_dict)
        session_dict["_id"] = str(result.inserted_id)
        logger.info(
            f"Session créée | id={session_id} | created_by={created_by!r}"
        )
        return InterviewSession(**session_dict)

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[InterviewSession]:
        query = {}
        if status:
            query["status"] = status
        sessions = list(db.interview_sessions.find(query).skip(skip).limit(limit).sort("created_at", -1))
        for s in sessions:
            s["_id"] = str(s["_id"])
        return [InterviewSession(**s) for s in sessions]

    @staticmethod
    def get_by_id(session_id_or_mongo_id: str) -> InterviewSession:
        session = db.interview_sessions.find_one({"session_id": session_id_or_mongo_id})
        if not session and ObjectId.is_valid(session_id_or_mongo_id):
            session = db.interview_sessions.find_one({"_id": ObjectId(session_id_or_mongo_id)})
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        session["_id"] = str(session["_id"])
        return InterviewSession(**session)

    @staticmethod
    def get_by_session_id(session_id: str) -> InterviewSession:
        session = db.interview_sessions.find_one({"session_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        session["_id"] = str(session["_id"])
        return InterviewSession(**session)

    @staticmethod
    def validate_session_access(session_id: str) -> tuple:
        try:
            session = InterviewSessionCRUD.get_by_session_id(session_id)
        except HTTPException:
            return None, False, "Session ID invalide ou introuvable."

        now          = datetime.utcnow()
        scheduled_at = getattr(session, "scheduled_at", None)
        deadline     = getattr(session, "late_access_deadline", None)

        if session.status == "completed":
            return session, False, "Cet entretien est déjà terminé."
        if session.status == "cancelled":
            return session, False, "Cette session a été annulée."

        if scheduled_at:
            if now < scheduled_at:
                delta_min = int((scheduled_at - now).total_seconds() / 60)
                hrs, mins = divmod(delta_min, 60)
                human = f"{hrs}h{mins:02d}" if hrs else f"{mins} min"
                return session, False, (
                    f"Entretien non encore disponible. Il commence dans {human} "
                    f"(prévu le {scheduled_at.strftime('%d/%m/%Y à %H:%M')} UTC)."
                )
            if deadline and now > deadline:
                delay_min = int((now - scheduled_at).total_seconds() / 60)
                return session, False, (
                    f"Retard trop important ({delay_min} min). "
                    f"Délai max {LATE_ACCESS_MINUTES} min après "
                    f"{scheduled_at.strftime('%d/%m/%Y à %H:%M')} UTC."
                )
        elif now > session.expires_at:
            delay = int((now - session.expires_at).total_seconds() / 60)
            return session, False, (
                f"Session expirée depuis {delay} minutes."
            )

        return session, True, ""

    @staticmethod
    def reschedule(session_id: str, scheduled_at: datetime) -> InterviewSession:
        session = InterviewSessionCRUD.get_by_session_id(session_id)
        if session.status == "completed":
            raise HTTPException(status_code=400, detail="Impossible de replanifier un entretien terminé.")
        late_access_deadline = scheduled_at + timedelta(minutes=LATE_ACCESS_MINUTES)
        fields: dict = {
            "scheduled_at":         scheduled_at,
            "late_access_deadline": late_access_deadline,
            "expires_at":           late_access_deadline,
            "updated_at":           datetime.utcnow(),
        }
        if session.status == "cancelled":
            fields["status"] = "pending"
        db.interview_sessions.update_one({"session_id": session_id}, {"$set": fields})
        return InterviewSessionCRUD.get_by_session_id(session_id)

    @staticmethod
    def update_status(session_id: str, status: str) -> InterviewSession:
        """
        Met à jour le statut d'une session.

        ★ Quand status == "completed" : insère automatiquement une notification
          dans db.notifications pour le recruteur créateur (ou tous en fallback).
        """
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Statut invalide : {', '.join(valid_statuses)}"
            )

        update_data: dict = {"status": status, "updated_at": datetime.utcnow()}
        if status == "in_progress":
            update_data["started_at"] = datetime.utcnow()
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()

        result = db.interview_sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data},
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session non trouvée")

        # ── Notification automatique quand l'entretien se termine ─────────────
        if status == "completed":
            logger.info(f"Déclenchement notification (update_status completed) | {session_id}")
            _send_completion_notification(session_id)

        return InterviewSessionCRUD.get_by_session_id(session_id)

    @staticmethod
    def add_answer(session_id: str, answer: Answer) -> InterviewSession:
        result = db.interview_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"answers": answer.model_dump()},
                "$set":  {"updated_at": datetime.utcnow()},
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        return InterviewSessionCRUD.get_by_session_id(session_id)

    @staticmethod
    def save_answer_evaluation(
        session_id: str,
        question_order: int,
        evaluation: AnswerEvaluationData,
    ) -> bool:
        eval_dict = evaluation.model_dump()
        result = db.interview_sessions.update_one(
            {
                "session_id":             session_id,
                "answers.question_order": question_order,
            },
            {
                "$set": {
                    "answers.$.evaluation": eval_dict,
                    "updated_at":           datetime.utcnow(),
                }
            },
        )
        return result.matched_count > 0

    @staticmethod
    def update_answer(
        session_id: str,
        question_order: int,
        transcript: str | None = None,
        evaluation: "AnswerEvaluationData | None" = None,
        audio_followup_path: str | None = None,
        initial_score: float | None = None,
        initial_verdict: str | None = None,
        followup_question: str | None = None,
        followup_transcript: str | None = None,
    ) -> bool:
        fields: dict = {"updated_at": datetime.utcnow()}
        if transcript is not None:
            fields["answers.$.transcript"] = transcript
        if evaluation is not None:
            eval_dict = evaluation.model_dump()
            if followup_question is not None:
                eval_dict["followup_question"] = followup_question
                eval_dict["had_followup"]       = True
            if followup_transcript is not None:
                eval_dict["followup_transcript"] = followup_transcript
            if initial_score is not None:
                eval_dict["initial_score"]   = initial_score
            if initial_verdict is not None:
                eval_dict["initial_verdict"] = initial_verdict
            fields["answers.$.evaluation"] = eval_dict
        if audio_followup_path is not None:
            fields["answers.$.audio_followup_path"] = audio_followup_path
        result = db.interview_sessions.update_one(
            {
                "session_id":             session_id,
                "answers.question_order": question_order,
            },
            {"$set": fields},
        )
        return result.matched_count > 0

    @staticmethod
    def get_answers_with_evaluations(session_id: str) -> List[Answer]:
        doc = db.interview_sessions.find_one(
            {"session_id": session_id},
            {"answers": 1, "_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        return [Answer(**a) for a in doc.get("answers", [])]

    @staticmethod
    def increment_question_index(session_id: str) -> InterviewSession:
        result = db.interview_sessions.update_one(
            {"session_id": session_id},
            {
                "$inc": {"current_question_index": 1},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        return InterviewSessionCRUD.get_by_session_id(session_id)

    @staticmethod
    def get_by_candidate_id(candidate_id: str) -> List[InterviewSession]:
        if not ObjectId.is_valid(candidate_id):
            raise HTTPException(status_code=400, detail="ID candidat invalide")
        sessions = list(
            db.interview_sessions.find({"candidate_id": candidate_id}).sort("created_at", -1)
        )
        for s in sessions:
            s["_id"] = str(s["_id"])
        return [InterviewSession(**s) for s in sessions]

    @staticmethod
    def delete(session_id: str) -> bool:
        result = db.interview_sessions.delete_one({"session_id": session_id})
        return result.deleted_count > 0