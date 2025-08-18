from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_active_user
import models
import schemas

router = APIRouter(prefix="/api/teachers", tags=["teachers"])

@router.get("/dashboard")
async def get_dashboard(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard data"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get teacher's classes
    classes = db.query(models.Class).filter(
        models.Class.teacher_id == current_user.id,
        models.Class.is_active == True
    ).all()
    
    # Get teacher's courses
    courses = db.query(models.Course).filter(
        models.Course.created_by == current_user.id,
        models.Course.is_active == True
    ).all()
    
    # Get recent assignments
    # This would need a more complex query joining through classes
    
    return {
        "classes": classes,
        "courses": courses,
        "stats": {
            "total_classes": len(classes),
            "total_courses": len(courses),
            "total_students": 0,  # TODO: Calculate from class enrollments
            "pending_grading": 0  # TODO: Calculate from submissions
        }
    }

@router.post("/classes", response_model=schemas.Class)
async def create_class(
    class_data: schemas.ClassCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new class"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_class = models.Class(
        **class_data.dict(),
        teacher_id=current_user.id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

@router.get("/classes", response_model=List[schemas.Class])
async def get_classes(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all classes for the current teacher"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    classes = db.query(models.Class).filter(
        models.Class.teacher_id == current_user.id
    ).all()
    return classes

@router.post("/classes/{class_id}/students")
async def add_students_to_class(
    class_id: str,
    student_ids: List[str],
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add students to a class"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify teacher owns the class
    class_ = db.query(models.Class).filter(
        models.Class.id == class_id,
        models.Class.teacher_id == current_user.id
    ).first()
    
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Add students to class
    added_students = []
    for student_id in student_ids:
        # Check if student exists
        student = db.query(models.Student).filter(models.Student.id == student_id).first()
        if not student:
            continue
            
        # Check if already enrolled
        existing = db.query(models.ClassStudent).filter(
            models.ClassStudent.class_id == class_id,
            models.ClassStudent.student_id == student_id
        ).first()
        
        if not existing:
            enrollment = models.ClassStudent(
                class_id=class_id,
                student_id=student_id
            )
            db.add(enrollment)
            added_students.append(student_id)
    
    db.commit()
    return {"added_students": added_students}

@router.post("/courses", response_model=schemas.Course)
async def create_course(
    course_data: schemas.CourseCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_course = models.Course(
        **course_data.dict(),
        created_by=current_user.id
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/courses", response_model=List[schemas.Course])
async def get_courses(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all courses created by the teacher"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    courses = db.query(models.Course).filter(
        models.Course.created_by == current_user.id
    ).all()
    return courses

@router.post("/courses/{course_id}/lessons", response_model=schemas.Lesson)
async def create_lesson(
    course_id: str,
    lesson_data: schemas.LessonCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new lesson in a course"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify teacher owns the course
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.created_by == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db_lesson = models.Lesson(
        **lesson_data.dict(),
        course_id=course_id
    )
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

@router.post("/assignments")
async def create_assignments(
    assignment_data: schemas.AssignmentCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create assignments for students"""
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify lesson exists and teacher has access
    lesson = db.query(models.Lesson).join(models.Course).filter(
        models.Lesson.id == assignment_data.lesson_id,
        models.Course.created_by == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Create assignments
    created_assignments = []
    for student_id in assignment_data.student_ids:
        assignment = models.StudentAssignment(
            student_id=student_id,
            lesson_id=assignment_data.lesson_id,
            due_date=assignment_data.due_date
        )
        db.add(assignment)
        created_assignments.append(assignment)
    
    db.commit()
    return {"created": len(created_assignments)}