"""Classroom request/response schemas for school management"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SchoolClassroomCreate(BaseModel):
    """Request to create classroom in school"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    level: str = Field(default="A1", pattern="^(PREA|A1|A2|B1|B2|C1|C2)$")
    teacher_id: Optional[int] = None  # Optional: Can assign later

    class Config:
        json_schema_extra = {
            "example": {
                "name": "一年級 A 班",
                "description": "一年級英文基礎班",
                "level": "A1",
                "teacher_id": 123
            }
        }


class SchoolClassroomUpdate(BaseModel):
    """Request to update classroom"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    level: Optional[str] = Field(None, pattern="^(PREA|A1|A2|B1|B2|C1|C2)$")
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "一年級 A 班（進階）",
                "level": "A2"
            }
        }


class AssignTeacherRequest(BaseModel):
    """Request to assign/reassign teacher to classroom"""
    teacher_id: Optional[int] = None  # None = unassign

    class Config:
        json_schema_extra = {
            "example": {
                "teacher_id": 123
            }
        }
