from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from backend.auth.models import RecruiterCreate, Token
from backend.auth.security import get_current_recruiter, create_access_token, verify_password
from backend.database import db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.recruiters.find_one({"email": form_data.username})

    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token}

@router.get("/me")
def read_users_me(email: str = Depends(get_current_recruiter)):
    return {"email": email}