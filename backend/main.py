from fastapi import FastAPI
from backend.auth.routes import router as auth_router
from backend.jobs.routes import router as jobs_router

app = FastAPI(title="Stark Recruitment API")

app.include_router(auth_router)
app.include_router(jobs_router)

# Endpoint de santé
@app.get("/health")
async def health():
    return {"status": "ok"}