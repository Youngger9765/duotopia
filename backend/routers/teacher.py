"""
Teacher API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
from database import get_db
from models import Teacher, Classroom, Student, ClassroomStudent, Program, Lesson, Content, StudentAssignment
from auth import get_current_teacher
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Response Models
class TeacherProfile(BaseModel):
    id: int
    email: str
    name: str
    phone: str | None = None
    is_demo: bool
    is_active: bool

class StudentInfo(BaseModel):
    id: int
    name: str
    email: str
    student_id: str | None = None

class ClassroomInfo(BaseModel):
    id: int
    name: str
    description: str | None = None
    level: str
    students: List[StudentInfo] = []
    student_count: int = 0

class ProgramInfo(BaseModel):
    id: int
    name: str
    description: str | None = None
    level: str
    classroom_id: int
    classroom_name: str
    estimated_hours: int | None = None
    lesson_count: int = 0

class DashboardStats(BaseModel):
    total_classrooms: int
    total_students: int
    total_programs: int
    active_assignments: int

class DashboardResponse(BaseModel):
    teacher: TeacherProfile
    statistics: DashboardStats
    recent_classrooms: List[ClassroomInfo]

@router.get("/dashboard", response_model=DashboardResponse)
async def get_teacher_dashboard(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard data"""
    
    # Get classrooms with students
    classrooms = db.query(Classroom).filter(
        Classroom.teacher_id == current_teacher.id,
        Classroom.is_active == True
    ).options(joinedload(Classroom.students).joinedload(ClassroomStudent.student)).all()
    
    # Calculate statistics
    total_students = 0
    recent_classrooms = []
    
    for classroom in classrooms[:5]:  # Get up to 5 recent classrooms
        students = [
            StudentInfo(
                id=cs.student.id,
                name=cs.student.name,
                email=cs.student.email,
                student_id=cs.student.student_id
            )
            for cs in classroom.students if cs.is_active
        ]
        total_students += len(students)
        
        recent_classrooms.append(ClassroomInfo(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            level=classroom.level.value if classroom.level else "A1",
            students=students,
            student_count=len(students)
        ))
    
    # Count programs
    total_programs = db.query(Program).filter(
        Program.teacher_id == current_teacher.id,
        Program.is_active == True
    ).count()
    
    # Count active assignments
    active_assignments = db.query(StudentAssignment).join(
        Classroom, StudentAssignment.classroom_id == Classroom.id
    ).filter(
        Classroom.teacher_id == current_teacher.id,
        StudentAssignment.status.in_(["not_started", "in_progress", "submitted"])
    ).count()
    
    return DashboardResponse(
        teacher=TeacherProfile(
            id=current_teacher.id,
            email=current_teacher.email,
            name=current_teacher.name,
            phone=current_teacher.phone,
            is_demo=current_teacher.is_demo,
            is_active=current_teacher.is_active
        ),
        statistics=DashboardStats(
            total_classrooms=len(classrooms),
            total_students=total_students,
            total_programs=total_programs,
            active_assignments=active_assignments
        ),
        recent_classrooms=recent_classrooms
    )

@router.get("/classrooms", response_model=List[ClassroomInfo])
async def get_teacher_classrooms(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all classrooms for the teacher"""
    
    classrooms = db.query(Classroom).filter(
        Classroom.teacher_id == current_teacher.id,
        Classroom.is_active == True
    ).options(joinedload(Classroom.students).joinedload(ClassroomStudent.student)).all()
    
    result = []
    for classroom in classrooms:
        students = [
            StudentInfo(
                id=cs.student.id,
                name=cs.student.name,
                email=cs.student.email,
                student_id=cs.student.student_id
            )
            for cs in classroom.students if cs.is_active
        ]
        
        result.append(ClassroomInfo(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            level=classroom.level.value if classroom.level else "A1",
            students=students,
            student_count=len(students)
        ))
    
    return result

@router.get("/programs", response_model=List[ProgramInfo])
async def get_teacher_programs(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all programs for the teacher"""
    
    programs = db.query(Program).filter(
        Program.teacher_id == current_teacher.id,
        Program.is_active == True
    ).options(
        joinedload(Program.classroom),
        joinedload(Program.lessons)
    ).all()
    
    result = []
    for program in programs:
        result.append(ProgramInfo(
            id=program.id,
            name=program.name,
            description=program.description,
            level=program.level.value if program.level else "A1",
            classroom_id=program.classroom_id,
            classroom_name=program.classroom.name if program.classroom else "Unknown",
            estimated_hours=program.estimated_hours,
            lesson_count=len(program.lessons)
        ))
    
    return result

@router.get("/me", response_model=TeacherProfile)
async def get_teacher_profile(
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """Get current teacher profile"""
    return TeacherProfile(
        id=current_teacher.id,
        email=current_teacher.email,
        name=current_teacher.name,
        phone=current_teacher.phone,
        is_demo=current_teacher.is_demo,
        is_active=current_teacher.is_active
    )