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
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


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


class ContentType(str, enum.Enum):
    READING_ASSESSMENT = "reading_assessment"  # Phase 1 只有這個
    # Phase 2 擴展
    # SPEAKING_PRACTICE = "speaking_practice"
    # SPEAKING_SCENARIO = "speaking_scenario"
    # LISTENING_CLOZE = "listening_cloze"
    # SENTENCE_MAKING = "sentence_making"
    # SPEAKING_QUIZ = "speaking_quiz"


# ============ 使用者系統 ============
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    classrooms = relationship("Classroom", back_populates="teacher", cascade="all, delete-orphan")
    programs = relationship("Program", back_populates="teacher", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher {self.name} ({self.email})>"


class Student(Base):
    """學生模型"""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    student_id = Column(String(50))  # 學號（選填）
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
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("Teacher", back_populates="classrooms")
    students = relationship("ClassroomStudent", back_populates="classroom", cascade="all, delete-orphan")
    programs = relationship("Program", back_populates="classroom", cascade="all, delete-orphan")  # 直接關聯課程
    assignments = relationship("Assignment", back_populates="classroom", cascade="all, delete-orphan")

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
    is_template = Column(Boolean, default=False, nullable=False)  # True=公版模板, False=班級課程
    classroom_id = Column(Integer, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=True)  # 公版課程為 NULL
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    # 來源追蹤
    source_type = Column(String(20), nullable=True)  # 'template', 'classroom', 'custom', None
    source_metadata = Column(JSON, nullable=True)
    """
    範例：
    - 從公版複製: {"template_id": 123, "template_name": "初級會話"}
    - 從其他班級: {"classroom_id": 456, "classroom_name": "五年級B班", "program_id": 789}
    - 自建: {"created_by": "manual"}
    """

    # 課程屬性
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
    lessons = relationship("Lesson", back_populates="program", cascade="all, delete-orphan")

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
    contents = relationship("Content", back_populates="lesson", cascade="all, delete-orphan")

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

    # 朗讀錄音集資料（3-15個項目）
    items = Column(JSON)  # [{"text": "Hello", "translation": "你好", "audio_url": "..."}, ...]

    # 設定
    target_wpm = Column(Integer)  # 目標 WPM
    target_accuracy = Column(Float)  # 目標準確率
    time_limit_seconds = Column(Integer)  # 時間限制

    # 新增欄位
    level = Column(String(10), default="A1")  # 等級 (PreA, A1, A2, B1, B2, C1, C2)
    tags = Column(JSON, default=list)  # 標籤列表
    is_public = Column(Boolean, default=False)  # 是否公開（給其他老師使用）

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson", back_populates="contents")
    assignments = relationship("StudentAssignment", back_populates="content")

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
    contents = relationship("AssignmentContent", back_populates="assignment", cascade="all, delete-orphan")
    student_assignments = relationship("StudentAssignment", back_populates="assignment", cascade="all, delete-orphan")

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

    def __repr__(self):
        return f"<AssignmentContent assignment={self.assignment_id} content={self.content_id}>"


class StudentAssignment(Base):
    """學生作業實例 - 每個學生對應作業的記錄"""

    __tablename__ = "student_assignments"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)  # nullable 暫時為 True 以兼容舊資料
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    # TODO: Phase 2 - 移除以下舊欄位（等資料遷移完成）
    # 這些欄位應該從 Assignment 取得，不需要重複儲存
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True)  # 舊架構，待移除
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)  # 可從 assignment.classroom_id 取得
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
    content = relationship("Content", back_populates="assignments")  # 保留以兼容舊資料
    content_progress = relationship(
        "StudentContentProgress",
        back_populates="student_assignment",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Assignment {self.title} for {self.student_id}>"


class StudentContentProgress(Base):
    """學生-內容進度表 - 追蹤學生對每個內容的完成狀況"""

    __tablename__ = "student_content_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_assignment_id = Column(Integer, ForeignKey("student_assignments.id"), nullable=False)
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
    student_assignment = relationship("StudentAssignment", back_populates="content_progress")
    content = relationship("Content")

    def __repr__(self):
        return f"<Progress student_assignment={self.student_assignment_id} content={self.content_id}>"


# AssignmentSubmission 已移除 - 新架構使用 StudentContentProgress 記錄提交內容
