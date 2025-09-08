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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password"
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
                    "type": (
                        content.type.value if content.type else "reading_assessment"
                    ),
                    "title": content.title,
                    "content": content.items,  # JSON array of items
                    "target_text": content.items,  # For reading assessment
                    "duration": 60,  # Default duration
                    "points": 100,
                    "status": (
                        progress.status.value if progress.status else "NOT_STARTED"
                    ),
                    "score": progress.score,
                    "audio_url": progress.audio_url,
                    "completed_at": (
                        progress.completed_at.isoformat()
                        if progress.completed_at
                        else None
                    ),
                }
            )

    # 如果有 assignment_id，直接獲取所有已存在的 StudentContentProgress 記錄
    elif student_assignment.assignment_id:
        # 直接查詢這個學生作業的所有進度記錄（這才是正確的數據源）
        progress_records = (
            db.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id == student_assignment.id
            )
            .order_by(StudentContentProgress.order_index)
            .all()
        )

        for progress in progress_records:
            content = (
                db.query(Content).filter(Content.id == progress.content_id).first()
            )

            if content:
                # 將整個 content 作為一個活動，包含所有 items
                activity_data = {
                    "id": progress.id,
                    "content_id": content.id,
                    "order": len(activities) + 1,
                    "type": (
                        content.type.value if content.type else "reading_assessment"
                    ),
                    "title": content.title,
                    "duration": 60,  # Default duration
                    "points": 100 // len(progress_records)
                    if len(progress_records) > 0
                    else 100,  # 平均分配分數
                    "status": (
                        progress.status.value if progress.status else "NOT_STARTED"
                    ),
                    "score": progress.score,
                    "completed_at": (
                        progress.completed_at.isoformat()
                        if progress.completed_at
                        else None
                    ),
                }

                # 如果有 items，將它們作為子題目包含進去
                if (
                    content.items
                    and isinstance(content.items, list)
                    and len(content.items) > 0
                ):
                    activity_data["items"] = content.items  # 包含所有 items
                    activity_data["item_count"] = len(content.items)  # 題目數量
                    activity_data["content"] = ""  # 對於有 items 的，content 為空
                    activity_data["target_text"] = ""

                    # 如果有 response_data，包含所有錄音
                    if progress.response_data:
                        activity_data["recordings"] = progress.response_data.get(
                            "recordings", []
                        )
                        activity_data["answers"] = progress.response_data.get(
                            "answers", []
                        )
                else:
                    # 沒有 items 的情況
                    activity_data["content"] = (
                        str(content.items) if content.items else ""
                    )
                    activity_data["target_text"] = (
                        str(content.items) if content.items else ""
                    )
                    activity_data["audio_url"] = (
                        progress.response_data.get("audio_url")
                        if progress.response_data
                        else None
                    )

                activities.append(activity_data)

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


# ========== Email 驗證相關 API ==========


class EmailUpdateRequest(BaseModel):
    email: str


@router.post("/update-email")
async def update_student_email(
    request: EmailUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新學生 email (簡化版本用於前端)"""
    from services.email_service import email_service

    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = int(current_user.get("sub"))
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # 更新 email
    student.email = request.email
    student.email_verified = False
    student.email_verified_at = None

    # 發送驗證信
    success = email_service.send_verification_email(db, student, request.email)

    db.commit()

    return {
        "message": "Email updated and verification email sent",
        "email": request.email,
        "verified": False,
        "verification_sent": success,
    }


@router.post("/unbind-email")
async def unbind_student_email(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """解除學生 email 綁定"""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = int(current_user.get("sub"))
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # 清除 email 相關欄位
    student.email = None
    student.email_verified = False
    student.email_verified_at = None
    student.email_verification_token = None
    student.email_verification_sent_at = None

    db.commit()

    return {
        "message": "Email unbind successfully",
        "email": None,
        "verified": False,
    }


@router.get("/me")
async def get_current_student_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取得當前學生資訊 (別名為 /profile)"""
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
        "email_verified": student.email_verified,
        "student_id": student.student_id,
        "classroom_id": classroom_id,
        "classroom_name": classroom_name,
        "target_wpm": student.target_wpm,
        "target_accuracy": student.target_accuracy,
    }


