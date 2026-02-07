from backend.database import db
from backend.candidates.models import Candidate, CandidateCreate, CandidateUpdate
from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime
from typing import Optional, List

class CandidateCRUD:
    @staticmethod
    def create(candidate: CandidateCreate) -> Candidate:
        """Créer un nouveau candidat"""
        candidate_dict = candidate.model_dump()
        candidate_dict["created_at"] = datetime.utcnow()
        candidate_dict["updated_at"] = datetime.utcnow()
        
        result = db.candidates.insert_one(candidate_dict)
        candidate_dict["_id"] = str(result.inserted_id)
        return Candidate(**candidate_dict)

    @staticmethod
    def get_all(skip: int = 0, limit: int = 100) -> List[Candidate]:
        """Récupérer tous les candidats avec pagination"""
        candidates = list(db.candidates.find().skip(skip).limit(limit).sort("created_at", -1))
        for candidate in candidates:
            candidate["_id"] = str(candidate["_id"])
        return [Candidate(**candidate) for candidate in candidates]

    @staticmethod
    def get_by_id(candidate_id: str) -> Candidate:
        """Récupérer un candidat par ID"""
        if not ObjectId.is_valid(candidate_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        candidate = db.candidates.find_one({"_id": ObjectId(candidate_id)})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")
        
        candidate["_id"] = str(candidate["_id"])
        return Candidate(**candidate)

    @staticmethod
    def search_by_email(email: str) -> Optional[Candidate]:
        """Rechercher un candidat par email"""
        candidate = db.candidates.find_one({"contact.email": email})
        if not candidate:
            return None
        
        candidate["_id"] = str(candidate["_id"])
        return Candidate(**candidate)

    @staticmethod
    def search_by_skills(skills: List[str], min_match: int = 1) -> List[Candidate]:
        """Rechercher des candidats par compétences"""
        # Recherche des candidats qui ont au moins min_match compétences parmi celles demandées
        candidates = list(db.candidates.find({
            "skills": {"$in": skills}
        }))
        
        # Filtrer et trier par nombre de correspondances
        results = []
        for candidate in candidates:
            matching_skills = set(candidate.get("skills", [])) & set(skills)
            if len(matching_skills) >= min_match:
                candidate["_id"] = str(candidate["_id"])
                candidate["_matching_skills_count"] = len(matching_skills)
                results.append(candidate)
        
        # Trier par nombre de compétences correspondantes (décroissant)
        results.sort(key=lambda x: x.get("_matching_skills_count", 0), reverse=True)
        
        return [Candidate(**candidate) for candidate in results]

    @staticmethod
    def update(candidate_id: str, candidate_update: CandidateUpdate) -> Candidate:
        """Mettre à jour un candidat"""
        if not ObjectId.is_valid(candidate_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        # Ne mettre à jour que les champs fournis
        update_data = candidate_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = db.candidates.update_one(
            {"_id": ObjectId(candidate_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")
        
        return CandidateCRUD.get_by_id(candidate_id)

    @staticmethod
    def delete(candidate_id: str) -> bool:
        """Supprimer un candidat"""
        if not ObjectId.is_valid(candidate_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        result = db.candidates.delete_one({"_id": ObjectId(candidate_id)})
        return result.deleted_count > 0

    @staticmethod
    def add_consent(candidate_id: str, consent: dict) -> Candidate:
        """Ajouter un consentement à un candidat"""
        if not ObjectId.is_valid(candidate_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        
        consent["timestamp"] = datetime.utcnow()
        
        result = db.candidates.update_one(
            {"_id": ObjectId(candidate_id)},
            {
                "$push": {"consents": consent},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Candidat non trouvé")
        
        return CandidateCRUD.get_by_id(candidate_id)