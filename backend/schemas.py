from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any  # noqa: F401
from datetime import datetime  # noqa: F401
from enum import Enum
from models import ProgramLevel  # 使用 models 中定義的 Enum


# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str  # "teacher" or "student"
    user_id: int
    name: str


# Teacher schemas
class TeacherCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class TeacherResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Program schemas
class ProgramBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: Optional[ProgramLevel] = ProgramLevel.A1
    estimated_hours: Optional[int] = None
    tags: Optional[List[str]] = None


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(ProgramBase):
    name: Optional[str] = None


class ProgramResponse(ProgramBase):
    id: int
    is_template: bool
    classroom_id: Optional[int] = None
    teacher_id: int
    source_type: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed fields
    classroom_name: Optional[str] = None
    teacher_name: Optional[str] = None
    lesson_count: Optional[int] = 0
    is_duplicate: Optional[bool] = None

    class Config:
        from_attributes = True


class ProgramCopyFromTemplate(BaseModel):
    template_id: int
    classroom_id: int
    name: Optional[str] = None  # 可選，預設使用模板名稱


class ProgramCopyFromClassroom(BaseModel):
    source_program_id: int
    target_classroom_id: int
    name: Optional[str] = None  # 可選，預設使用來源名稱


# Lesson schemas
class LessonBase(BaseModel):
    name: str
    description: Optional[str] = None
    order_index: int = 0
    estimated_minutes: Optional[int] = None


class LessonCreate(LessonBase):
    pass


class LessonResponse(LessonBase):
    id: int
    program_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Student schemas for teacher dashboard
class StudentCreate(BaseModel):
    name: str
    email: Optional[str] = None
    student_number: Optional[str] = None
    birthdate: str
    classroom_id: Optional[int] = None


class StudentResponse(BaseModel):
    id: int
    email: Optional[str] = None
    name: str
    class_id: Optional[int]
    is_active: bool
    created_at: datetime
    parent_email: Optional[str] = None
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Email verification schemas
class EmailVerificationRequest(BaseModel):
    parent_email: EmailStr


class EmailVerificationResponse(BaseModel):
    message: str
    email: str
    verification_sent: bool


class EmailVerifyToken(BaseModel):
    token: str


class StudentEmailUpdate(BaseModel):
    parent_email: EmailStr


# Class schemas
class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ClassResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    teacher_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Assignment Status Enum
class AssignmentStatusEnum(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"
    RETURNED = "RETURNED"
    RESUBMITTED = "RESUBMITTED"


# Assignment schemas
class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    classroom_id: int
    content_ids: List[int] = Field(..., min_items=1)
    student_ids: List[int] = []
    due_date: Optional[datetime] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_ids: Optional[List[int]] = None
    student_ids: Optional[List[int]] = None
    due_date: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    classroom_id: int
    teacher_id: int
    due_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssignmentWithDetails(AssignmentResponse):
    contents: Optional[List[Dict[str, Any]]] = []
    student_assignments: Optional[List[Dict[str, Any]]] = []


# Student Assignment schemas
class StudentAssignmentCreate(BaseModel):
    assignment_id: int
    student_id: int
    classroom_id: int
    title: str
    status: AssignmentStatusEnum = AssignmentStatusEnum.NOT_STARTED


class StudentAssignmentUpdate(BaseModel):
    status: Optional[AssignmentStatusEnum] = None
    score: Optional[float] = None
    feedback: Optional[str] = None


class StudentAssignmentResponse(BaseModel):
    id: int
    assignment_id: Optional[int]
    student_id: int
    classroom_id: int
    title: str
    status: AssignmentStatusEnum
    score: Optional[float]
    feedback: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StudentAssignmentWithProgress(StudentAssignmentResponse):
    content_progress: Optional[List[Dict[str, Any]]] = []


# Student Content Progress schemas
class StudentContentProgressCreate(BaseModel):
    student_assignment_id: int
    content_id: int
    status: AssignmentStatusEnum = AssignmentStatusEnum.NOT_STARTED
    order_index: int = 0


class StudentContentProgressUpdate(BaseModel):
    status: Optional[AssignmentStatusEnum] = None
    score: Optional[float] = None
    checked: Optional[bool] = None
    feedback: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    ai_scores: Optional[Dict[str, Any]] = None


class StudentContentProgressResponse(BaseModel):
    id: int
    student_assignment_id: int
    content_id: int
    status: AssignmentStatusEnum
    score: Optional[float]
    checked: Optional[bool]
    feedback: Optional[str]
    response_data: Optional[Dict[str, Any]]
    ai_scores: Optional[Dict[str, Any]]
    order_index: int

    class Config:
        from_attributes = True
