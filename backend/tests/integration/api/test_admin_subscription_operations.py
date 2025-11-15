"""
Tests for Admin Subscription Operations (Create/Edit/Cancel)

只使用 subscription_periods 表，不依賴 teacher_subscription_transactions
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import Teacher, SubscriptionPeriod


@pytest.fixture
def admin_teacher(db_session: Session):
    """創建 Admin 教師"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    teacher = Teacher(
        email="admin@duotopia.com",
        password_hash=pwd_context.hash("password"),
        name="Admin User",
        is_admin=True,
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(db_session: Session):
    """創建一般教師（無訂閱）"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    teacher = Teacher(
        email="teacher@duotopia.com",
        password_hash=pwd_context.hash("password"),
        name="Test Teacher",
        is_admin=False,
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def teacher_with_subscription(db_session: Session):
    """創建有訂閱的教師"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    teacher = Teacher(
        email="subscribed@duotopia.com",
        password_hash=pwd_context.hash("password"),
        name="Subscribed Teacher",
        is_admin=False,
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()

    # 新增訂閱
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="School Teachers",
        amount_paid=0,
        quota_total=25000,
        quota_used=5000,
        start_date=now,
        end_date=datetime(2025, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc),
        payment_method="admin_create",
        payment_status="paid",
        status="active",
        created_at=now,
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def admin_token(test_client, admin_teacher):
    """Admin 登入 token - 每個測試間加延遲避免 rate limit"""
    import time

    # 加延遲避免 rate limit (3 per minute = 每 20 秒一次)
    time.sleep(21)

    response = test_client.post(
        "/api/auth/teacher/login",
        json={"email": admin_teacher.email, "password": "password"},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["access_token"]


class TestCreateSubscription:
    """測試創建訂閱功能"""

    def test_create_subscription_for_new_teacher(
        self, test_client, db_session: Session, admin_token, regular_teacher
    ):
        """Admin 為沒有訂閱的老師創建訂閱"""
        # When: 創建訂閱（設定到 2025-12 月底）
        response = test_client.post(
            "/api/admin/subscription/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": regular_teacher.email,
                "plan_name": "School Teachers",
                "end_date": "2025-12-31",
                "reason": "Test subscription creation",
            },
        )

        # Then: 成功創建
        assert response.status_code == 200
        data = response.json()
        assert data["teacher_email"] == regular_teacher.email
        assert data["plan_name"] == "School Teachers"
        assert data["quota_total"] == 25000

        # 檢查資料庫
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=regular_teacher.id)
            .first()
        )
        assert period is not None
        assert period.plan_name == "School Teachers"
        assert period.quota_total == 25000
        assert period.status == "active"
        assert period.payment_method == "admin_create"
        assert period.end_date.year == 2025
        assert period.end_date.month == 12
        assert period.end_date.day == 31
        assert period.end_date.hour == 23
        assert period.end_date.minute == 59

    def test_create_subscription_sets_correct_month_end(
        self, test_client, db_session: Session, admin_token, regular_teacher
    ):
        """創建訂閱時，end_date 應該設定為月底 23:59:59"""
        # When: 設定到 2026-02 (二月只有 28 天)
        response = test_client.post(
            "/api/admin/subscription/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": regular_teacher.email,
                "plan_name": "Tutor Teachers",
                "end_date": "2026-02-28",
                "reason": "Test February",
            },
        )

        # Then: end_date 應該是 2026-02-28 23:59:59
        assert response.status_code == 200
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=regular_teacher.id)
            .first()
        )
        assert period.end_date.year == 2026
        assert period.end_date.month == 2
        assert period.end_date.day == 28
        assert period.end_date.hour == 23
        assert period.end_date.minute == 59

    def test_create_subscription_requires_admin_permission(
        self, test_client, db_session: Session, regular_teacher
    ):
        """非 Admin 無法創建訂閱"""
        import time

        time.sleep(0.5)  # 避免 rate limit
        # Given: 一般教師登入
        login_response = test_client.post(
            "/api/auth/teacher/login",
            json={"email": regular_teacher.email, "password": "password"},
        )
        token = login_response.json()["access_token"]

        # When: 嘗試創建訂閱
        response = test_client.post(
            "/api/admin/subscription/create",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "teacher_email": "someone@example.com",
                "plan_name": "School Teachers",
                "end_date": "2025-12-31",
                "reason": "Should fail",
            },
        )

        # Then: 應該被拒絕
        assert response.status_code == 403


