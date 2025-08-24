from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Dict, Any
import httpx
from google.auth import jwt as google_jwt
from google.auth.transport import requests
from pydantic import BaseModel

from database import get_db
from auth import (
    authenticate_user, 
    authenticate_student,
    create_access_token, 
    get_password_hash,
    get_current_active_user,
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

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login for teachers/admins"""
    # Authenticate user
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
    
    # Check if it's a dual user
    response = {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_type": user.role.value,
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email
    }
    
    # Add dual system specific fields if applicable
    if hasattr(user, 'is_individual_teacher'):
        response["is_individual_teacher"] = user.is_individual_teacher
        response["is_institutional_admin"] = user.is_institutional_admin
        response["current_role_context"] = user.current_role_context
    
    return response

@router.get("/validate")
async def validate_token(current_user: models.User = Depends(get_current_active_user)):
    """Validate token and return user info"""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "user_type": current_user.role.value,
        "is_individual_teacher": current_user.is_individual_teacher if hasattr(current_user, 'is_individual_teacher') else False,
        "is_institutional_admin": current_user.is_institutional_admin if hasattr(current_user, 'is_institutional_admin') else False,
        "current_role_context": current_user.current_role_context if hasattr(current_user, 'current_role_context') else "default"
    }

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
async def validate_token(user: models.User = Depends(get_current_active_user)):
    """Validate current token and return user info"""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }

# Student 4-step authentication flow
temp_student_sessions = {}  # In-memory storage for temporary sessions

@router.post("/student/send-otp")
async def send_otp(request: Dict[str, str]):
    """Step 1: Send OTP to student's phone"""
    phone_number = request.get("phone_number")
    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
    
    # In production, send real OTP via SMS
    # For testing, we'll accept any OTP
    return {"message": "OTP sent successfully", "status": "sent"}

@router.post("/student/verify-otp")
async def verify_otp(request: Dict[str, str], db: Session = Depends(get_db)):
    """Step 2: Verify OTP and return temporary token"""
    phone_number = request.get("phone_number")
    otp = request.get("otp")
    
    if not phone_number or not otp:
        raise HTTPException(status_code=400, detail="Phone number and OTP are required")
    
    # For testing, accept OTP "123456"
    if otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Create temporary token
    temp_token = create_access_token(
        data={"phone": phone_number, "step": "verified"},
        expires_delta=timedelta(minutes=10)
    )
    
    # Store session info
    temp_student_sessions[phone_number] = {
        "phone": phone_number,
        "verified": True
    }
    
    return {"temp_token": temp_token, "status": "verified"}

@router.post("/student/submit-info")
async def submit_student_info(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Step 3: Submit student information"""
    # Extract data from request
    name = request.get("name")
    grade = request.get("grade")
    school = request.get("school")
    
    if not all([name, grade, school]):
        raise HTTPException(status_code=400, detail="All fields are required")
    
    # TODO: Verify temp token and extract phone number
    phone_number = "+1234567890"  # For testing
    
    # Check if student exists
    student = db.query(models.Student).filter(
        models.Student.phone_number == phone_number
    ).first()
    
    if student:
        # Update existing student
        student.name = name
        student.grade = grade
        student.school = school
    else:
        # Create new student
        student = models.Student(
            phone_number=phone_number,
            name=name,
            full_name=name,  # Set full_name same as name
            grade=grade,
            school=school,
            email=f"student_{phone_number.replace('+', '')}@duotopia.com",
            birth_date="20120101"  # Default birth date for testing
        )
        db.add(student)
    
    db.commit()
    db.refresh(student)
    
    # Get student's existing courses
    existing_courses = []
    for enrollment in student.enrollments:
        course = enrollment.course
        existing_courses.append({
            "id": course.id,
            "title": course.title,
            "teacher_name": course.teacher.full_name if course.teacher else "N/A"
        })
    
    # Update session
    temp_student_sessions[phone_number]["student_id"] = student.id
    
    return {
        "status": "info_submitted",
        "existing_courses": existing_courses,
        "student_id": student.id
    }

@router.post("/student/enter-course-code")
async def enter_course_code(
    request: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Step 4: Enter course code and complete registration"""
    course_code = request.get("course_code")
    
    if not course_code:
        raise HTTPException(status_code=400, detail="Course code is required")
    
    # TODO: Extract student info from token
    phone_number = "+1234567890"  # For testing
    session = temp_student_sessions.get(phone_number)
    
    if not session or "student_id" not in session:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    student_id = session["student_id"]
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Find course by code
    course = db.query(models.Course).filter(
        models.Course.course_code == course_code
    ).first()
    
    if course:
        # Check if already enrolled
        existing_enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student.id,
            models.Enrollment.course_id == course.id
        ).first()
        
        if not existing_enrollment:
            # Enroll student in course
            enrollment = models.Enrollment(
                student_id=student.id,
                course_id=course.id
            )
            db.add(enrollment)
            db.commit()
    
    # Create final access token
    access_token = create_access_token(
        data={"sub": student.email, "role": "student"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Clean up session
    if phone_number in temp_student_sessions:
        del temp_student_sessions[phone_number]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "student",
        "user_id": student.id
    }