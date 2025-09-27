"""
Test Data Factory
測試資料工廠 - 簡化測試資料建立
完全不影響生產代碼，只用於測試
"""

from datetime import date
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    Assignment,
    StudentAssignment,
    StudentContentProgress,
    AssignmentContent,
    AssignmentStatus,
)


class TestDataFactory:
    """測試資料工廠，用於快速建立測試所需的完整資料鏈"""

    @staticmethod
    def create_teacher(
        db: Session,
        name: str = "Test Teacher",
        email: str = "teacher@test.com",
        password_hash: str = "test_hash",
    ) -> Teacher:
        """建立測試教師"""
        teacher = Teacher(name=name, email=email, password_hash=password_hash)
        db.add(teacher)
        db.commit()
        return teacher

    @staticmethod
    def create_classroom(
        db: Session, teacher: Teacher, name: str = "Test Classroom"
    ) -> Classroom:
        """建立測試班級"""
        classroom = Classroom(name=name, teacher_id=teacher.id)
        db.add(classroom)
        db.commit()
        return classroom

    @staticmethod
    def create_student(
        db: Session,
        name: str = "Test Student",
        email: str = "student@test.com",
        student_number: str = "S001",
        classroom: Optional[Classroom] = None,
    ) -> Student:
        """建立測試學生"""
        student = Student(
            name=name,
            email=email,
            student_number=student_number,
            password_hash="student_hash",
            birthdate=date(2000, 1, 1),
        )
        db.add(student)
        db.commit()

        # 如果提供了班級，建立關聯
        if classroom:
            classroom_student = ClassroomStudent(
                student_id=student.id, classroom_id=classroom.id
            )
            db.add(classroom_student)
            db.commit()

        return student

    @staticmethod
    def create_program(
        db: Session, teacher: Teacher, name: str = "Test Program"
    ) -> Program:
        """建立測試課程計畫"""
        program = Program(
            name=name, description="Test program description", teacher_id=teacher.id
        )
        db.add(program)
        db.commit()
        return program

    @staticmethod
    def create_lesson(
        db: Session, program: Program, name: str = "Test Lesson"
    ) -> Lesson:
        """建立測試課程單元"""
        lesson = Lesson(
            name=name, description="Test lesson description", program_id=program.id
        )
        db.add(lesson)
        db.commit()
        return lesson

    @staticmethod
    def create_content(
        db: Session,
        lesson: Lesson,
        title: str = "Test Content",
        items: Optional[list] = None,
    ) -> Content:
        """建立測試內容"""
        if items is None:
            items = [{"text": "Hello, how are you?", "translation": "你好，你好嗎？"}]

        content = Content(
            lesson_id=lesson.id,
            title=title,
            type="READING_ASSESSMENT",
        )
        db.add(content)
        db.commit()

        # 建立 ContentItem 關聯物件
        from models import ContentItem

        for idx, item in enumerate(items):
            content_item = ContentItem(
                content_id=content.id,
                text=item.get("text", ""),
                translation=item.get("translation", ""),
                audio_url=item.get("audio_url", ""),
                order_index=idx,
            )
            db.add(content_item)
        db.commit()

        return content

    @staticmethod
    def create_assignment(
        db: Session,
        classroom: Classroom,
        teacher: Teacher,
        title: str = "Test Assignment",
    ) -> Assignment:
        """建立測試作業"""
        assignment = Assignment(
            title=title,
            description="Test assignment description",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
        )
        db.add(assignment)
        db.commit()
        return assignment

    @staticmethod
    def create_student_assignment(
        db: Session,
        student: Student,
        assignment: Assignment,
        classroom: Classroom,
        status: AssignmentStatus = AssignmentStatus.SUBMITTED,
    ) -> StudentAssignment:
        """建立測試學生作業"""
        student_assignment = StudentAssignment(
            student_id=student.id,
            assignment_id=assignment.id,
            classroom_id=classroom.id,
            title=assignment.title,
            status=status,
        )
        db.add(student_assignment)
        db.commit()
        return student_assignment

    @staticmethod
    def create_full_assignment_chain(
        db: Session,
        with_ai_scores: bool = False,
        teacher_email: str = "teacher@test.com",
        student_email: str = "student@test.com",
        student_number: str = "S001",
        content_items: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        建立完整的作業資料鏈
        包含: Teacher -> Classroom -> Student -> Program -> Lesson -> Content -> Assignment -> StudentAssignment

        Args:
            db: 資料庫session
            with_ai_scores: 是否包含AI評分資料

        Returns:
            包含所有建立物件的字典
        """
        # 建立基礎人員
        teacher = TestDataFactory.create_teacher(db, email=teacher_email)
        classroom = TestDataFactory.create_classroom(db, teacher)
        student = TestDataFactory.create_student(
            db, classroom=classroom, email=student_email, student_number=student_number
        )

        # 建立課程結構
        program = TestDataFactory.create_program(db, teacher)
        lesson = TestDataFactory.create_lesson(db, program)

        # 使用自定義的 content_items 或預設值
        if content_items is None:
            content_items = [{"text": "Test text", "translation": "測試文字"}]

        content = TestDataFactory.create_content(db, lesson, items=content_items)

        # 建立作業
        assignment = TestDataFactory.create_assignment(db, classroom, teacher)

        # 連結內容到作業
        assignment_content = AssignmentContent(
            assignment_id=assignment.id, content_id=content.id, order_index=0
        )
        db.add(assignment_content)
        db.commit()

        # 建立學生作業
        student_assignment = TestDataFactory.create_student_assignment(
            db, student, assignment, classroom
        )

        # 建立進度記錄
        ai_scores_data = None
        if with_ai_scores:
            ai_scores_data = {
                "accuracy_score": 85.5,
                "fluency_score": 78.2,
                "completeness_score": 92.0,
                "pronunciation_score": 88.7,
                "word_details": [
                    {"word": "Hello", "accuracy_score": 95.0, "error_type": None},
                    {
                        "word": "how",
                        "accuracy_score": 82.5,
                        "error_type": "slight_mispronunciation",
                    },
                    {"word": "are", "accuracy_score": 88.0, "error_type": None},
                    {"word": "you", "accuracy_score": 90.5, "error_type": None},
                ],
            }

        # 建立 StudentItemProgress（新系統）而非 StudentContentProgress
        from models import StudentItemProgress

        item_progress = None
        # 獲取第一個 ContentItem
        content_item = content.content_items[0] if content.content_items else None

        if content_item:
            # 建立 StudentItemProgress 記錄
            import json

            item_progress = StudentItemProgress(
                student_assignment_id=student_assignment.id,
                content_item_id=content_item.id,
                recording_url="https://storage.googleapis.com/test-bucket/recording.webm",
                ai_feedback=json.dumps(ai_scores_data)
                if ai_scores_data
                else None,  # 轉換為 JSON 字串
                status="SUBMITTED",
            )
            db.add(item_progress)
            db.commit()

        # 為了相容性，也建立舊的 StudentContentProgress（某些測試可能仍需要）
        progress = StudentContentProgress(
            student_assignment_id=student_assignment.id,
            content_id=content.id,
            order_index=0,
            response_data={
                "audio_url": "https://storage.googleapis.com/test-bucket/recording.webm",
                "student_answer": "Hello how are you",
                "transcript": "Hello how are you",
            },
            ai_scores=ai_scores_data,
            status=AssignmentStatus.SUBMITTED,
        )
        db.add(progress)
        db.commit()

        return {
            "teacher": teacher,
            "classroom": classroom,
            "student": student,
            "program": program,
            "lesson": lesson,
            "content": content,
            "assignment": assignment,
            "assignment_content": assignment_content,
            "student_assignment": student_assignment,
            "progress": progress,
        }

    @staticmethod
    def cleanup_test_data(db: Session, data: Dict[str, Any]):
        """
        清理測試資料（反向順序刪除）
        用於測試結束後的清理工作
        """
        # 反向順序刪除，避免外鍵約束問題
        delete_order = [
            "progress",
            "student_assignment",
            "assignment_content",
            "assignment",
            "content",
            "lesson",
            "program",
            "student",
            "classroom",
            "teacher",
        ]

        for key in delete_order:
            if key in data and data[key]:
                db.delete(data[key])

        db.commit()
