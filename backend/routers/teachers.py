from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel
from database import get_db
from models import Teacher, Classroom, Student, Program, ClassroomStudent
from auth import verify_token
from typing import List, Optional

router = APIRouter(prefix="/api/teachers", tags=["teachers"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")

# ============ Dependency to get current teacher ============
async def get_current_teacher(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """取得當前登入的教師"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    teacher_id = payload.get("sub")
    teacher_type = payload.get("type")
    
    if teacher_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a teacher"
        )
    
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return teacher

# ============ Response Models ============
class TeacherProfile(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str]
    is_demo: bool
    is_active: bool
    
    class Config:
        from_attributes = True

class ClassroomSummary(BaseModel):
    id: int
    name: str
    description: Optional[str]
    student_count: int
    
class StudentSummary(BaseModel):
    id: int
    name: str
    email: str
    classroom_name: str

class TeacherDashboard(BaseModel):
    teacher: TeacherProfile
    classroom_count: int
    student_count: int
    program_count: int
    classrooms: List[ClassroomSummary]
    recent_students: List[StudentSummary]

# ============ Teacher Endpoints ============
@router.get("/me", response_model=TeacherProfile)
async def get_teacher_profile(current_teacher: Teacher = Depends(get_current_teacher)):
    """取得教師個人資料"""
    return current_teacher

@router.get("/dashboard", response_model=TeacherDashboard)
async def get_teacher_dashboard(current_teacher: Teacher = Depends(get_current_teacher), db: Session = Depends(get_db)):
    """取得教師儀表板資料"""
    
    # Get classrooms with student count
    classrooms = db.query(Classroom).filter(
        Classroom.teacher_id == current_teacher.id
    ).options(selectinload(Classroom.students).selectinload(ClassroomStudent.student)).all()
    
    classroom_summaries = []
    total_students = 0
    recent_students = []
    
    for classroom in classrooms:
        student_count = len(classroom.students)
        total_students += student_count
        
        classroom_summaries.append(ClassroomSummary(
            id=classroom.id,
            name=classroom.name,
            description=classroom.description,
            student_count=student_count
        ))
        
        # Add recent students (first 3 from each classroom)
        for classroom_student in classroom.students[:3]:
            if len(recent_students) < 10:  # Limit to 10 recent students
                recent_students.append(StudentSummary(
                    id=classroom_student.student.id,
                    name=classroom_student.student.name,
                    email=classroom_student.student.email,
                    classroom_name=classroom.name
                ))
    
    # Get program count (programs created by this teacher)
    program_count = db.query(Program).filter(Program.teacher_id == current_teacher.id).count()
    
    return TeacherDashboard(
        teacher=TeacherProfile.from_orm(current_teacher),
        classroom_count=len(classrooms),
        student_count=total_students,
        program_count=program_count,
        classrooms=classroom_summaries,
        recent_students=recent_students
    )

@router.get("/classrooms")
async def get_teacher_classrooms(current_teacher: Teacher = Depends(get_current_teacher), db: Session = Depends(get_db)):
    """取得教師的所有班級"""
    classrooms = db.query(Classroom).filter(
        Classroom.teacher_id == current_teacher.id
    ).options(selectinload(Classroom.students).selectinload(ClassroomStudent.student)).all()
    
    return [
        {
            "id": classroom.id,
            "name": classroom.name,
            "description": classroom.description,
            "student_count": len(classroom.students),
            "students": [
                {
                    "id": cs.student.id,
                    "name": cs.student.name,
                    "email": cs.student.email
                } for cs in classroom.students
            ]
        } for classroom in classrooms
    ]

@router.get("/programs")
async def get_teacher_programs(current_teacher: Teacher = Depends(get_current_teacher), db: Session = Depends(get_db)):
    """取得教師的所有課程"""
    programs = db.query(Program).filter(
        Program.teacher_id == current_teacher.id
    ).options(selectinload(Program.classroom)).all()
    
    return [
        {
            "id": program.id,
            "name": program.name,
            "description": program.description,
            "level": program.level.value if program.level else None,
            "classroom_id": program.classroom_id,
            "classroom_name": program.classroom.name,
            "estimated_hours": program.estimated_hours,
            "is_active": program.is_active,
            "created_at": program.created_at.isoformat() if program.created_at else None
        } for program in programs
    ]