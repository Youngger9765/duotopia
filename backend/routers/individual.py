"""
個體戶教師 API - 使用原始系統模型
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from auth import get_current_active_user
from models import (
    User, Classroom, Student, Course, Lesson, 
    ClassroomStudent, ClassroomCourseMapping, StudentAssignment
)
from pydantic import BaseModel, EmailStr

# ===== Schemas =====
class ClassroomCreate(BaseModel):
    name: str
    grade_level: Optional[str] = None
    difficulty_level: Optional[str] = None

class ClassroomResponse(BaseModel):
    id: str
    name: str
    grade_level: Optional[str]
    student_count: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class StudentCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    birth_date: str
    
class StudentResponse(BaseModel):
    id: str
    full_name: str
    name: Optional[str] = None  # 兼容性欄位
    email: Optional[str]
    birth_date: str
    classroom_names: List[str] = []
    referred_by: Optional[str] = None
    learning_goals: Optional[str] = None
    is_default_password: Optional[bool] = None
    default_password: Optional[str] = None
    
    class Config:
        orm_mode = True

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty_level: Optional[str] = None

class CourseResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    difficulty_level: Optional[str]
    lesson_count: int = 0
    
    class Config:
        orm_mode = True

# ===== Router =====
router = APIRouter(
    prefix="/api/individual",
    tags=["individual"]
)

# ===== Dependencies =====
async def get_individual_teacher(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """確保用戶是個體戶教師"""
    if not current_user.is_individual_teacher:
        raise HTTPException(
            status_code=403, 
            detail="需要個體戶教師權限"
        )
    return current_user

# ===== 教室管理 =====
@router.get("/classrooms", response_model=List[ClassroomResponse])
async def get_classrooms(
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取個體戶教師的教室列表"""
    # 查詢教師的教室（school_id 為 None 表示個體戶）
    classrooms = db.query(Classroom).filter(
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None,
        Classroom.is_active == True
    ).all()
    
    result = []
    for classroom in classrooms:
        # 計算學生數量
        student_count = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == classroom.id
        ).count()
        
        result.append({
            "id": classroom.id,
            "name": classroom.name,
            "grade_level": classroom.grade_level,
            "student_count": student_count,
            "created_at": classroom.created_at
        })
    
    return result

@router.post("/classrooms", response_model=ClassroomResponse)
async def create_classroom(
    classroom_data: ClassroomCreate,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """創建新教室"""
    classroom = Classroom(
        id=str(uuid.uuid4()),
        name=classroom_data.name,
        grade_level=classroom_data.grade_level,
        difficulty_level=classroom_data.difficulty_level,
        teacher_id=current_user.id,
        school_id=None  # 個體戶教師沒有學校
    )
    
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "grade_level": classroom.grade_level,
        "student_count": 0,
        "created_at": classroom.created_at
    }

