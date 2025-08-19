from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import User, Student, School, Class, Course, ClassStudent, ClassCourseMapping
from schemas import (
    SchoolCreate, SchoolUpdate, School as SchoolSchema,
    UserCreate, UserUpdate, User as UserSchema,
    StudentUpdate, Student as StudentSchema
)
from auth import get_current_user, require_admin

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]  # Ensure only admins can access these routes
)

# School/Institution Management
@router.get("/schools", response_model=List[SchoolSchema])
async def get_schools(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all schools/institutions"""
    schools = db.query(School).all()
    return schools

@router.get("/schools/{school_id}", response_model=SchoolSchema)
async def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific school by ID"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.post("/schools", response_model=SchoolSchema)
async def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new school/institution"""
    db_school = School(**school.dict())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school

@router.put("/schools/{school_id}", response_model=SchoolSchema)
async def update_school(
    school_id: int,
    school: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a school/institution"""
    db_school = db.query(School).filter(School.id == school_id).first()
    if not db_school:
        raise HTTPException(status_code=404, detail="School not found")
    
    for key, value in school.dict(exclude_unset=True).items():
        setattr(db_school, key, value)
    
    db.commit()
    db.refresh(db_school)
    return db_school

@router.delete("/schools/{school_id}")
async def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a school/institution"""
    db_school = db.query(School).filter(School.id == school_id).first()
    if not db_school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Check if there are users or students associated with this school
    users_count = db.query(User).filter(User.school_id == school_id).count()
    students_count = db.query(Student).filter(Student.school_id == school_id).count()
    
    if users_count > 0 or students_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete school with {users_count} users and {students_count} students"
        )
    
    db.delete(db_school)
    db.commit()
    return {"message": "School deleted successfully"}

# User/Staff Management
@router.get("/users", response_model=List[UserSchema])
async def get_users(
    role: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users with optional filtering"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if school_id:
        query = query.filter(User.school_id == school_id)
    
    users = query.all()
    return users

@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user (teacher/admin)"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user with hashed password
    from ..auth import get_password_hash
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        school_id=user.school_id,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow users to change their own role
    if current_user.id == user_id and user.role and user.role != db_user.role:
        raise HTTPException(status_code=403, detail="Cannot change your own role")
    
    for key, value in user.dict(exclude_unset=True).items():
        if key == "password" and value:
            from ..auth import get_password_hash
            setattr(db_user, "hashed_password", get_password_hash(value))
        elif key != "password":
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a user"""
    if current_user.id == user_id:
        raise HTTPException(status_code=403, detail="Cannot delete your own account")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has associated data
    classes_count = db.query(Class).filter(Class.teacher_id == user_id).count()
    courses_count = db.query(Course).filter(Course.teacher_id == user_id).count()
    
    if classes_count > 0 or courses_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user with {classes_count} classes and {courses_count} courses"
        )
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user active status"""
    if current_user.id == user_id:
        raise HTTPException(status_code=403, detail="Cannot change your own status")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.is_active = status.get("status") == "active"
    db.commit()
    db.refresh(db_user)
    return {"message": f"User status updated to {'active' if db_user.is_active else 'inactive'}"}

# Student Management
@router.get("/students", response_model=List[StudentSchema])
async def get_students(
    school_id: Optional[int] = Query(None),
    class_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all students with optional filtering"""
    query = db.query(Student)
    
    if school_id:
        query = query.filter(Student.school_id == school_id)
    
    if class_id:
        # Join with ClassStudent to filter by class
        query = query.join(ClassStudent).filter(ClassStudent.class_id == class_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Student.name.like(search_pattern)) |
            (Student.email.like(search_pattern)) |
            (Student.phone.like(search_pattern))
        )
    
    students = query.all()
    return students

@router.get("/students/{student_id}", response_model=StudentSchema)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed student information"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/students/{student_id}", response_model=StudentSchema)
async def update_student(
    student_id: int,
    student: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update student information"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    for key, value in student.dict(exclude_unset=True).items():
        setattr(db_student, key, value)
    
    db.commit()
    db.refresh(db_student)
    return db_student

@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a student"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Delete related records
    db.query(ClassStudent).filter(ClassStudent.student_id == student_id).delete()
    
    db.delete(db_student)
    db.commit()
    return {"message": "Student deleted successfully"}

# Statistics
@router.get("/stats")
async def get_platform_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall platform statistics"""
    stats = {
        "total_schools": db.query(School).count(),
        "total_users": db.query(User).count(),
        "total_teachers": db.query(User).filter(User.role == "teacher").count(),
        "total_admins": db.query(User).filter(User.role == "admin").count(),
        "total_students": db.query(Student).count(),
        "total_classes": db.query(Class).count(),
        "total_courses": db.query(Course).count(),
        "active_users": db.query(User).filter(User.is_active == True).count(),
        "schools": []
    }
    
    # Get stats per school
    schools = db.query(School).all()
    for school in schools:
        school_stats = {
            "id": school.id,
            "name": school.name,
            "users": db.query(User).filter(User.school_id == school.id).count(),
            "students": db.query(Student).filter(Student.school_id == school.id).count(),
            "classes": db.query(Class).filter(Class.school_id == school.id).count(),
            "courses": db.query(Course).filter(Course.school_id == school.id).count()
        }
        stats["schools"].append(school_stats)
    
    return stats