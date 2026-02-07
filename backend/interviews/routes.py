from fastapi import APIRouter, Depends, Query, HTTPException
from backend.interviews.models import (
    JobPosition, JobPositionCreate,
    InterviewSession, InterviewSessionCreate
)
from backend.interviews.crud import JobPositionCRUD, InterviewSessionCRUD
from backend.auth.security import get_current_recruiter
from typing import List, Optional

router = APIRouter(prefix="/interviews", tags=["Interviews"])

# ============ Job Positions Routes ============

@router.post("/positions", response_model=JobPosition)
def create_job_position(
    position: JobPositionCreate,
    _: str = Depends(get_current_recruiter)
):
    """Créer un nouveau poste avec questions prédéfinies"""
    return JobPositionCRUD.create(position)

@router.get("/positions", response_model=List[JobPosition])
def list_job_positions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: str = Depends(get_current_recruiter)
):
    """Lister tous les postes avec leurs questions"""
    return JobPositionCRUD.get_all(skip=skip, limit=limit)

@router.get("/positions/{position_id}", response_model=JobPosition)
def get_job_position(
    position_id: str,
    _: str = Depends(get_current_recruiter)
):
    """Récupérer un poste par ID"""
    return JobPositionCRUD.get_by_id(position_id)

@router.delete("/positions/{position_id}")
def delete_job_position(
    position_id: str,
    _: str = Depends(get_current_recruiter)
):
    """Supprimer un poste"""
    success = JobPositionCRUD.delete(position_id)
    if not success:
        raise HTTPException(status_code=404, detail="Poste non trouvé")
    return {"message": "Poste supprimé"}

# ============ Interview Sessions Routes ============

@router.post("/sessions", response_model=InterviewSession)
def create_interview_session(
    session: InterviewSessionCreate,
    _: str = Depends(get_current_recruiter)
):
    """Créer une nouvelle session d'entretien pour un candidat"""
    return InterviewSessionCRUD.create(session)

@router.get("/sessions", response_model=List[InterviewSession])
def list_interview_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    _: str = Depends(get_current_recruiter)
):
    """Lister toutes les sessions d'entretien"""
    return InterviewSessionCRUD.get_all(skip=skip, limit=limit, status=status)

@router.get("/sessions/{session_id}", response_model=InterviewSession)
def get_interview_session(
    session_id: str,
    _: str = Depends(get_current_recruiter)
):
    """
    Récupérer une session d'entretien par ID
    Accepte soit le session_id (ex: session_abc123) soit l'ID MongoDB
    """
    return InterviewSessionCRUD.get_by_id(session_id)

@router.get("/sessions/candidate/{candidate_id}", response_model=List[InterviewSession])
def get_candidate_sessions(
    candidate_id: str,
    _: str = Depends(get_current_recruiter)
):
    """Récupérer toutes les sessions d'un candidat"""
    return InterviewSessionCRUD.get_by_candidate_id(candidate_id)

@router.patch("/sessions/{session_id}/status")
def update_session_status(
    session_id: str,
    status: str = Query(..., description="Nouveau statut"),
    _: str = Depends(get_current_recruiter)
):
    """Mettre à jour le statut d'une session"""
    return InterviewSessionCRUD.update_status(session_id, status)

@router.delete("/sessions/{session_id}")
def delete_interview_session(
    session_id: str,
    _: str = Depends(get_current_recruiter)
):
    """Supprimer une session d'entretien"""
    success = InterviewSessionCRUD.delete(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return {"message": "Session supprimée"}