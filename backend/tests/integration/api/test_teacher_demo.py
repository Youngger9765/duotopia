"""
Test teacher demo login and API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Teacher
from auth import get_password_hash


@pytest.fixture
def demo_teacher(db):
    """Create a demo teacher for testing"""
    teacher = Teacher(
        email="demo@duotopia.com",
        password_hash=get_password_hash("demo123"),
        name="Demo Teacher",
        is_active=True,
        is_demo=True,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def test_teacher_login(client, demo_teacher):
    """Test demo teacher login"""
    # Login with demo account
    login_data = {"email": "demo@duotopia.com", "password": "demo123"}

    response = client.post("/api/auth/teacher/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "demo@duotopia.com"

    return data["access_token"]


@pytest.fixture
def demo_teacher_token(client, demo_teacher):
    """Get demo teacher token for authenticated tests"""
    login_data = {"email": "demo@duotopia.com", "password": "demo123"}

    response = client.post("/api/auth/teacher/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


def test_teacher_dashboard(client, demo_teacher_token):
    """Test teacher dashboard endpoint"""
    headers = {"Authorization": f"Bearer {demo_teacher_token}"}
    response = client.get("/api/teachers/dashboard", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "teacher" in data
    assert data["teacher"]["email"] == "demo@duotopia.com"


def test_teacher_classrooms(client, demo_teacher_token):
    """Test teacher classrooms endpoint"""
    headers = {"Authorization": f"Bearer {demo_teacher_token}"}
    response = client.get("/api/teachers/classrooms", headers=headers)

    # Should return 200 even if empty
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_teacher_programs(client, demo_teacher_token):
    """Test teacher programs endpoint"""
    headers = {"Authorization": f"Bearer {demo_teacher_token}"}
    response = client.get("/api/teachers/programs", headers=headers)

    # Should return 200 even if empty
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
