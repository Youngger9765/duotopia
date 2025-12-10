from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional, List, Dict, Any  # noqa: F401
from datetime import datetime, timedelta, timezone  # noqa: F401
from decimal import Decimal
import json
import logging
from database import get_db, get_session_local
from models import (
    Student,
    Classroom,
    ClassroomStudent,
    StudentAssignment,
    Content,
    ContentItem,
    StudentItemProgress,
    AssignmentStatus,
    AssignmentContent,
    StudentContentProgress,
)
from auth import (
    create_access_token,
    verify_password,
    get_current_user,
    get_password_hash,
    validate_password_strength,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/students", tags=["students"])


def get_score_with_fallback(
    item_progress,
    field_name: str,
    json_key: str,
    db: Session,
    ai_feedback_data: dict = None,
) -> float:
    """
    Get score from independent field or ai_feedback JSON with automatic backfill.

    This handles migration from old data (scores in JSON) to new schema (independent fields).
    If score is NULL in field but exists in JSON, it backfills the field on-the-fly.

    Args:
        item_progress: StudentItemProgress instance
        field_name: Database field name (e.g., 'completeness_score')
        json_key: JSON key in ai_feedback (e.g., 'completeness_score')
        db: Database session for backfill commit
        ai_feedback_data: Parsed ai_feedback dict (optimization to avoid re-parsing)

    Returns:
        float: Score value (0 if not found in either location)
    """
    score = getattr(item_progress, field_name)

    # If field has value, return it
    if score is not None:
        return float(score)

    # Field is NULL - try fallback to JSON
    if not item_progress.ai_feedback:
        return 0.0

    # Parse JSON if not already provided
    if ai_feedback_data is None:
        try:
            ai_feedback_data = (
                json.loads(item_progress.ai_feedback)
                if isinstance(item_progress.ai_feedback, str)
                else item_progress.ai_feedback
            )
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(
                f"Failed to parse ai_feedback JSON for item_progress {item_progress.id}: {e}"
            )
            return 0.0

    # Try to get score from JSON
    json_score = ai_feedback_data.get(json_key)
    if json_score is None:
        return 0.0

    # Found score in JSON - backfill the database field
    try:
        setattr(item_progress, field_name, Decimal(str(json_score)))
        db.commit()
        logger.info(
            f"Backfilled {field_name}={json_score} for item_progress {item_progress.id} from ai_feedback JSON"
        )
        return float(json_score)
    except Exception as e:
        logger.error(
            f"Failed to backfill {field_name} for item_progress {item_progress.id}: {e}"
        )
        db.rollback()
        # Return the JSON value even if backfill failed
        return float(json_score)


class StudentValidateRequest(BaseModel):
    email: str
    password: str  # Can be birthdate (YYYYMMDD) or new password if changed


class StudentLoginResponse(BaseModel):
    access_token: str
    token_type: str
    student: dict


class UpdateStudentProfileRequest(BaseModel):
    name: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class SubmitAssignmentRequest(BaseModel):
    """Assignment submission request"""

    answers: Optional[List[Dict[str, Any]]] = []


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
    # 🔥 Fix Issue #34: 只顯示已開始的作業（assigned_at <= 當前時間）
    current_time = datetime.now(timezone.utc)

    assignments = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.student_id == int(student_id),
            StudentAssignment.assigned_at <= current_time,  # 🔥 只顯示已開始的作業
        )
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

    if student_assignment.assignment_id:
        # 直接查詢這個學生作業的所有進度記錄（這才是正確的數據源）
        progress_records = (
            db.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id == student_assignment.id
            )
            .order_by(StudentContentProgress.order_index)
            .all()
        )

        # 如果沒有 progress_records，自動創建
        if not progress_records:
            # 獲取作業的所有 assignment_contents
            assignment_contents = (
                db.query(AssignmentContent)
                .filter(
                    AssignmentContent.assignment_id == student_assignment.assignment_id
                )
                .order_by(AssignmentContent.order_index)
                .all()
            )

            # 🔥 批次查詢所有 ContentItem (避免 N+1)
            content_ids = [ac.content_id for ac in assignment_contents]
            all_content_items = (
                db.query(ContentItem)
                .filter(ContentItem.content_id.in_(content_ids))
                .order_by(ContentItem.content_id, ContentItem.order_index)
                .all()
            )
            # 建立 content_id -> [items] 的索引
            content_items_map = {}
            for item in all_content_items:
                if item.content_id not in content_items_map:
                    content_items_map[item.content_id] = []
                content_items_map[item.content_id].append(item)

            # 為每個 assignment_content 創建 StudentContentProgress
            for idx, ac in enumerate(assignment_contents):
                progress = StudentContentProgress(
                    student_assignment_id=student_assignment.id,
                    content_id=ac.content_id,
                    status=AssignmentStatus.NOT_STARTED,
                    order_index=idx,
                )
                db.add(progress)
                progress_records.append(progress)

                # 🔥 使用預載入的 ContentItem (避免 N+1)
                content_items = content_items_map.get(ac.content_id, [])

                for item in content_items:
                    item_progress = StudentItemProgress(
                        student_assignment_id=student_assignment.id,
                        content_item_id=item.id,
                        status="NOT_STARTED",
                    )
                    db.add(item_progress)

            # 提交到資料庫
            db.commit()

            # 重新查詢以獲取 ID
            progress_records = (
                db.query(StudentContentProgress)
                .filter(
                    StudentContentProgress.student_assignment_id
                    == student_assignment.id
                )
                .order_by(StudentContentProgress.order_index)
                .all()
            )

        # 優化：批次查詢所有 content，避免 N+1 問題
        content_ids = [progress.content_id for progress in progress_records]
        contents = db.query(Content).filter(Content.id.in_(content_ids)).all()
        content_dict = {content.id: content for content in contents}

        # 🔥 優化：預先批次查詢所有 ContentItems 和 StudentItemProgress
        # 避免在循環中對每個 content 都查詢一次（N+1 問題）
        all_content_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id.in_(content_ids))
            .order_by(ContentItem.content_id, ContentItem.order_index)
            .all()
        )

        # 建立 content_id -> [items] 的索引
        content_items_map = {}
        for ci in all_content_items:
            if ci.content_id not in content_items_map:
                content_items_map[ci.content_id] = []
            content_items_map[ci.content_id].append(ci)

        # 批次查詢所有 StudentItemProgress
        all_item_progress = (
            db.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == student_assignment.id)
            .all()
        )

        # 建立 content_item_id -> progress 的索引
        progress_by_item = {p.content_item_id: p for p in all_item_progress}

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

                # 🔥 優化：從預先載入的 map 取得 ContentItems（不再查詢資料庫）
                content_items = content_items_map.get(content.id, [])

                if content_items:
                    # 使用 ContentItem 記錄（每個都有 ID）
                    items_with_ids = []
                    for ci in content_items:
                        item_progress = progress_by_item.get(ci.id)
                        item_data = {
                            "id": ci.id,  # ContentItem 的 ID！
                            "text": ci.text,
                            "translation": ci.translation,
                            "audio_url": ci.audio_url,
                            "order_index": ci.order_index,
                        }

                        # 如果有 progress 記錄，加入 AI 評估資料
                        if item_progress:
                            item_data["recording_url"] = item_progress.recording_url
                            item_data["status"] = item_progress.status
                            item_data[
                                "progress_id"
                            ] = item_progress.id  # 🔥 返回 progress_id 給前端用於批次分析

                            # 加入老師評語相關資料
                            item_data[
                                "teacher_feedback"
                            ] = item_progress.teacher_feedback
                            item_data["teacher_passed"] = item_progress.teacher_passed
                            item_data["teacher_review_score"] = (
                                float(item_progress.teacher_review_score)
                                if item_progress.teacher_review_score
                                else None
                            )
                            item_data["teacher_reviewed_at"] = (
                                item_progress.teacher_reviewed_at.isoformat()
                                if item_progress.teacher_reviewed_at
                                else None
                            )
                            item_data["review_status"] = item_progress.review_status

                            if item_progress.has_ai_assessment:
                                # 🔥 優化：核心分數從獨立欄位讀取（熱數據），冷數據從 JSON 讀取
                                # Parse ai_feedback JSON once for efficiency
                                ai_feedback_data = {}
                                if item_progress.ai_feedback:
                                    try:
                                        ai_feedback_data = (
                                            json.loads(item_progress.ai_feedback)
                                            if isinstance(
                                                item_progress.ai_feedback, str
                                            )
                                            else item_progress.ai_feedback
                                        )
                                    except (json.JSONDecodeError, TypeError):
                                        ai_feedback_data = {}

                                # 核心分數從獨立欄位讀取（優化性能），自動 fallback 到 JSON 並回填
                                item_data["ai_assessment"] = {
                                    "accuracy_score": get_score_with_fallback(
                                        item_progress,
                                        "accuracy_score",
                                        "accuracy_score",
                                        db,
                                        ai_feedback_data,
                                    ),
                                    "fluency_score": get_score_with_fallback(
                                        item_progress,
                                        "fluency_score",
                                        "fluency_score",
                                        db,
                                        ai_feedback_data,
                                    ),
                                    "pronunciation_score": get_score_with_fallback(
                                        item_progress,
                                        "pronunciation_score",
                                        "pronunciation_score",
                                        db,
                                        ai_feedback_data,
                                    ),
                                    "completeness_score": get_score_with_fallback(
                                        item_progress,
                                        "completeness_score",
                                        "completeness_score",
                                        db,
                                        ai_feedback_data,
                                    ),
                                    # 冷數據從 JSON 讀取
                                    "prosody_score": ai_feedback_data.get(
                                        "prosody_score"
                                    ),
                                    "word_details": ai_feedback_data.get(
                                        "word_details", []
                                    ),
                                    "detailed_words": ai_feedback_data.get(
                                        "detailed_words", []
                                    ),
                                    "reference_text": ai_feedback_data.get(
                                        "reference_text", ""
                                    ),
                                    "recognized_text": ai_feedback_data.get(
                                        "recognized_text", ""
                                    ),
                                    "analysis_summary": ai_feedback_data.get(
                                        "analysis_summary", {}
                                    ),
                                    "ai_feedback": item_progress.ai_feedback,
                                    "assessed_at": item_progress.ai_assessed_at.isoformat()
                                    if item_progress.ai_assessed_at
                                    else None,
                                }

                        items_with_ids.append(item_data)

                    activity_data["items"] = items_with_ids
                    activity_data["item_count"] = len(items_with_ids)
                else:
                    # 沒有 ContentItem 記錄的情況 - 返回空陣列
                    print(f"Warning: Content {content.id} has no ContentItem records")
                    activity_data["items"] = []
                    activity_data["item_count"] = 0

                # 如果完全沒有項目，提供一個空的預設項目
                if not activity_data.get("items"):
                    single_item = {
                        "text": "",
                        "translation": "",
                    }
                    activity_data["items"] = [single_item]
                    activity_data["item_count"] = 1

                activity_data["content"] = ""
                activity_data["target_text"] = ""

                # 現在統一使用 StudentItemProgress 的資料，不再從 response_data 讀取
                # recordings 和 AI 評分都應該從 items 的 recording_url 和 ai_assessment 取得
                # 保留這些空陣列只是為了向後相容，未來應該移除
                activity_data["recordings"] = []
                activity_data["answers"] = (
                    progress.response_data.get("answers", [])
                    if progress.response_data
                    else []
                )
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
        "status": student_assignment.status.value,  # 返回作業狀態
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


