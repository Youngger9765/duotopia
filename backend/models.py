"""
Duotopia 資料模型
Phase 1: 個體教師版本
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON, Date, Enum, Float
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
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"
    RETURNED = "RETURNED"

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
    
    def __repr__(self):
        return f"<Teacher {self.name} ({self.email})>"

class Student(Base):
    """學生模型"""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    student_id = Column(String(50))  # 學號（選填）
    email = Column(String(255), unique=True, index=True)  # 系統生成
    password_hash = Column(String(255), nullable=False)  # 密碼雜湊
    birthdate = Column(Date, nullable=False)  # 生日（預設密碼來源）
    password_changed = Column(Boolean, default=False)  # 是否已更改密碼
    parent_email = Column(String(255))  # Phase 2
    parent_phone = Column(String(20))   # Phase 2
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
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )

# ============ 課程系統（三層架構）============
class Program(Base):
    """課程計畫（最上層）- 在特定班級內創建"""
    __tablename__ = "programs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    level = Column(Enum(ProgramLevel), default=ProgramLevel.A1)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)  # 課程歸屬班級
    estimated_hours = Column(Integer)  # 預計時數
    order_index = Column(Integer, default=1)  # 排序順序
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("Teacher", back_populates="programs")
    classroom = relationship("Classroom", back_populates="programs")
    lessons = relationship("Lesson", back_populates="program", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Program {self.name}>"

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
class StudentAssignment(Base):
    """學生作業"""
    __tablename__ = "student_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    instructions = Column(Text)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.NOT_STARTED)
    
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    graded_at = Column(DateTime(timezone=True))
    
    # 成績
    score = Column(Float)
    feedback = Column(Text)
    
    # Relationships
    student = relationship("Student", back_populates="assignments")
    content = relationship("Content", back_populates="assignments")
    submission = relationship("AssignmentSubmission", back_populates="assignment", uselist=False)
    
    def __repr__(self):
        return f"<Assignment {self.title} for {self.student_id}>"

class AssignmentSubmission(Base):
    """作業提交記錄"""
    __tablename__ = "assignment_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("student_assignments.id"), nullable=False)
    
    # 提交內容（根據作業類型不同）
    submission_data = Column(JSON)  # 儲存錄音URL、答案等
    
    # AI 評分結果
    ai_scores = Column(JSON)  # {"wpm": 85, "accuracy": 0.92, "fluency": 0.88, ...}
    ai_feedback = Column(Text)
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assignment = relationship("StudentAssignment", back_populates="submission")
    
    def __repr__(self):
        return f"<Submission for Assignment {self.assignment_id}>"