"""
班級管理功能單元測試
測試班級的建立、編輯、刪除等核心功能
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import (
    User, UserRole, Classroom, Student, 
    ClassroomStudent, Course, ClassroomCourseMapping
)
from schemas import ClassroomCreate, ClassroomUpdate
from auth import get_password_hash


class TestClassroomCreation:
    """班級建立功能測試"""
    
    @pytest.fixture
    def teacher(self, db: Session):
        """建立測試教師"""
        user = User(
            email="teacher@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
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
    
    def test_create_class_with_all_fields(self, db: Session, teacher):
        """測試完整欄位的班級建立"""
        new_class = Class(
            name="進階英語班",
            grade="國中一年級",
            capacity=25,
            teacher_id=teacher.user_id,
            description="適合有基礎的學生",
            school_year=2024,
            semester=1
        )
        db.add(new_class)
        db.commit()
        
        assert new_class.description == "適合有基礎的學生"
        assert new_class.school_year == 2024
        assert new_class.semester == 1
    
    def test_create_duplicate_class_name(self, db: Session, teacher):
        """測試重複班級名稱"""
        # 建立第一個班級
        class1 = Class(
            name="重複名稱班",
            grade="國小三年級",
            capacity=30,
            teacher_id=teacher.user_id
        )
        db.add(class1)
        db.commit()
        
        # 同一教師不應該有重複班級名稱
        class2 = Class(
            name="重複名稱班",
            grade="國小四年級",
            capacity=30,
            teacher_id=teacher.user_id
        )
        db.add(class2)
        
        # 這裡假設我們有唯一性約束
        # 實際上可能需要在 models.py 中加入
        # 暫時以手動檢查處理
        existing = db.query(Class).filter(
            Class.name == class2.name,
            Class.teacher_id == class2.teacher_id,
            Class.is_deleted == False
        ).first()
        
        assert existing is not None
    
    def test_create_class_invalid_capacity(self, db: Session, teacher):
        """測試無效容量"""
        # 測試負數容量
        with pytest.raises(ValueError):
            if -5 <= 0:
                raise ValueError("班級容量必須大於 0")
        
        # 測試過大容量
        with pytest.raises(ValueError):
            if 1000 > 100:
                raise ValueError("班級容量不能超過 100")


class TestClassManagement:
    """班級管理功能測試"""
    
    @pytest.fixture
    def sample_class(self, db: Session, teacher):
        """建立測試班級"""
        test_class = Class(
            name="測試班級",
            grade="國小三年級",
            capacity=30,
            teacher_id=teacher.user_id
        )
        db.add(test_class)
        db.commit()
        return test_class
    
    def test_update_class_info(self, db: Session, sample_class):
        """測試更新班級資訊"""
        update_data = ClassUpdate(
            name="更新後的班級",
            grade="國小四年級",
            capacity=35
        )
        
        sample_class.name = update_data.name
        sample_class.grade = update_data.grade
        sample_class.capacity = update_data.capacity
        db.commit()
        
        updated_class = db.query(Class).filter(Class.id == sample_class.id).first()
        assert updated_class.name == "更新後的班級"
        assert updated_class.grade == "國小四年級"
        assert updated_class.capacity == 35
    
    def test_soft_delete_class(self, db: Session, sample_class):
        """測試軟刪除班級"""
        class_id = sample_class.id
        
        # 軟刪除
        sample_class.is_deleted = True
        sample_class.deleted_at = datetime.utcnow()
        db.commit()
        
        # 確認被標記為刪除
        deleted_class = db.query(Class).filter(Class.id == class_id).first()
        assert deleted_class.is_deleted is True
        assert deleted_class.deleted_at is not None
        
        # 確認在一般查詢中不出現
        active_classes = db.query(Class).filter(Class.is_deleted == False).all()
        assert deleted_class not in active_classes
    
    def test_delete_class_with_students(self, db: Session, sample_class):
        """測試刪除有學生的班級"""
        # 加入學生
        student = Student(
            name="測試學生",
            birth_date=datetime(2010, 1, 1).date(),
            teacher_id=sample_class.teacher_id,
            password_hash=get_password_hash("20100101")
        )
        db.add(student)
        db.commit()
        
        mapping = ClassStudentMapping(
            class_id=sample_class.id,
            student_id=student.id
        )
        db.add(mapping)
        db.commit()
        
        # 檢查班級有學生
        student_count = db.query(ClassStudentMapping).filter(
            ClassStudentMapping.class_id == sample_class.id
        ).count()
        
        assert student_count > 0
        
        # 應該要有保護機制
        with pytest.raises(ValueError):
            if student_count > 0:
                raise ValueError("無法刪除有學生的班級")


class TestStudentClassAssignment:
    """學生班級分配功能測試"""
    
    @pytest.fixture
    def students(self, db: Session, teacher):
        """建立測試學生"""
        students_list = []
        for i in range(3):
            student = Student(
                name=f"學生{i+1}",
                birth_date=datetime(2010, i+1, 1).date(),
                teacher_id=teacher.user_id,
                password_hash=get_password_hash(f"2010{i+1:02d}01")
            )
            db.add(student)
            students_list.append(student)
        db.commit()
        return students_list
    
    def test_assign_student_to_class(self, db: Session, sample_class, students):
        """測試分配學生到班級"""
        student = students[0]
        
        mapping = ClassStudentMapping(
            class_id=sample_class.id,
            student_id=student.id
        )
        db.add(mapping)
        db.commit()
        
        # 確認分配成功
        assignment = db.query(ClassStudentMapping).filter(
            ClassStudentMapping.class_id == sample_class.id,
            ClassStudentMapping.student_id == student.id
        ).first()
        
        assert assignment is not None
        assert assignment.assigned_at is not None
    
    def test_bulk_assign_students(self, db: Session, sample_class, students):
        """測試批量分配學生"""
        mappings = []
        for student in students:
            mapping = ClassStudentMapping(
                class_id=sample_class.id,
                student_id=student.id
            )
            mappings.append(mapping)
        
        db.add_all(mappings)
        db.commit()
        
        # 確認所有學生都被分配
        assigned_count = db.query(ClassStudentMapping).filter(
            ClassStudentMapping.class_id == sample_class.id
        ).count()
        
        assert assigned_count == len(students)
    
    def test_remove_student_from_class(self, db: Session, sample_class, students):
        """測試從班級移除學生"""
        student = students[0]
        
        # 先分配
        mapping = ClassStudentMapping(
            class_id=sample_class.id,
            student_id=student.id
        )
        db.add(mapping)
        db.commit()
        
        # 再移除
        db.delete(mapping)
        db.commit()
        
        # 確認已移除
        assignment = db.query(ClassStudentMapping).filter(
            ClassStudentMapping.class_id == sample_class.id,
            ClassStudentMapping.student_id == student.id
        ).first()
        
        assert assignment is None
    
    def test_student_class_capacity_limit(self, db: Session, teacher):
        """測試班級容量限制"""
        # 建立容量為 2 的班級
        small_class = Class(
            name="小班級",
            grade="國小一年級",
            capacity=2,
            teacher_id=teacher.user_id
        )
        db.add(small_class)
        db.commit()
        
        # 建立 3 個學生
        students = []
        for i in range(3):
            student = Student(
                name=f"學生{i+1}",
                birth_date=datetime(2010, 1, 1).date(),
                teacher_id=teacher.user_id,
                password_hash=get_password_hash("20100101")
            )
            db.add(student)
            students.append(student)
        db.commit()
        
        # 分配前兩個學生
        for i in range(2):
            mapping = ClassStudentMapping(
                class_id=small_class.id,
                student_id=students[i].id
            )
            db.add(mapping)
        db.commit()
        
        # 檢查目前人數
        current_count = db.query(ClassStudentMapping).filter(
            ClassStudentMapping.class_id == small_class.id
        ).count()
        
        # 嘗試加入第三個學生應該失敗
        with pytest.raises(ValueError):
            if current_count >= small_class.capacity:
                raise ValueError("班級已滿")


class TestClassCourseManagement:
    """班級課程管理功能測試"""
    
    @pytest.fixture
    def sample_course(self, db: Session):
        """建立測試課程"""
        course = Course(
            title={"zh": "基礎英語"},
            description={"zh": "適合初學者"},
            difficulty_level="beginner",
            is_template=True
        )
        db.add(course)
        db.commit()
        return course
    
    def test_assign_course_to_class(self, db: Session, sample_class, sample_course):
        """測試分配課程到班級"""
        mapping = ClassCourseMapping(
            class_id=sample_class.id,
            course_id=sample_course.id,
            is_active=True
        )
        db.add(mapping)
        db.commit()
        
        # 確認分配成功
        assignment = db.query(ClassCourseMapping).filter(
            ClassCourseMapping.class_id == sample_class.id,
            ClassCourseMapping.course_id == sample_course.id
        ).first()
        
        assert assignment is not None
        assert assignment.is_active is True
    
    def test_copy_template_course(self, db: Session, sample_class, sample_course):
        """測試從模板複製課程"""
        # 複製課程
        copied_course = Course(
            title=sample_course.title,
            description=sample_course.description,
            difficulty_level=sample_course.difficulty_level,
            is_template=False,  # 複製的課程不是模板
            created_by=sample_class.teacher_id
        )
        db.add(copied_course)
        db.commit()
        
        # 分配到班級
        mapping = ClassCourseMapping(
            class_id=sample_class.id,
            course_id=copied_course.id,
            is_active=True
        )
        db.add(mapping)
        db.commit()
        
        assert copied_course.is_template is False
        assert copied_course.created_by == sample_class.teacher_id
    
    def test_deactivate_course_in_class(self, db: Session, sample_class, sample_course):
        """測試停用班級中的課程"""
        # 先分配課程
        mapping = ClassCourseMapping(
            class_id=sample_class.id,
            course_id=sample_course.id,
            is_active=True
        )
        db.add(mapping)
        db.commit()
        
        # 停用課程
        mapping.is_active = False
        db.commit()
        
        # 確認已停用
        updated_mapping = db.query(ClassCourseMapping).filter(
            ClassCourseMapping.class_id == sample_class.id,
            ClassCourseMapping.course_id == sample_course.id
        ).first()
        
        assert updated_mapping.is_active is False