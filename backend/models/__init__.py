"""
Database models package.
All models are re-exported here for backward compatibility.
"""

# Base types and enums
from .base import (
    Base,
    UUID,
    JSONType,
    UserRole,
    ProgramLevel,
    AssignmentStatus,
    AnswerMode,
    TransactionType,
    TransactionStatus,
    ContentType,
    PracticeMode,
    ScoreCategory,
)

# User models
from .user import Teacher, Student

# Subscription models
from .subscription import (
    SubscriptionPeriod,
    PointUsageLog,
    TeacherSubscriptionTransaction,
    InvoiceStatusHistory,
)

# Organization models
from .organization import (
    Organization,
    OrganizationPointsLog,
    School,
    TeacherOrganization,
    TeacherSchool,
    ClassroomSchool,
    StudentSchool,
)

# Classroom models
from .classroom import Classroom, ClassroomStudent

# Program models
from .program import Program, Lesson, Content, ContentItem

# Assignment models
from .assignment import Assignment, AssignmentContent, StudentAssignment

# Progress models
from .progress import (
    StudentContentProgress,
    StudentItemProgress,
    PracticeSession,
    PracticeAnswer,
)

__all__ = [
    # Base
    "Base",
    "UUID",
    "JSONType",
    # Enums
    "UserRole",
    "ProgramLevel",
    "AssignmentStatus",
    "AnswerMode",
    "TransactionType",
    "TransactionStatus",
    "ContentType",
    "PracticeMode",
    "ScoreCategory",
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
    "StudentSchool",
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
    "PracticeSession",
    "PracticeAnswer",
]
