"""Teacher review API endpoints for item-level grading"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from jose import jwt
from core.config import settings

from database import get_db
from models import StudentItemProgress, Teacher, StudentAssignment
from schemas import (
    TeacherReviewCreate,
    TeacherReviewUpdate,
    TeacherReviewResponse,
    TeacherReviewBatchCreate,
)

router = APIRouter(prefix="/api/teacher-review", tags=["teacher-review"])
logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_teacher(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> Teacher:
    """Get current teacher from JWT token"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get("user_type")
        user_id = payload.get("user_id")

        if user_type != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized as teacher",
            )

        teacher = db.query(Teacher).filter(Teacher.id == user_id).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
            )

        return teacher

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@router.post("/item/{item_progress_id}", response_model=TeacherReviewResponse)
async def review_student_item(
    item_progress_id: int,
    review: TeacherReviewCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Submit teacher review for a specific student item"""

    # Get item progress
    item_progress = (
        db.query(StudentItemProgress)
        .filter(StudentItemProgress.id == item_progress_id)
        .first()
    )

    if not item_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student item progress not found",
        )

    # Update review fields
    item_progress.teacher_review_score = review.teacher_review_score
    item_progress.teacher_feedback = review.teacher_feedback
    item_progress.teacher_reviewed_at = datetime.utcnow()
    item_progress.teacher_id = current_teacher.id
    item_progress.review_status = "REVIEWED"

    db.commit()
    db.refresh(item_progress)

    # Prepare response with additional info
    response = TeacherReviewResponse(
        student_item_progress_id=item_progress.id,
        teacher_review_score=item_progress.teacher_review_score,
        teacher_feedback=item_progress.teacher_feedback,
        teacher_reviewed_at=item_progress.teacher_reviewed_at,
        teacher_id=item_progress.teacher_id,
        review_status=item_progress.review_status,
        student_name=None,  # Will be populated if needed
        item_text=item_progress.content_item.text
        if item_progress.content_item
        else None,
    )

    return response


@router.patch("/item/{item_progress_id}", response_model=TeacherReviewResponse)
async def update_teacher_review(
    item_progress_id: int,
    review: TeacherReviewUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Update existing teacher review"""

    item_progress = (
        db.query(StudentItemProgress)
        .filter(
            and_(
                StudentItemProgress.id == item_progress_id,
                StudentItemProgress.teacher_id == current_teacher.id,
            )
        )
        .first()
    )

    if not item_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or you don't have permission to update it",
        )

    # Update only provided fields
    if review.teacher_review_score is not None:
        item_progress.teacher_review_score = review.teacher_review_score
    if review.teacher_feedback is not None:
        item_progress.teacher_feedback = review.teacher_feedback

    item_progress.teacher_reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(item_progress)

    return TeacherReviewResponse(
        student_item_progress_id=item_progress.id,
        teacher_review_score=item_progress.teacher_review_score,
        teacher_feedback=item_progress.teacher_feedback,
        teacher_reviewed_at=item_progress.teacher_reviewed_at,
        teacher_id=item_progress.teacher_id,
        review_status=item_progress.review_status,
        student_name=None,
        item_text=item_progress.content_item.text
        if item_progress.content_item
        else None,
    )


@router.get("/assignment/{assignment_id}/items", response_model=List[dict])
async def get_assignment_items_for_review(
    assignment_id: int,
    student_id: Optional[int] = Query(None),
    review_status: Optional[str] = Query(None, pattern="^(PENDING|REVIEWED)$"),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Get all items for an assignment that need review"""

    query = (
        db.query(StudentItemProgress)
        .join(StudentAssignment)
        .options(
            joinedload(StudentItemProgress.content_item),
            joinedload(StudentItemProgress.student_assignment).joinedload(
                StudentAssignment.student
            ),
        )
        .filter(StudentAssignment.assignment_id == assignment_id)
    )

    if student_id:
        query = query.filter(StudentAssignment.student_id == student_id)

    if review_status:
        query = query.filter(StudentItemProgress.review_status == review_status)

    items = query.all()

    # Format response
    result = []
    for item in items:
        result.append(
            {
                "student_item_progress_id": item.id,
                "student_id": item.student_assignment.student_id,
                "student_name": item.student_assignment.student.name,
                "item_text": item.content_item.text if item.content_item else None,
                "student_answer": item.answer_text,
                "recording_url": item.recording_url,
                "ai_scores": {
                    "accuracy": float(item.accuracy_score)
                    if item.accuracy_score
                    else None,
                    "fluency": float(item.fluency_score)
                    if item.fluency_score
                    else None,
                    "pronunciation": float(item.pronunciation_score)
                    if item.pronunciation_score
                    else None,
                },
                "teacher_review": {
                    "score": float(item.teacher_review_score)
                    if item.teacher_review_score
                    else None,
                    "feedback": item.teacher_feedback,
                    "reviewed_at": item.teacher_reviewed_at,
                    "teacher_id": item.teacher_id,
                },
                "review_status": item.review_status,
            }
        )

    return result


@router.post("/batch", response_model=dict)
async def batch_review_items(
    batch_review: TeacherReviewBatchCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Submit reviews for multiple items at once"""

    # 🔥 Preload all StudentItemProgress records (avoid N+1)
    progress_ids = [r["student_item_progress_id"] for r in batch_review.item_reviews]
    all_item_progress = (
        db.query(StudentItemProgress)
        .filter(StudentItemProgress.id.in_(progress_ids))
        .all()
    )
    progress_map = {ip.id: ip for ip in all_item_progress}

    success_count = 0
    failed_items = []

    for review_data in batch_review.item_reviews:
        try:
            # 🔥 Get from preloaded map (no query)
            item_progress = progress_map.get(review_data["student_item_progress_id"])

            if item_progress:
                item_progress.teacher_review_score = review_data["teacher_review_score"]
                item_progress.teacher_feedback = review_data["teacher_feedback"]
                item_progress.teacher_reviewed_at = datetime.utcnow()
                item_progress.teacher_id = current_teacher.id
                item_progress.review_status = "REVIEWED"
                success_count += 1
            else:
                failed_items.append(
                    {
                        "id": review_data["student_item_progress_id"],
                        "error": "Not found",
                    }
                )
        except Exception as e:
            logger.error(
                f"Failed to process review for item {review_data.get('student_item_progress_id')}: {str(e)}"
            )
            failed_items.append(
                {
                    "id": review_data.get("student_item_progress_id"),
                    "error": "處理失敗，請稍後再試",
                }
            )

    db.commit()

    return {
        "success_count": success_count,
        "failed_count": len(failed_items),
        "failed_items": failed_items,
    }


@router.delete("/item/{item_progress_id}")
async def delete_teacher_review(
    item_progress_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Remove teacher review (reset to AI scores only)"""

    item_progress = (
        db.query(StudentItemProgress)
        .filter(
            and_(
                StudentItemProgress.id == item_progress_id,
                StudentItemProgress.teacher_id == current_teacher.id,
            )
        )
        .first()
    )

    if not item_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or you don't have permission to delete it",
        )

    # Reset teacher review fields
    item_progress.teacher_review_score = None
    item_progress.teacher_feedback = None
    item_progress.teacher_reviewed_at = None
    item_progress.teacher_id = None
    item_progress.review_status = "PENDING"

    db.commit()

    return {"message": "Teacher review removed successfully"}
