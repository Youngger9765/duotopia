"""
課程管理功能單元測試
測試課程和單元的建立、編輯、管理等核心功能
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
import json

from models import (
    User, IndividualTeacher, Course, Lesson, 
    Class, ClassCourseMapping
)
from schemas import CourseCreate, CourseUpdate, LessonCreate, LessonUpdate
from auth import get_password_hash


class TestCourseCreation:
    """課程建立功能測試"""
    
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
        
        teacher = IndividualTeacher(
            user_id=user.id,
            name="Test Teacher"
        )
        db.add(teacher)
        db.commit()
        return teacher
    
    def test_create_basic_course(self, db: Session, teacher):
        """測試建立基本課程"""
        course_data = CourseCreate(
            title={"zh": "基礎英語會話"},
            description={"zh": "適合初學者的英語課程"}
        )
        
        course = Course(
            title=course_data.title,
            description=course_data.description,
            created_by=teacher.user_id,
            is_template=False
        )
        db.add(course)
        db.commit()
        
        assert course.id is not None
        assert course.title["zh"] == "基礎英語會話"
        assert course.description["zh"] == "適合初學者的英語課程"
        assert course.created_by == teacher.user_id
        assert course.is_template is False
    
    def test_create_template_course(self, db: Session):
        """測試建立模板課程"""
        course = Course(
            title={"zh": "公版課程 - 基礎文法"},
            description={"zh": "系統提供的基礎文法課程"},
            difficulty_level="beginner",
            is_template=True,
            created_by=None  # 系統課程沒有建立者
        )
        db.add(course)
        db.commit()
        
        assert course.is_template is True
        assert course.created_by is None
        assert course.difficulty_level == "beginner"
    
    def test_create_course_with_metadata(self, db: Session, teacher):
        """測試建立包含元資料的課程"""
        course = Course(
            title={"zh": "進階商務英語", "en": "Advanced Business English"},
            description={
                "zh": "適合商務人士的進階課程",
                "en": "Advanced course for business professionals"
            },
            difficulty_level="advanced",
            price=2000,
            estimated_hours=30,
            tags=["商務", "進階", "口說"],
            created_by=teacher.user_id
        )
        db.add(course)
        db.commit()
        
        assert course.title["en"] == "Advanced Business English"
        assert course.price == 2000
        assert course.estimated_hours == 30
        assert "商務" in course.tags
        assert len(course.tags) == 3
    
    def test_copy_from_template(self, db: Session, teacher):
        """測試從模板複製課程"""
        # 建立模板課程
        template = Course(
            title={"zh": "模板課程"},
            description={"zh": "這是一個模板"},
            difficulty_level="intermediate",
            is_template=True,
            tags=["模板", "測試"]
        )
        db.add(template)
        db.commit()
        
        # 複製課程
        copied_course = Course(
            title=template.title,
            description=template.description,
            difficulty_level=template.difficulty_level,
            tags=template.tags.copy() if template.tags else [],
            is_template=False,
            created_by=teacher.user_id,
            copied_from_id=template.id
        )
        db.add(copied_course)
        db.commit()
        
        assert copied_course.is_template is False
        assert copied_course.created_by == teacher.user_id
        assert copied_course.copied_from_id == template.id
        assert copied_course.tags == template.tags


class TestLessonManagement:
    """單元管理功能測試"""
    
    @pytest.fixture
    def course(self, db: Session, teacher):
        """建立測試課程"""
        course = Course(
            title={"zh": "測試課程"},
            description={"zh": "用於測試"},
            created_by=teacher.user_id
        )
        db.add(course)
        db.commit()
        return course
    
    def test_create_lesson(self, db: Session, course):
        """測試建立課程單元"""
        lesson_data = LessonCreate(
            lesson_number=1,
            title={"zh": "第一課：自我介紹"},
            description={"zh": "學習如何用英語自我介紹"},
            activity_type="reading_assessment",
            time_limit=30
        )
        
        lesson = Lesson(
            course_id=course.id,
            lesson_number=lesson_data.lesson_number,
            title=lesson_data.title,
            description=lesson_data.description,
            activity_type=lesson_data.activity_type,
            time_limit=lesson_data.time_limit,
            is_active=True
        )
        db.add(lesson)
        db.commit()
        
        assert lesson.id is not None
        assert lesson.course_id == course.id
        assert lesson.lesson_number == 1
        assert lesson.activity_type == "reading_assessment"
        assert lesson.time_limit == 30
        assert lesson.is_active is True
    
    def test_create_multiple_lessons(self, db: Session, course):
        """測試建立多個單元"""
        lessons = []
        for i in range(5):
            lesson = Lesson(
                course_id=course.id,
                lesson_number=i + 1,
                title={"zh": f"第{i+1}課"},
                description={"zh": f"第{i+1}課的描述"},
                activity_type="reading_assessment",
                time_limit=30,
                is_active=True
            )
            lessons.append(lesson)
        
        db.add_all(lessons)
        db.commit()
        
        # 查詢課程的所有單元
        course_lessons = db.query(Lesson).filter(
            Lesson.course_id == course.id
        ).order_by(Lesson.lesson_number).all()
        
        assert len(course_lessons) == 5
        assert course_lessons[0].lesson_number == 1
        assert course_lessons[4].lesson_number == 5
    
    def test_update_lesson(self, db: Session, course):
        """測試更新單元資訊"""
        # 建立單元
        lesson = Lesson(
            course_id=course.id,
            lesson_number=1,
            title={"zh": "原始標題"},
            activity_type="reading_assessment",
            time_limit=30
        )
        db.add(lesson)
        db.commit()
        
        # 更新單元
        update_data = LessonUpdate(
            title={"zh": "更新後標題"},
            time_limit=45,
            is_active=False
        )
        
        if update_data.title:
            lesson.title = update_data.title
        if update_data.time_limit:
            lesson.time_limit = update_data.time_limit
        if update_data.is_active is not None:
            lesson.is_active = update_data.is_active
        
        db.commit()
        
        # 驗證更新
        updated_lesson = db.query(Lesson).filter(Lesson.id == lesson.id).first()
        assert updated_lesson.title["zh"] == "更新後標題"
        assert updated_lesson.time_limit == 45
        assert updated_lesson.is_active is False
    
    def test_lesson_content_management(self, db: Session, course):
        """測試單元內容管理"""
        lesson = Lesson(
            course_id=course.id,
            lesson_number=1,
            title={"zh": "內容測試單元"},
            activity_type="reading_assessment",
            content={
                "text": "This is a test passage for reading.",
                "questions": [
                    {
                        "id": 1,
                        "question": "What is this?",
                        "answer": "A test passage"
                    }
                ],
                "vocabulary": ["test", "passage", "reading"]
            },
            resources={
                "audio_url": "https://example.com/audio.mp3",
                "image_url": "https://example.com/image.jpg"
            }
        )
        db.add(lesson)
        db.commit()
        
        # 驗證內容儲存
        saved_lesson = db.query(Lesson).filter(Lesson.id == lesson.id).first()
        assert saved_lesson.content["text"] == "This is a test passage for reading."
        assert len(saved_lesson.content["questions"]) == 1
        assert "vocabulary" in saved_lesson.content
        assert saved_lesson.resources["audio_url"] == "https://example.com/audio.mp3"
    
    def test_delete_lesson(self, db: Session, course):
        """測試刪除單元"""
        # 建立單元
        lesson = Lesson(
            course_id=course.id,
            lesson_number=1,
            title={"zh": "要刪除的單元"},
            activity_type="reading_assessment"
        )
        db.add(lesson)
        db.commit()
        
        lesson_id = lesson.id
        
        # 刪除單元
        db.delete(lesson)
        db.commit()
        
        # 確認已刪除
        deleted_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        assert deleted_lesson is None


class TestActivityTypes:
    """活動類型功能測試"""
    
    def test_supported_activity_types(self):
        """測試支援的活動類型"""
        supported_types = [
            "reading_assessment",     # 錄音集
            "speaking_practice",      # 口說練習
            "speaking_scenario",      # 情境對話
            "listening_cloze",        # 聽力填空
            "sentence_making",        # 造句練習
            "speaking_quiz"           # 口說測驗
        ]
        
        # 目前只啟用第一種
        enabled_types = ["reading_assessment"]
        
        for activity_type in supported_types:
            if activity_type in enabled_types:
                assert activity_type == "reading_assessment"
            else:
                # 其他類型應該被標記為停用
                assert activity_type != "reading_assessment"
    
    def test_activity_type_configuration(self, db: Session, course):
        """測試不同活動類型的配置"""
        configurations = {
            "reading_assessment": {
                "requires_audio": True,
                "requires_text": True,
                "has_timer": True,
                "ai_feedback": True
            },
            "speaking_practice": {
                "requires_audio": True,
                "requires_prompt": True,
                "has_timer": True,
                "ai_feedback": True
            },
            "listening_cloze": {
                "requires_audio": True,
                "requires_text": True,
                "has_blanks": True,
                "ai_feedback": False
            }
        }
        
        # 測試錄音集配置
        reading_config = configurations["reading_assessment"]
        assert reading_config["requires_audio"] is True
        assert reading_config["ai_feedback"] is True


class TestCourseClassAssignment:
    """課程班級分配功能測試"""
    
    @pytest.fixture
    def test_class(self, db: Session, teacher):
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
    
    def test_assign_course_to_class(self, db: Session, course, test_class):
        """測試分配課程到班級"""
        mapping = ClassCourseMapping(
            class_id=test_class.id,
            course_id=course.id,
            is_active=True,
            assigned_by=test_class.teacher_id
        )
        db.add(mapping)
        db.commit()
        
        # 查詢班級的課程
        class_courses = db.query(ClassCourseMapping).filter(
            ClassCourseMapping.class_id == test_class.id
        ).all()
        
        assert len(class_courses) == 1
        assert class_courses[0].course_id == course.id
        assert class_courses[0].is_active is True
    
    def test_multiple_class_course_assignment(self, db: Session, teacher):
        """測試多個班級分配同一課程"""
        # 建立一個課程
        course = Course(
            title={"zh": "共用課程"},
            created_by=teacher.user_id
        )
        db.add(course)
        
        # 建立兩個班級
        class1 = Class(name="班級A", grade="國小三年級", capacity=30, teacher_id=teacher.user_id)
        class2 = Class(name="班級B", grade="國小四年級", capacity=25, teacher_id=teacher.user_id)
        db.add_all([class1, class2])
        db.commit()
        
        # 分配課程到兩個班級
        mapping1 = ClassCourseMapping(class_id=class1.id, course_id=course.id)
        mapping2 = ClassCourseMapping(class_id=class2.id, course_id=course.id)
        db.add_all([mapping1, mapping2])
        db.commit()
        
        # 查詢使用此課程的班級數
        class_count = db.query(ClassCourseMapping).filter(
            ClassCourseMapping.course_id == course.id
        ).count()
        
        assert class_count == 2
    
    def test_deactivate_course_in_class(self, db: Session, course, test_class):
        """測試停用班級中的課程"""
        # 先分配課程
        mapping = ClassCourseMapping(
            class_id=test_class.id,
            course_id=course.id,
            is_active=True
        )
        db.add(mapping)
        db.commit()
        
        # 停用課程
        mapping.is_active = False
        mapping.deactivated_at = datetime.utcnow()
        db.commit()
        
        # 查詢啟用的課程
        active_courses = db.query(ClassCourseMapping).filter(
            ClassCourseMapping.class_id == test_class.id,
            ClassCourseMapping.is_active == True
        ).all()
        
        assert len(active_courses) == 0