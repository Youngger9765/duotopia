"""
作業系統 API 測試
測試 Phase 1 & Phase 2 的所有作業相關功能
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from typing import Dict, List
import time

from main import app
from database import get_db
from models import (
    Teacher, Student, Classroom, ClassroomStudent,
    Program, Lesson, Content, ContentType,
    StudentAssignment, AssignmentSubmission, AssignmentStatus
)
from auth import create_access_token, get_password_hash


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """建立測試資料庫 session"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def teacher_token(db_session: Session) -> str:
    """建立測試教師並回傳 token"""
    # 建立或取得測試教師
    teacher = db_session.query(Teacher).filter(
        Teacher.email == "test.teacher@duotopia.com"
    ).first()
    
    if not teacher:
        teacher = Teacher(
            email="test.teacher@duotopia.com",
            password_hash=get_password_hash("test123"),
            name="Test Teacher",
            is_active=True,
            is_demo=True
        )
        db_session.add(teacher)
        db_session.commit()
    
    # 建立 token
    token = create_access_token(
        data={
            "sub": str(teacher.id),
            "email": teacher.email,
            "type": "teacher",
            "name": teacher.name
        },
        expires_delta=timedelta(hours=1)
    )
    
    return token


@pytest.fixture
def student_token(db_session: Session) -> str:
    """建立測試學生並回傳 token"""
    # 建立或取得測試學生
    student = db_session.query(Student).filter(
        Student.email == "test.student@duotopia.local"
    ).first()
    
    if not student:
        student = Student(
            email="test.student@duotopia.local",
            password_hash=get_password_hash("student123"),
            name="Test Student",
            birthdate=datetime(2010, 1, 1).date(),
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
    
    # 建立 token
    token = create_access_token(
        data={
            "sub": str(student.id),
            "email": student.email,
            "type": "student",
            "name": student.name
        },
        expires_delta=timedelta(hours=1)
    )
    
    return token


@pytest.fixture
def test_data(db_session: Session) -> Dict:
    """建立完整的測試資料"""
    # 取得測試教師
    teacher = db_session.query(Teacher).filter(
        Teacher.email == "test.teacher@duotopia.com"
    ).first()
    
    # 建立班級
    classroom = Classroom(
        name="Test Class",
        teacher_id=teacher.id,
        level="A1",
        is_active=True
    )
    db_session.add(classroom)
    
    # 建立學生（使用時間戳避免重複）
    timestamp = int(time.time())
    students = []
    for i in range(3):
        student = Student(
            email=f"student{i}_test_{timestamp}@test.local",
            password_hash=get_password_hash("test123"),
            name=f"Student {i}",
            birthdate=datetime(2010, 1, 1).date(),
            is_active=True
        )
        db_session.add(student)
        students.append(student)
    
    db_session.flush()
    
    # 學生加入班級
    for student in students:
        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student.id,
            is_active=True
        )
        db_session.add(enrollment)
    
    # 建立課程
    program = Program(
        name="Test Program",
        teacher_id=teacher.id,
        classroom_id=classroom.id,
        level="A1",
        is_active=True
    )
    db_session.add(program)
    db_session.flush()
    
    # 建立單元
    lesson = Lesson(
        program_id=program.id,
        name="Test Lesson",
        order_index=1
    )
    db_session.add(lesson)
    db_session.flush()
    
    # 建立 Content
    content = Content(
        lesson_id=lesson.id,
        type=ContentType.READING_ASSESSMENT,
        title="Test Content",
        items=[
            {"text": "Hello", "translation": "你好"},
            {"text": "World", "translation": "世界"}
        ],
        level="A1"
    )
    db_session.add(content)
    
    db_session.commit()
    
    return {
        "teacher": teacher,
        "classroom": classroom,
        "students": students,
        "program": program,
        "lesson": lesson,
        "content": content
    }


