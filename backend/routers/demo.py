"""
Demo router - Public demo assignment preview endpoints with rate limiting.

This module provides public access to demo assignments created by the demo teacher account.
No authentication required, but rate-limited to prevent abuse.
"""

import logging
import os
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session, selectinload
from core.limiter import limiter
from database import get_db
from models import (
    DemoConfig,
    Teacher,
    Assignment,
    AssignmentContent,
    Classroom,
    Content,
    ContentItem,
    ContentType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])

# Demo teacher email - from environment or default
DEMO_TEACHER_EMAIL = os.getenv("DEMO_TEACHER_EMAIL", "contact@duotopia.co")


# ============================================================================
# Helper Functions
# ============================================================================


def get_demo_assignment(assignment_id: int, db: Session) -> Assignment:
    """
    Validate that assignment belongs to demo teacher account.

    Args:
        assignment_id: Assignment ID to validate
        db: Database session

    Returns:
        Assignment object if valid

    Raises:
        HTTPException: 404 if assignment not found or doesn't belong to demo account
    """
    assignment = (
        db.query(Assignment)
        .join(Classroom)
        .join(Teacher)
        .filter(
            Assignment.id == assignment_id,
            Teacher.email == DEMO_TEACHER_EMAIL,
            Assignment.is_active == True,  # noqa: E712
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo assignment not found",
        )

    return assignment


# ============================================================================
# Demo Config API
# ============================================================================


@router.get("/config")
@limiter.limit("30/minute")
async def get_demo_config(request: Request, db: Session = Depends(get_db)):
    """
    Get demo configuration (assignment IDs for 4 practice modes).

    Rate limit: 30 requests per minute per IP.

    Returns:
        Dict of config keys and values, e.g.:
        {
            "demo_reading_assignment_id": "123",
            "demo_rearrangement_assignment_id": "124",
            ...
        }
    """
    configs = db.query(DemoConfig).all()
    return {c.key: c.value for c in configs}


# ============================================================================
# Demo Preview - Main Assignment Data
# ============================================================================


@router.get("/assignments/{assignment_id}/preview")
@limiter.limit("60/minute")
async def get_demo_preview(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Get demo assignment preview (no authentication required).

    This endpoint reuses the same logic as teacher preview endpoints,
    but without authentication. Only assignments from the demo teacher
    account can be accessed.

    Rate limit: 60 requests per minute per IP.

    Returns:
        Same format as teacher preview API, suitable for reusing frontend components.
    """
    # Validate assignment belongs to demo account
    assignment = get_demo_assignment(assignment_id, db)

    # Get all assignment contents
    assignment_contents = (
        db.query(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment_id)
        .order_by(AssignmentContent.order_index)
        .all()
    )

    # Batch-load all contents with items (avoid N+1)
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
            # Build activity data (same format as student API)
            activity_data = {
                "id": idx
                + 1,  # Temporary ID (preview mode doesn't need real progress ID)
                "content_id": content.id,
                "order": idx + 1,
                "type": content.type.value if content.type else "reading_assessment",
                "title": content.title,
                "duration": content.time_limit_seconds or 60,
                "points": 100 // len(assignment_contents)
                if len(assignment_contents) > 0
                else 100,
                "status": "NOT_STARTED",  # Preview mode always starts as NOT_STARTED
                "score": None,
                "completed_at": None,
            }

            # Use preloaded content_items (no additional query)
            content_items = sorted(content.content_items, key=lambda x: x.order_index)

            # Build items data
            items_data = []
            for item in content_items:
                item_data = {
                    "id": item.id,
                    "text": item.text,
                    "translation": item.translation,
                    "audio_url": item.audio_url,
                    "recording_url": None,  # No student recordings in preview mode
                }
                items_data.append(item_data)

            activity_data["items"] = items_data
            activity_data["item_count"] = len(items_data)

            # Additional fields based on content type
            if content.type == ContentType.READING_ASSESSMENT:
                activity_data["target_wpm"] = content.target_wpm
                activity_data["target_accuracy"] = content.target_accuracy

            activities.append(activity_data)

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "status": "preview",  # Special marker for preview mode
        "practice_mode": assignment.practice_mode,  # Frontend uses this to determine which component to show
        "show_answer": assignment.show_answer
        or False,  # Rearrangement: show correct answer after completion
        "score_category": assignment.score_category,  # Score recording category
        "total_activities": len(activities),
        "activities": activities,
    }


# ============================================================================
# Demo Preview - Speech Assessment
# ============================================================================


@router.post("/assignments/preview/assess-speech")
@limiter.limit("120/minute")  # Speech assessment needs higher quota
async def demo_assess_speech(
    request: Request,
    audio_file: UploadFile = File(...),
    reference_text: str = Form(...),
    assignment_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    Demo speech assessment (no authentication, no recording storage).

    Rate limit: 120 requests per minute per IP (higher than normal endpoints
    because speech assessment is the core demo feature).

    Args:
        audio_file: Audio file to assess
        reference_text: Reference text for pronunciation assessment
        assignment_id: Assignment ID (must belong to demo account)
        db: Database session

    Returns:
        Assessment results (same format as teacher preview API)
    """
    # Validate assignment belongs to demo account
    get_demo_assignment(assignment_id, db)

    # Reuse speech assessment logic from teachers preview
    from routers.speech_assessment import convert_audio_to_wav, assess_pronunciation

    # Check file format
    ALLOWED_AUDIO_FORMATS = [
        "audio/wav",
        "audio/webm",
        "audio/webm;codecs=opus",
        "audio/mp3",
        "audio/mpeg",
        "audio/mp4",  # macOS Safari uses MP4 format
        "video/mp4",  # Some browsers may use video/mp4
        "application/octet-stream",
    ]

    if audio_file.content_type not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Allowed formats: {', '.join(ALLOWED_AUDIO_FORMATS)}",
        )

    # Check file size
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    audio_data = await audio_file.read()
    if len(audio_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    try:
        # Convert audio format to WAV
        wav_audio_data = convert_audio_to_wav(audio_data, audio_file.content_type)

        # Perform pronunciation assessment (same logic as teacher API, but no database storage)
        assessment_result = assess_pronunciation(wav_audio_data, reference_text)

        # Return assessment results directly, do not save to database
        return {
            "success": True,
            "preview_mode": True,
            "demo_mode": True,
            "assessment": assessment_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo assessment failed: {e}")
        raise HTTPException(
            status_code=503, detail="AI assessment failed, please try again later"
        )


# ============================================================================
# Demo Preview - Vocabulary Activities
# ============================================================================


@router.get("/assignments/{assignment_id}/preview/vocabulary/activities")
@limiter.limit("60/minute")
async def demo_vocabulary_activities(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Demo mode: Get vocabulary word reading practice data.

    Rate limit: 60 requests per minute per IP.

    Returns:
        Same format as teacher preview API for vocabulary practice.
    """
    # Validate assignment belongs to demo account
    assignment = get_demo_assignment(assignment_id, db)

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

    if not content_items:
        raise HTTPException(status_code=404, detail="No vocabulary items found")

    # Build activities list
    activities = []
    for idx, item in enumerate(content_items):
        activity = {
            "id": idx + 1,
            "word": item.text,
            "translation": item.translation if assignment.show_translation else None,
            "image_url": item.image_url if assignment.show_image else None,
            "audio_url": item.audio_url,
            "order": idx + 1,
            "status": "NOT_STARTED",
            "score": None,
        }
        activities.append(activity)

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "practice_mode": "word_reading",
        "show_translation": assignment.show_translation,
        "show_image": assignment.show_image,
        "total_activities": len(activities),
        "activities": activities,
        "preview_mode": True,
        "demo_mode": True,
    }


# ============================================================================
# Demo Preview - Word Selection
# ============================================================================


@router.get("/assignments/{assignment_id}/preview/word-selection-start")
@limiter.limit("60/minute")
async def demo_word_selection_start(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Demo mode: Start word selection practice.

    Rate limit: 60 requests per minute per IP.

    Returns:
        Same format as teacher preview API for word selection practice.
    """
    # Validate assignment belongs to demo account
    assignment = get_demo_assignment(assignment_id, db)

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
        raise HTTPException(status_code=404, detail="No word items found")

    # Build question pool (same format as teacher preview)
    question_pool = []
    for item in content_items:
        question = {
            "item_id": item.id,
            "word": item.text if assignment.show_word else None,
            "audio_url": item.audio_url,
            "image_url": item.image_url if assignment.show_image else None,
            "correct_translation": item.translation,
        }
        question_pool.append(question)

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "practice_mode": "word_selection",
        "target_proficiency": assignment.target_proficiency or 80,
        "show_word": assignment.show_word,
        "show_image": assignment.show_image,
        "question_pool": question_pool,
        "preview_mode": True,
        "demo_mode": True,
    }


@router.post("/assignments/{assignment_id}/preview/word-selection-answer")
@limiter.limit("120/minute")  # Higher limit for interactive practice
async def demo_word_selection_answer(
    request: Request,
    assignment_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    """
    Demo mode: Submit word selection answer.

    Rate limit: 120 requests per minute per IP.

    This endpoint validates answers but does not save progress.

    Args:
        assignment_id: Assignment ID
        data: Answer data containing item_id and selected_translation

    Returns:
        Validation result (correct/incorrect)
    """
    # Validate assignment belongs to demo account
    get_demo_assignment(assignment_id, db)

    item_id = data.get("item_id")
    selected_translation = data.get("selected_translation")

    if not item_id or not selected_translation:
        raise HTTPException(
            status_code=400, detail="Missing item_id or selected_translation"
        )

    # Get the content item
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    # Check if answer is correct
    is_correct = (
        item.translation.strip().lower() == selected_translation.strip().lower()
    )

    return {
        "item_id": item_id,
        "is_correct": is_correct,
        "correct_translation": item.translation,
        "preview_mode": True,
        "demo_mode": True,
    }


# ============================================================================
# Demo Preview - Rearrangement Practice
# ============================================================================


@router.get("/assignments/{assignment_id}/preview/rearrangement-questions")
@limiter.limit("60/minute")
async def demo_rearrangement_questions(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Demo mode: Get rearrangement practice questions.

    Rate limit: 60 requests per minute per IP.

    Returns:
        Same format as teacher preview API for rearrangement practice.
    """
    import random

    # Validate assignment belongs to demo account
    assignment = get_demo_assignment(assignment_id, db)

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

    if not content_items:
        raise HTTPException(status_code=404, detail="No questions found")

    # Build questions list
    questions = []
    for idx, item in enumerate(content_items):
        # Split sentence into words and shuffle
        words = item.text.strip().split()
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)

        question = {
            "id": idx + 1,
            "item_id": item.id,
            "shuffled_words": shuffled_words,
            "correct_sentence": item.text,
            "translation": item.translation,
            "audio_url": item.audio_url if assignment.play_audio else None,
            "time_limit": assignment.time_limit_per_question or 30,
            "order": idx + 1,
        }
        questions.append(question)

    # Shuffle questions if configured
    if assignment.shuffle_questions:
        random.shuffle(questions)
        # Re-order the questions
        for idx, q in enumerate(questions):
            q["order"] = idx + 1

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "practice_mode": "rearrangement",
        "play_audio": assignment.play_audio or False,
        "show_answer": assignment.show_answer or False,
        "time_limit_per_question": assignment.time_limit_per_question or 30,
        "shuffle_questions": assignment.shuffle_questions or False,
        "total_questions": len(questions),
        "questions": questions,
        "preview_mode": True,
        "demo_mode": True,
    }


@router.post("/assignments/{assignment_id}/preview/rearrangement-answer")
@limiter.limit("120/minute")  # Higher limit for interactive practice
async def demo_rearrangement_answer(
    request: Request,
    assignment_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    """
    Demo mode: Submit rearrangement answer.

    Rate limit: 120 requests per minute per IP.

    This endpoint validates answers but does not save progress.

    Args:
        assignment_id: Assignment ID
        data: Answer data containing item_id and user_answer

    Returns:
        Validation result (correct/incorrect, score)
    """
    # Validate assignment belongs to demo account
    get_demo_assignment(assignment_id, db)

    item_id = data.get("item_id")
    user_answer = data.get("user_answer")

    if not item_id or not user_answer:
        raise HTTPException(status_code=400, detail="Missing item_id or user_answer")

    # Get the content item
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    # Normalize and compare answers
    correct_answer = item.text.strip().lower()
    user_answer_normalized = user_answer.strip().lower()

    is_correct = correct_answer == user_answer_normalized

    # Calculate score (100 if correct, 0 if incorrect)
    score = 100 if is_correct else 0

    return {
        "item_id": item_id,
        "is_correct": is_correct,
        "score": score,
        "correct_answer": item.text,
        "user_answer": user_answer,
        "preview_mode": True,
        "demo_mode": True,
    }


@router.post("/assignments/{assignment_id}/preview/rearrangement-retry")
@limiter.limit("60/minute")
async def demo_rearrangement_retry(
    request: Request,
    assignment_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    """
    Demo mode: Retry rearrangement practice.

    Rate limit: 60 requests per minute per IP.

    This endpoint resets progress for demo mode (no actual database changes).

    Returns:
        Success response
    """
    # Validate assignment belongs to demo account
    get_demo_assignment(assignment_id, db)

    return {
        "success": True,
        "message": "Demo practice reset (no data saved)",
        "preview_mode": True,
        "demo_mode": True,
    }


@router.post("/assignments/{assignment_id}/preview/rearrangement-complete")
@limiter.limit("60/minute")
async def demo_rearrangement_complete(
    request: Request,
    assignment_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    """
    Demo mode: Complete rearrangement practice.

    Rate limit: 60 requests per minute per IP.

    This endpoint records completion for demo mode (no database storage).

    Returns:
        Completion summary
    """
    # Validate assignment belongs to demo account
    get_demo_assignment(assignment_id, db)

    total_score = data.get("total_score", 0)
    total_questions = data.get("total_questions", 0)

    return {
        "success": True,
        "total_score": total_score,
        "total_questions": total_questions,
        "average_score": total_score / total_questions if total_questions > 0 else 0,
        "message": "Demo practice completed (progress not saved)",
        "preview_mode": True,
        "demo_mode": True,
    }
