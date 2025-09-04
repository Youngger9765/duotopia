from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any  # noqa: F401
from datetime import datetime  # noqa: F401
from enum import Enum


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


# Student schemas
class StudentCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    class_id: Optional[int] = None


class StudentResponse(BaseModel):
    id: int
    email: str
    name: str
    class_id: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


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