def calculate_assignment_score(
    student_assignment_id: int, db: Session
) -> Optional[float]:
    """
    Calculate assignment total score from StudentItemProgress AI scores

    Logic (per Issue #53):
    1. For each item: item_score = (accuracy + fluency + pronunciation) / available_count
    2. For assignment: total_score = sum(all_item_scores) / total_items
    3. If item has no AI scores: count as 0
    4. If no items exist: return None

    Args:
        student_assignment_id: StudentAssignment ID
        db: Database session

    Returns:
        Calculated score (0-100) or None if cannot calculate
    """
    # Get all item progress records
    items = (
        db.query(StudentItemProgress)
        .filter(StudentItemProgress.student_assignment_id == student_assignment_id)
        .all()
    )

    if not items:
        return None  # No items, cannot calculate

    # Calculate each item's score
    item_scores = []
    for item in items:
        # Use the overall_score property which handles partial scores
        if item.overall_score is not None:
            item_scores.append(float(item.overall_score))
        else:
            # No AI scores, count as 0 (per Issue #53 requirement)
            item_scores.append(0.0)

    # Calculate average of all item scores
    total_score = sum(item_scores) / len(item_scores)

    # Clamp score to valid range [0, 100]
    total_score = max(0.0, min(100.0, total_score))

    return round(total_score, 2)


