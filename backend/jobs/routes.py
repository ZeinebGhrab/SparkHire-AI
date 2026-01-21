from fastapi import APIRouter, Depends, HTTPException
from backend.jobs.models import Job, JobCreate
from backend.jobs.crud import JobCRUD
from backend.auth.security import get_current_recruiter

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=Job)
async def create_job(job: JobCreate, email: str = Depends(get_current_recruiter)):
    return await JobCRUD.create(job)

@router.get("/", response_model=list[Job])
async def list_jobs(active_only: bool = True, email: str = Depends(get_current_recruiter)):
    return await JobCRUD.get_all(active_only)

@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str, email: str = Depends(get_current_recruiter)):
    return await JobCRUD.get_by_id(job_id)

@router.put("/{job_id}", response_model=Job)
async def update_job(job_id: str, job: JobCreate, email: str = Depends(get_current_recruiter)):
    return await JobCRUD.update(job_id, job)

@router.delete("/{job_id}")
async def delete_job(job_id: str, email: str = Depends(get_current_recruiter)):
    success = await JobCRUD.delete(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    return {"message": "Offre supprimée"}