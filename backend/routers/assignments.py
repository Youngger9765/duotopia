"""
Backward compatibility layer for assignments router.

Original file refactored into routers/assignments/ directory structure:
- validators.py: Pydantic models and schemas
- utils.py: Helper functions (audio processing, scoring)
- dependencies.py: Shared dependencies
- crud.py: Create, read, update, delete operations
- detail.py: Assignment details and progress
- submission.py: Student submission endpoints
- grading.py: AI and manual grading operations

Backup of original file: assignments_backup.py
"""

from .assignments import router

__all__ = ["router"]
