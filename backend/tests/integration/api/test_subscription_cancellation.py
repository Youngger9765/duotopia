"""
測試訂閱取消與恢復功能
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Teacher
from auth import get_password_hash, create_access_token


@pytest.fixture
def subscribed_teacher(test_session: Session):
    """建立已訂閱的教師"""
    teacher = Teacher(
        email="subscribed@duotopia.com",
        password_hash=get_password_hash("test123"),
        name="Subscribed Teacher",
        is_active=True,
        email_verified=True,
        subscription_end_date=datetime.now(timezone.utc) + timedelta(days=30),
        subscription_auto_renew=True,  # 預設啟用自動續訂
    )
    test_session.add(teacher)
    test_session.commit()
    test_session.refresh(teacher)
    return teacher


@pytest.fixture
def auth_token(subscribed_teacher: Teacher):
    """取得認證 token"""
    return create_access_token(
        data={
            "sub": str(subscribed_teacher.id),
            "email": subscribed_teacher.email,
            "type": "teacher",
            "name": subscribed_teacher.name,
        }
    )


class TestCancelSubscription:
    """測試取消訂閱"""

    def test_cancel_active_subscription(
        self, test_client: TestClient, test_session: Session, subscribed_teacher: Teacher, auth_token: str
    ):
        """測試取消有效訂閱"""
        # Given: 用戶有有效訂閱
        assert subscribed_teacher.subscription_auto_renew is True
        original_end_date = subscribed_teacher.subscription_end_date

        # When: 取消訂閱
        response = test_client.post(
            "/api/subscription/cancel",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Then: 取消成功
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["auto_renew"] is False
        assert "已取消自動續訂" in data["message"]

        # 刷新資料
        test_session.refresh(subscribed_teacher)

        # 訂閱到期日不變
        assert subscribed_teacher.subscription_end_date == original_end_date

        # 自動續訂已關閉
        assert subscribed_teacher.subscription_auto_renew is False
        assert subscribed_teacher.subscription_cancelled_at is not None

    def test_cancel_already_cancelled_subscription(
        self, test_client: TestClient, test_session: Session, subscribed_teacher: Teacher, auth_token: str
    ):
        """測試重複取消（應該允許）"""
        # Given: 已經取消過
        subscribed_teacher.subscription_auto_renew = False
        subscribed_teacher.subscription_cancelled_at = datetime.now(timezone.utc)
        test_session.commit()

        # When: 再次取消
        response = test_client.post(
            "/api/subscription/cancel",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Then: 回傳已取消訊息
        assert response.status_code == 200
        data = response.json()
        assert "已經取消過" in data["message"]

    def test_cancel_without_subscription(
        self, test_client: TestClient, test_session: Session
    ):
        """測試無訂閱用戶取消（應失敗）"""
        # Given: 用戶無訂閱
        teacher = Teacher(
            email="nosubscription@duotopia.com",
            password_hash=get_password_hash("test123"),
            name="No Subscription Teacher",
            is_active=True,
            email_verified=True,
            subscription_end_date=None,
        )
        test_session.add(teacher)
        test_session.commit()

        token = create_access_token(
            data={
                "sub": str(teacher.id),
                "email": teacher.email,
                "type": "teacher",
                "name": teacher.name,
            }
        )

        # When: 嘗試取消
        response = test_client.post(
            "/api/subscription/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Then: 回傳錯誤
        assert response.status_code == 400
        assert "沒有訂閱" in response.json()["detail"]

    def test_cancel_expired_subscription(
        self, test_client: TestClient, test_session: Session
    ):
        """測試已過期訂閱取消（應失敗）"""
        # Given: 訂閱已過期
        teacher = Teacher(
            email="expired@duotopia.com",
            password_hash=get_password_hash("test123"),
            name="Expired Teacher",
            is_active=True,
            email_verified=True,
            subscription_end_date=datetime.now(timezone.utc) - timedelta(days=1),  # 昨天過期
        )
        test_session.add(teacher)
        test_session.commit()

        token = create_access_token(
            data={
                "sub": str(teacher.id),
                "email": teacher.email,
                "type": "teacher",
                "name": teacher.name,
            }
        )

        # When: 嘗試取消
        response = test_client.post(
            "/api/subscription/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Then: 回傳錯誤
        assert response.status_code == 400
        assert "已過期" in response.json()["detail"]


class TestResumeSubscription:
    """測試恢復訂閱"""

    def test_resume_cancelled_subscription(
        self, test_client: TestClient, test_session: Session, subscribed_teacher: Teacher, auth_token: str
    ):
        """測試恢復已取消的訂閱"""
        # Given: 訂閱已取消
        subscribed_teacher.subscription_auto_renew = False
        subscribed_teacher.subscription_cancelled_at = datetime.now(timezone.utc)
        test_session.commit()

        # When: 恢復訂閱
        response = test_client.post(
            "/api/subscription/resume",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Then: 恢復成功
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["auto_renew"] is True

        # 刷新資料
        test_session.refresh(subscribed_teacher)

        # 自動續訂已啟用
        assert subscribed_teacher.subscription_auto_renew is True
        assert subscribed_teacher.subscription_cancelled_at is None

    def test_resume_active_subscription(
        self, test_client: TestClient, subscribed_teacher: Teacher, auth_token: str
    ):
        """測試恢復已啟用的訂閱（允許）"""
        # Given: 訂閱已啟用
        assert subscribed_teacher.subscription_auto_renew is True

        # When: 恢復訂閱
        response = test_client.post(
            "/api/subscription/resume",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Then: 回傳已啟用訊息
        assert response.status_code == 200
        data = response.json()
        assert "已設定為自動續訂" in data["message"]

    def test_resume_without_subscription(
        self, test_client: TestClient, test_session: Session
    ):
        """測試無訂閱用戶恢復（應失敗）"""
        # Given: 用戶無訂閱
        teacher = Teacher(
            email="nosubscription2@duotopia.com",
            password_hash=get_password_hash("test123"),
            name="No Subscription Teacher 2",
            is_active=True,
            email_verified=True,
            subscription_end_date=None,
        )
        test_session.add(teacher)
        test_session.commit()

        token = create_access_token(
            data={
                "sub": str(teacher.id),
                "email": teacher.email,
                "type": "teacher",
                "name": teacher.name,
            }
        )

        # When: 嘗試恢復
        response = test_client.post(
            "/api/subscription/resume",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Then: 回傳錯誤
        assert response.status_code == 400
        assert "沒有訂閱" in response.json()["detail"]


class TestSubscriptionStatus:
    """測試訂閱狀態查詢"""

    def test_get_active_subscription_status(
        self, test_client: TestClient, subscribed_teacher: Teacher, auth_token: str
    ):
        """測試查詢有效訂閱狀態"""
        response = test_client.get(
            "/api/subscription/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證資料
        assert data["subscription_end_date"] is not None
        assert data["auto_renew"] is True
        assert data["cancelled_at"] is None
        assert data["is_active"] is True

    def test_get_cancelled_subscription_status(
        self, test_client: TestClient, test_session: Session, subscribed_teacher: Teacher, auth_token: str
    ):
        """測試查詢已取消訂閱狀態"""
        # Given: 訂閱已取消
        subscribed_teacher.subscription_auto_renew = False
        subscribed_teacher.subscription_cancelled_at = datetime.now(timezone.utc)
        test_session.commit()

        # When: 查詢狀態
        response = test_client.get(
            "/api/subscription/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Then: 顯示已取消
        assert response.status_code == 200
        data = response.json()

        assert data["auto_renew"] is False
        assert data["cancelled_at"] is not None
        assert data["is_active"] is True  # 仍在有效期內

    def test_get_expired_subscription_status(
        self, test_client: TestClient, test_session: Session
    ):
        """測試查詢已過期訂閱狀態"""
        # Given: 訂閱已過期
        teacher = Teacher(
            email="expired2@duotopia.com",
            password_hash=get_password_hash("test123"),
            name="Expired Teacher 2",
            is_active=True,
            email_verified=True,
            subscription_end_date=datetime.now(timezone.utc) - timedelta(days=1),
        )
        test_session.add(teacher)
        test_session.commit()

        token = create_access_token(
            data={
                "sub": str(teacher.id),
                "email": teacher.email,
                "type": "teacher",
                "name": teacher.name,
            }
        )

        # When: 查詢狀態
        response = test_client.get(
            "/api/subscription/status",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Then: 顯示已過期
        assert response.status_code == 200
        data = response.json()

        assert data["is_active"] is False  # 已過期


class TestSubscriptionWorkflow:
    """測試完整訂閱流程"""

    def test_cancel_and_resume_workflow(
        self, test_client: TestClient, test_session: Session, subscribed_teacher: Teacher, auth_token: str
    ):
        """測試取消後恢復的完整流程"""
        # Step 1: 查詢初始狀態
        response = test_client.get(
            "/api/subscription/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.json()["auto_renew"] is True

        # Step 2: 取消訂閱
        response = test_client.post(
            "/api/subscription/cancel",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

        # Step 3: 驗證已取消
        response = test_client.get(
            "/api/subscription/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.json()["auto_renew"] is False

        # Step 4: 恢復訂閱
        response = test_client.post(
            "/api/subscription/resume",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

        # Step 5: 驗證已恢復
        response = test_client.get(
            "/api/subscription/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["auto_renew"] is True
        assert data["cancelled_at"] is None
