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
    role = Column(Enum(UserRole), nullable=False)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_classes = relationship("Class", back_populates="teacher")
    created_courses = relationship("Course", back_populates="creator")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=False)  # YYYYMMDD format
    parent_email = Column(String)
    parent_phone = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    class_enrollments = relationship("ClassStudent", back_populates="student")
    assignments = relationship("StudentAssignment", back_populates="student")

class School(Base):
    __tablename__ = "schools"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    address = Column(String)
    phone = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    classes = relationship("Class", back_populates="school")

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    grade_level = Column(String)
    difficulty_level = Column(Enum(DifficultyLevel))
    teacher_id = Column(String, ForeignKey("users.id"))
    school_id = Column(String, ForeignKey("schools.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("User", back_populates="created_classes")
    school = relationship("School", back_populates="classes")
    students = relationship("ClassStudent", back_populates="class_")
    course_mappings = relationship("ClassCourseMapping", back_populates="class_")

class ClassStudent(Base):
    __tablename__ = "class_students"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey("classes.id"))
    student_id = Column(String, ForeignKey("students.id"))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    class_ = relationship("Class", back_populates="students")
    student = relationship("Student", back_populates="class_enrollments")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    difficulty_level = Column(Enum(DifficultyLevel))
    created_by = Column(String, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_courses")
    lessons = relationship("Lesson", back_populates="course")
    class_mappings = relationship("ClassCourseMapping", back_populates="course")

class ClassCourseMapping(Base):
    __tablename__ = "class_course_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String, ForeignKey("classes.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    class_ = relationship("Class", back_populates="course_mappings")
    course = relationship("Course", back_populates="class_mappings")

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