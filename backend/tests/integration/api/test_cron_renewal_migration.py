"""
測試 Cron 自動續訂使用新的訂閱系統

新系統:
- 查詢 SubscriptionPeriod.end_date
- 使用 SubscriptionPeriod.plan_name
- 創建新的 SubscriptionPeriod
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Teacher, SubscriptionPeriod
from auth import get_password_hash


@pytest.fixture
def teacher_with_subscription(db_session: Session):
    """使用新系統的老師（有 SubscriptionPeriod）"""
    teacher = Teacher(
        email="test_teacher@test.com",
        password_hash=get_password_hash("test123"),
        name="測試老師",
        email_verified=True,
        is_active=True,
        subscription_auto_renew=True,
    )
    db_session.add(teacher)
    db_session.flush()

    # 創建訂閱週期
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=10000,
        quota_used=0,
        start_date=datetime.now(timezone.utc) - timedelta(days=29),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        payment_method="auto_renew",
        payment_status="paid",
        status="active",
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


class TestCronRenewalSystem:
    """測試新訂閱系統"""

    def test_query_uses_subscription_periods(self, db_session, teacher_with_subscription):
        """✅ 查詢 SubscriptionPeriod.end_date"""
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()

        # 新邏輯：查詢 SubscriptionPeriod 表
        periods = db_session.query(SubscriptionPeriod).filter(
            SubscriptionPeriod.status == "active",
            SubscriptionPeriod.payment_method == "auto_renew",
            SubscriptionPeriod.cancelled_at.is_(None),
            func.date(SubscriptionPeriod.end_date) == tomorrow,
        ).all()

        assert len(periods) == 1
        assert periods[0].teacher.email == "test_teacher@test.com"
        assert periods[0].plan_name == "Tutor Teachers"

    def test_teacher_has_current_period(self, teacher_with_subscription):
        """✅ 老師有 current_period"""
        assert teacher_with_subscription.current_period is not None
        assert teacher_with_subscription.current_period.plan_name == "Tutor Teachers"

    def test_creates_new_period_on_renewal(self, db_session, teacher_with_subscription):
        """✅ 續訂創建新的 SubscriptionPeriod"""
        old_period_count = db_session.query(SubscriptionPeriod).filter_by(
            teacher_id=teacher_with_subscription.id
        ).count()

        assert old_period_count == 1

        # 模擬續訂：創建新 period
        old_period = teacher_with_subscription.current_period

        new_period = SubscriptionPeriod(
            teacher_id=teacher_with_subscription.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            quota_used=0,
            start_date=old_period.end_date,
            end_date=old_period.end_date + timedelta(days=30),
            payment_method="auto_renew",
            payment_status="paid",
            status="active",
        )
        db_session.add(new_period)

        # 舊 period 改為 expired
        old_period.status = "expired"

        db_session.commit()

        # 驗證
        new_period_count = db_session.query(SubscriptionPeriod).filter_by(
            teacher_id=teacher_with_subscription.id
        ).count()

        assert new_period_count == 2

        # current_period 應該返回新的 active period
        db_session.refresh(teacher_with_subscription)
        assert teacher_with_subscription.current_period.id == new_period.id
