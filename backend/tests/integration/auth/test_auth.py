"""
Test cases for teacher authentication
Following TDD principles
"""

from fastapi import status


class TestTeacherLogin:
    """Test teacher login functionality"""

    def test_successful_login(self, test_client, demo_teacher):
        """Test successful teacher login with correct credentials"""
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "test@duotopia.com", "password": "test123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data

        # Check token type
        assert data["token_type"] == "bearer"

        # Check user info
        assert data["user"]["email"] == "test@duotopia.com"
        assert data["user"]["name"] == "Test Teacher"
        assert data["user"]["is_demo"] is False
        assert data["user"]["id"] == demo_teacher.id

    def test_login_with_wrong_password(self, test_client, demo_teacher):
        """Test login fails with incorrect password"""
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "test@duotopia.com", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_with_nonexistent_email(self, test_client):
        """Test login fails with non-existent email"""
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "nonexistent@duotopia.com", "password": "test123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_with_invalid_email_format(self, test_client):
        """Test login fails with invalid email format"""
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "invalid-email", "password": "test123"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_with_inactive_account(self, test_client, inactive_teacher):
        """Test login fails with inactive account (unverified email)"""
        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "inactive@duotopia.com", "password": "test123"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Should show email verification message
        assert "verify your email" in response.json()["detail"].lower()

    def test_login_with_missing_fields(self, test_client):
        """Test login fails with missing required fields"""
        # Missing password
        response = test_client.post(
            "/api/auth/teacher/login", json={"email": "test@duotopia.com"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing email
        response = test_client.post(
            "/api/auth/teacher/login", json={"password": "test123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Empty body
        response = test_client.post("/api/auth/teacher/login", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTeacherRegistration:
    """Test teacher registration functionality"""

    def test_successful_registration(self, test_client, test_session):
        """Test successful teacher registration"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "newteacher@duotopia.com",
                "password": "NewPass123!",  # Strong password
                "name": "New Teacher",
                "phone": "0912345678",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure (no auto-login, email verification required)
        assert "message" in data
        assert "email" in data
        assert "verification_required" in data
        assert data["verification_required"] is True
        assert data["email"] == "newteacher@duotopia.com"

        # Verify teacher was created in database but not active
        from models import Teacher

        teacher = (
            test_session.query(Teacher)
            .filter(Teacher.email == "newteacher@duotopia.com")
            .first()
        )
        assert teacher is not None
        assert teacher.name == "New Teacher"
        assert teacher.phone == "0912345678"
        assert teacher.is_active is False  # Not active until email verified
        assert teacher.email_verified is False

    def test_registration_with_existing_email(self, test_client, demo_teacher):
        """Test registration fails with already registered email"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test@duotopia.com",  # Already exists
                "password": "NewPass123!",  # Strong password
                "name": "Another Teacher",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Email already registered and verified"

    def test_registration_without_phone(self, test_client, test_session):
        """Test registration succeeds without optional phone field"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "nophone@duotopia.com",
                "password": "Pass123!",  # Strong password
                "name": "No Phone Teacher",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "nophone@duotopia.com"
        assert data["verification_required"] is True

    def test_registration_with_invalid_email(self, test_client):
        """Test registration fails with invalid email format"""
        response = test_client.post(
            "/api/auth/teacher/register",
            json={
                "email": "not-an-email",
                "password": "pass123",
                "name": "Test Teacher",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_registration_with_missing_fields(self, test_client):
        """Test registration fails with missing required fields"""
        # Missing name
        response = test_client.post(
            "/api/auth/teacher/register",
            json={"email": "test@duotopia.com", "password": "pass123"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing password
        response = test_client.post(
            "/api/auth/teacher/register",
            json={"email": "test@duotopia.com", "name": "Test Teacher"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDemoTeacher:
    """Test demo teacher specific functionality"""

    def test_demo_teacher_login(self, test_client, test_session):
        """Test demo teacher can login successfully"""
        # Create demo teacher
        from models import Teacher
        from auth import get_password_hash

        demo = Teacher(
            email="demo@duotopia.com",
            password_hash=get_password_hash("Demo123!"),  # Strong password
            name="Demo Teacher",
            is_active=True,
            is_demo=True,
            email_verified=True,  # Demo teacher is verified
        )
        test_session.add(demo)
        test_session.commit()

        response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": "demo@duotopia.com", "password": "Demo123!"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user"]["is_demo"] is True
        assert data["user"]["name"] == "Demo Teacher"
