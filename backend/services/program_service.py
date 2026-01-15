"""
Program Service Layer

Unified business logic for Program/Lesson/Content operations
Supporting both teacher-scoped and organization-scoped materials.

Service Architecture:
- Permission checking abstracted from routers
- Automatic scope detection (teacher vs organization)
- Reusable CRUD operations
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
import uuid
import logging
from datetime import datetime

from models import (
    Program,
    Lesson,
    Content,
    ContentItem,
    Teacher,
    Organization,
)
from utils.permissions import (
    has_manage_materials_permission,
    has_program_permission,
    has_lesson_permission,
    has_content_permission,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Program CRUD
# ============================================================================


def get_programs_by_scope(
    scope: str,
    teacher_id: int,
    db: Session,
    organization_id: Optional[uuid.UUID] = None,
    include_inactive: bool = False,
) -> List[Program]:
    """
    Get programs based on scope (teacher or organization).

    Args:
        scope: 'teacher' or 'organization'
        teacher_id: Current teacher ID
        db: Database session
        organization_id: Required if scope='organization'
        include_inactive: Include soft-deleted programs

    Returns:
        List of programs with full hierarchy
    """
    # Filter lessons and contents by is_active
    lessons_filter = Lesson.is_active.is_(True) if not include_inactive else True
    contents_filter = Content.is_active.is_(True) if not include_inactive else True

    query = db.query(Program).options(
        joinedload(Program.lessons.and_(lessons_filter))
        .joinedload(Lesson.contents.and_(contents_filter))
        .joinedload(Content.content_items)
    )

    if scope == "teacher":
        # Teacher-owned programs (personal materials)
        query = query.filter(
            Program.teacher_id == teacher_id,
            Program.organization_id.is_(None),
            Program.is_template.is_(True),
        )
    elif scope == "organization":
        if not organization_id:
            raise ValueError("organization_id required for organization scope")

        # Check permission first
        if not has_manage_materials_permission(teacher_id, organization_id, db):
            raise PermissionError("No permission to access organization materials")

        # Organization-owned programs
        query = query.filter(
            Program.organization_id == organization_id,
            Program.is_template.is_(True),
        )
    else:
        raise ValueError(f"Invalid scope: {scope}. Must be 'teacher' or 'organization'")

    if not include_inactive:
        query = query.filter(Program.is_active.is_(True))

    return query.all()


def create_program(
    scope: str,
    teacher_id: int,
    data: Dict[str, Any],
    db: Session,
    organization_id: Optional[uuid.UUID] = None,
) -> Program:
    """
    Create a new program.

    Args:
        scope: 'teacher' or 'organization'
        teacher_id: Creator teacher ID
        data: Program data (name, description, etc.)
        db: Database session
        organization_id: Required if scope='organization'

    Returns:
        Created program
    """
    if scope == "organization":
        if not organization_id:
            raise ValueError("organization_id required for organization scope")

        # Check permission
        if not has_manage_materials_permission(teacher_id, organization_id, db):
            raise PermissionError("No permission to create organization materials")

        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise ValueError("Organization not found")

        program = Program(
            name=data["name"],
            description=data.get("description"),
            level=data.get("level"),
            estimated_hours=data.get("estimated_hours"),
            tags=data.get("tags"),
            is_template=True,
            teacher_id=teacher_id,
            organization_id=organization_id,
            classroom_id=None,
            is_active=True,
            source_metadata={"created_by": teacher_id},
        )
    elif scope == "teacher":
        program = Program(
            name=data["name"],
            description=data.get("description"),
            level=data.get("level"),
            estimated_hours=data.get("estimated_hours"),
            tags=data.get("tags"),
            is_template=True,
            teacher_id=teacher_id,
            organization_id=None,
            classroom_id=None,
            is_active=True,
        )
    else:
        raise ValueError(f"Invalid scope: {scope}")

    db.add(program)
    db.commit()
    db.refresh(program)

    return program


def update_program(
    program_id: int, teacher_id: int, data: Dict[str, Any], db: Session
) -> Program:
    """
    Update program.

    Automatically checks permission based on program scope.
    """
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise ValueError("Program not found")

    # Check permission
    if not has_program_permission(db, program_id, teacher_id, "write"):
        raise PermissionError("No permission to update this program")

    # Update fields
    if "name" in data:
        program.name = data["name"]
    if "description" in data:
        program.description = data["description"]

    db.commit()
    db.refresh(program)

    return program


def delete_program(program_id: int, teacher_id: int, db: Session) -> Dict[str, Any]:
    """
    Soft delete program.

    Automatically checks permission based on program scope.
    """
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise ValueError("Program not found")

    # Check permission
    if not has_program_permission(db, program_id, teacher_id, "write"):
        raise PermissionError("No permission to delete this program")

    # Soft delete
    program.is_active = False
    program.deleted_at = datetime.now()

    db.commit()

    return {"message": "Program soft deleted successfully", "program_id": program_id}


# ============================================================================
# Lesson CRUD
# ============================================================================


def create_lesson(
    program_id: int, teacher_id: int, data: Dict[str, Any], db: Session
) -> Lesson:
    """
    Create lesson in program.

    Automatically checks program permission.
    """
    logger.info(f"[SERVICE_CREATE_LESSON] Called with program_id={program_id}, teacher_id={teacher_id}, data={data}")

    # Check program permission
    if not has_program_permission(db, program_id, teacher_id, "write"):
        logger.error(f"[SERVICE_CREATE_LESSON] Permission denied for teacher_id={teacher_id}, program_id={program_id}")
        raise PermissionError("No permission to create lessons in this program")

    logger.info(f"[SERVICE_CREATE_LESSON] Permission check passed. Creating lesson object...")

    lesson = Lesson(
        program_id=program_id,
        name=data["name"],
        description=data.get("description"),
        order_index=data.get("order_index", 1),
        estimated_minutes=data.get("estimated_minutes"),
        is_active=True,
    )

    logger.info(f"[SERVICE_CREATE_LESSON] Lesson object created (not yet added to DB): name={lesson.name}")

    db.add(lesson)
    logger.info(f"[SERVICE_CREATE_LESSON] db.add() called")

    db.commit()
    logger.info(f"[SERVICE_CREATE_LESSON] db.commit() called")

    db.refresh(lesson)
    logger.info(f"[SERVICE_CREATE_LESSON] db.refresh() called. Final lesson_id={lesson.id}, name={lesson.name}")

    # Post-commit verification
    duplicate_count = db.query(Lesson).filter(
        Lesson.program_id == program_id,
        Lesson.name == lesson.name,
        Lesson.is_active == True
    ).count()
    logger.info(f"[SERVICE_CREATE_LESSON] Post-commit check: Found {duplicate_count} lessons with name '{lesson.name}' in program {program_id}")

    if duplicate_count > 1:
        logger.error(f"[SERVICE_CREATE_LESSON] !!!! DUPLICATE DETECTED !!!! {duplicate_count} lessons found")

    return lesson


def update_lesson(
    lesson_id: int, teacher_id: int, data: Dict[str, Any], db: Session
) -> Lesson:
    """
    Update lesson.

    Automatically checks lesson->program permission chain.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise ValueError("Lesson not found")

    # Check permission via program
    if not has_lesson_permission(db, lesson_id, teacher_id, "write"):
        raise PermissionError("No permission to update this lesson")

    # Update fields
    if "name" in data:
        lesson.name = data["name"]
    if "description" in data:
        lesson.description = data["description"]
    if "order_index" in data:
        lesson.order_index = data["order_index"]

    db.commit()
    db.refresh(lesson)

    return lesson


