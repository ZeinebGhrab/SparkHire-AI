from fastapi import FastAPI
from backend.auth.routes import router as auth_router
from backend.jobs.routes import router as jobs_router
from backend.candidates.routes import router as candidates_router
from backend.matches.routes import router as matches_router

app = FastAPI(
    title="Stark Recruitment API",
    description="API pour le système de recrutement intelligent avec IA vocale"
)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(matches_router)

# Endpoint de santé
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API Stark Recruitment",
        "documentation": "/docs",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "jobs": "/jobs",
            "candidates": "/candidates",
            "matches": "/matches"
        }
    }
