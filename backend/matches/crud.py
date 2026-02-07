from backend.database import db
from backend.matches.models import Match, MatchCreate, MatchUpdate
from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional

class MatchCRUD:
    @staticmethod
    def create(match: MatchCreate) -> Match:
        """Créer un nouveau match"""
        # Vérifier que le candidat et le job existent
        if not ObjectId.is_valid(match.candidate_id):
            raise HTTPException(status_code=400, detail="ID candidat invalide")
        if not ObjectId.is_valid(match.job_id):
            raise HTTPException(status_code=400, detail="ID job invalide")
        
        candidate = db.candidates.find_one({"_id": ObjectId(match.candidate_id)})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")
        
        job = db.jobs.find_one({"_id": ObjectId(match.job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
        
        # Vérifier qu'un match n'existe pas déjà
        existing = db.matches.find_one({
            "candidate_id": match.candidate_id,
            "job_id": match.job_id
        })
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Un match existe déjà pour ce candidat et cette offre"
            )
        
        match_dict = match.model_dump()
        match_dict["created_at"] = datetime.utcnow()
        match_dict["updated_at"] = datetime.utcnow()
        
        result = db.matches.insert_one(match_dict)
        match_dict["_id"] = str(result.inserted_id)
        return Match(**match_dict)

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100, min_score: float = 0.0) -> List[Match]:
        """Récupérer tous les matches avec pagination et score minimum"""
        query = {"score": {"$gte": min_score}}
        matches = list(db.matches.find(query).skip(skip).limit(limit).sort("score", -1))
        
        for match in matches:
            match["_id"] = str(match["_id"])
        return [Match(**match) for match in matches]

    @staticmethod
    def get_by_id(match_id: str) -> Match:
        """Récupérer un match par ID"""
        if not ObjectId.is_valid(match_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        match = db.matches.find_one({"_id": ObjectId(match_id)})
        if not match:
            raise HTTPException(status_code=404, detail="Match non trouvé")
        
        match["_id"] = str(match["_id"])
        return Match(**match)

    @staticmethod
    def get_by_candidate_id(candidate_id: str, min_score: float = 0.0) -> List[Match]:
        """Récupérer tous les matches d'un candidat"""
        if not ObjectId.is_valid(candidate_id):
            raise HTTPException(status_code=400, detail="ID candidat invalide")
        
        query = {
            "candidate_id": candidate_id,
            "score": {"$gte": min_score}
        }
        matches = list(db.matches.find(query).sort("score", -1))
        
        for match in matches:
            match["_id"] = str(match["_id"])
        return [Match(**match) for match in matches]

    @staticmethod
    def get_by_job_id(job_id: str, min_score: float = 0.0) -> List[Match]:
        """Récupérer tous les matches d'une offre d'emploi"""
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID job invalide")
        
        query = {
            "job_id": job_id,
            "score": {"$gte": min_score}
        }
        matches = list(db.matches.find(query).sort("score", -1))
        
        for match in matches:
            match["_id"] = str(match["_id"])
        return [Match(**match) for match in matches]

    @staticmethod
    def get_by_status(status: str, skip: int = 0, limit: int = 100) -> List[Match]:
        """Récupérer tous les matches par statut"""
        matches = list(
            db.matches.find({"status": status})
            .skip(skip)
            .limit(limit)
            .sort("score", -1)
        )
        
        for match in matches:
            match["_id"] = str(match["_id"])
        return [Match(**match) for match in matches]

    @staticmethod
    def update(match_id: str, match_update: MatchUpdate) -> Match:
        """Mettre à jour un match"""
        if not ObjectId.is_valid(match_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        update_data = match_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = db.matches.update_one(
            {"_id": ObjectId(match_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Match non trouvé")
        
        return MatchCRUD.get_by_id(match_id)

    @staticmethod
    def update_status(match_id: str, status: str, recruiter_notes: Optional[str] = None) -> Match:
        """Mettre à jour le statut d'un match"""
        if not ObjectId.is_valid(match_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        valid_statuses = ["pending", "reviewed", "accepted", "rejected"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Statut invalide. Valeurs possibles: {', '.join(valid_statuses)}"
            )
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if recruiter_notes is not None:
            update_data["recruiter_notes"] = recruiter_notes
        
        result = db.matches.update_one(
            {"_id": ObjectId(match_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Match non trouvé")
        
        return MatchCRUD.get_by_id(match_id)

    @staticmethod
    def delete(match_id: str) -> bool:
        """Supprimer un match"""
        if not ObjectId.is_valid(match_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        result = db.matches.delete_one({"_id": ObjectId(match_id)})
        return result.deleted_count > 0