def delete_lesson(lesson_id: int, teacher_id: int, db: Session) -> Dict[str, Any]:
    """
    Soft delete lesson.

    Automatically checks lesson->program permission chain.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise ValueError("Lesson not found")

    # Check permission via program
    if not has_lesson_permission(db, lesson_id, teacher_id, "write"):
        raise PermissionError("No permission to delete this lesson")

    # Soft delete
    lesson.is_active = False

    db.commit()

    return {"message": "Lesson soft deleted successfully", "lesson_id": lesson_id}


# ============================================================================
# Content CRUD
# ============================================================================


def create_content(
    lesson_id: int, teacher_id: int, data: Dict[str, Any], db: Session
) -> Content:
    """
    Create content in lesson.

    Automatically checks lesson->program permission chain.
    """
    # Check permission via lesson->program chain
    if not has_lesson_permission(db, lesson_id, teacher_id, "write"):
        raise PermissionError("No permission to create contents in this lesson")

    content = Content(
        lesson_id=lesson_id,
        type=data["type"],
        title=data["title"],
        order_index=data.get("order_index", 1),
        is_active=True,
    )

    db.add(content)
    db.commit()
    db.refresh(content)

    return content


def delete_content(content_id: int, teacher_id: int, db: Session) -> Dict[str, Any]:
    """
    Soft delete content.

    Automatically checks content->lesson->program permission chain.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise ValueError("Content not found")

    # Check permission via content->lesson->program chain
    if not has_content_permission(db, content_id, teacher_id, "write"):
        raise PermissionError("No permission to delete this content")

    # Soft delete
    content.is_active = False

    db.commit()

    return {"message": "Content soft deleted successfully", "content_id": content_id}
