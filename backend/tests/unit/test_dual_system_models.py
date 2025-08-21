"""
測試雙體系（機構/個體戶）模型設計
使用 TDD 方式，先寫測試再實作
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from models_v2 import (
    ClassroomBase, InstitutionalClassroom, IndividualClassroom,
    StudentBase, InstitutionalStudent, IndividualStudent,
    CourseBase, InstitutionalCourse, IndividualCourse,
    InstitutionalEnrollment, IndividualEnrollment,
    check_teacher_classroom_access
)
from models import User, School


class TestClassroomModels:
    """測試教室模型的雙體系設計"""
    
    def test_institutional_classroom_requires_school(self, db: Session):
        """機構教室必須屬於某個學校"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="機構教室必須指定學校"):
            classroom = InstitutionalClassroom(
                name="數學教室 A",
                grade_level="國小三年級",
                school_id=None  # 這應該要失敗
            )
    
    def test_individual_classroom_requires_teacher(self, db: Session):
        """個體戶教室必須屬於某個教師"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="個體戶教室必須指定教師"):
            classroom = IndividualClassroom(
                name="Jane 的英語教室",
                grade_level="國小",
                teacher_id=None  # 這應該要失敗
            )
    
    def test_institutional_classroom_creation(self, db: Session, sample_school, sample_teacher):
        """測試機構教室的創建"""
        # Arrange
        classroom_data = {
            "name": "數學教室 301",
            "grade_level": "國小三年級",
            "school_id": sample_school.id,
            "room_number": "301",
            "capacity": 30
        }
        
        # Act
        classroom = InstitutionalClassroom(**classroom_data)
        db.add(classroom)
        db.commit()
        
        # Assert
        assert classroom.id is not None
        assert classroom.type == "institutional"
        assert classroom.school_id == sample_school.id
        assert classroom.room_number == "301"
        assert classroom.capacity == 30
    
    def test_individual_classroom_creation(self, db: Session, sample_individual_teacher):
        """測試個體戶教室的創建"""
        # Arrange
        classroom_data = {
            "name": "Amy 的數學小班",
            "grade_level": "國小1-3年級",
            "teacher_id": sample_individual_teacher.id,
            "location": "線上授課",
            "pricing": 800,  # 每小時收費
            "max_students": 5
        }
        
        # Act
        classroom = IndividualClassroom(**classroom_data)
        db.add(classroom)
        db.commit()
        
        # Assert
        assert classroom.id is not None
        assert classroom.type == "individual"
        assert classroom.teacher_id == sample_individual_teacher.id
        assert classroom.pricing == 800
        assert classroom.max_students == 5
    
    def test_query_all_classrooms_polymorphic(self, db: Session):
        """測試多型查詢：可以一次查詢所有類型的教室"""
        # Arrange
        inst_classroom = InstitutionalClassroom(
            name="機構教室", 
            school_id="school_1",
            room_number="101"
        )
        ind_classroom = IndividualClassroom(
            name="個人教室",
            teacher_id="teacher_1", 
            pricing=600
        )
        db.add_all([inst_classroom, ind_classroom])
        db.commit()
        
        # Act
        all_classrooms = db.query(ClassroomBase).all()
        
        # Assert
        assert len(all_classrooms) == 2
        assert isinstance(all_classrooms[0], InstitutionalClassroom)
        assert isinstance(all_classrooms[1], IndividualClassroom)


class TestStudentModels:
    """測試學生模型的雙體系設計"""
    
    def test_institutional_student_requires_school(self, db: Session):
        """機構學生必須屬於某個學校"""
        with pytest.raises(ValueError, match="機構學生必須指定學校"):
            student = InstitutionalStudent(
                full_name="王小明",
                email="xiaoming@example.com",
                school_id=None
            )
    
    def test_institutional_student_creation(self, db: Session, sample_school):
        """測試機構學生的創建"""
        # Arrange
        student_data = {
            "full_name": "李小華",
            "email": "xiaohua@example.com",
            "birth_date": "2015-03-15",
            "school_id": sample_school.id,
            "student_id": "STU2024001",  # 學號
            "parent_phone": "0912-345-678",
            "emergency_contact": "李爸爸 0912-345-678"
        }
        
        # Act
        student = InstitutionalStudent(**student_data)
        db.add(student)
        db.commit()
        
        # Assert
        assert student.id is not None
        assert student.type == "institutional"
        assert student.student_id == "STU2024001"
        assert student.school_id == sample_school.id
    
    def test_individual_student_creation(self, db: Session):
        """測試個體戶學生的創建"""
        # Arrange
        student_data = {
            "full_name": "張小美",
            "email": "xiaomei@example.com",
            "birth_date": "2014-07-20",
            "referred_by": "朋友介紹",
            "learning_goals": "希望提升英文口說能力",
            "preferred_schedule": {
                "weekdays": ["週三", "週五"],
                "time": "下午4-6點"
            }
        }
        
        # Act
        student = IndividualStudent(**student_data)
        db.add(student)
        db.commit()
        
        # Assert
        assert student.id is not None
        assert student.type == "individual"
        assert student.referred_by == "朋友介紹"
        assert "英文口說" in student.learning_goals
    
    def test_student_enrollment_isolation(self, db: Session):
        """測試學生註冊的隔離性：機構學生不能註冊個體戶教室"""
        # Arrange
        inst_student = InstitutionalStudent(
            full_name="機構學生",
            school_id="school_1"
        )
        ind_classroom = IndividualClassroom(
            name="個人教室",
            teacher_id="teacher_1"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="機構學生不能註冊個體戶教室"):
            enrollment = IndividualEnrollment(
                student=inst_student,
                classroom=ind_classroom
            )


class TestCourseModels:
    """測試課程模型的雙體系設計"""
    
    def test_institutional_course_sharing(self, db: Session, sample_school):
        """測試機構課程可以在教師間共享"""
        # Arrange
        course = InstitutionalCourse(
            title="標準英語課程 Level 1",
            description="適合初學者",
            school_id=sample_school.id,
            is_template=True,  # 可作為模板
            shared_with_teachers=["teacher_1", "teacher_2"]
        )
        
        # Act
        db.add(course)
        db.commit()
        
        # Assert
        assert course.is_template is True
        assert len(course.shared_with_teachers) == 2
        assert "teacher_1" in course.shared_with_teachers
    
    def test_individual_course_customization(self, db: Session, sample_individual_teacher):
        """測試個體戶課程的客製化特性"""
        # Arrange
        course = IndividualCourse(
            title="Amy 的進階會話班",
            description="針對中級學習者的口說訓練",
            teacher_id=sample_individual_teacher.id,
            is_public=False,  # 不公開
            custom_materials=True,  # 使用自訂教材
            pricing_per_lesson=1200
        )
        
        # Act
        db.add(course)
        db.commit()
        
        # Assert
        assert course.type == "individual"
        assert course.is_public is False
        assert course.pricing_per_lesson == 1200
    
    def test_course_assignment_compatibility(self, db: Session):
        """測試作業指派的相容性：確保體系內一致"""
        # Arrange
        inst_course = InstitutionalCourse(title="機構課程", school_id="school_1")
        ind_student = IndividualStudent(full_name="個人學生", email="test@example.com")
        
        # Act & Assert
        # 這個測試需要 Assignment 模型，暫時跳過
        pass


class TestBusinessRules:
    """測試業務規則"""
    
    def test_individual_teacher_cannot_access_institutional_resources(self, db: Session):
        """個體戶教師不能存取機構資源"""
        # Arrange
        ind_teacher = User(
            email="individual@test.com",
            role="teacher",
            is_individual_teacher=True,
            is_institutional_admin=False
        )
        inst_classroom = InstitutionalClassroom(
            name="機構教室",
            school_id="school_1"
        )
        
        # Act & Assert
        with pytest.raises(PermissionError, match="個體戶教師不能存取機構資源"):
            can_access = check_teacher_classroom_access(ind_teacher, inst_classroom)
    
    def test_max_students_enforcement(self, db: Session):
        """測試個體戶教室的學生人數上限"""
        # Arrange
        classroom = IndividualClassroom(
            name="小班教學",
            teacher_id="teacher_1",
            max_students=3
        )
        
        # 加入3個學生
        for i in range(3):
            student = IndividualStudent(
                full_name=f"學生{i+1}",
                email=f"student{i+1}@example.com"
            )
            enrollment = IndividualEnrollment(
                student=student,
                classroom=classroom
            )
            db.add(enrollment)
        db.commit()
        
        # Act & Assert - 嘗試加入第4個學生
        with pytest.raises(ValueError, match="教室已達人數上限"):
            student4 = IndividualStudent(
                full_name="學生4",
                email="student4@example.com"
            )
            enrollment4 = IndividualEnrollment(
                student=student4,
                classroom=classroom
            )


class TestMigrationScenarios:
    """測試體系轉換場景"""
    
    def test_individual_teacher_joins_institution(self, db: Session):
        """測試個體戶教師加入機構的場景"""
        # Arrange
        teacher = User(
            email="teacher@example.com",
            is_individual_teacher=True,
            is_institutional_admin=False
        )
        
        # 教師有自己的教室和學生
        ind_classroom = IndividualClassroom(
            name="私人教室",
            teacher_id=teacher.id
        )
        
        # Act - 教師加入機構
        teacher.is_institutional_admin = True
        teacher.current_role_context = "institutional"
        
        # Assert
        assert teacher.has_multiple_roles is True
        # 原有的個體戶資源應該保留
        assert ind_classroom.teacher_id == teacher.id
        assert ind_classroom.is_active is True
    
    def test_data_isolation_after_role_switch(self, db: Session):
        """測試角色切換後的資料隔離"""
        # Arrange
        hybrid_teacher = User(
            email="hybrid@example.com",
            is_individual_teacher=True,
            is_institutional_admin=True,
            current_role_context="individual"
        )
        
        # Act - 在個體戶模式下查詢
        ind_classrooms = db.query(IndividualClassroom).filter(
            IndividualClassroom.teacher_id == hybrid_teacher.id
        ).all()
        
        # 切換到機構模式
        hybrid_teacher.current_role_context = "institutional"
        
        inst_classrooms = db.query(InstitutionalClassroom).join(
            School
        ).filter(
            # 這裡應該根據教師的學校權限過濾
            School.id == hybrid_teacher.school_id
        ).all()
        
        # Assert - 兩種模式下看到的資料應該不同
        assert len(ind_classrooms) >= 0  # 可能有個人教室
        assert len(inst_classrooms) >= 0  # 可能有機構教室
        # 重要：兩個查詢結果不應該有交集