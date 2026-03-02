"""
訂閱計算器單元測試

測試固定每月訂閱週期邏輯：
1. 首次訂閱：從訂閱日 +1 個月，收全額
2. 續訂：從到期日 +1 個月，收全額
3. 月末邊界：1/31 → 2/28

注意：這是純粹的單元測試，不依賴資料庫
"""

import pytest
from datetime import datetime, timezone
from services.subscription_calculator import SubscriptionCalculator

# Mark all tests to not use database
pytestmark = pytest.mark.no_db


class TestSubscriptionCalculator:
    """測試訂閱計算器"""

    def test_subscription_normal_day(self):
        """測試一般日期訂閱：3/5 → 4/5"""
        start_date = datetime(2026, 3, 5, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert end_date.date() == datetime(2026, 4, 5, tzinfo=timezone.utc).date()
        assert amount == 299
        assert details["pricing_method"] == "fixed_monthly"

    def test_subscription_on_first_day(self):
        """測試 1 號訂閱：10/1 → 11/1"""
        start_date = datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert end_date.date() == datetime(2025, 11, 1, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_subscription_jan_31_to_feb_28(self):
        """測試月末邊界：1/31 → 2/28（平年）"""
        start_date = datetime(2025, 1, 31, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 2 月沒有 31 號，取 2/28
        assert end_date.date() == datetime(2025, 2, 28, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_subscription_jan_31_to_feb_29_leap_year(self):
        """測試閏年月末邊界：1/31 → 2/29"""
        start_date = datetime(2024, 1, 31, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 2024 閏年，2 月有 29 天
        assert end_date.date() == datetime(2024, 2, 29, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_subscription_mar_31_to_apr_30(self):
        """測試月末邊界：3/31 → 4/30"""
        start_date = datetime(2026, 3, 31, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 4 月沒有 31 號，取 4/30
        assert end_date.date() == datetime(2026, 4, 30, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_subscription_feb_28_to_mar_28(self):
        """測試 2/28 → 3/28"""
        start_date = datetime(2025, 2, 28, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert end_date.date() == datetime(2025, 3, 28, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_subscription_december_to_january(self):
        """測試跨年：12/15 → 1/15"""
        start_date = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert end_date.date() == datetime(2026, 1, 15, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_school_teachers_plan(self):
        """測試 School Teachers 方案（599元）"""
        start_date = datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "School Teachers"
        )

        assert end_date.date() == datetime(2025, 11, 15, tzinfo=timezone.utc).date()
        assert amount == 599
        assert details["full_price"] == 599

    def test_renewal_calculation(self):
        """測試續訂計算：4/5 → 5/5"""
        current_end_date = datetime(2026, 4, 5, 0, 0, 0, tzinfo=timezone.utc)
        new_end_date, amount = SubscriptionCalculator.calculate_renewal(
            current_end_date, "Tutor Teachers"
        )

        assert new_end_date.date() == datetime(2026, 5, 5, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_renewal_cross_year(self):
        """測試跨年續訂：12/15 → 1/15"""
        current_end_date = datetime(2025, 12, 15, 0, 0, 0, tzinfo=timezone.utc)
        new_end_date, amount = SubscriptionCalculator.calculate_renewal(
            current_end_date, "Tutor Teachers"
        )

        assert new_end_date.date() == datetime(2026, 1, 15, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_renewal_month_end_boundary(self):
        """測試續訂月末邊界：1/31 → 2/28"""
        current_end_date = datetime(2025, 1, 31, 0, 0, 0, tzinfo=timezone.utc)
        new_end_date, amount = SubscriptionCalculator.calculate_renewal(
            current_end_date, "Tutor Teachers"
        )

        assert new_end_date.date() == datetime(2025, 2, 28, tzinfo=timezone.utc).date()
        assert amount == 299

    def test_days_until_renewal(self):
        """測試距離續訂天數計算"""
        from unittest.mock import patch

        mock_now = datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
        subscription_end = datetime(2025, 11, 15, 0, 0, 0, tzinfo=timezone.utc)

        with patch("services.subscription_calculator.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            days = SubscriptionCalculator.get_days_until_renewal(subscription_end)
            assert days == 30  # 10/15 到 11/15

    def test_should_renew_today(self):
        """測試是否應該續訂"""
        from unittest.mock import patch

        mock_now = datetime(2025, 11, 15, 2, 0, 0, tzinfo=timezone.utc)
        subscription_end = datetime(2025, 11, 15, 0, 0, 0, tzinfo=timezone.utc)

        with patch("services.subscription_calculator.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            should_renew = SubscriptionCalculator.should_renew_today(subscription_end)
            assert should_renew is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
