"""
Unified permission checking utilities for Programs, Lessons, and Contents

Supports both:
1. Teacher-owned programs (teacher_id)
2. Organization-owned programs (organization_id + user role)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

from services.casbin_service import get_casbin_service
from models import Teacher, Program, Lesson, Content, TeacherOrganization


def has_manage_materials_permission(
    teacher_id: int, org_id: uuid.UUID, db: Session
) -> bool:
    """
    Check if teacher has manage_materials permission in organization.

    Permission hierarchy:
    - org_owner: Always has permission
    - org_admin: Needs explicit manage_materials permission via Casbin
    - teacher: No permission
    """
    membership = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher_id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if not membership:
        return False

    if membership.role == "org_owner":
        return True

    casbin = get_casbin_service()
    return casbin.check_permission(
        teacher_id=teacher_id,
        domain=f"org-{org_id}",
        resource="manage_materials",
        action="write",
    )


def has_school_materials_permission(
    teacher_id: int, school_id, db: Session
) -> bool:
    """
    Check if teacher can manage school materials.

    Permission rules:
    - school_admin role in the school: Has permission
    - org-level manage_materials permission: Has permission
    - Otherwise: No permission
    """
    from models import School, TeacherSchool

    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return False

    # Check school_admin role
    has_school_admin = db.query(TeacherSchool).filter(
        TeacherSchool.teacher_id == teacher_id,
        TeacherSchool.school_id == school_id,
        TeacherSchool.roles.contains(["school_admin"]),
        TeacherSchool.is_active.is_(True),
    ).first() is not None

    # Check org-level permission
    has_org_permission = has_manage_materials_permission(teacher_id, school.organization_id, db)

    return has_school_admin or has_org_permission


def has_program_permission(
    db: Session, program_id: int, teacher_id: int, action: str = "write"
) -> bool:
    """
    Check if teacher can perform action on program.

    Supports teacher-owned, organization-owned, and school-owned programs.
    """
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        return False

    # Teacher-owned (personal materials)
    if program.teacher_id and program.organization_id is None and program.school_id is None:
        return program.teacher_id == teacher_id

    # Organization-owned
    if program.organization_id and program.school_id is None:
        return has_manage_materials_permission(teacher_id, program.organization_id, db)

    # School-owned
    if program.school_id:
        return has_school_materials_permission(teacher_id, program.school_id, db)

    return False


def has_lesson_permission(
    db: Session, lesson_id: int, teacher_id: int, action: str = "write"
) -> bool:
    """
    Check if teacher can perform action on lesson.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        return False

    return has_program_permission(db, lesson.program_id, teacher_id, action)


def has_content_permission(
    db: Session, content_id: int, teacher_id: int, action: str = "write"
) -> bool:
    """
    Check if teacher can perform action on content.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return False

    return has_lesson_permission(db, content.lesson_id, teacher_id, action)


def check_program_access(
    db: Session,
    program_id: int,
    current_teacher: Teacher,
    require_owner: bool = False
) -> Program:
    """
    Check teacher's access to a Program

    Supports:
    1. Teacher Programs: teacher_id == current_teacher.id AND organization_id IS NULL
    2. Organization Programs: organization_id + teacher has access to org
    3. Template Programs: is_template = True (read-only for all teachers)

    Args:
        db: Database session
        program_id: Program ID to check
        current_teacher: Current authenticated teacher
        require_owner: If True, requires org_owner/org_admin role for org programs

    Returns:
        Program object if access granted

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.is_active.is_(True)
    ).first()

    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Case 1: Teacher's personal program
    if program.teacher_id == current_teacher.id and program.organization_id is None:
        return program

    # Case 2: Organization program
    if program.organization_id:
        # Check if teacher has access to this organization
        teacher_org = db.query(TeacherOrganization).filter(
            TeacherOrganization.teacher_id == current_teacher.id,
            TeacherOrganization.organization_id == program.organization_id,
            TeacherOrganization.is_active.is_(True)
        ).first()

        if not teacher_org:
            raise HTTPException(
                status_code=403,
                detail="No access to this organization's materials"
            )

        # Check role requirement for edit operations
        if require_owner and not has_manage_materials_permission(
            current_teacher.id, program.organization_id, db
        ):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions. Only org owners/admins can edit."
            )

        return program

    # Case 3: Template program (read-only for all teachers)
    if program.is_template:
        if require_owner:
            # Only the creator can edit templates
            if program.teacher_id != current_teacher.id:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot edit templates created by others"
                )
        return program

    raise HTTPException(status_code=403, detail="Access denied to this program")


def check_lesson_access(
    db: Session,
    lesson_id: int,
    current_teacher: Teacher,
    require_owner: bool = False
) -> tuple[Program, Lesson]:
    """
    Check teacher's access to a Lesson

    Returns:
        Tuple of (Program, Lesson) if access granted

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.is_active.is_(True)
    ).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check access to parent program
    program = check_program_access(db, lesson.program_id, current_teacher, require_owner)

    return program, lesson


def check_content_access(
    db: Session,
    content_id: int,
    current_teacher: Teacher,
    require_owner: bool = False,
    allow_assignment_copy: bool = True
) -> tuple[Program, Lesson, Content]:
    """
    Check teacher's access to a Content

    Args:
        allow_assignment_copy: If True, also allows access to assignment copies
                              owned by the teacher

    Returns:
        Tuple of (Program, Lesson, Content) if access granted

    Raises:
        HTTPException: 404 if not found, 403 if access denied
    """
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.is_active.is_(True)
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Special case: Assignment copies belong to the teacher's assignments
    if allow_assignment_copy and content.is_assignment_copy:
        # Check if this assignment copy belongs to the current teacher
        from models import Assignment, AssignmentContent

        assignment = db.query(Assignment).join(
            AssignmentContent,
            AssignmentContent.assignment_id == Assignment.id
        ).filter(
            AssignmentContent.content_id == content_id,
            Assignment.teacher_id == current_teacher.id,
            Assignment.is_active.is_(True)
        ).first()

        if assignment:
            # Return dummy program/lesson for assignment copies
            # (they don't belong to a program/lesson)
            return None, None, content

    # Check access to parent lesson and program
    program, lesson = check_lesson_access(db, content.lesson_id, current_teacher, require_owner)

    return program, lesson, content
