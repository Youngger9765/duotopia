"""
Backward compatibility layer for students router.

This file has been refactored into a modular structure at routers/students/
See routers/students/__init__.py for the new structure.

Original file: 1548 lines
Refactored into:
- auth.py (68 lines)
- profile.py (291 lines)
- assignments.py (527 lines)
- recordings.py (188 lines)
- email_verification.py (225 lines)
- account_management.py (246 lines)
- validators.py (32 lines)
- dependencies.py (23 lines)

Total: ~1600 lines (with some shared code improvements)
"""

from .students import router

__all__ = ["router"]
