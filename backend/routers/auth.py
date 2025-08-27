from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from database import get_db
from models import Teacher
from auth import verify_password, create_access_token, get_password_hash
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_type: str

class GoogleAuthRequest(BaseModel):
    token: str

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """教師登入"""
    teacher = db.query(Teacher).filter(Teacher.email == request.email).first()
    
    if not teacher or not verify_password(request.password, teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(
        data={"sub": str(teacher.id), "type": "teacher"},
        expires_delta=timedelta(minutes=30)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "teacher"
    }

@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Google OAuth 登入"""
    # TODO: 實作 Google OAuth 驗證
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth not implemented yet"
    )

@router.get("/validate")
async def validate_token():
    """驗證 token (用於測試)"""
    return {"status": "auth endpoint working"}