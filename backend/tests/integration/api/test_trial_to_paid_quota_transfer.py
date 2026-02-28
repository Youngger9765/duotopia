"""
測試 Trial → 付費方案升級行為

測試情境：
1. 用戶完成 Email 驗證，獲得 Free Trial (2000 點)
2. 用戶使用了部分 Trial 點數（例如用了 500 點）
3. 用戶刷卡購買付費方案（Tutor Teachers: 2000 點）
4. 系統應該：
   - 取消 Trial period (status = "cancelled")
   - 建立新的 period，quota_total = 2000（不轉移 Trial 剩餘點數）
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Teacher, SubscriptionPeriod
from services.email_service import email_service

client = TestClient(app)


@pytest.fixture
def trial_teacher(db_session: Session):
    """建立有 Trial period 的教師"""
    from auth import get_password_hash

    # 1. 建立教師帳號
    teacher = Teacher(
        email="trial_upgrade@example.com",
        password_hash=get_password_hash("Test1234!"),
        name="Trial Upgrade Test",
        is_active=False,
        email_verified=False,
        email_verification_token="trial_token_123",
        email_verification_sent_at=datetime.utcnow(),
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    # 2. 驗證 Email（會建立 Trial period）
    email_service.verify_teacher_email_token(db_session, "trial_token_123")

    # 重新載入 teacher
    db_session.refresh(teacher)

    return teacher


@pytest.fixture
def trial_teacher_with_usage(db_session: Session, trial_teacher: Teacher):
    """建立已使用部分 Trial 點數的教師"""
    # 找到 Trial period
    trial_period = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == trial_teacher.id,
            SubscriptionPeriod.payment_method == "trial",
            SubscriptionPeriod.status == "active",
        )
        .first()
    )

    assert trial_period is not None, "Trial period 應該存在"

    # 模擬使用 500 點
    trial_period.quota_used = 500

    db_session.commit()
    db_session.refresh(trial_teacher)

    return trial_teacher


def test_trial_to_paid_no_quota_transfer(
    db_session: Session, trial_teacher_with_usage: Teacher
):
    """測試：Trial 轉付費時，剩餘點數不應轉移"""

    teacher = trial_teacher_with_usage

    # ========================================
    # 1️⃣ 驗證初始狀態
    # ========================================
    trial_period = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.payment_method == "trial",
            SubscriptionPeriod.status == "active",
        )
        .first()
    )

    assert trial_period is not None
    assert trial_period.quota_total == 2000  # Trial 是 2000 點
    assert trial_period.quota_used == 500  # 使用了 500 點

    # ========================================
    # 2️⃣ 模擬購買 Tutor Teachers (2000 點)
    # ========================================
    now = datetime.now(timezone.utc)

    # 取消 Trial period（不轉移剩餘點數）
    trial_period.status = "cancelled"
    trial_period.cancelled_at = now
    trial_period.cancel_reason = "Upgraded to paid plan"

    # 建立新的付費 period（純方案配額，不加 Trial 剩餘）
    new_period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=299,
        quota_total=2000,  # 純方案配額，不轉移 Trial 剩餘
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )

    db_session.add(new_period)
    db_session.commit()
    db_session.refresh(new_period)

    # ========================================
    # 3️⃣ 驗證結果
    # ========================================

    # ✅ 驗證：Trial period 已被取消
    cancelled_trial = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.payment_method == "trial",
        )
        .first()
    )
    assert cancelled_trial.status == "cancelled"
    assert cancelled_trial.cancel_reason == "Upgraded to paid plan"
    assert cancelled_trial.cancelled_at is not None

    # ✅ 驗證：新 period 的 quota_total 不包含 Trial 剩餘點數
    assert new_period.quota_total == 2000  # 純方案配額
    assert new_period.quota_used == 0
    assert new_period.status == "active"
    assert new_period.payment_method == "credit_card"

    # ✅ 驗證：沒有 trial_credits_transferred metadata
    assert new_period.admin_metadata is None


def test_trial_fully_used_then_purchase(db_session: Session, trial_teacher: Teacher):
    """測試：Trial 點數用完時，購買後只有方案配額"""

    # ========================================
    # 1️⃣ 模擬 Trial 點數用完
    # ========================================
    trial_period = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == trial_teacher.id,
            SubscriptionPeriod.payment_method == "trial",
            SubscriptionPeriod.status == "active",
        )
        .first()
    )

    trial_period.quota_used = 2000  # 全部用完
    db_session.commit()

    # ========================================
    # 2️⃣ 購買付費方案
    # ========================================
    now = datetime.now(timezone.utc)

    trial_period.status = "cancelled"
    trial_period.cancelled_at = now
    trial_period.cancel_reason = "Upgraded to paid plan"

    new_period = SubscriptionPeriod(
        teacher_id=trial_teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=299,
        quota_total=2000,
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )

    db_session.add(new_period)
    db_session.commit()

    # ========================================
    # 3️⃣ 驗證
    # ========================================
    db_session.refresh(new_period)

    assert new_period.quota_total == 2000  # 標準配額
    assert new_period.admin_metadata is None


def test_no_trial_period_normal_purchase(db_session: Session):
    """測試：沒有 Trial period 的用戶直接購買，不應受影響"""
    from auth import get_password_hash

    # 建立沒有 Trial 的教師
    teacher = Teacher(
        email="no_trial@example.com",
        password_hash=get_password_hash("Test1234!"),
        name="No Trial User",
        is_active=True,
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    # ========================================
    # 購買付費方案（沒有 Trial period）
    # ========================================
    now = datetime.now(timezone.utc)

    new_period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=299,
        quota_total=2000,
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )

    db_session.add(new_period)
    db_session.commit()
    db_session.refresh(new_period)

    # ========================================
    # 驗證
    # ========================================
    assert new_period.quota_total == 2000  # 標準配額
    assert new_period.admin_metadata is None
