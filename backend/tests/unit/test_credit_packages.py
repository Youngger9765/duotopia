"""
Credit Packages 單元測試

測試內容：
1. 點數包常數驗證
2. CreditPackage model properties
3. 配額 waterfall 扣點邏輯
4. QuotaService 整合（get_quota_info, check_quota）
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException


class TestCreditPackageConstants:
    """點數包常數驗證"""

    def test_all_packages_defined(self):
        """測試所有包定義存在"""
        from config.plans import CREDIT_PACKAGES

        expected_ids = ["pkg-1000", "pkg-2000", "pkg-5000", "pkg-10000", "pkg-20000"]
        for pkg_id in expected_ids:
            assert pkg_id in CREDIT_PACKAGES, f"Missing package: {pkg_id}"

    def test_package_structure(self):
        """測試每個包都有必要欄位"""
        from config.plans import CREDIT_PACKAGES

        for pkg_id, pkg in CREDIT_PACKAGES.items():
            assert "points" in pkg, f"{pkg_id} missing 'points'"
            assert "bonus" in pkg, f"{pkg_id} missing 'bonus'"
            assert "price" in pkg, f"{pkg_id} missing 'price'"
            assert pkg["points"] > 0, f"{pkg_id} points must be > 0"
            assert pkg["price"] > 0, f"{pkg_id} price must be > 0"
            assert pkg["bonus"] >= 0, f"{pkg_id} bonus must be >= 0"

    def test_package_pricing(self):
        """測試各包的定價"""
        from config.plans import CREDIT_PACKAGES

        assert CREDIT_PACKAGES["pkg-1000"]["price"] == 180
        assert CREDIT_PACKAGES["pkg-2000"]["price"] == 320
        assert CREDIT_PACKAGES["pkg-5000"]["price"] == 700
        assert CREDIT_PACKAGES["pkg-10000"]["price"] == 1200
        assert CREDIT_PACKAGES["pkg-20000"]["price"] == 2000

    def test_package_bonus_points(self):
        """測試贈點"""
        from config.plans import CREDIT_PACKAGES

        assert CREDIT_PACKAGES["pkg-1000"]["bonus"] == 0
        assert CREDIT_PACKAGES["pkg-2000"]["bonus"] == 0
        assert CREDIT_PACKAGES["pkg-5000"]["bonus"] == 200
        assert CREDIT_PACKAGES["pkg-10000"]["bonus"] == 500
        assert CREDIT_PACKAGES["pkg-20000"]["bonus"] == 800

    def test_total_points_with_bonus(self):
        """測試含贈送的總點數"""
        from config.plans import CREDIT_PACKAGES

        for pkg_id, pkg in CREDIT_PACKAGES.items():
            total = pkg["points"] + pkg["bonus"]
            assert total > 0, f"{pkg_id} total must be > 0"

        # 5000 包含 200 贈送 = 5200
        pkg5000 = CREDIT_PACKAGES["pkg-5000"]
        assert pkg5000["points"] + pkg5000["bonus"] == 5200

        # 20000 包含 800 贈送 = 20800
        pkg20000 = CREDIT_PACKAGES["pkg-20000"]
        assert pkg20000["points"] + pkg20000["bonus"] == 20800

    def test_org_allowed_packages(self):
        """測試機構可購買的包"""
        from config.plans import ORG_ALLOWED_PACKAGES, CREDIT_PACKAGES

        assert "pkg-20000" in ORG_ALLOWED_PACKAGES
        # 機構允許的包都必須存在
        for pkg_id in ORG_ALLOWED_PACKAGES:
            assert pkg_id in CREDIT_PACKAGES

    def test_validity_days(self):
        """測試有效期限"""
        from config.plans import CREDIT_PACKAGE_VALIDITY_DAYS

        assert CREDIT_PACKAGE_VALIDITY_DAYS == 365

    def test_unit_cost_decreasing(self):
        """測試越大包越划算（單位成本遞減）"""
        from config.plans import CREDIT_PACKAGES

        packages = sorted(CREDIT_PACKAGES.items(), key=lambda x: x[1]["points"])
        prev_unit_cost = float("inf")
        for pkg_id, pkg in packages:
            total_points = pkg["points"] + pkg["bonus"]
            unit_cost = pkg["price"] / total_points
            assert (
                unit_cost <= prev_unit_cost
            ), f"{pkg_id} unit cost ({unit_cost:.4f}) > previous ({prev_unit_cost:.4f})"
            prev_unit_cost = unit_cost


class TestCreditPackageModel:
    """CreditPackage model 屬性測試"""

    def test_points_remaining(self):
        """測試 points_remaining property"""
        from models.credit_package import CreditPackage

        pkg = CreditPackage(points_total=5200, points_used=300)
        assert pkg.points_remaining == 4900

    def test_points_remaining_zero(self):
        """測試點數用完"""
        from models.credit_package import CreditPackage

        pkg = CreditPackage(points_total=1000, points_used=1000)
        assert pkg.points_remaining == 0

    def test_points_remaining_never_negative(self):
        """測試 points_remaining 不會為負數"""
        from models.credit_package import CreditPackage

        pkg = CreditPackage(points_total=1000, points_used=1200)
        assert pkg.points_remaining == 0


class TestWaterfallDeduction:
    """Waterfall 扣點邏輯測試（使用 mock）"""

    def _make_mock_teacher(self, current_period=None, teacher_id=1):
        """建立 mock teacher"""
        teacher = MagicMock()
        teacher.id = teacher_id
        teacher.current_period = current_period
        return teacher

    def _make_mock_period(self, quota_total=2000, quota_used=0):
        """建立 mock subscription period"""
        period = MagicMock()
        period.id = 1
        period.quota_total = quota_total
        period.quota_used = quota_used
        return period

    def _make_mock_package(self, points_total=5200, points_used=0, expires_at=None):
        """建立 mock credit package"""
        from models.credit_package import CreditPackage

        pkg = MagicMock(spec=CreditPackage)
        pkg.points_total = points_total
        pkg.points_used = points_used
        pkg.points_remaining = max(0, points_total - points_used)
        pkg.status = "active"
        pkg.expires_at = expires_at or (datetime.now(timezone.utc) + timedelta(days=300))
        return pkg

    def test_deduct_from_subscription_only(self):
        """測試只從訂閱扣除"""
        from services.quota_service import QuotaService

        period = self._make_mock_period(quota_total=2000, quota_used=100)
        teacher = self._make_mock_teacher(current_period=period)
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        usage_log = QuotaService.deduct_quota(
            db=db,
            teacher=teacher,
            student_id=None,
            assignment_id=None,
            feature_type="speech_recording",
            unit_count=30,
            unit_type="秒",
        )

        # 訂閱配額應該增加 30
        assert period.quota_used == 130

    def test_deduct_from_credit_package_only(self):
        """測試純點數包用戶扣除"""
        from services.quota_service import QuotaService

        teacher = self._make_mock_teacher(current_period=None)
        pkg = self._make_mock_package(points_total=5200, points_used=0)
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            pkg
        ]

        usage_log = QuotaService.deduct_quota(
            db=db,
            teacher=teacher,
            student_id=None,
            assignment_id=None,
            feature_type="speech_recording",
            unit_count=30,
            unit_type="秒",
        )

        # 點數包應該增加 30
        assert pkg.points_used == 30

    def test_waterfall_subscription_then_package(self):
        """測試 waterfall：先扣訂閱，再扣點數包"""
        from services.quota_service import QuotaService

        # 訂閱只剩 20 秒
        period = self._make_mock_period(quota_total=2000, quota_used=1980)
        teacher = self._make_mock_teacher(current_period=period)
        pkg = self._make_mock_package(points_total=5200, points_used=0)
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            pkg
        ]

        # 扣除 50 秒（訂閱 20 + 點數包 30）
        usage_log = QuotaService.deduct_quota(
            db=db,
            teacher=teacher,
            student_id=None,
            assignment_id=None,
            feature_type="speech_recording",
            unit_count=50,
            unit_type="秒",
        )

        assert period.quota_used == 2000  # 訂閱用滿
        assert pkg.points_used == 30  # 剩餘 30 從點數包扣

    def test_waterfall_multiple_packages(self):
        """測試 waterfall：多個點數包按到期日排序"""
        from services.quota_service import QuotaService

        teacher = self._make_mock_teacher(current_period=None)

        # 第一個包只剩 10 秒（最早到期）
        pkg1 = self._make_mock_package(
            points_total=1000,
            points_used=990,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        # 第二個包有 5200 秒
        pkg2 = self._make_mock_package(
            points_total=5200,
            points_used=0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=180),
        )

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            pkg1,
            pkg2,
        ]

        # 扣除 30 秒（pkg1: 10 + pkg2: 20）
        usage_log = QuotaService.deduct_quota(
            db=db,
            teacher=teacher,
            student_id=None,
            assignment_id=None,
            feature_type="speech_recording",
            unit_count=30,
            unit_type="秒",
        )

        assert pkg1.points_used == 1000  # 第一個包用完
        assert pkg2.points_used == 20  # 剩餘 20 從第二個包扣

    def test_no_quota_raises_error(self):
        """測試完全沒有配額時報錯"""
        from services.quota_service import QuotaService

        teacher = self._make_mock_teacher(current_period=None)
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        with pytest.raises(HTTPException) as exc_info:
            QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_recording",
                unit_count=30,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402
        assert "NO_SUBSCRIPTION" in str(exc_info.value.detail)

    def test_hard_limit_exceeded(self):
        """測試超過 hard limit（含 20% buffer）報錯"""
        from services.quota_service import QuotaService

        # 訂閱 2000，已用 2350（超過 2000*1.2=2400 的 buffer 前）
        period = self._make_mock_period(quota_total=2000, quota_used=2350)
        teacher = self._make_mock_teacher(current_period=period)
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        # 再扣 100 秒 → 2450 > 2400 → 超過 hard limit
        with pytest.raises(HTTPException) as exc_info:
            QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_recording",
                unit_count=100,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402
        assert "QUOTA_HARD_LIMIT_EXCEEDED" in str(exc_info.value.detail)


class TestCheckQuota:
    """check_quota 測試"""

    def test_check_quota_with_subscription_sufficient(self):
        """測試訂閱配額足夠"""
        from services.quota_service import QuotaService

        period = MagicMock()
        period.quota_total = 2000
        period.quota_used = 100

        teacher = MagicMock()
        teacher.current_period = period

        assert QuotaService.check_quota(teacher, 50) is True

    def test_check_quota_subscription_insufficient_but_packages_cover(self):
        """測試訂閱不足但點數包能補"""
        from services.quota_service import QuotaService
        from models.credit_package import CreditPackage

        period = MagicMock()
        period.quota_total = 2000
        period.quota_used = 1980  # 只剩 20

        teacher = MagicMock()
        teacher.id = 1
        teacher.current_period = period

        pkg = MagicMock(spec=CreditPackage)
        pkg.points_remaining = 5000

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            pkg
        ]

        # 需要 50，訂閱 20 + 點數包 5000 → 足夠
        assert QuotaService.check_quota(teacher, 50, db) is True

    def test_check_quota_no_subscription_packages_only(self):
        """測試純點數包足夠"""
        from services.quota_service import QuotaService
        from models.credit_package import CreditPackage

        teacher = MagicMock()
        teacher.id = 1
        teacher.current_period = None

        pkg = MagicMock(spec=CreditPackage)
        pkg.points_remaining = 1000

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            pkg
        ]

        assert QuotaService.check_quota(teacher, 50, db) is True


class TestGetQuotaInfo:
    """get_quota_info 測試"""

    def test_quota_info_subscription_only(self):
        """測試只有訂閱的配額資訊"""
        from services.quota_service import QuotaService

        period = MagicMock()
        period.quota_total = 2000
        period.quota_used = 500
        period.status = "active"

        teacher = MagicMock()
        teacher.id = 1
        teacher.current_period = period

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            []
        )

        info = QuotaService.get_quota_info(teacher, db)

        assert info["quota_total"] == 2000
        assert info["quota_used"] == 500
        assert info["quota_remaining"] == 1500
        assert info["status"] == "active"
        assert info["subscription_total"] == 2000
        assert info["credit_packages_total"] == 0

    def test_quota_info_mixed_sources(self):
        """測試訂閱 + 點數包的混合配額資訊"""
        from services.quota_service import QuotaService
        from models.credit_package import CreditPackage

        period = MagicMock()
        period.quota_total = 2000
        period.quota_used = 2000
        period.status = "active"

        teacher = MagicMock()
        teacher.id = 1
        teacher.current_period = period

        pkg = MagicMock(spec=CreditPackage)
        pkg.points_total = 5200
        pkg.points_used = 300

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            pkg
        ]

        info = QuotaService.get_quota_info(teacher, db)

        assert info["quota_total"] == 7200  # 2000 + 5200
        assert info["quota_used"] == 2300  # 2000 + 300
        assert info["quota_remaining"] == 4900  # 0 + 4900
        assert info["subscription_total"] == 2000
        assert info["subscription_remaining"] == 0
        assert info["credit_packages_total"] == 5200
        assert info["credit_packages_remaining"] == 4900

    def test_quota_info_credit_packages_only(self):
        """測試純點數包配額資訊"""
        from services.quota_service import QuotaService
        from models.credit_package import CreditPackage

        teacher = MagicMock()
        teacher.id = 1
        teacher.current_period = None

        pkg = MagicMock(spec=CreditPackage)
        pkg.points_total = 2000
        pkg.points_used = 100

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            pkg
        ]

        info = QuotaService.get_quota_info(teacher, db)

        assert info["quota_total"] == 2000
        assert info["quota_used"] == 100
        assert info["quota_remaining"] == 1900
        assert info["status"] == "credit_packages_only"
        assert info["subscription_total"] == 0
        assert info["credit_packages_total"] == 2000
