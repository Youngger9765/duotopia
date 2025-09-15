"""
routers/auth.py 單元測試，目標覆蓋率 80% 以上
"""
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock  # noqa: F401

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from auth import create_access_token  # noqa: E402

client = TestClient(app)


class TestTeacherAuth:
    """教師認證相關測試"""

    @patch("routers.auth.get_db")
    @patch("routers.auth.authenticate_teacher")
    def test_teacher_login_success(self, mock_auth, mock_get_db):
        """測試教師登入成功"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_teacher = Mock()
        mock_teacher.id = 1
        mock_teacher.email = "teacher@test.com"
        mock_teacher.name = "Test Teacher"
        mock_auth.return_value = mock_teacher

        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "teacher@test.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_type"] == "teacher"

    @patch("routers.auth.get_db")
    @patch("routers.auth.authenticate_teacher")
    def test_teacher_login_invalid_credentials(self, mock_auth, mock_get_db):
        """測試教師登入失敗 - 無效憑證"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_auth.return_value = None

        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "teacher@test.com", "password": "wrong_password"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    @patch("routers.auth.get_db")
    def test_teacher_register_success(self, mock_get_db):
        """測試教師註冊成功"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock query for checking existing teacher
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "newteacher@test.com",
                "password": "password123",
                "name": "New Teacher",
                "phone": "0912345678",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newteacher@test.com"
        assert data["name"] == "New Teacher"
        assert "id" in data

    @patch("routers.auth.get_db")
    def test_teacher_register_email_exists(self, mock_get_db):
        """測試教師註冊失敗 - Email 已存在"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock existing teacher
        mock_existing = Mock()
        mock_db.query().filter().first.return_value = mock_existing

        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "existing@test.com",
                "password": "password123",
                "name": "Teacher",
                "phone": "0912345678",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestStudentAuth:
    """學生認證相關測試"""

    @patch("routers.auth.get_db")
    @patch("routers.auth.authenticate_student")
    def test_student_login_success(self, mock_auth, mock_get_db):
        """測試學生登入成功"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_student = Mock()
        mock_student.id = 1
        mock_student.student_id = "S001"
        mock_student.email = "student@test.com"
        mock_student.name = "Test Student"
        mock_student.classroom_id = 1
        mock_auth.return_value = mock_student

        response = client.post(
            "/api/auth/student/login",
            json={"email": "student@test.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_type"] == "student"
        assert data["student_id"] == "S001"

    @patch("routers.auth.get_db")
    @patch("routers.auth.authenticate_student")
    def test_student_login_invalid_credentials(self, mock_auth, mock_get_db):
        """測試學生登入失敗 - 無效憑證"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_auth.return_value = None

        response = client.post(
            "/api/auth/student/login",
            json={"email": "student@test.com", "password": "wrong_password"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    @patch("routers.auth.get_db")
    def test_student_create_success(self, mock_get_db):
        """測試創建學生成功"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock query for checking existing student
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/auth/student/create",
            json={
                "student_id": "S999",
                "email": "newstudent@test.com",
                "password": "password123",
                "name": "New Student",
                "classroom_id": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "S999"
        assert data["email"] == "newstudent@test.com"
        assert data["name"] == "New Student"

    @patch("routers.auth.get_db")
    def test_student_create_duplicate_id(self, mock_get_db):
        """測試創建學生失敗 - 學號重複"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock existing student
        mock_existing = Mock()
        mock_db.query().filter().first.return_value = mock_existing

        response = client.post(
            "/api/auth/student/create",
            json={
                "student_id": "S001",
                "email": "student@test.com",
                "password": "password123",
                "name": "Student",
                "classroom_id": 1,
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestTokenValidation:
    """Token 驗證相關測試"""

    @patch("routers.auth.verify_token")
    def test_validate_token_success(self, mock_verify):
        """測試 Token 驗證成功"""
        mock_verify.return_value = {
            "sub": "1",
            "type": "teacher",
            "email": "teacher@test.com",
        }

        response = client.get(
            "/api/auth/validate", headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user"]["id"] == "1"
        assert data["user"]["type"] == "teacher"

    @patch("routers.auth.verify_token")
    def test_validate_token_invalid(self, mock_verify):
        """測試 Token 驗證失敗"""
        mock_verify.return_value = None

        response = client.get(
            "/api/auth/validate", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["user"] is None

    def test_validate_token_missing(self):
        """測試沒有提供 Token"""
        response = client.get("/api/auth/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["user"] is None


class TestPasswordReset:
    """密碼重設相關測試"""

    @patch("routers.auth.get_db")
    def test_request_password_reset_teacher(self, mock_get_db):
        """測試教師請求密碼重設"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_teacher = Mock()
        mock_teacher.email = "teacher@test.com"
        mock_db.query().filter().first.return_value = mock_teacher

        response = client.post(
            "/api/auth/teacher/reset-password", json={"email": "teacher@test.com"}
        )

        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()

    @patch("routers.auth.get_db")
    def test_request_password_reset_nonexistent(self, mock_get_db):
        """測試請求密碼重設 - 用戶不存在"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query().filter().first.return_value = None

        response = client.post(
            "/api/auth/teacher/reset-password", json={"email": "nonexistent@test.com"}
        )

        # 為了安全，即使用戶不存在也返回成功
        assert response.status_code == 200

    @patch("routers.auth.get_db")
    def test_reset_password_with_token(self, mock_get_db):
        """測試使用 token 重設密碼"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_teacher = Mock()
        mock_teacher.reset_token = "valid_reset_token"
        mock_teacher.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        mock_db.query().filter().first.return_value = mock_teacher

        response = client.post(
            "/api/auth/teacher/reset-password/confirm",
            json={"token": "valid_reset_token", "new_password": "new_password123"},
        )

        assert response.status_code == 200
        assert "successfully reset" in response.json()["message"].lower()


class TestAuthHelpers:
    """認證輔助功能測試"""

    @patch("routers.auth.get_db")
    def test_get_current_user_teacher(self, mock_get_db):
        """測試取得當前教師用戶"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_teacher = Mock()
        mock_teacher.id = 1
        mock_teacher.email = "teacher@test.com"
        mock_db.query().filter().first.return_value = mock_teacher

        token = create_access_token({"sub": "1", "type": "teacher"})

        response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["email"] == "teacher@test.com"
        assert data["type"] == "teacher"

    @patch("routers.auth.get_db")
    def test_get_current_user_student(self, mock_get_db):
        """測試取得當前學生用戶"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_student = Mock()
        mock_student.id = 1
        mock_student.student_id = "S001"
        mock_student.email = "student@test.com"
        mock_db.query().filter().first.return_value = mock_student

        token = create_access_token({"sub": "1", "type": "student"})

        response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["student_id"] == "S001"
        assert data["type"] == "student"

    def test_get_current_user_unauthorized(self):
        """測試未授權訪問當前用戶"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401


class TestAuthEdgeCases:
    """認證邊界情況測試"""

    def test_login_with_invalid_json(self):
        """測試使用無效 JSON 登入"""
        response = client.post("/api/auth/teacher/login", data="invalid json")

        assert response.status_code == 422

    def test_login_with_missing_fields(self):
        """測試缺少必要欄位"""
        response = client.post(
            "/api/auth/teacher/login", json={"email": "teacher@test.com"}  # 缺少 password
        )

        assert response.status_code == 422

    def test_register_with_invalid_email(self):
        """測試使用無效 email 註冊"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "name": "Teacher",
                "phone": "0912345678",
            },
        )

        assert response.status_code == 422

    def test_register_with_weak_password(self):
        """測試使用弱密碼註冊"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "teacher@test.com",
                "password": "123",  # 太短
                "name": "Teacher",
                "phone": "0912345678",
            },
        )

        assert response.status_code == 422
