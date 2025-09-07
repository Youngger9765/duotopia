"""
測試 Email 驗證功能的完整流程
包含：綁定、驗證、解除綁定
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import secrets
import hashlib
from main import app
from database import get_db, engine, Base
from models import Student, Teacher, Classroom
from sqlalchemy.orm import Session

# 創建測試客戶端
client = TestClient(app)

# 測試數據
TEST_STUDENT_DATA = {
    "name": "測試學生",
    "birthdate": "20100315",
    "email": "test_student@test.com",
}

TEST_TEACHER_DATA = {
    "name": "測試老師",
    "email": "test_teacher@test.com",
    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRsiEz1DpS",  # "password123" hashed
}


@pytest.fixture(scope="function")
def test_db():
    """創建測試資料庫會話"""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def create_test_environment(test_db: Session):
    """創建測試環境：班級、老師、學生"""
    # 創建老師
    teacher = Teacher(
        name=TEST_TEACHER_DATA["name"],
        email=TEST_TEACHER_DATA["email"],
        password_hash=TEST_TEACHER_DATA["password_hash"],
    )
    test_db.add(teacher)
    test_db.flush()

    # 創建班級
    classroom = Classroom(name="測試班級", teacher_id=teacher.id)
    test_db.add(classroom)
    test_db.flush()

    # 創建學生（未綁定 Email）
    student = Student(
        name=TEST_STUDENT_DATA["name"],
        birthdate=datetime.strptime(TEST_STUDENT_DATA["birthdate"], "%Y%m%d").date(),
        classroom_id=classroom.id,
        teacher_id=teacher.id,
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRsiEz1DpS",  # 預設密碼
        email=None,  # 初始未綁定
        email_verified=False,
    )
    test_db.add(student)
    test_db.commit()

    return {"teacher": teacher, "classroom": classroom, "student": student}


def get_student_token(student_id: int):
    """生成學生登入 token"""
    response = client.post(
        "/api/students/login",
        json={"student_id": student_id, "password": TEST_STUDENT_DATA["birthdate"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestEmailVerification:
    """Email 驗證功能測試"""

    def test_update_email_success(self, test_db: Session, create_test_environment):
        """測試成功更新 Email"""
        env = create_test_environment
        student = env["student"]

        # 學生登入
        token = get_student_token(student.id)

        # 更新 Email
        with patch(
            "services.email_service.EmailService.send_verification_email"
        ) as mock_send:
            mock_send.return_value = True

            response = client.post(
                "/api/students/update-email",
                headers={"Authorization": f"Bearer {token}"},
                json={"email": TEST_STUDENT_DATA["email"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Email 已更新，驗證信已發送"
            assert data["verification_sent"] is True

            # 檢查資料庫
            test_db.refresh(student)
            assert student.email == TEST_STUDENT_DATA["email"]
            assert student.email_verified is False
            assert student.email_verification_token is not None
            assert student.email_verification_sent_at is not None

            # 確認發送郵件被呼叫
            mock_send.assert_called_once()

    def test_verify_email_with_valid_token(
        self, test_db: Session, create_test_environment
    ):
        """測試使用有效 token 驗證 Email"""
        env = create_test_environment
        student = env["student"]

        # 先更新 Email 並生成 token
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()

        student.email = TEST_STUDENT_DATA["email"]
        student.email_verification_token = hashed_token
        student.email_verification_sent_at = datetime.utcnow()
        student.email_verified = False
        test_db.commit()

        # 驗證 Email
        response = client.get(f"/api/students/verify-email/{token}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Email 驗證成功"
        assert data["student_name"] == student.name
        assert data["email"] == TEST_STUDENT_DATA["email"]

        # 檢查資料庫
        test_db.refresh(student)
        assert student.email_verified is True
        assert student.email_verified_at is not None
        assert student.email_verification_token is None  # token 應該被清除

    def test_verify_email_with_invalid_token(self, test_db: Session):
        """測試使用無效 token 驗證 Email"""
        invalid_token = "invalid_token_12345"

        response = client.get(f"/api/students/verify-email/{invalid_token}")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    def test_verify_email_with_expired_token(
        self, test_db: Session, create_test_environment
    ):
        """測試使用過期 token 驗證 Email"""
        env = create_test_environment
        student = env["student"]

        # 生成過期的 token
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()

        student.email = TEST_STUDENT_DATA["email"]
        student.email_verification_token = hashed_token
        student.email_verification_sent_at = datetime.utcnow() - timedelta(
            hours=25
        )  # 超過 24 小時
        student.email_verified = False
        test_db.commit()

        # 嘗試驗證
        response = client.get(f"/api/students/verify-email/{token}")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    def test_verify_email_twice_fails(self, test_db: Session, create_test_environment):
        """測試重複使用同一個 token 驗證會失敗"""
        env = create_test_environment
        student = env["student"]

        # 生成 token
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()

        student.email = TEST_STUDENT_DATA["email"]
        student.email_verification_token = hashed_token
        student.email_verification_sent_at = datetime.utcnow()
        student.email_verified = False
        test_db.commit()

        # 第一次驗證成功
        response = client.get(f"/api/students/verify-email/{token}")
        assert response.status_code == 200

        # 第二次驗證失敗（token 已被清除）
        response = client.get(f"/api/students/verify-email/{token}")
        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired token" in data["detail"]

    def test_unbind_email_success(self, test_db: Session, create_test_environment):
        """測試成功解除 Email 綁定"""
        env = create_test_environment
        student = env["student"]

        # 先設定已驗證的 Email
        student.email = TEST_STUDENT_DATA["email"]
        student.email_verified = True
        student.email_verified_at = datetime.utcnow()
        test_db.commit()

        # 學生登入
        token = get_student_token(student.id)

        # 解除綁定
        response = client.post(
            "/api/students/unbind-email", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Email 綁定已解除"

        # 檢查資料庫
        test_db.refresh(student)
        assert student.email is None
        assert student.email_verified is False
        assert student.email_verified_at is None
        assert student.email_verification_token is None
        assert student.email_verification_sent_at is None

    def test_get_student_profile_with_email(
        self, test_db: Session, create_test_environment
    ):
        """測試獲取學生資料（含 Email 資訊）"""
        env = create_test_environment
        student = env["student"]

        # 設定已驗證的 Email
        student.email = TEST_STUDENT_DATA["email"]
        student.email_verified = True
        student.email_verified_at = datetime.utcnow()
        test_db.commit()

        # 學生登入
        token = get_student_token(student.id)

        # 獲取個人資料
        response = client.get(
            "/api/students/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_STUDENT_DATA["email"]
        assert data["email_verified"] is True
        assert data["email_verified_at"] is not None

    def test_update_email_validation(self, test_db: Session, create_test_environment):
        """測試 Email 格式驗證"""
        env = create_test_environment
        student = env["student"]

        # 學生登入
        token = get_student_token(student.id)

        # 測試無效的 Email 格式
        invalid_emails = [
            "not_an_email",
            "@example.com",
            "user@",
            "user@.com",
            "user@domain",
            "",
        ]

        for invalid_email in invalid_emails:
            response = client.post(
                "/api/students/update-email",
                headers={"Authorization": f"Bearer {token}"},
                json={"email": invalid_email},
            )

            assert response.status_code == 422  # Validation error

    def test_email_uniqueness(self, test_db: Session, create_test_environment):
        """測試 Email 唯一性約束"""
        env = create_test_environment

        # 創建第二個學生
        student2 = Student(
            name="學生二",
            birthdate=datetime(2010, 5, 20).date(),
            classroom_id=env["classroom"].id,
            teacher_id=env["teacher"].id,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRsiEz1DpS",
            email=TEST_STUDENT_DATA["email"],  # 使用相同 Email
            email_verified=True,
        )
        test_db.add(student2)
        test_db.commit()

        # 第一個學生嘗試使用相同 Email
        student1 = env["student"]
        token = get_student_token(student1.id)

        with patch(
            "services.email_service.EmailService.send_verification_email"
        ) as mock_send:
            mock_send.return_value = True

            response = client.post(
                "/api/students/update-email",
                headers={"Authorization": f"Bearer {token}"},
                json={"email": TEST_STUDENT_DATA["email"]},
            )

            assert response.status_code == 400
            data = response.json()
            assert "Email 已被其他帳號使用" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
