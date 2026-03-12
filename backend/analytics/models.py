from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class SkillStat(BaseModel):
    skill: str
    count: int


class CandidateStats(BaseModel):
    total_candidates: int
    candidates_by_status: Dict[str, int]
    candidates_by_skill: Dict[str, int]
    recent_candidates: int
    top_skills: List[SkillStat]


class InterviewStats(BaseModel):
    total_interviews: int
    interviews_by_status: Dict[str, int]
    interviews_by_position: Dict[str, int]
    average_duration_minutes: float
    completion_rate: float
    total_questions_answered: int
    average_questions_per_interview: float
    average_score: float = 0.0          # Score moyen LLM sur toutes les réponses


class SystemStats(BaseModel):
    total_recruiters: int
    total_job_positions: int
    active_sessions: int
    storage_used_mb: float
    api_calls_today: int
    last_updated: datetime = datetime.utcnow()


class DashboardStats(BaseModel):
    candidates: CandidateStats
    interviews: InterviewStats
    system: SystemStats
    period_start: datetime
    period_end: datetime


class SchedulingStats(BaseModel):
    total_scheduled: int          # Tous les entretiens planifiés (status != cancelled)
    this_week: int                # Créés ou planifiés cette semaine (lun–dim)
    confirmed: int                # status = "completed" ou "in_progress"
    pending: int                  # status = "pending"
    cancelled: int                # status = "cancelled"
    by_day_this_week: Dict[str, int]   # {"Lun": 1, "Mar": 0, ...}
    by_position: Dict[str, int]        # {"Data Scientist": 3, ...}
    by_language: Dict[str, int]        # {"ar": 2, "fr": 1, "en": 0}
    upcoming_7_days: int          # Sessions créées dans les 7 prochains jours (expires_at)


# ── Score / Candidature Statistics ───────────────────────────────────────────

class MonthlyTrend(BaseModel):
    month: str                     # "Jan", "Fév", "Mar" ...
    applications: int              # Candidatures (sessions créées)
    interviews: int                # Entretiens démarrés (in_progress + completed)
    hires: int                     # Entretiens avec score >= 7 (recommandés)


class StatusDistribution(BaseModel):
    hired: int                     # score >= 7 + completed
    rejected: int                  # score < 5 + completed
    in_interview: int              # in_progress
    pending: int                   # pending


class ScoreBucket(BaseModel):
    range: str                     # "0-20", "20-40", "40-60", "60-80", "80-100"
    count: int


class DepartmentPerformance(BaseModel):
    department: str
    candidates: int                # Nombre de sessions pour ce département
    rate: float                    # Taux de réussite (score >= 7) en %


class ScoreStats(BaseModel):
    # ── KPI cards ──────────────────────────────────────────────────────
    accepted: int                  # Sessions completed avec score_moyen >= 7
    accepted_pct_change: float     # % variation vs mois précédent
    rejected: int                  # Sessions completed avec score_moyen < 5
    rejected_pct_change: float
    in_interview: int              # Sessions in_progress
    in_interview_pct_change: float
    pending: int                   # Sessions pending
    # ── Graphiques ─────────────────────────────────────────────────────
    monthly_trend: List[MonthlyTrend]         # 6 derniers mois
    status_distribution: StatusDistribution   # Répartition des statuts (%)
    score_distribution: List[ScoreBucket]     # Distribution des scores 0-100
    department_performance: List[DepartmentPerformance]  # Performance par département