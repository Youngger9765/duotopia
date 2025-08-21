"""
個體戶體系 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from database import get_db
from auth import get_current_active_user
from models import User, UserRole
from models_dual_system import (
    IndividualClassroom, IndividualStudent,
    IndividualCourse, IndividualLesson, IndividualEnrollment,
    IndividualAssignment
)
from pydantic import BaseModel, EmailStr
import uuid


# ===== Schemas =====
class IndividualClassroomCreate(BaseModel):
    name: str
    grade_level: Optional[str] = None
    location: Optional[str] = "線上授課"
    pricing: Optional[int] = None
    max_students: int = 10


class IndividualStudentCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    birth_date: str
    referred_by: Optional[str] = None
    learning_goals: Optional[str] = None
    preferred_schedule: Optional[dict] = None


class IndividualCourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    is_public: bool = False
    custom_materials: bool = True
    pricing_per_lesson: Optional[int] = None
    classroom_id: Optional[str] = None


class CourseCopyRequest(BaseModel):
    source_course_id: str


class AddStudentRequest(BaseModel):
    student_id: str


class IndividualLessonCreate(BaseModel):
    lesson_number: int
    title: str
    activity_type: str
    content: dict = {}
    time_limit_minutes: int = 30
    is_active: bool = True


class IndividualEnrollmentCreate(BaseModel):
    student_id: str
    classroom_id: str
    payment_status: str = "pending"


class AssignClassroomsRequest(BaseModel):
    student_ids: List[str]
    classroom_ids: List[str]


# ===== Router =====
router = APIRouter(
    prefix="/api/individual",
    tags=["individual"]
)


# ===== Dependency =====
async def require_individual_teacher(
    current_user: User = Depends(get_current_active_user)
):
    """確保用戶是個體戶教師"""
    if not current_user.is_individual_teacher:
        raise HTTPException(status_code=403, detail="需要個體戶教師權限")
    
    if current_user.current_role_context == "institutional":
        raise HTTPException(status_code=403, detail="請切換到個體戶模式")
    
    return current_user


# ===== 教室管理 =====
@router.post("/classrooms", response_model=dict)
async def create_classroom(
    classroom_data: IndividualClassroomCreate,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """創建個體戶教室"""
    classroom = IndividualClassroom(
        **classroom_data.dict(),
        teacher_id=current_user.id
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "grade_level": classroom.grade_level,
        "teacher_id": classroom.teacher_id,
        "teacher_name": current_user.full_name,
        "location": classroom.location,
        "pricing": classroom.pricing,
        "max_students": classroom.max_students,
        "type": "individual",
        "created_at": classroom.created_at
    }


@router.get("/classrooms", response_model=List[dict])
async def get_classrooms(
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取個體戶教室列表"""
    classrooms = db.query(IndividualClassroom).filter(
        IndividualClassroom.teacher_id == current_user.id
    ).all()
    
    result = []
    for classroom in classrooms:
        # 計算當前學生數
        student_count = db.query(IndividualEnrollment).filter(
            IndividualEnrollment.classroom_id == classroom.id,
            IndividualEnrollment.is_active == True
        ).count()
        
        result.append({
            "id": classroom.id,
            "name": classroom.name,
            "grade_level": classroom.grade_level,
            "teacher_id": classroom.teacher_id,
            "teacher_name": current_user.full_name,
            "location": classroom.location,
            "pricing": classroom.pricing,
            "max_students": classroom.max_students,
            "student_count": student_count,
            "available_slots": classroom.max_students - student_count,
            "type": "individual",
            "created_at": classroom.created_at
        })
    
    return result


