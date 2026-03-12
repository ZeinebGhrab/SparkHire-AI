from fastapi import APIRouter, Depends, Query
from backend.analytics.models import (
    CandidateStats, InterviewStats,
    SystemStats, DashboardStats
)
from backend.auth.security import get_current_recruiter
from backend.database import db
from datetime import datetime, timedelta
from collections import Counter

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/candidates", response_model=CandidateStats)
async def get_candidate_statistics(
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_recruiter)
):
    """Statistiques des candidats"""
    start_date = datetime.utcnow() - timedelta(days=days)

    total_candidates  = db.candidates.count_documents({})
    recent_candidates = db.candidates.count_documents({"created_at": {"$gte": start_date}})

    all_skills = []
    for candidate in db.candidates.find({}, {"technical_skills": 1}):
        for ts in candidate.get("technical_skills", []):
            name = ts.get("name") if isinstance(ts, dict) else ts
            if name:
                all_skills.append(name)

    skill_counts = Counter(all_skills)
    top_skills   = [{"skill": s, "count": c} for s, c in skill_counts.most_common(10)]

    return CandidateStats(
        total_candidates=total_candidates,
        candidates_by_status={"active": total_candidates},
        candidates_by_skill=dict(skill_counts),
        recent_candidates=recent_candidates,
        top_skills=top_skills,
    )


@router.get("/interviews", response_model=InterviewStats)
async def get_interview_statistics(
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_recruiter)
):
    """Statistiques des entretiens"""
    start_date = datetime.utcnow() - timedelta(days=days)

    total_interviews = db.interview_sessions.count_documents(
        {"created_at": {"$gte": start_date}}
    )

    status_results = list(db.interview_sessions.aggregate([
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]))
    interviews_by_status = {r["_id"]: r["count"] for r in status_results}

    position_results = list(db.interview_sessions.aggregate([
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {"_id": "$job_position_id", "count": {"$sum": 1}}},
    ]))
    interviews_by_position = {r["_id"]: r["count"] for r in position_results}

    completed_sessions = list(db.interview_sessions.find({
        "status": "completed",
        "started_at":   {"$exists": True},
        "completed_at": {"$exists": True},
    }))
    if completed_sessions:
        durations = [
            (s["completed_at"] - s["started_at"]).total_seconds() / 60
            for s in completed_sessions
        ]
        average_duration = sum(durations) / len(durations)
    else:
        average_duration = 0.0

    completed_count = interviews_by_status.get("completed", 0)
    completion_rate = (completed_count / total_interviews * 100) if total_interviews > 0 else 0.0

    total_questions = sum(
        len(s.get("answers", []))
        for s in db.interview_sessions.find({}, {"answers": 1})
    )
    avg_questions = total_questions / total_interviews if total_interviews > 0 else 0.0

    # Score moyen sur toutes les évaluations
    scores = []
    for session in db.interview_sessions.find({}, {"answers": 1}):
        for answer in session.get("answers", []):
            ev = answer.get("evaluation")
            if ev and ev.get("score") is not None:
                scores.append(float(ev["score"]))
    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    return InterviewStats(
        total_interviews=total_interviews,
        interviews_by_status=interviews_by_status,
        interviews_by_position=interviews_by_position,
        average_duration_minutes=round(average_duration, 2),
        completion_rate=round(completion_rate, 2),
        total_questions_answered=total_questions,
        average_questions_per_interview=round(avg_questions, 2),
        average_score=average_score,
    )


@router.get("/system", response_model=SystemStats)
async def get_system_statistics(
    _: str = Depends(get_current_recruiter)
):
    """Statistiques système"""
    from backend.config import settings

    total_recruiters    = db.recruiters.count_documents({})
    total_job_positions = db.job_positions.count_documents({})
    active_sessions     = db.interview_sessions.count_documents({"status": "in_progress"})

    storage_used_mb = 0.0
    if settings.UPLOAD_DIR.exists():
        total_size = sum(
            f.stat().st_size for f in settings.UPLOAD_DIR.rglob("*") if f.is_file()
        )
        storage_used_mb = total_size / (1024 * 1024)

    return SystemStats(
        total_recruiters=total_recruiters,
        total_job_positions=total_job_positions,
        active_sessions=active_sessions,
        storage_used_mb=round(storage_used_mb, 2),
        api_calls_today=0,
    )


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_statistics(
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_recruiter)
):
    """Toutes les statistiques pour le dashboard"""
    end_date   = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    candidates_stats = await get_candidate_statistics(days, _)
    interviews_stats = await get_interview_statistics(days, _)
    system_stats     = await get_system_statistics(_)

    return DashboardStats(
        candidates=candidates_stats,
        interviews=interviews_stats,
        system=system_stats,
        period_start=start_date,
        period_end=end_date,
    )