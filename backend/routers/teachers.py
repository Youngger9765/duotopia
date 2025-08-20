from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_active_user
import models
import schemas

router = APIRouter(prefix="/api/teachers", tags=["teachers"])

@router.get("/profile")
async def get_teacher_profile(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get teacher profile"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active
    }

@router.get("/dashboard")
async def get_dashboard(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard data"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get teacher's classrooms
    classrooms = db.query(models.Classroom).filter(
        models.Classroom.teacher_id == current_user.id,
        models.Classroom.is_active == True
    ).all()
    
    # Get teacher's courses
    courses = db.query(models.Course).filter(
        models.Course.created_by == current_user.id,
        models.Course.is_active == True
    ).all()
    
    # Get recent assignments
    # This would need a more complex query joining through classes
    
    return {
        "classrooms": classrooms,
        "courses": courses,
        "stats": {
            "total_classrooms": len(classrooms),
            "total_courses": len(courses),
            "total_students": 0,  # TODO: Calculate from classroom enrollments
            "pending_grading": 0  # TODO: Calculate from submissions
        }
    }

@router.post("/classrooms", response_model=schemas.Classroom)
async def create_classroom(
    classroom_data: schemas.ClassroomCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new classroom"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_classroom = models.Classroom(
        **classroom_data.dict(),
        teacher_id=current_user.id
    )
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return db_classroom

@router.get("/classrooms", response_model=List[schemas.Classroom])
async def get_classrooms(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all classrooms for the current teacher"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    classrooms = db.query(models.Classroom).filter(
        models.Classroom.teacher_id == current_user.id
    ).all()
    return classrooms

@router.post("/classrooms/{classroom_id}/students")
async def add_students_to_classroom(
    classroom_id: str,
    student_ids: List[str],
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add students to a classroom"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify teacher owns the classroom
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Add students to classroom
    added_students = []
    for student_id in student_ids:
        # Check if student exists
        student = db.query(models.Student).filter(models.Student.id == student_id).first()
        if not student:
            continue
            
        # Check if already enrolled
        existing = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.classroom_id == classroom_id,
            models.ClassroomStudent.student_id == student_id
        ).first()
        
        if not existing:
            enrollment = models.ClassroomStudent(
                classroom_id=classroom_id,
                student_id=student_id
            )
            db.add(enrollment)
            added_students.append(student_id)
    
    db.commit()
    return {"added_students": added_students}

@router.post("/courses")
async def create_course(
    course_data: schemas.CourseCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate a unique course code
    import random
    import string
    course_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Check if code already exists
    while db.query(models.Course).filter(models.Course.course_code == course_code).first():
        course_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    db_course = models.Course(
        **course_data.dict(),
        course_code=course_code,
        created_by=current_user.id
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    return {
        "id": db_course.id,
        "title": db_course.title,
        "description": db_course.description,
        "course_code": db_course.course_code,
        "grade_level": db_course.grade_level,
        "subject": db_course.subject,
        "max_students": db_course.max_students,
        "created_at": db_course.created_at
    }

@router.get("/courses", response_model=List[schemas.Course])
async def get_courses(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all courses created by the teacher"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    courses = db.query(models.Course).filter(
        models.Course.created_by == current_user.id
    ).all()
    return courses

@router.get("/courses/{course_id}")
async def get_course_details(
    course_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific course"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get course with enrollments
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.created_by == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get enrolled students
    students = []
    for enrollment in course.enrollments:
        student = enrollment.student
        students.append({
            "id": student.id,
            "name": student.name or student.full_name,
            "grade": student.grade,
            "school": student.school,
            "enrolled_at": enrollment.enrolled_at
        })
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "course_code": course.course_code,
        "grade_level": course.grade_level,
        "subject": course.subject,
        "max_students": course.max_students,
        "students": students,
        "created_at": course.created_at
    }

@router.post("/courses/{course_id}/lessons", response_model=schemas.Lesson)
async def create_lesson(
    course_id: str,
    lesson_data: schemas.LessonCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new lesson in a course"""
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
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
    if current_user.role not in [models.UserRole.TEACHER, models.UserRole.ADMIN]:
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