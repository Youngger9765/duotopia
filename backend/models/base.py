"""
Base models and common types for Duotopia
"""

from sqlalchemy import (
    String,
    JSON,
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID, JSONB
from database import Base
import enum
import uuid


# ============ SQLite Compatible UUID Type ============
class UUID(TypeDecorator):
    """
    Cross-database UUID type
    - PostgreSQL: Uses native UUID
    - SQLite: Uses CHAR(36) to store string format
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


# ============ SQLite Compatible JSONB Type ============
class JSONType(TypeDecorator):
    """
    Cross-database JSON type
    - PostgreSQL: Uses JSONB
    - SQLite: Uses JSON
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


# ============ Enums ============
class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"


class ProgramLevel(str, enum.Enum):
    PRE_A = "preA"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class AssignmentStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"  # 未開始
    IN_PROGRESS = "IN_PROGRESS"  # 進行中
    SUBMITTED = "SUBMITTED"  # 已提交（待批改）
    GRADED = "GRADED"  # 已批改（完成）
    RETURNED = "RETURNED"  # 退回訂正
    RESUBMITTED = "RESUBMITTED"  # 重新提交（訂正後待批改）


class TransactionType(str, enum.Enum):
    TRIAL = "TRIAL"  # 試用期啟動
    RECHARGE = "RECHARGE"  # 充值
    EXPIRED = "EXPIRED"  # 到期
    REFUND = "REFUND"  # 退款


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"  # 處理中
    SUCCESS = "SUCCESS"  # 成功
    FAILED = "FAILED"  # 失敗


class ContentType(str, enum.Enum):
    # ===== Phase 1 - 已啟用 =====
    READING_ASSESSMENT = "reading_assessment"  # Legacy name (kept for backward compatibility)
    EXAMPLE_SENTENCES = "example_sentences"  # 例句集 (new name for reading_assessment)
    VOCABULARY_SET = "vocabulary_set"  # 單字集
    SINGLE_CHOICE_QUIZ = "single_choice_quiz"  # 單選題庫
    SCENARIO_DIALOGUE = "scenario_dialogue"  # 情境對話

    # ===== Phase 2 - 未來擴展 =====
    # SPEAKING_PRACTICE = "speaking_practice"
    # LISTENING_CLOZE = "listening_cloze"
    # SENTENCE_MAKING = "sentence_making"  # Legacy - replaced by VOCABULARY_SET
    # SPEAKING_QUIZ = "speaking_quiz"
