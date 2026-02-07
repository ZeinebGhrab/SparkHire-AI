from fastapi import APIRouter, Depends, Query, HTTPException
from backend.candidates.models import Candidate, CandidateCreate, CandidateUpdate, Consent
from backend.candidates.crud import CandidateCRUD
from backend.auth.security import get_current_recruiter
from typing import List, Optional

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.post("/", response_model=Candidate)
def create_candidate(
    candidate: CandidateCreate, 
    _: str = Depends(get_current_recruiter)
):
    """Créer un nouveau candidat"""
    return CandidateCRUD.create(candidate)

@router.get("/", response_model=List[Candidate])
def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: str = Depends(get_current_recruiter)
):
    """Lister tous les candidats avec pagination"""
    return CandidateCRUD.get_all(skip=skip, limit=limit)

@router.get("/search/email", response_model=Candidate)
def search_candidate_by_email(
    email: str = Query(..., description="Email du candidat"),
    _: str = Depends(get_current_recruiter)
):
    """Rechercher un candidat par email"""
    candidate = CandidateCRUD.search_by_email(email)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return candidate

@router.get("/search/skills", response_model=List[Candidate])
def search_candidates_by_skills(
    skills: List[str] = Query(..., description="Liste de compétences"),
    min_match: int = Query(1, ge=1, description="Nombre minimum de compétences correspondantes"),
    _: str = Depends(get_current_recruiter)
):
    """Rechercher des candidats par compétences"""
    return CandidateCRUD.search_by_skills(skills, min_match)

@router.get("/{candidate_id}", response_model=Candidate)
def get_candidate(
    candidate_id: str, 
    _: str = Depends(get_current_recruiter)
):
    """Récupérer un candidat par ID"""
    return CandidateCRUD.get_by_id(candidate_id)

@router.patch("/{candidate_id}", response_model=Candidate)
def update_candidate(
    candidate_id: str,
    candidate_update: CandidateUpdate,
    _: str = Depends(get_current_recruiter)
):
    """Mettre à jour partiellement un candidat"""
    return CandidateCRUD.update(candidate_id, candidate_update)

@router.delete("/{candidate_id}")
def delete_candidate(
    candidate_id: str, 
    _: str = Depends(get_current_recruiter)
):
    """Supprimer un candidat"""
    success = CandidateCRUD.delete(candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return {"message": "Candidat supprimé"}

@router.post("/{candidate_id}/consents", response_model=Candidate)
def add_consent(
    candidate_id: str,
    consent: Consent,
    _: str = Depends(get_current_recruiter)
):
    """Ajouter un consentement à un candidat"""
    return CandidateCRUD.add_consent(candidate_id, consent.model_dump())