"""
Unit Tests for Content CRUD API Endpoints
測試 Content 的 Create, Read, Update, Delete API 端點
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Teacher, Program, Classroom, Lesson
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# 密碼雜湊
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 測試資料庫連接
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_content_crud.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)


def override_get_db():
    """Override database dependency for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup test database before tests"""
    from models import Base

    Base.metadata.create_all(bind=engine)

    # 創建測試老師
    db = TestingSessionLocal()
    teacher = Teacher(
        email="test@teacher.com",
        name="Test Teacher",
        password_hash=pwd_context.hash("test123"),
        email_verified=True,
    )
    db.add(teacher)

    # 創建測試班級
    classroom = Classroom(name="Test Classroom", teacher_id=1, grade="Grade 1")
    db.add(classroom)

    # 創建測試課程
    program = Program(
        name="Test Program",
        description="Test Program Description",
        teacher_id=1,
        classroom_id=1,
    )
    db.add(program)

    # 創建測試單元
    lesson = Lesson(
        name="Test Lesson",
        description="Test Lesson Description",
        program_id=1,
        order_index=1,
        estimated_minutes=30,
    )
    db.add(lesson)

    db.commit()
    db.close()

    yield

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_token():
    """Get authentication token for testing"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": "test@teacher.com", "password": "test123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestContentCRUD:
    """測試 Content CRUD API"""

    def test_create_content(self, auth_token):
        """測試創建 Content (CREATE)"""
        response = client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Test Content",
                "items": [
                    {"text": "Hello", "translation": "你好"},
                    {"text": "World", "translation": "世界"},
                ],
                "target_wpm": 100,
                "target_accuracy": 95.0,
                "order_index": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Content"
        assert data["target_wpm"] == 100
        assert data["target_accuracy"] == 95.0
        assert len(data["items"]) == 2
        assert "id" in data

    def test_read_content(self, auth_token):
        """測試讀取 Content (READ)"""
        # 先創建一個 content
        create_response = client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Read Test Content",
                "items": [{"text": "Test", "translation": "測試"}],
                "target_wpm": 120,
                "target_accuracy": 90.0,
                "order_index": 1,
            },
        )
        content_id = create_response.json()["id"]

        # 讀取 content
        response = client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == "Read Test Content"
        assert data["target_wpm"] == 120

    def test_update_content(self, auth_token):
        """測試更新 Content (UPDATE)"""
        # 先創建一個 content
        create_response = client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Original Content",
                "items": [{"text": "Original", "translation": "原始"}],
                "target_wpm": 100,
                "target_accuracy": 90.0,
                "order_index": 1,
            },
        )
        content_id = create_response.json()["id"]

        # 更新 content
        response = client.put(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Updated Content",
                "target_wpm": 150,
                "target_accuracy": 95.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Content"
        assert data["target_wpm"] == 150
        assert data["target_accuracy"] == 95.0

    def test_delete_content(self, auth_token):
        """測試刪除 Content (DELETE) - 軟刪除"""
        # 先創建一個 content
        create_response = client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Delete Test",
                "items": [{"text": "Delete", "translation": "刪除"}],
                "target_wpm": 100,
                "target_accuracy": 90.0,
                "order_index": 1,
            },
        )
        content_id = create_response.json()["id"]

        # 刪除 content
        response = client.delete(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200

        # 驗證軟刪除：嘗試讀取應該返回 404
        get_response = client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_response.status_code == 404

        # 驗證軟刪除：嘗試更新應該返回 404
        update_response = client.put(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Should Not Work",
                "target_wpm": 100,
                "target_accuracy": 90.0,
            },
        )
        assert update_response.status_code == 404

    def test_cannot_create_content_in_deleted_lesson(self, auth_token):
        """測試無法在已刪除的 Lesson 中創建 Content"""
        # 創建一個新 lesson
        db = TestingSessionLocal()
        lesson = Lesson(
            name="To Delete Lesson",
            description="Will be deleted",
            program_id=1,
            order_index=2,
            estimated_minutes=30,
        )
        db.add(lesson)
        db.commit()
        lesson_id = lesson.id
        db.close()

        # 刪除 lesson
        client.delete(
            f"/api/teachers/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # 嘗試在已刪除的 lesson 中創建 content
        response = client.post(
            f"/api/teachers/lessons/{lesson_id}/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "Should Not Work",
                "items": [{"text": "Test", "translation": "測試"}],
                "target_wpm": 100,
                "target_accuracy": 90.0,
                "order_index": 1,
            },
        )

        assert response.status_code == 404

    def test_unauthorized_access(self):
        """測試未授權存取"""
        # 沒有 token
        response = client.post(
            "/api/teachers/lessons/1/contents",
            json={
                "title": "Test",
                "items": [{"text": "Test", "translation": "測試"}],
                "target_wpm": 100,
                "target_accuracy": 90.0,
                "order_index": 1,
            },
        )
        assert response.status_code == 401

        # 錯誤的 token
        response = client.get(
            "/api/teachers/contents/1",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
