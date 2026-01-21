from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

class JobBase(BaseModel):
    title: str
    must_have: List[str]
    nice_to_have: List[str] = []
    is_active: bool = True

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: str = Field(..., alias="_id")  
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}