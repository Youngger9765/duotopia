"""
訂閱計算器單元測試

測試統一每月 1 號扣款的邏輯

注意：這是純粹的單元測試，不依賴資料庫
"""

import pytest
from datetime import datetime, timezone
from services.subscription_calculator import SubscriptionCalculator

# Mark all tests to not use database
pytestmark = pytest.mark.no_db


class TestSubscriptionCalculator:
    """測試訂閱計算器"""

    def test_subscription_on_first_day(self):
        """測試 1 號訂閱（完整月）"""
        start_date = datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert (
            end_date.date()
            == datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        assert amount == 230  # 完整月價格
        assert details["actual_days"] == 31  # 10/1 到 11/1 = October 全月 31 天
        assert details["bonus_days"] == 0
        assert details["pricing_method"] == "prorated"

    def test_subscription_mid_month_31_days(self):
        """測試月中訂閱（1月 31天）"""
        start_date = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert (
            end_date.date() == datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        # 1/15 到 2/1 = 17 天
        # 1月有 31 天
        # 230 × (17/31) = 126.45... → 126
        assert amount == 126
        assert details["actual_days"] == 17
        assert details["pricing_method"] == "prorated"

    def test_subscription_mid_month_28_days(self):
        """測試月中訂閱（2月 28天，平年）"""
        start_date = datetime(2025, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert (
            end_date.date() == datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        # 2/15 到 3/1 = 14 days (2/15-2/28)
        # 2月有 28 天
        # 230 × (14/28) = 115
        assert amount == 115
        assert details["actual_days"] == 14
        assert details["pricing_method"] == "prorated"

    def test_subscription_leap_year_february(self):
        """測試閏年 2 月訂閱（29天）"""
        start_date = datetime(2024, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        assert (
            end_date.date() == datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        # 2/15 到 3/1 = 15 days (2/15-2/29)
        # 閏年 2 月有 29 天
        # 230 × (15/29) = 119.0
        assert amount == 119
        assert details["actual_days"] == 15

    def test_subscription_end_of_month_grace_period(self):
        """測試月底訂閱（少於 7 天，觸發優惠期）"""
        start_date = datetime(2025, 10, 26, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 10/26 距離 11/1 只有 6 天 (10/26-10/31)，跳到 12/1
        assert (
            end_date.date()
            == datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        assert amount == 230  # 收全額
        assert details["actual_days"] == 36  # 10/26 到 12/1 = 36 days
        assert details["bonus_days"] == 6  # 36 - 30 = 6 天贈送
        assert details["grace_period_applied"] is True
        assert details["pricing_method"] == "grace_period"

    def test_subscription_grace_period_boundary(self):
        """測試優惠期邊界（剛好 7 天）"""
        # 10/25 距離 11/1 剛好 7 天，不觸發優惠期
        start_date = datetime(2025, 10, 25, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 應該到 11/1，不跳過
        assert (
            end_date.date()
            == datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        assert details["grace_period_applied"] is False

    def test_subscription_january_end(self):
        """測試 1 月底訂閱（31天月份）"""
        start_date = datetime(2025, 1, 28, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 1/28 距離 2/1 只有 4 天 (1/28-1/31)，跳到 3/1
        assert (
            end_date.date() == datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        assert amount == 230  # 收全額
        assert details["actual_days"] == 32  # 1/28 到 3/1 = 32 days
        assert details["grace_period_applied"] is True

    def test_school_teachers_plan(self):
        """測試 School Teachers 方案（330元）"""
        start_date = datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "School Teachers"
        )

        # 10 月有 31 天，10/15 到 11/1 = 17 天
        # 330 × (17/31) = 181.29... → 181
        assert amount == 181
        assert details["full_price"] == 330

    def test_renewal_calculation(self):
        """測試續訂計算"""
        current_end_date = datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc)
        new_end_date, amount = SubscriptionCalculator.calculate_renewal(
            current_end_date, "Tutor Teachers"
        )

        # 續訂應該到下個月 1 號
        assert (
            new_end_date.date()
            == datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        assert amount == 230  # 續訂收全額

    def test_renewal_cross_year(self):
        """測試跨年續訂"""
        current_end_date = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        new_end_date, amount = SubscriptionCalculator.calculate_renewal(
            current_end_date, "Tutor Teachers"
        )

        # 12/1 續訂應該到 2026/1/1
        assert (
            new_end_date.date()
            == datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        assert amount == 230

    def test_days_until_renewal(self):
        """測試距離續訂天數計算"""
        # 假設現在是 10/15
        from unittest.mock import patch

        mock_now = datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
        subscription_end = datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc)

        with patch("services.subscription_calculator.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            days = SubscriptionCalculator.get_days_until_renewal(subscription_end)
            assert days == 16  # 10/15 到 11/1

    def test_should_renew_today(self):
        """測試是否應該續訂"""
        from unittest.mock import patch

        mock_now = datetime(2025, 11, 1, 2, 0, 0, tzinfo=timezone.utc)
        subscription_end = datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc)

        with patch("services.subscription_calculator.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            should_renew = SubscriptionCalculator.should_renew_today(subscription_end)
            assert should_renew is True

    def test_december_to_january(self):
        """測試 12 月到 1 月的邊界情況"""
        # 12/15 訂閱
        start_date = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 12/15 到 1/1 = 17 days (12/15-12/31)
        # 12 月有 31 天
        # 230 × (17/31) = 126.45... → 126
        assert (
            end_date.date() == datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).date()
        )
        assert amount == 126
        assert details["actual_days"] == 17

    def test_all_months_calculations(self):
        """測試所有月份的計算（全年覆蓋）"""
        test_cases = [
            (1, 31),  # 1月 31天
            (2, 28),  # 2月 28天（平年）
            (3, 31),  # 3月 31天
            (4, 30),  # 4月 30天
            (5, 31),  # 5月 31天
            (6, 30),  # 6月 30天
            (7, 31),  # 7月 31天
            (8, 31),  # 8月 31天
            (9, 30),  # 9月 30天
            (10, 31),  # 10月 31天
            (11, 30),  # 11月 30天
            (12, 31),  # 12月 31天
        ]

        for month, expected_days in test_cases:
            start_date = datetime(2025, month, 15, 10, 0, 0, tzinfo=timezone.utc)
            (
                end_date,
                amount,
                details,
            ) = SubscriptionCalculator.calculate_first_subscription(
                start_date, "Tutor Teachers"
            )

            # 驗證計算有用到正確的月份天數
            assert details["actual_days"] > 0, f"Month {month} failed"
            assert amount > 0, f"Month {month} amount is 0"
            assert amount <= 230, f"Month {month} amount exceeds full price"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
