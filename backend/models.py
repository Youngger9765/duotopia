"""
Backward compatibility layer for models.
All models have been refactored into models/ directory.

This file re-exports everything from the models package to maintain
backward compatibility with existing imports like:
    from models import Teacher, Student, ...
"""

# Re-export everything from the models package
from models import *

# Preserve the original __all__ for compatibility
__all__ = [
    # Base
    "Base",
    "UUID",
    "JSONType",
    # Enums
    "UserRole",
    "ProgramLevel",
    "AssignmentStatus",
    "TransactionType",
    "TransactionStatus",
    "ContentType",
    # Users
    "Teacher",
    "Student",
    # Subscriptions
    "SubscriptionPeriod",
    "PointUsageLog",
    "TeacherSubscriptionTransaction",
    "InvoiceStatusHistory",
    # Organizations
    "Organization",
    "School",
    "TeacherOrganization",
    "TeacherSchool",
    "ClassroomSchool",
    # Classrooms
    "Classroom",
    "ClassroomStudent",
    # Programs
    "Program",
    "Lesson",
    "Content",
    "ContentItem",
    # Assignments
    "Assignment",
    "AssignmentContent",
    "StudentAssignment",
    # Progress
    "StudentContentProgress",
    "StudentItemProgress",
]