# Removed Cloud Tasks scheduling - submissions now only upload audio without executing analysis


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    request: SubmitAssignmentRequest = SubmitAssignmentRequest(),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交作業（只儲存，不執行分析）"""
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

    # 🔥 Fix Issue #58: 判斷是否為訂正後提交
    # 如果當前狀態是 RETURNED (待訂正)，提交後應該是 RESUBMITTED (已訂正)
    # 否則就是第一次提交，狀態為 SUBMITTED (已提交)
    if student_assignment.status == AssignmentStatus.RETURNED:
        student_assignment.status = AssignmentStatus.RESUBMITTED
        student_assignment.resubmitted_at = datetime.now(timezone.utc)
    else:
        student_assignment.status = AssignmentStatus.SUBMITTED
        student_assignment.submitted_at = datetime.now(timezone.utc)

    # 🆕 Auto-calculate score from StudentItemProgress AI scores (Issue #53)
    calculated_score = calculate_assignment_score(student_assignment.id, db)
    if calculated_score is not None:
        student_assignment.score = calculated_score

    db.commit()

    return {
        "message": "Assignment submitted successfully",
        "submitted_at": student_assignment.submitted_at.isoformat(),
        "score": student_assignment.score,  # Include calculated score in response
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


@router.put("/me")
async def update_student_profile(
    request: UpdateStudentProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新學生個人資料"""
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

    # Update name if provided
    if request.name is not None:
        student.name = request.name

    db.commit()
    db.refresh(student)

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