class TestEditSubscription:
    """測試編輯訂閱功能"""

    def test_edit_subscription_change_plan(
        self, test_client, db_session: Session, admin_token, teacher_with_subscription
    ):
        """Admin 可以修改訂閱方案"""
        # When: 修改 Plan (School Teachers → Tutor Teachers)
        response = test_client.post(
            "/api/admin/subscription/edit",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": teacher_with_subscription.email,
                "plan_name": "Tutor Teachers",
                "reason": "Downgrade plan",
            },
        )

        # Then: 成功修改
        assert response.status_code == 200
        data = response.json()
        assert data["plan_name"] == "Tutor Teachers"
        assert data["quota_total"] == 10000  # Tutor Teachers 的 quota

        # 檢查資料庫
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher_with_subscription.id, status="active")
            .first()
        )
        assert period.plan_name == "Tutor Teachers"
        assert period.quota_total == 10000
        assert period.payment_method == "admin_edit"  # ✅ 檢查 payment_method

    def test_edit_subscription_change_quota(
        self, test_client, db_session: Session, admin_token, teacher_with_subscription
    ):
        """Admin 可以修改 Quota"""
        # When: 修改 Quota (25000 → 50000)
        response = test_client.post(
            "/api/admin/subscription/edit",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": teacher_with_subscription.email,
                "quota_total": 50000,
                "reason": "Increase quota",
            },
        )

        # Then: 成功修改
        assert response.status_code == 200
        data = response.json()
        assert data["quota_total"] == 50000

        # 檢查資料庫
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher_with_subscription.id, status="active")
            .first()
        )
        assert period.quota_total == 50000
        assert period.payment_method == "admin_edit"  # ✅ 檢查 payment_method

    def test_edit_subscription_change_end_date(
        self, test_client, db_session: Session, admin_token, teacher_with_subscription
    ):
        """Admin 可以修改結束日期"""
        # When: 延長到 2026-06-30
        response = test_client.post(
            "/api/admin/subscription/edit",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": teacher_with_subscription.email,
                "end_date": "2026-06-30",
                "reason": "Extend subscription",
            },
        )

        # Then: 成功修改
        assert response.status_code == 200

        # 檢查資料庫
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher_with_subscription.id, status="active")
            .first()
        )
        assert period.end_date.year == 2026
        assert period.end_date.month == 6
        assert period.end_date.day == 30
        assert period.payment_method == "admin_edit"  # ✅ 檢查 payment_method


class TestCancelSubscription:
    """測試取消訂閱功能"""

    def test_cancel_active_subscription(
        self, test_client, db_session: Session, admin_token, teacher_with_subscription
    ):
        """Admin 可以取消訂閱"""
        # When: 取消訂閱
        response = test_client.post(
            "/api/admin/subscription/cancel",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": teacher_with_subscription.email,
                "reason": "Test cancellation",
            },
        )

        # Then: 成功取消
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

        # 檢查資料庫
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher_with_subscription.id)
            .order_by(SubscriptionPeriod.created_at.desc())
            .first()
        )
        assert period.status == "cancelled"


class TestOperationHistory:
    """測試操作歷史功能"""

    def test_operation_history_shows_admin_operations(
        self, test_client, db_session: Session, admin_token, regular_teacher
    ):
        """Operation History 顯示所有 Admin 操作"""

        # 創建訂閱
        test_client.post(
            "/api/admin/subscription/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": regular_teacher.email,
                "plan_name": "School Teachers",
                "end_date": "2025-12-31",
                "reason": "Initial subscription",
            },
        )

        # When: 查詢 Operation History
        response = test_client.get(
            "/api/admin/subscription/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 應該顯示剛才的操作
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) > 0

        # 檢查第一筆記錄
        record = data["history"][0]
        assert record["teacher_email"] == regular_teacher.email
        assert record["plan_name"] == "School Teachers"
        assert record["payment_method"] == "admin_create"
