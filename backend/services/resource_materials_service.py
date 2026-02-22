"""
Resource Materials Service

Business logic for the Resource Materials Pack feature.
Manages browsing and copying programs from the resource account (contact@duotopia.co).
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, cast, Date
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
import uuid
import logging

from models import (
    Program,
    Lesson,
    Content,
    ContentItem,
    Teacher,
    ProgramCopyLog,
)
from models.program import COPIED_BY_INDIVIDUAL, COPIED_BY_ORGANIZATION
from core.config import settings
from services.program_service import copy_program_tree_to_template

logger = logging.getLogger(__name__)

DAILY_COPY_LIMIT = 10


def get_resource_account(db: Session) -> Optional[Teacher]:
    """Get the resource account teacher by configured email."""
    return (
        db.query(Teacher)
        .filter(Teacher.email == settings.RESOURCE_ACCOUNT_EMAIL)
        .first()
    )


def list_resource_materials(
    db: Session,
    scope: str,
    viewer_teacher_id: Optional[int] = None,
    organization_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List available resource materials filtered by visibility.

    Args:
        db: Database session
        scope: 'individual' or 'organization'
        viewer_teacher_id: Current teacher ID (for individual scope)
        organization_id: Organization ID (for organization scope)

    Returns:
        List of program dicts with lesson/content counts and copy status
    """
    resource_account = get_resource_account(db)
    if not resource_account:
        logger.warning(f"Resource account not found: {settings.RESOURCE_ACCOUNT_EMAIL}")
        return []

    # Base query: active templates owned by resource account (personal, not org/school)
    query = db.query(Program).filter(
        Program.teacher_id == resource_account.id,
        Program.is_template.is_(True),
        Program.is_active.is_(True),
        Program.organization_id.is_(None),
        Program.school_id.is_(None),
    )

    # Filter by visibility based on scope
    if scope == "individual":
        # Resource account can see all their own programs
        if viewer_teacher_id == resource_account.id:
            pass  # No visibility filter
        else:
            query = query.filter(Program.visibility.in_(["public", "individual_only"]))
    elif scope == "organization":
        query = query.filter(Program.visibility.in_(["public", "organization_only"]))
    else:
        raise ValueError(f"Invalid scope: {scope}")

    programs = (
        query.options(joinedload(Program.lessons).joinedload(Lesson.contents))
        .order_by(Program.order_index)
        .all()
    )

    # Get today's copy status (use UTC to match TIMESTAMPTZ)
    today = datetime.now(timezone.utc).date()
    if scope == "individual" and viewer_teacher_id:
        copied_by_id = str(viewer_teacher_id)
        copied_by_type = COPIED_BY_INDIVIDUAL
    elif scope == "organization" and organization_id:
        copied_by_id = str(organization_id)
        copied_by_type = COPIED_BY_ORGANIZATION
    else:
        copied_by_id = None
        copied_by_type = None

    # Count copies per program today (not just boolean)
    copy_counts_today: dict = {}
    if copied_by_id and copied_by_type:
        logs = (
            db.query(
                ProgramCopyLog.source_program_id,
                func.count().label("cnt"),
            )
            .filter(
                ProgramCopyLog.copied_by_type == copied_by_type,
                ProgramCopyLog.copied_by_id == copied_by_id,
                cast(ProgramCopyLog.copied_at, Date) == today,
            )
            .group_by(ProgramCopyLog.source_program_id)
            .all()
        )
        copy_counts_today = {row.source_program_id: row.cnt for row in logs}

    results = []
    for program in programs:
        active_lessons = [ls for ls in program.lessons if ls.is_active]
        total_contents = sum(
            len(
                [
                    c
                    for c in ls.contents
                    if c.is_active
                    and not (hasattr(c, "is_assignment_copy") and c.is_assignment_copy)
                ]
            )
            for ls in active_lessons
        )
        count = copy_counts_today.get(program.id, 0)

        results.append(
            {
                "id": program.id,
                "name": program.name,
                "description": program.description,
                "level": program.level.value if program.level else None,
                "visibility": program.visibility,
                "estimated_hours": program.estimated_hours,
                "tags": program.tags,
                "order_index": program.order_index,
                "lesson_count": len(active_lessons),
                "content_count": total_contents,
                "copied_today": count >= DAILY_COPY_LIMIT,
                "copy_count_today": count,
                "created_at": (
                    program.created_at.isoformat() if program.created_at else None
                ),
            }
        )

    return results


def get_resource_material_detail(
    db: Session, program_id: int
) -> Optional[Dict[str, Any]]:
    """
    Get detailed resource material with full hierarchy (read-only view).
    """
    resource_account = get_resource_account(db)
    if not resource_account:
        return None

    program = (
        db.query(Program)
        .options(
            joinedload(Program.lessons)
            .joinedload(Lesson.contents)
            .joinedload(Content.content_items)
        )
        .filter(
            Program.id == program_id,
            Program.teacher_id == resource_account.id,
            Program.is_template.is_(True),
            Program.is_active.is_(True),
        )
        .first()
    )

    if not program:
        return None

    lessons_data = []
    for lesson in sorted(program.lessons, key=lambda ls: ls.order_index):
        if not lesson.is_active:
            continue

        contents_data = []
        for content in sorted(lesson.contents, key=lambda c: c.order_index):
            if not content.is_active:
                continue
            if hasattr(content, "is_assignment_copy") and content.is_assignment_copy:
                continue

            items_data = []
            for item in sorted(content.content_items, key=lambda i: i.order_index):
                items_data.append(
                    {
                        "id": item.id,
                        "order_index": item.order_index,
                        "text": item.text,
                        "translation": item.translation,
                    }
                )

            contents_data.append(
                {
                    "id": content.id,
                    "title": content.title,
                    "type": content.type.value if content.type else None,
                    "order_index": content.order_index,
                    "item_count": len(items_data),
                    "items": items_data,
                }
            )

        lessons_data.append(
            {
                "id": lesson.id,
                "name": lesson.name,
                "description": lesson.description,
                "order_index": lesson.order_index,
                "content_count": len(contents_data),
                "contents": contents_data,
            }
        )

    return {
        "id": program.id,
        "name": program.name,
        "description": program.description,
        "level": program.level.value if program.level else None,
        "visibility": program.visibility,
        "estimated_hours": program.estimated_hours,
        "tags": program.tags,
        "lesson_count": len(lessons_data),
        "lessons": lessons_data,
        "created_at": (program.created_at.isoformat() if program.created_at else None),
    }


