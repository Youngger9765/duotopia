"""
Shared dependencies for assignment routers
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Teacher, Student
from ..auth import get_current_user


def get_current_teacher(
    current_user=Depends(get_current_user),
) -> Teacher:
    """Verify current user is a teacher"""
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access this endpoint"
        )
    return current_user


def get_current_student(
    current_user=Depends(get_current_user),
) -> Student:
    """Verify current user is a student"""
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=403, detail="Only students can access this endpoint"
        )
    return current_user
