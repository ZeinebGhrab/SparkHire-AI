from fastapi import APIRouter, Depends, HTTPException, status
from backend.auth.models import RecruiterCreate, Token
from backend.auth.security import get_current_recruiter, get_password_hash, create_access_token, verify_password
from backend.database import db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
async def login(recruiter: RecruiterCreate):
    user = await db.recruiters.find_one({"email": recruiter.email})
    if not user or not verify_password(recruiter.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    access_token = create_access_token(data={"sub": recruiter.email})
    return {"access_token": access_token}

@router.get("/me")
async def read_users_me(email: str = Depends(get_current_recruiter)):
    return {"email": email}