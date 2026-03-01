"""
測試 check_billing_permission：所有老師（不論有無機構）都能管理個人訂閱
"""

from unittest.mock import MagicMock, patch


def test_personal_teacher_can_pay():
    """無機構的老師可以付款（不會拋出例外）"""
    from routers.payment import check_billing_permission

    teacher = MagicMock()
    teacher.id = 1
    db = MagicMock()

    # Should not raise
    check_billing_permission(teacher, db)


def test_org_member_can_pay_personal():
    """機構成員（非 owner）可以管理個人訂閱"""
    from routers.payment import check_billing_permission

    teacher = MagicMock()
    teacher.id = 2
    db = MagicMock()

    # Should not raise (previously would raise 403)
    check_billing_permission(teacher, db)


def test_org_owner_can_pay():
    """機構 owner 可以付款"""
    from routers.payment import check_billing_permission

    teacher = MagicMock()
    teacher.id = 3
    db = MagicMock()

    # Should not raise
    check_billing_permission(teacher, db)
