from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Question:
    order: int
    question_ar: str
    question_en: str
    max_duration_seconds: int

@dataclass
class Answer:
    question_order: int
    question_text: str
    transcript: str
    duration_seconds: float

@dataclass
class InterviewSession:
    session_id: str
    candidate_id: str
    job_position_id: str
    language: str
    status: str
    current_question_index: int
    answers: List[Answer]
    
@dataclass
class Progress:
    current: int
    total: int
    percentage: int