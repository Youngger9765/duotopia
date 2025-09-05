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
    Content,
    AssignmentStatus,
    AssignmentContent,
    StudentContentProgress,
)
from auth import (
    create_access_token,
    verify_password,
    get_current_user,
)
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


@router.get("/assignments/{assignment_id}/activities")
async def get_assignment_activities(
    assignment_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取得作業的活動內容列表（題目）"""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = int(current_user.get("sub"))

    # 確認學生有這個作業
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == student_id,
            StudentAssignment.is_active.is_(True),
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not assigned to you",
        )

    # 獲取作業對應的 Assignment（如果有 assignment_id）
    activities = []

    # 如果有 content_id，直接獲取該內容
    if student_assignment.content_id:
        content = (
            db.query(Content)
            .filter(Content.id == student_assignment.content_id)
            .first()
        )

        if content:
            # 檢查是否已有進度記錄
            progress = (
                db.query(StudentContentProgress)
                .filter(
                    StudentContentProgress.student_assignment_id
                    == student_assignment.id,
                    StudentContentProgress.content_id == content.id,
                )
                .first()
            )

            # 如果沒有進度記錄，創建一個
            if not progress:
                progress = StudentContentProgress(
                    student_assignment_id=student_assignment.id,
                    content_id=content.id,
                    order_index=0,
                    status=AssignmentStatus.NOT_STARTED,
                )
                db.add(progress)
                db.commit()
                db.refresh(progress)

            activities.append(
                {
                    "id": progress.id,
                    "content_id": content.id,
                    "order": 1,
                    "type": content.type.value
                    if content.type
                    else "reading_assessment",
                    "title": content.title,
                    "content": content.content,
                    "target_text": content.content,  # For reading assessment
                    "duration": 60,  # Default duration
                    "points": 100,
                    "status": progress.status.value
                    if progress.status
                    else "NOT_STARTED",
                    "score": progress.score,
                    "audio_url": progress.audio_url,
                    "completed_at": progress.completed_at.isoformat()
                    if progress.completed_at
                    else None,
                }
            )

    # 如果有 assignment_id，獲取所有相關內容
    elif student_assignment.assignment_id:
        # 獲取作業的所有內容
        assignment_contents = (
            db.query(AssignmentContent)
            .filter(AssignmentContent.assignment_id == student_assignment.assignment_id)
            .order_by(AssignmentContent.order_index)
            .all()
        )

        for idx, ac in enumerate(assignment_contents):
            content = db.query(Content).filter(Content.id == ac.content_id).first()

            if content:
                # 檢查是否已有進度記錄
                progress = (
                    db.query(StudentContentProgress)
                    .filter(
                        StudentContentProgress.student_assignment_id
                        == student_assignment.id,
                        StudentContentProgress.content_id == content.id,
                    )
                    .first()
                )

                # 如果沒有進度記錄，創建一個
                if not progress:
                    progress = StudentContentProgress(
                        student_assignment_id=student_assignment.id,
                        content_id=content.id,
                        order_index=ac.order_index,
                        status=AssignmentStatus.NOT_STARTED,
                    )
                    db.add(progress)
                    db.commit()
                    db.refresh(progress)

                activities.append(
                    {
                        "id": progress.id,
                        "content_id": content.id,
                        "order": ac.order_index + 1,
                        "type": content.type.value
                        if content.type
                        else "reading_assessment",
                        "title": content.title,
                        "content": content.content,
                        "target_text": content.content,  # For reading assessment
                        "duration": 60,  # Default duration
                        "points": 100 // len(assignment_contents)
                        if assignment_contents
                        else 100,
                        "status": progress.status.value
                        if progress.status
                        else "NOT_STARTED",
                        "score": progress.score,
                        "audio_url": progress.audio_url,
                        "completed_at": progress.completed_at.isoformat()
                        if progress.completed_at
                        else None,
                    }
                )

    # 如果沒有活動，創建一個默認的朗讀活動
    if not activities:
        # 創建一個臨時的朗讀活動
        activities.append(
            {
                "id": 0,
                "content_id": 0,
                "order": 1,
                "type": "reading_assessment",
                "title": "朗讀測驗",
                "content": "Please read the following text aloud.",
                "target_text": (
                    "The quick brown fox jumps over the lazy dog. "
                    "This pangram contains all letters of the English alphabet."
                ),
                "duration": 60,
                "points": 100,
                "status": "NOT_STARTED",
                "score": None,
                "audio_url": None,
                "completed_at": None,
            }
        )

    # 更新作業狀態為進行中（如果還是未開始）
    if student_assignment.status == AssignmentStatus.NOT_STARTED:
        student_assignment.status = AssignmentStatus.IN_PROGRESS
        db.commit()

    return {
        "assignment_id": assignment_id,
        "title": student_assignment.title,
        "total_activities": len(activities),
        "activities": activities,
    }


@router.post("/assignments/{assignment_id}/activities/{progress_id}/save")
async def save_activity_progress(
    assignment_id: int,
    progress_id: int,
    audio_url: Optional[str] = None,
    text_answer: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """儲存活動進度（自動儲存）"""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = int(current_user.get("sub"))

    # 確認學生有這個作業
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # 獲取並更新進度記錄
    progress = (
        db.query(StudentContentProgress)
        .filter(
            StudentContentProgress.id == progress_id,
            StudentContentProgress.student_assignment_id == student_assignment.id,
        )
        .first()
    )

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity progress not found"
        )

    # 更新進度
    if audio_url:
        progress.audio_url = audio_url
    if text_answer:
        progress.text_response = text_answer

    # 更新狀態
    if progress.status == AssignmentStatus.NOT_STARTED:
        progress.status = AssignmentStatus.IN_PROGRESS

    db.commit()

    return {"message": "Progress saved successfully"}


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交作業"""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = int(current_user.get("sub"))

    # 確認學生有這個作業
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # 更新所有進度為已完成
    progress_records = (
        db.query(StudentContentProgress)
        .filter(StudentContentProgress.student_assignment_id == student_assignment.id)
        .all()
    )

    for progress in progress_records:
        if progress.status == AssignmentStatus.IN_PROGRESS:
            progress.status = AssignmentStatus.SUBMITTED
            progress.completed_at = datetime.now()

    # 更新作業狀態
    student_assignment.status = AssignmentStatus.SUBMITTED
    student_assignment.submitted_at = datetime.now()

    db.commit()

    return {
        "message": "Assignment submitted successfully",
        "submitted_at": student_assignment.submitted_at.isoformat(),
    }
