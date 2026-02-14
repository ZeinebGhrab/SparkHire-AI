from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime


class CandidateStats(BaseModel):
    """Statistiques des candidats"""
    total_candidates: int
    candidates_by_status: Dict[str, int]
    candidates_by_skill: Dict[str, int]
    recent_candidates: int
    top_skills: List[Dict[str, int]]

class InterviewStats(BaseModel):
    """Statistiques des entretiens"""
    total_interviews: int
    interviews_by_status: Dict[str, int]
    interviews_by_position: Dict[str, int]
    average_duration_minutes: float
    completion_rate: float
    total_questions_answered: int
    average_questions_per_interview: float

class MatchStats(BaseModel):
    """Statistiques des matches"""
    total_matches: int
    matches_by_status: Dict[str, int]
    average_match_score: float
    top_matched_positions: List[Dict[str, Any]]
    matches_above_threshold: int

class SystemStats(BaseModel):
    """Statistiques globales du système"""
    total_recruiters: int
    total_job_positions: int
    active_sessions: int
    storage_used_mb: float
    api_calls_today: int
    last_updated: datetime = datetime.utcnow()

class DashboardStats(BaseModel):
    """Statistiques complètes pour le dashboard"""
    candidates: CandidateStats
    interviews: InterviewStats
    matches: MatchStats
    system: SystemStats
    period_start: datetime
    period_end: datetime