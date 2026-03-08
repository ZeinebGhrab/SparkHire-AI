"""
Routes API pour l'évaluation LLM des entretiens.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from backend.auth.security import get_current_recruiter
from backend.evaluation.models import (
    GlobalEvaluation, EvaluationRequest, EvaluationSummaryResponse
)
from backend.database import db
from typing import List

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


def _get_eval_service():
    """Récupère le service d'évaluation depuis les singletons."""
    from backend.websocket import interview_handler as ih
    from backend.services.llm_service import get_llm_service
    from backend.evaluation.service import EvaluationService
    return EvaluationService(
        llm_service=get_llm_service(),
        asr_service=ih._asr_service,
    )


@router.post("/trigger", response_model=dict)
async def trigger_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(get_current_recruiter),
):
    """
    Déclenche une évaluation LLM complète d'une session d'entretien.
    L'évaluation tourne en arrière-plan pour ne pas bloquer la réponse API.
    """
    session = db.interview_sessions.find_one({"session_id": request.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    if session.get("status") not in ("completed", "in_progress"):
        raise HTTPException(
            status_code=400,
            detail="L'évaluation n'est disponible que pour les sessions terminées ou en cours"
        )

    eval_service = _get_eval_service()

    async def _run():
        await eval_service.evaluate_full_session(
            request.session_id,
            language=request.language,
        )

    background_tasks.add_task(_run)

    return {
        "message": "Évaluation lancée en arrière-plan",
        "session_id": request.session_id,
        "status": "processing",
    }


@router.get("/{session_id}", response_model=GlobalEvaluation)
async def get_evaluation(
    session_id: str,
    _: str = Depends(get_current_recruiter),
):
    """Récupère l'évaluation d'une session (si disponible)."""
    doc = db.evaluations.find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Évaluation non trouvée. Déclenchez-la d'abord via POST /evaluations/trigger"
        )
    doc.pop("_id", None)
    return GlobalEvaluation(**doc)


@router.get("/", response_model=List[EvaluationSummaryResponse])
async def list_evaluations(
    skip: int = 0,
    limit: int = 50,
    _: str = Depends(get_current_recruiter),
):
    """Liste toutes les évaluations disponibles (résumé)."""
    docs = list(
        db.evaluations.find({}, {
            "session_id": 1, "candidate_name": 1, "position_title": 1,
            "average_score": 1, "global_score": 1, "global_verdict": 1,
            "recommendation": 1, "evaluated_at": 1
        })
        .sort("evaluated_at", -1)
        .skip(skip)
        .limit(limit)
    )
    for d in docs:
        d.pop("_id", None)
    return [EvaluationSummaryResponse(**d) for d in docs]


@router.delete("/{session_id}")
async def delete_evaluation(
    session_id: str,
    _: str = Depends(get_current_recruiter),
):
    """Supprime une évaluation."""
    result = db.evaluations.delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Évaluation introuvable")
    return {"message": "Évaluation supprimée"}


@router.get("/health/llm")
async def llm_health(_: str = Depends(get_current_recruiter)):
    """Vérifie que le service Ollama est disponible."""
    from backend.services.llm_service import get_llm_service
    svc = get_llm_service()
    available = await svc.is_available()
    return {
        "ollama_available": available,
        "model": svc.model,
        "base_url": svc.base_url,
    }