from fastapi import APIRouter, Depends, Query
from backend.analytics.models import (
    CandidateStats, InterviewStats,
    SystemStats, DashboardStats, SchedulingStats,
    ScoreStats, MonthlyTrend, StatusDistribution, ScoreBucket, DepartmentPerformance
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


@router.get("/scheduling", response_model=SchedulingStats)
async def get_scheduling_statistics(
    _: str = Depends(get_current_recruiter)
):
    """
    Statistiques de planification des entretiens.
    Retourne les compteurs affichés dans le widget calendrier :
      - Total planifiés, Cette semaine, Confirmés, En attente, Annulés
      - Répartition par jour de la semaine courante
      - Répartition par poste et par langue
      - Entretiens dont expires_at tombe dans les 7 prochains jours
    """
    now   = datetime.utcnow()

    # Semaine courante : lundi 00:00 → dimanche 23:59
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end   = week_start + timedelta(days=7)

    # ── Compteurs principaux ──────────────────────────────────────────────────
    total_scheduled = db.interview_sessions.count_documents(
        {"status": {"$ne": "cancelled"}}
    )

    this_week = db.interview_sessions.count_documents({
        "created_at": {"$gte": week_start, "$lt": week_end},
        "status": {"$ne": "cancelled"},
    })

    confirmed = db.interview_sessions.count_documents({
        "status": {"$in": ["completed", "in_progress"]}
    })

    pending = db.interview_sessions.count_documents({"status": "pending"})

    cancelled = db.interview_sessions.count_documents({"status": "cancelled"})

    # ── Répartition par jour de la semaine courante ───────────────────────────
    day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    by_day: dict = {d: 0 for d in day_names}

    sessions_this_week = db.interview_sessions.find(
        {
            "created_at": {"$gte": week_start, "$lt": week_end},
            "status": {"$ne": "cancelled"},
        },
        {"created_at": 1},
    )
    for s in sessions_this_week:
        dow = s["created_at"].weekday()   # 0=lundi … 6=dimanche
        by_day[day_names[dow]] += 1

    # ── Répartition par poste (top 10) ────────────────────────────────────────
    pos_pipeline = [
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {"_id": "$job_position_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    pos_results = list(db.interview_sessions.aggregate(pos_pipeline))

    # Résoudre les IDs → titres de poste
    from bson import ObjectId
    by_position: dict = {}
    for r in pos_results:
        pid = r["_id"]
        try:
            pos = db.job_positions.find_one({"_id": ObjectId(pid)}, {"title": 1})
            label = pos["title"] if pos else pid
        except Exception:
            label = pid
        by_position[label] = r["count"]

    # ── Répartition par langue ────────────────────────────────────────────────
    lang_pipeline = [
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
    ]
    lang_results  = list(db.interview_sessions.aggregate(lang_pipeline))
    by_language   = {"ar": 0, "fr": 0, "en": 0}
    for r in lang_results:
        lang = r["_id"] or "ar"
        by_language[lang] = r["count"]

    # ── Entretiens expirant dans les 7 prochains jours ────────────────────────
    upcoming_7_days = db.interview_sessions.count_documents({
        "status": "pending",
        "expires_at": {"$gte": now, "$lt": now + timedelta(days=7)},
    })

    return SchedulingStats(
        total_scheduled=total_scheduled,
        this_week=this_week,
        confirmed=confirmed,
        pending=pending,
        cancelled=cancelled,
        by_day_this_week=by_day,
        by_position=by_position,
        by_language=by_language,
        upcoming_7_days=upcoming_7_days,
    )


@router.get("/scores", response_model=ScoreStats)
async def get_score_statistics(
    _: str = Depends(get_current_recruiter)
):
    """
    Statistiques scores & candidatures pour le dashboard :
    - KPI cards : acceptés / refusés / en entretien / en attente + variation mensuelle
    - Tendance des candidatures sur 6 mois
    - Répartition des statuts (camembert)
    - Distribution des scores 0-100 (histogramme)
    - Performance par département
    """
    from bson import ObjectId
    now = datetime.utcnow()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _avg_score(session: dict) -> float | None:
        scores = [
            float(a["evaluation"]["score"])
            for a in session.get("answers", [])
            if a.get("evaluation") and a["evaluation"].get("score") is not None
        ]
        return round(sum(scores) / len(scores), 2) if scores else None

    def _month_range(months_ago: int):
        """Retourne (start, end) pour le mois N mois en arrière."""
        d = now - timedelta(days=30 * months_ago)
        start = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end

    # ── KPI : compteurs current month ─────────────────────────────────────────
    month_start, month_end = _month_range(0)
    prev_start,  prev_end  = _month_range(1)

    def _count_kpi(status_filter: dict, date_range: tuple) -> int:
        q = {"created_at": {"$gte": date_range[0], "$lt": date_range[1]}}
        q.update(status_filter)
        return db.interview_sessions.count_documents(q)

    def _pct_change(curr: int, prev: int) -> float:
        if prev == 0:
            return 100.0 if curr > 0 else 0.0
        return round((curr - prev) / prev * 100, 1)

    # Acceptés = completed avec score_moyen >= 7
    all_completed = list(db.interview_sessions.find(
        {"status": "completed"}, {"answers": 1, "created_at": 1}
    ))
    accepted_curr = sum(
        1 for s in all_completed
        if month_start <= s.get("created_at", now) < month_end
        and (_avg_score(s) or 0) >= 7
    )
    accepted_prev = sum(
        1 for s in all_completed
        if prev_start <= s.get("created_at", now) < prev_end
        and (_avg_score(s) or 0) >= 7
    )

    # Refusés = completed avec score_moyen < 5
    rejected_curr = sum(
        1 for s in all_completed
        if month_start <= s.get("created_at", now) < month_end
        and (_avg_score(s) or 0) < 5
    )
    rejected_prev = sum(
        1 for s in all_completed
        if prev_start <= s.get("created_at", now) < prev_end
        and (_avg_score(s) or 0) < 5
    )

    # En entretien = in_progress
    in_interview_curr = _count_kpi({"status": "in_progress"}, (month_start, month_end))
    in_interview_prev = _count_kpi({"status": "in_progress"}, (prev_start, prev_end))

    # En attente = pending
    pending_total = db.interview_sessions.count_documents({"status": "pending"})

    # ── Tendance 6 mois ───────────────────────────────────────────────────────
    FR_MONTHS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                 "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    monthly_trend = []
    for i in range(5, -1, -1):   # 5 mois en arrière → mois courant
        ms, me = _month_range(i)
        label  = FR_MONTHS[ms.month - 1]

        sessions_m = list(db.interview_sessions.find(
            {"created_at": {"$gte": ms, "$lt": me}},
            {"status": 1, "answers": 1}
        ))
        applications = len(sessions_m)
        interviews   = sum(1 for s in sessions_m if s.get("status") in ("in_progress", "completed"))
        hires        = sum(
            1 for s in sessions_m
            if s.get("status") == "completed" and (_avg_score(s) or 0) >= 7
        )
        monthly_trend.append(MonthlyTrend(
            month=label,
            applications=applications,
            interviews=interviews,
            hires=hires,
        ))

    # ── Répartition des statuts ───────────────────────────────────────────────
    total_sessions = db.interview_sessions.count_documents({})
    hired_total    = sum(1 for s in all_completed if (_avg_score(s) or 0) >= 7)
    rejected_total = sum(1 for s in all_completed if (_avg_score(s) or 0) < 5)
    in_iv_total    = db.interview_sessions.count_documents({"status": "in_progress"})
    pending_stat   = db.interview_sessions.count_documents({"status": "pending"})

    status_distribution = StatusDistribution(
        hired=hired_total,
        rejected=rejected_total,
        in_interview=in_iv_total,
        pending=pending_stat,
    )

    # ── Distribution des scores (buckets 0-100) ───────────────────────────────
    buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for session in db.interview_sessions.find({}, {"answers": 1}):
        avg = _avg_score(session)
        if avg is None:
            continue
        score_100 = avg * 10    # Convertir /10 → /100
        if score_100 <= 20:
            buckets["0-20"] += 1
        elif score_100 <= 40:
            buckets["20-40"] += 1
        elif score_100 <= 60:
            buckets["40-60"] += 1
        elif score_100 <= 80:
            buckets["60-80"] += 1
        else:
            buckets["80-100"] += 1

    score_distribution = [
        ScoreBucket(range=k, count=v) for k, v in buckets.items()
    ]

    # ── Performance par département ───────────────────────────────────────────
    # Récupérer tous les postes pour mapper id → département
    positions_map = {
        str(p["_id"]): p.get("department", "Autre")
        for p in db.job_positions.find({}, {"_id": 1, "department": 1})
    }

    dept_candidates: dict = {}
    dept_hires:      dict = {}

    for session in db.interview_sessions.find({}, {"job_position_id": 1, "status": 1, "answers": 1}):
        dept = positions_map.get(session.get("job_position_id", ""), "Autre")
        dept_candidates[dept] = dept_candidates.get(dept, 0) + 1
        if session.get("status") == "completed" and (_avg_score(session) or 0) >= 7:
            dept_hires[dept] = dept_hires.get(dept, 0) + 1

    department_performance = [
        DepartmentPerformance(
            department=dept,
            candidates=count,
            rate=round(dept_hires.get(dept, 0) / count * 100, 1) if count > 0 else 0.0,
        )
        for dept, count in sorted(dept_candidates.items(), key=lambda x: -x[1])
    ]

    return ScoreStats(
        accepted=accepted_curr,
        accepted_pct_change=_pct_change(accepted_curr, accepted_prev),
        rejected=rejected_curr,
        rejected_pct_change=_pct_change(rejected_curr, rejected_prev),
        in_interview=in_interview_curr,
        in_interview_pct_change=_pct_change(in_interview_curr, in_interview_prev),
        pending=pending_total,
        monthly_trend=monthly_trend,
        status_distribution=status_distribution,
        score_distribution=score_distribution,
        department_performance=department_performance,
    )