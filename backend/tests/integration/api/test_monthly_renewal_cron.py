"""
Monthly Renewal Cron Job 測試

測試每月 1 號自動續訂邏輯的所有情境
"""
import pytest
from datetime import date
from freezegun import freeze_time
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from models import (
    Teacher,
    SubscriptionPeriod,
    TeacherSubscriptionTransaction,
)


@pytest.fixture(autouse=True)
def mock_cron_secret():
    """Mock CRON_SECRET for all tests"""
    with patch("routers.cron.CRON_SECRET", "test-secret"):
        yield


@pytest.fixture
def setup_test_data(test_session: Session):
    """準備測試資料"""
    # 清空相關表
    test_session.query(TeacherSubscriptionTransaction).delete()
    test_session.query(SubscriptionPeriod).delete()
    test_session.query(Teacher).delete()
    test_session.commit()

    return test_session


class TestMonthlyRenewalCron:
    """每月續訂 Cron Job 測試"""

    # ============================================
    # 階段 1: 標記過期訂閱
    # ============================================

    @freeze_time("2025-12-01 02:00:00")
    def test_mark_expired_subscriptions_last_month(self, setup_test_data, test_client):
        """
        情境 1.1: 標記上個月到期的訂閱為 expired

        Given: 有一個 11/30 到期的 active 訂閱
        When: 12/1 Cron 執行
        Then: 該訂閱被標記為 expired
        """
        db = setup_test_data

        # Given: 建立 11/30 到期的訂閱
        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=False,  # 沒有 auto_renew
        )
        db.add(teacher)
        db.flush()

        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            quota_used=0,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="manual",
            payment_status="paid",
            status="active",  # 還是 active
        )
        db.add(period)
        db.commit()

        # When: 執行 Cron
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 訂閱被標記為 expired
        db.refresh(period)
        assert period.status == "expired"
        assert response.json()["marked_expired"] == 1

    @freeze_time("2025-12-01 02:00:00")
    def test_mark_expired_subscriptions_old_months(self, setup_test_data, test_client):
        """
        情境 1.2: 標記所有過期訂閱（包含很久以前的）

        Given: 有多個過期訂閱（10/31, 9/30, 8/31）
        When: 12/1 Cron 執行
        Then: 所有過期訂閱都被標記為 expired
        """
        db = setup_test_data

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
        )
        db.add(teacher)
        db.flush()

        # 建立多個過期訂閱
        old_periods = [
            SubscriptionPeriod(
                teacher_id=teacher.id,
                plan_name="Tutor Teachers",
                amount_paid=330,
                quota_total=10000,
                start_date=date(2025, 10, 1),
                end_date=date(2025, 10, 31),
                payment_method="manual",
                status="active",
            ),
            SubscriptionPeriod(
                teacher_id=teacher.id,
                plan_name="Tutor Teachers",
                amount_paid=330,
                quota_total=10000,
                start_date=date(2025, 9, 1),
                end_date=date(2025, 9, 30),
                payment_method="manual",
                status="active",
            ),
        ]
        for p in old_periods:
            db.add(p)
        db.commit()

        # When: 執行 Cron
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 所有過期訂閱都被標記
        for p in old_periods:
            db.refresh(p)
            assert p.status == "expired"
        assert response.json()["marked_expired"] == 2

    @freeze_time("2025-12-01 02:00:00")
    def test_do_not_mark_current_month_subscriptions(
        self, setup_test_data, test_client
    ):
        """
        情境 1.3: 不標記本月的訂閱

        Given: 有一個 12/31 到期的訂閱
        When: 12/1 Cron 執行
        Then: 該訂閱保持 active
        """
        db = setup_test_data

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
        )
        db.add(teacher)
        db.flush()

        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31),
            payment_method="manual",
            status="active",
        )
        db.add(period)
        db.commit()

        # When: 執行 Cron
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 訂閱保持 active
        db.refresh(period)
        assert period.status == "active"
        assert response.json()["marked_expired"] == 0

    # ============================================
    # 階段 2: 自動續訂 - 正常流程
    # ============================================

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_auto_renew_success(self, mock_tappay_class, setup_test_data, test_client):
        """
        情境 2.1: 自動續訂成功

        Given: 用戶有 11/30 到期訂閱 + auto_renew + 有綁卡
        When: 12/1 Cron 執行
        Then: 扣款成功，建立 12/1~12/31 訂閱
        """
        db = setup_test_data

        # Mock TapPay 扣款成功
        mock_tappay = Mock()
        mock_tappay.pay_by_token.return_value = {
            "status": 0,  # 成功
            "rec_trade_id": "REC123456",
            "card_secret": {
                "card_token": "new_token_123",
            },
        }
        mock_tappay_class.return_value = mock_tappay

        # Given: 建立用戶和訂閱
        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,  # ✅ 啟用 auto_renew
            card_key="card_key_123",  # ✅ 有綁卡
            card_token="card_token_123",
            card_last_four="1234",
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            quota_used=0,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="auto_renew",
            payment_status="paid",
            status="active",
        )
        db.add(old_period)
        db.commit()

        # When: 執行 Cron
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 扣款成功
        assert response.json()["auto_renewed"] == 1
        assert response.json()["renewal_failed"] == 0

        # Then: 建立新訂閱
        new_period = (
            db.query(SubscriptionPeriod)
            .filter(
                SubscriptionPeriod.teacher_id == teacher.id,
                SubscriptionPeriod.start_date == date(2025, 12, 1),
            )
            .first()
        )
        assert new_period is not None
        assert new_period.end_date.date() == date(2025, 12, 31)
        assert new_period.status == "active"
        assert new_period.payment_method == "auto_renew"
        assert new_period.quota_total == 10000

        # Then: card_token 被更新
        db.refresh(teacher)
        assert teacher.card_token == "new_token_123"

        # Then: TapPay 被正確呼叫
        mock_tappay.pay_by_token.assert_called_once()
        call_args = mock_tappay.pay_by_token.call_args[1]
        assert call_args["amount"] == 330
        assert call_args["card_key"] == "card_key_123"

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_auto_renew_school_plan(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 2.2: School Teachers 方案自動續訂

        Given: School Teachers 方案（660元，25000點）
        When: 12/1 Cron 執行
        Then: 扣款 660 元，配額 25000 點
        """
        db = setup_test_data

        # Mock TapPay
        mock_tappay = Mock()
        mock_tappay.pay_by_token.return_value = {
            "status": 0,
            "rec_trade_id": "REC123456",
        }
        mock_tappay_class.return_value = mock_tappay

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="School Teachers",  # School 方案
            amount_paid=660,
            quota_total=25000,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="auto_renew",
            status="active",
        )
        db.add(old_period)
        db.commit()

        # When
        test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 扣款 660 元
        call_args = mock_tappay.pay_by_token.call_args[1]
        assert call_args["amount"] == 660

        # Then: 新訂閱配額 25000
        new_period = (
            db.query(SubscriptionPeriod)
            .filter(
                SubscriptionPeriod.teacher_id == teacher.id,
                SubscriptionPeriod.start_date == date(2025, 12, 1),
            )
            .first()
        )
        assert new_period.quota_total == 25000

    # ============================================
    # 階段 2: 自動續訂 - 失敗情境
    # ============================================

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_auto_renew_payment_failed(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 3.1: 扣款失敗

        Given: 用戶有訂閱但信用卡餘額不足
        When: 12/1 Cron 執行
        Then: 不建立新訂閱，記錄失敗交易
        """
        db = setup_test_data

        # Mock TapPay 扣款失敗
        mock_tappay = Mock()
        mock_tappay.pay_by_token.return_value = {
            "status": -1,  # 失敗
            "msg": "餘額不足",
        }
        mock_tappay_class.return_value = mock_tappay

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="auto_renew",
            status="active",
        )
        db.add(old_period)
        db.commit()

        # When
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 續訂失敗
        assert response.json()["renewal_failed"] == 1
        assert response.json()["auto_renewed"] == 0

        # Then: 沒有建立新訂閱
        new_period = (
            db.query(SubscriptionPeriod)
            .filter(
                SubscriptionPeriod.teacher_id == teacher.id,
                SubscriptionPeriod.start_date == date(2025, 12, 1),
            )
            .first()
        )
        assert new_period is None

    # ============================================
    # 階段 2: 檢查 1 - 防重複扣款
    # ============================================

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_skip_if_already_renewed_this_month(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 4.1: 檢查 1 - 已有本月訂閱，跳過

        Given: 用戶已有 12/1~12/31 訂閱（手動續訂或重複執行）
        When: 12/1 Cron 執行
        Then: 跳過該用戶，不重複扣款
        """
        db = setup_test_data

        mock_tappay = Mock()
        mock_tappay_class.return_value = mock_tappay

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        # Given: 上個月訂閱
        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="auto_renew",
            status="active",
            amount_paid=330,
            quota_total=10000,
        )
        db.add(old_period)

        # Given: 已有本月訂閱（手動續訂）
        current_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31),
            payment_method="manual",  # 手動付的
            status="active",
        )
        db.add(current_period)
        db.commit()

        # When
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 跳過，不扣款
        assert response.json()["skipped"] == 1
        assert response.json()["auto_renewed"] == 0
        mock_tappay.pay_by_token.assert_not_called()

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_skip_if_cron_runs_twice(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 4.2: Cron Job 被觸發兩次，第二次跳過

        Given: Cron 第一次執行成功
        When: Cron 第二次執行（誤觸發）
        Then: 跳過，不重複扣款
        """
        db = setup_test_data

        mock_tappay = Mock()
        mock_tappay.pay_by_token.return_value = {"status": 0, "rec_trade_id": "REC123"}
        mock_tappay_class.return_value = mock_tappay

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="auto_renew",
            status="active",
            amount_paid=330,
            quota_total=10000,
        )
        db.add(old_period)
        db.commit()

        # When: 第一次執行
        response1 = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        assert response1.json()["auto_renewed"] == 1

        # When: 第二次執行（重複）
        response2 = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 第二次跳過
        assert response2.json()["skipped"] == 1
        assert response2.json()["auto_renewed"] == 0

        # Then: TapPay 只被呼叫一次
        assert mock_tappay.pay_by_token.call_count == 1

    # ============================================
    # 階段 2: 檢查 2 - 防錯誤扣款 + 關閉 auto_renew
    # ============================================

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_disable_auto_renew_if_no_last_month_subscription(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 5.1: 檢查 2 - 上個月沒訂閱，關閉 auto_renew

        Given: 用戶有 auto_renew 但沒有 11/30 訂閱（中斷）
        When: 12/1 Cron 執行
        Then: 關閉 auto_renew，發送通知
        """
        db = setup_test_data

        mock_tappay = Mock()
        mock_tappay_class.return_value = mock_tappay

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,  # 有啟用
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        # Given: 沒有 11/30 訂閱（可能是 11/1 扣款失敗）
        # 不建立任何訂閱

        db.commit()

        # When
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: auto_renew 被關閉
        db.refresh(teacher)
        assert teacher.subscription_auto_renew is False
        assert response.json()["auto_renew_disabled"] == 1

        # Then: 不扣款
        mock_tappay.pay_by_token.assert_not_called()

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_disable_auto_renew_for_new_user_never_subscribed(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 5.2: 新用戶綁卡但從未訂閱，關閉 auto_renew

        Given: 新用戶綁卡啟用 auto_renew，但從未付費
        When: 12/1 Cron 執行
        Then: 關閉 auto_renew
        """
        db = setup_test_data

        mock_tappay = Mock()
        mock_tappay_class.return_value = mock_tappay

        # Given: 11/20 註冊並綁卡的新用戶
        teacher = Teacher(
            name="New User",
            email="new@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.commit()

        # When
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: auto_renew 被關閉
        db.refresh(teacher)
        assert teacher.subscription_auto_renew is False
        assert response.json()["auto_renew_disabled"] == 1

    # ============================================
    # 階段 2: 跳過情境
    # ============================================

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_skip_if_no_card(self, mock_tappay_class, setup_test_data, test_client):
        """
        情境 6.1: 沒有綁卡，跳過

        Given: 用戶有 auto_renew 但沒綁卡
        When: 12/1 Cron 執行
        Then: 跳過，不處理
        """
        db = setup_test_data

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,
            card_key=None,  # 沒綁卡
            card_token=None,
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="manual",
            status="active",
            amount_paid=330,
            quota_total=10000,
        )
        db.add(old_period)
        db.commit()

        # When
        test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 不在處理列表中（因為查詢條件就過濾掉了）
        # 舊訂閱被標記為 expired（階段 1）
        db.refresh(old_period)
        assert old_period.status == "expired"

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_skip_if_auto_renew_disabled(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 6.2: auto_renew 關閉，跳過

        Given: 用戶有綁卡但 auto_renew = False
        When: 12/1 Cron 執行
        Then: 跳過，舊訂閱標記 expired
        """
        db = setup_test_data

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=False,  # 關閉
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="manual",
            status="active",
            amount_paid=330,
            quota_total=10000,
        )
        db.add(old_period)
        db.commit()

        # When
        test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 舊訂閱被標記 expired
        db.refresh(old_period)
        assert old_period.status == "expired"

    @freeze_time("2025-12-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_skip_if_account_inactive(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 6.3: 帳號停用，跳過

        Given: 用戶帳號被停用（is_active = False）
        When: 12/1 Cron 執行
        Then: 跳過
        """
        db = setup_test_data

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=False,  # 停用
            subscription_auto_renew=True,
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            payment_method="auto_renew",
            status="active",
            amount_paid=330,
            quota_total=10000,
        )
        db.add(old_period)
        db.commit()

        # When
        test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 不處理（查詢條件過濾）
        db.refresh(old_period)
        assert old_period.status == "expired"

    # ============================================
    # 邊界情境
    # ============================================

    @freeze_time("2025-12-02 02:00:00")
    def test_skip_if_not_first_day_of_month(self, setup_test_data, test_client):
        """
        情境 7.1: 不是每月 1 號，跳過執行

        Given: 今天是 12/2
        When: Cron 執行
        Then: 跳過，不處理任何訂閱
        """
        setup_test_data

        # When
        response = test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then
        assert response.json()["status"] == "skipped"
        assert "Not the 1st" in response.json()["message"]

    @freeze_time("2025-12-01 02:00:00")
    def test_reject_invalid_cron_secret(self, setup_test_data, test_client):
        """
        情境 7.2: 錯誤的 Cron Secret，拒絕執行

        Given: Cron Secret 不正確
        When: Cron 執行
        Then: 返回 401 Unauthorized
        """
        setup_test_data

        # When: 使用錯誤的 secret
        with patch("routers.cron.CRON_SECRET", "correct-secret"):
            response = test_client.post(
                "/api/cron/monthly-renewal", headers={"x-cron-secret": "wrong-secret"}
            )

        # Then: 返回 401
        assert response.status_code == 401

    @freeze_time("2026-01-01 02:00:00")
    @patch("routers.cron.TapPayService")
    def test_handle_year_boundary(
        self, mock_tappay_class, setup_test_data, test_client
    ):
        """
        情境 7.3: 跨年邊界處理（12月 → 1月）

        Given: 2026/1/1 執行，處理 12/31 到期的訂閱
        When: Cron 執行
        Then: 正確處理跨年
        """
        db = setup_test_data

        mock_tappay = Mock()
        mock_tappay.pay_by_token.return_value = {
            "status": 0,
            "rec_trade_id": "REC123",
        }
        mock_tappay_class.return_value = mock_tappay

        teacher = Teacher(
            name="Test Teacher",
            email="test@example.com",
            password_hash="hashed",
            email_verified=True,
            is_active=True,
            subscription_auto_renew=True,
            card_key="card_key_123",
            card_token="card_token_123",
        )
        db.add(teacher)
        db.flush()

        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31),
            payment_method="auto_renew",
            status="active",
            amount_paid=330,
            quota_total=10000,
        )
        db.add(old_period)
        db.commit()

        # When
        test_client.post(
            "/api/cron/monthly-renewal", headers={"x-cron-secret": "test-secret"}
        )

        # Then: 建立 1 月訂閱
        new_period = (
            db.query(SubscriptionPeriod)
            .filter(
                SubscriptionPeriod.teacher_id == teacher.id,
                SubscriptionPeriod.start_date == date(2026, 1, 1),
            )
            .first()
        )
        assert new_period is not None
        assert new_period.end_date.date() == date(2026, 1, 31)
