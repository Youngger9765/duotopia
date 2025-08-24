"""
雙體系模型設計 (V2)
支援機構體系和個體戶體系
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, JSON, Enum, CheckConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from database import Base
import enum
import uuid


# ===== 基礎類別 =====

class ClassroomBase(Base):
    """教室基礎類別"""
    __tablename__ = "classroom_base"
    
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
    __tablename__ = "institutional_classrooms"
    
    id = Column(String, ForeignKey("classroom_base.id"), primary_key=True)
    school_id = Column(String, ForeignKey("schools.id"), nullable=False)
    room_number = Column(String)
    capacity = Column(Integer, default=30)
    
    # 關聯
    # school = relationship("School", back_populates="classrooms")  # 暫時註解，避免衝突
    
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
    __tablename__ = "individual_classrooms"
    
    id = Column(String, ForeignKey("classroom_base.id"), primary_key=True)
    teacher_id = Column(String, ForeignKey("users.id"), nullable=False)
    location = Column(String)  # 線上/實體地址
    pricing = Column(Integer)  # 每小時收費
    max_students = Column(Integer, default=10)
    
    # 關聯
    # teacher = relationship("User", back_populates="individual_classrooms")  # 暫時註解，避免衝突
    enrollments = relationship("IndividualEnrollment", back_populates="classroom")
    
    __mapper_args__ = {
        'polymorphic_identity': 'individual'
    }
    
    @validates('teacher_id')
    def validate_teacher_id(self, key, value):
        if not value:
            raise ValueError("個體戶教室必須指定教師")
        return value
    
    def check_capacity(self, session):
        """檢查是否還有空位"""
        current_count = session.query(IndividualEnrollment).filter(
            IndividualEnrollment.classroom_id == self.id,
            IndividualEnrollment.is_active == True
        ).count()
        
        if current_count >= self.max_students:
            raise ValueError("教室已達人數上限")
        return True


# ===== 學生模型 =====

class StudentBase(Base):
    """學生基礎類別"""
    __tablename__ = "student_base"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
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
    __tablename__ = "institutional_students"
    
    id = Column(String, ForeignKey("student_base.id"), primary_key=True)
    school_id = Column(String, ForeignKey("schools.id"), nullable=False)
    student_id = Column(String, unique=True)  # 學號
    parent_phone = Column(String)
    emergency_contact = Column(String)
    
    # 關聯
    # school = relationship("School", back_populates="students")  # 暫時註解，避免衝突
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
    """個體戶學生"""
    __tablename__ = "individual_students"
    
    id = Column(String, ForeignKey("student_base.id"), primary_key=True)
    referred_by = Column(String)
    learning_goals = Column(Text)
    preferred_schedule = Column(JSON)
    
    # 關聯
    enrollments = relationship("IndividualEnrollment", back_populates="student")
    
    __mapper_args__ = {
        'polymorphic_identity': 'individual'
    }


# ===== 註冊關聯表 =====

class InstitutionalEnrollment(Base):
    """機構體系的註冊關聯"""
    __tablename__ = "institutional_enrollments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("institutional_students.id"))
    classroom_id = Column(String, ForeignKey("institutional_classrooms.id"))
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # 關聯
    student = relationship("InstitutionalStudent", back_populates="enrollments")
    classroom = relationship("InstitutionalClassroom")


class IndividualEnrollment(Base):
    """個體戶體系的註冊關聯"""
    __tablename__ = "individual_enrollments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("individual_students.id"))
    classroom_id = Column(String, ForeignKey("individual_classrooms.id"))
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    payment_status = Column(String, default="pending")  # 個體戶可能需要追蹤付款
    
    # 關聯
    student = relationship("IndividualStudent", back_populates="enrollments")
    classroom = relationship("IndividualClassroom", back_populates="enrollments")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 檢查類型匹配
        if hasattr(self, 'student') and hasattr(self, 'classroom'):
            if isinstance(self.student, InstitutionalStudent):
                raise ValueError("機構學生不能註冊個體戶教室")


# ===== 課程模型 =====

class CourseBase(Base):
    """課程基礎類別"""
    __tablename__ = "course_base"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    difficulty_level = Column(String)
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
    __tablename__ = "institutional_courses"
    
    id = Column(String, ForeignKey("course_base.id"), primary_key=True)
    school_id = Column(String, ForeignKey("schools.id"), nullable=False)
    is_template = Column(Boolean, default=False)
    shared_with_teachers = Column(JSON, default=list)
    
    # 關聯
    # school = relationship("School", back_populates="courses")  # 暫時註解，避免衝突
    
    __mapper_args__ = {
        'polymorphic_identity': 'institutional'
    }


class IndividualCourse(CourseBase):
    """個體戶課程"""
    __tablename__ = "individual_courses"
    
    id = Column(String, ForeignKey("course_base.id"), primary_key=True)
    teacher_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    custom_materials = Column(Boolean, default=True)
    pricing_per_lesson = Column(Integer)
    
    # 關聯
    # teacher = relationship("User", back_populates="individual_courses")  # 暫時註解，避免衝突
    
    __mapper_args__ = {
        'polymorphic_identity': 'individual'
    }


# ===== 權限檢查函數 =====

def check_teacher_classroom_access(teacher, classroom):
    """檢查教師是否可以存取教室"""
    # 個體戶教師不能存取機構資源
    if teacher.is_individual_teacher and not teacher.is_institutional_admin:
        if isinstance(classroom, InstitutionalClassroom):
            raise PermissionError("個體戶教師不能存取機構資源")
    
    # 機構教師只能存取自己學校的資源
    if isinstance(classroom, InstitutionalClassroom):
        if teacher.school_id != classroom.school_id:
            raise PermissionError("只能存取所屬學校的資源")
    
    # 個體戶教室只能由擁有者存取
    if isinstance(classroom, IndividualClassroom):
        if teacher.id != classroom.teacher_id:
            raise PermissionError("只能存取自己的教室")
    
    return True


# ===== 更新 User 和 School 模型的關聯 =====

# 需要在原本的 models.py 中更新 User 和 School 的關聯
# 或者這裡我們可以使用 monkey patching 來添加關聯（僅供測試）