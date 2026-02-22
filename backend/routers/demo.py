"""
Demo router - Public demo assignment preview endpoints with rate limiting.

This module provides public access to demo assignments created by the demo teacher account.
No authentication required, but rate-limited to prevent abuse.

Includes:
- Demo Azure Speech Token endpoint (with daily quota)
- Demo assignment preview endpoints
- Demo speech assessment endpoints
"""

import logging
import os
import random
from typing import Optional
from pydantic import BaseModel
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
    Header,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session, selectinload
from core.limiter import limiter
from core.demo_quota import (
    get_demo_quota_manager,
    validate_referer,
    reset_demo_quota,
    DEMO_TOKEN_DAILY_LIMIT,
)
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


# ============================================================================
# Request Models
# ============================================================================


class WordSelectionAnswerRequest(BaseModel):
    item_id: int
    selected_translation: str


class RearrangementAnswerRequest(BaseModel):
    item_id: int
    user_answer: str


class RearrangementCompleteRequest(BaseModel):
    total_score: int = 0
    total_questions: int = 0


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
# Demo Azure Speech Token
# ============================================================================


def get_client_ip(request: Request) -> str:
    """Get real client IP from trusted proxy (Cloud Run / GCP Load Balancer).

    Uses the rightmost IP in X-Forwarded-For, which is the one appended by
    the last trusted proxy (e.g., Cloud Run ingress). The leftmost IP can be
    spoofed by the client, so we avoid using it for quota enforcement.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",")]
        # Always use rightmost — appended by our trusted proxy
        return ips[-1]
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/azure-speech/token")
@limiter.limit("5/minute")
async def get_demo_speech_token(request: Request):
    """
    Demo-only Azure Speech Token endpoint.

    This endpoint provides Azure Speech tokens for demo users without authentication.
    Protected by multiple layers:
    1. Rate Limit: 5 requests per minute per IP (slowapi)
    2. Daily Quota: 60 requests per day per IP
    3. Referer Validation: Only accepts requests from allowed origins
    4. Short Token TTL: 5 minutes (vs normal 10 minutes)

    Rate limit: 5 requests per minute per IP.
    Daily limit: 60 requests per day per IP.

    Returns:
        {
            "token": "<azure-speech-token>",
            "region": "eastasia",
            "expires_in": 300,
            "demo_mode": true,
            "remaining_today": <remaining quota>
        }

    Errors:
        403: Invalid referer
        429: Rate limit or daily quota exceeded
        500: Azure token service error
    """
    client_ip = get_client_ip(request)
    referer = request.headers.get("referer", "")

    # Layer 1: Referer validation
    if not validate_referer(referer):
        logger.warning(
            f"Demo token rejected - invalid referer: {referer}, IP: {client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request origin",
        )

    # Layer 2: Daily quota check
    quota_manager = get_demo_quota_manager()
    allowed, quota_info = quota_manager.check_and_increment(client_ip)

    if not allowed:
        logger.info(
            f"Demo token daily limit reached: IP={client_ip}, limit={DEMO_TOKEN_DAILY_LIMIT}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "daily_limit_exceeded",
                "message": "今日免費試用次數已達上限",
                "suggestion": "註冊帳號即可無限使用",
                "limit": DEMO_TOKEN_DAILY_LIMIT,
                "reset_at": quota_info["reset_at"],
            },
        )

    # Layer 3: Get token from Azure
    try:
        from services.azure_speech_token import get_azure_speech_token_service

        token_service = get_azure_speech_token_service()
        token_data = await token_service.get_token()

        logger.info(
            f"Demo token issued: IP={client_ip}, "
            f"remaining={quota_info['remaining']}/{DEMO_TOKEN_DAILY_LIMIT}, "
            f"referer={referer[:50] if referer else 'none'}"
        )

        return {
            "token": token_data["token"],
            "region": token_data["region"],
            "expires_in": 300,  # 5 minutes (shorter than normal 10 min)
            "demo_mode": True,
            "remaining_today": quota_info["remaining"],
        }

    except Exception as e:
        logger.error(f"Demo token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get speech token",
        )


@router.post("/azure-speech/reset-quota")
async def reset_demo_quota_endpoint(
    request: Request,
    ip: str = None,
    admin_secret: Optional[str] = Header(default=None, alias="X-Admin-Secret"),
):
    """
    Reset demo token quota (development/staging only).

    This endpoint is only available in non-production environments
    for testing purposes. In staging, requires DEMO_RESET_SECRET.

    Args:
        ip: Optional specific IP to reset. If not provided, resets caller's IP.
        admin_secret: Required in staging for authorization.

    Returns:
        Number of entries reset
    """
    environment = os.getenv("ENVIRONMENT", "development")

    # Only allow in non-production environments
    if environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is not available in production",
        )

    # Require secret in staging
    if environment == "staging":
        expected_secret = os.getenv("DEMO_RESET_SECRET")
        if not expected_secret or admin_secret != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized",
            )

    # If no IP specified, reset the caller's IP
    target_ip = ip or get_client_ip(request)

    count = reset_demo_quota(target_ip)
    logger.info(f"Demo quota reset: IP={target_ip}, count={count}")

    return {
        "success": True,
        "message": f"Reset quota for {target_ip}",
        "entries_reset": count,
    }


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

    # Build items list (matching teacher API format)
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
        "assignment_id": assignment.id,
        "title": assignment.title,
        "status": "preview",
        "practice_mode": "word_reading",
        "show_translation": (
            assignment.show_translation
            if assignment.show_translation is not None
            else True
        ),
        "show_image": (
            assignment.show_image if assignment.show_image is not None else True
        ),
        "time_limit_per_question": assignment.time_limit_per_question or 0,
        "total_items": len(items),
        "items": items,
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
    # from services.translation import translation_service  # disabled (#303)

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
        raise HTTPException(
            status_code=404, detail="No vocabulary items found for this assignment"
        )

    # Record total words before limiting
    total_words_in_assignment = len(content_items)

    # Shuffle if needed
    if assignment.shuffle_questions:
        random.shuffle(content_items)

    # Limit to 10 words (consistent with student API)
    content_items = content_items[:10]

    # NOTE: AI distractor generation is temporarily disabled (#303).
    # All distractors now come from other words in the assignment.
    #
    # --- AI distractor generation (disabled) ---
    # items_needing_generation = [item for item in content_items if not item.distractors]
    # if items_needing_generation:
    #     words_for_distractors = [
    #         {"word": item.text, "translation": item.translation or ""}
    #         for item in items_needing_generation
    #     ]
    #     try:
    #         generated = await translation_service.batch_generate_distractors(
    #             words_for_distractors, count=2
    #         )
    #         for i, item in enumerate(items_needing_generation):
    #             if i < len(generated):
    #                 item._generated_distractors = generated[i]
    #     except Exception as e:
    #         logger.error(f"Failed to generate distractors for demo preview: {e}")
    #         for item in items_needing_generation:
    #             item._generated_distractors = ["選項A", "選項B", "選項C"]
    # --- end AI distractor generation ---

    # Build response data
    words_with_options = []

    # Collect all unique translations for picking distractors from the word set
    all_translations = {
        item.translation.lower().strip(): item.translation
        for item in content_items
        if item.translation
    }

    for item in content_items:
        correct_answer = item.translation or ""

        # Pick 3 random distractors from other words' translations (#303)
        other_translations = [
            t
            for key, t in all_translations.items()
            if key != correct_answer.lower().strip()
        ]
        random.shuffle(other_translations)
        final_distractors = other_translations[:3]

        # Build options array and shuffle
        options = [correct_answer] + final_distractors
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
        "total_words": total_words_in_assignment,  # Total words in assignment, not current practice
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
@limiter.limit("120/minute")  # Higher limit for interactive practice
async def demo_word_selection_answer(
    request: Request,
    assignment_id: int,
    data: WordSelectionAnswerRequest,
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

    item_id = data.item_id
    selected_translation = data.selected_translation

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

    # Shuffle items if configured (before building questions)
    if assignment.shuffle_questions:
        random.shuffle(content_items)

    # Build questions list
    questions = []
    for item in content_items:
        # Split sentence into words and shuffle
        words = item.text.strip().split()
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)

        question = {
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
            "original_text": item.text.strip(),
        }
        questions.append(question)

    return {
        "student_assignment_id": assignment.id,
        "practice_mode": "rearrangement",
        "score_category": assignment.score_category,
        "questions": questions,
        "total_questions": len(questions),
    }


@router.post("/assignments/{assignment_id}/preview/rearrangement-answer")
@limiter.limit("120/minute")  # Higher limit for interactive practice
async def demo_rearrangement_answer(
    request: Request,
    assignment_id: int,
    data: RearrangementAnswerRequest,
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

    item_id = data.item_id
    user_answer = data.user_answer

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
    data: RearrangementCompleteRequest,
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

    total_score = data.total_score
    total_questions = data.total_questions

    return {
        "success": True,
        "total_score": total_score,
        "total_questions": total_questions,
        "average_score": total_score / total_questions if total_questions > 0 else 0,
        "message": "Demo practice completed (progress not saved)",
        "preview_mode": True,
        "demo_mode": True,
    }
