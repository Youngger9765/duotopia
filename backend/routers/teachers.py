from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
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
    program_count = db.query(Program).filter(
        Program.teacher_id == current_teacher.id,
        Program.is_active == True
    ).count()
    
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
    
    # Get classrooms with students (only active classrooms)
    classrooms = db.query(Classroom).filter(
        Classroom.teacher_id == current_teacher.id,
        Classroom.is_active == True  # Only show active classrooms
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
        Program.teacher_id == current_teacher.id,
        Program.is_active == True
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
            "lesson_count": len([l for l in program.lessons if l.is_active]),  # Count only active lessons
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
    classroom_id: Optional[int] = None  # 班級改為選填，可以之後再分配
    student_id: Optional[str] = None
    phone: Optional[str] = None  # 新增 phone 欄位

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    student_id: Optional[str] = None
    birthdate: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    target_wpm: Optional[int] = None
    target_accuracy: Optional[float] = None
    classroom_id: Optional[int] = None  # 新增班級分配功能

class BatchStudentCreate(BaseModel):
    students: List[Dict[str, Any]]

@router.get("/students")
async def get_all_students(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取得教師的所有學生（包含未分配班級的）"""
    # Get all students created by this teacher or in their classrooms
    # First, get students in teacher's classrooms
    students_in_classrooms = db.query(Student).join(
        ClassroomStudent, Student.id == ClassroomStudent.student_id
    ).join(
        Classroom, ClassroomStudent.classroom_id == Classroom.id
    ).filter(
        Classroom.teacher_id == current_teacher.id,
        Student.is_active == True  # Only show active students
    ).all()
    
    # Also get students without classroom (created by this teacher)
    # We need to track which teacher created a student - for now, get all unassigned
    students_without_classroom = db.query(Student).outerjoin(
        ClassroomStudent, Student.id == ClassroomStudent.student_id
    ).filter(
        ClassroomStudent.id == None,
        Student.is_active == True  # Only show active students
    ).all()
    
    # Combine and deduplicate
    all_students = list({s.id: s for s in students_in_classrooms + students_without_classroom}.values())
    
    # Build response with classroom info
    result = []
    for student in all_students:
        # Get classroom info if exists
        classroom_student = db.query(ClassroomStudent).filter(
            ClassroomStudent.student_id == student.id,
            ClassroomStudent.is_active == True
        ).join(
            Classroom
        ).filter(
            Classroom.teacher_id == current_teacher.id
        ).first()
        
        classroom_info = None
        if classroom_student:
            classroom = db.query(Classroom).filter(
                Classroom.id == classroom_student.classroom_id
            ).first()
            if classroom:
                classroom_info = {
                    "id": classroom.id,
                    "name": classroom.name
                }
        
        result.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "student_id": student.student_id,
            "birthdate": student.birthdate.isoformat() if student.birthdate else None,
            "phone": getattr(student, 'phone', ''),
            "password_changed": student.password_changed,
            "last_login": student.last_login.isoformat() if student.last_login else None,
            "status": "active" if student.is_active else "inactive",
            "classroom_id": classroom_info["id"] if classroom_info else None,
            "classroom_name": classroom_info["name"] if classroom_info else "未分配"
        })
    
    return result

@router.post("/students")
async def create_student(
    student_data: StudentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """創建新學生"""
    # Verify classroom belongs to teacher (only if classroom_id is provided)
    if student_data.classroom_id:
        classroom = db.query(Classroom).filter(
            Classroom.id == student_data.classroom_id,
            Classroom.teacher_id == current_teacher.id
        ).first()
        
        if not classroom:
            raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Parse birthdate with error handling
    try:
        # Try to parse the birthdate
        birthdate = date.fromisoformat(student_data.birthdate)
    except ValueError:
        # If format is wrong, try to handle common formats
        try:
            # Try format with slashes
            from datetime import datetime
            birthdate = datetime.strptime(student_data.birthdate, "%Y/%m/%d").date()
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid birthdate format. Please use YYYY-MM-DD format"
            )
    
    default_password = birthdate.strftime("%Y%m%d")
    
    # Generate unique email if not provided
    if not student_data.email:
        # Generate a unique email based on student_id or timestamp
        import time
        timestamp = int(time.time())
        email = f"student_{timestamp}@duotopia.local"
    else:
        email = student_data.email
    
    # Check if email already exists
    existing_student = db.query(Student).filter(Student.email == email).first()
    if existing_student:
        raise HTTPException(
            status_code=422,
            detail=f"Email '{email}' is already registered. Please use a different email."
        )
    
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
    
    try:
        db.add(student)
        db.commit()
        db.refresh(student)
    except Exception as e:
        db.rollback()
        # Check if it's a unique constraint violation
        if "duplicate key" in str(e):
            raise HTTPException(
                status_code=422,
                detail="Email or student ID already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))
    
    # Add student to classroom (only if classroom_id is provided)
    if student_data.classroom_id:
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
        "classroom_id": student_data.classroom_id,
        "student_id": student.student_id,
        "phone": student_data.phone
    }

@router.get("/students/{student_id}")
async def get_student(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取得單一學生資料"""
    # First check if student exists and is active
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if student belongs to teacher's classroom (if assigned to any)
    classroom_student = db.query(ClassroomStudent).filter(
        ClassroomStudent.student_id == student_id
    ).first()
    
    if classroom_student:
        # If student is in a classroom, verify it belongs to this teacher
        classroom = db.query(Classroom).filter(
            Classroom.id == classroom_student.classroom_id,
            Classroom.teacher_id == current_teacher.id
        ).first()
        
        if not classroom:
            raise HTTPException(status_code=403, detail="You don't have permission to access this student")
    
    # If student has no classroom, we assume the teacher can access them
    
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
    # First check if student exists and is active
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if student belongs to teacher's classroom (if assigned to any)
    classroom_student = db.query(ClassroomStudent).filter(
        ClassroomStudent.student_id == student_id
    ).first()
    
    if classroom_student:
        # If student is in a classroom, verify it belongs to this teacher
        classroom = db.query(Classroom).filter(
            Classroom.id == classroom_student.classroom_id,
            Classroom.teacher_id == current_teacher.id
        ).first()
        
        if not classroom:
            raise HTTPException(status_code=403, detail="You don't have permission to update this student")
    
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
    
    # Handle classroom assignment
    if update_data.classroom_id is not None:
        # First, remove student from current classroom (if any)
        existing_enrollment = db.query(ClassroomStudent).filter(
            ClassroomStudent.student_id == student_id,
            ClassroomStudent.is_active == True
        ).first()
        
        if existing_enrollment:
            existing_enrollment.is_active = False
        
        # If classroom_id is provided (not 0 or empty), assign to new classroom
        if update_data.classroom_id > 0:
            # Verify classroom belongs to teacher
            classroom = db.query(Classroom).filter(
                Classroom.id == update_data.classroom_id,
                Classroom.teacher_id == current_teacher.id,
                Classroom.is_active == True
            ).first()
            
            if not classroom:
                raise HTTPException(status_code=404, detail="Classroom not found")
            
            # Create new enrollment
            new_enrollment = ClassroomStudent(
                classroom_id=update_data.classroom_id,
                student_id=student_id,
                is_active=True
            )
            db.add(new_enrollment)
    
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
    # First check if student exists and is active
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if student belongs to teacher's classroom (if assigned to any)
    classroom_student = db.query(ClassroomStudent).filter(
        ClassroomStudent.student_id == student_id
    ).first()
    
    if classroom_student:
        # If student is in a classroom, verify it belongs to this teacher
        classroom = db.query(Classroom).filter(
            Classroom.id == classroom_student.classroom_id,
            Classroom.teacher_id == current_teacher.id
        ).first()
        
        if not classroom:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this student")
    
    # If student has no classroom, we assume the teacher can delete them
    # (since they likely created them)
    
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
                        "type": content.type.value if content.type else "reading_assessment",
                        "title": content.title,
                        "items": content.items or [],  # Include actual items
                        "items_count": len(content.items) if content.items else 0,
                        "estimated_time": "10 分鐘"  # Can be calculated based on items
                    } for content in sorted(lesson.contents or [], key=lambda x: x.order_index) 
                    if content.is_active  # Filter by is_active
                ]
            } for lesson in sorted(program.lessons or [], key=lambda x: x.order_index) 
            if lesson.is_active  # Filter by is_active
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
    """刪除課程 - 使用軟刪除保護資料完整性"""
    from models import StudentAssignment, Content, Lesson
    
    program = db.query(Program).filter(
        Program.id == program_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # 檢查相關資料
    lesson_count = db.query(Lesson).filter(Lesson.program_id == program_id).count()
    content_count = db.query(Content).join(Lesson).filter(Lesson.program_id == program_id).count()
    assignment_count = db.query(StudentAssignment).join(Content).join(Lesson).filter(
        Lesson.program_id == program_id
    ).count()
    
    # 軟刪除 - 保留資料以供日後參考
    program.is_active = False
    db.commit()
    
    return {
        "message": "Program successfully deactivated (soft delete)",
        "details": {
            "program_id": program_id,
            "program_name": program.name,
            "deactivated": True,
            "related_data": {
                "lessons": lesson_count,
                "contents": content_count,
                "assignments": assignment_count
            },
            "note": "課程已停用但資料保留，可聯繫管理員恢復"
        }
    }

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

@router.put("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新課程單元"""
    # 驗證 lesson 屬於當前教師
    lesson = db.query(Lesson).join(Program).filter(
        Lesson.id == lesson_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # 更新資料
    lesson.name = lesson_data.name
    lesson.description = lesson_data.description
    lesson.order_index = lesson_data.order_index
    lesson.estimated_minutes = lesson_data.estimated_minutes
    
    db.commit()
    db.refresh(lesson)
    
    return {
        "id": lesson.id,
        "name": lesson.name,
        "description": lesson.description,
        "order_index": lesson.order_index,
        "estimated_minutes": lesson.estimated_minutes
    }

@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """刪除課程單元 - 使用軟刪除保護資料完整性"""
    from models import StudentAssignment, Content
    
    # 驗證 lesson 屬於當前教師
    lesson = db.query(Lesson).join(Program).filter(
        Lesson.id == lesson_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # 檢查相關資料
    content_count = db.query(Content).filter(
        Content.lesson_id == lesson_id,
        Content.is_active == True
    ).count()
    
    assignment_count = db.query(StudentAssignment).join(Content).filter(
        Content.lesson_id == lesson_id
    ).count()
    
    # 軟刪除 lesson
    lesson.is_active = False
    
    # 同時軟刪除相關的 contents
    db.query(Content).filter(
        Content.lesson_id == lesson_id
    ).update({"is_active": False})
    
    db.commit()
    
    return {
        "message": "Lesson successfully deactivated (soft delete)",
        "details": {
            "lesson_id": lesson_id,
            "lesson_name": lesson.name,
            "deactivated": True,
            "related_data": {
                "contents": content_count,
                "assignments": assignment_count
            },
            "note": "單元已停用但資料保留，可聯繫管理員恢復"
        }
    }

# ------------ Content CRUD ------------

class ContentCreate(BaseModel):
    type: str = "reading_assessment"
    title: str
    items: List[Dict[str, Any]]  # [{"text": "...", "translation": "..."}, ...]
    target_wpm: Optional[int] = 60
    target_accuracy: Optional[float] = 0.8
    order_index: int = 0
    level: Optional[str] = "A1"
    tags: Optional[List[str]] = []
    is_public: Optional[bool] = False

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    target_wpm: Optional[int] = None
    target_accuracy: Optional[float] = None
    time_limit_seconds: Optional[int] = None
    order_index: Optional[int] = None
    level: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

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
        Content.lesson_id == lesson_id,
        Content.is_active == True
    ).order_by(Content.order_index).all()
    
    return [
        {
            "id": content.id,
            "type": content.type.value if content.type else "reading_assessment",
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
        type=ContentType.READING_ASSESSMENT,  # Phase 1 only has this type
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
        "order_index": content.order_index,
        "level": content.level if hasattr(content, 'level') else "A1",
        "tags": content.tags if hasattr(content, 'tags') else []
    }

@router.get("/contents/{content_id}")
async def get_content_detail(
    content_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """獲取內容詳情"""
    # Verify the content belongs to the teacher
    content = db.query(Content).join(Lesson).join(Program).filter(
        Content.id == content_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return {
        "id": content.id,
        "type": content.type.value if content.type else "reading_assessment",
        "title": content.title,
        "items": content.items or [],
        "target_wpm": content.target_wpm,
        "target_accuracy": content.target_accuracy,
        "time_limit_seconds": content.time_limit_seconds,
        "level": "A1",  # 可以從 lesson 或 program 獲取
        "tags": ["public"],  # 可以從其他地方獲取
        "order_index": content.order_index,
        "level": content.level if hasattr(content, 'level') else "A1",
        "tags": content.tags if hasattr(content, 'tags') else []
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
    
    # 引入音檔管理器
    from services.audio_manager import get_audio_manager
    audio_manager = get_audio_manager()
    
    if update_data.title is not None:
        content.title = update_data.title
    if update_data.items is not None:
        # 處理音檔更新（刪除舊的）
        if content.items and update_data.items:
            old_items = content.items if isinstance(content.items, list) else []
            new_items = update_data.items
            
            # 建立新音檔 URL 的集合
            new_audio_urls = set()
            for item in new_items:
                if isinstance(item, dict) and 'audio_url' in item and item['audio_url']:
                    new_audio_urls.add(item['audio_url'])
            
            # 刪除不再使用的舊音檔
            for old_item in old_items:
                if isinstance(old_item, dict) and 'audio_url' in old_item:
                    old_url = old_item['audio_url']
                    if old_url and old_url not in new_audio_urls:
                        audio_manager.delete_old_audio(old_url)
        
        content.items = update_data.items
    if update_data.target_wpm is not None:
        content.target_wpm = update_data.target_wpm
    if update_data.target_accuracy is not None:
        content.target_accuracy = update_data.target_accuracy
    if update_data.time_limit_seconds is not None:
        content.time_limit_seconds = update_data.time_limit_seconds
    if update_data.order_index is not None:
        content.order_index = update_data.order_index
    if update_data.level is not None:
        content.level = update_data.level
    if update_data.tags is not None:
        content.tags = update_data.tags
    
    db.commit()
    db.refresh(content)
    
    return {
        "id": content.id,
        "type": content.type.value,
        "title": content.title,
        "items": content.items,
        "target_wpm": content.target_wpm,
        "target_accuracy": content.target_accuracy,
        "order_index": content.order_index,
        "level": content.level if hasattr(content, 'level') else "A1",
        "tags": content.tags if hasattr(content, 'tags') else []
    }

@router.delete("/contents/{content_id}")
async def delete_content(
    content_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """刪除內容（軟刪除）"""
    # Verify the content belongs to the teacher
    content = db.query(Content).join(Lesson).join(Program).filter(
        Content.id == content_id,
        Program.teacher_id == current_teacher.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # 檢查是否有相關的作業
    from models import StudentAssignment
    assignment_count = db.query(StudentAssignment).filter(
        StudentAssignment.content_id == content_id
    ).count()
    
    # 軟刪除
    content.is_active = False
    db.commit()
    
    return {
        "message": "Content deactivated successfully",
        "details": {
            "content_title": content.title,
            "deactivated": True,
            "related_data": {
                "assignments": assignment_count
            },
            "reason": "soft_delete",
            "note": "內容已停用但資料保留，相關作業仍可查看"
        }
    }

# ------------ Translation API ------------
from services.translation import translation_service

class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "zh-TW"

class BatchTranslateRequest(BaseModel):
    texts: List[str]
    target_lang: str = "zh-TW"

@router.post("/translate")
async def translate_text(
    request: TranslateRequest,
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """翻譯單一文本"""
    try:
        translation = await translation_service.translate_text(
            request.text, 
            request.target_lang
        )
        return {
            "original": request.text,
            "translation": translation
        }
    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")

@router.post("/translate/batch")
async def batch_translate(
    request: BatchTranslateRequest,
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """批次翻譯多個文本"""
    try:
        translations = await translation_service.batch_translate(
            request.texts,
            request.target_lang
        )
        return {
            "originals": request.texts,
            "translations": translations
        }
    except Exception as e:
        print(f"Batch translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")

# ============ TTS Endpoints ============
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-JennyNeural"
    rate: Optional[str] = "+0%"
    volume: Optional[str] = "+0%"

class BatchTTSRequest(BaseModel):
    texts: List[str]
    voice: Optional[str] = "en-US-JennyNeural"
    rate: Optional[str] = "+0%"
    volume: Optional[str] = "+0%"

@router.post("/tts")
async def generate_tts(
    request: TTSRequest,
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """生成單一 TTS 音檔"""
    try:
        from services.tts import get_tts_service
        
        tts_service = get_tts_service()
        
        # 直接使用 await，因為 FastAPI 已經在異步環境中
        audio_url = await tts_service.generate_tts(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            volume=request.volume
        )
        
        return {"audio_url": audio_url}
    except Exception as e:
        print(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")

@router.post("/tts/batch")
async def batch_generate_tts(
    request: BatchTTSRequest,
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """批次生成 TTS 音檔"""
    try:
        from services.tts import get_tts_service
        
        tts_service = get_tts_service()
        
        # 直接使用 await，因為 FastAPI 已經在異步環境中
        audio_urls = await tts_service.batch_generate_tts(
            texts=request.texts,
            voice=request.voice,
            rate=request.rate,
            volume=request.volume
        )
        
        return {"audio_urls": audio_urls}
    except Exception as e:
        print(f"Batch TTS error: {e}")
        raise HTTPException(status_code=500, detail="Batch TTS generation failed")

@router.get("/tts/voices")
async def get_tts_voices(
    language: str = "en",
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """取得可用的 TTS 語音列表"""
    try:
        from services.tts import get_tts_service
        
        tts_service = get_tts_service()
        
        # 直接使用 await，因為 FastAPI 已經在異步環境中
        voices = await tts_service.get_available_voices(language)
        
        return {"voices": voices}
    except Exception as e:
        print(f"Get voices error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get voices")

# ============ Audio Upload Endpoints ============
@router.post("/upload/audio")
async def upload_audio(
    file: UploadFile = File(...),
    duration: int = Form(30),
    content_id: Optional[int] = Form(None),
    item_index: Optional[int] = Form(None),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """上傳錄音檔案
    
    Args:
        file: 音檔檔案
        duration: 錄音長度（秒）
        content_id: 內容 ID（用於識別要替換的音檔）
        item_index: 項目索引（用於識別是哪個項目的音檔）
    """
    try:
        from services.audio_upload import get_audio_upload_service
        from services.audio_manager import get_audio_manager
        
        audio_service = get_audio_upload_service()
        audio_manager = get_audio_manager()
        
        # 如果提供了 content_id 和 item_index，先刪除舊音檔
        if content_id and item_index is not None:
            content = db.query(Content).filter(
                Content.id == content_id,
                Content.lesson.has(Lesson.program.has(Program.teacher_id == current_teacher.id))
            ).first()
            
            if content and content.items and item_index < len(content.items):
                old_audio_url = content.items[item_index].get("audio_url")
                if old_audio_url:
                    # 刪除舊音檔
                    audio_manager.delete_old_audio(old_audio_url)
        
        # 上傳新音檔（包含 content_id 和 item_index 在檔名中）
        audio_url = await audio_service.upload_audio(
            file, 
            duration,
            content_id=content_id,
            item_index=item_index
        )
        
        return {"audio_url": audio_url}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Audio upload error: {e}")
        raise HTTPException(status_code=500, detail="Audio upload failed")