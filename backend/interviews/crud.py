from backend.database import db
from backend.interviews.models import (
    JobPosition, JobPositionCreate,
    InterviewSession, InterviewSessionCreate, Answer
)
from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
import secrets

# ============ CONSTANTES ============
SESSION_EXPIRATION_MINUTES = 30  # Délai d'expiration: 30 minutes

class JobPositionCRUD:
    """CRUD pour les postes avec questions"""
    
    @staticmethod
    def create(position: JobPositionCreate) -> JobPosition:
        """Créer un nouveau poste"""
        position_dict = position.model_dump()
        position_dict["created_at"] = datetime.utcnow()
        
        result = db.job_positions.insert_one(position_dict)
        position_dict["_id"] = str(result.inserted_id)
        return JobPosition(**position_dict)
    
    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[JobPosition]:
        """Récupérer tous les postes"""
        positions = list(db.job_positions.find().skip(skip).limit(limit).sort("created_at", -1))
        
        for position in positions:
            position["_id"] = str(position["_id"])
        
        return [JobPosition(**position) for position in positions]
    
    @staticmethod
    def get_by_id(position_id: str) -> JobPosition:
        """Récupérer un poste par ID"""
        if not ObjectId.is_valid(position_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        position = db.job_positions.find_one({"_id": ObjectId(position_id)})
        if not position:
            raise HTTPException(status_code=404, detail="Poste non trouvé")
        
        position["_id"] = str(position["_id"])
        return JobPosition(**position)
    
    @staticmethod
    def delete(position_id: str) -> bool:
        """Supprimer un poste"""
        if not ObjectId.is_valid(position_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        result = db.job_positions.delete_one({"_id": ObjectId(position_id)})
        return result.deleted_count > 0


class InterviewSessionCRUD:
    """CRUD pour les sessions d'entretien"""
    
    @staticmethod
    def create(session: InterviewSessionCreate) -> InterviewSession:
        """Créer une nouvelle session d'entretien"""
        # Vérifier que le candidat existe
        if not ObjectId.is_valid(session.candidate_id):
            raise HTTPException(status_code=400, detail="ID candidat invalide")
        
        candidate = db.candidates.find_one({"_id": ObjectId(session.candidate_id)})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")
        
        # Vérifier que le poste existe
        if not ObjectId.is_valid(session.job_position_id):
            raise HTTPException(status_code=400, detail="ID poste invalide")
        
        position = db.job_positions.find_one({"_id": ObjectId(session.job_position_id)})
        if not position:
            raise HTTPException(status_code=404, detail="Poste non trouvé")
        
        # Générer un session_id unique
        session_id = f"session_{secrets.token_urlsafe(16)}"
        
        # Calculer la date d'expiration (30 minutes après création)
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=SESSION_EXPIRATION_MINUTES)
        
        session_dict = session.model_dump()
        session_dict["session_id"] = session_id
        session_dict["status"] = "pending"
        session_dict["current_question_index"] = 0
        session_dict["answers"] = []
        session_dict["created_at"] = now
        session_dict["expires_at"] = expires_at
        session_dict["updated_at"] = now
        
        result = db.interview_sessions.insert_one(session_dict)
        session_dict["_id"] = str(result.inserted_id)
        
        return InterviewSession(**session_dict)
    
    @staticmethod
    def get_all(skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[InterviewSession]:
        """Récupérer toutes les sessions"""
        query = {}
        if status:
            query["status"] = status
        
        sessions = list(db.interview_sessions.find(query).skip(skip).limit(limit).sort("created_at", -1))
        
        for session in sessions:
            session["_id"] = str(session["_id"])
        
        return [InterviewSession(**session) for session in sessions]
    
    @staticmethod
    def get_by_id(session_id_or_mongo_id: str) -> InterviewSession:
        """Récupérer une session par ID MongoDB ou session_id"""
        # Essayer d'abord par session_id
        session = db.interview_sessions.find_one({"session_id": session_id_or_mongo_id})
        
        # Si pas trouvé, essayer par _id MongoDB
        if not session and ObjectId.is_valid(session_id_or_mongo_id):
            session = db.interview_sessions.find_one({"_id": ObjectId(session_id_or_mongo_id)})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        session["_id"] = str(session["_id"])
        return InterviewSession(**session)
    
    @staticmethod
    def get_by_session_id(session_id: str) -> InterviewSession:
        """Récupérer une session par session_id"""
        session = db.interview_sessions.find_one({"session_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        session["_id"] = str(session["_id"])
        return InterviewSession(**session)
    
    @staticmethod
    def validate_session_access(session_id: str) -> tuple[InterviewSession, bool, str]:
        """
        Valider l'accès à une session
        
        Returns:
            tuple: (session, is_valid, error_message)
        """
        # 1. Vérifier que la session existe
        try:
            session = InterviewSessionCRUD.get_by_session_id(session_id)
        except HTTPException:
            return None, False, "Session ID invalide ou introuvable"
        
        # 2. Vérifier que la session n'est pas expirée
        now = datetime.utcnow()
        if now > session.expires_at:
            # Calculer le retard
            delay = (now - session.expires_at).total_seconds() / 60  # en minutes
            return session, False, f"Session expirée (retard de {int(delay)} minutes). Délai maximum: {SESSION_EXPIRATION_MINUTES} minutes"
        
        # 3. Vérifier le statut de la session
        if session.status in ["completed", "cancelled"]:
            return session, False, f"Session déjà {session.status}. Impossible de la réutiliser"
        
        # 4. Tout est OK
        return session, True, ""
    
    @staticmethod
    def update_status(session_id: str, status: str) -> InterviewSession:
        """Mettre à jour le statut d'une session"""
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Statut invalide. Valeurs possibles: {', '.join(valid_statuses)}"
            )
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        # Si status = in_progress, set started_at
        if status == "in_progress":
            update_data["started_at"] = datetime.utcnow()
        
        # Si status = completed, set completed_at
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()
        
        result = db.interview_sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        return InterviewSessionCRUD.get_by_session_id(session_id)
    
    @staticmethod
    def add_answer(session_id: str, answer: Answer) -> InterviewSession:
        """Ajouter une réponse à une session"""
        answer_dict = answer.model_dump()
        
        result = db.interview_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"answers": answer_dict},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        return InterviewSessionCRUD.get_by_session_id(session_id)
    
    @staticmethod
    def increment_question_index(session_id: str) -> InterviewSession:
        """Passer à la question suivante"""
        result = db.interview_sessions.update_one(
            {"session_id": session_id},
            {
                "$inc": {"current_question_index": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session non trouvée")
        
        return InterviewSessionCRUD.get_by_session_id(session_id)
    
    @staticmethod
    def get_by_candidate_id(candidate_id: str) -> List[InterviewSession]:
        """Récupérer toutes les sessions d'un candidat"""
        if not ObjectId.is_valid(candidate_id):
            raise HTTPException(status_code=400, detail="ID candidat invalide")
        
        sessions = list(db.interview_sessions.find({"candidate_id": candidate_id}).sort("created_at", -1))
        
        for session in sessions:
            session["_id"] = str(session["_id"])
        
        return [InterviewSession(**session) for session in sessions]
    
    @staticmethod
    def delete(session_id: str) -> bool:
        """Supprimer une session"""
        result = db.interview_sessions.delete_one({"session_id": session_id})
        return result.deleted_count > 0