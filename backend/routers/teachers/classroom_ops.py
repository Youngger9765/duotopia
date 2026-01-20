"""
Classroom Ops operations for teachers.
"""
from fastapi import APIRouter, Depends, HTTPException
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
)
from .dependencies import get_current_teacher
from .validators import *
from .utils import TEST_SUBSCRIPTION_WHITELIST, parse_birthdate

router = APIRouter()


@router.get("/classrooms")
async def get_teacher_classrooms(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """取得教師的所有班級"""

    # Get classrooms with students (only active classrooms)
    classrooms = (
        db.query(Classroom)
        .filter(
            Classroom.teacher_id == current_teacher.id,
            Classroom.is_active.is_(True),  # Only show active classrooms
        )
        .options(
            selectinload(Classroom.students).selectinload(ClassroomStudent.student)
        )
        .all()
    )

    # Get program counts in a single query for all classrooms
    program_counts = (
        db.query(Program.classroom_id, func.count(Program.id).label("count"))
        .filter(
            Program.classroom_id.in_([c.id for c in classrooms]),
            Program.is_active.is_(True),
        )
        .group_by(Program.classroom_id)
        .all()
    )

    # Convert to dict for easy lookup
    program_count_map = {pc.classroom_id: pc.count for pc in program_counts}

    return [
        {
            "id": classroom.id,
            "name": classroom.name,
            "description": classroom.description,
            "level": classroom.level.value if classroom.level else "A1",
            "student_count": len([s for s in classroom.students if s.is_active]),
            "program_count": program_count_map.get(classroom.id, 0),  # Efficient lookup
            "created_at": (
                classroom.created_at.isoformat() if classroom.created_at else None
            ),
            "students": [
                {
                    "id": cs.student.id,
                    "name": cs.student.name,
                    "email": cs.student.email,
                    "student_id": cs.student.student_number,
                    "birthdate": (
                        cs.student.birthdate.isoformat()
                        if cs.student.birthdate
                        else None
                    ),
                    "password_changed": cs.student.password_changed,
                    "last_login": (
                        cs.student.last_login.isoformat()
                        if cs.student.last_login
                        else None
                    ),
                    "phone": "",  # Privacy: don't expose phone numbers in list
                    "status": "active" if cs.student.is_active else "inactive",
                }
                for cs in classroom.students
                if cs.is_active
            ],
        }
        for classroom in classrooms
    ]


@router.post("/classrooms")
async def create_classroom(
    classroom_data: ClassroomCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """創建新班級"""
    classroom = Classroom(
        name=classroom_data.name,
        description=classroom_data.description,
        level=getattr(
            ProgramLevel,
            classroom_data.level.upper().replace("-", "_"),
            ProgramLevel.A1,
        ),
        teacher_id=current_teacher.id,
        is_active=True,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return {
        "id": classroom.id,
        "name": classroom.name,
        "description": classroom.description,
        "level": classroom.level.value,
        "teacher_id": classroom.teacher_id,
    }


@router.get("/classrooms/{classroom_id}")
async def get_classroom(
    classroom_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """取得單一班級資料"""
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id, Classroom.teacher_id == current_teacher.id
        )
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    return {
        "id": classroom.id,
        "name": classroom.name,
        "description": classroom.description,
        "level": classroom.level.value if classroom.level else "A1",
        "teacher_id": classroom.teacher_id,
    }


@router.get("/classrooms/{classroom_id}/students")
async def get_classroom_students(
    classroom_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """取得班級的學生列表"""
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id,
            Classroom.teacher_id == current_teacher.id,
            Classroom.is_active.is_(True),
        )
        .options(
            selectinload(Classroom.students).selectinload(ClassroomStudent.student)
        )
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    return [
        {
            "id": cs.student.id,
            "name": cs.student.name,
            "email": cs.student.email,
            "student_number": cs.student.student_number,
            "birthdate": (
                cs.student.birthdate.isoformat() if cs.student.birthdate else None
            ),
            "password_changed": cs.student.password_changed,
            "last_login": (
                cs.student.last_login.isoformat() if cs.student.last_login else None
            ),
            "phone": "",
            "status": "active" if cs.student.is_active else "inactive",
        }
        for cs in classroom.students
        if cs.is_active
    ]


@router.put("/classrooms/{classroom_id}")
async def update_classroom(
    classroom_id: int,
    update_data: ClassroomUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """更新班級資料"""
    from utils.permissions import check_classroom_is_personal
    
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id, Classroom.teacher_id == current_teacher.id
        )
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Check if classroom belongs to school (should not be allowed)
    if not check_classroom_is_personal(classroom.id, db):
        raise HTTPException(
            status_code=403,
            detail="此班級屬於學校，請通過學校後台編輯"
        )

    if update_data.name is not None:
        classroom.name = update_data.name
    if update_data.description is not None:
        classroom.description = update_data.description
    if update_data.level is not None:
        classroom.level = getattr(
            ProgramLevel, update_data.level.upper().replace("-", "_"), ProgramLevel.A1
        )

    db.commit()
    db.refresh(classroom)

    return {
        "id": classroom.id,
        "name": classroom.name,
        "description": classroom.description,
        "level": classroom.level.value,
    }


@router.delete("/classrooms/{classroom_id}")
async def delete_classroom(
    classroom_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """刪除班級"""
    from utils.permissions import check_classroom_is_personal
    
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id, Classroom.teacher_id == current_teacher.id
        )
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Check if classroom belongs to school (should not be allowed)
    if not check_classroom_is_personal(classroom.id, db):
        raise HTTPException(
            status_code=403,
            detail="此班級屬於學校，請通過學校後台刪除"
        )

    # Soft delete by setting is_active = False
    classroom.is_active = False
    db.commit()

    return {"message": "Classroom deleted successfully"}


# ------------ Student CRUD ------------
class StudentCreate(BaseModel):
    name: str
    email: Optional[str] = None  # Email（選填，可以是真實 email）
    birthdate: str  # YYYY-MM-DD format
    classroom_id: Optional[int] = None  # 班級改為選填，可以之後再分配
    student_number: Optional[str] = None
    phone: Optional[str] = None  # 新增 phone 欄位


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None  # 可更新為真實 email
    student_number: Optional[str] = None
    birthdate: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    target_wpm: Optional[int] = None
    target_accuracy: Optional[float] = None
    classroom_id: Optional[int] = None  # 新增班級分配功能


class BatchStudentCreate(BaseModel):
    students: List[Dict[str, Any]]