@router.get("/classrooms/{classroom_id}")
async def get_classroom_detail(
    classroom_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取教室詳細資訊"""
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 獲取學生列表
    students = db.query(Student).join(
        ClassroomStudent
    ).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).all()
    
    # 獲取課程列表
    courses = db.query(Course).join(
        ClassroomCourseMapping
    ).filter(
        ClassroomCourseMapping.classroom_id == classroom_id
    ).all()
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "grade_level": classroom.grade_level,
        "teacher_name": current_user.full_name,
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email
            } for s in students
        ],
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description
            } for c in courses
        ],
        "student_count": len(students),
        "course_count": len(courses)
    }

@router.delete("/classrooms/{classroom_id}")
async def delete_classroom(
    classroom_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """刪除教室"""
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 軟刪除
    classroom.is_active = False
    db.commit()
    
    return {"message": "教室已刪除"}

# ===== 學生管理 =====
@router.get("/students", response_model=List[StudentResponse])
async def get_students(
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取個體戶教師的所有學生"""
    # 使用優化的查詢避免 N+1 問題
    # 使用 eager loading 一次性獲取所有數據
    from sqlalchemy.orm import contains_eager
    
    # 一次查詢獲取所有學生及其教室關聯
    students_with_classrooms = (
        db.query(Student)
        .join(ClassroomStudent)
        .join(Classroom)
        .options(contains_eager(Student.classroom_enrollments).contains_eager(ClassroomStudent.classroom))
        .filter(
            Classroom.teacher_id == current_user.id,
            Classroom.school_id == None
        )
        .distinct()
        .all()
    )
    
    # 構建結果，使用已經加載的關聯數據
    result = []
    for student in students_with_classrooms:
        # 從已加載的關聯中獲取教室名稱
        classroom_names = [
            enrollment.classroom.name 
            for enrollment in student.classroom_enrollments 
            if enrollment.classroom.teacher_id == current_user.id and enrollment.classroom.school_id is None
        ]
        
        result.append({
            "id": student.id,
            "full_name": student.full_name,
            "name": student.full_name,  # 兼容性
            "email": student.email,
            "birth_date": f"{student.birth_date[:4]}-{student.birth_date[4:6]}-{student.birth_date[6:8]}" if student.birth_date else "",
            "classroom_names": classroom_names
        })
    
    return result

@router.post("/students", response_model=StudentResponse)
async def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """創建新學生"""
    # 檢查 email 是否已存在
    if student_data.email:
        existing = db.query(Student).filter(
            Student.email == student_data.email
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="此 Email 已被使用"
            )
    
    student = Student(
        id=str(uuid.uuid4()),
        name=student_data.name,
        full_name=student_data.name,  # Student 模型需要 full_name
        email=student_data.email,
        birth_date=student_data.birth_date.replace("-", "")  # 轉換為 YYYYMMDD 格式
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    return {
        "id": student.id,
        "full_name": student.full_name,  # 前端期望的 full_name 欄位  
        "name": student.full_name,  # 兼容性
        "email": student.email,
        "birth_date": f"{student.birth_date[:4]}-{student.birth_date[4:6]}-{student.birth_date[6:8]}",
        "classroom_names": []
    }

@router.put("/students/{student_id}")
async def update_student(
    student_id: str,
    student_data: StudentCreate,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """更新學生資料"""
    # 通過教室確認學生屬於該教師
    student = db.query(Student).join(
        ClassroomStudent
    ).join(
        Classroom
    ).filter(
        Student.id == student_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    student.name = student_data.name
    student.full_name = student_data.name
    student.email = student_data.email
    student.birth_date = student_data.birth_date.replace("-", "")
    
    db.commit()
    db.refresh(student)
    
    return {"message": "學生資料已更新"}

@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """刪除學生"""
    # 通過教室確認學生屬於該教師
    student = db.query(Student).join(
        ClassroomStudent
    ).join(
        Classroom
    ).filter(
        Student.id == student_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    # 先刪除教室關聯
    db.query(ClassroomStudent).filter(
        ClassroomStudent.student_id == student_id
    ).delete()
    
    # 刪除學生
    db.delete(student)
    db.commit()
    
    return {"message": "學生已刪除"}

# ===== 教室學生管理 =====
@router.post("/classrooms/{classroom_id}/students/{student_id}")
async def add_student_to_classroom(
    classroom_id: str,
    student_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """將學生加入教室"""
    # 驗證教室
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 驗證學生（通過教室關聯驗證）
    student = db.query(Student).join(
        ClassroomStudent
    ).join(
        Classroom
    ).filter(
        Student.id == student_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    # 檢查是否已在教室中
    existing = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id,
        ClassroomStudent.student_id == student_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="學生已在教室中")
    
    # 加入教室
    classroom_student = ClassroomStudent(
        id=str(uuid.uuid4()),
        classroom_id=classroom_id,
        student_id=student_id
    )
    
    db.add(classroom_student)
    db.commit()
    
    return {"message": "學生已加入教室"}

@router.delete("/classrooms/{classroom_id}/students/{student_id}")
async def remove_student_from_classroom(
    classroom_id: str,
    student_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """將學生從教室移除"""
    # 驗證教室屬於教師
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 刪除關聯
    result = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id,
        ClassroomStudent.student_id == student_id
    ).delete()
    
    if result == 0:
        raise HTTPException(status_code=404, detail="學生不在此教室中")
    
    db.commit()
    
    return {"message": "學生已從教室移除"}

@router.get("/classrooms/{classroom_id}/students")
async def get_classroom_students(
    classroom_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取教室內的學生列表"""
    # 驗證教室
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 獲取學生
    students = db.query(Student).join(
        ClassroomStudent
    ).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).all()
    
    return [
        {
            "id": s.id,
            "full_name": s.full_name,  # 前端期望的 full_name 欄位
            "name": s.full_name,  # 兼容性
            "email": s.email
        } for s in students
    ]

# ===== 課程管理 =====
@router.get("/courses", response_model=List[CourseResponse])
async def get_courses(
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取個體戶教師的課程"""
    courses = db.query(Course).filter(
        Course.created_by == current_user.id
    ).all()
    
    result = []
    for course in courses:
        lesson_count = db.query(Lesson).filter(
            Lesson.course_id == course.id
        ).count()
        
        result.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "difficulty_level": course.difficulty_level,
            "lesson_count": lesson_count,
            "pricing_per_lesson": 0,  # 個體戶教師可以自行設定價格
            "is_public": False,  # 個體戶教師的課程預設為私有
            "teacher_name": current_user.full_name
        })
    
    return result

@router.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """創建新課程"""
    course = Course(
        id=str(uuid.uuid4()),
        title=course_data.title,
        description=course_data.description,
        difficulty_level=course_data.difficulty_level,
        created_by=current_user.id
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "difficulty_level": course.difficulty_level,
        "lesson_count": 0
    }

@router.get("/courses/{course_id}/lessons")
async def get_course_lessons(
    course_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取課程的單元列表"""
    # 驗證課程屬於該教師
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.created_by == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="課程不存在")
    
    # 獲取課程的單元
    lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).order_by(Lesson.lesson_number).all()
    
    return [
        {
            "id": lesson.id,
            "course_id": lesson.course_id,
            "lesson_number": lesson.lesson_number,
            "title": lesson.title,
            "activity_type": lesson.activity_type,
            "time_limit_minutes": lesson.time_limit_minutes,
            "target_wpm": lesson.target_wpm,
            "target_accuracy": lesson.target_accuracy,
            "is_active": lesson.is_active
        }
        for lesson in lessons
    ]

# ===== 統計資料 =====
@router.get("/classrooms/{classroom_id}/stats")
async def get_classroom_stats(
    classroom_id: str,
    current_user: User = Depends(get_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取教室統計資料"""
    # 驗證教室
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_user.id,
        Classroom.school_id == None
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 學生總數
    total_students = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).count()
    
    # 進行中的作業
    active_assignments = db.query(StudentAssignment).join(
        Student
    ).join(
        ClassroomStudent
    ).filter(
        ClassroomStudent.classroom_id == classroom_id,
        StudentAssignment.status == "assigned"
    ).count()
    
    # 完成率（簡化版）
    total_assignments = db.query(StudentAssignment).join(
        Student
    ).join(
        ClassroomStudent
    ).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).count()
    
    completed_assignments = db.query(StudentAssignment).join(
        Student
    ).join(
        ClassroomStudent
    ).filter(
        ClassroomStudent.classroom_id == classroom_id,
        StudentAssignment.status == "completed"
    ).count()
    
    completion_rate = (
        int((completed_assignments / total_assignments) * 100) 
        if total_assignments > 0 else 0
    )
    
    # 平均分數（簡化版）
    scores = db.query(StudentAssignment.score).join(
        Student
    ).join(
        ClassroomStudent
    ).filter(
        ClassroomStudent.classroom_id == classroom_id,
        StudentAssignment.score != None
    ).all()
    
    average_score = (
        sum(s[0] for s in scores) / len(scores) 
        if scores else 0
    )
    
    return {
        "total_students": total_students,
        "active_assignments": active_assignments,
        "completion_rate": completion_rate,
        "average_score": round(average_score, 1)
    }