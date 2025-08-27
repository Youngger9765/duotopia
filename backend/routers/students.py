from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models import Student, Classroom
from auth import create_access_token, verify_password, get_password_hash
from datetime import timedelta, datetime

router = APIRouter(prefix="/api/students", tags=["students"])

class StudentValidateRequest(BaseModel):
    email: str
    birthdate: str  # Format: YYYYMMDD

class StudentLoginResponse(BaseModel):
    access_token: str
    token_type: str
    student: dict

@router.post("/validate", response_model=StudentLoginResponse)
async def validate_student(request: StudentValidateRequest, db: Session = Depends(get_db)):
    """學生登入驗證"""
    # 查詢學生
    student = db.query(Student).filter(Student.email == request.email).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # 驗證生日（作為密碼）
    if not verify_password(request.birthdate, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 建立 token
    access_token = create_access_token(
        data={"sub": str(student.id), "type": "student"},
        expires_delta=timedelta(minutes=30)
    )
    
    # 取得班級資訊 - 需要從 ClassroomStudent 關聯取得
    # TODO: 實作取得學生班級資訊
    student_class = None
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "class_id": None,  # TODO: Get from ClassroomStudent
            "class_name": None  # TODO: Get from ClassroomStudent
        }
    }

@router.get("/me")
async def get_current_student():
    """取得當前學生資訊"""
    # TODO: 實作從 token 取得學生資訊
    return {"message": "Student profile endpoint"}

@router.get("/assignments")
async def get_student_assignments():
    """取得學生作業列表"""
    # TODO: 實作作業列表
    return {"assignments": []}