from fastapi import APIRouter, Depends, HTTPException
from backend.auth.models import RecruiterCreate, Token
from backend.auth.security import get_current_recruiter, create_access_token, verify_password
from backend.database import db

router = APIRouter(prefix="/auth", tags=["Auth"])

# backend/auth/routes.py
@router.post("/login", response_model=Token)
def login(recruiter: RecruiterCreate):
    print("🔍 Tentative de login :", recruiter.email)  # ← Ajoutez ceci
    user = db.recruiters.find_one({"email": recruiter.email})
    print("👤 Utilisateur trouvé :", user)  # ← Et ceci
    if not user or not verify_password(recruiter.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    access_token = create_access_token(data={"sub": recruiter.email})
    return {"access_token": access_token}

@router.get("/me")
def read_users_me(email: str = Depends(get_current_recruiter)):
    return {"email": email}