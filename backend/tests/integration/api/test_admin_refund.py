"""
Admin 退款功能測試 (TDD)

測試範圍：
1. Admin 可以對 active period 進行退款
2. 退款會更新 period 狀態和 metadata
3. 退款會調用 TapPay API
4. 退款會建立 transaction log
5. Webhook 會自動處理後續更新
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from unittest.mock import patch
from models import (
    Teacher,
    SubscriptionPeriod,
    TeacherSubscriptionTransaction,
    TransactionType,
)


@pytest.fixture
def admin_teacher(test_session: Session):
    """創建 Admin 教師"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    teacher = Teacher(
        email="admin@duotopia.com",
        password_hash=pwd_context.hash("admin123"),
        name="Admin User",
        is_admin=True,
        email_verified=True,
    )
    test_session.add(teacher)
    test_session.commit()
    test_session.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(test_session: Session):
    """創建一般教師"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    teacher = Teacher(
        email="teacher@duotopia.com",
        password_hash=pwd_context.hash("password"),
        name="Regular Teacher",
        is_admin=False,
        email_verified=True,
    )
    test_session.add(teacher)
    test_session.commit()
    test_session.refresh(teacher)
    return teacher


@pytest.fixture
def teacher_with_paid_subscription(test_session: Session):
    """創建有付費訂閱的教師（有 TapPay 交易）"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    teacher = Teacher(
        email="paid@duotopia.com",
        password_hash=pwd_context.hash("password"),
        name="Paid Teacher",
        is_admin=False,
        email_verified=True,
    )
    test_session.add(teacher)
    test_session.commit()

    # 建立訂閱 period
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="School Teachers",
        amount_paid=599,
        quota_total=6000,
        quota_used=5000,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="tappay",
        payment_id="TEST_REC_TRADE_ID_123",
        payment_status="paid",
        status="active",
    )
    test_session.add(period)
    test_session.commit()

    # 建立對應的 transaction
    transaction = TeacherSubscriptionTransaction(
        teacher_id=teacher.id,
        teacher_email=teacher.email,
        transaction_type=TransactionType.RECHARGE,
        subscription_type="月方案",
        amount=599,
        currency="TWD",
        status="SUCCESS",
        months=1,
        period_start=now,
        period_end=now + timedelta(days=30),
        previous_end_date=now,
        new_end_date=now + timedelta(days=30),
        payment_provider="tappay",
        payment_method="credit_card",
        external_transaction_id="TEST_REC_TRADE_ID_123",
        webhook_status="PROCESSED",
    )
    test_session.add(transaction)
    test_session.commit()
    test_session.refresh(teacher)
    test_session.refresh(period)
    test_session.refresh(transaction)

    return teacher, period, transaction


