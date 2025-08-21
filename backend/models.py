from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid

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
    SPEAKING_SCENARIO = "speaking_scenario"
    LISTENING_CLOZE = "listening_cloze"
    SENTENCE_MAKING = "sentence_making"
    SPEAKING_QUIZ = "speaking_quiz"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)  # Primary role
    phone = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Multi-role support
    is_individual_teacher = Column(Boolean, default=False)  # Can act as individual teacher
    is_institutional_admin = Column(Boolean, default=False)  # Can act as institutional admin
    current_role_context = Column(String, default="default")  # "individual" or "institutional" or "default"
    
    # Relationships - 舊系統
    created_classrooms = relationship("Classroom", back_populates="teacher")
    created_courses = relationship("Course", back_populates="creator")
    
    # Relationships - 新的雙體系
    # individual_classrooms = relationship("IndividualClassroom", back_populates="teacher")
    # individual_courses = relationship("IndividualCourse", back_populates="teacher")
    
    @property
    def has_multiple_roles(self):
        """Check if user has multiple role contexts"""
        return self.is_individual_teacher and self.is_institutional_admin
    
    @property
    def effective_role(self):
        """Get the effective role based on current context"""
        if self.current_role_context == "individual" and self.is_individual_teacher:
            return UserRole.TEACHER
        elif self.current_role_context == "institutional" and self.is_institutional_admin:
            return UserRole.ADMIN
        return self.role

class Student(Base):
    __tablename__ = "students"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=False)  # YYYYMMDD format
    phone_number = Column(String, unique=True, index=True)  # Student's phone
    parent_email = Column(String)
    parent_phone = Column(String)
    name = Column(String)  # Alias for full_name
    grade = Column(Integer)
    school = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    classroom_enrollments = relationship("ClassroomStudent", back_populates="student")
    assignments = relationship("StudentAssignment", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student")

class School(Base):
    __tablename__ = "schools"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    address = Column(String)
    phone = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    classrooms = relationship("Classroom", back_populates="school")

class Classroom(Base):
    __tablename__ = "classrooms"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    grade_level = Column(String)
    difficulty_level = Column(Enum(DifficultyLevel))
    teacher_id = Column(String, ForeignKey("users.id"))
    school_id = Column(String, ForeignKey("schools.id"), nullable=True)  # Nullable for individual teachers
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("User", back_populates="created_classrooms")
    school = relationship("School", back_populates="classrooms")
    students = relationship("ClassroomStudent", back_populates="classroom")
    course_mappings = relationship("ClassroomCourseMapping", back_populates="classroom")
    
    @property
    def is_individual(self):
        """Check if this is an individual teacher's classroom"""
        return self.school_id is None
    
    @property
    def owner_name(self):
        """Get the owner name (school name for institutional, teacher name for individual)"""
        if self.is_individual:
            return self.teacher.full_name if self.teacher else "個人教師"
        return self.school.name if self.school else "未知學校"
    
    @property
    def owner_type(self):
        """Get the owner type"""
        return "individual" if self.is_individual else "institutional"

class ClassroomStudent(Base):
    __tablename__ = "classroom_students"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String, ForeignKey("classrooms.id"))
    student_id = Column(String, ForeignKey("students.id"))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    classroom = relationship("Classroom", back_populates="students")
    student = relationship("Student", back_populates="classroom_enrollments")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    course_code = Column(String, unique=True, index=True)
    grade_level = Column(Integer)
    subject = Column(String)
    max_students = Column(Integer, default=30)
    difficulty_level = Column(Enum(DifficultyLevel))
    created_by = Column(String, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_courses")
    lessons = relationship("Lesson", back_populates="course")
    classroom_mappings = relationship("ClassroomCourseMapping", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")
    
    @property
    def teacher(self):
        """Alias for creator to maintain consistency"""
        return self.creator

class ClassroomCourseMapping(Base):
    __tablename__ = "classroom_course_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String, ForeignKey("classrooms.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    classroom = relationship("Classroom", back_populates="course_mappings")
    course = relationship("Course", back_populates="classroom_mappings")

class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"))
    lesson_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    activity_type = Column(Enum(ActivityType), nullable=False)
    content = Column(JSON)  # Flexible content structure
    time_limit_minutes = Column(Integer, default=30)
    target_wpm = Column(Integer)  # For reading assessment
    target_accuracy = Column(Integer)  # For reading assessment
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    assignments = relationship("StudentAssignment", back_populates="lesson")

class StudentAssignment(Base):
    __tablename__ = "student_assignments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"))
    lesson_id = Column(String, ForeignKey("lessons.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    status = Column(String, default="pending")  # pending, in_progress, completed, overdue
    
    # Relationships
    student = relationship("Student", back_populates="assignments")
    lesson = relationship("Lesson", back_populates="assignments")
    submissions = relationship("ActivityResult", back_populates="assignment")

class ActivityResult(Base):
    __tablename__ = "activity_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = Column(String, ForeignKey("student_assignments.id"))
    attempt_number = Column(Integer, default=1)
    result_data = Column(JSON)  # Flexible result structure
    score = Column(Integer)
    feedback = Column(Text)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assignment = relationship("StudentAssignment", back_populates="submissions")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")