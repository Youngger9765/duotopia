"""
機構體系 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from auth import get_current_active_user
from models import User, UserRole
from models import (
    School, Classroom, Student,
    Course, Lesson, ClassroomStudent,
    StudentAssignment
)
from pydantic import BaseModel, EmailStr


# ===== Schemas =====
class SchoolCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None


class ClassroomCreate(BaseModel):
    name: str
    grade_level: Optional[str] = None
    school_id: str
    room_number: Optional[str] = None
    capacity: int = 30


class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr
    birth_date: str
    school_id: str
    student_id: Optional[str] = None
    parent_phone: Optional[str] = None
    emergency_contact: Optional[str] = None


class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    school_id: str
    difficulty_level: Optional[str] = None
    is_template: bool = False


class LessonCreate(BaseModel):
    lesson_number: int
    title: str
    activity_type: str
    content: dict
    time_limit_minutes: int = 30


class EnrollmentCreate(BaseModel):
    student_ids: List[str]
    classroom_id: str


# ===== Router =====
router = APIRouter(
    prefix="/api/institutional",
    tags=["institutional"]
)


# ===== Dependency =====
async def require_institutional_admin(
    current_user: User = Depends(get_current_active_user)
):
    """確保用戶是機構管理員"""
    if current_user.role != UserRole.ADMIN and not current_user.is_institutional_admin:
        raise HTTPException(status_code=403, detail="需要機構管理員權限")
    
    if current_user.current_role_context == "individual":
        raise HTTPException(status_code=403, detail="請切換到機構管理模式")
    
    return current_user


# ===== 學校管理 =====
@router.post("/schools", response_model=dict)
async def create_school(
    school_data: SchoolCreate,
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """創建新學校"""
    # 檢查學校代碼是否已存在
    existing = db.query(School).filter(
        School.code == school_data.code
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="學校代碼已存在")
    
    school = School(**school_data.dict())
    db.add(school)
    db.commit()
    db.refresh(school)
    
    return {
        "id": school.id,
        "name": school.name,
        "code": school.code,
        "address": school.address,
        "phone": school.phone,
        "created_at": school.created_at
    }


@router.get("/schools", response_model=List[dict])
async def get_schools(
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """獲取所有學校"""
    schools = db.query(School).all()
    
    return [{
        "id": school.id,
        "name": school.name,
        "code": school.code,
        "address": school.address,
        "phone": school.phone,
        "classroom_count": len(school.inst_classrooms),
        "student_count": len(school.inst_students),
        "created_at": school.created_at
    } for school in schools]


# ===== 教室管理 =====
@router.post("/classrooms", response_model=dict)
async def create_classroom(
    classroom_data: ClassroomCreate,
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """創建機構教室"""
    # 驗證學校存在
    school = db.query(School).filter(
        School.id == classroom_data.school_id
    ).first()
    
    if not school:
        raise HTTPException(status_code=404, detail="學校不存在")
    
    classroom = Classroom(**classroom_data.dict())
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "grade_level": classroom.grade_level,
        "school_id": classroom.school_id,
        "school_name": school.name,
        "room_number": classroom.room_number,
        "capacity": classroom.capacity,
        "type": "institutional",
        "created_at": classroom.created_at
    }


@router.get("/classrooms", response_model=List[dict])
async def get_classrooms(
    school_id: Optional[str] = Query(None),
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """獲取機構教室列表"""
    query = db.query(Classroom)
    
    if school_id:
        query = query.filter(Classroom.school_id == school_id)
    
    classrooms = query.all()
    
    result = []
    for classroom in classrooms:
        # 計算學生數
        student_count = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == classroom.id,
            ClassroomStudent.is_active == True
        ).count()
        
        result.append({
            "id": classroom.id,
            "name": classroom.name,
            "grade_level": classroom.grade_level,
            "school_id": classroom.school_id,
            "school_name": classroom.school.name,
            "room_number": classroom.room_number,
            "capacity": classroom.capacity,
            "student_count": student_count,
            "type": "institutional",
            "created_at": classroom.created_at
        })
    
    return result


# ===== 學生管理 =====
@router.post("/students", response_model=dict)
async def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """創建機構學生"""
    # 檢查 email 是否已存在
    existing = db.query(Student).filter(
        Student.email == student_data.email
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email 已存在")
    
    # 如果沒有提供學號，自動生成
    if not student_data.student_id:
        student_data.student_id = f"STU{datetime.now().year}{str(uuid.uuid4())[:8].upper()}"
    
    student = Student(**student_data.dict())
    db.add(student)
    db.commit()
    db.refresh(student)
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "email": student.email,
        "birth_date": student.birth_date,
        "school_id": student.school_id,
        "school_name": student.school.name,
        "student_id": student.student_id,
        "parent_phone": student.parent_phone,
        "type": "institutional"
    }


@router.get("/students", response_model=List[dict])
async def get_students(
    school_id: Optional[str] = Query(None),
    classroom_id: Optional[str] = Query(None),
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """獲取機構學生列表"""
    query = db.query(Student)
    
    if school_id:
        query = query.filter(Student.school_id == school_id)
    
    students = query.all()
    
    result = []
    for student in students:
        # 獲取學生的教室信息
        enrollment = db.query(ClassroomStudent).filter(
            ClassroomStudent.student_id == student.id,
            ClassroomStudent.is_active == True
        ).first()
        
        student_dict = {
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "birth_date": student.birth_date,
            "school_id": student.school_id,
            "school_name": student.school.name,
            "student_id": student.student_id,
            "parent_phone": student.parent_phone,
            "type": "institutional"
        }
        
        if enrollment and enrollment.classroom:
            student_dict["classroom_id"] = enrollment.classroom_id
            student_dict["classroom_name"] = enrollment.classroom.name
            student_dict["status"] = "已分班"
        else:
            student_dict["classroom_id"] = None
            student_dict["classroom_name"] = "未分班"
            student_dict["status"] = "待分班"
        
        # 如果指定了教室篩選
        if classroom_id:
            if not enrollment or enrollment.classroom_id != classroom_id:
                continue
        
        result.append(student_dict)
    
    return result


# ===== 註冊管理 =====
@router.post("/enrollments", response_model=dict)
async def enroll_students(
    enrollment_data: EnrollmentCreate,
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """將學生加入教室"""
    # 驗證教室存在
    classroom = db.query(Classroom).filter(
        Classroom.id == enrollment_data.classroom_id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    enrolled_count = 0
    for student_id in enrollment_data.student_ids:
        # 檢查學生是否存在
        student = db.query(Student).filter(
            Student.id == student_id
        ).first()
        
        if not student:
            continue
        
        # 檢查是否已註冊
        existing = db.query(ClassroomStudent).filter(
            ClassroomStudent.student_id == student_id,
            ClassroomStudent.classroom_id == enrollment_data.classroom_id
        ).first()
        
        if existing:
            continue
        
        # 創建註冊記錄
        enrollment = ClassroomStudent(
            student_id=student_id,
            classroom_id=enrollment_data.classroom_id
        )
        db.add(enrollment)
        enrolled_count += 1
    
    db.commit()
    
    return {
        "enrolled_count": enrolled_count,
        "classroom_id": enrollment_data.classroom_id,
        "classroom_name": classroom.name
    }


# ===== 課程管理 =====
@router.post("/courses", response_model=dict)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """創建機構課程"""
    course = Course(**course_data.dict())
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "school_id": course.school_id,
        "school_name": course.school.name,
        "difficulty_level": course.difficulty_level,
        "is_template": course.is_template,
        "type": "institutional"
    }


@router.get("/courses", response_model=List[dict])
async def get_courses(
    school_id: Optional[str] = Query(None),
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """獲取機構課程列表"""
    query = db.query(Course)
    
    if school_id:
        query = query.filter(Course.school_id == school_id)
    
    courses = query.all()
    
    return [{
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "school_id": course.school_id,
        "school_name": course.school.name,
        "difficulty_level": course.difficulty_level,
        "is_template": course.is_template,
        "lesson_count": len(course.lessons),
        "type": "institutional"
    } for course in courses]


@router.post("/courses/{course_id}/lessons", response_model=dict)
async def create_lesson(
    course_id: str,
    lesson_data: LessonCreate,
    current_user: User = Depends(require_institutional_admin),
    db: Session = Depends(get_db)
):
    """為課程創建課時"""
    # 驗證課程存在
    course = db.query(Course).filter(
        Course.id == course_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="課程不存在")
    
    lesson = Lesson(
        **lesson_data.dict(),
        course_id=course_id
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return {
        "id": lesson.id,
        "course_id": lesson.course_id,
        "lesson_number": lesson.lesson_number,
        "title": lesson.title,
        "activity_type": lesson.activity_type,
        "content": lesson.content,
        "time_limit_minutes": lesson.time_limit_minutes
    }