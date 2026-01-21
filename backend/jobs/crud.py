# jobs/crud.py
from backend.jobs.models import Job, JobCreate
from bson import ObjectId
from fastapi import HTTPException
from backend.database import db

class JobCRUD:
    @staticmethod
    async def get_by_id(job_id: str) -> Job:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        job_doc = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job_doc:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        # Convertir _id (ObjectId) en str
        job_doc["_id"] = str(job_doc["_id"])
        return Job(**job_doc)

    @staticmethod
    async def create(job: JobCreate) -> Job:
        job_dict = job.dict()
        result = await db.jobs.insert_one(job_dict)
        job_dict["_id"] = str(result.inserted_id)  # ← Conversion ici
        return Job(**job_dict)

    @staticmethod
    async def update(job_id: str, job: JobCreate) -> Job:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        await db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": job.dict()})
        return await JobCRUD.get_by_id(job_id)

    @staticmethod
    async def delete(job_id: str) -> bool:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID invalide")
        result = await db.jobs.delete_one({"_id": ObjectId(job_id)})
        return result.deleted_count > 0