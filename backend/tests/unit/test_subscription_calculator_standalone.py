#!/usr/bin/env python3
"""
獨立的訂閱計算器測試
不依賴資料庫，可直接執行驗證邏輯

執行方式：
  cd backend && python3 tests/unit/test_subscription_calculator_standalone.py
"""

import sys
from pathlib import Path

# 添加 backend 目錄到 Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from services.subscription_calculator import SubscriptionCalculator


def test_subscription_on_first_day():
    """測試 1 號訂閱（完整月）"""
    start_date = datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 230
    assert details['actual_days'] == 31
    print("✅ test_subscription_on_first_day")


def test_subscription_mid_month_31_days():
    """測試月中訂閱（1月 31天）"""
    start_date = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 126  # 230 × (17/31) = 126.45 → 126
    assert details['actual_days'] == 17
    print("✅ test_subscription_mid_month_31_days")


def test_subscription_mid_month_28_days():
    """測試月中訂閱（2月 28天，平年）"""
    start_date = datetime(2025, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 115  # 230 × (14/28) = 115
    assert details['actual_days'] == 14
    print("✅ test_subscription_mid_month_28_days")


def test_subscription_leap_year_february():
    """測試閏年 2 月訂閱（29天）"""
    start_date = datetime(2024, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 119  # 230 × (15/29) = 118.97 → 119
    assert details['actual_days'] == 15
    print("✅ test_subscription_leap_year_february")


def test_subscription_end_of_month_grace_period():
    """測試月底訂閱（少於 7 天，觸發優惠期）"""
    start_date = datetime(2025, 10, 26, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 230
    assert details['actual_days'] == 36
    assert details['bonus_days'] == 6
    assert details['grace_period_applied'] is True
    print("✅ test_subscription_end_of_month_grace_period")


def test_subscription_grace_period_boundary():
    """測試優惠期邊界（剛好 7 天）"""
    start_date = datetime(2025, 10, 25, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert details['grace_period_applied'] is False
    print("✅ test_subscription_grace_period_boundary")


def test_school_teachers_plan():
    """測試 School Teachers 方案（330元）"""
    start_date = datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "School Teachers"
    )

    assert amount == 181  # 330 × (17/31) = 180.6 → 181
    assert details['full_price'] == 330
    print("✅ test_school_teachers_plan")


def test_renewal_calculation():
    """測試續訂計算"""
    current_end_date = datetime(2025, 11, 1, 0, 0, 0, tzinfo=timezone.utc)
    new_end_date, amount = SubscriptionCalculator.calculate_renewal(
        current_end_date, "Tutor Teachers"
    )

    assert new_end_date.date() == datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 230
    print("✅ test_renewal_calculation")


def test_renewal_cross_year():
    """測試跨年續訂"""
    current_end_date = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
    new_end_date, amount = SubscriptionCalculator.calculate_renewal(
        current_end_date, "Tutor Teachers"
    )

    assert new_end_date.date() == datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 230
    print("✅ test_renewal_cross_year")


def test_december_to_january():
    """測試 12 月到 1 月的邊界情況"""
    start_date = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).date()
    assert amount == 126  # 230 × (17/31) = 126
    assert details['actual_days'] == 17
    print("✅ test_december_to_january")


def test_all_months_calculations():
    """測試所有月份的計算（確保沒有月份被遺漏）"""
    # 測試每個月的 15 號訂閱
    months_data = [
        (1, 31), (2, 28), (3, 31), (4, 30), (5, 31), (6, 30),
        (7, 31), (8, 31), (9, 30), (10, 31), (11, 30), (12, 31)
    ]

    for month, days_in_month in months_data:
        start_date = datetime(2025, month, 15, 10, 0, 0, tzinfo=timezone.utc)
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        # 計算預期天數：從 15 號到下個月 1 號
        expected_days = days_in_month - 15 + 1
        assert details['actual_days'] == expected_days, \
            f"Month {month}: expected {expected_days} days, got {details['actual_days']}"

    print("✅ test_all_months_calculations")


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 訂閱計算器獨立測試")
    print("=" * 70)

    tests = [
        test_subscription_on_first_day,
        test_subscription_mid_month_31_days,
        test_subscription_mid_month_28_days,
        test_subscription_leap_year_february,
        test_subscription_end_of_month_grace_period,
        test_subscription_grace_period_boundary,
        test_school_teachers_plan,
        test_renewal_calculation,
        test_renewal_cross_year,
        test_december_to_january,
        test_all_months_calculations,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__}: Unexpected error: {e}")
            failed += 1

    print("=" * 70)
    print(f"結果: {passed}/{len(tests)} 通過")

    if failed == 0:
        print("✅✅✅ 所有測試通過！")
        exit(0)
    else:
        print(f"❌ {failed} 個測試失敗")
        exit(1)
