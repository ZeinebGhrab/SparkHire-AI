from fastapi import APIRouter, Depends, Query, HTTPException, Body
from backend.matches.models import Match, MatchCreate, MatchUpdate
from backend.matches.crud import MatchCRUD
from backend.auth.security import get_current_recruiter
from typing import List, Optional

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.post("/", response_model=Match)
def create_match(
    match: MatchCreate, 
    _: str = Depends(get_current_recruiter)
):
    """Créer un nouveau match entre un candidat et une offre d'emploi"""
    return MatchCRUD.create(match)

@router.get("/", response_model=List[Match])
def list_matches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Score minimum"),
    _: str = Depends(get_current_recruiter)
):
    """Lister tous les matches avec pagination et filtrage par score"""
    return MatchCRUD.get_all(skip=skip, limit=limit, min_score=min_score)

@router.get("/status/{status}", response_model=List[Match])
def get_matches_by_status(
    status: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: str = Depends(get_current_recruiter)
):
    """Récupérer tous les matches par statut (pending, reviewed, accepted, rejected)"""
    return MatchCRUD.get_by_status(status, skip=skip, limit=limit)

@router.get("/candidate/{candidate_id}", response_model=List[Match])
def get_candidate_matches(
    candidate_id: str,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    _: str = Depends(get_current_recruiter)
):
    """Récupérer tous les matches d'un candidat"""
    return MatchCRUD.get_by_candidate_id(candidate_id, min_score=min_score)

@router.get("/job/{job_id}", response_model=List[Match])
def get_job_matches(
    job_id: str,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    _: str = Depends(get_current_recruiter)
):
    """Récupérer tous les matches d'une offre d'emploi"""
    return MatchCRUD.get_by_job_id(job_id, min_score=min_score)

@router.get("/{match_id}", response_model=Match)
def get_match(
    match_id: str, 
    _: str = Depends(get_current_recruiter)
):
    """Récupérer un match par ID"""
    return MatchCRUD.get_by_id(match_id)

@router.patch("/{match_id}", response_model=Match)
def update_match(
    match_id: str,
    match_update: MatchUpdate,
    _: str = Depends(get_current_recruiter)
):
    """Mettre à jour partiellement un match"""
    return MatchCRUD.update(match_id, match_update)

@router.put("/{match_id}/status", response_model=Match)
def update_match_status(
    match_id: str,
    status: str = Body(..., embed=True),
    recruiter_notes: Optional[str] = Body(None, embed=True),
    _: str = Depends(get_current_recruiter)
):
    """Mettre à jour le statut d'un match (pending, reviewed, accepted, rejected)"""
    return MatchCRUD.update_status(match_id, status, recruiter_notes)

@router.delete("/{match_id}")
def delete_match(
    match_id: str, 
    _: str = Depends(get_current_recruiter)
):
    """Supprimer un match"""
    success = MatchCRUD.delete(match_id)
    if not success:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    return {"message": "Match supprimé"}