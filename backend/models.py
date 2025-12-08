"""
Duotopia 資料模型
Phase 1: 個體教師版本
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    JSON,
    Date,
    Enum,
    Float,
    DECIMAL,
    Numeric,
    UniqueConstraint,
    Index,
    TypeDecorator,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from database import Base
import enum
import uuid


# ============ SQLite 兼容的 UUID 類型 ============
class UUID(TypeDecorator):
    """
    跨資料庫的 UUID 類型
    - PostgreSQL: 使用原生 UUID
    - SQLite: 使用 CHAR(36) 儲存字串格式
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


# ============ SQLite 兼容的 JSONB 類型 ============
class JSONType(TypeDecorator):
    """
    跨資料庫的 JSON 類型
    - PostgreSQL: 使用 JSONB
    - SQLite: 使用 JSON
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
    # Phase 2 擴展
    # SPEAKING_PRACTICE = "speaking_practice"
    # SPEAKING_SCENARIO = "speaking_scenario"
    # LISTENING_CLOZE = "listening_cloze"
    # SENTENCE_MAKING = "sentence_making"
    # SPEAKING_QUIZ = "speaking_quiz"


# ============ 使用者系統 ============
class SubscriptionPeriod(Base):
    """訂閱週期表 - 記錄每次付款的訂閱週期"""

    __tablename__ = "subscription_periods"
    __table_args__ = (
        Index("ix_subscription_periods_teacher_status", "teacher_id", "status"),
        Index("ix_subscription_periods_end_date", "end_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    # 訂閱資訊
    plan_name = Column(String, nullable=False)  # "Tutor Teachers" or "School Teachers"
    amount_paid = Column(Integer, nullable=False)  # 330 or 660
    quota_total = Column(Integer, nullable=False)  # 10000 or 25000 點
    quota_used = Column(Integer, default=0, nullable=False)

    # 時間範圍
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # 付款資訊
    payment_method = Column(String, nullable=False)  # "auto_renew" or "manual"
    payment_id = Column(String, nullable=True)  # TapPay rec_id
    payment_status = Column(
        String, default="paid", nullable=False
    )  # paid/pending/failed/refunded

    # 狀態
    status = Column(
        String, default="active", nullable=False
    )  # active/expired/cancelled
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_reason = Column(String, nullable=True)

    # Admin 操作記錄（結構化欄位 + JSONB metadata）
    admin_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    admin_reason = Column(Text, nullable=True)
    admin_metadata = Column(JSONType, nullable=True)  # 記錄完整操作歷史

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    teacher = relationship(
        "Teacher", foreign_keys=[teacher_id], back_populates="subscription_periods"
    )
    admin = relationship("Teacher", foreign_keys=[admin_id])
    usage_logs = relationship(
        "PointUsageLog",
        back_populates="subscription_period",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        start = self.start_date.date() if self.start_date else "None"
        end = self.end_date.date() if self.end_date else "None"
        return (
            f"<SubscriptionPeriod teacher={self.teacher_id} "
            f"period={start}-{end} method={self.payment_method}>"
        )


class PointUsageLog(Base):
    """點數使用記錄表 - 追蹤每一筆配額消耗"""

    __tablename__ = "point_usage_logs"
    __table_args__ = (
        Index("ix_point_usage_logs_teacher_id", "teacher_id"),
        Index("ix_point_usage_logs_period_id", "subscription_period_id"),
        Index("ix_point_usage_logs_created_at", "created_at"),
        Index("ix_point_usage_logs_feature_type", "feature_type"),
        Index("ix_point_usage_logs_teacher_created", "teacher_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # 關聯
    subscription_period_id = Column(
        Integer,
        ForeignKey("subscription_periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True
    )  # 哪個學生用的
    assignment_id = Column(Integer, nullable=True)  # 哪個作業

    # 功能資訊
    feature_type = Column(
        String, nullable=False
    )  # "speech_recording", "speech_assessment", "text_correction"
    feature_detail = Column(JSON)  # 詳細資訊 {"duration": 30, "file_url": "..."}

    # 點數消耗
    points_used = Column(Integer, nullable=False)  # 本次消耗點數
    quota_before = Column(Integer)  # 使用前配額
    quota_after = Column(Integer)  # 使用後配額

    # 單位資訊
    unit_count = Column(Float)  # 單位數量（30秒、500字）
    unit_type = Column(String)  # "秒", "字", "張"

    # 時間
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    teacher = relationship("Teacher", back_populates="point_usage_logs")
    student = relationship("Student")
    subscription_period = relationship(
        "SubscriptionPeriod", back_populates="usage_logs"
    )

    def __repr__(self):
        return (
            f"<PointUsageLog teacher={self.teacher_id} "
            f"student={self.student_id} feature={self.feature_type} "
            f"points={self.points_used}>"
        )


class Teacher(Base):
    """教師模型（個體戶）"""

    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)  # 標記 demo 帳號
    is_admin = Column(Boolean, default=False)  # Admin 權限

    # Email 驗證字段
    email_verified = Column(Boolean, default=False)  # email 是否已驗證
    email_verified_at = Column(DateTime(timezone=True))  # email 驗證時間
    email_verification_token = Column(String(100))  # email 驗證 token
    email_verification_sent_at = Column(DateTime(timezone=True))  # 最後發送驗證信時間

    # 密碼重設字段
    password_reset_token = Column(String(100))  # 密碼重設 token
    password_reset_sent_at = Column(DateTime(timezone=True))  # 最後發送密碼重設郵件時間
    password_reset_expires_at = Column(DateTime(timezone=True))  # token 過期時間

    # 新手上線字段 (Issue #61)
    onboarding_completed = Column(Boolean, default=False, nullable=False)  # 是否完成新手上線
    onboarding_started_at = Column(DateTime(timezone=True), nullable=True)  # 新手上線開始時間

    # 訂閱系統 - 新系統使用 subscription_periods 表
    # 移除舊欄位：subscription_type, subscription_status, subscription_start_date,
    #            subscription_end_date, subscription_renewed_at, monthly_message_limit,
    #            messages_used_this_month
    subscription_auto_renew = Column(Boolean, default=False)  # 是否自動續訂（全域偏好）
    subscription_cancelled_at = Column(DateTime(timezone=True), nullable=True)  # 取消續訂時間
    trial_start_date = Column(DateTime(timezone=True), nullable=True)  # 試用開始日
    trial_end_date = Column(DateTime(timezone=True), nullable=True)  # 試用結束日

    # TapPay 信用卡 Token（用於自動續訂扣款）
    card_key = Column(String(255), nullable=True)  # TapPay Card Key（永久有效）
    card_token = Column(String(255), nullable=True)  # TapPay Card Token（90天有效，每次交易更新）
    card_last_four = Column(String(4), nullable=True)  # 信用卡末四碼（顯示用）
    card_bin_code = Column(String(6), nullable=True)  # 信用卡 BIN Code
    card_type = Column(
        Integer, nullable=True
    )  # 卡別（1: VISA, 2: MasterCard, 3: JCB, 4: Union Pay, 5: AMEX）
    card_funding = Column(Integer, nullable=True)  # 卡種（0: 信用卡, 1: 金融卡, 2: 預付卡）
    card_issuer = Column(String(100), nullable=True)  # 發卡銀行
    card_country = Column(String(2), nullable=True)  # 發卡國家代碼
    card_saved_at = Column(DateTime(timezone=True), nullable=True)  # 卡片儲存時間

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    classrooms = relationship(
        "Classroom", back_populates="teacher", cascade="all, delete-orphan"
    )
    programs = relationship(
        "Program", back_populates="teacher", cascade="all, delete-orphan"
    )
    assignments = relationship("Assignment", back_populates="teacher")
    subscription_transactions = relationship(
        "TeacherSubscriptionTransaction",
        foreign_keys="TeacherSubscriptionTransaction.teacher_id",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    subscription_periods = relationship(
        "SubscriptionPeriod",
        foreign_keys="SubscriptionPeriod.teacher_id",
        back_populates="teacher",
        cascade="all, delete-orphan",
        order_by="SubscriptionPeriod.start_date.desc()",
    )
    point_usage_logs = relationship(
        "PointUsageLog",
        back_populates="teacher",
        cascade="all, delete-orphan",
        order_by="PointUsageLog.created_at.desc()",
    )

    @property
    def current_period(self):
        """取得當前有效的訂閱週期

        優化說明：
        - 使用 SQL query 而非 Python 循環（避免 N+1 query）
        - 利用 (teacher_id, status) 複合索引
        - 只查詢需要的欄位
        """
        # 從 session 取得當前 session（如果物件已 attached）
        session = Session.object_session(self)
        if not session:
            # Fallback: 使用原始方法（物件未 attached 時）
            for period in self.subscription_periods:
                if period.status == "active":
                    return period
            return None

        # 使用 SQL query（利用索引）
        stmt = (
            select(SubscriptionPeriod)
            .where(
                SubscriptionPeriod.teacher_id == self.id,
                SubscriptionPeriod.status == "active",
            )
            .order_by(SubscriptionPeriod.start_date.desc())  # 最新的 period 優先
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @property
    def quota_total(self) -> int:
        """當前週期的總配額"""
        period = self.current_period
        return period.quota_total if period else 0

    @property
    def quota_remaining(self) -> int:
        """當前週期的剩餘配額"""
        period = self.current_period
        if not period:
            return 0
        return max(0, period.quota_total - period.quota_used)

    @property
    def subscription_status(self):
        """獲取訂閱狀態 - 從 subscription_periods 計算"""
        period = self.current_period
        if not period:
            return "expired"

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # 確保 end_date 有 timezone
        end_date = period.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if end_date > now:
            return "subscribed"
        else:
            return "expired"

    @property
    def days_remaining(self):
        """獲取剩餘天數 - 從 subscription_periods 計算"""
        period = self.current_period
        if not period:
            return 0

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # 確保 end_date 有 timezone
        end_date = period.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if end_date > now:
            return (end_date - now).days
        else:
            return 0

    @property
    def subscription_end_date(self):
        """獲取訂閱結束日期 - 從 subscription_periods 計算"""
        period = self.current_period
        if not period:
            return None
        return period.end_date

    @property
    def can_assign_homework(self):
        """是否可以分派作業 - 檢查是否有有效的 subscription_period"""
        period = self.current_period
        if not period:
            return False

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # 確保 end_date 有 timezone
        end_date = period.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        return end_date > now

    def __repr__(self):
        return f"<Teacher {self.name} ({self.email})>"


class Student(Base):
    """學生模型"""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    student_number = Column(String(50))  # 學號（選填）
    email = Column(String(255), nullable=True, index=True)  # Email（可為空，可重複）
    password_hash = Column(String(255), nullable=False)  # 密碼雜湊
    birthdate = Column(Date, nullable=False)  # 生日（預設密碼來源）
    password_changed = Column(Boolean, default=False)  # 是否已更改密碼
    email_verified = Column(Boolean, default=False)  # email 是否已驗證
    email_verified_at = Column(DateTime(timezone=True))  # email 驗證時間
    email_verification_token = Column(String(100))  # email 驗證 token
    email_verification_sent_at = Column(DateTime(timezone=True))  # 最後發送驗證信時間
    parent_phone = Column(String(20))  # Phase 2
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))  # 最後登入時間

    # 學習目標設定
    target_wpm = Column(Integer, default=80)  # 目標每分鐘字數
    target_accuracy = Column(Float, default=0.8)  # 目標準確率

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    classroom_enrollments = relationship("ClassroomStudent", back_populates="student")
    assignments = relationship("StudentAssignment", back_populates="student")

    def get_default_password(self):
        """取得預設密碼（生日格式：YYYYMMDD）"""
        if self.birthdate:
            return self.birthdate.strftime("%Y%m%d")
        return None

    def __repr__(self):
        return f"<Student {self.name}>"


# ============ 班級管理 ============
class Classroom(Base):
    """班級模型（注意：使用 Classroom 避免與 Python 保留字衝突）"""

    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    level = Column(Enum(ProgramLevel), default=ProgramLevel.A1)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    school = Column(String(255), nullable=True)  # 學校名稱（與 DB 一致，但不使用）
    grade = Column(String(50), nullable=True)  # 年級（與 DB 一致，但不使用）
    academic_year = Column(String(20), nullable=True)  # 學年度（與 DB 一致，但不使用）
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("Teacher", back_populates="classrooms")
    students = relationship(
        "ClassroomStudent", back_populates="classroom", cascade="all, delete-orphan"
    )
    programs = relationship(
        "Program", back_populates="classroom", cascade="all, delete-orphan"
    )  # 直接關聯課程
    assignments = relationship(
        "Assignment", back_populates="classroom", cascade="all, delete-orphan"
    )

    # 移除 program_mappings，因為 Program 已直接關聯到 Classroom

    def __repr__(self):
        return f"<Classroom {self.name}>"


class ClassroomStudent(Base):
    """班級學生關聯表"""

    __tablename__ = "classroom_students"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="students")
    student = relationship("Student", back_populates="classroom_enrollments")

    # Unique constraint
    __table_args__ = ({"mysql_engine": "InnoDB"},)


# ============ 課程系統（三層架構）============
class Program(Base):
    """課程計畫 - 公版模板或班級課程"""

    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    level = Column(Enum(ProgramLevel), default=ProgramLevel.A1)

    # 類型與歸屬
    is_template = Column(
        Boolean, default=False, nullable=False
    )  # True=公版模板, False=班級課程
    classroom_id = Column(
        Integer, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=True
    )  # 公版課程為 NULL
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    # 來源追蹤
    source_type = Column(
        String(20), nullable=True
    )  # 'template', 'classroom', 'custom', None
    source_metadata = Column(JSON, nullable=True)
    """
    範例：
    - 從公版複製: {"template_id": 123, "template_name": "初級會話"}
    - 從其他班級: {"classroom_id": 456, "classroom_name": "五年級B班", "program_id": 789}
    - 自建: {"created_by": "manual"}
    """

    # 課程屬性
    is_public = Column(Boolean, nullable=True)  # 是否公開（與 DB 一致，但不使用）
    estimated_hours = Column(Integer)  # 預計時數
    order_index = Column(Integer, default=1)  # 排序順序
    tags = Column(JSON, nullable=True)  # 標籤

    # 軟刪除
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("Teacher", back_populates="programs")
    classroom = relationship("Classroom", back_populates="programs")
    lessons = relationship(
        "Lesson",
        back_populates="program",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )

    @property
    def is_public_template(self):
        """判斷是否為公版模板"""
        return self.is_template and self.classroom_id is None

    @property
    def is_classroom_program(self):
        """判斷是否為班級課程"""
        return not self.is_template and self.classroom_id is not None

    def __repr__(self):
        type_str = "Template" if self.is_template else f"Class {self.classroom_id}"
        return f"<Program {self.name} ({type_str})>"


class Lesson(Base):
    """課程單元（中層）"""

    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)  # 排序
    estimated_minutes = Column(Integer)  # 預計分鐘數
    is_active = Column(Boolean, default=True)  # 軟刪除標記

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    program = relationship("Program", back_populates="lessons")
    contents = relationship(
        "Content",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="Content.order_index",
    )

    def __repr__(self):
        return f"<Lesson {self.name}>"


# (重複定義已刪除)


class Content(Base):
    """課程內容（底層 - Phase 1 只有朗讀錄音集）"""

    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    type = Column(Enum(ContentType), default=ContentType.READING_ASSESSMENT)
    title = Column(String(200), nullable=False)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)  # 軟刪除標記

    # 注意：items 欄位已移除，改用 ContentItem 關聯表
    # items = Column(JSON) # DEPRECATED - 使用 content_items 關聯

    # 設定
    target_wpm = Column(Integer)  # 目標 WPM
    target_accuracy = Column(Float)  # 目標準確率
    time_limit_seconds = Column(Integer)  # 時間限制

    # 新增欄位
    level = Column(String(10), default="A1")  # 等級 (PreA, A1, A2, B1, B2, C1, C2)
    tags = Column(JSON, default=list)  # 標籤列表
    is_public = Column(Boolean, default=False)  # 是否公開（給其他老師使用）

    # 作業副本機制欄位
    is_assignment_copy = Column(
        Boolean, nullable=False, server_default=text("false"), default=False, index=True
    )  # 標記是否為作業副本
    source_content_id = Column(
        Integer, ForeignKey("contents.id"), nullable=True, index=True
    )  # 原始內容 ID（如果是副本）

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson", back_populates="contents")
    content_items = relationship(
        "ContentItem", back_populates="content", cascade="all, delete-orphan"
    )
    source_content = relationship(
        "Content", remote_side=[id], foreign_keys=[source_content_id]
    )  # 原始內容（如果是副本）

    def __repr__(self):
        return f"<Content {self.title}>"


# ============ 作業系統 ============
class Assignment(Base):
    """作業主表 - 教師建立的作業任務"""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 指派設定
    # 移除 assign_to_all，改為透過 StudentAssignment 記錄實際指派的學生

    # 軟刪除標記
    is_active = Column(Boolean, default=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="assignments")
    teacher = relationship("Teacher", back_populates="assignments")
    contents = relationship(
        "AssignmentContent", back_populates="assignment", cascade="all, delete-orphan"
    )
    student_assignments = relationship(
        "StudentAssignment", back_populates="assignment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Assignment {self.title} in Classroom {self.classroom_id}>"


class AssignmentContent(Base):
    """作業-內容關聯表 - 一個作業可包含多個內容"""

    __tablename__ = "assignment_contents"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    order_index = Column(Integer, default=0)  # 內容順序

    # Relationships
    assignment = relationship("Assignment", back_populates="contents")
    content = relationship("Content")

    # Constraints - 確保同一作業不會重複包含相同內容
    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "content_id", name="unique_assignment_content"
        ),
        Index(
            "ix_assignment_content_assignment_order", "assignment_id", "order_index"
        ),  # 優化查詢排序
    )

    def __repr__(self):
        return f"<AssignmentContent assignment={self.assignment_id} content={self.content_id}>"


class StudentAssignment(Base):
    """學生作業實例 - 每個學生對應作業的記錄"""

    __tablename__ = "student_assignments"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(
        Integer, ForeignKey("assignments.id"), nullable=True
    )  # nullable 暫時為 True 以兼容舊資料
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    # TODO: Phase 2 - 移除以下舊欄位（等資料遷移完成）
    # 這些欄位應該從 Assignment 取得，不需要重複儲存
    classroom_id = Column(
        Integer, ForeignKey("classrooms.id"), nullable=False
    )  # 可從 assignment.classroom_id 取得
    title = Column(String(200), nullable=False)  # 可從 assignment.title 取得
    instructions = Column(Text)  # 可從 assignment.description 取得
    due_date = Column(DateTime(timezone=True))  # 可從 assignment.due_date 取得

    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.NOT_STARTED)

    # 時間記錄
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))  # 首次開始時間
    submitted_at = Column(DateTime(timezone=True))  # 全部完成時間
    graded_at = Column(DateTime(timezone=True))  # 批改完成時間
    returned_at = Column(DateTime(timezone=True))  # 🔥 退回訂正時間
    resubmitted_at = Column(DateTime(timezone=True))  # 🔥 重新提交時間

    # 成績與回饋
    score = Column(Float, nullable=True)  # 總分（選填，保留但不強制使用）
    feedback = Column(Text)  # 總評

    # 軟刪除標記
    is_active = Column(Boolean, default=True)

    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assignment = relationship("Assignment", back_populates="student_assignments")
    student = relationship("Student", back_populates="assignments")
    content_progress = relationship(
        "StudentContentProgress",
        back_populates="student_assignment",
        cascade="all, delete-orphan",
    )
    item_progress = relationship(
        "StudentItemProgress",
        back_populates="student_assignment",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Assignment {self.title} for {self.student_id}>"


class StudentContentProgress(Base):
    """學生-內容進度表 - 追蹤學生對每個內容的完成狀況"""

    __tablename__ = "student_content_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_assignment_id = Column(
        Integer, ForeignKey("student_assignments.id"), nullable=False
    )
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)

    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.NOT_STARTED)
    score = Column(Float, nullable=True)  # 該內容的分數（選填，保留但不強制）

    # 順序與鎖定（支援順序學習）
    order_index = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)  # 是否需要解鎖（Phase 2）

    # 批改相關
    checked = Column(Boolean, nullable=True)  # True=通過, False=未通過, None=未批改
    feedback = Column(Text)  # 該內容的個別回饋

    # 學生回答/提交內容
    response_data = Column(JSON)  # 儲存錄音URL、答案等

    # AI 評分結果
    ai_scores = Column(JSON)  # {"wpm": 85, "accuracy": 0.92, ...}
    ai_feedback = Column(Text)

    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    student_assignment = relationship(
        "StudentAssignment", back_populates="content_progress"
    )
    content = relationship("Content")

    # Constraints - 優化查詢性能
    __table_args__ = (
        Index(
            "ix_student_content_progress_assignment_order",
            "student_assignment_id",
            "order_index",
        ),  # 優化查詢排序
    )

    def __repr__(self):
        return (
            f"<Progress student_assignment={self.student_assignment_id} "
            f"content={self.content_id}>"
        )


# AssignmentSubmission 已移除 - 新架構使用 StudentContentProgress 記錄提交內容


# ============ New Item-based Models (Phase 2) ============


class ContentItem(Base):
    """Individual question/item within a Content"""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False
    )
    order_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    translation = Column(Text)
    audio_url = Column(Text)  # Example audio file
    item_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    content = relationship("Content", back_populates="content_items")
    student_progress = relationship(
        "StudentItemProgress",
        back_populates="content_item",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("content_id", "order_index", name="_content_item_order_uc"),
    )

    def __repr__(self):
        return (
            f"<ContentItem(id={self.id}, content_id={self.content_id}, "
            f"order={self.order_index}, text='{self.text[:30]}...')>"
        )


class StudentItemProgress(Base):
    """Track individual item progress for each student"""

    __tablename__ = "student_item_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_assignment_id = Column(
        Integer,
        ForeignKey("student_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_item_id = Column(
        Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False
    )

    # Recording data
    recording_url = Column(Text)
    answer_text = Column(Text)
    transcription = Column(Text)  # AI 轉錄文字（與 DB 一致）
    submitted_at = Column(DateTime(timezone=True))

    # AI Assessment (flattened structure for better querying)
    accuracy_score = Column(DECIMAL(5, 2))
    fluency_score = Column(DECIMAL(5, 2))
    pronunciation_score = Column(DECIMAL(5, 2))
    completeness_score = Column(DECIMAL(5, 2))
    ai_feedback = Column(Text)
    ai_assessed_at = Column(DateTime(timezone=True))

    # Teacher Review Fields (新增老師批改功能)
    teacher_review_score = Column(DECIMAL(5, 2))  # 老師評分 (0-100)
    teacher_feedback = Column(Text)  # 老師文字回饋
    teacher_passed = Column(Boolean)  # 老師判定是否通過 (True/False/None)
    teacher_reviewed_at = Column(DateTime(timezone=True))  # 批改時間
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"))  # 批改老師
    review_status = Column(String(20), default="PENDING")  # PENDING, REVIEWED

    # Status tracking
    status = Column(
        String(20), default="NOT_STARTED"
    )  # NOT_STARTED, IN_PROGRESS, COMPLETED, SUBMITTED
    attempts = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    student_assignment = relationship(
        "StudentAssignment", back_populates="item_progress"
    )
    content_item = relationship("ContentItem", back_populates="student_progress")
    teacher = relationship("Teacher", foreign_keys=[teacher_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "student_assignment_id", "content_item_id", name="_student_item_progress_uc"
        ),
        Index("ix_student_item_progress_assignment", "student_assignment_id"),  # 優化查詢性能
    )

    @property
    def overall_score(self):
        """Calculate overall score from all components"""
        scores = [
            s
            for s in [
                self.accuracy_score,
                self.fluency_score,
                self.pronunciation_score,
                self.completeness_score,
            ]
            if s is not None
        ]
        return sum(scores) / len(scores) if scores else None

    @property
    def is_completed(self):
        """Check if this item is completed"""
        return self.status == "COMPLETED"

    @property
    def has_teacher_review(self):
        """Check if teacher has reviewed this item"""
        return (
            self.review_status == "REVIEWED" and self.teacher_review_score is not None
        )

    @property
    def final_score(self):
        """Get final score (teacher review if available, otherwise AI score)"""
        if self.has_teacher_review:
            return float(self.teacher_review_score)
        return self.overall_score

    @property
    def has_recording(self):
        """Check if recording exists"""
        return self.recording_url is not None and self.recording_url != ""

    @property
    def has_ai_assessment(self):
        """Check if AI assessment exists"""
        # 使用 ai_assessed_at 判斷是否有 AI 評估，因為分數可能為 0
        return self.ai_assessed_at is not None

    def __repr__(self):
        return (
            f"<StudentItemProgress(id={self.id}, "
            f"assignment={self.student_assignment_id}, "
            f"item={self.content_item_id}, status={self.status})>"
        )


# ============ 訂閱交易系統 ============
class TeacherSubscriptionTransaction(Base):
    """教師訂閱交易記錄 - 支援多種支付方式的完整金流記錄"""

    __tablename__ = "teacher_subscription_transactions"

    # 基本欄位
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    # 1. 用戶識別
    teacher_email = Column(String(255), nullable=True, index=True)  # 直接儲存教師 email

    # 2. 交易基本資訊
    transaction_type = Column(Enum(TransactionType), nullable=False)
    subscription_type = Column(String, nullable=True)  # 訂閱類型
    amount = Column(Numeric(10, 2), nullable=True)  # 充值金額（可為空，如試用期）
    currency = Column(String(3), nullable=True, default="TWD")  # 貨幣
    status = Column(String, nullable=False, default="PENDING", index=True)  # 交易狀態
    months = Column(Integer, nullable=False)  # 訂閱月數

    # 3. 時間相關
    period_start = Column(DateTime(timezone=True), nullable=True)  # 訂閱期間開始
    period_end = Column(DateTime(timezone=True), nullable=True)  # 訂閱期間結束
    previous_end_date = Column(DateTime(timezone=True), nullable=True)  # 交易前的到期日
    new_end_date = Column(DateTime(timezone=True), nullable=False)  # 交易後的到期日
    processed_at = Column(DateTime(timezone=True), nullable=True)  # 實際處理時間
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 過期時間（PENDING 狀態用）

    # 4. 防重複扣款
    idempotency_key = Column(
        String(255), nullable=True, unique=True, index=True
    )  # 防重複扣款
    retry_count = Column(Integer, nullable=False, default=0)  # 重試次數

    # 5. 稽核追蹤
    ip_address = Column(String(45), nullable=True)  # 支援 IPv6
    user_agent = Column(Text, nullable=True)  # 瀏覽器/裝置資訊
    request_id = Column(String(255), nullable=True)  # API 請求 ID

    # 6. 支付詳情
    payment_provider = Column(
        String(50), nullable=True, index=True
    )  # tappay/line_pay/paypal
    payment_method = Column(
        String(50), nullable=True
    )  # credit_card/bank_transfer/e_wallet
    external_transaction_id = Column(String(255), nullable=True, index=True)  # 外部交易 ID

    # 7. 錯誤處理
    failure_reason = Column(Text, nullable=True)  # 失敗原因
    error_code = Column(String(50), nullable=True)  # 錯誤代碼
    gateway_response = Column(JSON, nullable=True)  # 金流商完整回應

    # 8. 退款相關
    refunded_amount = Column(Integer, nullable=True, default=0)  # 已退款金額（TWD 分）
    refund_status = Column(String(20), nullable=True)  # 退款狀態
    refund_amount = Column(Integer, nullable=True)  # 本次退款金額（TWD 元）
    refund_reason = Column(Text, nullable=True)  # 退款原因
    refund_notes = Column(Text, nullable=True)  # 退款備註
    refund_initiated_by = Column(
        Integer, ForeignKey("teachers.id"), nullable=True
    )  # 退款操作者
    refund_initiated_at = Column(DateTime(timezone=True), nullable=True)  # 退款發起時間
    original_transaction_id = Column(
        Integer, ForeignKey("teacher_subscription_transactions.id"), nullable=True
    )  # 原始交易（退款時參照）

    # 9. TapPay 電子發票欄位
    rec_invoice_id = Column(String(30), nullable=True, index=True)  # TapPay 發票 ID
    invoice_number = Column(String(10), nullable=True, index=True)  # 發票號碼
    invoice_status = Column(
        String(20), nullable=True, default="PENDING", index=True
    )  # 發票狀態
    invoice_issued_at = Column(DateTime(timezone=True), nullable=True)  # 發票開立時間
    buyer_tax_id = Column(String(8), nullable=True)  # 統一編號
    buyer_name = Column(String(100), nullable=True)  # 買受人名稱
    buyer_email = Column(String(255), nullable=True)  # 買受人 email
    carrier_type = Column(String(10), nullable=True)  # 載具類型
    carrier_id = Column(String(64), nullable=True)  # 載具號碼
    invoice_response = Column(JSON, nullable=True)  # 發票 API 完整回應

    # 10. 其他
    webhook_status = Column(String(20), nullable=True)  # Webhook 通知狀態
    transaction_metadata = Column("metadata", JSON, nullable=True)  # 額外資料（向後相容）
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )  # 更新時間（與 DB 一致）

    # 關聯
    teacher = relationship(
        "Teacher", foreign_keys=[teacher_id], back_populates="subscription_transactions"
    )

    def __repr__(self):
        return (
            f"<TeacherSubscriptionTransaction({self.teacher_id}, "
            f"{self.transaction_type}, {self.months}個月)>"
        )


class InvoiceStatusHistory(Base):
    """發票狀態變更歷史 - 追蹤發票生命週期與 Notify 事件"""

    __tablename__ = "invoice_status_history"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        Integer,
        ForeignKey("teacher_subscription_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 狀態轉換
    from_status = Column(String(20), nullable=True)  # 原狀態
    to_status = Column(String(20), nullable=False)  # 新狀態
    action_type = Column(
        String(20), nullable=False
    )  # ISSUE/VOID/ALLOWANCE/REISSUE/NOTIFY
    reason = Column(Text, nullable=True)  # 變更原因

    # Notify 事件相關
    is_notify = Column(Boolean, nullable=False, default=False)  # 是否為 Notify 觸發
    notify_error_code = Column(String(20), nullable=True)  # Notify 錯誤代碼
    notify_error_msg = Column(Text, nullable=True)  # Notify 錯誤訊息

    # 完整 API 記錄
    request_payload = Column(JSON, nullable=True)  # 請求資料
    response_payload = Column(JSON, nullable=True)  # 回應資料

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self):
        return (
            f"<InvoiceStatusHistory({self.transaction_id}, "
            f"{self.from_status}->{self.to_status}, {self.action_type})>"
        )
