"""Shared dependencies for student routers."""

from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from auth import get_current_user


def get_current_student(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Verify current user is a student and return user info."""
    if current_user.get("type") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )
    return current_user


def get_student_id(
    current_student: Dict[str, Any] = Depends(get_current_student)
) -> int:
    """Extract student ID from current user."""
    return int(current_student.get("sub"))
