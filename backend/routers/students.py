from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, func, cast, Date, and_
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
    ContentType,
    StudentItemProgress,
    AssignmentStatus,
    AssignmentContent,
    StudentContentProgress,
    PracticeSession,
    PracticeAnswer,
    Assignment,
)
from auth import (
    create_access_token,
    verify_password,
    get_current_user,
    get_password_hash,
    validate_password_strength,
    get_current_student,
    get_current_student_or_teacher,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/students", tags=["students"])


# =============================================================================
# Content Type Compatibility Helpers
# =============================================================================
# 處理新舊 ContentType 的相容性，API 回傳時統一使用新類型：
# - READING_ASSESSMENT (legacy) → EXAMPLE_SENTENCES (new) - 例句集
# - SENTENCE_MAKING (legacy) → VOCABULARY_SET (new) - 單字集


def normalize_content_type_for_response(content_type) -> str:
    """將舊的 ContentType 值轉換為新值（用於 API 回傳）

    🎯 Issue #118: 確保前端顯示正確的內容類型
    - READING_ASSESSMENT → EXAMPLE_SENTENCES
    - SENTENCE_MAKING → VOCABULARY_SET
    """
    # Handle None
    if not content_type:
        return "EXAMPLE_SENTENCES"

    mapping = {
        "READING_ASSESSMENT": "EXAMPLE_SENTENCES",
        "reading_assessment": "EXAMPLE_SENTENCES",
        "SENTENCE_MAKING": "VOCABULARY_SET",
        "sentence_making": "VOCABULARY_SET",
    }
    return mapping.get(content_type, content_type)


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

    # 🎯 Issue #118: 批次查詢 content_type 和 practice_mode
    assignment_ids = [
        a.assignment_id for a in assignments if a.assignment_id is not None
    ]
    content_type_map = {}
    practice_mode_map = {}

    if assignment_ids:
        from sqlalchemy import func as sqla_func

        # 查詢 practice_mode（從 Assignment 表）
        assignment_settings = (
            db.query(Assignment.id, Assignment.practice_mode)
            .filter(Assignment.id.in_(assignment_ids))
            .all()
        )
        practice_mode_map = {row.id: row.practice_mode for row in assignment_settings}

        # 子查詢：每個作業的最小 order_index
        min_order_subq = (
            db.query(
                AssignmentContent.assignment_id,
                sqla_func.min(AssignmentContent.order_index).label("min_order"),
            )
            .filter(AssignmentContent.assignment_id.in_(assignment_ids))
            .group_by(AssignmentContent.assignment_id)
            .subquery()
        )

        # 主查詢：取得第一個內容的 type
        first_contents = (
            db.query(
                AssignmentContent.assignment_id,
                Content.type,
            )
            .join(Content, AssignmentContent.content_id == Content.id)
            .join(
                min_order_subq,
                and_(
                    AssignmentContent.assignment_id == min_order_subq.c.assignment_id,
                    AssignmentContent.order_index == min_order_subq.c.min_order,
                ),
            )
            .all()
        )
        content_type_map = {row.assignment_id: row.type for row in first_contents}

    result = []
    for assignment in assignments:
        # 🎯 Issue #118: 取得並正規化 content_type
        raw_ct = content_type_map.get(assignment.assignment_id)
        normalized_ct = normalize_content_type_for_response(
            raw_ct.value if hasattr(raw_ct, "value") else raw_ct
        )

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
                # 🎯 Issue #118: 新增 content_type 和 practice_mode
                "content_type": normalized_ct,
                "practice_mode": practice_mode_map.get(
                    assignment.assignment_id, "reading"
                ),
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
    assignment_practice_mode = None
    assignment_score_category = None
    assignment_show_answer = False

    if student_assignment.assignment_id:
        # 獲取 Assignment 的 practice_mode 設定
        assignment = (
            db.query(Assignment)
            .filter(Assignment.id == student_assignment.assignment_id)
            .first()
        )
        if assignment:
            assignment_practice_mode = assignment.practice_mode
            assignment_score_category = assignment.score_category
            assignment_show_answer = assignment.show_answer or False
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
                    "type": normalize_content_type_for_response(
                        content.type.value if content.type else "EXAMPLE_SENTENCES"
                    ),
                    "title": content.title,
                    "duration": (
                        assignment.time_limit_per_question
                        if assignment and assignment.time_limit_per_question is not None
                        else 30
                    ),
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

                # 🔧 修復：為 EXAMPLE_SENTENCES 類型添加 example_audio_url（取第一個 item 的 audio_url）
                # 檢查 content type（處理新舊類型）
                is_example_sentences = (
                    content.type
                    in [
                        ContentType.EXAMPLE_SENTENCES,
                        ContentType.READING_ASSESSMENT,
                    ]
                    if content.type
                    else False
                )
                if is_example_sentences and content_items and len(content_items) > 0:
                    first_item = content_items[0]
                    activity_data["example_audio_url"] = first_item.audio_url
                    # 同時設置 content 和 target_text（ReadingAssessmentTemplate 需要）
                    activity_data["content"] = first_item.translation or ""
                    activity_data["target_text"] = first_item.text or ""

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
        "practice_mode": assignment_practice_mode,  # 例句重組/朗讀模式
        "score_category": assignment_score_category,  # 計分類別
        "show_answer": assignment_show_answer,  # 答題結束後是否顯示正確答案
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
    student_assignment_id: int, db: Session, practice_mode: Optional[str] = None
) -> Optional[float]:
    """
    Calculate assignment total score from StudentItemProgress scores

    Logic:
    - For reading mode (Issue #53):
      1. For each item: item_score = (accuracy + fluency + pronunciation) / available_count
      2. For assignment: total_score = sum(all_item_scores) / total_items
      3. If item has no AI scores: count as 0
      4. If no items exist: return None

    - For rearrangement mode:
      1. For each item: use expected_score field
      2. For assignment: total_score = sum(all_expected_scores) / total_items
      3. Round to 1 decimal place

    Args:
        student_assignment_id: StudentAssignment ID
        db: Database session
        practice_mode: Optional practice mode ("reading" or "rearrangement")

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
        # 🆕 rearrangement 模式使用 expected_score
        if practice_mode == "rearrangement":
            # Use expected_score for rearrangement mode
            if item.expected_score is not None:
                item_scores.append(float(item.expected_score))
            else:
                item_scores.append(0.0)
        else:
            # Use the overall_score property which handles partial scores (for reading mode)
            if item.overall_score is not None:
                item_scores.append(float(item.overall_score))
            else:
                # No AI scores, count as 0 (per Issue #53 requirement)
                item_scores.append(0.0)

    # Calculate average of all item scores
    total_score = sum(item_scores) / len(item_scores)

    # Clamp score to valid range [0, 100]
    total_score = max(0.0, min(100.0, total_score))

    # 🆕 rearrangement 模式取到小數第一位
    if practice_mode == "rearrangement":
        return round(total_score, 1)
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

    # 取得父作業以檢查 practice_mode
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == student_assignment.assignment_id)
        .first()
    )

    # 🆕 rearrangement 模式自動完成：跳過 SUBMITTED → RETURNED → RESUBMITTED 階段，直接到 GRADED
    is_rearrangement = assignment and assignment.practice_mode == "rearrangement"
    final_status = (
        AssignmentStatus.GRADED if is_rearrangement else AssignmentStatus.SUBMITTED
    )

    # 更新所有進度為已完成
    progress_records = (
        db.query(StudentContentProgress)
        .filter(StudentContentProgress.student_assignment_id == student_assignment.id)
        .all()
    )

    for progress in progress_records:
        if progress.status == AssignmentStatus.IN_PROGRESS:
            progress.status = final_status
            progress.completed_at = datetime.now()

    # 🔥 Fix Issue #58: 判斷是否為訂正後提交
    # 如果當前狀態是 RETURNED (待訂正)，提交後應該是 RESUBMITTED (已訂正)
    # 否則就是第一次提交，狀態為 SUBMITTED (已提交)
    # 🆕 Fix Issue #107: rearrangement 模式使用 final_status (GRADED) 而非 SUBMITTED
    if student_assignment.status == AssignmentStatus.RETURNED:
        student_assignment.status = AssignmentStatus.RESUBMITTED
        student_assignment.resubmitted_at = datetime.now(timezone.utc)
    else:
        student_assignment.status = (
            final_status  # 🔥 Fix: 使用 final_status 而非寫死 SUBMITTED
        )
        student_assignment.submitted_at = datetime.now(timezone.utc)

    # 🆕 rearrangement 模式：同時設定 graded_at
    if is_rearrangement:
        student_assignment.graded_at = datetime.now()

    # 🆕 Auto-calculate score from StudentItemProgress AI scores (Issue #53)
    # 🆕 傳入 practice_mode 讓函數知道使用哪種計分方式
    calculated_score = calculate_assignment_score(
        student_assignment.id, db, assignment.practice_mode if assignment else None
    )
    if calculated_score is not None:
        student_assignment.score = calculated_score

    db.commit()

    # 根據模式回傳不同訊息
    if is_rearrangement:
        return {
            "message": "Assignment completed successfully",
            "status": "GRADED",
            "submitted_at": student_assignment.submitted_at.isoformat(),
            "graded_at": student_assignment.graded_at.isoformat()
            if student_assignment.graded_at
            else None,
            "score": student_assignment.score,
        }
    else:
        return {
            "message": "Assignment submitted successfully",
            "status": "SUBMITTED",
            "submitted_at": student_assignment.submitted_at.isoformat(),
            "score": student_assignment.score,
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


# ============ 造句練習 Sentence Making Endpoints ============


class PracticeWord(BaseModel):
    """練習單字資料"""

    content_item_id: int
    text: str
    translation: str
    example_sentence: str
    example_sentence_translation: str
    audio_url: Optional[str] = None
    memory_strength: float
    priority_score: float


class PracticeWordsResponse(BaseModel):
    """練習單字回應"""

    session_id: int
    answer_mode: str
    words: List[PracticeWord]


class SubmitAnswerRequest(BaseModel):
    """提交答案請求"""

    content_item_id: int
    is_correct: bool
    time_spent_seconds: int
    answer_data: Dict[str, Any]  # {"selected_words": [...], "attempts": 3}


class SubmitAnswerResponse(BaseModel):
    """提交答案回應"""

    success: bool
    new_memory_strength: float
    next_review_at: Optional[datetime]


class MasteryStatusResponse(BaseModel):
    """達標狀態回應"""

    current_mastery: float
    target_mastery: float
    achieved: bool
    words_mastered: int
    total_words: int


@router.get(
    "/assignments/{student_assignment_id}/practice-words",
    response_model=PracticeWordsResponse,
)
async def get_practice_words(
    student_assignment_id: int,
    user=Depends(get_current_student_or_teacher),
    db: Session = Depends(get_db),
):
    """
    獲取練習題目（10個單字）
    - 根據艾賓浩斯記憶曲線智能選擇單字
    - 優先選擇即將遺忘或從未練習的單字
    - 支援老師預覽模式

    參數：student_assignment_id（不是 assignment_id）
    """

    # 檢查是學生還是老師（user 現在總是 dict）
    is_teacher = user.get("user_type") == "teacher"

    if is_teacher:
        # === 老師預覽模式 ===
        # 老師預覽時，student_assignment_id 其實是 assignment_id（從預覽 URL 來的）
        # 1. 驗證 assignment 存在
        assignment = (
            db.query(Assignment).filter(Assignment.id == student_assignment_id).first()
        )
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # 2. 獲取 assignment 的 content_items（不使用記憶曲線，直接返回所有單字）
        result = db.execute(
            text(
                """
                SELECT DISTINCT
                    ci.id as content_item_id,
                    ci.text,
                    ci.translation,
                    ci.example_sentence,
                    ci.example_sentence_translation,
                    ci.audio_url
                FROM assignment_contents ac
                JOIN contents c ON c.id = ac.content_id
                JOIN content_items ci ON ci.content_id = c.id
                WHERE ac.assignment_id = :assignment_id
                AND c.type = 'VOCABULARY_SET'
                LIMIT 10
            """
            ),
            {"assignment_id": student_assignment_id},
        )

        words = []
        for row in result:
            words.append(
                PracticeWord(
                    content_item_id=row[0],
                    text=row[1] or "",
                    translation=row[2] or "",
                    example_sentence=row[3] or "",
                    example_sentence_translation=row[4] or "",
                    audio_url=row[5] or "",
                    memory_strength=0.0,  # 老師預覽不需要記憶強度
                    priority_score=0.0,
                )
            )

        return PracticeWordsResponse(
            session_id=-1,  # -1 表示老師預覽模式，不創建真實 session
            answer_mode=assignment.answer_mode,
            words=words,
        )

    else:
        # === 學生模式 ===
        student_id = user["student_id"]  # user 是 dict

        # 1. 取得學生作業實例（使用 student_assignment_id）
        student_assignment = (
            db.query(StudentAssignment)
            .join(Assignment)
            .filter(
                StudentAssignment.id == student_assignment_id,
                StudentAssignment.student_id == student_id,
            )
            .first()
        )

        if not student_assignment:
            raise HTTPException(status_code=404, detail="Student assignment not found")

        # 2. 創建新的練習 session
        assignment = student_assignment.assignment

        # 確保 practice_mode 是正確的字串值 ('listening' 或 'writing')
        answer_mode_value = assignment.answer_mode
        if answer_mode_value is None:
            raise HTTPException(
                status_code=500,
                detail="Assignment answer_mode is None. Please set answer_mode when creating assignment.",
            )

        if isinstance(answer_mode_value, str):
            # 如果是字串，確保是小寫
            practice_mode_str = answer_mode_value.lower()
        else:
            # 如果是 enum，取其值（.value）
            try:
                practice_mode_str = answer_mode_value.value
            except AttributeError:
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid answer_mode type: {type(answer_mode_value)}",
                )

        practice_session = PracticeSession(
            student_id=student_id,
            student_assignment_id=student_assignment.id,
            practice_mode=practice_mode_str,  # 直接使用字串值
        )
        db.add(practice_session)
        db.commit()
        db.refresh(practice_session)

        # 3. 使用 SQL function 選擇 10 個單字
        result = db.execute(
            text(
                """
                SELECT * FROM get_words_for_practice(
                    :student_assignment_id,
                    :limit_count
                )
            """
            ),
            {"student_assignment_id": student_assignment.id, "limit_count": 10},
        )

        words = []
        for row in result:
            words.append(
                PracticeWord(
                    content_item_id=row[0],
                    text=row[1],
                    translation=row[2],
                    example_sentence=row[3],
                    example_sentence_translation=row[4],
                    audio_url=row[5],
                    memory_strength=float(row[6]),
                    priority_score=float(row[7]),
                )
            )

        return PracticeWordsResponse(
            session_id=practice_session.id,
            answer_mode=assignment.answer_mode,
            words=words,
        )


@router.post(
    "/practice-sessions/{session_id}/submit-answer", response_model=SubmitAnswerResponse
)
async def submit_answer(
    session_id: int,
    request: SubmitAnswerRequest,
    user=Depends(get_current_student_or_teacher),
    db: Session = Depends(get_db),
):
    """
    提交單字答案
    - 記錄答題結果
    - 更新記憶強度（使用 SM-2 演算法）
    - 計算下次複習時間
    - 支援老師預覽模式（session_id = -1 時不記錄）
    """

    # 檢查是否為老師預覽模式
    is_teacher = user.get("user_type") == "teacher"

    if is_teacher:
        # === 老師預覽模式 ===
        # session_id = -1 表示預覽，不實際記錄資料
        if session_id == -1:
            # 直接返回成功，不更新資料庫
            return SubmitAnswerResponse(
                success=True,
                new_memory_strength=0.5,  # 假設值
                next_review_at=None,
            )
        else:
            # 老師不應該提交真實 session 的答案
            raise HTTPException(
                status_code=403,
                detail="Teachers cannot submit answers for student sessions",
            )

    # === 學生模式 ===
    student_id = user["student_id"]

    # 1. 驗證 session 屬於當前學生
    session = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.id == session_id,
            PracticeSession.student_id == student_id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")

    # 2. 記錄答案
    practice_answer = PracticeAnswer(
        practice_session_id=session_id,
        content_item_id=request.content_item_id,
        is_correct=request.is_correct,
        time_spent_seconds=request.time_spent_seconds,
        answer_data=request.answer_data,
    )
    db.add(practice_answer)

    # 3. 更新記憶強度（使用 PostgreSQL function）
    result = db.execute(
        text(
            """
            SELECT * FROM update_memory_strength(
                :student_assignment_id,
                :content_item_id,
                :is_correct
            )
        """
        ),
        {
            "student_assignment_id": session.student_assignment_id,
            "content_item_id": request.content_item_id,
            "is_correct": request.is_correct,
        },
    )

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to update memory strength")

    # 4. 更新 session 統計
    session.words_practiced += 1
    if request.is_correct:
        session.correct_count += 1
    session.total_time_seconds += request.time_spent_seconds

    db.commit()

    return SubmitAnswerResponse(
        success=True,
        new_memory_strength=float(row[0]),
        next_review_at=row[1],
    )


@router.get(
    "/assignments/{student_assignment_id}/mastery-status",
    response_model=MasteryStatusResponse,
)
async def get_mastery_status(
    student_assignment_id: int,
    user=Depends(get_current_student_or_teacher),
    db: Session = Depends(get_db),
):
    """
    檢查作業完成度
    - 計算整體熟悉度
    - 判斷是否達成目標（90%）
    - 返回已掌握的單字數
    - 支援老師預覽模式

    參數：student_assignment_id（學生模式）或 assignment_id（老師預覽模式）
    """

    # 檢查是否為老師預覽模式
    is_teacher = user.get("user_type") == "teacher"

    if is_teacher:
        # === 老師預覽模式 ===
        # 老師預覽時，student_assignment_id 其實是 assignment_id
        # 返回假的達標狀態（因為沒有真實學生資料）
        return MasteryStatusResponse(
            current_mastery=0.0,
            target_mastery=90.0,
            achieved=False,
            words_mastered=0,
            total_words=10,  # 假設值
        )

    # === 學生模式 ===
    student_id = user["student_id"]

    # 1. 取得學生作業實例（使用 student_assignment_id）
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == student_assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(status_code=404, detail="Student assignment not found")

    # 2. 使用 SQL function 計算達標狀態
    result = db.execute(
        text(
            """
            SELECT * FROM calculate_assignment_mastery(
                :student_assignment_id
            )
        """
        ),
        {"student_assignment_id": student_assignment.id},
    )

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to calculate mastery")

    return MasteryStatusResponse(
        current_mastery=float(row[0]),
        target_mastery=float(row[1]),
        achieved=row[2],
        words_mastered=row[3],
        total_words=row[4],
    )


# ============ 例句重組（Rearrangement）API ============


class RearrangementQuestionResponse(BaseModel):
    """例句重組題目回應"""

    content_item_id: int
    shuffled_words: List[str]  # 打亂後的單字列表
    word_count: int
    max_errors: int
    time_limit: int  # 時間限制（秒）
    play_audio: bool  # 是否播放音檔
    audio_url: Optional[str] = None
    translation: Optional[str] = None
    original_text: Optional[str] = None  # 正確答案（用於顯示答案功能）


class RearrangementAnswerRequest(BaseModel):
    """例句重組答題請求"""

    content_item_id: int
    selected_word: str  # 學生選擇的單字
    current_position: int  # 目前已正確選擇的位置（0-based）


class RearrangementAnswerResponse(BaseModel):
    """例句重組答題回應"""

    is_correct: bool
    correct_word: Optional[str] = None  # 如果錯誤，顯示正確答案
    error_count: int
    max_errors: int
    expected_score: float
    correct_word_count: int
    total_word_count: int
    challenge_failed: bool  # 達到錯誤上限
    completed: bool  # 是否完成此題


class RearrangementRetryRequest(BaseModel):
    """重新挑戰請求"""

    content_item_id: int


class RearrangementCompleteRequest(BaseModel):
    """完成題目請求"""

    content_item_id: int
    timeout: bool = False  # 是否因超時完成
    expected_score: Optional[float] = None  # 最終分數
    error_count: Optional[int] = None  # 錯誤次數


@router.get("/assignments/{assignment_id}/rearrangement-questions")
async def get_rearrangement_questions(
    assignment_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """取得例句重組題目列表"""
    import random

    # 驗證學生作業存在（assignment_id 實際上是 StudentAssignment.id）
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == current_student.id,
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(status_code=404, detail="Student assignment not found")

    # 取得作業設定
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == student_assignment.assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 確認是例句重組模式
    if assignment.practice_mode != "rearrangement":
        raise HTTPException(
            status_code=400, detail="This assignment is not in rearrangement mode"
        )

    # 取得所有內容項目
    content_items = (
        db.query(ContentItem)
        .join(Content)
        .join(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment.id)
        .order_by(ContentItem.order_index)
        .all()
    )

    # 如果需要打亂順序
    if assignment.shuffle_questions:
        random.shuffle(content_items)

    questions = []
    for item in content_items:
        # 打亂單字順序
        words = item.text.strip().split()
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)

        questions.append(
            RearrangementQuestionResponse(
                content_item_id=item.id,
                shuffled_words=shuffled_words,
                word_count=item.word_count or len(words),
                max_errors=item.max_errors or (3 if len(words) <= 10 else 5),
                time_limit=(
                    assignment.time_limit_per_question
                    if assignment.time_limit_per_question is not None
                    else 30
                ),
                play_audio=assignment.play_audio or False,
                audio_url=item.audio_url,
                translation=item.translation,
                original_text=item.text.strip(),  # 正確答案
            )
        )

    return {
        "student_assignment_id": assignment_id,
        "practice_mode": "rearrangement",
        "score_category": assignment.score_category,
        "questions": questions,
        "total_questions": len(questions),
    }


@router.post("/assignments/{assignment_id}/rearrangement-answer")
async def submit_rearrangement_answer(
    assignment_id: int,
    request: RearrangementAnswerRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """提交例句重組答案"""
    import math

    # 驗證學生作業存在（assignment_id 實際上是 StudentAssignment.id）
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == current_student.id,
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(status_code=404, detail="Student assignment not found")

    # 取得內容項目
    content_item = (
        db.query(ContentItem).filter(ContentItem.id == request.content_item_id).first()
    )

    if not content_item:
        raise HTTPException(status_code=404, detail="Content item not found")

    # 取得或建立進度記錄
    progress = (
        db.query(StudentItemProgress)
        .filter(
            StudentItemProgress.student_assignment_id == assignment_id,
            StudentItemProgress.content_item_id == request.content_item_id,
        )
        .first()
    )

    if not progress:
        progress = StudentItemProgress(
            student_assignment_id=assignment_id,
            content_item_id=request.content_item_id,
            status="IN_PROGRESS",
            error_count=0,
            correct_word_count=0,
            expected_score=100.0,
            rearrangement_data={"selections": []},
        )
        db.add(progress)
        db.flush()

    # 解析正確答案
    correct_words = content_item.text.strip().split()
    word_count = len(correct_words)
    max_errors = content_item.max_errors or (3 if word_count <= 10 else 5)
    points_per_word = math.floor(100 / word_count)

    # 檢查答案是否正確
    current_position = request.current_position
    if current_position >= word_count:
        raise HTTPException(status_code=400, detail="Invalid position")

    correct_word = correct_words[current_position]
    is_correct = request.selected_word.strip() == correct_word.strip()

    # 更新進度
    if is_correct:
        progress.correct_word_count = current_position + 1
    else:
        progress.error_count = (progress.error_count or 0) + 1

    # 修正：每次回答後都計算 expected_score（與老師預覽端一致）
    # 這樣即使 progress 記錄已存在，分數也會正確計算
    progress.expected_score = max(
        0, 100 - ((progress.error_count or 0) * points_per_word)
    )

    # 記錄選擇歷史
    selections = (
        progress.rearrangement_data.get("selections", [])
        if progress.rearrangement_data
        else []
    )
    selections.append(
        {
            "position": current_position,
            "selected": request.selected_word,
            "correct": correct_word,
            "is_correct": is_correct,
            "timestamp": datetime.now().isoformat(),
        }
    )
    progress.rearrangement_data = {"selections": selections}

    # 檢查是否達到錯誤上限
    challenge_failed = progress.error_count >= max_errors

    # 檢查是否完成
    completed = progress.correct_word_count >= word_count

    if completed:
        progress.status = "COMPLETED"
        # 確保保底分（完成作答最低分）
        assignment = (
            db.query(Assignment)
            .filter(Assignment.id == student_assignment.assignment_id)
            .first()
        )
        if assignment:
            # 取得總題數
            total_items = (
                db.query(ContentItem)
                .join(Content)
                .join(AssignmentContent)
                .filter(AssignmentContent.assignment_id == assignment.id)
                .count()
            )
            min_score = math.floor(100 / total_items) if total_items > 0 else 1
            progress.expected_score = max(
                float(progress.expected_score or 0), min_score
            )

    db.commit()

    return RearrangementAnswerResponse(
        is_correct=is_correct,
        correct_word=correct_word if not is_correct else None,
        error_count=progress.error_count or 0,
        max_errors=max_errors,
        expected_score=float(progress.expected_score or 0),
        correct_word_count=progress.correct_word_count or 0,
        total_word_count=word_count,
        challenge_failed=challenge_failed,
        completed=completed,
    )


@router.post("/assignments/{student_assignment_id}/rearrangement-retry")
async def retry_rearrangement(
    student_assignment_id: int,
    request: RearrangementRetryRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """重新挑戰題目（重置分數）"""
    # 驗證學生作業存在
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == student_assignment_id,
            StudentAssignment.student_id == current_student.id,
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(status_code=404, detail="Student assignment not found")

    # 取得進度記錄
    progress = (
        db.query(StudentItemProgress)
        .filter(
            StudentItemProgress.student_assignment_id == student_assignment_id,
            StudentItemProgress.content_item_id == request.content_item_id,
        )
        .first()
    )

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    # 重置進度
    progress.error_count = 0
    progress.correct_word_count = 0
    progress.expected_score = 100.0
    progress.retry_count = (progress.retry_count or 0) + 1
    progress.status = "IN_PROGRESS"
    progress.rearrangement_data = {"selections": [], "retries": progress.retry_count}

    db.commit()

    return {
        "success": True,
        "retry_count": progress.retry_count,
        "message": "Progress reset. You can start again.",
    }


@router.post("/assignments/{student_assignment_id}/rearrangement-complete")
async def complete_rearrangement(
    student_assignment_id: int,
    request: RearrangementCompleteRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """完成題目（時間到期或主動完成）"""
    # 驗證學生作業存在
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == student_assignment_id,
            StudentAssignment.student_id == current_student.id,
        )
        .first()
    )

    if not student_assignment:
        raise HTTPException(status_code=404, detail="Student assignment not found")

    # 取得進度記錄
    progress = (
        db.query(StudentItemProgress)
        .filter(
            StudentItemProgress.student_assignment_id == student_assignment_id,
            StudentItemProgress.content_item_id == request.content_item_id,
        )
        .first()
    )

    if not progress:
        # 防禦性：建立新記錄（正常情況下應該已存在）
        progress = StudentItemProgress(
            student_assignment_id=student_assignment_id,
            content_item_id=request.content_item_id,
            status="COMPLETED",
            timeout_ended=request.timeout,
            expected_score=request.expected_score or 0,
            error_count=request.error_count or 0,
        )
        db.add(progress)
    else:
        # 標記完成狀態
        progress.status = "COMPLETED"
        progress.timeout_ended = request.timeout

        # 更新分數（如果前端有提供）
        if request.expected_score is not None:
            progress.expected_score = request.expected_score
        if request.error_count is not None:
            progress.error_count = request.error_count

    db.commit()

    return {
        "success": True,
        "final_score": float(progress.expected_score or 0),
        "timeout": request.timeout,
        "completed_at": datetime.now().isoformat(),
    }
