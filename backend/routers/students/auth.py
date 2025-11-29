"""Student authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from models import Student, Classroom, ClassroomStudent
from auth import create_access_token, verify_password
from .validators import StudentValidateRequest, StudentLoginResponse

router = APIRouter()


@router.post("/validate", response_model=StudentLoginResponse)
async def validate_student(
    request: StudentValidateRequest, db: Session = Depends(get_db)
):
    """學生登入驗證"""
    # 查詢學生
    student = db.query(Student).filter(Student.email == request.email).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # 驗證密碼 - 未改密碼時是生日，改密碼後是新密碼
    if not verify_password(request.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password"
        )

    # 建立 token
    access_token = create_access_token(
        data={"sub": str(student.id), "type": "student"},
        expires_delta=timedelta(minutes=30),
    )

    # 取得班級資訊 - 使用 JOIN 優化查詢（避免 N+1）
    # 原本：3次查詢 (Student + ClassroomStudent + Classroom)
    # 現在：1次查詢 (JOIN)
    classroom_info = (
        db.query(Classroom.id, Classroom.name)
        .join(ClassroomStudent)
        .filter(ClassroomStudent.student_id == student.id)
        .first()
    )

    classroom_id = classroom_info[0] if classroom_info else None
    classroom_name = classroom_info[1] if classroom_info else None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "classroom_id": classroom_id,
            "classroom_name": classroom_name,
        },
    }
