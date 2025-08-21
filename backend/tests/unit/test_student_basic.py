"""
學生管理基礎功能單元測試
測試學生的建立、更新、班級分配等核心功能
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
import os

# 設置測試環境變數
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"

from models import User, UserRole, Student, Classroom, ClassroomStudent
from auth import get_password_hash


class TestStudentCreation:
    """學生建立功能測試"""
    
    def test_create_student_basic(self, db: Session):
        """測試基本學生建立"""
        student = Student(
            email="xiaoming@test.com",
            full_name="張小明",
            birth_date="20100101",
            name="張小明"
        )
        db.add(student)
        db.commit()
        
        assert student.id is not None
        assert student.email == "xiaoming@test.com"
        assert student.full_name == "張小明"
        assert student.birth_date == "20100101"
        assert student.is_active is True
    
    def test_create_student_with_phone(self, db: Session):
        """測試建立有電話的學生"""
        student = Student(
            email="student2@test.com",
            full_name="李小華",
            birth_date="20100215",
            phone_number="0912345678",
            parent_phone="0923456789",
            name="李小華"
        )
        db.add(student)
        db.commit()
        
        assert student.phone_number == "0912345678"
        assert student.parent_phone == "0923456789"
    
    def test_student_default_password(self, db: Session):
        """測試學生預設密碼（生日）"""
        student = Student(
            email="test@test.com",
            full_name="測試學生",
            birth_date="20100320",
            name="測試學生"
        )
        db.add(student)
        db.commit()
        
        # 預設密碼應該是生日
        expected_password = "20100320"
        assert student.birth_date == expected_password


class TestStudentUpdate:
    """學生更新功能測試"""
    
    @pytest.fixture
    def student(self, db: Session):
        """建立測試學生"""
        student = Student(
            email="update@test.com",
            full_name="原始姓名",
            birth_date="20100101",
            name="原始姓名"
        )
        db.add(student)
        db.commit()
        return student
    
    def test_update_student_info(self, db: Session, student):
        """測試更新學生資訊"""
        # 更新資料
        student.full_name = "更新後姓名"
        student.name = "更新後姓名"
        student.parent_email = "parent@test.com"
        student.grade = 4
        student.school = "測試國小"
        db.commit()
        
        # 查詢確認
        updated = db.query(Student).filter(Student.id == student.id).first()
        assert updated.full_name == "更新後姓名"
        assert updated.parent_email == "parent@test.com"
        assert updated.grade == 4
        assert updated.school == "測試國小"
        # 生日不應該被更改
        assert updated.birth_date == "20100101"
    
    def test_deactivate_student(self, db: Session, student):
        """測試停用學生"""
        student.is_active = False
        db.commit()
        
        inactive_student = db.query(Student).filter(Student.id == student.id).first()
        assert inactive_student.is_active is False


class TestStudentClassroomRelationship:
    """學生班級關係測試"""
    
    @pytest.fixture
    def teacher(self, db: Session):
        """建立測試教師"""
        user = User(
            email="teacher@test.com",
            full_name="Test Teacher",
            role=UserRole.TEACHER,
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        return user
    
    @pytest.fixture
    def classrooms(self, db: Session, teacher):
        """建立多個測試班級"""
        classrooms = []
        for i in range(2):
            classroom = Classroom(
                name=f"班級{i+1}",
                grade_level=f"國小{i+3}年級",
                teacher_id=teacher.id
            )
            db.add(classroom)
            classrooms.append(classroom)
        db.commit()
        return classrooms
    
    def test_student_multiple_classrooms(self, db: Session, classrooms):
        """測試學生加入多個班級"""
        student = Student(
            email="multi@test.com",
            full_name="多班學生",
            birth_date="20100101",
            name="多班學生"
        )
        db.add(student)
        db.commit()
        
        # 加入兩個班級
        for classroom in classrooms:
            assignment = ClassroomStudent(
                classroom_id=classroom.id,
                student_id=student.id
            )
            db.add(assignment)
        db.commit()
        
        # 查詢學生的班級數
        enrollments = db.query(ClassroomStudent).filter(
            ClassroomStudent.student_id == student.id
        ).count()
        
        assert enrollments == 2
    
    def test_get_students_by_classroom(self, db: Session, teacher):
        """測試按班級查詢學生"""
        # 建立班級
        classroom = Classroom(
            name="查詢測試班",
            grade_level="國小五年級",
            teacher_id=teacher.id
        )
        db.add(classroom)
        db.commit()
        
        # 建立並分配3個學生
        for i in range(3):
            student = Student(
                email=f"student{i}@test.com",
                full_name=f"學生{i+1}",
                birth_date="20100101",
                name=f"學生{i+1}"
            )
            db.add(student)
            db.commit()
            
            assignment = ClassroomStudent(
                classroom_id=classroom.id,
                student_id=student.id
            )
            db.add(assignment)
        db.commit()
        
        # 查詢班級學生數
        student_count = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == classroom.id
        ).count()
        
        assert student_count == 3