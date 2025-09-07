"""
簡化的 Email 驗證測試 - 專注測試重複 token 驗證問題
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import secrets
import hashlib
import time
from main import app
from database import get_db, engine, Base
from models import Student
from sqlalchemy.orm import Session

# 創建測試客戶端
client = TestClient(app)


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
def create_test_student(test_db: Session):
    """創建簡單的測試學生"""
    student = Student(
        name="測試學生",
        birthdate=datetime(2010, 3, 15).date(),
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRsiEz1DpS",
        email=None,
        email_verified=False,
    )
    test_db.add(student)
    test_db.commit()
    return student


def test_verify_email_token_only_once(test_db: Session, create_test_student):
    """測試驗證 token 只能使用一次 - 模擬 React StrictMode 重複呼叫"""
    student = create_test_student

    # 設置待驗證的 Email
    token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(token.encode()).hexdigest()

    student.email = "test@example.com"
    student.email_verification_token = hashed_token
    student.email_verification_sent_at = datetime.utcnow()
    student.email_verified = False
    test_db.commit()

    print(f"\n[測試開始] Token: {token[:10]}...")
    print(f"[測試開始] 學生 Email: {student.email}")
    print(f"[測試開始] 驗證狀態: {student.email_verified}")

    # 第一次驗證 - 應該成功
    print("\n[第一次驗證] 發送請求...")
    first_response = client.get(f"/api/students/verify-email/{token}")
    print(f"[第一次驗證] 狀態碼: {first_response.status_code}")
    print(f"[第一次驗證] 回應: {first_response.json()}")

    assert first_response.status_code == 200
    assert "Email 驗證成功" in first_response.json()["message"]

    # 檢查資料庫狀態
    test_db.refresh(student)
    print(f"[第一次驗證後] Email 已驗證: {student.email_verified}")
    print(f"[第一次驗證後] Token 是否已清除: {student.email_verification_token is None}")

    # 模擬 React StrictMode 重複呼叫（間隔很短）
    time.sleep(0.1)

    # 第二次驗證 - 應該失敗
    print("\n[第二次驗證] 發送請求（模擬 React StrictMode）...")
    second_response = client.get(f"/api/students/verify-email/{token}")
    print(f"[第二次驗證] 狀態碼: {second_response.status_code}")
    print(f"[第二次驗證] 回應: {second_response.json()}")

    assert second_response.status_code == 400
    assert "Invalid or expired token" in second_response.json()["detail"]

    # 確認 Email 仍然是已驗證狀態
    test_db.refresh(student)
    print(f"\n[最終狀態] Email 已驗證: {student.email_verified}")
    print(f"[最終狀態] Token: {student.email_verification_token}")

    assert student.email_verified is True
    assert student.email_verification_token is None


def test_verify_email_with_valid_token(test_db: Session, create_test_student):
    """測試使用有效 token 驗證 Email"""
    student = create_test_student

    # 生成並設置 token
    token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(token.encode()).hexdigest()

    student.email = "valid@example.com"
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
    assert data["email"] == "valid@example.com"

    # 檢查資料庫
    test_db.refresh(student)
    assert student.email_verified is True
    assert student.email_verified_at is not None
    assert student.email_verification_token is None


def test_verify_email_with_invalid_token(test_db: Session):
    """測試使用無效 token 驗證 Email"""
    invalid_token = "invalid_token_12345"

    response = client.get(f"/api/students/verify-email/{invalid_token}")

    assert response.status_code == 400
    data = response.json()
    assert "Invalid or expired token" in data["detail"]


if __name__ == "__main__":
    # 執行特定測試
    pytest.main([__file__, "-v", "-s", "-k", "test_verify_email_token_only_once"])
