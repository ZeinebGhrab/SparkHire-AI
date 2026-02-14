from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from backend.auth.security import get_current_recruiter
from backend.database import db
from datetime import datetime
import csv
import io
import json

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/candidates/csv")
async def export_candidates_csv(
    _: str = Depends(get_current_recruiter)
):
    """Exporter tous les candidats en CSV"""
    
    candidates = list(db.candidates.find({}))
    
    if not candidates:
        raise HTTPException(status_code=404, detail="Aucun candidat à exporter")
    
    # Créer le CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        "ID", "Prénom", "Nom", "Email", "Téléphone",
        "Compétences", "Date de création"
    ])
    
    # Données
    for candidate in candidates:
        writer.writerow([
            str(candidate["_id"]),
            candidate.get("first_name", ""),
            candidate.get("last_name", ""),
            candidate.get("contact", {}).get("email", ""),
            candidate.get("contact", {}).get("phone", ""),
            ", ".join(candidate.get("skills", [])),
            candidate.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if candidate.get("created_at") else ""
        ])
    
    # Retourner le CSV
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.get("/interviews/csv")
async def export_interviews_csv(
    _: str = Depends(get_current_recruiter)
):
    """Exporter toutes les sessions d'entretien en CSV"""
    
    sessions = list(db.interview_sessions.find({}))
    
    if not sessions:
        raise HTTPException(status_code=404, detail="Aucune session à exporter")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        "Session ID", "Candidat ID", "Poste ID", "Statut",
        "Langue", "Questions posées", "Réponses", "Date de création"
    ])
    
    # Données
    for session in sessions:
        writer.writerow([
            session.get("session_id", ""),
            session.get("candidate_id", ""),
            session.get("job_position_id", ""),
            session.get("status", ""),
            session.get("language", ""),
            session.get("current_question_index", 0),
            len(session.get("answers", [])),
            session.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if session.get("created_at") else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=interviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.get("/matches/csv")
async def export_matches_csv(
    _: str = Depends(get_current_recruiter)
):
    """Exporter tous les matches en CSV"""
    
    matches = list(db.matches.find({}))
    
    if not matches:
        raise HTTPException(status_code=404, detail="Aucun match à exporter")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow([
        "ID", "Candidat ID", "Job ID", "Score",
        "Statut", "Notes", "Date de création"
    ])
    
    # Données
    for match in matches:
        writer.writerow([
            str(match["_id"]),
            match.get("candidate_id", ""),
            match.get("job_id", ""),
            match.get("score", 0),
            match.get("status", ""),
            match.get("recruiter_notes", ""),
            match.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if match.get("created_at") else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.get("/interviews/{session_id}/json")
async def export_interview_details_json(
    session_id: str,
    _: str = Depends(get_current_recruiter)
):
    """Exporter les détails complets d'un entretien en JSON"""
    
    session = db.interview_sessions.find_one({"session_id": session_id})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    # Récupérer le candidat
    candidate = db.candidates.find_one({"_id": session.get("candidate_id")})
    
    # Récupérer le poste
    position = db.job_positions.find_one({"_id": session.get("job_position_id")})
    
    # Préparer les données
    export_data = {
        "session": {
            "session_id": session.get("session_id"),
            "status": session.get("status"),
            "language": session.get("language"),
            "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
            "started_at": session.get("started_at").isoformat() if session.get("started_at") else None,
            "completed_at": session.get("completed_at").isoformat() if session.get("completed_at") else None
        },
        "candidate": {
            "id": str(candidate["_id"]) if candidate else None,
            "first_name": candidate.get("first_name") if candidate else None,
            "last_name": candidate.get("last_name") if candidate else None,
            "email": candidate.get("contact", {}).get("email") if candidate else None
        },
        "position": {
            "id": str(position["_id"]) if position else None,
            "title": position.get("title") if position else None,
            "department": position.get("department") if position else None
        },
        "answers": session.get("answers", [])
    }
    
    # Convertir en JSON
    json_data = json.dumps(export_data, indent=2, default=str)
    
    return StreamingResponse(
        iter([json_data]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=interview_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )