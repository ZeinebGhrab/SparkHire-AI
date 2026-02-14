from fastapi import APIRouter, Depends, Query
from backend.analytics.models import (
    CandidateStats, InterviewStats, MatchStats, 
    SystemStats, DashboardStats
)
from backend.auth.security import get_current_recruiter
from backend.database import db
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/candidates", response_model=CandidateStats)
async def get_candidate_statistics(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours pour les statistiques"),
    _: str = Depends(get_current_recruiter)
):
    """Obtenir les statistiques des candidats"""
    
    # Date de début
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total candidats
    total_candidates = db.candidates.count_documents({})
    
    # Candidats récents
    recent_candidates = db.candidates.count_documents({
        "created_at": {"$gte": start_date}
    })
    
    # Compétences
    all_skills = []
    for candidate in db.candidates.find({}, {"skills": 1}):
        all_skills.extend(candidate.get("skills", []))
    
    skill_counts = Counter(all_skills)
    top_skills = [{"skill": skill, "count": count} 
                  for skill, count in skill_counts.most_common(10)]
    
    return CandidateStats(
        total_candidates=total_candidates,
        candidates_by_status={"active": total_candidates},
        candidates_by_skill=dict(skill_counts),
        recent_candidates=recent_candidates,
        top_skills=top_skills
    )

@router.get("/interviews", response_model=InterviewStats)
async def get_interview_statistics(
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_recruiter)
):
    """Obtenir les statistiques des entretiens"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total entretiens
    total_interviews = db.interview_sessions.count_documents({
        "created_at": {"$gte": start_date}
    })
    
    # Statuts
    status_pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_results = list(db.interview_sessions.aggregate(status_pipeline))
    interviews_by_status = {item["_id"]: item["count"] for item in status_results}
    
    # Positions
    position_pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {"_id": "$job_position_id", "count": {"$sum": 1}}}
    ]
    position_results = list(db.interview_sessions.aggregate(position_pipeline))
    interviews_by_position = {item["_id"]: item["count"] for item in position_results}
    
    # Durée moyenne
    completed_sessions = list(db.interview_sessions.find({
        "status": "completed",
        "started_at": {"$exists": True},
        "completed_at": {"$exists": True}
    }))
    
    if completed_sessions:
        durations = [
            (session["completed_at"] - session["started_at"]).total_seconds() / 60
            for session in completed_sessions
        ]
        average_duration = sum(durations) / len(durations)
    else:
        average_duration = 0.0
    
    # Taux de complétion
    completed_count = interviews_by_status.get("completed", 0)
    completion_rate = (completed_count / total_interviews * 100) if total_interviews > 0 else 0.0
    
    # Questions répondues
    total_questions = sum(len(session.get("answers", [])) 
                         for session in db.interview_sessions.find({}, {"answers": 1}))
    
    avg_questions = total_questions / total_interviews if total_interviews > 0 else 0.0
    
    return InterviewStats(
        total_interviews=total_interviews,
        interviews_by_status=interviews_by_status,
        interviews_by_position=interviews_by_position,
        average_duration_minutes=round(average_duration, 2),
        completion_rate=round(completion_rate, 2),
        total_questions_answered=total_questions,
        average_questions_per_interview=round(avg_questions, 2)
    )

@router.get("/matches", response_model=MatchStats)
async def get_match_statistics(
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_recruiter)
):
    """Obtenir les statistiques des matches"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total matches
    total_matches = db.matches.count_documents({
        "created_at": {"$gte": start_date}
    })
    
    # Statuts
    status_pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_results = list(db.matches.aggregate(status_pipeline))
    matches_by_status = {item["_id"]: item["count"] for item in status_results}
    
    # Score moyen
    all_matches = list(db.matches.find(
        {"created_at": {"$gte": start_date}},
        {"score": 1}
    ))
    
    if all_matches:
        average_score = sum(m.get("score", 0) for m in all_matches) / len(all_matches)
    else:
        average_score = 0.0
    
    # Top positions matchées
    position_pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": "$job_id",
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$score"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_positions = list(db.matches.aggregate(position_pipeline))
    top_matched_positions = [
        {
            "job_id": item["_id"],
            "match_count": item["count"],
            "average_score": round(item["avg_score"], 3)
        }
        for item in top_positions
    ]
    
    # Matches au-dessus du seuil (0.7)
    matches_above_threshold = db.matches.count_documents({
        "created_at": {"$gte": start_date},
        "score": {"$gte": 0.7}
    })
    
    return MatchStats(
        total_matches=total_matches,
        matches_by_status=matches_by_status,
        average_match_score=round(average_score, 3),
        top_matched_positions=top_matched_positions,
        matches_above_threshold=matches_above_threshold
    )

@router.get("/system", response_model=SystemStats)
async def get_system_statistics(
    _: str = Depends(get_current_recruiter)
):
    """Obtenir les statistiques système"""
    
    total_recruiters = db.recruiters.count_documents({})
    total_job_positions = db.job_positions.count_documents({})
    active_sessions = db.interview_sessions.count_documents({
        "status": "in_progress"
    })
    
    # Calcul de l'espace de stockage (simplifié)
    from backend.config import settings
    storage_used_mb = 0.0
    
    if settings.UPLOAD_DIR.exists():
        total_size = sum(f.stat().st_size for f in settings.UPLOAD_DIR.rglob('*') if f.is_file())
        storage_used_mb = total_size / (1024 * 1024)
    
    return SystemStats(
        total_recruiters=total_recruiters,
        total_job_positions=total_job_positions,
        active_sessions=active_sessions,
        storage_used_mb=round(storage_used_mb, 2),
        api_calls_today=0  # À implémenter avec un système de logs
    )

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_statistics(
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_recruiter)
):
    """Obtenir toutes les statistiques pour le dashboard"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    candidates_stats = await get_candidate_statistics(days, _)
    interviews_stats = await get_interview_statistics(days, _)
    matches_stats = await get_match_statistics(days, _)
    system_stats = await get_system_statistics(_)
    
    return DashboardStats(
        candidates=candidates_stats,
        interviews=interviews_stats,
        matches=matches_stats,
        system=system_stats,
        period_start=start_date,
        period_end=end_date
    )