@router.put("/me/password")
async def update_student_password(
    request: UpdatePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新學生密碼"""
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

    # Verify current password
    if not verify_password(request.current_password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Check if new password is same as current password
    if verify_password(request.new_password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Validate new password strength (same as registration)
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Update password
    student.password_hash = get_password_hash(request.new_password)
    student.password_changed = True  # Mark that password has been changed
    db.commit()

    return {"message": "Password updated successfully"}


@router.get("/stats")
async def get_student_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current student statistics for dashboard"""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    student_id = current_user.get("sub")

    # Calculate completed assignments (GRADED status)
    completed_count = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.student_id == int(student_id),
            StudentAssignment.status == AssignmentStatus.GRADED,
        )
        .count()
    )

    # Calculate average score from graded assignments
    graded_assignments = (
        db.query(StudentAssignment.score)
        .filter(
            StudentAssignment.student_id == int(student_id),
            StudentAssignment.status == AssignmentStatus.GRADED,
            StudentAssignment.score.isnot(None),
        )
        .all()
    )

    average_score = 0
    if graded_assignments:
        total_scores = [
            score[0] for score in graded_assignments if score[0] is not None
        ]
        if total_scores:
            average_score = round(sum(total_scores) / len(total_scores))

    # Calculate total practice time (sum of all submitted assignments' durations)
    # For now, estimate based on number of submissions (10 min per assignment)
    submitted_count = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.student_id == int(student_id),
            StudentAssignment.status.in_(
                [
                    AssignmentStatus.SUBMITTED,
                    AssignmentStatus.GRADED,
                    AssignmentStatus.RESUBMITTED,
                ]
            ),
        )
        .count()
    )
    total_practice_time = submitted_count * 10  # 10 minutes per assignment

    # Calculate practice days (累積練習天數 - 有幾天有練習過)
    # Count distinct dates where student submitted assignments
    from sqlalchemy import func, cast, Date

    practice_days_result = (
        db.query(func.count(func.distinct(cast(StudentAssignment.submitted_at, Date))))
        .filter(
            StudentAssignment.student_id == int(student_id),
            StudentAssignment.submitted_at.isnot(None),
        )
        .scalar()
    )
    practice_days = practice_days_result or 0

    return {
        "completedAssignments": completed_count,
        "averageScore": average_score,
        "totalPracticeTime": total_practice_time,
        "practiceDays": practice_days,  # 累積練習天數
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
    assignment_id: int = Form(...),  # StudentAssignment ID
    content_item_id: int = Form(...),  # ContentItem ID (最關鍵的簡化)
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上傳學生錄音到 Google Cloud Storage (支援重新錄製)

    CRITICAL FIX: Release DB connection before GCS upload to prevent pool exhaustion.
    This function is split into 3 phases:
    1. Quick DB query to get necessary data
    2. Release DB connection, upload to GCS (2-5 seconds)
    3. Acquire new DB connection, update database
    """
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

        # ============ PHASE 1: Quick DB query (connection held) ============
        try:
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

            # 直接用 content_item_id 查詢
            content_item = (
                db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
            )

            if not content_item:
                raise HTTPException(
                    status_code=404,
                    detail=f"Content item not found with id {content_item_id}",
                )

            # 查找現有的 StudentItemProgress 記錄以獲取舊 URL
            existing_item_progress = (
                db.query(StudentItemProgress)
                .filter(
                    StudentItemProgress.student_assignment_id == assignment_id,
                    StudentItemProgress.content_item_id == content_item.id,
                )
                .first()
            )

            # CRITICAL: Extract ALL needed values as primitives BEFORE db.close()
            # After db.close(), ORM objects become detached and cannot access lazy-loaded attributes
            old_audio_url = None
            if existing_item_progress and existing_item_progress.recording_url:
                old_audio_url = existing_item_progress.recording_url

            # Extract primitive values from ORM objects
            content_id_value = content_item.content_id
            content_item_id_value = content_item.id

        except HTTPException:
            # FIX #1: Close DB connection on validation errors
            db.close()
            raise
        except Exception as e:
            # FIX #1: Close DB connection on unexpected errors
            db.close()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        # ============ PHASE 2: Release DB connection, upload to GCS ============
        # CRITICAL: Close DB connection BEFORE slow GCS upload (2-5 seconds)
        # WARNING: After this point, do NOT access ORM objects from Phase 1
        #          All data must be extracted as primitives above
        db.close()

        try:
            # 上傳新錄音（不傳 content_id 和 item_index，讓它用 UUID）
            # This operation takes 2-5 seconds but NO LONGER blocks DB connections
            audio_url = await audio_service.upload_audio(
                audio_file,
                duration_seconds=30,  # 預設 30 秒
                assignment_id=assignment_id,
                student_id=student_id,
            )
        except Exception as upload_error:
            # If GCS upload fails, don't update database
            print(f"GCS upload failed: {upload_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload recording to cloud storage: {str(upload_error)}",
            )

        # 刪除舊錄音檔案（如果存在且不同）
        # This is async operation that doesn't require DB connection
        if old_audio_url and old_audio_url != audio_url:
            try:
                audio_manager.delete_old_audio(old_audio_url)
                print(f"Deleted old student recording: {old_audio_url}")
            except Exception as e:
                print(f"Failed to delete old recording: {e}")

        # ============ PHASE 3: Acquire new DB connection, update database ============
        # Create a new DB session for database updates
        SessionLocal = get_session_local()
        db_new = SessionLocal()

        try:
            # Re-query the existing progress record (must use new session)
            # FIX #3: Add row-level locking to prevent concurrent update race conditions
            existing_item_progress = (
                db_new.query(StudentItemProgress)
                .filter(
                    StudentItemProgress.student_assignment_id == assignment_id,
                    StudentItemProgress.content_item_id == content_item_id_value,
                )
                .with_for_update()  # SELECT FOR UPDATE - blocks concurrent updates
                .first()
            )

            # 更新或創建 StudentItemProgress 記錄
            if existing_item_progress:
                # 更新現有記錄
                existing_item_progress.recording_url = audio_url
                # FIX #6: Replace deprecated datetime.utcnow() with timezone-aware version
                existing_item_progress.submitted_at = datetime.now(timezone.utc)
                existing_item_progress.status = "COMPLETED"

                # 同時清除舊的 AI 分數，因為分數對應的是舊錄音
                if old_audio_url:
                    existing_item_progress.accuracy_score = None
                    existing_item_progress.fluency_score = None
                    existing_item_progress.pronunciation_score = None
                    existing_item_progress.completeness_score = None
                    existing_item_progress.ai_feedback = None
                    existing_item_progress.ai_assessed_at = None
                    print("Cleared AI scores for re-recording")

                print(
                    f"Updated existing item progress record: {existing_item_progress.id}"
                )
                current_item_progress = existing_item_progress
            else:
                # 創建新記錄
                new_item_progress = StudentItemProgress(
                    student_assignment_id=assignment_id,
                    content_item_id=content_item_id_value,
                    recording_url=audio_url,
                    # FIX #6: Replace deprecated datetime.utcnow() with timezone-aware version
                    submitted_at=datetime.now(timezone.utc),
                    status="COMPLETED",
                )
                db_new.add(new_item_progress)
                print("Created new item progress record")
                current_item_progress = new_item_progress

            # 更新或創建摘要統計 (StudentContentProgress)
            summary_progress = (
                db_new.query(StudentContentProgress)
                .filter(
                    StudentContentProgress.student_assignment_id == assignment_id,
                    StudentContentProgress.content_id == content_id_value,
                )
                .first()
            )

            if not summary_progress:
                summary_progress = StudentContentProgress(
                    student_assignment_id=assignment_id,
                    content_id=content_id_value,
                    order_index=0,  # 摘要記錄使用 0
                    status=AssignmentStatus.IN_PROGRESS,
                )
                db_new.add(summary_progress)

            # 更新 StudentContentProgress 狀態
            summary_progress.status = AssignmentStatus.IN_PROGRESS

            db_new.commit()

            # 重新查詢以取得 ID（因為新記錄需要 commit 後才有 ID）
            db_new.refresh(current_item_progress)

            progress_id = current_item_progress.id

        except Exception as db_error:
            db_new.rollback()

            # FIX #4: Best-effort cleanup of orphaned GCS file
            # If Phase 3 fails, audio file is uploaded but not recorded in DB
            if audio_url:
                try:
                    audio_manager.delete_old_audio(audio_url)
                    logger.warning(
                        f"Cleaned up orphaned GCS file after DB error: {audio_url}"
                    )
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup orphaned file: {cleanup_error}")

            print(f"Database update failed after GCS upload: {db_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Recording uploaded but database update failed: {str(db_error)}",
            )
        finally:
            db_new.close()

        return {
            "audio_url": audio_url,
            "assignment_id": assignment_id,
            "content_item_id": content_item_id,
            "progress_id": progress_id,  # 🔥 新增：回傳 progress_id 給前端使用
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

    # 🔥 優化：批次查詢所有 linked students 的 classroom 資訊（避免 N+1）
    linked_student_ids = [s.id for s in linked_students]

    # 批次查詢所有 ClassroomStudent 關係
    classroom_enrollments = (
        db.query(ClassroomStudent)
        .filter(
            ClassroomStudent.student_id.in_(linked_student_ids),
            ClassroomStudent.is_active is True,
        )
        .all()
    )

    # 建立 student_id -> classroom_id 的索引
    student_classroom_map = {
        ce.student_id: ce.classroom_id for ce in classroom_enrollments
    }

    # 批次查詢所有 Classroom（包含 teacher 關係）
    classroom_ids = list(set(student_classroom_map.values()))

    classrooms = (
        db.query(Classroom)
        .options(joinedload(Classroom.teacher))  # 🔥 eager load teacher
        .filter(Classroom.id.in_(classroom_ids))
        .all()
    )

    # 建立 classroom_id -> classroom 的索引
    classroom_map = {c.id: c for c in classrooms}

    # 建立回應，包含班級資訊
    linked_accounts = []
    for linked_student in linked_students:
        # 🔥 從預先載入的 map 取得 classroom 資訊（不再查詢資料庫）
        classroom_id = student_classroom_map.get(linked_student.id)
        classroom = classroom_map.get(classroom_id) if classroom_id else None

        classroom_info = None
        if classroom:
            classroom_info = {
                "id": classroom.id,
                "name": classroom.name,
                "teacher_name": (classroom.teacher.name if classroom.teacher else None),
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