class TestPhase1Assignments:
    """Phase 1: 基礎指派功能測試"""
    
    def test_create_assignment_for_whole_class(
        self, client: TestClient, teacher_token: str, test_data: Dict
    ):
        """測試指派作業給全班"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = client.post(
            "/api/assignments/create",
            json={
                "content_id": test_data["content"].id,
                "classroom_id": test_data["classroom"].id,
                "student_ids": [],  # 空陣列表示全班
                "title": "Test Assignment - Whole Class",
                "instructions": "Complete this assignment",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat()
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == len(test_data["students"])
    
    def test_create_assignment_for_specific_students(
        self, client: TestClient, teacher_token: str, test_data: Dict
    ):
        """測試指派作業給特定學生"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        student_ids = [test_data["students"][0].id, test_data["students"][1].id]
        
        response = client.post(
            "/api/assignments/create",
            json={
                "content_id": test_data["content"].id,
                "classroom_id": test_data["classroom"].id,
                "student_ids": student_ids,
                "title": "Test Assignment - Specific Students",
                "instructions": "Only for selected students",
                "due_date": (datetime.now() + timedelta(days=5)).isoformat()
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
    
    def test_get_classroom_students(
        self, client: TestClient, teacher_token: str, test_data: Dict
    ):
        """測試取得班級學生列表"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = client.get(
            f"/api/classrooms/{test_data['classroom'].id}/students",
            headers=headers
        )
        
        assert response.status_code == 200
        students = response.json()
        assert len(students) == len(test_data["students"])
    
    def test_get_available_contents(
        self, client: TestClient, teacher_token: str, test_data: Dict
    ):
        """測試取得可用的 Content 列表"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = client.get(
            f"/api/contents?classroom_id={test_data['classroom'].id}",
            headers=headers
        )
        
        assert response.status_code == 200
        contents = response.json()
        assert len(contents) >= 1
        assert contents[0]["title"] == "Test Content"


class TestPhase2Assignments:
    """Phase 2: 作業列表管理測試"""
    
    def test_get_teacher_assignments(
        self, client: TestClient, teacher_token: str, test_data: Dict, db_session: Session
    ):
        """測試教師取得作業列表"""
        # 先建立一些作業
        for student in test_data["students"]:
            assignment = StudentAssignment(
                student_id=student.id,
                content_id=test_data["content"].id,
                classroom_id=test_data["classroom"].id,
                title="Test Assignment",
                status=AssignmentStatus.NOT_STARTED,
                due_date=datetime.now() + timedelta(days=7)
            )
            db_session.add(assignment)
        db_session.commit()
        
        # 測試 API
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = client.get("/api/assignments/teacher", headers=headers)
        
        assert response.status_code == 200
        assignments = response.json()
        assert len(assignments) >= 1
        assert assignments[0]["total_students"] == 3
    
    def test_get_student_assignments(
        self, client: TestClient, student_token: str, db_session: Session
    ):
        """測試學生取得自己的作業列表"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = client.get("/api/assignments/student", headers=headers)
        
        assert response.status_code == 200
        assignments = response.json()
        assert isinstance(assignments, list)
    
    def test_submit_assignment(
        self, client: TestClient, student_token: str, db_session: Session
    ):
        """測試提交作業"""
        # 先建立一個作業
        student = db_session.query(Student).filter(
            Student.email == "test.student@duotopia.local"
        ).first()
        
        # 確保有 Content
        content = db_session.query(Content).first()
        if not content:
            # 建立測試 Content
            lesson = db_session.query(Lesson).first()
            content = Content(
                lesson_id=lesson.id,
                type=ContentType.READING_ASSESSMENT,
                title="Test Content for Submission",
                items=[{"text": "Test"}]
            )
            db_session.add(content)
            db_session.flush()
        
        assignment = StudentAssignment(
            student_id=student.id,
            content_id=content.id,
            classroom_id=1,  # 假設有班級 ID 1
            title="Test Assignment for Submission",
            status=AssignmentStatus.NOT_STARTED
        )
        db_session.add(assignment)
        db_session.commit()
        
        # 測試提交
        headers = {"Authorization": f"Bearer {student_token}"}
        submission_data = {
            "audio_urls": ["test_audio_1.mp3", "test_audio_2.mp3"],
            "completed_at": datetime.now().isoformat()
        }
        
        response = client.post(
            f"/api/assignments/{assignment.id}/submit",
            json=submission_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "提交成功" in data["message"]
    
    def test_get_assignment_detail(
        self, client: TestClient, student_token: str, db_session: Session
    ):
        """測試取得作業詳細資訊"""
        # 取得學生
        student = db_session.query(Student).filter(
            Student.email == "test.student@duotopia.local"
        ).first()
        
        # 建立作業
        content = db_session.query(Content).first()
        assignment = StudentAssignment(
            student_id=student.id,
            content_id=content.id,
            classroom_id=1,
            title="Test Assignment Detail",
            status=AssignmentStatus.IN_PROGRESS
        )
        db_session.add(assignment)
        db_session.commit()
        
        # 測試 API
        headers = {"Authorization": f"Bearer {student_token}"}
        response = client.get(
            f"/api/assignments/{assignment.id}/detail",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "assignment" in data
        assert "content" in data
        assert data["assignment"]["title"] == "Test Assignment Detail"
    
    def test_filter_assignments_by_status(
        self, client: TestClient, student_token: str
    ):
        """測試按狀態篩選作業"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = client.get(
            "/api/assignments/student?status=NOT_STARTED",
            headers=headers
        )
        
        assert response.status_code == 200
        assignments = response.json()
        assert isinstance(assignments, list)
        # 所有回傳的作業都應該是 NOT_STARTED 狀態
        for assignment in assignments:
            assert assignment["status"] == "NOT_STARTED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])