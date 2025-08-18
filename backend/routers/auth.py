from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Dict
import httpx
from google.auth import jwt as google_jwt
from google.auth.transport import requests

from database import get_db
from auth import (
    authenticate_user, 
    authenticate_student,
    create_access_token, 
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
import models
import schemas
import os

router = APIRouter(prefix="/api/auth", tags=["authentication"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

@router.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new teacher/admin user"""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login for teachers/admins"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google", response_model=schemas.Token)
async def google_auth(request: schemas.GoogleAuthRequest, db: Session = Depends(get_db)):
    """Google OAuth login for teachers"""
    try:
        # Verify the Google ID token
        idinfo = google_jwt.decode(request.id_token, requests.Request())
        
        if idinfo['aud'] != GOOGLE_CLIENT_ID:
            raise ValueError('Invalid client ID')
        
        email = idinfo['email']
        name = idinfo.get('name', email)
        
        # Check if user exists
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            # Create new teacher account
            user = models.User(
                email=email,
                full_name=name,
                role=models.UserRole.TEACHER,
                hashed_password=""  # No password for OAuth users
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/student/login", response_model=schemas.Token)
async def student_login(request: schemas.StudentLoginRequest, db: Session = Depends(get_db)):
    """Student login with email and birth date"""
    student = authenticate_student(db, request.email, request.birth_date)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or birth date"
        )
    
    # Create a user session for the student
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.email, "role": "student"}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/validate")
async def validate_token(user: models.User = Depends(auth.get_current_active_user)):
    """Validate current token and return user info"""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }