"""
班級管理基礎功能單元測試
測試班級的建立、編輯、學生管理等核心功能
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
import os

# 設置測試環境變數
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"

from models import User, UserRole, Classroom, Student, ClassroomStudent
from auth import get_password_hash


class TestClassroomCreation:
    """班級建立功能測試"""
    
    @pytest.fixture
    def teacher(self, db: Session):
        """建立測試教師"""
        user = User(
            email="teacher@test.com",
            full_name="Test Teacher",
            role=UserRole.TEACHER,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_individual_teacher=True
        )
        db.add(user)
        db.commit()
        return user
    
    def test_create_classroom_basic(self, db: Session, teacher):
        """測試基本班級建立"""
        new_classroom = Classroom(
            name="測試班級A",
            grade_level="國小三年級",
            teacher_id=teacher.id
        )
        db.add(new_classroom)
        db.commit()
        
        assert new_classroom.id is not None
        assert new_classroom.name == "測試班級A"
        assert new_classroom.grade_level == "國小三年級"
        assert new_classroom.teacher_id == teacher.id
        assert new_classroom.is_active is True
    
    def test_create_individual_classroom(self, db: Session, teacher):
        """測試個體教師班級（無學校ID）"""
        classroom = Classroom(
            name="個人英語班",
            grade_level="國小四年級",
            teacher_id=teacher.id,
            school_id=None  # 個體教師沒有學校
        )
        db.add(classroom)
        db.commit()
        
        assert classroom.is_individual is True
        assert classroom.owner_type == "individual"
        assert classroom.owner_name == teacher.full_name


class TestStudentClassroomAssignment:
    """學生班級分配功能測試"""
    
    @pytest.fixture
    def teacher(self, db: Session):
        """建立測試教師"""
        user = User(
            email="teacher2@test.com",
            full_name="Test Teacher 2",
            role=UserRole.TEACHER,
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        return user
    
    @pytest.fixture
    def classroom(self, db: Session, teacher):
        """建立測試班級"""
        classroom = Classroom(
            name="測試班級",
            grade_level="國小三年級",
            teacher_id=teacher.id
        )
        db.add(classroom)
        db.commit()
        return classroom
    
    @pytest.fixture
    def student(self, db: Session):
        """建立測試學生"""
        student = Student(
            email="student@test.com",
            full_name="測試學生",
            birth_date="20100101",
            name="測試學生"
        )
        db.add(student)
        db.commit()
        return student
    
    def test_assign_student_to_classroom(self, db: Session, classroom, student):
        """測試分配學生到班級"""
        assignment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student.id
        )
        db.add(assignment)
        db.commit()
        
        assert assignment.id is not None
        assert assignment.classroom_id == classroom.id
        assert assignment.student_id == student.id
        assert assignment.joined_at is not None
    
    def test_get_classroom_students(self, db: Session, classroom, student):
        """測試取得班級學生列表"""
        # 分配學生
        assignment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student.id
        )
        db.add(assignment)
        db.commit()
        
        # 查詢班級學生
        students = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == classroom.id
        ).all()
        
        assert len(students) == 1
        assert students[0].student_id == student.id
    
    def test_remove_student_from_classroom(self, db: Session, classroom, student):
        """測試從班級移除學生"""
        # 先分配
        assignment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student.id
        )
        db.add(assignment)
        db.commit()
        
        # 再移除
        db.delete(assignment)
        db.commit()
        
        # 確認已移除
        remaining = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == classroom.id
        ).count()
        
        assert remaining == 0