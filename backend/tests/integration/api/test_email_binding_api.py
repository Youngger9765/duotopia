#!/usr/bin/env python3
"""
Email 綁定 API 整合測試
測試學生 email 綁定功能的 API 端點
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from main import app
from database import get_db
from models import Student, User
from auth import hash_password

client = TestClient(app)


@pytest.fixture
def test_student(db: Session):
    """建立測試學生"""
    student = Student(
        name="測試學生",
        email="test.student@duotopia.com",
        password_hash=hash_password("20120101"),
        student_id="TEST001",
        email_verified=False,
        is_active=True,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@pytest.fixture
def student_token(test_student):
    """獲取學生 JWT token"""
    response = client.post(
        "/api/auth/student/login",
        json={"email": test_student.email, "password": "20120101"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestEmailBindingAPI:
    """Email 綁定 API 測試"""

    def test_get_student_profile(self, student_token, test_student):
        """測試獲取學生資料端點"""
        response = client.get(
            "/api/students/me", headers={"Authorization": f"Bearer {student_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_student.name
        assert data["email"] == test_student.email
        assert data["email_verified"] == False

    @patch("services.email_service.EmailService.send_verification_email")
    def test_update_email(
        self, mock_send_email, student_token, test_student, db: Session
    ):
        """測試更新 Email (使用 mock 不真的寄信)"""
        # Mock email 發送，返回成功
        mock_send_email.return_value = True

        new_email = "new.email@example.com"

        response = client.post(
            "/api/students/update-email",
            json={"email": new_email},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email
        assert data["verified"] == False
        assert data["verification_sent"] == True

        # 驗證 mock 被呼叫
        mock_send_email.assert_called_once()

        # 驗證資料庫更新
        db.refresh(test_student)
        assert test_student.email == new_email
        assert test_student.email_verified == False

    @patch("services.email_service.EmailService.send_verification_email")
    def test_update_email_with_failed_sending(
        self, mock_send_email, student_token, test_student, db: Session
    ):
        """測試更新 Email 但郵件發送失敗的情況"""
        # Mock email 發送失敗
        mock_send_email.return_value = False

        new_email = "another.email@example.com"

        response = client.post(
            "/api/students/update-email",
            json={"email": new_email},
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email
        assert data["verified"] == False
        assert data["verification_sent"] == False  # 發送失敗

        # 但 email 還是會更新
        db.refresh(test_student)
        assert test_student.email == new_email

    def test_update_email_without_auth(self):
        """測試未認證情況下更新 Email"""
        response = client.post(
            "/api/students/update-email", json={"email": "test@example.com"}
        )

        assert response.status_code == 401  # Unauthorized

    def test_update_email_with_teacher_token(self, db: Session):
        """測試用教師 token 無法更新學生 email"""
        # 建立測試教師
        teacher = User(
            email="test.teacher@duotopia.com",
            password_hash=hash_password("teacher123"),
            name="測試教師",
            is_active=True,
        )
        db.add(teacher)
        db.commit()

        # 獲取教師 token
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": teacher.email, "password": "teacher123"},
        )
        teacher_token = response.json()["access_token"]

        # 嘗試用教師 token 更新學生 email
        response = client.post(
            "/api/students/update-email",
            json={"email": "test@example.com"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 403  # Forbidden

    def test_profile_endpoint_compatibility(self, student_token):
        """測試 /profile 端點相容性"""
        # 測試舊版 /profile 端點
        response = client.get(
            "/api/students/profile",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200

        # 測試新版 /me 端點
        response = client.get(
            "/api/students/me", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    # 可以直接執行測試
    pytest.main([__file__, "-v"])
