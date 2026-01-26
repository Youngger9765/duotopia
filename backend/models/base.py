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


class AnswerMode(str, enum.Enum):
    LISTENING = "listening"  # 聽力模式作答
    WRITING = "writing"  # 寫作模式作答


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
<<<<<<< HEAD
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
=======
    # Phase 1 - 啟用
    EXAMPLE_SENTENCES = "EXAMPLE_SENTENCES"  # 例句集（原 READING_ASSESSMENT）

    # Phase 2 - 暫時禁用（UI 中不顯示）
    VOCABULARY_SET = "VOCABULARY_SET"  # 單字集（原 SENTENCE_MAKING）
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"  # 單選題庫
    SCENARIO_DIALOGUE = "SCENARIO_DIALOGUE"  # 情境對話

    # Legacy values - 保留向後相容性（deprecated，新資料不應使用）
    READING_ASSESSMENT = "READING_ASSESSMENT"  # @deprecated: use EXAMPLE_SENTENCES
    SENTENCE_MAKING = "SENTENCE_MAKING"  # @deprecated: use VOCABULARY_SET


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
>>>>>>> origin/staging