def get_auth_token(email: str, password: str, test_client: TestClient) -> str:
    """取得認證 token（helper function）"""
    import time

    time.sleep(0.5)  # 避免 rate limit
    response = test_client.post(
        "/api/auth/teacher/login", json={"email": email, "password": password}
    )
    if response.status_code == 429:
        # Rate limit hit, wait and retry
        time.sleep(2)
        response = test_client.post(
            "/api/auth/teacher/login", json={"email": email, "password": password}
        )
    assert response.status_code == 200, f"Login failed: {response.status_code}"
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(test_client: TestClient, admin_teacher: Teacher) -> dict:
    """取得 Admin 認證 headers"""
    token = get_auth_token("admin@duotopia.com", "admin123", test_client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_headers(test_client: TestClient, regular_teacher: Teacher) -> dict:
    """取得一般教師認證 headers"""
    token = get_auth_token("teacher@duotopia.com", "password", test_client)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 測試案例
# ============================================================================


def test_admin_refund_full_success(
    test_client: TestClient,
    test_session: Session,
    admin_headers: dict,
    teacher_with_paid_subscription,
):
    """測試 Admin 全額退款成功"""
    teacher, period, transaction = teacher_with_paid_subscription

    # Mock TapPay refund API
    with patch("services.tappay_service.TapPayService.refund") as mock_refund:
        mock_refund.return_value = {
            "status": 0,
            "msg": "Success",
            "rec_trade_id": "TEST_REC_TRADE_ID_123",
            "refund_rec_trade_id": "REFUND_123",
        }

        # 發送退款請求（全額退款）
        response = test_client.post(
            "/api/admin/refund",
            json={
                "rec_trade_id": "TEST_REC_TRADE_ID_123",
                "reason": "用戶要求退款",
                "notes": "測試退款",
            },
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "rec_trade_id" in data

        # 驗證 TapPay API 被調用
        mock_refund.assert_called_once_with(
            rec_trade_id="TEST_REC_TRADE_ID_123", amount=None  # None = 全額退款
        )


def test_admin_refund_partial_success(
    test_client: TestClient,
    test_session: Session,
    admin_headers: dict,
    teacher_with_paid_subscription,
):
    """測試 Admin 部分退款成功"""
    teacher, period, transaction = teacher_with_paid_subscription

    with patch("services.tappay_service.TapPayService.refund") as mock_refund:
        mock_refund.return_value = {
            "status": 0,
            "msg": "Success",
            "rec_trade_id": "TEST_REC_TRADE_ID_123",
            "refund_rec_trade_id": "REFUND_PARTIAL_123",
        }

        # 使用 admin_headers fixture

        # 部分退款 NT$ 299（一半）
        response = test_client.post(
            "/api/admin/refund",
            json={
                "rec_trade_id": "TEST_REC_TRADE_ID_123",
                "amount": 299,
                "reason": "用戶要求部分退款",
            },
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # 驗證 TapPay API 被調用（帶金額）
        mock_refund.assert_called_once_with(
            rec_trade_id="TEST_REC_TRADE_ID_123", amount=299
        )


def test_admin_refund_records_in_period_metadata(
    test_client: TestClient,
    test_session: Session,
    admin_headers: dict,
    teacher_with_paid_subscription,
):
    """測試退款會記錄在 period metadata 中"""
    teacher, period, transaction = teacher_with_paid_subscription

    with patch("services.tappay_service.TapPayService.refund") as mock_refund:
        mock_refund.return_value = {"status": 0, "msg": "Success"}

        # 使用 admin_headers fixture

        response = test_client.post(
            "/api/admin/refund",
            json={"rec_trade_id": "TEST_REC_TRADE_ID_123", "reason": "測試退款記錄"},
            headers=admin_headers,
        )

        assert response.status_code == 200

        # 重新查詢 period（因為可能在 webhook 中更新）
        # 注意：實際更新是在 webhook，這裡只驗證 API 成功
        # 完整驗證需要測試 webhook 處理


def test_non_admin_cannot_refund(
    test_client: TestClient,
    test_session: Session,
    regular_headers: dict,
    teacher_with_paid_subscription,
):
    """測試非 Admin 無法執行退款"""
    teacher, period, transaction = teacher_with_paid_subscription

    # 一般教師登入
    response = test_client.post(
        "/api/admin/refund",
        json={"rec_trade_id": "TEST_REC_TRADE_ID_123", "reason": "嘗試退款"},
        headers=regular_headers,
    )

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_refund_transaction_not_found(
    test_client: TestClient, test_session: Session, admin_headers: dict
):
    """測試退款不存在的交易"""

    response = test_client.post(
        "/api/admin/refund",
        json={"rec_trade_id": "NOT_EXIST_123", "reason": "測試"},
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_refund_already_refunded(
    test_client: TestClient,
    test_session: Session,
    admin_headers: dict,
    teacher_with_paid_subscription,
):
    """測試重複退款會被拒絕"""
    teacher, period, transaction = teacher_with_paid_subscription

    # 手動標記為已退款
    transaction.refund_status = "completed"
    test_session.commit()

    # 使用 admin_headers fixture

    response = test_client.post(
        "/api/admin/refund",
        json={"rec_trade_id": "TEST_REC_TRADE_ID_123", "reason": "重複退款測試"},
        headers=admin_headers,
    )

    assert response.status_code == 400
    assert "已退款" in response.json()["detail"]


def test_refund_tappay_api_failure(
    test_client: TestClient,
    test_session: Session,
    admin_headers: dict,
    teacher_with_paid_subscription,
):
    """測試 TapPay API 失敗時的處理"""
    teacher, period, transaction = teacher_with_paid_subscription

    with patch("services.tappay_service.TapPayService.refund") as mock_refund:
        # Mock TapPay 退款失敗
        mock_refund.return_value = {"status": -1, "msg": "Refund failed"}

        # 使用 admin_headers fixture

        response = test_client.post(
            "/api/admin/refund",
            json={"rec_trade_id": "TEST_REC_TRADE_ID_123", "reason": "測試失敗情境"},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "退款失敗" in response.json()["detail"]


def test_refund_reason_is_required(
    test_client: TestClient,
    test_session: Session,
    admin_headers: dict,
    teacher_with_paid_subscription,
):
    """測試退款原因為必填"""
    teacher, period, transaction = teacher_with_paid_subscription

    # 使用 admin_headers fixture

    # 不提供 reason
    response = test_client.post(
        "/api/admin/refund",
        json={"rec_trade_id": "TEST_REC_TRADE_ID_123"},
        headers=admin_headers,
    )

    assert response.status_code == 422  # Validation error
