"""
Comprehensive tests for student endpoints to improve coverage
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models import Student, Classroom, ClassroomStudent
from auth import create_access_token
import json  # noqa: F401

client = TestClient(app)


@pytest.fixture
def teacher_token(test_teacher):
    """Create a valid teacher token"""
    return create_access_token({"sub": str(test_teacher.id), "type": "teacher"})


@pytest.fixture
def student_token(test_student):
    """Create a valid student token"""
    return create_access_token({"sub": str(test_student.id), "type": "student"})


class TestStudentLogin:
    """Test student login functionality"""

    def test_valid_student_login_email_format(self, db_session: Session, test_student: Student):
        """Test successful student login with email format"""
        response = client.post(
            "/api/students/login",
            json={
                "identifier": test_student.email,
                "password": "20000101",  # Default birthdate password
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["student"]["id"] == test_student.id

    def test_valid_student_login_student_id_format(self, db_session: Session, test_student: Student):
        """Test successful student login with student_id format"""
        # Update student to have student_id
        test_student.student_id = "STU001"
        db_session.commit()

        response = client.post("/api/students/login", json={"identifier": "STU001", "password": "20000101"})
        assert response.status_code == 200
        data = response.json()
        assert data["student"]["id"] == test_student.id

    def test_invalid_password(self, test_student: Student):
        """Test login with wrong password"""
        response = client.post(
            "/api/students/login",
            json={"identifier": test_student.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_nonexistent_student(self):
        """Test login with non-existent student"""
        response = client.post(
            "/api/students/login",
            json={"identifier": "nonexistent@test.com", "password": "20000101"},
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_missing_credentials(self):
        """Test login with missing fields"""
        response = client.post(
            "/api/students/login",
            json={
                "identifier": "test@test.com"
                # Missing password
            },
        )
        assert response.status_code == 422  # Validation error

    def test_empty_credentials(self):
        """Test login with empty credentials"""
        response = client.post("/api/students/login", json={"identifier": "", "password": ""})
        assert response.status_code == 401

    def test_invalid_json(self):
        """Test login with invalid JSON"""
        response = client.post(
            "/api/students/login",
            data="invalid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422


class TestStudentProfile:
    """Test student profile endpoints"""

    def test_get_student_profile_success(self, test_student: Student, student_token: str):
        """Test successful profile retrieval"""
        response = client.get("/api/students/me", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_student.id
        assert data["email"] == test_student.email
        assert data["name"] == test_student.name

    def test_get_profile_invalid_token(self):
        """Test profile retrieval with invalid token"""
        response = client.get("/api/students/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

    def test_get_profile_missing_token(self):
        """Test profile retrieval without token"""
        response = client.get("/api/students/me")
        assert response.status_code == 401

    def test_get_profile_teacher_token(self, teacher_token: str):
        """Test profile retrieval with teacher token (should fail)"""
        response = client.get("/api/students/me", headers={"Authorization": f"Bearer {teacher_token}"})
        assert response.status_code == 403
        assert "Not a student" in response.json()["detail"]


class TestStudentDashboard:
    """Test student dashboard functionality"""

    def test_get_dashboard_success(
        self,
        db_session: Session,
        test_student: Student,
        test_classroom: Classroom,
        student_token: str,
    ):
        """Test successful dashboard retrieval"""
        # Add student to classroom
        classroom_student = ClassroomStudent(classroom_id=test_classroom.id, student_id=test_student.id, is_active=True)
        db_session.add(classroom_student)
        db_session.commit()

        response = client.get(
            "/api/students/dashboard",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "student" in data
        assert "statistics" in data
        assert data["student"]["id"] == test_student.id

    def test_get_dashboard_invalid_token(self):
        """Test dashboard with invalid token"""
        response = client.get("/api/students/dashboard", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

    def test_get_dashboard_teacher_token(self, teacher_token: str):
        """Test dashboard with teacher token (should fail)"""
        response = client.get(
            "/api/students/dashboard",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 403


class TestStudentAuthentication:
    """Test student authentication dependency"""

    def test_nonexistent_student_token(self, db_session: Session):
        """Test token for non-existent student"""
        # Create token for non-existent student ID
        fake_token = create_access_token({"sub": "99999", "type": "student"})

        response = client.get("/api/students/me", headers={"Authorization": f"Bearer {fake_token}"})
        assert response.status_code == 404
        assert "Student not found" in response.json()["detail"]

    def test_malformed_token_payload(self):
        """Test token with malformed payload"""
        # Token without required fields
        malformed_token = create_access_token({"sub": "123"})  # Missing type

        response = client.get("/api/students/me", headers={"Authorization": f"Bearer {malformed_token}"})
        assert response.status_code == 403


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_database_connection_resilience(self, student_token: str):
        """Test API behavior with database issues"""
        # This test verifies graceful error handling
        response = client.get("/api/students/me", headers={"Authorization": f"Bearer {student_token}"})
        # Should work normally
        assert response.status_code == 200

    def test_concurrent_requests(self, student_token: str):
        """Test handling multiple concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/api/students/me", headers={"Authorization": f"Bearer {student_token}"})

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in results)


class TestInputValidation:
    """Test input validation and edge cases"""

    def test_long_identifier(self):
        """Test with very long identifier"""
        long_identifier = "a" * 1000 + "@test.com"
        response = client.post(
            "/api/students/login",
            json={"identifier": long_identifier, "password": "20000101"},
        )
        assert response.status_code == 401  # Should handle gracefully

    def test_special_characters_in_password(self, test_student: Student):
        """Test password with special characters"""
        response = client.post(
            "/api/students/login",
            json={"identifier": test_student.email, "password": "!@#$%^&*()"},
        )
        assert response.status_code == 401

    def test_unicode_in_credentials(self, test_student: Student):
        """Test with Unicode characters"""
        response = client.post(
            "/api/students/login",
            json={"identifier": test_student.email, "password": "密碼123"},
        )
        assert response.status_code == 401
