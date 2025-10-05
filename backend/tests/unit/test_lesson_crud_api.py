"""
Unit Tests for Lesson CRUD API Endpoints
測試 Lesson 的 Create, Read, Update, Delete API 端點
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Teacher, Program, Classroom
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# 密碼雜湊
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 測試資料庫連接
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_lesson_crud.db"
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


class TestLessonCRUD:
    """測試 Lesson CRUD API"""

    def test_create_lesson(self, auth_token):
        """測試創建 Lesson (CREATE)"""
        response = client.post(
            "/api/teachers/programs/1/lessons",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Lesson",
                "description": "Test Description",
                "order_index": 1,
                "estimated_minutes": 30,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Lesson"
        assert data["description"] == "Test Description"
        assert data["order_index"] == 1
        assert data["estimated_minutes"] == 30
        assert "id" in data

    def test_read_lesson(self, auth_token):
        """測試讀取 Lesson (透過 Program) (READ)"""
        # 先創建一個 lesson
        create_response = client.post(
            "/api/teachers/programs/1/lessons",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Read Test Lesson",
                "description": "For reading",
                "order_index": 1,
                "estimated_minutes": 45,
            },
        )
        lesson_id = create_response.json()["id"]

        # 透過 GET program 讀取 lesson
        response = client.get(
            "/api/teachers/programs/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "lessons" in data
        # 找到剛創建的 lesson
        lesson = next(
            (
                lesson_item
                for lesson_item in data["lessons"]
                if lesson_item["id"] == lesson_id
            ),
            None,
        )
        assert lesson is not None
        assert lesson["name"] == "Read Test Lesson"

    def test_update_lesson(self, auth_token):
        """測試更新 Lesson (UPDATE)"""
        # 先創建一個 lesson
        create_response = client.post(
            "/api/teachers/programs/1/lessons",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Original Lesson",
                "description": "Original",
                "order_index": 1,
                "estimated_minutes": 30,
            },
        )
        lesson_id = create_response.json()["id"]

        # 更新 lesson
        response = client.put(
            f"/api/teachers/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Lesson",
                "description": "Updated Description",
                "order_index": 2,
                "estimated_minutes": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Lesson"
        assert data["description"] == "Updated Description"
        assert data["order_index"] == 2
        assert data["estimated_minutes"] == 60

    def test_delete_lesson(self, auth_token):
        """測試刪除 Lesson (DELETE) - 軟刪除"""
        # 先創建一個 lesson
        create_response = client.post(
            "/api/teachers/programs/1/lessons",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Delete Test",
                "description": "To be deleted",
                "order_index": 1,
                "estimated_minutes": 30,
            },
        )
        lesson_id = create_response.json()["id"]

        # 刪除 lesson
        response = client.delete(
            f"/api/teachers/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200

        # 驗證軟刪除：嘗試更新應該返回 404
        update_response = client.put(
            f"/api/teachers/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Should Not Work",
                "description": "Should Not Work",
                "order_index": 1,
                "estimated_minutes": 30,
            },
        )
        assert update_response.status_code == 404

    def test_cannot_create_lesson_in_deleted_program(self, auth_token):
        """測試無法在已刪除的 Program 中創建 Lesson"""
        # 創建一個新 program
        db = TestingSessionLocal()
        program = Program(
            name="To Delete Program",
            description="Will be deleted",
            teacher_id=1,
            classroom_id=1,
        )
        db.add(program)
        db.commit()
        program_id = program.id
        db.close()

        # 刪除 program
        client.delete(
            f"/api/teachers/programs/{program_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # 嘗試在已刪除的 program 中創建 lesson
        response = client.post(
            f"/api/teachers/programs/{program_id}/lessons",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Should Not Work",
                "description": "Should Not Work",
                "order_index": 1,
                "estimated_minutes": 30,
            },
        )

        assert response.status_code == 404

    def test_unauthorized_access(self):
        """測試未授權存取"""
        # 沒有 token
        response = client.post(
            "/api/teachers/programs/1/lessons",
            json={
                "name": "Test",
                "description": "Test",
                "order_index": 1,
                "estimated_minutes": 30,
            },
        )
        assert response.status_code == 401

        # 錯誤的 token
        response = client.put(
            "/api/teachers/lessons/1",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "name": "Test",
                "description": "Test",
                "order_index": 1,
                "estimated_minutes": 30,
            },
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
