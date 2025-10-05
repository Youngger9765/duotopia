"""
Unit Tests for Program CRUD API Endpoints
測試 Program 的 Create, Read, Update, Delete API 端點
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import Teacher, Classroom
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# 密碼雜湊
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 測試資料庫連接
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_program_crud.db"
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


class TestProgramCRUD:
    """測試 Program CRUD API"""

    def test_create_program(self, auth_token):
        """測試創建 Program (CREATE)"""
        response = client.post(
            "/api/teachers/programs",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Program",
                "description": "Test Description",
                "classroom_id": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Program"
        assert data["description"] == "Test Description"
        assert "id" in data

        # 保存 program_id for後續測試
        return data["id"]

    def test_read_program(self, auth_token):
        """測試讀取 Program (READ)"""
        # 先創建一個 program
        create_response = client.post(
            "/api/teachers/programs",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Read Test Program",
                "description": "For reading",
                "classroom_id": 1,
            },
        )
        program_id = create_response.json()["id"]

        # 讀取 program
        response = client.get(
            f"/api/teachers/programs/{program_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == program_id
        assert data["name"] == "Read Test Program"

    def test_update_program(self, auth_token):
        """測試更新 Program (UPDATE)"""
        # 先創建一個 program
        create_response = client.post(
            "/api/teachers/programs",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Original Name",
                "description": "Original",
                "classroom_id": 1,
            },
        )
        program_id = create_response.json()["id"]

        # 更新 program
        response = client.put(
            f"/api/teachers/programs/{program_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Name",
                "description": "Updated Description",
                "estimated_hours": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated Description"
        assert data["estimated_hours"] == 20

    def test_update_program_level_and_tags(self, auth_token):
        """測試更新 Program 的 level 和 tags"""
        # 先創建一個 program
        create_response = client.post(
            "/api/teachers/programs",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Program",
                "description": "Test Description",
                "classroom_id": 1,
            },
        )
        program_id = create_response.json()["id"]

        # 更新 level 和 tags
        response = client.put(
            f"/api/teachers/programs/{program_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Program",
                "description": "Updated Description",
                "level": "B1",
                "estimated_hours": 35,
                "tags": ["英語", "基礎"],
            },
        )

        print(f"\n📊 Response status: {response.status_code}")
        print(f"📊 Response body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Program"
        assert data["description"] == "Updated Description"
        assert data["level"] == "B1", f"Expected level='B1', got {data.get('level')}"
        assert data["estimated_hours"] == 35
        assert data["tags"] == ["英語", "基礎"]

    def test_delete_program(self, auth_token):
        """測試刪除 Program (DELETE)"""
        # 先創建一個 program
        create_response = client.post(
            "/api/teachers/programs",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Delete Test",
                "description": "To be deleted",
                "classroom_id": 1,
            },
        )
        program_id = create_response.json()["id"]

        # 刪除 program
        response = client.delete(
            f"/api/teachers/programs/{program_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200

        # 驗證已刪除（應該 404）
        get_response = client.get(
            f"/api/teachers/programs/{program_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_response.status_code == 404

    def test_list_programs(self, auth_token):
        """測試列出所有 Programs"""
        # 創建幾個 programs
        for i in range(3):
            client.post(
                "/api/teachers/programs",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "name": f"Program {i}",
                    "description": f"Description {i}",
                    "classroom_id": 1,
                },
            )

        # 列出所有 programs
        response = client.get(
            "/api/teachers/programs", headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_unauthorized_access(self):
        """測試未授權存取"""
        # 沒有 token
        response = client.get("/api/teachers/programs")
        assert response.status_code == 401

        # 錯誤的 token
        response = client.get(
            "/api/teachers/programs", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
