from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any  # noqa: F401
from database import get_db
from models import (
    Student,
    Classroom,
    ClassroomStudent,
    StudentAssignment,
)
from auth import (
    create_access_token,
    verify_password,
    get_current_user,
)
from datetime import timedelta, datetime  # noqa: F401

router = APIRouter(prefix="/api/students", tags=["students"])


class StudentValidateRequest(BaseModel):
    email: str
    birthdate: str  # Format: YYYYMMDD


class StudentLoginResponse(BaseModel):
    access_token: str
    token_type: str
    student: dict


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

    # 驗證生日（作為密碼）
    if not verify_password(request.birthdate, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # 建立 token
    access_token = create_access_token(
        data={"sub": str(student.id), "type": "student"},
        expires_delta=timedelta(minutes=30),
    )

    # 取得班級資訊 - 需要從 ClassroomStudent 關聯取得
    # TODO: 實作取得學生班級資訊
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "class_id": None,  # TODO: Get from ClassroomStudent
            "class_name": None,  # TODO: Get from ClassroomStudent
        },
    }


@router.get("/profile")
async def get_student_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取得當前學生資訊"""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = current_user.get("sub")
    student = db.query(Student).filter(Student.id == int(student_id)).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # Get classroom info
    classroom_student = (
        db.query(ClassroomStudent)
        .filter(ClassroomStudent.student_id == student.id)
        .first()
    )

    classroom_name = None
    classroom_id = None
    if classroom_student:
        classroom = (
            db.query(Classroom)
            .filter(Classroom.id == classroom_student.classroom_id)
            .first()
        )
        if classroom:
            classroom_name = classroom.name
            classroom_id = classroom.id

    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "student_id": student.student_id,
        "classroom_id": classroom_id,
        "classroom_name": classroom_name,
        "target_wpm": student.target_wpm,
        "target_accuracy": student.target_accuracy,
    }


@router.get("/assignments")
async def get_student_assignments(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取得學生作業列表"""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = current_user.get("sub")

    # Get assignments
    assignments = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.student_id == int(student_id))
        .order_by(
            StudentAssignment.due_date.desc()
            if StudentAssignment.due_date
            else StudentAssignment.assigned_at.desc()
        )
        .all()
    )

    result = []
    for assignment in assignments:
        result.append(
            {
                "id": assignment.id,
                "title": assignment.title,
                "status": (
                    assignment.status.value if assignment.status else "not_started"
                ),
                "due_date": (
                    assignment.due_date.isoformat() if assignment.due_date else None
                ),
                "assigned_at": (
                    assignment.assigned_at.isoformat()
                    if assignment.assigned_at
                    else None
                ),
                "submitted_at": (
                    assignment.submitted_at.isoformat()
                    if assignment.submitted_at
                    else None
                ),
                "content_id": assignment.content_id,
                "classroom_id": assignment.classroom_id,
                "score": assignment.score,
                "feedback": assignment.feedback,
            }
        )

    return result
