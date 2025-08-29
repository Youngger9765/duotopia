from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from pydantic import BaseModel
from database import get_db
from models import Teacher, Classroom, Student, Program, ClassroomStudent, Lesson, Content, ContentType, ProgramLevel
from auth import verify_token, get_password_hash
from typing import List, Optional, Dict, Any
from datetime import date

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
    from sqlalchemy import func
    
    # Get classrooms with students
    classrooms = db.query(Classroom).filter(
        Classroom.teacher_id == current_teacher.id
    ).options(
        selectinload(Classroom.students).selectinload(ClassroomStudent.student)
    ).all()
    
    # Get program counts in a single query for all classrooms
    program_counts = db.query(
        Program.classroom_id,
        func.count(Program.id).label("count")
    ).filter(
        Program.classroom_id.in_([c.id for c in classrooms]),
        Program.is_active == True
    ).group_by(Program.classroom_id).all()
    
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
            "created_at": classroom.created_at.isoformat() if classroom.created_at else None,
            "students": [
                {
                    "id": cs.student.id,
                    "name": cs.student.name,
                    "email": cs.student.email,
                    "student_id": cs.student.student_id,
                    "birthdate": cs.student.birthdate.isoformat() if cs.student.birthdate else None,
                    "password_changed": cs.student.password_changed,
                    "last_login": cs.student.last_login.isoformat() if cs.student.last_login else None,
                    "phone": "",  # Privacy: don't expose phone numbers in list
                    "status": "active" if cs.student.is_active else "inactive"
                } for cs in classroom.students if cs.is_active
            ]
        } for classroom in classrooms
    ]

@router.get("/programs")
async def get_teacher_programs(current_teacher: Teacher = Depends(get_current_teacher), db: Session = Depends(get_db)):
    """取得教師的所有課程"""
    programs = db.query(Program).filter(
        Program.teacher_id == current_teacher.id
    ).options(selectinload(Program.classroom), selectinload(Program.lessons)).order_by(Program.order_index).all()
    
    result = []
    for program in programs:
        # Get student count for the classroom through ClassroomStudent relationship
        student_count = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == program.classroom_id
        ).count()
        
        result.append({
            "id": program.id,
            "name": program.name,
            "description": program.description,
            "level": program.level.value if program.level else None,
            "classroom_id": program.classroom_id,
            "classroom_name": program.classroom.name,
            "estimated_hours": program.estimated_hours,
            "is_active": program.is_active,
            "created_at": program.created_at.isoformat() if program.created_at else None,
            "lesson_count": len(program.lessons),  # Real lesson count
            "student_count": student_count,  # Real student count
            "status": "active" if program.is_active else "archived",  # Real status based on is_active
            "order_index": program.order_index if hasattr(program, 'order_index') else 1
        })
    
    return result

# ============ CRUD Endpoints ============

# ------------ Classroom CRUD ------------
class ClassroomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    level: str = "A1"

class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None

