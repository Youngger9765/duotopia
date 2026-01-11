"""Pydantic schemas and validators for student endpoints."""

from pydantic import BaseModel
from typing import Optional


class StudentValidateRequest(BaseModel):
    email: str
    password: str  # Can be birthdate (YYYYMMDD) or new password if changed


class StudentLoginResponse(BaseModel):
    access_token: str
    token_type: str
    student: dict


class UpdateStudentProfileRequest(BaseModel):
    name: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class EmailUpdateRequest(BaseModel):
    email: str


class SwitchAccountRequest(BaseModel):
    target_student_id: int
    password: str  # 目標帳號的密碼（生日）
