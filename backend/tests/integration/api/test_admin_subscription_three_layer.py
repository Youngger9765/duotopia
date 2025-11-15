"""
Admin Subscription Three-Layer Architecture Tests

測試三層架構 API 和 admin_metadata history tracking:
- Layer 1: /all-teachers
- Layer 2: /teacher/{id}/periods
- Layer 3: /period/{id}/history (從 admin_metadata 讀取)

同時測試 Create/Edit/Cancel 都會記錄到 admin_metadata
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

    # 新增訂閱 (沒有 admin_metadata，測試空的情況)
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
        admin_metadata=None,  # 測試沒有 history 的情況
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def admin_token(test_client, admin_teacher):
    """Admin 登入 token"""
    import time

    time.sleep(21)  # 避免 rate limit

    response = test_client.post(
        "/api/auth/teacher/login",
        json={"email": admin_teacher.email, "password": "password"},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["access_token"]


class TestThreeLayerArchitecture:
    """測試三層 API 架構"""

    def test_layer1_all_teachers(
        self, test_client, admin_token, regular_teacher, teacher_with_subscription
    ):
        """Layer 1: 獲取所有教師及其訂閱狀態"""
        response = test_client.get(
            "/api/admin/subscription/all-teachers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "teachers" in data
        assert "total" in data
        assert data["total"] >= 2

        # 檢查資料結構
        teachers = data["teachers"]
        assert len(teachers) >= 2

        # 找到有訂閱的教師
        subscribed = next(
            (
                t
                for t in teachers
                if t["teacher_email"] == teacher_with_subscription.email
            ),
            None,
        )
        assert subscribed is not None
        assert subscribed["current_subscription"] is not None
        assert subscribed["current_subscription"]["plan_name"] == "School Teachers"
        assert subscribed["current_subscription"]["quota_total"] == 25000

        # 找到沒訂閱的教師
        no_sub = next(
            (t for t in teachers if t["teacher_email"] == regular_teacher.email), None
        )
        assert no_sub is not None
        assert no_sub["current_subscription"] is None

    def test_layer2_teacher_periods(
        self, test_client, db_session, admin_token, teacher_with_subscription
    ):
        """Layer 2: 獲取教師的所有訂閱 periods"""
        response = test_client.get(
            f"/api/admin/subscription/teacher/{teacher_with_subscription.id}/periods",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "teacher" in data
        assert "periods" in data
        assert "total" in data

        # 檢查教師資訊
        assert data["teacher"]["email"] == teacher_with_subscription.email
        assert data["teacher"]["name"] == teacher_with_subscription.name

        # 檢查 periods
        assert len(data["periods"]) >= 1
        period = data["periods"][0]
        assert period["plan_name"] == "School Teachers"
        assert period["quota_total"] == 25000
        assert period["status"] == "active"

    def test_layer3_period_history_empty(
        self, test_client, db_session, admin_token, teacher_with_subscription
    ):
        """Layer 3: 獲取 period 的 edit history（測試空的情況）"""
        # 找到 period
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher_with_subscription.id, status="active")
            .first()
        )

        response = test_client.get(
            f"/api/admin/subscription/period/{period.id}/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "period_id" in data
        assert "edit_history" in data
        assert data["period_id"] == period.id
        assert data["edit_history"] == []  # 沒有 history


class TestCreateSubscriptionHistory:
    """測試 Create 操作會記錄 history"""

    def test_create_records_history(
        self, test_client, db_session, admin_token, admin_teacher, regular_teacher
    ):
        """Create subscription 應該記錄到 admin_metadata"""
        # When: 創建訂閱
        create_response = test_client.post(
            "/api/admin/subscription/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": regular_teacher.email,
                "plan_name": "Tutor Teachers",
                "end_date": "2025-12-31",
                "reason": "Test create history",
            },
        )

        assert create_response.status_code == 200

        # Then: 查詢 period history
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=regular_teacher.id)
            .first()
        )
        assert period is not None

        history_response = test_client.get(
            f"/api/admin/subscription/period/{period.id}/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert history_response.status_code == 200
        data = history_response.json()
        assert len(data["edit_history"]) == 1

        # 檢查 history 內容
        record = data["edit_history"][0]
        assert record["action"] == "create"
        assert record["admin_email"] == admin_teacher.email
        assert record["admin_name"] == admin_teacher.name
        assert record["reason"] == "Test create history"
        assert "changes" in record
        assert record["changes"]["plan_name"] == "Tutor Teachers"
        assert record["changes"]["quota_total"] == 10000
        assert record["changes"]["status"] == "active"
        assert "timestamp" in record


class TestEditSubscriptionHistory:
    """測試 Edit 操作會記錄 history"""

    def test_edit_records_history(
        self,
        test_client,
        db_session,
        admin_token,
        admin_teacher,
        teacher_with_subscription,
    ):
        """Edit subscription 應該記錄到 admin_metadata"""
        # When: 編輯訂閱
        edit_response = test_client.post(
            "/api/admin/subscription/edit",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": teacher_with_subscription.email,
                "plan_name": "Tutor Teachers",
                "quota_total": 15000,
                "reason": "Test edit history",
            },
        )

        assert edit_response.status_code == 200

        # Then: 查詢 period history
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher_with_subscription.id, status="active")
            .first()
        )

        history_response = test_client.get(
            f"/api/admin/subscription/period/{period.id}/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert history_response.status_code == 200
        data = history_response.json()
        assert len(data["edit_history"]) >= 1

        # 找到最新的 edit 記錄
        edit_record = next(
            (r for r in data["edit_history"] if r["action"] == "edit"), None
        )
        assert edit_record is not None
        assert edit_record["admin_email"] == admin_teacher.email
        assert edit_record["reason"] == "Test edit history"

        # 檢查 changes（from → to format）
        changes = edit_record["changes"]
        assert "plan_name" in changes
        assert changes["plan_name"]["from"] == "School Teachers"
        assert changes["plan_name"]["to"] == "Tutor Teachers"
        assert "quota_total" in changes
        assert changes["quota_total"]["to"] == 15000


class TestCancelSubscriptionHistory:
    """測試 Cancel 操作會記錄 history"""

    def test_cancel_records_history(
        self,
        test_client,
        db_session,
        admin_token,
        admin_teacher,
        teacher_with_subscription,
    ):
        """Cancel subscription 應該記錄到 admin_metadata"""
        # When: 取消訂閱
        cancel_response = test_client.post(
            "/api/admin/subscription/cancel",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": teacher_with_subscription.email,
                "reason": "Test cancel history",
            },
        )

        assert cancel_response.status_code == 200

        # Then: 查詢 period history
        period = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher_with_subscription.id)
            .first()
        )

        history_response = test_client.get(
            f"/api/admin/subscription/period/{period.id}/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert history_response.status_code == 200
        data = history_response.json()
        assert len(data["edit_history"]) >= 1

        # 找到 cancel 記錄
        cancel_record = next(
            (r for r in data["edit_history"] if r["action"] == "cancel"), None
        )
        assert cancel_record is not None
        assert cancel_record["admin_email"] == admin_teacher.email
        assert cancel_record["reason"] == "Test cancel history"

        # 檢查 status change
        changes = cancel_record["changes"]
        assert "status" in changes
        assert changes["status"]["from"] == "active"
        assert changes["status"]["to"] == "cancelled"


class TestEditFailsWithoutSubscription:
    """測試 Edit API 在沒有訂閱時應該失敗"""

    def test_edit_without_subscription_returns_404(
        self, test_client, admin_token, regular_teacher
    ):
        """沒有訂閱時，edit 應該返回 404（應該用 create）"""
        response = test_client.post(
            "/api/admin/subscription/edit",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": regular_teacher.email,
                "plan_name": "School Teachers",
                "end_date": "2025-12-31",
                "reason": "Should fail",
            },
        )

        # Should fail with 404
        assert response.status_code == 404
        assert "Use /create" in response.json()["detail"]


class TestCreateFailsWithExistingSubscription:
    """測試 Create API 在已有訂閱時應該失敗"""

    def test_create_with_existing_subscription_returns_400(
        self, test_client, admin_token, teacher_with_subscription
    ):
        """已有訂閱時，create 應該返回 400（應該用 edit）"""
        response = test_client.post(
            "/api/admin/subscription/create",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "teacher_email": teacher_with_subscription.email,
                "plan_name": "Tutor Teachers",
                "end_date": "2026-12-31",
                "reason": "Should fail",
            },
        )

        # Should fail with 400
        assert response.status_code == 400
        assert "already has an active subscription" in response.json()["detail"]