@router.get("/classrooms/{classroom_id}", response_model=dict)
async def get_classroom_details(
    classroom_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取教室詳情"""
    classroom = db.query(IndividualClassroom).filter(
        IndividualClassroom.id == classroom_id,
        IndividualClassroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 獲取學生列表
    enrollments = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.classroom_id == classroom_id,
        IndividualEnrollment.is_active == True
    ).all()
    
    students = []
    for enrollment in enrollments:
        student = enrollment.student
        students.append({
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "enrolled_at": enrollment.enrolled_at,
            "payment_status": enrollment.payment_status
        })
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "grade_level": classroom.grade_level,
        "location": classroom.location,
        "pricing": classroom.pricing,
        "max_students": classroom.max_students,
        "students": students,
        "student_count": len(students),
        "available_slots": classroom.max_students - len(students)
    }


@router.get("/classrooms/{classroom_id}/students", response_model=List[dict])
async def get_classroom_students(
    classroom_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取教室內的學生列表"""
    # 驗證教室屬於當前教師
    classroom = db.query(IndividualClassroom).filter(
        IndividualClassroom.id == classroom_id,
        IndividualClassroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 獲取學生列表
    enrollments = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.classroom_id == classroom_id,
        IndividualEnrollment.is_active == True
    ).all()
    
    students = []
    for enrollment in enrollments:
        student = enrollment.student
        students.append({
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "enrollment_id": enrollment.id,
            "enrolled_at": enrollment.enrolled_at,
            "payment_status": enrollment.payment_status
        })
    
    return students


@router.post("/classrooms/{classroom_id}/students", response_model=dict)
async def add_student_to_classroom(
    classroom_id: str,
    request: AddStudentRequest,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """將學生加入教室"""
    # 驗證教室屬於當前教師
    classroom = db.query(IndividualClassroom).filter(
        IndividualClassroom.id == classroom_id,
        IndividualClassroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 檢查學生是否存在
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == request.student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    # 檢查是否已經在教室中
    existing = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.classroom_id == classroom_id,
        IndividualEnrollment.student_id == request.student_id,
        IndividualEnrollment.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="學生已在教室中")
    
    # 檢查教室是否已滿
    current_count = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.classroom_id == classroom_id,
        IndividualEnrollment.is_active == True
    ).count()
    
    if current_count >= classroom.max_students:
        raise HTTPException(status_code=400, detail="教室已滿")
    
    # 創建註冊記錄
    enrollment = IndividualEnrollment(
        id=str(uuid.uuid4()),
        student_id=request.student_id,
        classroom_id=classroom_id,
        payment_status="pending"
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    return {
        "enrollment_id": enrollment.id,
        "student_id": request.student_id,
        "classroom_id": classroom_id,
        "enrolled_at": enrollment.enrolled_at,
        "payment_status": enrollment.payment_status
    }


@router.delete("/enrollments/{enrollment_id}")
async def remove_student_from_classroom(
    enrollment_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """從教室移除學生"""
    # 獲取註冊記錄
    enrollment = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.id == enrollment_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="註冊記錄不存在")
    
    # 驗證教室屬於當前教師
    classroom = enrollment.classroom
    if classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權限操作此教室")
    
    # 標記為非活躍（軟刪除）
    enrollment.is_active = False
    db.commit()
    
    return {"message": "學生已從教室移除"}


@router.get("/classrooms/{classroom_id}/courses", response_model=List[dict])
async def get_classroom_courses(
    classroom_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取教室內的課程列表"""
    # 驗證教室屬於當前教師
    classroom = db.query(IndividualClassroom).filter(
        IndividualClassroom.id == classroom_id,
        IndividualClassroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 獲取教室課程
    courses = db.query(IndividualCourse).filter(
        IndividualCourse.classroom_id == classroom_id,
        IndividualCourse.is_active == True
    ).all()
    
    result = []
    for course in courses:
        # 獲取課時數
        lesson_count = db.query(IndividualLesson).filter(
            IndividualLesson.course_id == course.id
        ).count()
        
        # 獲取複製來源資訊
        copied_from_title = None
        if course.copied_from_id:
            source_course = db.query(IndividualCourse).filter(
                IndividualCourse.id == course.copied_from_id
            ).first()
            if source_course:
                copied_from_title = source_course.title
        
        result.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "difficulty_level": course.difficulty_level,
            "is_public": course.is_public,
            "classroom_id": course.classroom_id,
            "copied_from_id": course.copied_from_id,
            "copied_from_title": copied_from_title,
            "lesson_count": lesson_count,
            "created_at": course.created_at
        })
    
    return result


@router.post("/classrooms/{classroom_id}/courses/copy", response_model=dict)
async def copy_course_to_classroom(
    classroom_id: str,
    request: CourseCopyRequest,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """從公版課程複製到教室"""
    # 驗證教室屬於當前教師
    classroom = db.query(IndividualClassroom).filter(
        IndividualClassroom.id == classroom_id,
        IndividualClassroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 獲取來源課程
    source_course = db.query(IndividualCourse).filter(
        IndividualCourse.id == request.source_course_id,
        IndividualCourse.is_public == True
    ).first()
    
    if not source_course:
        raise HTTPException(status_code=404, detail="公版課程不存在")
    
    # 創建課程副本
    new_course = IndividualCourse(
        id=str(uuid.uuid4()),
        title=f"{source_course.title} (副本)",
        description=source_course.description,
        difficulty_level=source_course.difficulty_level,
        teacher_id=current_user.id,
        classroom_id=classroom_id,
        is_public=False,
        custom_materials=True,
        pricing_per_lesson=source_course.pricing_per_lesson,
        copied_from_id=request.source_course_id,
        type="individual"
    )
    db.add(new_course)
    
    # 複製課時
    source_lessons = db.query(IndividualLesson).filter(
        IndividualLesson.course_id == request.source_course_id
    ).all()
    
    for lesson in source_lessons:
        new_lesson = IndividualLesson(
            id=str(uuid.uuid4()),
            course_id=new_course.id,
            lesson_number=lesson.lesson_number,
            title=lesson.title,
            activity_type=lesson.activity_type,
            content=lesson.content,
            time_limit_minutes=lesson.time_limit_minutes,
            type="individual"
        )
        db.add(new_lesson)
    
    db.commit()
    db.refresh(new_course)
    
    return {
        "id": new_course.id,
        "title": new_course.title,
        "description": new_course.description,
        "classroom_id": new_course.classroom_id,
        "copied_from_id": new_course.copied_from_id,
        "lesson_count": len(source_lessons)
    }


@router.get("/courses/public", response_model=List[dict])
async def get_public_courses(
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取公版課程列表"""
    courses = db.query(IndividualCourse).filter(
        IndividualCourse.is_public == True,
        IndividualCourse.is_active == True
    ).all()
    
    result = []
    for course in courses:
        # 獲取課時數
        lesson_count = db.query(IndividualLesson).filter(
            IndividualLesson.course_id == course.id
        ).count()
        
        result.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "difficulty_level": course.difficulty_level,
            "teacher_name": course.teacher.full_name if course.teacher else "系統",
            "lesson_count": lesson_count,
            "pricing_per_lesson": course.pricing_per_lesson,
            "is_public": True
        })
    
    return result


# ===== 學生管理 =====
@router.post("/students", response_model=dict)
async def create_student(
    student_data: IndividualStudentCreate,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """創建個體戶學生"""
    # 創建學生時加上所屬老師
    student_dict = student_data.dict()
    student_dict['teacher_id'] = current_user.id
    
    student = IndividualStudent(**student_dict)
    db.add(student)
    db.commit()
    db.refresh(student)
    
    # 生成預設密碼（生日格式：YYYYMMDD）
    password = student.birth_date.replace('-', '') if student.birth_date else None
    
    return {
        "id": student.id,
        "full_name": student.full_name,
        "email": student.email,
        "birth_date": student.birth_date,
        "default_password": password,  # 預設密碼
        "is_default_password": student.is_default_password,
        "referred_by": student.referred_by,
        "learning_goals": student.learning_goals,
        "preferred_schedule": student.preferred_schedule,
        "type": "individual"
    }


@router.get("/students", response_model=List[dict])
async def get_students(
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取個體戶學生列表"""
    # 直接查詢該老師的學生
    students = db.query(IndividualStudent).filter(
        IndividualStudent.teacher_id == current_user.id
    ).all()
    
    result = []
    for student in students:
        # 獲取學生的班級資訊
        enrollments = db.query(IndividualEnrollment).filter(
            IndividualEnrollment.student_id == student.id,
            IndividualEnrollment.is_active == True
        ).all()
        
        classrooms = []
        classroom_names = []
        classroom_ids = []
        
        for enrollment in enrollments:
            classrooms.append({
                "classroom_id": enrollment.classroom_id,
                "classroom_name": enrollment.classroom.name,
                "payment_status": enrollment.payment_status
            })
            classroom_names.append(enrollment.classroom.name)
            classroom_ids.append(enrollment.classroom_id)
        
        result.append({
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "birth_date": student.birth_date,
            "referred_by": student.referred_by,
            "learning_goals": student.learning_goals,
            "classroom_names": classroom_names,
            "classroom_ids": classroom_ids,
            "classrooms": classrooms,
            "is_default_password": student.is_default_password,  # 密碼狀態
            "default_password": student.default_password if student.is_default_password else None,  # 只有使用預設密碼時才顯示
            "type": "individual"
        })
    
    return result


@router.get("/students/{student_id}/classrooms", response_model=dict)
async def get_student_classrooms(
    student_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取單個學生的班級資訊"""
    # 驗證學生存在
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    # 獲取教師的教室
    teacher_classrooms = db.query(IndividualClassroom).filter(
        IndividualClassroom.teacher_id == current_user.id
    ).all()
    
    classroom_ids = [c.id for c in teacher_classrooms]
    
    # 獲取學生在這些教室的註冊記錄
    enrollments = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.student_id == student_id,
        IndividualEnrollment.classroom_id.in_(classroom_ids),
        IndividualEnrollment.is_active == True
    ).all()
    
    classrooms = []
    classroom_ids_list = []
    
    for enrollment in enrollments:
        classrooms.append({
            "classroom_id": enrollment.classroom_id,
            "classroom_name": enrollment.classroom.name,
            "payment_status": enrollment.payment_status
        })
        classroom_ids_list.append(enrollment.classroom_id)
    
    return {
        "student_id": student_id,
        "classroom_names": [c["classroom_name"] for c in classrooms],
        "classroom_ids": classroom_ids_list,
        "classrooms": classrooms
    }


@router.post("/students/assign-classrooms", response_model=dict)
async def assign_students_to_classrooms(
    request: AssignClassroomsRequest,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """批量分配學生到班級（完整更新）"""
    # 驗證所有學生存在
    students = db.query(IndividualStudent).filter(
        IndividualStudent.id.in_(request.student_ids)
    ).all()
    
    if len(students) != len(request.student_ids):
        raise HTTPException(status_code=404, detail="部分學生不存在")
    
    # 獲取教師的所有教室
    teacher_classrooms = db.query(IndividualClassroom).filter(
        IndividualClassroom.teacher_id == current_user.id
    ).all()
    
    teacher_classroom_ids = [c.id for c in teacher_classrooms]
    
    # 驗證所有指定的教室屬於當前教師
    invalid_classrooms = [cid for cid in request.classroom_ids if cid not in teacher_classroom_ids]
    if invalid_classrooms:
        raise HTTPException(status_code=404, detail="部分教室不存在或不屬於您")
    
    success_count = 0
    errors = []
    
    for student_id in request.student_ids:
        try:
            # 獲取學生在教師所有教室的現有註冊
            existing_enrollments = db.query(IndividualEnrollment).filter(
                IndividualEnrollment.student_id == student_id,
                IndividualEnrollment.classroom_id.in_(teacher_classroom_ids)
            ).all()
            
            current_classroom_ids = {e.classroom_id for e in existing_enrollments if e.is_active}
            target_classroom_ids = set(request.classroom_ids)
            
            # 獲取所有存在的註冊記錄（包括非活躍的）
            existing_classroom_ids = {e.classroom_id for e in existing_enrollments}
            current_classroom_ids = {e.classroom_id for e in existing_enrollments if e.is_active}
            
            # 需要新增的班級（完全不存在的）
            to_add = target_classroom_ids - existing_classroom_ids
            # 需要移除的班級
            to_remove = current_classroom_ids - target_classroom_ids
            # 需要重新啟用的班級（存在但非活躍的）
            to_reactivate = target_classroom_ids & (existing_classroom_ids - current_classroom_ids)
            
            # 新增班級（只有完全不存在的才創建新記錄）
            for classroom_id in to_add:
                enrollment = IndividualEnrollment(
                    id=str(uuid.uuid4()),
                    student_id=student_id,
                    classroom_id=classroom_id,
                    payment_status="pending"
                )
                db.add(enrollment)
                success_count += 1
            
            # 移除班級（設為非活躍）
            for enrollment in existing_enrollments:
                if enrollment.classroom_id in to_remove and enrollment.is_active:
                    enrollment.is_active = False
                    success_count += 1
            
            # 重新啟用班級
            for enrollment in existing_enrollments:
                if enrollment.classroom_id in to_reactivate:
                    enrollment.is_active = True
                    enrollment.payment_status = "pending"
                    success_count += 1
                    
        except Exception as e:
            errors.append(f"學生 {student_id} 分配失敗: {str(e)}")
    
    db.commit()
    
    return {
        "message": f"成功更新 {success_count} 個班級分配",
        "success_count": success_count,
        "errors": errors
    }


@router.post("/students/{student_id}/reset-password", response_model=dict)
async def reset_student_password(
    student_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """重置學生密碼為預設密碼（生日）"""
    # 驗證學生屬於當前老師
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == student_id,
        IndividualStudent.teacher_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在或不屬於您")
    
    # 重置為預設密碼
    student.is_default_password = True
    student.password_hash = None  # 清除自訂密碼
    
    db.commit()
    db.refresh(student)
    
    return {
        "message": "密碼已重置為預設密碼",
        "student_id": student_id,
        "student_name": student.full_name,
        "default_password": student.default_password,
        "is_default_password": True
    }


@router.put("/students/{student_id}", response_model=dict)
async def update_student(
    student_id: str,
    student_data: IndividualStudentCreate,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """更新學生資料"""
    # 驗證學生屬於當前老師
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == student_id,
        IndividualStudent.teacher_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在或不屬於您")
    
    # 更新學生資料
    for field, value in student_data.dict().items():
        if hasattr(student, field):
            setattr(student, field, value)
    
    # 如果生日有變更且使用預設密碼，需要更新密碼
    if student.is_default_password and student.birth_date != student_data.birth_date:
        # 預設密碼會自動更新（因為是 property）
        pass
    
    db.commit()
    db.refresh(student)
    
    return {
        "message": "學生資料更新成功",
        "student_id": student_id,
        "student_name": student.full_name,
        "is_default_password": student.is_default_password
    }


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """刪除學生"""
    # 驗證學生屬於當前老師
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == student_id,
        IndividualStudent.teacher_id == current_user.id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在或不屬於您")
    
    # 軟刪除：標記為非活躍
    student.is_active = False
    
    # 同時將所有註冊記錄標記為非活躍
    enrollments = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.student_id == student_id
    ).all()
    
    for enrollment in enrollments:
        enrollment.is_active = False
    
    db.commit()
    
    return {"message": "學生已刪除"}


# ===== 註冊管理 =====
@router.post("/enrollments", response_model=dict)
async def enroll_student(
    enrollment_data: IndividualEnrollmentCreate,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """將學生加入教室"""
    # 驗證教室屬於當前教師
    classroom = db.query(IndividualClassroom).filter(
        IndividualClassroom.id == enrollment_data.classroom_id,
        IndividualClassroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    
    # 檢查教室是否還有空位
    current_count = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.classroom_id == enrollment_data.classroom_id,
        IndividualEnrollment.is_active == True
    ).count()
    
    if current_count >= classroom.max_students:
        raise HTTPException(status_code=400, detail="教室已滿")
    
    # 檢查學生是否存在
    student = db.query(IndividualStudent).filter(
        IndividualStudent.id == enrollment_data.student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    
    # 檢查是否已註冊
    existing = db.query(IndividualEnrollment).filter(
        IndividualEnrollment.student_id == enrollment_data.student_id,
        IndividualEnrollment.classroom_id == enrollment_data.classroom_id
    ).first()
    
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="學生已在此教室")
        else:
            # 重新啟用
            existing.is_active = True
            existing.payment_status = enrollment_data.payment_status
            db.commit()
            return {
                "message": "學生重新加入教室",
                "enrollment_id": existing.id
            }
    
    # 創建註冊記錄
    enrollment = IndividualEnrollment(**enrollment_data.dict())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    return {
        "message": "註冊成功",
        "enrollment_id": enrollment.id,
        "classroom_name": classroom.name,
        "student_name": student.full_name
    }


# ===== 課程管理 =====
@router.post("/courses", response_model=dict)
async def create_course(
    course_data: IndividualCourseCreate,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """創建個體戶課程"""
    course = IndividualCourse(
        **course_data.dict(),
        teacher_id=current_user.id
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "teacher_id": course.teacher_id,
        "teacher_name": current_user.full_name,
        "difficulty_level": course.difficulty_level,
        "is_public": course.is_public,
        "custom_materials": course.custom_materials,
        "pricing_per_lesson": course.pricing_per_lesson,
        "type": "individual"
    }


@router.get("/courses", response_model=List[dict])
async def get_courses(
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取個體戶課程列表"""
    courses = db.query(IndividualCourse).filter(
        IndividualCourse.teacher_id == current_user.id
    ).all()
    
    return [{
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "difficulty_level": course.difficulty_level,
        "is_public": course.is_public,
        "custom_materials": course.custom_materials,
        "pricing_per_lesson": course.pricing_per_lesson,
        "lesson_count": len(course.lessons),
        "teacher_name": course.teacher.full_name if course.teacher else "",
        "classroom_id": None,  # 個人教師課程不屬於特定教室
        "classroom_name": None
    } for course in courses]


@router.put("/courses/{course_id}", response_model=dict)
async def update_course(
    course_id: str,
    course_data: IndividualCourseCreate,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """更新個體戶課程"""
    # 驗證課程屬於當前教師
    course = db.query(IndividualCourse).filter(
        IndividualCourse.id == course_id,
        IndividualCourse.teacher_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="課程不存在")
    
    # 更新課程資料
    for field, value in course_data.dict(exclude_unset=True).items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "difficulty_level": course.difficulty_level,
        "is_public": course.is_public,
        "custom_materials": course.custom_materials,
        "pricing_per_lesson": course.pricing_per_lesson,
        "lesson_count": len(course.lessons),
        "teacher_name": course.teacher.full_name if course.teacher else "",
        "classroom_id": course.classroom_id,
        "type": "individual"
    }


@router.get("/courses/{course_id}/lessons", response_model=List[dict])
async def get_course_lessons(
    course_id: str,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取課程的所有課時"""
    # 驗證課程屬於當前教師或是公版課程
    course = db.query(IndividualCourse).filter(
        IndividualCourse.id == course_id,
        or_(
            IndividualCourse.teacher_id == current_user.id,
            IndividualCourse.is_public == True
        )
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="課程不存在")
    
    # 獲取課程的所有課時/單元
    lessons = db.query(IndividualLesson).filter(
        IndividualLesson.course_id == course_id
    ).order_by(IndividualLesson.lesson_number).all()
    
    return [{
        "id": lesson.id,
        "course_id": lesson.course_id,
        "lesson_number": lesson.lesson_number,  # 保持一致
        "title": lesson.title,
        "activity_type": lesson.activity_type,
        "content": lesson.content,
        "time_limit_minutes": lesson.time_limit_minutes,
        "is_active": lesson.is_active
    } for lesson in lessons]


@router.post("/courses/{course_id}/lessons", response_model=dict)
async def create_lesson(
    course_id: str,
    lesson_data: IndividualLessonCreate,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """為課程創建課時"""
    # 驗證課程屬於當前教師
    course = db.query(IndividualCourse).filter(
        IndividualCourse.id == course_id,
        IndividualCourse.teacher_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="課程不存在")
    
    lesson = IndividualLesson(
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


# ===== 作業管理 =====
@router.post("/assignments", response_model=dict)
async def create_assignment(
    student_id: str,
    lesson_id: str,
    due_date: Optional[datetime] = None,
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """創建個人化作業"""
    # 驗證課程屬於當前教師
    lesson = db.query(IndividualLesson).join(
        IndividualCourse
    ).filter(
        IndividualLesson.id == lesson_id,
        IndividualCourse.teacher_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="課時不存在")
    
    # 驗證學生在教師的教室中
    enrollment = db.query(IndividualEnrollment).join(
        IndividualClassroom
    ).filter(
        IndividualEnrollment.student_id == student_id,
        IndividualClassroom.teacher_id == current_user.id,
        IndividualEnrollment.is_active == True
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="學生不在您的教室中")
    
    # 創建作業
    assignment = IndividualAssignment(
        student_id=student_id,
        lesson_id=lesson_id,
        due_date=due_date
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    return {
        "id": assignment.id,
        "student_id": assignment.student_id,
        "lesson_id": assignment.lesson_id,
        "assigned_at": assignment.assigned_at,
        "due_date": assignment.due_date,
        "status": assignment.status
    }


@router.get("/assignments", response_model=List[dict])
async def get_assignments(
    student_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_individual_teacher),
    db: Session = Depends(get_db)
):
    """獲取作業列表"""
    # 獲取教師的所有課程
    teacher_courses = db.query(IndividualCourse).filter(
        IndividualCourse.teacher_id == current_user.id
    ).all()
    
    course_ids = [c.id for c in teacher_courses]
    
    # 獲取這些課程的所有課時
    lessons = db.query(IndividualLesson).filter(
        IndividualLesson.course_id.in_(course_ids)
    ).all()
    
    lesson_ids = [l.id for l in lessons]
    
    # 查詢作業
    query = db.query(IndividualAssignment).filter(
        IndividualAssignment.lesson_id.in_(lesson_ids)
    )
    
    if student_id:
        query = query.filter(IndividualAssignment.student_id == student_id)
    
    if status:
        query = query.filter(IndividualAssignment.status == status)
    
    assignments = query.all()
    
    result = []
    for assignment in assignments:
        student = assignment.student
        lesson = assignment.lesson
        
        result.append({
            "id": assignment.id,
            "student_id": assignment.student_id,
            "student_name": student.full_name,
            "lesson_id": assignment.lesson_id,
            "lesson_title": lesson.title,
            "course_title": lesson.course.title,
            "assigned_at": assignment.assigned_at,
            "due_date": assignment.due_date,
            "completed_at": assignment.completed_at,
            "status": assignment.status,
            "score": assignment.score,
            "personalized_feedback": assignment.personalized_feedback
        })
    
    return result