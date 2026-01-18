"""
Assignment Ops operations for teachers.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import Teacher, Classroom, Student, Program, Lesson, Content, ContentItem
from models import ClassroomStudent, Assignment, AssignmentContent
from models import (
    ProgramLevel,
    TeacherOrganization,
    TeacherSchool,
    Organization,
    School,
    ContentType,
)
from .dependencies import get_current_teacher
from .validators import *
from .utils import TEST_SUBSCRIPTION_WHITELIST, parse_birthdate

router = APIRouter()


@router.get("/assignments/{assignment_id}/preview")
async def get_assignment_preview(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    取得作業的預覽內容（供老師示範用）

    返回與學生 API 相同格式的資料，讓老師可以預覽完整的作業內容
    """
    # 查詢作業（確認老師有權限）
    assignment = (
        db.query(Assignment)
        .join(Classroom)
        .filter(
            Assignment.id == assignment_id,
            Classroom.teacher_id == current_teacher.id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or access denied",
        )

    # 獲取作業的所有 content
    assignment_contents = (
        db.query(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment_id)
        .order_by(AssignmentContent.order_index)
        .all()
    )

    # 🔥 Batch-load all contents with items (avoid N+1)
    content_ids = [ac.content_id for ac in assignment_contents]
    contents = (
        db.query(Content)
        .filter(Content.id.in_(content_ids))
        .options(selectinload(Content.content_items))  # Eager load items
        .all()
    )
    content_dict = {content.id: content for content in contents}

    activities = []

    for idx, ac in enumerate(assignment_contents):
        content = content_dict.get(ac.content_id)

        if content:
            # 構建活動資料（與學生 API 格式相同）
            activity_data = {
                "id": idx + 1,  # 臨時 ID（預覽模式不需要實際進度 ID）
                "content_id": content.id,
                "order": idx + 1,
                "type": content.type.value if content.type else "reading_assessment",
                "title": content.title,
                "duration": content.time_limit_seconds or 60,
                "points": 100 // len(assignment_contents)
                if len(assignment_contents) > 0
                else 100,
                "status": "NOT_STARTED",  # 預覽模式始終是未開始
                "score": None,
                "completed_at": None,
            }

            # 🔥 Use preloaded content_items (no query)
            content_items = sorted(content.content_items, key=lambda x: x.order_index)

            # 構建 items 資料
            items_data = []
            for item in content_items:
                item_data = {
                    "id": item.id,
                    "text": item.text,
                    "translation": item.translation,
                    "audio_url": item.audio_url,
                    "recording_url": None,  # 預覽模式沒有學生錄音
                }
                items_data.append(item_data)

            activity_data["items"] = items_data
            activity_data["item_count"] = len(items_data)

            # 額外欄位（根據 content type）
            if content.type == ContentType.READING_ASSESSMENT:
                activity_data["target_wpm"] = content.target_wpm
                activity_data["target_accuracy"] = content.target_accuracy

            activities.append(activity_data)

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "status": "preview",  # 特殊標記表示這是預覽模式
        "total_activities": len(activities),
        "activities": activities,
    }


@router.post("/assignments/preview/assess-speech")
async def preview_assess_speech(
    audio_file: UploadFile = File(...),
    reference_text: str = Form(...),
    current_teacher: Teacher = Depends(get_current_teacher),  # noqa: F811
):
    """
    預覽模式專用：評估發音但不存入資料庫

    - 只做 AI 評估，不需要 progress_id
    - 不更新資料庫
    - 供老師預覽示範用
    """
    import logging

    logger = logging.getLogger(__name__)

    # 使用與學生相同的 AI 評估邏輯（確保一致性）
    from routers.speech_assessment import convert_audio_to_wav, assess_pronunciation

    # 檢查檔案格式
    ALLOWED_AUDIO_FORMATS = [
        "audio/wav",
        "audio/webm",
        "audio/webm;codecs=opus",
        "audio/mp3",
        "audio/mpeg",
        "audio/mp4",  # macOS Safari 使用 MP4 格式
        "video/mp4",  # 某些瀏覽器可能用 video/mp4
        "application/octet-stream",
    ]

    if audio_file.content_type not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的音檔格式。允許的格式: {', '.join(ALLOWED_AUDIO_FORMATS)}",
        )

    # 檢查檔案大小
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    audio_data = await audio_file.read()
    if len(audio_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"檔案太大。最大大小: {MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    try:
        # 轉換音檔格式為 WAV（與學生 API 相同的邏輯）
        wav_audio_data = convert_audio_to_wav(audio_data, audio_file.content_type)

        # 進行發音評估（與學生 API 相同的邏輯，但不儲存到資料庫）
        assessment_result = assess_pronunciation(wav_audio_data, reference_text)

        # 直接返回評估結果，不存入資料庫
        return {
            "success": True,
            "preview_mode": True,
            "assessment": assessment_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview assessment failed: {e}")
        raise HTTPException(status_code=503, detail="AI 評估失敗，請稍後再試")
