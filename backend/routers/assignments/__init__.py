"""
Assignment routers - modular structure

This module aggregates all assignment-related routers:
- CRUD operations
- Assignment details and progress
- Student submissions
- Grading (AI and manual)
"""

from fastapi import APIRouter
from . import crud, detail, submission, grading

# Main router with prefix
router = APIRouter(prefix="/api/teachers/assignments", tags=["assignments"])

# Include CRUD operations (create, read, update, delete)
router.include_router(crud.router, tags=["assignments-crud"])

# Include detail and progress endpoints
router.include_router(detail.router, tags=["assignments-detail"])

# Include student submission endpoints
router.include_router(submission.router, tags=["assignments-submission"])

# Include grading endpoints (AI and manual)
router.include_router(grading.router, tags=["assignments-grading"])

# Export functions for backward compatibility with tests
from .grading import get_student_submission

__all__ = ["router", "get_student_submission"]
