from fastapi import APIRouter, Depends, HTTPException
from backend.jobs.models import Job, JobCreate
from backend.jobs.crud import JobCRUD
from backend.auth.security import get_current_recruiter

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=Job)
def create_job(job: JobCreate, _: str = Depends(get_current_recruiter)):
    return JobCRUD.create(job)

@router.get("/", response_model=list[Job])
def list_jobs(active_only: bool = True, _: str = Depends(get_current_recruiter)):
    return JobCRUD.get_all(active_only)

@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str, _: str = Depends(get_current_recruiter)):
    return JobCRUD.get_by_id(job_id)

@router.put("/{job_id}", response_model=Job)
def update_job(job_id: str, job: JobCreate, _: str = Depends(get_current_recruiter)):
    return JobCRUD.update(job_id, job)

@router.delete("/{job_id}")
def delete_job(job_id: str, _: str = Depends(get_current_recruiter)):
    success = JobCRUD.delete(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    return {"message": "Offre supprimée"}