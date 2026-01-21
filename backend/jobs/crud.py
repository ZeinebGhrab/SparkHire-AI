from backend.database import db
from backend.jobs.models import Job, JobCreate
from bson import ObjectId
from fastapi import HTTPException

class JobCRUD:
    @staticmethod
    def create(job: JobCreate) -> Job:
        job_dict = job.dict()
        result = db.jobs.insert_one(job_dict)
        job_dict["_id"] = str(result.inserted_id)
        return Job(**job_dict)

    @staticmethod
    def get_all(active_only: bool = True) -> list[Job]:
        query = {"is_active": True} if active_only else {}
        jobs = list(db.jobs.find(query))
        for job in jobs:
            job["_id"] = str(job["_id"])
        return [Job(**job) for job in jobs]

    @staticmethod
    def get_by_id(job_id: str) -> Job:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        job = db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        job["_id"] = str(job["_id"])
        return Job(**job)

    @staticmethod
    def update(job_id: str, job: JobCreate) -> Job:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": job.dict()})
        return JobCRUD.get_by_id(job_id)

    @staticmethod
    def delete(job_id: str) -> bool:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        result = db.jobs.delete_one({"_id": ObjectId(job_id)})
        return result.deleted_count > 0