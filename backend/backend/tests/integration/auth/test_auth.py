"""
Test cases for teacher authentication
Following TDD principles
"""

from fastapi import status


class TestTeacherLogin:
    """Test teacher login functionality"""

    def test_successful_login(self, client, demo_teacher):
        """Test successful teacher login with correct credentials"""
        response = client.post(
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

    def test_login_with_wrong_password(self, client, demo_teacher):
        """Test login fails with incorrect password"""
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "test@duotopia.com", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect password"

    def test_login_with_nonexistent_email(self, client):
        """Test login fails with non-existent email"""
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "nonexistent@duotopia.com", "password": "test123"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Email not found"

    def test_login_with_invalid_email_format(self, client):
        """Test login fails with invalid email format"""
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "invalid-email", "password": "test123"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_with_inactive_account(self, client, inactive_teacher):
        """Test login fails with inactive account"""
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "inactive@duotopia.com", "password": "test123"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Account is inactive"

    def test_login_with_missing_fields(self, client):
        """Test login fails with missing required fields"""
        # Missing password
        response = client.post("/api/auth/teacher/login", json={"email": "test@duotopia.com"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing email
        response = client.post("/api/auth/teacher/login", json={"password": "test123"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Empty body
        response = client.post("/api/auth/teacher/login", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTeacherRegistration:
    """Test teacher registration functionality"""

    def test_successful_registration(self, client, db):
        """Test successful teacher registration"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "newteacher@duotopia.com",
                "password": "newpass123",
                "name": "New Teacher",
                "phone": "0912345678",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data

        # Check user info
        assert data["user"]["email"] == "newteacher@duotopia.com"
        assert data["user"]["name"] == "New Teacher"
        assert data["user"]["is_demo"] is False
        # Verify teacher was created in database
        from models import Teacher

        teacher = db.query(Teacher).filter(Teacher.email == "newteacher@duotopia.com").first()
        assert teacher is not None
        assert teacher.name == "New Teacher"
        assert teacher.phone == "0912345678"

    def test_registration_with_existing_email(self, client, demo_teacher):
        """Test registration fails with already registered email"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test@duotopia.com",  # Already exists
                "password": "newpass123",
                "name": "Another Teacher",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Email already registered"

    def test_registration_without_phone(self, client, db):
        """Test registration succeeds without optional phone field"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "nophone@duotopia.com",
                "password": "pass123",
                "name": "No Phone Teacher",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user"]["email"] == "nophone@duotopia.com"

    def test_registration_with_invalid_email(self, client):
        """Test registration fails with invalid email format"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "not-an-email",
                "password": "pass123",
                "name": "Test Teacher",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_registration_with_missing_fields(self, client):
        """Test registration fails with missing required fields"""
        # Missing name
        response = client.post(
            "/api/auth/teacher/register",
            json={"email": "test@duotopia.com", "password": "pass123"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing password
        response = client.post(
            "/api/auth/teacher/register",
            json={"email": "test@duotopia.com", "name": "Test Teacher"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDemoTeacher:
    """Test demo teacher specific functionality"""

    def test_demo_teacher_login(self, client, db):
        """Test demo teacher can login successfully"""
        # Create demo teacher
        from models import Teacher
        from auth import get_password_hash

        demo = Teacher(
            email="demo@duotopia.com",
            password_hash=get_password_hash("demo123"),
            name="Demo Teacher",
            is_active=True,
            is_demo=True,
        )
        db.add(demo)
        db.commit()

        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "demo@duotopia.com", "password": "demo123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user"]["is_demo"] is True
        assert data["user"]["name"] == "Demo Teacher"
