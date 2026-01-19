"""
Assignment Ops operations for teachers.
"""
import logging
import random
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import Teacher, Classroom, Student, Program, Lesson, Content, ContentItem
from models import ClassroomStudent, Assignment, AssignmentContent, ContentType
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

logger = logging.getLogger(__name__)

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
        "practice_mode": assignment.practice_mode,  # 前端用來判斷顯示哪個元件
        "show_answer": assignment.show_answer or False,  # 例句重組：答題結束後是否顯示正確答案
        "score_category": assignment.score_category,  # 分數記錄分類
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


# =============================================================================
# Vocabulary Preview APIs
# =============================================================================


@router.get("/assignments/{assignment_id}/preview/vocabulary/activities")
async def preview_vocabulary_activities(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Preview mode: Get vocabulary word reading practice data.

    - For teacher preview/demo purposes
    - No StudentAssignment needed, reads directly from Assignment
    - Returns same format as student API
    """
    # Get assignment (verify teacher has permission)
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify this is word_reading mode
    if assignment.practice_mode != "word_reading":
        raise HTTPException(
            status_code=400, detail="This assignment is not in word_reading mode"
        )

    # Get all content items
    content_items = (
        db.query(ContentItem)
        .join(Content)
        .join(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment.id)
        .order_by(ContentItem.order_index)
        .all()
    )

    # Build items data (preview mode has no student progress)
    items = []
    for item in content_items:
        item_data = {
            "id": item.id,
            "text": item.text,
            "translation": item.translation,
            "audio_url": item.audio_url,
            "image_url": item.image_url,
            "part_of_speech": item.part_of_speech,
            "order_index": item.order_index,
            "recording_url": None,  # Preview mode has no student recordings
        }
        items.append(item_data)

    return {
        "assignment_id": assignment_id,
        "title": assignment.title,
        "status": "preview",
        "practice_mode": "word_reading",
        "show_translation": assignment.show_translation
        if assignment.show_translation is not None
        else True,
        "show_image": assignment.show_image
        if assignment.show_image is not None
        else True,
        "time_limit_per_question": assignment.time_limit_per_question or 0,
        "total_items": len(items),
        "items": items,
    }


# ============ Word Selection Preview API ============


@router.get("/assignments/{assignment_id}/preview/word-selection-start")
async def preview_word_selection_start(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Preview mode: Get word selection practice data.

    - For teacher preview/demo purposes
    - No StudentAssignment needed, reads directly from Assignment
    - Uses pre-generated distractors if available
    """
    from services.translation import translation_service

    # Get assignment (verify teacher has permission)
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify this is word_selection mode
    if assignment.practice_mode != "word_selection":
        raise HTTPException(
            status_code=400, detail="This assignment is not in word_selection mode"
        )

    # Get all content items
    content_items = (
        db.query(ContentItem)
        .join(Content)
        .join(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment.id)
        .order_by(ContentItem.order_index)
        .all()
    )

    if not content_items:
        raise HTTPException(
            status_code=404, detail="No vocabulary items found for this assignment"
        )

    # Record total word count (before limiting)
    total_words_in_assignment = len(content_items)

    # Shuffle if needed
    if assignment.shuffle_questions:
        random.shuffle(content_items)

    # Limit to 10 words (consistent with student API)
    content_items = content_items[:10]

    # Collect items that need distractor generation
    items_needing_generation = [item for item in content_items if not item.distractors]

    # If some need generation, batch generate
    if items_needing_generation:
        words_for_distractors = [
            {"word": item.text, "translation": item.translation or ""}
            for item in items_needing_generation
        ]
        try:
            # 2 AI-generated, 1 from other words in assignment
            generated = await translation_service.batch_generate_distractors(
                words_for_distractors, count=2
            )
            for i, item in enumerate(items_needing_generation):
                if i < len(generated):
                    item._generated_distractors = generated[i]
        except Exception as e:
            logger.error(f"Failed to generate distractors for preview: {e}")
            for item in items_needing_generation:
                item._generated_distractors = ["選項A", "選項B", "選項C"]

    # Build response data
    words_with_options = []

    # Collect all translations for cross-distraction
    all_translations = {
        item.translation.lower().strip(): item.translation
        for item in content_items
        if item.translation
    }

    for item in content_items:
        correct_answer = item.translation or ""

        # Use pre-generated or just-generated distractors
        if item.distractors:
            ai_distractors = item.distractors
        elif hasattr(item, "_generated_distractors"):
            ai_distractors = item._generated_distractors
        else:
            ai_distractors = []

        # Dedup set
        seen = {correct_answer.lower().strip()}
        final_distractors = []

        # Step 1: Add 1 distractor from other words in assignment
        other_translations = [
            t
            for key, t in all_translations.items()
            if key != correct_answer.lower().strip()
        ]
        if other_translations:
            sibling_distractor = random.choice(other_translations)
            if sibling_distractor.lower().strip() not in seen:
                final_distractors.append(sibling_distractor)
                seen.add(sibling_distractor.lower().strip())

        # Step 2: Add AI-generated distractors (up to 2)
        for d in ai_distractors:
            d_normalized = d.lower().strip()
            if d_normalized not in seen and d.strip():
                seen.add(d_normalized)
                final_distractors.append(d)
            if len(final_distractors) >= 3:
                break

        # Step 3: Fallback to ensure 3 distractors
        fallback_options = ["選項A", "選項B", "選項C", "選項D", "選項E"]
        fallback_idx = 0
        while len(final_distractors) < 3:
            fallback = fallback_options[fallback_idx]
            if fallback.lower() not in seen:
                final_distractors.append(fallback)
                seen.add(fallback.lower())
            fallback_idx += 1

        # Build options array and shuffle
        options = [correct_answer] + final_distractors[:3]
        random.shuffle(options)

        words_with_options.append(
            {
                "content_item_id": item.id,
                "text": item.text,
                "translation": correct_answer,
                "audio_url": item.audio_url,
                "image_url": item.image_url,
                "memory_strength": 0,
                "options": options,
            }
        )

    return {
        "session_id": None,  # Preview mode doesn't create session
        "words": words_with_options,
        "total_words": total_words_in_assignment,
        "current_proficiency": 0,
        "target_proficiency": assignment.target_proficiency or 80,
        "show_word": assignment.show_word if assignment.show_word is not None else True,
        "show_image": (
            assignment.show_image if assignment.show_image is not None else True
        ),
        "play_audio": assignment.play_audio or False,
        "time_limit_per_question": assignment.time_limit_per_question,
    }


@router.post("/assignments/{assignment_id}/preview/word-selection-answer")
async def preview_word_selection_answer(
    assignment_id: int,
    request: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Preview mode: Submit word selection answer (not saved).

    - Only validates if answer is correct
    - Does not update any database records
    - Returns simulated result
    """
    # Get assignment (verify teacher has permission)
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    content_item_id = request.get("content_item_id")
    selected_answer = request.get("selected_answer")

    # Get content item to verify answer
    content_item = (
        db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    )

    if not content_item:
        raise HTTPException(status_code=404, detail="Content item not found")

    is_correct = selected_answer == content_item.translation

    # Return simulated result (preview mode doesn't update memory_strength)
    return {
        "is_correct": is_correct,
        "correct_answer": content_item.translation,
        "new_memory_strength": 0.5 if is_correct else 0,  # Simulated value
        "current_mastery": 50.0,  # Simulated value
        "target_mastery": assignment.target_proficiency or 80,
        "achieved": False,
    }


# ============ Rearrangement Preview APIs ============


@router.get("/assignments/{assignment_id}/preview/rearrangement-questions")
async def preview_rearrangement_questions(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Preview mode: Get rearrangement questions.

    - For teacher preview/demo purposes
    - No StudentAssignment needed, reads directly from Assignment
    - Returns same format as student API
    """
    # Get assignment (verify teacher has permission)
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify this is rearrangement mode
    if assignment.practice_mode != "rearrangement":
        raise HTTPException(
            status_code=400, detail="This assignment is not in rearrangement mode"
        )

    # Get all content items
    content_items = (
        db.query(ContentItem)
        .join(Content)
        .join(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment.id)
        .order_by(ContentItem.order_index)
        .all()
    )

    # Shuffle if needed
    if assignment.shuffle_questions:
        random.shuffle(content_items)

    questions = []
    for item in content_items:
        # Shuffle words
        words = item.text.strip().split()
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)

        questions.append(
            {
                "content_item_id": item.id,
                "shuffled_words": shuffled_words,
                "word_count": item.word_count or len(words),
                "max_errors": item.max_errors or (3 if len(words) <= 10 else 5),
                "time_limit": (
                    assignment.time_limit_per_question
                    if assignment.time_limit_per_question is not None
                    else 30
                ),
                "play_audio": assignment.play_audio or False,
                "audio_url": item.audio_url,
                "translation": item.translation,
                "original_text": item.text.strip(),  # Correct answer
            }
        )

    return {
        "assignment_id": assignment_id,
        "practice_mode": "rearrangement",
        "show_answer": assignment.show_answer or False,
        "score_category": assignment.score_category,
        "questions": questions,
        "total_questions": len(questions),
    }


@router.post("/assignments/{assignment_id}/preview/rearrangement-answer")
async def preview_rearrangement_answer(
    assignment_id: int,
    request: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Preview mode: Submit rearrangement answer (not saved).

    - Only validates if selected word is correct
    - Does not update any database records
    - Returns simulated result
    """
    # Get assignment (verify teacher has permission)
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    content_item_id = request.get("content_item_id")
    selected_word = request.get("selected_word", "")
    current_position = request.get("current_position", 0)

    # Get content item to verify answer
    content_item = (
        db.query(ContentItem).filter(ContentItem.id == content_item_id).first()
    )

    if not content_item:
        raise HTTPException(status_code=404, detail="Content item not found")

    # Parse correct words
    correct_words = content_item.text.strip().split()
    word_count = len(correct_words)

    if current_position >= word_count:
        raise HTTPException(status_code=400, detail="Invalid position")

    correct_word = correct_words[current_position]
    is_correct = selected_word.strip() == correct_word.strip()

    max_errors = content_item.max_errors or (3 if word_count <= 10 else 5)

    # Return simulated result (preview mode uses static values)
    return {
        "is_correct": is_correct,
        "correct_word": correct_word if not is_correct else None,
        "error_count": 0 if is_correct else 1,  # Simulated
        "max_errors": max_errors,
        "expected_score": 100.0 if is_correct else 90.0,  # Simulated
        "correct_word_count": current_position + 1 if is_correct else current_position,
        "total_word_count": word_count,
        "challenge_failed": False,  # Preview mode never fails
        "completed": is_correct and (current_position + 1 >= word_count),
    }


@router.post("/assignments/{assignment_id}/preview/rearrangement-retry")
async def preview_rearrangement_retry(
    assignment_id: int,
    request: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Preview mode: Retry rearrangement question (simulated).

    - Does not update any database records
    - Returns simulated success response
    """
    # Get assignment (verify teacher has permission)
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Return simulated success (preview mode doesn't track retries)
    return {
        "success": True,
        "retry_count": 1,  # Simulated
        "message": "Progress reset. You can start again.",
    }


@router.post("/assignments/{assignment_id}/preview/rearrangement-complete")
async def preview_rearrangement_complete(
    assignment_id: int,
    request: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Preview mode: Complete rearrangement question (simulated).

    - Does not update any database records
    - Returns simulated completion response
    """
    from datetime import datetime

    # Get assignment (verify teacher has permission)
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    timeout = request.get("timeout", False)
    expected_score = request.get("expected_score", 100.0)

    # Return simulated completion
    return {
        "success": True,
        "final_score": expected_score,
        "timeout": timeout,
        "completed_at": datetime.now().isoformat(),
    }
