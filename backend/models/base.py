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
    READING_ASSESSMENT = "reading_assessment"  # Phase 1 只有這個
    EXAMPLE_SENTENCES = "EXAMPLE_SENTENCES"  # 例句集（新名稱）
    VOCABULARY_SET = "VOCABULARY_SET"  # 單字集（Phase 2）
    # Phase 2 擴展
    # SPEAKING_PRACTICE = "speaking_practice"
    # SPEAKING_SCENARIO = "speaking_scenario"
    # LISTENING_CLOZE = "listening_cloze"
    # SENTENCE_MAKING = "sentence_making"
    # SPEAKING_QUIZ = "speaking_quiz"


class PracticeMode(str, enum.Enum):
    """作答模式"""

    # 例句集 (EXAMPLE_SENTENCES)
    READING = "reading"  # 例句朗讀 -> 口說分類
    REARRANGEMENT = "rearrangement"  # 例句重組 -> 聽力/寫作分類

    # 單字集 (VOCABULARY_SET) - Phase 2
    WORD_READING = "word_reading"  # 單字朗讀 -> 口說分類
    WORD_SELECTION = "word_selection"  # 單字選擇 -> 艾賓浩斯記憶曲線


class ScoreCategory(str, enum.Enum):
    """分數記錄分類"""

    SPEAKING = "speaking"  # 口說
    LISTENING = "listening"  # 聽力
    WRITING = "writing"  # 寫作
    VOCABULARY = "vocabulary"  # 單字（Phase 2 新增）
