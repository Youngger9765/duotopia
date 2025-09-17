from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any  # noqa: F401
from datetime import datetime, timedelta  # noqa: F401
from database import get_db
from models import (
    Student,
    Classroom,
    ClassroomStudent,
    StudentAssignment,
    Content,
    ContentItem,
    StudentItemProgress,
    AssignmentStatus,
    # AssignmentContent,
    StudentContentProgress,
)
from auth import (
    create_access_token,
    verify_password,
    get_current_user,
)

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
        "student_id": student.student_number,
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
            # 獲取內容項目
            content_items = (
                db.query(ContentItem)
                .filter(ContentItem.content_id == content.id)
                .order_by(ContentItem.order_index)
                .all()
            )

            # 獲取學生的項目進度
            item_progress_list = (
                db.query(StudentItemProgress)
                .filter(StudentItemProgress.student_assignment_id == student_assignment.id)
                .all()
            )
            
            # 建立進度索引 (content_item_id -> progress)
            progress_by_item = {p.content_item_id: p for p in item_progress_list}

            # 轉換為前端格式
            items = []
            for item in content_items:
                progress = progress_by_item.get(item.id)
                
                item_data = {
                    "text": item.text,
                    "translation": item.translation,
                    "audio_url": item.audio_url,
                    "order_index": item.order_index,
                    "status": progress.status if progress else "NOT_STARTED",
                    "recording_url": progress.recording_url if progress else None,
                    "accuracy_score": float(progress.accuracy_score) if progress and progress.accuracy_score else None,
                    "fluency_score": float(progress.fluency_score) if progress and progress.fluency_score else None,
                    "pronunciation_score": float(progress.pronunciation_score) if progress and progress.pronunciation_score else None,
                    "ai_feedback": progress.ai_feedback if progress else None,
                    "submitted_at": progress.submitted_at.isoformat() if progress and progress.submitted_at else None,
                    "ai_assessed_at": progress.ai_assessed_at.isoformat() if progress and progress.ai_assessed_at else None
                }
                items.append(item_data)

            # 檢查或創建摘要統計
            summary_progress = (
                db.query(StudentContentProgress)
                .filter(
                    StudentContentProgress.student_assignment_id == student_assignment.id,
                    StudentContentProgress.content_id == content.id,
                )
                .first()
            )

            if not summary_progress:
                summary_progress = StudentContentProgress(
                    student_assignment_id=student_assignment.id,
                    content_id=content.id,
                    order_index=0,
                    total_items=len(content_items),
                    completed_items=0,
                    completion_rate=0.0,
                    status=AssignmentStatus.NOT_STARTED,
                )
                db.add(summary_progress)
                db.commit()
                db.refresh(summary_progress)

            activities.append(
                {
                    "id": summary_progress.id,
                    "content_id": content.id,
                    "order": 1,
                    "type": (
                        content.type.value if content.type else "reading_assessment"
                    ),
                    "title": content.title,
                    "items": items,  # New structured format
                    "content": items,  # Backward compatibility
                    "target_text": items,  # For reading assessment
                    "duration": 60,  # Default duration
                    "points": 100,
                    "status": (
                        summary_progress.status.value if summary_progress.status else "NOT_STARTED"
                    ),
                    "score": summary_progress.score,
                    "completion_rate": summary_progress.completion_rate,
                    "completed_items": summary_progress.completed_items,
                    "total_items": summary_progress.total_items,
                    "completed_at": (
                        summary_progress.completed_at.isoformat()
                        if summary_progress.completed_at
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

        # 優化：批次查詢所有 content，避免 N+1 問題
        content_ids = [progress.content_id for progress in progress_records]
        contents = db.query(Content).filter(Content.id.in_(content_ids)).all()
        content_dict = {content.id: content for content in contents}

        for progress in progress_records:
            content = content_dict.get(progress.content_id)

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
                    "points": (
                        100 // len(progress_records)
                        if len(progress_records) > 0
                        else 100
                    ),  # 平均分配分數
                    "status": (
                        progress.status.value if progress.status else "NOT_STARTED"
                    ),
                    "score": progress.score,
                    "completed_at": (
                        progress.completed_at.isoformat()
                        if progress.completed_at
                        else None
                    ),
                    # AI 評估結果現在統一在 activity_data["ai_assessments"] 陣列中處理
                }

                # 統一處理所有情況為多題目模式（陣列模式）
                if (
                    content.items
                    and isinstance(content.items, list)
                    and len(content.items) > 0
                ):
                    # 多題目情況
                    activity_data["items"] = content.items
                    activity_data["item_count"] = len(content.items)
                    activity_data["content"] = ""
                    activity_data["target_text"] = ""
                else:
                    # 單題目情況 - 也統一為陣列模式
                    single_item = {
                        "text": str(content.items) if content.items else "",
                        "translation": "",
                    }
                    activity_data["items"] = [single_item]
                    activity_data["item_count"] = 1
                    activity_data["content"] = ""
                    activity_data["target_text"] = ""

                # 統一處理錄音和 AI 評分（一律使用陣列模式）
                if progress.response_data:
                    # 處理錄音
                    recordings = progress.response_data.get("recordings", [])
                    audio_url = progress.response_data.get("audio_url")

                    # 如果是舊格式的 audio_url，轉換為陣列格式
                    if audio_url and not recordings:
                        recordings = [audio_url]

                    activity_data["recordings"] = recordings
                    activity_data["answers"] = progress.response_data.get("answers", [])

                    # 處理 AI 評分 - 統一從 response_data 中讀取陣列格式
                    ai_assessments = progress.response_data.get("ai_assessments", [])
                    activity_data["ai_assessments"] = ai_assessments
                else:
                    # 沒有 response_data 的情況
                    activity_data["recordings"] = []
                    activity_data["answers"] = []
                    activity_data["ai_assessments"] = []

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
    recordings: Optional[List[str]] = None,
    answers: Optional[List[str]] = None,
    user_answers: Optional[List[str]] = None,
    item_index: Optional[int] = None,
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

    # 更新進度 - 使用 response_data JSON 欄位儲存所有資料
    if not progress.response_data:
        progress.response_data = {}

    # 更新各種類型的資料
    if audio_url:
        progress.response_data["audio_url"] = audio_url
    if text_answer:
        progress.response_data["text_answer"] = text_answer
    if recordings:
        progress.response_data["recordings"] = recordings
    if answers:
        progress.response_data["answers"] = answers
    if user_answers:
        progress.response_data["user_answers"] = user_answers
    if item_index is not None:
        progress.response_data["item_index"] = item_index

    # 標記 JSON 欄位已修改，確保 SQLAlchemy 偵測到變更
    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(progress, "response_data")

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
        "student_id": student.student_number,
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


@router.post("/upload-recording")
async def upload_student_recording(
    assignment_id: int = Form(...),
    content_item_index: int = Form(...),
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上傳學生錄音到 Google Cloud Storage (支援重新錄製)"""
    try:
        from services.audio_upload import get_audio_upload_service
        from services.audio_manager import get_audio_manager

        audio_service = get_audio_upload_service()
        audio_manager = get_audio_manager()

        # 驗證學生身份
        if current_user.get("type") != "student":
            raise HTTPException(
                status_code=403, detail="Only students can upload recordings"
            )

        student_id = int(current_user.get("sub"))

        # 驗證作業存在且屬於該學生
        assignment = (
            db.query(StudentAssignment)
            .filter(
                StudentAssignment.id == assignment_id,
                StudentAssignment.student_id == student_id,
            )
            .first()
        )
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # 找到對應的 ContentItem
        if not assignment.content_id:
            raise HTTPException(status_code=400, detail="Assignment has no content assigned")
            
        content_item = (
            db.query(ContentItem)
            .filter(
                ContentItem.content_id == assignment.content_id,
                ContentItem.order_index == content_item_index
            )
            .first()
        )
        
        if not content_item:
            raise HTTPException(
                status_code=404,
                detail=f"Content item not found for index {content_item_index}"
            )

        # 查找現有的 StudentItemProgress 記錄以獲取舊 URL
        existing_item_progress = (
            db.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id == assignment_id,
                StudentItemProgress.content_item_id == content_item.id
            )
            .first()
        )

        # 檢查是否有舊錄音需要刪除
        old_audio_url = None
        if existing_item_progress and existing_item_progress.recording_url:
            old_audio_url = existing_item_progress.recording_url

        # 上傳新錄音（不傳 content_id 和 item_index，讓它用 UUID）
        audio_url = await audio_service.upload_audio(
            audio_file, duration_seconds=30  # 預設 30 秒
        )

        # 刪除舊錄音檔案（如果存在且不同）
        if old_audio_url and old_audio_url != audio_url:
            try:
                audio_manager.delete_old_audio(old_audio_url)
                print(f"Deleted old student recording: {old_audio_url}")

                # 同時清除舊的 AI 分數，因為分數對應的是舊錄音
                if existing_item_progress:
                    existing_item_progress.accuracy_score = None
                    existing_item_progress.fluency_score = None
                    existing_item_progress.pronunciation_score = None
                    existing_item_progress.ai_feedback = None
                    existing_item_progress.ai_assessed_at = None
                    print("Cleared AI scores for re-recording")

            except Exception as e:
                print(f"Failed to delete old recording: {e}")

        # 更新或創建 StudentItemProgress 記錄
        if existing_item_progress:
            # 更新現有記錄
            existing_item_progress.recording_url = audio_url
            existing_item_progress.submitted_at = datetime.utcnow()
            existing_item_progress.status = "COMPLETED"
            print(f"Updated existing item progress record: {existing_item_progress.id}")
        else:
            # 創建新記錄
            new_item_progress = StudentItemProgress(
                student_assignment_id=assignment_id,
                content_item_id=content_item.id,
                recording_url=audio_url,
                submitted_at=datetime.utcnow(),
                status="COMPLETED"
            )
            db.add(new_item_progress)
            print("Created new item progress record")

        # 更新或創建摘要統計 (StudentContentProgress)
        summary_progress = (
            db.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id == assignment_id,
                StudentContentProgress.content_id == assignment.content_id
            )
            .first()
        )
        
        if not summary_progress:
            # 計算總題數
            total_items = db.query(ContentItem).filter(
                ContentItem.content_id == assignment.content_id
            ).count()
            
            summary_progress = StudentContentProgress(
                student_assignment_id=assignment_id,
                content_id=assignment.content_id,
                order_index=0,  # 摘要記錄使用 0
                total_items=total_items,
                completed_items=0,
                completion_rate=0.0
            )
            db.add(summary_progress)
        
        # 更新完成統計
        completed_count = db.query(StudentItemProgress).filter(
            StudentItemProgress.student_assignment_id == assignment_id,
            StudentItemProgress.status.in_(["COMPLETED", "SUBMITTED"])
        ).count()
        
        summary_progress.completed_items = completed_count
        if summary_progress.total_items > 0:
            summary_progress.completion_rate = (completed_count / summary_progress.total_items) * 100
        
        print(f"Updated summary: {completed_count}/{summary_progress.total_items} completed")

        db.commit()

        return {
            "audio_url": audio_url,
            "assignment_id": assignment_id,
            "content_item_index": content_item_index,
            "storage_type": "gcs",
            "message": "Recording uploaded successfully to cloud storage",
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Student upload error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload recording: {str(e)}"
        )


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
