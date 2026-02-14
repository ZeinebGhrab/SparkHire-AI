"""
Service de notifications automatiques
Envoie des notifications lors d'événements importants
"""

from backend.database import db
from backend.notifications.models import NotificationCreate
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour gérer les notifications automatiques"""
    
    @staticmethod
    async def notify_interview_started(session_id: str, recruiter_email: str):
        """Notifier le début d'un entretien"""
        try:
            notification = {
                "recipient_email": recruiter_email,
                "type": "interview_started",
                "title": "Entretien Démarré",
                "message": f"L'entretien {session_id} vient de commencer",
                "data": {"session_id": session_id},
                "priority": "normal",
                "read": False,
                "created_at": datetime.utcnow()
            }
            
            db.notifications.insert_one(notification)
            logger.info(f"Notification envoyée: entretien démarré {session_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
    
    @staticmethod
    async def notify_interview_completed(
        session_id: str, 
        recruiter_email: str,
        candidate_name: str,
        total_questions: int,
        total_answers: int
    ):
        """Notifier la fin d'un entretien"""
        try:
            notification = {
                "recipient_email": recruiter_email,
                "type": "interview_completed",
                "title": "Entretien Terminé",
                "message": f"{candidate_name} a terminé l'entretien ({total_answers}/{total_questions} réponses)",
                "data": {
                    "session_id": session_id,
                    "candidate_name": candidate_name,
                    "total_questions": total_questions,
                    "total_answers": total_answers
                },
                "priority": "high",
                "read": False,
                "created_at": datetime.utcnow()
            }
            
            db.notifications.insert_one(notification)
            logger.info(f"Notification envoyée: entretien terminé {session_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
    
    @staticmethod
    async def notify_new_match(
        recruiter_email: str,
        candidate_name: str,
        job_title: str,
        match_score: float
    ):
        """Notifier un nouveau match de haute qualité"""
        try:
            if match_score >= 0.8:  # Seuil pour notification
                notification = {
                    "recipient_email": recruiter_email,
                    "type": "match_found",
                    "title": "Excellent Match Trouvé!",
                    "message": f"{candidate_name} est un excellent match pour {job_title} (Score: {match_score:.1%})",
                    "data": {
                        "candidate_name": candidate_name,
                        "job_title": job_title,
                        "match_score": match_score
                    },
                    "priority": "high",
                    "read": False,
                    "created_at": datetime.utcnow()
                }
                
                db.notifications.insert_one(notification)
                logger.info(f"Notification envoyée: nouveau match {candidate_name} - {job_title}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
    
    @staticmethod
    async def notify_new_candidate(
        recruiter_email: str,
        candidate_name: str,
        candidate_email: str,
        skills: list
    ):
        """Notifier l'ajout d'un nouveau candidat"""
        try:
            notification = {
                "recipient_email": recruiter_email,
                "type": "new_candidate",
                "title": "Nouveau Candidat Enregistré",
                "message": f"{candidate_name} ({candidate_email}) a été ajouté au système",
                "data": {
                    "candidate_name": candidate_name,
                    "candidate_email": candidate_email,
                    "skills": skills
                },
                "priority": "normal",
                "read": False,
                "created_at": datetime.utcnow()
            }
            
            db.notifications.insert_one(notification)
            logger.info(f"Notification envoyée: nouveau candidat {candidate_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
    
    @staticmethod
    async def notify_system_alert(
        recruiter_email: str,
        alert_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Notifier une alerte système"""
        try:
            notification = {
                "recipient_email": recruiter_email,
                "type": f"system_alert_{alert_type}",
                "title": "Alerte Système",
                "message": message,
                "data": data or {},
                "priority": "urgent",
                "read": False,
                "created_at": datetime.utcnow()
            }
            
            db.notifications.insert_one(notification)
            logger.warning(f"Alerte système envoyée: {alert_type}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")


# Instance globale
notification_service = NotificationService()