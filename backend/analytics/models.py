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