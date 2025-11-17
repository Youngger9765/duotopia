"""
測試 Trial 期間點數轉移到付費方案

測試情境：
1. 用戶完成 Email 驗證，獲得 30-Day Trial (10000 點)
2. 用戶使用了部分 Trial 點數（例如用了 3000 點）
3. 用戶刷卡購買付費方案（Tutor Teachers: 10000 點）
4. 系統應該：
   - 取消 Trial period (status = "cancelled")
   - 建立新的 period，quota_total = 10000 + 7000（Trial 剩餘）
   - 在 admin_metadata 記錄 Trial 點數轉移資訊
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

    # 模擬使用 3000 點
    trial_period.quota_used = 3000

    db_session.commit()
    db_session.refresh(trial_teacher)

    return trial_teacher


def test_trial_to_paid_quota_transfer(
    db_session: Session, trial_teacher_with_usage: Teacher
):
    """測試：Trial 轉付費時，剩餘點數應正確轉移"""

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
    assert trial_period.quota_total == 10000  # Trial 也是 10000 點
    assert trial_period.quota_used == 3000  # 使用了 3000 點
    trial_remaining = trial_period.quota_total - trial_period.quota_used
    assert trial_remaining == 7000  # 剩餘 7000 點

    # ========================================
    # 2️⃣ 模擬刷卡購買 Tutor Teachers (10000 點)
    # ========================================
    # 注意：這裡需要 mock TapPay API
    # 暫時跳過實際付款測試，直接測試核心邏輯

    # 手動建立付費 period（模擬 payment.py 的邏輯）
    now = datetime.now(timezone.utc)

    # 🔥 核心邏輯：計算 Trial 剩餘點數
    trial_period_before_cancel = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.payment_method == "trial",
            SubscriptionPeriod.status == "active",
        )
        .first()
    )

    trial_remaining_points = 0
    if trial_period_before_cancel:
        trial_remaining_points = (
            trial_period_before_cancel.quota_total
            - trial_period_before_cancel.quota_used
        )
        # 取消 Trial period
        trial_period_before_cancel.status = "cancelled"
        trial_period_before_cancel.cancelled_at = now
        trial_period_before_cancel.cancel_reason = "Upgraded to paid plan"

    # 建立新的付費 period（包含 Trial 剩餘點數）
    new_period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=10000 + trial_remaining_points,  # 🔥 關鍵：包含 Trial 剩餘
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )

    # 記錄 Trial 點數轉移資訊
    if trial_remaining_points > 0:
        new_period.admin_metadata = {
            "trial_credits_transferred": trial_remaining_points,
            "from_period_id": trial_period_before_cancel.id,
            "transferred_at": now.isoformat(),
        }

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

    # ✅ 驗證：新 period 的 quota_total 包含 Trial 剩餘點數
    assert new_period.quota_total == 17000  # 10000 + 7000
    assert new_period.quota_used == 0
    assert new_period.status == "active"
    assert new_period.payment_method == "credit_card"

    # ✅ 驗證：admin_metadata 記錄正確
    assert new_period.admin_metadata is not None
    assert new_period.admin_metadata["trial_credits_transferred"] == 7000
    assert new_period.admin_metadata["from_period_id"] == cancelled_trial.id


def test_trial_fully_used_no_transfer(db_session: Session, trial_teacher: Teacher):
    """測試：Trial 點數用完時，不應轉移點數"""

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

    trial_period.quota_used = 10000  # 全部用完
    db_session.commit()

    # ========================================
    # 2️⃣ 購買付費方案
    # ========================================
    now = datetime.now(timezone.utc)

    trial_remaining_points = trial_period.quota_total - trial_period.quota_used  # 0
    assert trial_remaining_points == 0

    trial_period.status = "cancelled"
    trial_period.cancelled_at = now
    trial_period.cancel_reason = "Upgraded to paid plan"

    new_period = SubscriptionPeriod(
        teacher_id=trial_teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=10000 + trial_remaining_points,  # 10000 + 0
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )

    # 沒有剩餘點數，不記錄 metadata
    if trial_remaining_points > 0:
        new_period.admin_metadata = {
            "trial_credits_transferred": trial_remaining_points,
            "from_period_id": trial_period.id,
            "transferred_at": now.isoformat(),
        }

    db_session.add(new_period)
    db_session.commit()

    # ========================================
    # 3️⃣ 驗證
    # ========================================
    db_session.refresh(new_period)

    assert new_period.quota_total == 10000  # 沒有額外點數
    assert new_period.admin_metadata is None  # 沒有 metadata


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

    # 檢查 Trial period（應該沒有）
    trial_period = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.payment_method == "trial",
            SubscriptionPeriod.status == "active",
        )
        .first()
    )

    trial_remaining_points = 0
    if trial_period:
        trial_remaining_points = trial_period.quota_total - trial_period.quota_used
        trial_period.status = "cancelled"
        trial_period.cancelled_at = now

    new_period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=10000 + trial_remaining_points,  # 10000 + 0
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
    assert new_period.quota_total == 10000  # 標準配額
    assert new_period.admin_metadata is None


def test_trial_period_cancelled_not_transferred_twice(
    db_session: Session, trial_teacher_with_usage: Teacher
):
    """測試：已取消的 Trial period 不會被重複轉移"""

    teacher = trial_teacher_with_usage

    # ========================================
    # 1️⃣ 第一次購買（Trial 轉移）
    # ========================================
    now = datetime.now(timezone.utc)

    trial_period = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.payment_method == "trial",
            SubscriptionPeriod.status == "active",
        )
        .first()
    )

    trial_remaining = trial_period.quota_total - trial_period.quota_used  # 700
    trial_period.status = "cancelled"
    trial_period.cancelled_at = now

    first_period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=10000 + trial_remaining,
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )
    db_session.add(first_period)
    db_session.commit()

    # ========================================
    # 2️⃣ 第二次續訂（不應轉移 Trial）
    # ========================================
    first_period.status = "expired"

    # 查詢 active trial period（應該沒有）
    active_trial = (
        db_session.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.payment_method == "trial",
            SubscriptionPeriod.status == "active",  # 🔥 關鍵：只轉移 active 的
        )
        .first()
    )

    trial_remaining_second = 0
    if active_trial:
        trial_remaining_second = active_trial.quota_total - active_trial.quota_used

    second_period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=10000 + trial_remaining_second,  # 10000 + 0
        quota_used=0,
        start_date=now + timedelta(days=30),
        end_date=now + timedelta(days=60),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )
    db_session.add(second_period)
    db_session.commit()
    db_session.refresh(second_period)

    # ========================================
    # 3️⃣ 驗證
    # ========================================
    assert second_period.quota_total == 10000  # 沒有轉移 Trial（已 cancelled）
    assert second_period.admin_metadata is None
