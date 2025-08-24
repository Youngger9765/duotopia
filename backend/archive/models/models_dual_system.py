"""
完整的雙體系模型
這是獨立的模型文件，不影響現有系統
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, JSON, Enum
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum
import uuid

# 使用獨立的 Base，避免與現有系統衝突
DualBase = declarative_base()


# ===== 列舉 =====
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class DifficultyLevel(str, enum.Enum):
    PRE_A = "preA"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class ActivityType(str, enum.Enum):
    READING_ASSESSMENT = "reading_assessment"
    SPEAKING_PRACTICE = "speaking_practice"
    LISTENING_CLOZE = "listening_cloze"
    SENTENCE_MAKING = "sentence_making"
    SPEAKING_QUIZ = "speaking_quiz"


# ===== 用戶模型 =====
class DualUser(DualBase):
    """雙體系用戶模型"""
    __tablename__ = "dual_users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    phone = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # 多重角色支援
    is_individual_teacher = Column(Boolean, default=False)
    is_institutional_admin = Column(Boolean, default=False)
    current_role_context = Column(String, default="default")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 關聯
    individual_classrooms = relationship("IndividualClassroom", back_populates="teacher")
    individual_courses = relationship("IndividualCourse", back_populates="teacher")
    
    @property
    def has_multiple_roles(self):
        return self.is_individual_teacher and self.is_institutional_admin
    
    @property
    def effective_role(self):
        if self.current_role_context == "individual" and self.is_individual_teacher:
            return UserRole.TEACHER
        elif self.current_role_context == "institutional" and self.is_institutional_admin:
            return UserRole.ADMIN
        return self.role


# ===== 學校模型 =====
class DualSchool(DualBase):
    """雙體系學校模型"""
    __tablename__ = "dual_schools"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    address = Column(String)
    phone = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    inst_classrooms = relationship("InstitutionalClassroom", back_populates="school")
    inst_students = relationship("InstitutionalStudent", back_populates="school")
    inst_courses = relationship("InstitutionalCourse", back_populates="school")


# ===== 教室基礎類別 =====
class ClassroomBase(DualBase):
    """教室基礎類別"""
    __tablename__ = "dual_classroom_base"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    grade_level = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 多型欄位
    type = Column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': type
    }


class InstitutionalClassroom(ClassroomBase):
    """機構教室"""
    __tablename__ = "dual_institutional_classrooms"
    
    id = Column(String, ForeignKey("dual_classroom_base.id"), primary_key=True)
    school_id = Column(String, ForeignKey("dual_schools.id"), nullable=False)
    room_number = Column(String)
    capacity = Column(Integer, default=30)
    
    # 關聯
    school = relationship("DualSchool", back_populates="inst_classrooms")
    enrollments = relationship("InstitutionalEnrollment", back_populates="classroom")
    
    __mapper_args__ = {
        'polymorphic_identity': 'institutional'
    }
    
    @validates('school_id')
    def validate_school_id(self, key, value):
        if not value:
            raise ValueError("機構教室必須指定學校")
        return value


class IndividualClassroom(ClassroomBase):
    """個體戶教室"""
    __tablename__ = "dual_individual_classrooms"
    
    id = Column(String, ForeignKey("dual_classroom_base.id"), primary_key=True)
    teacher_id = Column(String, ForeignKey("dual_users.id"), nullable=False)
    location = Column(String)
    pricing = Column(Integer)
    max_students = Column(Integer, default=10)
    
    # 關聯
    teacher = relationship("DualUser", back_populates="individual_classrooms")
    enrollments = relationship("IndividualEnrollment", back_populates="classroom")
    
    __mapper_args__ = {
        'polymorphic_identity': 'individual'
    }
    
    @validates('teacher_id')
    def validate_teacher_id(self, key, value):
        if not value:
            raise ValueError("個體戶教室必須指定教師")
        return value


# ===== 學生基礎類別 =====
class StudentBase(DualBase):
    """學生基礎類別"""
    __tablename__ = "dual_student_base"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)  # 移除唯一性約束，改為可選
    birth_date = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 多型欄位
    type = Column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': type
    }


class InstitutionalStudent(StudentBase):
    """機構學生"""
    __tablename__ = "dual_institutional_students"
    
    id = Column(String, ForeignKey("dual_student_base.id"), primary_key=True)
    school_id = Column(String, ForeignKey("dual_schools.id"), nullable=False)
    student_id = Column(String, unique=True)
    parent_phone = Column(String)
    emergency_contact = Column(String)
    
    # 關聯
    school = relationship("DualSchool", back_populates="inst_students")
    enrollments = relationship("InstitutionalEnrollment", back_populates="student")
    
    __mapper_args__ = {
        'polymorphic_identity': 'institutional'
    }
    
    @validates('school_id')
    def validate_school_id(self, key, value):
        if not value:
            raise ValueError("機構學生必須指定學校")
        return value


class IndividualStudent(StudentBase):
    """個體戶學生 - 每個老師獨立管理"""
    __tablename__ = "dual_individual_students"
    
    id = Column(String, ForeignKey("dual_student_base.id"), primary_key=True)
    teacher_id = Column(String, ForeignKey("dual_users.id"), nullable=False)  # 所屬老師
    referred_by = Column(String)
    learning_goals = Column(Text)
    preferred_schedule = Column(JSON)
    
    # 密碼管理（每個老師獨立）
    is_default_password = Column(Boolean, default=True)  # 是否使用預設密碼
    password_hash = Column(String, nullable=True)  # 自訂密碼的 hash（如果有）
    
    # 關聯
    teacher = relationship("DualUser", foreign_keys=[teacher_id])
    enrollments = relationship("IndividualEnrollment", back_populates="student")
    
    __mapper_args__ = {
        'polymorphic_identity': 'individual'
    }
    
    @property
    def default_password(self):
        """生成預設密碼（生日格式：YYYYMMDD）"""
        return self.birth_date.replace('-', '') if self.birth_date else None


# ===== 註冊關聯表 =====
class InstitutionalEnrollment(DualBase):
    """機構體系的註冊關聯"""
    __tablename__ = "dual_institutional_enrollments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("dual_institutional_students.id"))
    classroom_id = Column(String, ForeignKey("dual_institutional_classrooms.id"))
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # 關聯
    student = relationship("InstitutionalStudent", back_populates="enrollments")
    classroom = relationship("InstitutionalClassroom", back_populates="enrollments")


class IndividualEnrollment(DualBase):
    """個體戶體系的註冊關聯"""
    __tablename__ = "dual_individual_enrollments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("dual_individual_students.id"))
    classroom_id = Column(String, ForeignKey("dual_individual_classrooms.id"))
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    payment_status = Column(String, default="pending")
    
    # 關聯
    student = relationship("IndividualStudent", back_populates="enrollments")
    classroom = relationship("IndividualClassroom", back_populates="enrollments")


# ===== 課程基礎類別 =====
class CourseBase(DualBase):
    """課程基礎類別"""
    __tablename__ = "dual_course_base"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    difficulty_level = Column(Enum(DifficultyLevel))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 多型欄位
    type = Column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': type
    }


class InstitutionalCourse(CourseBase):
    """機構課程"""
    __tablename__ = "dual_institutional_courses"
    
    id = Column(String, ForeignKey("dual_course_base.id"), primary_key=True)
    school_id = Column(String, ForeignKey("dual_schools.id"), nullable=False)
    is_template = Column(Boolean, default=False)
    shared_with_teachers = Column(JSON, default=list)
    
    # 關聯
    school = relationship("DualSchool", back_populates="inst_courses")
    lessons = relationship("InstitutionalLesson", back_populates="course")
    
    __mapper_args__ = {
        'polymorphic_identity': 'institutional'
    }


class IndividualCourse(CourseBase):
    """個體戶課程"""
    __tablename__ = "dual_individual_courses"
    
    id = Column(String, ForeignKey("dual_course_base.id"), primary_key=True)
    teacher_id = Column(String, ForeignKey("dual_users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    custom_materials = Column(Boolean, default=True)
    pricing_per_lesson = Column(Integer)
    
    # 課程歸屬
    classroom_id = Column(String, ForeignKey("dual_individual_classrooms.id"), nullable=True)
    
    # 複製來源追蹤
    copied_from_id = Column(String, ForeignKey("dual_course_base.id"), nullable=True)
    
    # 關聯
    teacher = relationship("DualUser", back_populates="individual_courses")
    lessons = relationship("IndividualLesson", back_populates="course")
    classroom = relationship("IndividualClassroom", backref="classroom_courses", foreign_keys=[classroom_id])
    copied_from = relationship("CourseBase", 
                             primaryjoin="IndividualCourse.copied_from_id==CourseBase.id",
                             remote_side="CourseBase.id", 
                             foreign_keys=[copied_from_id])
    
    __mapper_args__ = {
        'polymorphic_identity': 'individual',
        'inherit_condition': id == CourseBase.id
    }


# ===== 課程內容 =====
class LessonBase(DualBase):
    """課程內容基礎類別"""
    __tablename__ = "dual_lesson_base"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    activity_type = Column(Enum(ActivityType), nullable=False)
    content = Column(JSON)
    time_limit_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 多型欄位
    type = Column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': type
    }


class InstitutionalLesson(LessonBase):
    """機構課程內容"""
    __tablename__ = "dual_institutional_lessons"
    
    id = Column(String, ForeignKey("dual_lesson_base.id"), primary_key=True)
    course_id = Column(String, ForeignKey("dual_institutional_courses.id"))
    
    # 關聯
    course = relationship("InstitutionalCourse", back_populates="lessons")
    assignments = relationship("InstitutionalAssignment", back_populates="lesson")
    
    __mapper_args__ = {
        'polymorphic_identity': 'institutional'
    }


class IndividualLesson(LessonBase):
    """個體戶課程內容"""
    __tablename__ = "dual_individual_lessons"
    
    id = Column(String, ForeignKey("dual_lesson_base.id"), primary_key=True)
    course_id = Column(String, ForeignKey("dual_individual_courses.id"))
    
    # 關聯
    course = relationship("IndividualCourse", back_populates="lessons")
    assignments = relationship("IndividualAssignment", back_populates="lesson")
    
    __mapper_args__ = {
        'polymorphic_identity': 'individual'
    }


# ===== 作業系統 =====
class InstitutionalAssignment(DualBase):
    """機構作業"""
    __tablename__ = "dual_institutional_assignments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("dual_institutional_students.id"))
    lesson_id = Column(String, ForeignKey("dual_institutional_lessons.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    status = Column(String, default="pending")
    score = Column(Integer)
    
    # 關聯
    student = relationship("InstitutionalStudent")
    lesson = relationship("InstitutionalLesson", back_populates="assignments")


class IndividualAssignment(DualBase):
    """個體戶作業"""
    __tablename__ = "dual_individual_assignments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("dual_individual_students.id"))
    lesson_id = Column(String, ForeignKey("dual_individual_lessons.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    status = Column(String, default="pending")
    score = Column(Integer)
    personalized_feedback = Column(Text)
    
    # 關聯
    student = relationship("IndividualStudent")
    lesson = relationship("IndividualLesson", back_populates="assignments")