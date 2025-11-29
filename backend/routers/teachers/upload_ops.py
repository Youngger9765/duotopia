"""
Upload Ops operations for teachers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import Teacher, Classroom, Student, Program, Lesson, Content, ContentItem
from models import ClassroomStudent, Assignment, AssignmentContent
from models import ProgramLevel, TeacherOrganization, TeacherSchool, Organization, School
from .dependencies import get_current_teacher
from .validators import *
from .utils import TEST_SUBSCRIPTION_WHITELIST, parse_birthdate
from fastapi import UploadFile, File, Form

router = APIRouter()

@router.post("/upload/audio")
async def upload_audio(
    file: UploadFile = File(...),
    duration: int = Form(30),
    content_id: Optional[int] = Form(None),
    item_index: Optional[int] = Form(None),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """上傳錄音檔案

    Args:
        file: 音檔檔案
        duration: 錄音長度（秒）
        content_id: 內容 ID（用於識別要替換的音檔）
        item_index: 項目索引（用於識別是哪個項目的音檔）
    """
    try:
        from services.audio_upload import get_audio_upload_service
        from services.audio_manager import get_audio_manager

        audio_service = get_audio_upload_service()
        audio_manager = get_audio_manager()

        # 如果提供了 content_id 和 item_index，先刪除舊音檔
        if content_id and item_index is not None:
            content = (
                db.query(Content)
                .filter(
                    Content.id == content_id,
                    Content.lesson.has(
                        Lesson.program.has(Program.teacher_id == current_teacher.id)
                    ),
                )
                .first()
            )

            if content:
                # 查找對應的 ContentItem

                content_items = (
                    db.query(ContentItem)
                    .filter(ContentItem.content_id == content_id)
                    .order_by(ContentItem.order_index)
                    .all()
                )

                if content_items and item_index < len(content_items):
                    old_audio_url = content_items[item_index].audio_url
                    if old_audio_url:
                        # 刪除舊音檔
                        audio_manager.delete_old_audio(old_audio_url)

        # 上傳新音檔（包含 content_id 和 item_index 在檔名中）
        audio_url = await audio_service.upload_audio(
            file, duration, content_id=content_id, item_index=item_index
        )

        return {"audio_url": audio_url}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Audio upload error: {e}")
        raise HTTPException(status_code=500, detail="Audio upload failed")


