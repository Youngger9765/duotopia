"""
Test cases for password-related bug fixes
Following TDD principles for the three password bugs:
1. Bug1: Login error messages should be in English
2. Bug2: Password requirements consistency between registration and profile change
3. Bug3: Block identical new/old passwords
"""

from fastapi import status
import pytest


class TestBug1EnglishErrorMessages:
    """Bug1: Login error messages should be in English, not Chinese"""

    def test_teacher_login_wrong_password_returns_english_error(
        self, test_client, demo_teacher
    ):
        """Test that wrong password returns English error message"""
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "test@duotopia.com", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error_detail = response.json()["detail"]

        # Bug1 Fix: Must be English, not Chinese ("帳號或密碼錯誤")
        assert error_detail == "Invalid credentials"
        assert "帳號" not in error_detail  # Ensure no Chinese characters

    def test_teacher_login_nonexistent_email_returns_english_error(self, test_client):
        """Test that non-existent email returns English error message"""
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "nonexistent@duotopia.com", "password": "test123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error_detail = response.json()["detail"]

        # Bug1 Fix: Must be English
        assert error_detail == "Invalid credentials"
        assert "帳號" not in error_detail

    def test_student_login_wrong_password_returns_english_error(self, test_client):
        """Test student login also returns English error messages"""
        # Create a student first (would need fixture, simplified here)
        # Assuming student with ID 1 exists in fixtures
        response = test_client.post(
            "/api/auth/student/login", json={"id": 99999, "password": "wrongpass"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error_detail = response.json()["detail"]

        # Bug1 Fix: Student login must also use English
        assert error_detail == "Invalid credentials"
        assert "帳號" not in error_detail


class TestBug2PasswordStrengthConsistency:
    """Bug2: Password requirements must be consistent between registration and profile change"""

    # Password strength requirements:
    # - At least 8 characters
    # - Contains uppercase letter
    # - Contains lowercase letter
    # - Contains number
    # - Contains special character

    def test_registration_rejects_password_too_short(self, test_client):
        """Registration: Password < 8 characters should be rejected"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test_short@duotopia.com",
                "password": "Short1!",  # Only 7 characters
                "name": "Test Teacher",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least 8 characters" in response.json()["detail"]

    def test_registration_rejects_password_no_uppercase(self, test_client):
        """Registration: Password without uppercase should be rejected"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test_nouppercase@duotopia.com",
                "password": "nouppercase1!",  # No uppercase
                "name": "Test Teacher",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "uppercase" in response.json()["detail"].lower()

    def test_registration_rejects_password_no_lowercase(self, test_client):
        """Registration: Password without lowercase should be rejected"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test_nolowercase@duotopia.com",
                "password": "NOLOWERCASE1!",  # No lowercase
                "name": "Test Teacher",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "lowercase" in response.json()["detail"].lower()

    def test_registration_rejects_password_no_number(self, test_client):
        """Registration: Password without number should be rejected"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test_nonumber@duotopia.com",
                "password": "NoNumber!",  # No number
                "name": "Test Teacher",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "number" in response.json()["detail"].lower()

    def test_registration_rejects_password_no_special_char(self, test_client):
        """Registration: Password without special character should be rejected"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test_nospecial@duotopia.com",
                "password": "NoSpecial123",  # No special character
                "name": "Test Teacher",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "special character" in response.json()["detail"].lower()

    def test_registration_accepts_valid_strong_password(self, test_client):
        """Registration: Valid strong password should be accepted"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test_validpass@duotopia.com",
                "password": "Valid123!@#",  # Meets all requirements
                "name": "Test Teacher",
            },
        )

        # Should succeed (200 OK) with verification required
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["verification_required"] is True


class TestBug3BlockIdenticalPasswords:
    """Bug3: Changing password to same password should be blocked"""

    @pytest.fixture
    def authenticated_teacher(self, test_client, test_session):
        """Create and authenticate a teacher with known password"""
        from models import Teacher
        from auth import get_password_hash

        # Create teacher with strong password
        teacher = Teacher(
            email="changepass@duotopia.com",
            password_hash=get_password_hash("Current123!@#"),
            name="Password Test Teacher",
            is_active=True,
            email_verified=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Login to get token
        login_response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "changepass@duotopia.com", "password": "Current123!@#"},
        )

        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        return {"teacher": teacher, "token": token, "password": "Current123!@#"}

    def test_teacher_cannot_change_to_same_password(
        self, test_client, authenticated_teacher
    ):
        """Bug3 Fix: Teacher changing password to same password should be rejected"""
        token = authenticated_teacher["token"]
        current_pass = authenticated_teacher["password"]

        response = test_client.put(
            "/api/teachers/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": current_pass, "new_password": current_pass},
        )

        # Bug3 Fix: Must reject with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_detail = response.json()["detail"]
        assert "different from current password" in error_detail.lower()

    def test_teacher_can_change_to_different_password(
        self, test_client, authenticated_teacher
    ):
        """Teacher can change to a different valid password"""
        token = authenticated_teacher["token"]
        current_pass = authenticated_teacher["password"]

        response = test_client.put(
            "/api/teachers/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": current_pass,
                "new_password": "NewValid123!@#",  # Different password
            },
        )

        # Should succeed
        assert response.status_code == status.HTTP_200_OK
        assert "successfully" in response.json()["message"].lower()

    def test_student_cannot_change_to_same_password(self, test_client, test_session):
        """Bug3 Fix: Student changing password to same password should be rejected"""
        from models import Student
        from auth import get_password_hash

        # Create student with strong password
        student = Student(
            name="Password Test Student",
            password_hash=get_password_hash("StudentPass123!"),
            birthdate="2010-01-01",
        )
        test_session.add(student)
        test_session.commit()
        test_session.refresh(student)

        # Login to get token
        login_response = test_client.post(
            "/api/auth/student/login",
            json={"id": student.id, "password": "StudentPass123!"},
        )

        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Attempt to change to same password
        response = test_client.put(
            "/api/students/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "StudentPass123!",
                "new_password": "StudentPass123!",
            },
        )

        # Bug3 Fix: Must reject
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "different from current password" in response.json()["detail"].lower()


class TestPasswordBugRegressionSuite:
    """Comprehensive regression tests for all three password bugs"""

    def test_bug1_bug2_bug3_together(self, test_client, test_session):
        """Integration test: All three bugs should be fixed simultaneously"""
        from models import Teacher

        # Setup: Create teacher with weak password (for testing old behavior)
        email = "regression@duotopia.com"

        # Test Bug1: Wrong password returns English
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": email, "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid credentials"

        # Test Bug2: Registration requires strong password
        response = test_client.post(
            "/api/auth/teacher/register",
            json={"email": email, "password": "weak", "name": "Test"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "8 characters" in response.json()["detail"]

        # Register with strong password
        response = test_client.post(
            "/api/auth/teacher/register",
            json={"email": email, "password": "Strong123!@#", "name": "Test Teacher"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Mark as verified for login (in real scenario, email verification needed)
        teacher = test_session.query(Teacher).filter(Teacher.email == email).first()
        teacher.is_active = True
        teacher.email_verified = True
        test_session.commit()

        # Login
        login_response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": email, "password": "Strong123!@#"},
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Test Bug3: Cannot change to same password
        response = test_client.put(
            "/api/teachers/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "Strong123!@#",
                "new_password": "Strong123!@#",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "different from current password" in response.json()["detail"].lower()

        # But can change to different strong password
        response = test_client.put(
            "/api/teachers/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "Strong123!@#",
                "new_password": "NewStrong456!@#",
            },
        )
        assert response.status_code == status.HTTP_200_OK
