from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

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