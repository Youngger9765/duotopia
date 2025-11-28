"""
Classroom-School Relationship API Routes

Manages the linking of classrooms to schools within the organization hierarchy.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid

from database import get_db
from models import Teacher, School, Classroom, ClassroomSchool, ClassroomStudent, Assignment
from auth import verify_token


router = APIRouter(tags=["classroom-schools"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


# ============ Dependencies ============


async def get_current_teacher(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Teacher:
    """Get current authenticated teacher"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    teacher_id = payload.get("sub")
    teacher_type = payload.get("type")

    if teacher_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a teacher"
        )

    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    return teacher


# ============ Request/Response Models ============


class LinkClassroomRequest(BaseModel):
    """Request to link classroom to school"""

    school_id: str


class ClassroomSchoolResponse(BaseModel):
    """Response for classroom-school link"""

    id: int
    classroom_id: int
    school_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, link: ClassroomSchool):
        return cls(
            id=link.id,
            classroom_id=link.classroom_id,
            school_id=str(link.school_id),
            is_active=link.is_active,
            created_at=link.created_at,
        )


class SchoolInfo(BaseModel):
    """School information"""

    id: str
    organization_id: str
    name: str
    display_name: str | None
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, school: School):
        return cls(
            id=str(school.id),
            organization_id=str(school.organization_id),
            name=school.name,
            display_name=school.display_name,
            description=school.description,
            is_active=school.is_active,
        )


class ClassroomInfo(BaseModel):
    """Classroom information"""

    id: str
    name: str
    program_level: str
    is_active: bool
    created_at: datetime
    teacher_name: str | None = None
    teacher_email: str | None = None
    student_count: int = 0
    assignment_count: int = 0

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_counts(
        cls, classroom: Classroom, student_count: int, assignment_count: int
    ):
        return cls(
            id=str(classroom.id),
            name=classroom.name,
            program_level=classroom.level.value if classroom.level else "A1",
            is_active=classroom.is_active,
            created_at=classroom.created_at,
            teacher_name=classroom.teacher.name if classroom.teacher else None,
            teacher_email=classroom.teacher.email if classroom.teacher else None,
            student_count=student_count,
            assignment_count=assignment_count,
        )


# ============ API Endpoints ============


@router.post(
    "/api/classrooms/{classroom_id}/school",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomSchoolResponse,
)
async def link_classroom_to_school(
    classroom_id: int,
    request: LinkClassroomRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Link a classroom to a school.
    Classroom owner must be the requesting teacher.
    One classroom can only be linked to one school at a time.
    """
    # Verify classroom exists and belongs to teacher
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id,
            Classroom.teacher_id == teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you don't have permission",
        )

    # Verify school exists
    try:
        school_uuid = uuid.UUID(request.school_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid school ID format"
        )

    school = db.query(School).filter(School.id == school_uuid).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    # Check if classroom is already linked to a school
    existing_link = (
        db.query(ClassroomSchool)
        .filter(
            ClassroomSchool.classroom_id == classroom_id,
            ClassroomSchool.is_active.is_(True),
        )
        .first()
    )

    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classroom is already linked to a school",
        )

    # Create link
    link = ClassroomSchool(
        classroom_id=classroom_id,
        school_id=school_uuid,
        is_active=True,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return ClassroomSchoolResponse.from_orm(link)


@router.get("/api/classrooms/{classroom_id}/school", response_model=SchoolInfo)
async def get_classroom_school(
    classroom_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Get the school that a classroom is linked to.
    """
    # Verify classroom exists and belongs to teacher
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id,
            Classroom.teacher_id == teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you don't have permission",
        )

    # Get active link
    link = (
        db.query(ClassroomSchool)
        .filter(
            ClassroomSchool.classroom_id == classroom_id,
            ClassroomSchool.is_active.is_(True),
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom is not linked to any school",
        )

    # Get school
    school = db.query(School).filter(School.id == link.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return SchoolInfo.from_orm(school)


@router.delete("/api/classrooms/{classroom_id}/school")
async def unlink_classroom_from_school(
    classroom_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Unlink a classroom from its school (soft delete).
    """
    # Verify classroom exists and belongs to teacher
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id,
            Classroom.teacher_id == teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you don't have permission",
        )

    # Find active link
    link = (
        db.query(ClassroomSchool)
        .filter(
            ClassroomSchool.classroom_id == classroom_id,
            ClassroomSchool.is_active.is_(True),
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom is not linked to any school",
        )

    # Soft delete
    link.is_active = False
    db.commit()

    return {"message": "Classroom unlinked from school successfully"}


@router.get("/api/schools/{school_id}/classrooms", response_model=List[ClassroomInfo])
async def list_school_classrooms(
    school_id: uuid.UUID,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    List all classrooms in a school with student and assignment counts.
    Optimized to avoid N+1 queries.
    """
    # Verify school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    # Get all active classroom IDs for this school
    classroom_ids_subq = (
        db.query(ClassroomSchool.classroom_id)
        .filter(
            ClassroomSchool.school_id == school_id,
            ClassroomSchool.is_active.is_(True),
        )
        .subquery()
    )

    classroom_ids = db.query(classroom_ids_subq.c.classroom_id).scalar_subquery()

    # Create subqueries for counts
    student_counts = (
        db.query(
            ClassroomStudent.classroom_id,
            func.count(ClassroomStudent.student_id).label("count"),
        )
        .group_by(ClassroomStudent.classroom_id)
        .subquery()
    )

    assignment_counts = (
        db.query(
            Assignment.classroom_id, func.count(Assignment.id).label("count")
        )
        .group_by(Assignment.classroom_id)
        .subquery()
    )

    # Get classrooms with teacher preloaded and counts in a single query
    classrooms_query = (
        db.query(
            Classroom,
            func.coalesce(student_counts.c.count, 0).label("student_count"),
            func.coalesce(assignment_counts.c.count, 0).label("assignment_count"),
        )
        .options(joinedload(Classroom.teacher))
        .outerjoin(student_counts, Classroom.id == student_counts.c.classroom_id)
        .outerjoin(assignment_counts, Classroom.id == assignment_counts.c.classroom_id)
        .filter(Classroom.id.in_(classroom_ids), Classroom.is_active.is_(True))
        .all()
    )

    # Build result
    result = []
    for classroom, student_count, assignment_count in classrooms_query:
        result.append(
            ClassroomInfo.from_orm_with_counts(classroom, student_count, assignment_count)
        )

    return result
