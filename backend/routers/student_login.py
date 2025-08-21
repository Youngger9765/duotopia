"""
學生登入系統 API - 支援雙體系架構
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
from database import get_db
from models_dual_system import (
    DualUser, IndividualClassroom, IndividualStudent, 
    IndividualEnrollment
)
from pydantic import BaseModel
import bcrypt

router = APIRouter(prefix="/api/student-login", tags=["student-login"])

class StudentPasswordVerify(BaseModel):
    student_id: str
    password: str

class StudentPasswordChange(BaseModel):
    student_id: str
    current_password: str
    new_password: str

@router.get("/teachers/search")
async def search_teachers_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """根據 email 查找個體戶老師"""
    teacher = db.query(DualUser).filter(
        DualUser.email == email,
        DualUser.is_individual_teacher == True,
        DualUser.is_active == True
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="找不到此老師的Email")
    
    return {
        "id": teacher.id,
        "email": teacher.email,
        "full_name": teacher.full_name
    }

@router.get("/teachers/{teacher_id}/info")
async def get_teacher_info(
    teacher_id: str,
    db: Session = Depends(get_db)
):
    """獲取老師的基本資訊"""
    teacher = db.query(DualUser).filter(
        DualUser.id == teacher_id,
        DualUser.is_individual_teacher == True,
        DualUser.is_active == True
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="找不到該老師")
    
    return {
        "id": teacher.id,
        "email": teacher.email,
        "full_name": teacher.full_name
    }

@router.get("/teachers/{teacher_id}/classrooms")
async def get_teacher_classrooms(
    teacher_id: str,
    db: Session = Depends(get_db)
):
    """獲取老師的所有教室"""
    classrooms = db.query(IndividualClassroom).filter(
        IndividualClassroom.teacher_id == teacher_id,
        IndividualClassroom.is_active == True
    ).all()
    
    return [{
        "id": classroom.id,
        "name": classroom.name,
        "grade_level": classroom.grade_level,
        "student_count": db.query(IndividualEnrollment).filter(
            IndividualEnrollment.classroom_id == classroom.id,
            IndividualEnrollment.is_active == True
        ).count()
    } for classroom in classrooms]

@router.get("/classrooms/{classroom_id}/students")
async def get_classroom_students(
    classroom_id: str,
    db: Session = Depends(get_db)
):
    """獲取教室內的所有學生"""
    # 驗證教室存在
    classroom = db.query(IndividualClassroom).filter(
        IndividualClassroom.id == classroom_id,
        IndividualClassroom.is_active == True
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 獲取學生列表
    enrollments = db.query(IndividualEnrollment).options(
        joinedload(IndividualEnrollment.student)
    ).filter(
        IndividualEnrollment.classroom_id == classroom_id,
        IndividualEnrollment.is_active == True
    ).all()
    
    students = []
    for enrollment in enrollments:
        student = enrollment.student
        students.append({
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email or "未設定",
            "birth_date": student.birth_date
        })
    
    return students

@router.post("/verify-password")
async def verify_student_password(
    request: StudentPasswordVerify,
    db: Session = Depends(get_db)
):
    """驗證學生密碼並返回登入令牌"""
    from auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    from datetime import timedelta
    
    # 查找學生
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == request.student_id,
        IndividualStudent.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    # 驗證密碼
    if student.is_default_password:
        # 使用預設密碼（生日格式：YYYYMMDD）
        expected_password = student.birth_date.replace('-', '') if student.birth_date else None
        if expected_password != request.password:
            raise HTTPException(status_code=401, detail="密碼錯誤")
    else:
        # 使用自訂密碼（需要比對 hash）
        if not student.password_hash:
            raise HTTPException(status_code=500, detail="密碼設定異常")
        
        if not bcrypt.checkpw(request.password.encode('utf-8'), student.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="密碼錯誤")
    
    # 創建登入令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": student.email or f"student_{student.id}",
            "role": "student", 
            "student_id": student.id,
            "teacher_id": student.teacher_id
        }, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "teacher_id": student.teacher_id,
            "is_default_password": student.is_default_password
        }
    }

@router.post("/change-password")
async def change_student_password(
    request: StudentPasswordChange,
    db: Session = Depends(get_db)
):
    """學生修改密碼"""
    # 查找學生
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == request.student_id,
        IndividualStudent.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    # 驗證當前密碼
    if student.is_default_password:
        # 使用預設密碼（生日格式：YYYYMMDD）
        expected_password = student.birth_date.replace('-', '') if student.birth_date else None
        if expected_password != request.current_password:
            raise HTTPException(status_code=401, detail="當前密碼錯誤")
    else:
        # 使用自訂密碼（需要比對 hash）
        if not student.password_hash:
            raise HTTPException(status_code=500, detail="密碼設定異常")
        
        if not bcrypt.checkpw(request.current_password.encode('utf-8'), student.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="當前密碼錯誤")
    
    # 設定新密碼
    if len(request.new_password) < 4:
        raise HTTPException(status_code=400, detail="新密碼至少需要4個字符")
    
    # Hash 新密碼
    new_password_hash = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # 更新資料庫
    student.password_hash = new_password_hash
    student.is_default_password = False
    db.commit()
    
    return {
        "success": True,
        "message": "密碼修改成功"
    }