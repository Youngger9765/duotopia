"""Student assignment management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime

from database import get_db
from models import (
    StudentAssignment,
    StudentContentProgress,
    AssignmentContent,
    Content,
    ContentItem,
    StudentItemProgress,
    AssignmentStatus,
)
from .dependencies import get_current_student

router = APIRouter()


@router.get("/assignments")
async def get_student_assignments(
    current_student: Dict[str, Any] = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """取得學生作業列表"""
    student_id = current_student.get("sub")

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
                "classroom_id": assignment.classroom_id,
                "score": assignment.score,
                "feedback": assignment.feedback,
            }
        )

    return result


@router.get("/assignments/{assignment_id}/activities")
async def get_assignment_activities(
    assignment_id: int,
    current_student: Dict[str, Any] = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """取得作業的活動內容列表（題目）"""
    student_id = int(current_student.get("sub"))

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

                # 同時創建 StudentItemProgress
                content_items = (
                    db.query(ContentItem)
                    .filter(ContentItem.content_id == ac.content_id)
                    .order_by(ContentItem.order_index)
                    .all()
                )

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

        # 優化：預先批次查詢所有 ContentItems 和 StudentItemProgress
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

                # 優化：從預先載入的 map 取得 ContentItems（不再查詢資料庫）
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
                            ] = item_progress.id  # 返回 progress_id 給前端用於批次分析

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

                            if (
                                item_progress.has_ai_assessment
                                and item_progress.ai_feedback
                            ):
                                # 從 ai_feedback JSON 中取得分數
                                import json

                                try:
                                    ai_feedback = (
                                        json.loads(item_progress.ai_feedback)
                                        if isinstance(item_progress.ai_feedback, str)
                                        else item_progress.ai_feedback
                                    )
                                    item_data["ai_assessment"] = {
                                        "accuracy_score": float(
                                            ai_feedback.get("accuracy_score", 0)
                                        ),
                                        "fluency_score": float(
                                            ai_feedback.get("fluency_score", 0)
                                        ),
                                        "pronunciation_score": float(
                                            ai_feedback.get("pronunciation_score", 0)
                                        ),
                                        "completeness_score": float(
                                            ai_feedback.get("completeness_score", 0)
                                        ),
                                        "prosody_score": ai_feedback.get(
                                            "prosody_score"
                                        ),
                                        # 舊版相容性
                                        "word_details": ai_feedback.get(
                                            "word_details", []
                                        ),
                                        # 新版詳細分析資料
                                        "detailed_words": ai_feedback.get(
                                            "detailed_words", []
                                        ),
                                        "reference_text": ai_feedback.get(
                                            "reference_text", ""
                                        ),
                                        "recognized_text": ai_feedback.get(
                                            "recognized_text", ""
                                        ),
                                        "analysis_summary": ai_feedback.get(
                                            "analysis_summary", {}
                                        ),
                                        "ai_feedback": item_progress.ai_feedback,
                                        "assessed_at": item_progress.ai_assessed_at.isoformat()
                                        if item_progress.ai_assessed_at
                                        else None,
                                    }
                                except (json.JSONDecodeError, TypeError):
                                    # 如果 JSON 解析失敗，設為 None
                                    item_data["ai_assessment"] = None

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
    current_student: Dict[str, Any] = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """儲存活動進度（自動儲存）"""
    student_id = int(current_student.get("sub"))

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
    current_student: Dict[str, Any] = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """提交作業"""
    student_id = int(current_student.get("sub"))

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
