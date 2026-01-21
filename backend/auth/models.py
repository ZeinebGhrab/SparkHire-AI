from pydantic import BaseModel, EmailStr

class Recruiter(BaseModel):
    email: EmailStr
    password_hash: str  

class RecruiterCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"