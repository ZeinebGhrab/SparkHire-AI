from fastapi import APIRouter, Depends, Query, HTTPException
from backend.interviews.models import (
    JobPosition, JobPositionCreate,
    InterviewSession, InterviewSessionCreate,
    AnswerWithEvalResponse, AnswersSummaryResponse,
)
from backend.interviews.crud import JobPositionCRUD, InterviewSessionCRUD
from backend.auth.security import get_current_recruiter
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/interviews", tags=["Interviews"])

# ============ Job Positions ============

@router.post("/positions", response_model=JobPosition)
def create_job_position(
    position: JobPositionCreate,
    _: str = Depends(get_current_recruiter),
):
    """Créer un nouveau poste avec questions prédéfinies"""
    return JobPositionCRUD.create(position)

@router.get("/positions", response_model=List[JobPosition])
def list_job_positions(
    skip:        int            = Query(0,    ge=0),
    limit:       int            = Query(100,  ge=1, le=500),
    department:  Optional[str]  = Query(None, description="Filter by department"),
    location:    Optional[str]  = Query(None, description="Filter by city / location"),
    is_active:   Optional[bool] = Query(None, description="True=active, False=archived, None=all"),
    period_days: Optional[int]  = Query(None, ge=1, description="Positions created in the last N days"),
    sort_by:     str            = Query("created_at", description="Sort field: created_at | title | department"),
    order:       str            = Query("desc", description="asc | desc"),
    _: str = Depends(get_current_recruiter),
):
    """List job positions with filters: department, location, period, sort order"""
    return JobPositionCRUD.get_all(
        skip=skip, limit=limit,
        department=department, location=location,
        is_active=is_active, period_days=period_days,
        sort_by=sort_by, order=order,
    )


@router.get("/positions/meta/departments", response_model=List[str])
def list_departments(_: str = Depends(get_current_recruiter)):
    """Distinct list of all departments (for filter dropdown)"""
    return JobPositionCRUD.get_distinct_departments()


@router.get("/positions/meta/locations", response_model=List[str])
def list_locations(_: str = Depends(get_current_recruiter)):
    """Distinct list of all locations (for filter dropdown)"""
    return JobPositionCRUD.get_distinct_locations()

@router.get("/positions/{position_id}", response_model=JobPosition)
def get_job_position(
    position_id: str,
    _: str = Depends(get_current_recruiter),
):
    return JobPositionCRUD.get_by_id(position_id)

@router.delete("/positions/{position_id}")
def delete_job_position(
    position_id: str,
    _: str = Depends(get_current_recruiter),
):
    success = JobPositionCRUD.delete(position_id)
    if not success:
        raise HTTPException(status_code=404, detail="Poste non trouvé")
    return {"message": "Poste supprimé"}

# ============ Interview Sessions ============

@router.post("/sessions", response_model=InterviewSession)
def create_interview_session(
    session: InterviewSessionCreate,
    _: str = Depends(get_current_recruiter),
):
    """Créer une nouvelle session d'entretien pour un candidat"""
    return InterviewSessionCRUD.create(session)

@router.get("/sessions", response_model=List[InterviewSession])
def list_interview_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None),
    _: str = Depends(get_current_recruiter),
):
    return InterviewSessionCRUD.get_all(skip=skip, limit=limit, status=status)

@router.get("/sessions/{session_id}", response_model=InterviewSession)
def get_interview_session(
    session_id: str,
    _: str = Depends(get_current_recruiter),
):
    """
    Session complète avec answers[n].evaluation inclus.
    Accepte session_id (ex: session_abc123) ou l'_id MongoDB.
    """
    return InterviewSessionCRUD.get_by_id(session_id)

@router.get(
    "/sessions/{session_id}/answers",
    response_model=List[AnswerWithEvalResponse],
    summary="Réponses + évaluations LLM d'une session",
)
def get_session_answers(
    session_id: str,
    _: str = Depends(get_current_recruiter),
):
    """
    Retourne toutes les réponses de la session avec :
    - transcript (Whisper ASR)
    - score, verdict, feedback, strengths, improvements (LLM)
    - evaluated=False si l'évaluation est encore en cours

    Structure MongoDB lue :
      interview_sessions.answers[n].transcript
      interview_sessions.answers[n].evaluation.score
      ...
    """
    answers = InterviewSessionCRUD.get_answers_with_evaluations(session_id)
    return [AnswerWithEvalResponse.from_answer(a) for a in answers]

@router.get(
    "/sessions/{session_id}/answers/summary",
    response_model=AnswersSummaryResponse,
    summary="Résumé des scores d'évaluation d'une session",
)
def get_session_answers_summary(
    session_id: str,
    _: str = Depends(get_current_recruiter),
):
    """
    Résumé rapide :
    - Nombre de réponses / évaluées
    - Score moyen
    - Tableau question par question
    """
    answers = InterviewSessionCRUD.get_answers_with_evaluations(session_id)
    items = [AnswerWithEvalResponse.from_answer(a) for a in answers]

    evaluated = [a for a in items if a.evaluated]
    avg_score: Optional[float] = None
    if evaluated:
        avg_score = round(sum(a.score for a in evaluated if a.score is not None) / len(evaluated), 2)

    return AnswersSummaryResponse(
        session_id=session_id,
        total_answers=len(items),
        evaluated_count=len(evaluated),
        average_score=avg_score,
        answers=items,
    )

@router.get("/sessions/candidate/{candidate_id}", response_model=List[InterviewSession])
def get_candidate_sessions(
    candidate_id: str,
    _: str = Depends(get_current_recruiter),
):
    return InterviewSessionCRUD.get_by_candidate_id(candidate_id)

@router.patch("/sessions/{session_id}/status")
def update_session_status(
    session_id: str,
    status: str = Query(...),
    _: str = Depends(get_current_recruiter),
):
    return InterviewSessionCRUD.update_status(session_id, status)

@router.delete("/sessions/{session_id}")
def delete_interview_session(
    session_id: str,
    _: str = Depends(get_current_recruiter),
):
    success = InterviewSessionCRUD.delete(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return {"message": "Session supprimée"}

@router.patch("/sessions/{session_id}/schedule")
def schedule_interview(
    session_id: str,
    scheduled_at: datetime = Query(..., description="Date et heure planifiée (ISO 8601, UTC)"),
    _: str = Depends(get_current_recruiter),
):
    """
    Planifier ou replanifier un entretien.

    - Définit scheduled_at sur la session
    - Recalcule late_access_deadline = scheduled_at + 30 min
    - Recalcule expires_at = late_access_deadline
    - La session redevient 'pending' si elle était cancelled
    """
    return InterviewSessionCRUD.reschedule(session_id, scheduled_at)