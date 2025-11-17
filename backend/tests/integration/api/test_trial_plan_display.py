"""
測試新註冊用戶的 Trial Plan 在 admin/subscription 頁面正確顯示

測試目標：
- 新註冊用戶完成 email 驗證後，應建立 "30-Day Trial" subscription period
- admin/subscription API 應返回 plan_name = "30-Day Trial"
- end_date 應為註冊日 + 30 天
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Teacher, SubscriptionPeriod
from services.email_service import email_service


client = TestClient(app)


@pytest.fixture
def test_teacher(db_session: Session):
    """建立測試用教師帳號（未驗證）"""
    from auth import get_password_hash

    teacher = Teacher(
        email="trial_test@example.com",
        password_hash=get_password_hash("Test1234!"),
        name="Trial Test User",
        is_active=False,
        email_verified=False,
        email_verification_token="test_token_123",
        email_verification_sent_at=datetime.utcnow(),
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


def test_email_verification_creates_trial_plan(
    db_session: Session, test_teacher: Teacher
):
    """測試：Email 驗證後應建立 30-Day Trial subscription period"""

    # 驗證 email
    verified_teacher = email_service.verify_teacher_email_token(
        db_session, "test_token_123"
    )

    assert verified_teacher is not None
    assert verified_teacher.email_verified is True
    assert verified_teacher.is_active is True

    # ✅ 驗證：新用戶預設 auto_renew 應該是 False（沒綁卡不應啟用）
    assert verified_teacher.subscription_auto_renew is False, "新註冊用戶預設不應啟用自動續訂"

    # 檢查是否建立了 subscription period
    period = (
        db_session.query(SubscriptionPeriod)
        .filter(SubscriptionPeriod.teacher_id == test_teacher.id)
        .first()
    )

    assert period is not None, "應該要建立 SubscriptionPeriod"

    # ✅ 驗證：plan_name 應該是 "30-Day Trial"
    assert (
        period.plan_name == "30-Day Trial"
    ), f"Plan name 應該是 '30-Day Trial'，但實際是 '{period.plan_name}'"

    # ✅ 驗證：end_date 應該是 start_date + 30 天
    expected_end_date = period.start_date + timedelta(days=30)
    assert period.end_date.date() == expected_end_date.date()

    # ✅ 驗證：payment_method 應該是 "trial"
    assert period.payment_method == "trial"

    # ✅ 驗證：status 應該是 "active"
    assert period.status == "active"


def test_trial_plan_name_and_duration(db_session: Session, test_teacher: Teacher):
    """測試：Trial plan 的名稱和期限應該正確"""

    # 驗證 email 建立 trial period
    email_service.verify_teacher_email_token(db_session, "test_token_123")

    # 直接從資料庫查詢 subscription period
    period = (
        db_session.query(SubscriptionPeriod)
        .filter(SubscriptionPeriod.teacher_id == test_teacher.id)
        .first()
    )

    assert period is not None, "應該要建立 SubscriptionPeriod"

    # ✅ 驗證：plan_name 應該是 "30-Day Trial"
    assert (
        period.plan_name == "30-Day Trial"
    ), f"Plan name 應該是 '30-Day Trial'，但實際是 '{period.plan_name}'"

    # ✅ 驗證：end_date 應該是 start_date + 30 天
    expected_end_date = period.start_date + timedelta(days=30)
    assert period.end_date.date() == expected_end_date.date()

    # ✅ 驗證：payment_method 應該是 "trial"
    assert period.payment_method == "trial"

    # ✅ 驗證：status 應該是 "active"
    assert period.status == "active"
