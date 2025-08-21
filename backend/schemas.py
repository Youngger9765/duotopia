from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class DifficultyLevel(str, Enum):
    PRE_A = "preA"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class ActivityType(str, Enum):
    READING_ASSESSMENT = "reading_assessment"
    SPEAKING_PRACTICE = "speaking_practice"
    SPEAKING_SCENARIO = "speaking_scenario"
    LISTENING_CLOZE = "listening_cloze"
    SENTENCE_MAKING = "sentence_making"
    SPEAKING_QUIZ = "speaking_quiz"

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None

class User(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    is_individual_teacher: bool = False
    is_institutional_admin: bool = False
    current_role_context: str = "default"
    has_multiple_roles: bool = False
    effective_role: UserRole

    class Config:
        from_attributes = True

# Student Schemas
class StudentBase(BaseModel):
    email: EmailStr
    full_name: str
    birth_date: str  # YYYYMMDD format
    parent_email: Optional[EmailStr] = None
    parent_phone: Optional[str] = None

    @validator('birth_date')
    def validate_birth_date(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('Birth date must be in YYYYMMDD format')
        return v

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    parent_phone: Optional[str] = None

class Student(StudentBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Classroom Schemas
class ClassroomBase(BaseModel):
    name: str
    grade_level: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None

class ClassroomCreate(ClassroomBase):
    pass

class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    is_active: Optional[bool] = None

class Classroom(ClassroomBase):
    id: str
    teacher_id: str
    school_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Course Schemas
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    is_active: Optional[bool] = None

class Course(CourseBase):
    id: str
    created_by: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Lesson Schemas
class LessonBase(BaseModel):
    title: str
    lesson_number: int
    activity_type: ActivityType
    content: Dict[str, Any]
    time_limit_minutes: int = 30
    target_wpm: Optional[int] = None
    target_accuracy: Optional[int] = None

class LessonCreate(LessonBase):
    pass  # course_id is provided in URL path

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    time_limit_minutes: Optional[int] = None
    target_wpm: Optional[int] = None
    target_accuracy: Optional[int] = None
    is_active: Optional[bool] = None

class Lesson(LessonBase):
    id: str
    course_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Assignment Schemas
class AssignmentCreate(BaseModel):
    student_ids: List[str]
    lesson_id: str
    due_date: datetime

class AssignmentStatus(BaseModel):
    id: str
    student_id: str
    lesson_id: str
    assigned_at: datetime
    due_date: datetime
    completed_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True

# Activity Result Schemas
class ActivityResultCreate(BaseModel):
    assignment_id: str
    result_data: Dict[str, Any]
    score: Optional[int] = None
    feedback: Optional[str] = None

class ActivityResult(BaseModel):
    id: str
    assignment_id: str
    attempt_number: int
    result_data: Dict[str, Any]
    score: Optional[int]
    feedback: Optional[str]
    submitted_at: datetime

    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    id_token: str

class StudentLoginRequest(BaseModel):
    email: str
    birth_date: str  # YYYYMMDD as password

class StudentPasswordVerify(BaseModel):
    student_id: str
    password: str  # YYYYMMDD format birth date

# School Schemas
class SchoolBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    code: Optional[str] = None

class SchoolCreate(SchoolBase):
    pass

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class School(SchoolBase):
    id: str  # Changed from int to str to support UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Extended User Schemas for Admin
class UserCreateAdmin(UserBase):
    password: str
    school_id: Optional[int] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    school_id: Optional[int] = None
    is_active: Optional[bool] = None

# Extended Student Schemas for Admin  
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    school_id: Optional[int] = None
    grade: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    parent_phone: Optional[str] = None