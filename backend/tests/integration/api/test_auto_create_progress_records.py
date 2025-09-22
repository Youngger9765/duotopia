"""
測試當學生訪問作業時，自動創建缺失的進度記錄功能

場景：
1. 學生被加入到已存在的作業，但沒有 StudentContentProgress 和 StudentItemProgress
2. 當學生第一次訪問作業時，系統應該自動創建這些記錄
3. 確保學生看到正確的作業內容，而不是預設內容
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
from models import (
    Teacher,
    Classroom,
    Student,
    ClassroomStudent,
    Program,
    Lesson,
    Assignment,
    AssignmentContent,
    Content,
    ContentItem,
    StudentAssignment,
    StudentContentProgress,
    StudentItemProgress,
    AssignmentStatus,
)
from auth import create_access_token, get_password_hash


@pytest.fixture
def db_session():
    """創建測試用的記憶體資料庫"""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """創建測試客戶端"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def setup_test_data(db_session):
    """設置測試資料 - 模擬 StudentAssignment 321 的情況"""

    # 創建老師
    teacher = Teacher(
        id=1,
        email="teacher@test.com",
        name="Test Teacher",
        password_hash=get_password_hash("password"),
    )
    db_session.add(teacher)

    # 創建教室
    classroom = Classroom(
        id=4, name="Test Class", teacher_id=1, created_at=datetime.now(timezone.utc)
    )
    db_session.add(classroom)

    # 創建學生
    student = Student(
        id=29,
        student_number="71201",
        name="Test Student",
        email="student@test.com",
        password_hash=get_password_hash("pwd71201"),
        birthdate=datetime(2010, 1, 1).date(),
        is_active=True,
    )
    db_session.add(student)

    # 加入學生到教室
    classroom_student = ClassroomStudent(classroom_id=4, student_id=29)
    db_session.add(classroom_student)

    # 創建 Program (課程)
    program = Program(id=1, name="Test Program", teacher_id=1, classroom_id=4)
    db_session.add(program)

    # 創建 Lesson (課程單元)
    lesson = Lesson(id=1, program_id=1, name="Test Lesson")
    db_session.add(lesson)

    # 創建內容
    content = Content(id=27, lesson_id=1, title="單字", type="READING_ASSESSMENT")
    db_session.add(content)

    # 創建內容項目
    items_data = [
        {"id": 117, "text": "cousin", "translation": "表親"},
        {"id": 118, "text": "beautiful", "translation": "美麗的"},
        {"id": 119, "text": "handsome", "translation": "英俊的"},
        {"id": 120, "text": "smart", "translation": "聰明的"},
    ]

    for idx, item_data in enumerate(items_data):
        item = ContentItem(
            id=item_data["id"],
            content_id=27,
            text=item_data["text"],
            translation=item_data["translation"],
            order_index=idx,
        )
        db_session.add(item)

    # 創建作業
    assignment = Assignment(
        id=31,
        classroom_id=4,
        title="Test Assignment",
        description="Test",
        teacher_id=1,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(assignment)

    # 創建作業內容關聯
    assignment_content = AssignmentContent(
        id=37, assignment_id=31, content_id=27, order_index=1
    )
    db_session.add(assignment_content)

    # 創建 StudentAssignment - 但故意不創建 progress 記錄
    # 模擬 patch_assignment 的 bug 情況
    student_assignment = StudentAssignment(
        id=321,
        student_id=29,
        assignment_id=31,
        classroom_id=4,
        title="Test Assignment",
        status=AssignmentStatus.NOT_STARTED,
        assigned_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(student_assignment)

    # 重要：不創建任何 StudentContentProgress 和 StudentItemProgress！
    # 這就是 bug 的情況

    db_session.commit()

    return {
        "student": student,
        "student_assignment": student_assignment,
        "content": content,
        "items": items_data,
    }


def test_auto_create_progress_records_when_missing(client, setup_test_data):
    """測試：當學生訪問缺少進度記錄的作業時，系統會自動創建"""

    # 準備學生的 token
    student = setup_test_data["student"]
    token = create_access_token(data={"sub": str(student.id), "type": "student"})

    # 學生訪問作業活動 API
    response = client.get(
        "/api/students/assignments/321/activities",
        headers={"Authorization": f"Bearer {token}"},
    )

    # 驗證回應成功
    assert response.status_code == 200
    data = response.json()

    # 驗證返回的是正確的作業內容，不是預設內容
    assert "activities" in data
    assert len(data["activities"]) > 0

    # 檢查第一個活動的內容
    first_activity = data["activities"][0]
    assert "items" in first_activity
    assert len(first_activity["items"]) == 4  # 應該有 4 個單字

    # 驗證不是預設的 "quick brown fox" 內容
    items = first_activity["items"]
    item_texts = [item["text"] for item in items]
    assert "quick" not in " ".join(item_texts).lower()
    assert "brown" not in " ".join(item_texts).lower()
    assert "fox" not in " ".join(item_texts).lower()

    # 驗證是正確的內容
    assert "cousin" in item_texts
    assert "beautiful" in item_texts
    assert "handsome" in item_texts
    assert "smart" in item_texts


def test_progress_records_are_actually_created(client, db_session, setup_test_data):
    """測試：確認進度記錄真的被創建到資料庫"""

    # 準備學生的 token
    student = setup_test_data["student"]
    token = create_access_token(data={"sub": str(student.id), "type": "student"})

    # 訪問 API 前，確認沒有進度記錄
    content_progress_before = (
        db_session.query(StudentContentProgress)
        .filter_by(student_assignment_id=321)
        .count()
    )
    item_progress_before = (
        db_session.query(StudentItemProgress)
        .filter_by(student_assignment_id=321)
        .count()
    )

    assert content_progress_before == 0
    assert item_progress_before == 0

    # 學生訪問作業活動 API
    response = client.get(
        "/api/students/assignments/321/activities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    # 訪問 API 後，確認進度記錄被創建
    content_progress_after = (
        db_session.query(StudentContentProgress)
        .filter_by(student_assignment_id=321)
        .count()
    )
    item_progress_after = (
        db_session.query(StudentItemProgress)
        .filter_by(student_assignment_id=321)
        .count()
    )

    assert content_progress_after == 1  # 應該創建 1 個 content progress
    assert item_progress_after == 4  # 應該創建 4 個 item progress (4個單字)


def test_existing_progress_records_not_duplicated(client, db_session, setup_test_data):
    """測試：如果進度記錄已存在，不會重複創建"""

    # 先手動創建一些進度記錄
    content_progress = StudentContentProgress(
        student_assignment_id=321, content_id=27, status=AssignmentStatus.IN_PROGRESS
    )
    db_session.add(content_progress)
    db_session.commit()

    # 準備學生的 token
    student = setup_test_data["student"]
    token = create_access_token(data={"sub": str(student.id), "type": "student"})

    # 學生訪問作業活動 API
    response = client.get(
        "/api/students/assignments/321/activities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    # 確認沒有重複創建
    content_progress_count = (
        db_session.query(StudentContentProgress)
        .filter_by(student_assignment_id=321)
        .count()
    )

    assert content_progress_count == 1  # 仍然只有 1 個，沒有重複創建


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