def check_copy_limit(
    db: Session,
    source_program_id: int,
    copied_by_type: str,
    copied_by_id: str,
) -> bool:
    """
    Check if the copy limit (10 per day per course) has been reached.

    Returns True if copying is allowed, False if limit reached.
    """
    today = datetime.now(timezone.utc).date()
    count = (
        db.query(ProgramCopyLog)
        .filter(
            ProgramCopyLog.source_program_id == source_program_id,
            ProgramCopyLog.copied_by_type == copied_by_type,
            ProgramCopyLog.copied_by_id == copied_by_id,
            cast(ProgramCopyLog.copied_at, Date) == today,
        )
        .count()
    )
    return count < DAILY_COPY_LIMIT


def copy_resource_material(
    db: Session,
    program_id: int,
    target_type: str,
    teacher_id: int,
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Copy a resource material to individual's materials or organization materials.

    Args:
        db: Database session
        program_id: Source program ID
        target_type: 'individual' or 'organization'
        teacher_id: Current teacher ID
        organization_id: Target organization ID (required if target_type='organization')

    Returns:
        Dict with copied program info
    """
    resource_account = get_resource_account(db)
    if not resource_account:
        raise ValueError("Resource account not found")

    # Load source program with full tree
    source_program = (
        db.query(Program)
        .options(
            joinedload(Program.lessons)
            .joinedload(Lesson.contents)
            .joinedload(Content.content_items)
        )
        .filter(
            Program.id == program_id,
            Program.teacher_id == resource_account.id,
            Program.is_template.is_(True),
            Program.is_active.is_(True),
        )
        .first()
    )

    if not source_program:
        raise ValueError("Resource material not found")

    # Determine copied_by for rate limiting
    if target_type == "individual":
        copied_by_type = COPIED_BY_INDIVIDUAL
        copied_by_id = str(teacher_id)
    elif target_type == "organization":
        if not organization_id:
            raise ValueError("organization_id required for organization copy")
        copied_by_type = COPIED_BY_ORGANIZATION
        copied_by_id = str(organization_id)
    else:
        raise ValueError(f"Invalid target_type: {target_type}")

    # Check visibility permission
    visibility = source_program.visibility
    if target_type == "individual" and teacher_id != resource_account.id:
        if visibility not in ("public", "individual_only"):
            raise PermissionError("This material is not available for individual users")
    elif target_type == "organization":
        if visibility not in ("public", "organization_only"):
            raise PermissionError("This material is not available for organizations")

    # Check daily copy limit
    if not check_copy_limit(db, program_id, copied_by_type, copied_by_id):
        raise ValueError("Daily copy limit reached for this course")

    # Perform the copy
    source_metadata = {
        "source_type": "resource_pack",
        "resource_program_id": source_program.id,
        "resource_program_name": source_program.name,
        "resource_account_email": settings.RESOURCE_ACCOUNT_EMAIL,
    }

    try:
        if target_type == "individual":
            new_program = copy_program_tree_to_template(
                source_program=source_program,
                target_teacher_id=teacher_id,
                db=db,
                source_type="resource_pack",
                source_metadata=source_metadata,
            )
        elif target_type == "organization":
            new_program = copy_program_tree_to_template(
                source_program=source_program,
                target_teacher_id=teacher_id,
                db=db,
                source_type="resource_pack",
                source_metadata={
                    **source_metadata,
                    "organization_id": organization_id,
                },
            )
            # Set organization ownership
            new_program.organization_id = uuid.UUID(organization_id)
            db.flush()

        # Record the copy
        copy_log = ProgramCopyLog(
            source_program_id=program_id,
            copied_by_type=copied_by_type,
            copied_by_id=copied_by_id,
            copied_program_id=new_program.id,
        )
        db.add(copy_log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to copy resource material {program_id}: {e}", exc_info=True)
        raise

    return {
        "message": "Program copied successfully",
        "source_program_id": program_id,
        "copied_program_id": new_program.id,
        "copied_program_name": new_program.name,
        "target_type": target_type,
    }


def update_program_visibility(
    db: Session,
    program_id: int,
    teacher_id: int,
    visibility: str,
) -> Dict[str, Any]:
    """
    Update program visibility. Only the resource account can do this.
    """
    resource_account = get_resource_account(db)
    if not resource_account or teacher_id != resource_account.id:
        raise PermissionError("Only the resource account can update visibility")

    valid_values = {"private", "public", "organization_only", "individual_only"}
    if visibility not in valid_values:
        raise ValueError(f"Invalid visibility: {visibility}")

    program = (
        db.query(Program)
        .filter(
            Program.id == program_id,
            Program.teacher_id == resource_account.id,
            Program.is_active.is_(True),
        )
        .first()
    )

    if not program:
        raise ValueError("Program not found")

    program.visibility = visibility
    db.commit()

    return {
        "message": "Visibility updated",
        "program_id": program_id,
        "visibility": visibility,
    }
