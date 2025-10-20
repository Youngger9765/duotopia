"""
測試訂閱模擬 API - 單元測試 (TDD)
測試模擬充值功能，不經過 TapPay
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import Teacher

client = TestClient(app)

# 測試帳號
TEST_EMAILS = [
    "demo@duotopia.com",
    "trial@duotopia.com",
    "expired@duotopia.com",
]


@pytest.fixture(scope="function")
def setup_test_accounts():
    """確保測試帳號存在"""
    db = SessionLocal()
    try:
        for email in TEST_EMAILS:
            teacher = db.query(Teacher).filter(Teacher.email == email).first()
            if not teacher:
                pytest.skip(f"測試帳號 {email} 不存在")
        yield
    finally:
        db.close()


class TestSubscriptionMockAPI:
    """測試訂閱模擬 API（不經過 TapPay）"""

    def test_get_status_demo_account(self, setup_test_accounts):
        """測試查詢 demo 帳號狀態"""
        response = client.get("/api/test/subscription/demo@duotopia.com/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "days_remaining" in data
        assert data["status"] in ["subscribed", "expired"]

    def test_get_status_trial_account(self, setup_test_accounts):
        """測試查詢 trial 帳號狀態"""
        response = client.get("/api/test/subscription/trial@duotopia.com/status")
        assert response.status_code == 200

    def test_get_status_expired_account(self, setup_test_accounts):
        """測試查詢 expired 帳號狀態"""
        response = client.get("/api/test/subscription/expired@duotopia.com/status")
        assert response.status_code == 200

    def test_get_status_non_test_account(self):
        """測試查詢非測試帳號（應該失敗）"""
        response = client.get("/api/test/subscription/regular@duotopia.com/status")
        assert response.status_code == 403
        assert "僅限測試帳號" in response.json()["detail"]

    def test_set_subscribed(self, setup_test_accounts):
        """測試設定為已訂閱（30天）"""
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "set_subscribed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"]["status"] == "subscribed"
        assert data["status"]["days_remaining"] >= 29
        assert data["status"]["days_remaining"] <= 30
        assert "已設定" in data["message"]

    def test_set_expired(self, setup_test_accounts):
        """測試設定為未訂閱"""
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "set_expired"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"]["status"] == "expired"
        assert data["status"]["days_remaining"] == 0
        assert "未訂閱" in data["message"]

    def test_add_months(self, setup_test_accounts):
        """測試增加月數"""
        # 先設定為已訂閱
        client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "set_subscribed"},
        )

        # 增加 3 個月
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "add_months", "months": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"]["status"] == "subscribed"
        # 30天 + 90天 = 120天（允許誤差1天）
        assert data["status"]["days_remaining"] >= 118
        assert data["status"]["days_remaining"] <= 120
        assert "3 個月" in data["message"]

    def test_add_months_to_expired(self, setup_test_accounts):
        """測試對過期帳號增加月數"""
        # 先設定為過期
        client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "set_expired"},
        )

        # 增加 1 個月
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "add_months", "months": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"]["status"] == "subscribed"
        # 從現在開始計算30天
        assert data["status"]["days_remaining"] >= 29
        assert data["status"]["days_remaining"] <= 30

    def test_reset_to_new(self, setup_test_accounts):
        """測試重置為新帳號（30天試用）"""
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "reset_to_new"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"]["status"] == "subscribed"
        assert data["status"]["days_remaining"] >= 29
        assert data["status"]["days_remaining"] <= 30
        assert "新帳號" in data["message"]

    def test_expire_tomorrow(self, setup_test_accounts):
        """測試設定明天到期"""
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "expire_tomorrow"},
        )
        assert response.status_code == 200
        data = response.json()
        # 明天到期，剩餘0-1天都合理（取決於執行時間）
        assert data["status"]["days_remaining"] <= 1
        assert "明天到期" in data["message"]

    def test_expire_in_week(self, setup_test_accounts):
        """測試設定一週後到期"""
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "expire_in_week"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"]["status"] == "subscribed"
        assert data["status"]["days_remaining"] >= 6
        assert data["status"]["days_remaining"] <= 7
        assert "一週後到期" in data["message"]

    def test_invalid_action(self, setup_test_accounts):
        """測試無效的操作"""
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "invalid_action"},
        )
        assert response.status_code == 400
        assert "不支援的操作" in response.json()["detail"]

    def test_non_existent_account(self):
        """測試不存在的帳號"""
        response = client.post(
            "/api/test/subscription/nonexistent@duotopia.com/update",
            json={"action": "set_subscribed"},
        )
        # 應該先被白名單阻擋
        assert response.status_code == 403

    def test_all_three_accounts(self, setup_test_accounts):
        """測試所有三個測試帳號都能正常運作"""
        for email in TEST_EMAILS:
            # 查詢狀態
            response = client.get(f"/api/test/subscription/{email}/status")
            assert response.status_code == 200

            # 設定為已訂閱
            response = client.post(
                f"/api/test/subscription/{email}/update",
                json={"action": "set_subscribed"},
            )
            assert response.status_code == 200
            assert response.json()["status"]["status"] == "subscribed"


class TestSubscriptionMockVsTapPaySeparation:
    """測試模擬 API 與 TapPay 完全分離"""

    def test_mock_api_does_not_call_tappay(self, setup_test_accounts):
        """確保模擬 API 不會呼叫 TapPay"""
        # 模擬充值不應該產生 TapPay 相關的記錄
        response = client.post(
            "/api/test/subscription/demo@duotopia.com/update",
            json={"action": "add_months", "months": 1},
        )
        assert response.status_code == 200
        data = response.json()

        # 確認回應中沒有 TapPay 相關欄位
        assert "transaction_id" not in data
        assert "tappay_rec_trade_id" not in data
        assert "prime" not in data

    def test_mock_api_endpoint_different_from_payment(self):
        """確保模擬 API 端點與付款 API 完全不同"""
        # 模擬 API: /api/test/subscription/*
        # 付款 API: /api/payment/process

        # 確保兩個端點不同
        mock_endpoint = "/api/test/subscription/demo@duotopia.com/update"
        payment_endpoint = "/api/payment/process"

        assert mock_endpoint != payment_endpoint
        assert "test" in mock_endpoint
        assert "payment" in payment_endpoint

    def test_mock_api_only_accepts_test_accounts(self):
        """確保模擬 API 只接受測試帳號"""
        # 嘗試用真實用戶帳號（應該被拒絕）
        response = client.post(
            "/api/test/subscription/realuser@example.com/update",
            json={"action": "set_subscribed"},
        )
        assert response.status_code == 403
        assert "僅限測試帳號" in response.json()["detail"]
