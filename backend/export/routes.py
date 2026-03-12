from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.auth.security import get_current_recruiter
from backend.database import db
from datetime import datetime
import csv
import io
import json

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/candidates/csv")
async def export_candidates_csv(_: str = Depends(get_current_recruiter)):
    """Exporter tous les candidats en CSV"""
    candidates = list(db.candidates.find({}))
    if not candidates:
        raise HTTPException(status_code=404, detail="Aucun candidat à exporter")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Prénom", "Nom", "Email", "Téléphone", "Compétences", "Date de création"])

    for c in candidates:
        writer.writerow([
            str(c["_id"]),
            c.get("first_name", ""),
            c.get("last_name", ""),
            c.get("contact", {}).get("email", ""),
            c.get("contact", {}).get("phone", ""),
            ", ".join(c.get("skills", [])),
            c.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if c.get("created_at") else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"},
    )


@router.get("/interviews/csv")
async def export_interviews_csv(_: str = Depends(get_current_recruiter)):
    """Exporter toutes les sessions d'entretien en CSV"""
    sessions = list(db.interview_sessions.find({}))
    if not sessions:
        raise HTTPException(status_code=404, detail="Aucune session à exporter")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Session ID", "Candidat ID", "Poste ID", "Statut", "Langue",
        "Questions posées", "Réponses", "Score moyen", "Date de création",
    ])

    for s in sessions:
        answers = s.get("answers", [])
        scores  = [
            float(a["evaluation"]["score"])
            for a in answers
            if a.get("evaluation") and a["evaluation"].get("score") is not None
        ]
        avg_score = round(sum(scores) / len(scores), 2) if scores else ""

        writer.writerow([
            s.get("session_id", ""),
            s.get("candidate_id", ""),
            s.get("job_position_id", ""),
            s.get("status", ""),
            s.get("language", ""),
            s.get("current_question_index", 0),
            len(answers),
            avg_score,
            s.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if s.get("created_at") else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=interviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"},
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

    candidate = db.candidates.find_one({"_id": session.get("candidate_id")})
    position  = db.job_positions.find_one({"_id": session.get("job_position_id")})

    answers = session.get("answers", [])
    scores  = [
        float(a["evaluation"]["score"])
        for a in answers
        if a.get("evaluation") and a["evaluation"].get("score") is not None
    ]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    export_data = {
        "session": {
            "session_id":   session.get("session_id"),
            "status":       session.get("status"),
            "language":     session.get("language"),
            "average_score": avg_score,
            "created_at":   session.get("created_at").isoformat()   if session.get("created_at")   else None,
            "started_at":   session.get("started_at").isoformat()   if session.get("started_at")   else None,
            "completed_at": session.get("completed_at").isoformat() if session.get("completed_at") else None,
        },
        "candidate": {
            "id":         str(candidate["_id"]) if candidate else None,
            "first_name": candidate.get("first_name") if candidate else None,
            "last_name":  candidate.get("last_name")  if candidate else None,
            "email":      candidate.get("contact", {}).get("email") if candidate else None,
        },
        "position": {
            "id":         str(position["_id"])          if position else None,
            "title":      position.get("title")         if position else None,
            "department": position.get("department")    if position else None,
        },
        "answers": answers,
    }

    json_data = json.dumps(export_data, indent=2, default=str)
    return StreamingResponse(
        iter([json_data]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=interview_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"},
    )


@router.get("/evaluations/csv")
async def export_evaluations_csv(_: str = Depends(get_current_recruiter)):
    """Exporter toutes les évaluations LLM en CSV"""
    sessions = list(db.interview_sessions.find({}))
    if not sessions:
        raise HTTPException(status_code=404, detail="Aucune session à exporter")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Session ID", "Candidat ID", "Poste ID", "Langue",
        "Q. Ordre", "Question", "Transcript", "Score", "Verdict", "Feedback",
    ])

    for s in sessions:
        for answer in s.get("answers", []):
            ev = answer.get("evaluation") or {}
            writer.writerow([
                s.get("session_id", ""),
                s.get("candidate_id", ""),
                s.get("job_position_id", ""),
                s.get("language", ""),
                answer.get("question_order", ""),
                answer.get("question_text", ""),
                answer.get("transcript", ""),
                ev.get("score", ""),
                ev.get("verdict", ""),
                ev.get("feedback", ""),
            ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"},
    )