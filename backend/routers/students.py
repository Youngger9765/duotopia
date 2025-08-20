from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/students", tags=["students"])

@router.get("/profile")
async def get_student_profile(
    db: Session = Depends(get_db)
):
    """Get student profile based on token"""
    # For testing, return a mock profile
    # In production, decode the JWT token to get student info
    return {
        "id": "test-student-id",
        "name": "Test Student",
        "grade": 10,
        "school": "Test High School",
        "phone_number": "+1234567890"
    }

@router.post("/register", response_model=schemas.Student)
async def register_student(
    student_data: schemas.StudentCreate,
    db: Session = Depends(get_db)
):
    """Register a new student"""
    # Check if email already exists
    existing = db.query(models.Student).filter(
        models.Student.email == student_data.email
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_student = models.Student(**student_data.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@router.get("/teachers/search")
async def search_teachers_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """Search for teachers by email (for student login flow)"""
    teacher = db.query(models.User).filter(
        models.User.email == email,
        models.User.role == models.UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return {
        "id": teacher.id,
        "email": teacher.email,
        "full_name": teacher.full_name
    }

@router.get("/teachers/{teacher_id}/classes")
async def get_teacher_classes(
    teacher_id: str,
    db: Session = Depends(get_db)
):
    """Get all classes for a specific teacher"""
    classes = db.query(models.Class).filter(
        models.Class.teacher_id == teacher_id,
        models.Class.is_active == True
    ).all()
    
    return [{
        "id": c.id,
        "name": c.name,
        "grade_level": c.grade_level
    } for c in classes]

@router.get("/classes/{class_id}/students")
async def get_class_students(
    class_id: str,
    db: Session = Depends(get_db)
):
    """Get all students in a class (for student selection)"""
    students = db.query(models.Student).join(models.ClassroomStudent).filter(
        models.ClassroomStudent.classroom_id == class_id
    ).all()
    
    return [{
        "id": s.id,
        "full_name": s.full_name,
        "email": s.email
    } for s in students]

@router.post("/verify-password")
async def verify_student_password(
    request: schemas.StudentPasswordVerify,
    db: Session = Depends(get_db)
):
    """Verify student password (birth date) and return access token"""
    from auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    from datetime import timedelta
    
    student = db.query(models.Student).filter(
        models.Student.id == request.student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if birth_date matches (expecting YYYYMMDD format)
    if student.birth_date != request.password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.email, "role": "student", "student_id": student.id}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": student.id,
            "name": student.full_name,
            "email": student.email
        }
    }

@router.get("/{student_id}/assignments")
async def get_student_assignments(
    student_id: str,
    db: Session = Depends(get_db)
):
    """Get all assignments for a student"""
    assignments = db.query(models.StudentAssignment).filter(
        models.StudentAssignment.student_id == student_id
    ).order_by(models.StudentAssignment.assigned_at.desc()).all()
    
    # Get lesson details for each assignment
    result = []
    for assignment in assignments:
        lesson = db.query(models.Lesson).filter(
            models.Lesson.id == assignment.lesson_id
        ).first()
        
        if lesson:
            result.append({
                "id": assignment.id,
                "lesson": {
                    "id": lesson.id,
                    "title": lesson.title,
                    "activity_type": lesson.activity_type,
                    "time_limit_minutes": lesson.time_limit_minutes
                },
                "assigned_at": assignment.assigned_at,
                "due_date": assignment.due_date,
                "status": assignment.status,
                "completed_at": assignment.completed_at
            })
    
    return result

@router.get("/courses")
async def get_student_courses_auth(
    db: Session = Depends(get_db)
):
    """Get all courses for authenticated student"""
    # For testing, return mock courses
    return [
        {
            "id": "course-1",
            "title": "基礎英語會話",
            "teacher_name": "王老師",
            "description": "培養日常英語對話能力"
        },
        {
            "id": "course-2", 
            "title": "進階閱讀理解",
            "teacher_name": "李老師",
            "description": "提升英文閱讀理解與分析能力"
        }
    ]

@router.get("/{student_id}/courses")
async def get_student_courses(
    student_id: str,
    db: Session = Depends(get_db)
):
    """Get all courses available to a student through their classes"""
    # Get student's classes
    class_ids = db.query(models.ClassroomStudent.classroom_id).filter(
        models.ClassroomStudent.student_id == student_id
    ).subquery()
    
    # Get courses mapped to those classes
    courses = db.query(models.Course).join(models.ClassroomCourseMapping).filter(
        models.ClassroomCourseMapping.classroom_id.in_(class_ids),
        models.Course.is_active == True
    ).distinct().all()
    
    return courses

@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: str,
    result_data: schemas.ActivityResultCreate,
    db: Session = Depends(get_db)
):
    """Submit an assignment result"""
    # Verify assignment exists
    assignment = db.query(models.StudentAssignment).filter(
        models.StudentAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Get attempt number
    existing_attempts = db.query(models.ActivityResult).filter(
        models.ActivityResult.assignment_id == assignment_id
    ).count()
    
    # Create result
    db_result = models.ActivityResult(
        assignment_id=assignment_id,
        attempt_number=existing_attempts + 1,
        **result_data.dict()
    )
    db.add(db_result)
    
    # Update assignment status
    assignment.status = "completed"
    assignment.completed_at = db_result.submitted_at
    
    db.commit()
    db.refresh(db_result)
    return db_result

@router.put("/{student_id}/parent-info")
async def update_parent_info(
    student_id: str,
    parent_email: str,
    parent_phone: str,
    db: Session = Depends(get_db)
):
    """Update student's parent contact information"""
    student = db.query(models.Student).filter(
        models.Student.id == student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.parent_email = parent_email
    student.parent_phone = parent_phone
    
    db.commit()
    return {"message": "Parent information updated"}