@router.post("/{student_id}/email/request-verification")
async def request_email_verification(
    student_id: int,
    email_request: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """請求發送 email 驗證信"""
    from services.email_service import email_service

    # 確認是學生本人
    if (
        current_user.get("type") != "student"
        or int(current_user.get("sub")) != student_id
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 檢查是否已經驗證
    if student.email_verified:
        return {"message": "Email already verified", "verified": True}

    email = email_request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # 發送驗證信
    success = email_service.send_verification_email(db, student, email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {
        "message": "Verification email sent successfully",
        "email": email,
        "verification_sent": True,
    }


@router.post("/{student_id}/email/resend-verification")
async def resend_email_verification(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """重新發送驗證信"""
    from services.email_service import email_service

    # 確認是學生本人
    if (
        current_user.get("type") != "student"
        or int(current_user.get("sub")) != student_id
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 檢查是否已經驗證
    if student.email_verified:
        return {"message": "Email already verified", "verified": True}

    # 檢查是否有 email（且不是系統生成的）
    if not student.email or "@duotopia.local" in student.email:
        raise HTTPException(status_code=400, detail="No valid email to verify")

    # 重新發送
    success = email_service.resend_verification_email(db, student)
    if not success:
        raise HTTPException(
            status_code=429, detail="Please wait 5 minutes before requesting again"
        )

    return {
        "message": "Verification email resent successfully",
        "email": student.email,
        "verification_sent": True,
    }


@router.get("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """驗證 email token"""
    from services.email_service import email_service

    student = email_service.verify_email_token(db, token)
    if not student:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    return {
        "message": "Email 驗證成功",
        "student_name": student.name,
        "email": student.email,
        "verified": True,
    }


@router.get("/{student_id}/email-status")
async def get_email_status(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """獲取 email 驗證狀態"""
    # 確認是學生本人
    if (
        current_user.get("type") != "student"
        or int(current_user.get("sub")) != student_id
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "email": student.email,
        "is_system_email": (
            "@duotopia.local" in student.email if student.email else True
        ),
        "email_verified": student.email_verified,
        "email_verified_at": (
            student.email_verified_at.isoformat() if student.email_verified_at else None
        ),
        "verification_sent_at": (
            student.email_verification_sent_at.isoformat()
            if student.email_verification_sent_at
            else None
        ),
    }


# ========== 班級切換相關 API ==========


@router.get("/{student_id}/linked-accounts")
async def get_linked_accounts(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """獲取相同已驗證 email 的其他學生帳號"""
    # 確認是學生本人
    if (
        current_user.get("type") != "student"
        or int(current_user.get("sub")) != student_id
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 檢查是否有已驗證的 email
    if not student.email or not student.email_verified:
        return {"linked_accounts": [], "message": "No verified email"}

    # 找出所有相同 email 且已驗證的學生帳號
    linked_students = (
        db.query(Student)
        .filter(
            Student.email == student.email,
            Student.email_verified is True,
            Student.id != student_id,  # 排除自己
            Student.is_active is True,
        )
        .all()
    )

    # 建立回應，包含班級資訊
    linked_accounts = []
    for linked_student in linked_students:
        # 取得班級資訊
        classroom_enrollment = (
            db.query(ClassroomStudent)
            .filter(
                ClassroomStudent.student_id == linked_student.id,
                ClassroomStudent.is_active is True,
            )
            .first()
        )

        classroom_info = None
        if classroom_enrollment:
            classroom = (
                db.query(Classroom)
                .filter(Classroom.id == classroom_enrollment.classroom_id)
                .first()
            )
            if classroom:
                classroom_info = {
                    "id": classroom.id,
                    "name": classroom.name,
                    "teacher_name": (
                        classroom.teacher.name if classroom.teacher else None
                    ),
                }

        linked_accounts.append(
            {
                "student_id": linked_student.id,
                "name": linked_student.name,
                "classroom": classroom_info,
                "last_login": (
                    linked_student.last_login.isoformat()
                    if linked_student.last_login
                    else None
                ),
            }
        )

    return {"linked_accounts": linked_accounts, "current_email": student.email}


class SwitchAccountRequest(BaseModel):
    target_student_id: int
    password: str  # 目標帳號的密碼（生日）


@router.post("/switch-account")
async def switch_account(
    request: SwitchAccountRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """切換到另一個已連結的學生帳號"""
    # 確認是學生
    if current_user.get("type") != "student":
        raise HTTPException(status_code=403, detail="Only students can switch accounts")

    current_student_id = int(current_user.get("sub"))
    current_student = db.query(Student).filter(Student.id == current_student_id).first()

    if not current_student:
        raise HTTPException(status_code=404, detail="Current student not found")

    # 檢查當前帳號是否有已驗證的 email
    if not current_student.email or not current_student.email_verified:
        raise HTTPException(
            status_code=400, detail="Current account has no verified email"
        )

    # 查找目標學生
    target_student = (
        db.query(Student).filter(Student.id == request.target_student_id).first()
    )

    if not target_student:
        raise HTTPException(status_code=404, detail="Target student not found")

    # 檢查目標學生是否有相同的已驗證 email
    if (
        target_student.email != current_student.email
        or not target_student.email_verified
    ):
        raise HTTPException(status_code=403, detail="Target account is not linked")

    # 驗證目標帳號的密碼
    if not verify_password(request.password, target_student.password_hash):
        raise HTTPException(
            status_code=401, detail="Invalid password for target account"
        )

    # 更新最後登入時間
    target_student.last_login = datetime.now()
    db.commit()

    # 建立新的 JWT token
    access_token = create_access_token(
        data={"sub": str(target_student.id), "type": "student"},
        expires_delta=timedelta(minutes=30),
    )

    # 取得班級資訊
    classroom_enrollment = (
        db.query(ClassroomStudent)
        .filter(
            ClassroomStudent.student_id == target_student.id,
            ClassroomStudent.is_active is True,
        )
        .first()
    )

    classroom_info = None
    if classroom_enrollment:
        classroom = (
            db.query(Classroom)
            .filter(Classroom.id == classroom_enrollment.classroom_id)
            .first()
        )
        if classroom:
            classroom_info = {"id": classroom.id, "name": classroom.name}

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": target_student.id,
            "name": target_student.name,
            "email": target_student.email,
            "classroom": classroom_info,
        },
        "message": "Successfully switched to target account",
    }


@router.delete("/{student_id}/email-binding")
async def unbind_email(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """解除 email 綁定（學生自己或老師都可以操作）"""
    # 檢查權限：學生本人或老師
    is_student_self = (
        current_user.get("type") == "student"
        and int(current_user.get("sub")) == student_id
    )
    is_teacher = current_user.get("type") == "teacher"

    if not is_student_self and not is_teacher:
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 如果是老師，檢查學生是否在老師的班級中
    if is_teacher:
        teacher_id = int(current_user.get("sub"))
        # 檢查學生是否在該老師的任何班級中
        student_in_teacher_class = (
            db.query(ClassroomStudent)
            .join(Classroom)
            .filter(
                ClassroomStudent.student_id == student_id,
                Classroom.teacher_id == teacher_id,
                ClassroomStudent.is_active is True,
            )
            .first()
        )
        if not student_in_teacher_class:
            raise HTTPException(
                status_code=403, detail="Student is not in your classroom"
            )

    # 清除 email 綁定相關資訊
    old_email = student.email
    student.email = None
    student.email_verified = False
    student.email_verified_at = None
    student.email_verification_token = None
    student.email_verification_sent_at = None

    db.commit()

    return {
        "message": "Email binding removed successfully",
        "student_id": student_id,
        "old_email": old_email,
        "removed_by": "teacher" if is_teacher else "student",
    }