@router.post("/classrooms")
async def create_classroom(
    classroom_data: ClassroomCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """創建新班級"""
    classroom = Classroom(
        name=classroom_data.name,
        description=classroom_data.description,
        level=getattr(ProgramLevel, classroom_data.level.upper().replace("-", "_"), ProgramLevel.A1),
        teacher_id=current_teacher.id,
        is_active=True
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "description": classroom.description,
        "level": classroom.level.value,
        "teacher_id": classroom.teacher_id
    }

@router.get("/classrooms/{classroom_id}")
async def get_classroom(
    classroom_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取得單一班級資料"""
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "description": classroom.description,
        "level": classroom.level.value if classroom.level else "A1",
        "teacher_id": classroom.teacher_id
    }

@router.put("/classrooms/{classroom_id}")
async def update_classroom(
    classroom_id: int,
    update_data: ClassroomUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新班級資料"""
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    if update_data.name is not None:
        classroom.name = update_data.name
    if update_data.description is not None:
        classroom.description = update_data.description
    if update_data.level is not None:
        classroom.level = getattr(ProgramLevel, update_data.level.upper().replace("-", "_"), ProgramLevel.A1)
    
    db.commit()
    db.refresh(classroom)
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "description": classroom.description,
        "level": classroom.level.value
    }

@router.delete("/classrooms/{classroom_id}")
async def delete_classroom(
    classroom_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """刪除班級"""
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Soft delete by setting is_active = False
    classroom.is_active = False
    db.commit()
    
    return {"message": "Classroom deleted successfully"}

# ------------ Student CRUD ------------
class StudentCreate(BaseModel):
    name: str
    email: Optional[str] = None  # Email 改為選填
    birthdate: str  # YYYY-MM-DD format
    classroom_id: int
    student_id: Optional[str] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    student_id: Optional[str] = None
    birthdate: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    target_wpm: Optional[int] = None
    target_accuracy: Optional[float] = None

class BatchStudentCreate(BaseModel):
    students: List[Dict[str, Any]]

@router.post("/students")
async def create_student(
    student_data: StudentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """創建新學生"""
    # Verify classroom belongs to teacher
    classroom = db.query(Classroom).filter(
        Classroom.id == student_data.classroom_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Parse birthdate
    birthdate = date.fromisoformat(student_data.birthdate)
    default_password = birthdate.strftime("%Y%m%d")
    
    # Generate unique email if not provided
    if not student_data.email:
        # Generate a unique email based on student_id or timestamp
        import time
        timestamp = int(time.time())
        email = f"student_{timestamp}@duotopia.local"
    else:
        email = student_data.email
    
    # Create student
    student = Student(
        name=student_data.name,
        email=email,
        birthdate=birthdate,
        password_hash=get_password_hash(default_password),
        password_changed=False,
        student_id=student_data.student_id,
        target_wpm=80,
        target_accuracy=0.8,
        is_active=True
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    
    # Add student to classroom
    enrollment = ClassroomStudent(
        classroom_id=student_data.classroom_id,
        student_id=student.id,
        is_active=True
    )
    db.add(enrollment)
    db.commit()
    
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "birthdate": student.birthdate.isoformat(),
        "default_password": default_password,
        "password_changed": False,
        "classroom_id": student_data.classroom_id
    }

@router.get("/students/{student_id}")
async def get_student(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取得單一學生資料"""
    # Get student with classroom verification
    student = db.query(Student).join(
        ClassroomStudent, Student.id == ClassroomStudent.student_id
    ).join(
        Classroom, ClassroomStudent.classroom_id == Classroom.id
    ).filter(
        Student.id == student_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "birthdate": student.birthdate.isoformat(),
        "password_changed": student.password_changed,
        "student_id": student.student_id
    }

@router.put("/students/{student_id}")
async def update_student(
    student_id: int,
    update_data: StudentUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新學生資料"""
    # Get student with classroom verification
    student = db.query(Student).join(
        ClassroomStudent, Student.id == ClassroomStudent.student_id
    ).join(
        Classroom, ClassroomStudent.classroom_id == Classroom.id
    ).filter(
        Student.id == student_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if birthdate is being changed and student is using default password
    if update_data.birthdate is not None and not student.password_changed:
        from datetime import datetime
        from auth import get_password_hash
        
        # Parse new birthdate
        new_birthdate = datetime.strptime(update_data.birthdate, "%Y-%m-%d").date()
        student.birthdate = new_birthdate
        
        # Update password to new birthdate (YYYYMMDD format)
        new_default_password = new_birthdate.strftime("%Y%m%d")
        student.password_hash = get_password_hash(new_default_password)
    
    # Update other fields
    if update_data.name is not None:
        student.name = update_data.name
    if update_data.email is not None:
        student.email = update_data.email
    if update_data.student_id is not None:
        student.student_id = update_data.student_id
    if update_data.phone is not None:
        student.phone = update_data.phone
    if update_data.status is not None:
        student.status = update_data.status
    if update_data.target_wpm is not None:
        student.target_wpm = update_data.target_wpm
    if update_data.target_accuracy is not None:
        student.target_accuracy = update_data.target_accuracy
    
    db.commit()
    db.refresh(student)
    
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "student_id": student.student_id
    }

@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """刪除學生"""
    # Get student with classroom verification
    student = db.query(Student).join(
        ClassroomStudent, Student.id == ClassroomStudent.student_id
    ).join(
        Classroom, ClassroomStudent.classroom_id == Classroom.id
    ).filter(
        Student.id == student_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Soft delete
    student.is_active = False
    db.commit()
    
    return {"message": "Student deleted successfully"}

@router.post("/students/{student_id}/reset-password")
async def reset_student_password(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """重設學生密碼為預設值（生日）"""
    # Get student and verify it belongs to teacher's classroom
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.classroom_enrollments.any(
            ClassroomStudent.classroom.has(
                Classroom.teacher_id == current_teacher.id
            )
        )
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.birthdate:
        raise HTTPException(status_code=400, detail="Student birthdate not set")
    
    # Reset password to birthdate (YYYYMMDD format)
    from auth import get_password_hash
    default_password = student.birthdate.strftime("%Y%m%d")
    student.password_hash = get_password_hash(default_password)
    student.password_changed = False
    
    db.commit()
    
    return {
        "message": "Password reset successfully",
        "default_password": default_password
    }

@router.post("/classrooms/{classroom_id}/students/batch")
async def batch_create_students(
    classroom_id: int,
    batch_data: BatchStudentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """批次創建學生"""
    # Verify classroom belongs to teacher
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    created_students = []
    for student_data in batch_data.students:
        birthdate = date.fromisoformat(student_data["birthdate"])
        default_password = birthdate.strftime("%Y%m%d")
        
        student = Student(
            name=student_data["name"],
            email=student_data["email"],
            birthdate=birthdate,
            password_hash=get_password_hash(default_password),
            password_changed=False,
            student_id=student_data.get("student_id"),
            target_wpm=80,
            target_accuracy=0.8,
            is_active=True
        )
        db.add(student)
        db.flush()  # Get the ID
        
        # Add to classroom
        enrollment = ClassroomStudent(
            classroom_id=classroom_id,
            student_id=student.id,
            is_active=True
        )
        db.add(enrollment)
        created_students.append(student)
    
    db.commit()
    
    return {
        "created_count": len(created_students),
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "default_password": s.birthdate.strftime("%Y%m%d")
            } for s in created_students
        ]
    }

# ------------ Program CRUD ------------
class ProgramCreate(BaseModel):
    name: str
    description: Optional[str] = None
    level: str = "A1"
    classroom_id: int
    estimated_hours: Optional[int] = None

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    estimated_hours: Optional[int] = None

class LessonCreate(BaseModel):
    name: str
    description: Optional[str] = None
    order_index: int = 0
    estimated_minutes: Optional[int] = None

@router.post("/programs")
async def create_program(
    program_data: ProgramCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """創建新課程"""
    # Verify classroom belongs to teacher
    classroom = db.query(Classroom).filter(
        Classroom.id == program_data.classroom_id,
        Classroom.teacher_id == current_teacher.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Get the max order_index for programs in this classroom
    max_order = db.query(func.max(Program.order_index)).filter(
        Program.classroom_id == program_data.classroom_id
    ).scalar() or 0
    
    program = Program(
        name=program_data.name,
        description=program_data.description,
        level=getattr(ProgramLevel, program_data.level.upper().replace("-", "_"), ProgramLevel.A1),
        classroom_id=program_data.classroom_id,
        teacher_id=current_teacher.id,
        estimated_hours=program_data.estimated_hours,
        is_active=True,
        order_index=max_order + 1
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    
    return {
        "id": program.id,
        "name": program.name,
        "description": program.description,
        "level": program.level.value,
        "classroom_id": program.classroom_id,
        "estimated_hours": program.estimated_hours,
        "order_index": program.order_index
    }

@router.put("/programs/reorder")
async def reorder_programs(
    order_data: List[Dict[str, int]],  # [{"id": 1, "order_index": 1}, ...]
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """重新排序課程"""
    for item in order_data:
        program = db.query(Program).filter(
            Program.id == item["id"],
            Program.teacher_id == current_teacher.id
        ).first()
        if program:
            program.order_index = item["order_index"]
    
    db.commit()
    return {"message": "Programs reordered successfully"}

@router.put("/programs/{program_id}/lessons/reorder")
async def reorder_lessons(
    program_id: int,
    order_data: List[Dict[str, int]],  # [{"id": 1, "order_index": 1}, ...]
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """重新排序單元"""
    # 驗證 program 屬於當前教師
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    for item in order_data:
        lesson = db.query(Lesson).filter(
            Lesson.id == item["id"],
            Lesson.program_id == program_id
        ).first()
        if lesson:
            lesson.order_index = item["order_index"]
    
    db.commit()
    return {"message": "Lessons reordered successfully"}

@router.get("/programs/{program_id}")
async def get_program(
    program_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取得單一課程資料"""
    # Import selectinload for nested loading
    from sqlalchemy.orm import selectinload
    
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.teacher_id == current_teacher.id
    ).options(
        selectinload(Program.lessons).selectinload(Lesson.contents)
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return {
        "id": program.id,
        "name": program.name,
        "description": program.description,
        "level": program.level.value if program.level else "A1",
        "classroom_id": program.classroom_id,
        "estimated_hours": program.estimated_hours,
        "order_index": program.order_index if hasattr(program, 'order_index') else 1,
        "lessons": [
            {
                "id": lesson.id,
                "name": lesson.name,
                "description": lesson.description,
                "order_index": lesson.order_index,
                "estimated_minutes": lesson.estimated_minutes,
                "contents": [
                    {
                        "id": content.id,
                        "type": content.type.value if content.type else "reading_recording",
                        "title": content.title,
                        "items": content.items or [],  # Include actual items
                        "items_count": len(content.items) if content.items else 0,
                        "estimated_time": "10 分鐘"  # Can be calculated based on items
                    } for content in sorted(lesson.contents or [], key=lambda x: x.order_index)
                ]
            } for lesson in sorted(program.lessons or [], key=lambda x: x.order_index)
        ]
    }

@router.put("/programs/{program_id}")
async def update_program(
    program_id: int,
    update_data: ProgramUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新課程資料"""
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    if update_data.name is not None:
        program.name = update_data.name
    if update_data.description is not None:
        program.description = update_data.description
    if update_data.estimated_hours is not None:
        program.estimated_hours = update_data.estimated_hours
    
    db.commit()
    db.refresh(program)
    
    return {
        "id": program.id,
        "name": program.name,
        "description": program.description,
        "estimated_hours": program.estimated_hours
    }


@router.delete("/programs/{program_id}")
async def delete_program(
    program_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """刪除課程"""
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Soft delete
    program.is_active = False
    db.commit()
    
    return {"message": "Program deleted successfully"}

@router.post("/programs/{program_id}/lessons")
async def add_lesson(
    program_id: int,
    lesson_data: LessonCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """新增課程單元"""
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    lesson = Lesson(
        program_id=program_id,
        name=lesson_data.name,
        description=lesson_data.description,
        order_index=lesson_data.order_index,
        estimated_minutes=lesson_data.estimated_minutes
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return {
        "id": lesson.id,
        "name": lesson.name,
        "description": lesson.description,
        "order_index": lesson.order_index,
        "estimated_minutes": lesson.estimated_minutes
    }

# ------------ Content CRUD ------------

class ContentCreate(BaseModel):
    type: str = "reading_recording"
    title: str
    items: List[Dict[str, Any]]  # [{"text": "...", "translation": "..."}, ...]
    target_wpm: Optional[int] = 60
    target_accuracy: Optional[float] = 0.8
    order_index: int = 0

class ContentUpdate(BaseModel):
    title: Optional[str]
    items: Optional[List[Dict[str, Any]]]
    target_wpm: Optional[int]
    target_accuracy: Optional[float]
    time_limit_seconds: Optional[int]
    order_index: Optional[int]

@router.get("/lessons/{lesson_id}/contents")
async def get_lesson_contents(
    lesson_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取得單元的內容列表"""
    # Verify the lesson belongs to the teacher
    lesson = db.query(Lesson).join(Program).filter(
        Lesson.id == lesson_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    contents = db.query(Content).filter(
        Content.lesson_id == lesson_id
    ).order_by(Content.order_index).all()
    
    return [
        {
            "id": content.id,
            "type": content.type.value if content.type else "reading_recording",
            "title": content.title,
            "items": content.items or [],
            "target_wpm": content.target_wpm,
            "target_accuracy": content.target_accuracy,
            "order_index": content.order_index
        } for content in contents
    ]

@router.post("/lessons/{lesson_id}/contents")
async def create_content(
    lesson_id: int,
    content_data: ContentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """建立新內容"""
    # Verify the lesson belongs to the teacher
    lesson = db.query(Lesson).join(Program).filter(
        Lesson.id == lesson_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    content = Content(
        lesson_id=lesson_id,
        type=ContentType.READING_RECORDING,  # Phase 1 only has this type
        title=content_data.title,
        items=content_data.items,
        target_wpm=content_data.target_wpm,
        target_accuracy=content_data.target_accuracy,
        order_index=content_data.order_index
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    
    return {
        "id": content.id,
        "type": content.type.value,
        "title": content.title,
        "items": content.items,
        "target_wpm": content.target_wpm,
        "target_accuracy": content.target_accuracy,
        "order_index": content.order_index
    }

@router.put("/contents/{content_id}")
async def update_content(
    content_id: int,
    update_data: ContentUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新內容"""
    # Verify the content belongs to the teacher
    content = db.query(Content).join(Lesson).join(Program).filter(
        Content.id == content_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if update_data.title is not None:
        content.title = update_data.title
    if update_data.items is not None:
        content.items = update_data.items
    if update_data.target_wpm is not None:
        content.target_wpm = update_data.target_wpm
    if update_data.target_accuracy is not None:
        content.target_accuracy = update_data.target_accuracy
    if update_data.time_limit_seconds is not None:
        content.time_limit_seconds = update_data.time_limit_seconds
    if update_data.order_index is not None:
        content.order_index = update_data.order_index
    
    db.commit()
    db.refresh(content)
    
    return {
        "id": content.id,
        "type": content.type.value,
        "title": content.title,
        "items": content.items,
        "target_wpm": content.target_wpm,
        "target_accuracy": content.target_accuracy,
        "order_index": content.order_index
    }

@router.delete("/contents/{content_id}")
async def delete_content(
    content_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """刪除內容"""
    # Verify the content belongs to the teacher
    content = db.query(Content).join(Lesson).join(Program).filter(
        Content.id == content_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    db.delete(content)
    db.commit()
    
    return {"message": "Content deleted successfully"}