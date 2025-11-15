"""
簡化版 Admin Operation History 測試

驗證：所有 admin 操作都記錄到 operation history
"""

import pytest
from datetime import datetime, timezone, timedelta

from models import Teacher, SubscriptionPeriod, TeacherSubscriptionTransaction
import uuid


def get_unique_email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture
def db_session(test_db_session):
    """使用測試資料庫 session（從 conftest.py）"""
    return test_db_session


@pytest.fixture
def create_admin(db_session):
    def _create():
        admin = Teacher(
            email=get_unique_email("admin"),
            name="Admin",
            password_hash="x",
            is_admin=True,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    return _create


@pytest.fixture
def create_teacher(db_session):
    def _create(with_subscription=False):
        teacher = Teacher(
            email=get_unique_email("teacher"),
            name="Teacher",
            password_hash="x",
            is_admin=False,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(teacher)
        db_session.flush()

        if with_subscription:
            now = datetime.now(timezone.utc)
            period = SubscriptionPeriod(
                teacher_id=teacher.id,
                plan_name="30-Day Trial",
                amount_paid=0,
                quota_total=10000,
                quota_used=0,
                start_date=now,
                end_date=now + timedelta(days=30),
                payment_method="tappay",
                payment_status="paid",
                status="active",
                created_at=now,
            )
            db_session.add(period)

        db_session.commit()
        db_session.refresh(teacher)
        return teacher

    return _create


def get_admin_transactions(db_session, teacher_email):
    return (
        db_session.query(TeacherSubscriptionTransaction)
        .filter_by(
            teacher_email=teacher_email,
            payment_method="manual",
            payment_provider="admin",
        )
        .all()
    )


@pytest.mark.asyncio
async def test_extend_records_history(db_session, create_admin, create_teacher):
    """測試：Extend 操作記錄到 history"""
    from routers.admin import ExtendSubscriptionRequest, extend_subscription

    admin = create_admin()
    teacher = create_teacher()

    request = ExtendSubscriptionRequest(
        teacher_email=teacher.email,
        plan_name="Tutor Teachers",
        months=1,
        reason="Test extend",
    )

    await extend_subscription(request, admin, db_session)

    transactions = get_admin_transactions(db_session, teacher.email)
    assert len(transactions) == 1
    assert transactions[0].transaction_metadata["reason"] == "Test extend"
    print("✅ Extend 有記錄")


@pytest.mark.asyncio
async def test_cancel_active_records_history(db_session, create_admin, create_teacher):
    """測試：Cancel active subscription 記錄到 history"""
    from routers.admin import CancelSubscriptionRequest, cancel_subscription

    admin = create_admin()
    teacher = create_teacher(with_subscription=True)

    request = CancelSubscriptionRequest(
        teacher_email=teacher.email, reason="Test cancel"
    )

    await cancel_subscription(request, admin, db_session)

    transactions = get_admin_transactions(db_session, teacher.email)
    assert len(transactions) == 1
    assert transactions[0].transaction_metadata["cancelled_periods"] == 1
    print("✅ Cancel active 有記錄")


@pytest.mark.asyncio
async def test_cancel_no_subscription_records_history(
    db_session, create_admin, create_teacher
):
    """測試：Cancel 無訂閱也記錄到 history"""
    from routers.admin import CancelSubscriptionRequest, cancel_subscription

    admin = create_admin()
    teacher = create_teacher()

    request = CancelSubscriptionRequest(
        teacher_email=teacher.email, reason="Test cancel no sub"
    )

    await cancel_subscription(request, admin, db_session)

    transactions = get_admin_transactions(db_session, teacher.email)
    assert len(transactions) == 1
    assert transactions[0].transaction_metadata["action"] == "cancel_attempt"
    print("✅ Cancel 無訂閱也有記錄")


@pytest.mark.asyncio
async def test_edit_plan_records_history(db_session, create_admin, create_teacher):
    """測試：Edit plan 記錄到 history"""
    from routers.admin import EditSubscriptionRequest, edit_subscription

    admin = create_admin()
    teacher = create_teacher(with_subscription=True)

    request = EditSubscriptionRequest(
        teacher_email=teacher.email,
        plan_name="School Teachers",
        reason="Test edit plan",
    )

    await edit_subscription(request, admin, db_session)

    transactions = get_admin_transactions(db_session, teacher.email)
    assert len(transactions) == 1
    assert "Plan:" in str(transactions[0].transaction_metadata["changes"])
    print("✅ Edit plan 有記錄")


@pytest.mark.asyncio
async def test_create_subscription_records_history(
    db_session, create_admin, create_teacher
):
    """測試：創建新訂閱記錄到 history"""
    from routers.admin import EditSubscriptionRequest, edit_subscription

    admin = create_admin()
    teacher = create_teacher()

    request = EditSubscriptionRequest(
        teacher_email=teacher.email,
        plan_name="Tutor Teachers",
        months=1,
        reason="Test create",
    )

    await edit_subscription(request, admin, db_session)

    transactions = get_admin_transactions(db_session, teacher.email)
    assert len(transactions) == 1
    assert transactions[0].transaction_metadata["action"] == "create"
    print("✅ Create subscription 有記錄")


@pytest.mark.asyncio
async def test_history_api_returns_all(db_session, create_admin, create_teacher):
    """測試：History API 返回所有記錄"""
    from routers.admin import (
        ExtendSubscriptionRequest,
        extend_subscription,
        CancelSubscriptionRequest,
        cancel_subscription,
        get_extension_history,
    )

    admin = create_admin()
    t1 = create_teacher()
    t2 = create_teacher()

    # 執行多個操作
    await extend_subscription(
        ExtendSubscriptionRequest(
            teacher_email=t1.email, plan_name="Tutor Teachers", months=1, reason="R1"
        ),
        admin,
        db_session,
    )
    await cancel_subscription(
        CancelSubscriptionRequest(teacher_email=t2.email, reason="R2"),
        admin,
        db_session,
    )

    # 查詢 history
    result = await get_extension_history(limit=50, offset=0, admin=admin, db=db_session)

    assert result["total"] >= 2
    for record in result["history"]:
        assert record.teacher_email is not None
        assert record.admin_email is not None

    print(f"✅ History API 返回 {result['total']} 筆記錄")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
