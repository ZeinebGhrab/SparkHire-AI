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