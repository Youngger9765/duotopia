#!/usr/bin/env python3
"""
獨立的訂閱計算器測試
不依賴資料庫，可直接執行驗證邏輯

測試固定每月訂閱週期：+1 個月，收全額

執行方式：
  cd backend && python3 tests/unit/test_subscription_calculator_standalone.py
"""

import sys
from pathlib import Path

# 添加 backend 目錄到 Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone  # noqa: E402
from services.subscription_calculator import SubscriptionCalculator  # noqa: E402


def test_subscription_normal_day():
    """測試一般日期：3/5 → 4/5"""
    start_date = datetime(2026, 3, 5, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2026, 4, 5, tzinfo=timezone.utc).date()
    assert amount == 299
    assert details["pricing_method"] == "fixed_monthly"
    print("pass test_subscription_normal_day")


def test_subscription_on_first_day():
    """測試 1 號訂閱：10/1 → 11/1"""
    start_date = datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 11, 1, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_subscription_on_first_day")


def test_subscription_jan_31_to_feb_28():
    """測試月末邊界：1/31 → 2/28（平年）"""
    start_date = datetime(2025, 1, 31, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 2, 28, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_subscription_jan_31_to_feb_28")


def test_subscription_jan_31_to_feb_29_leap_year():
    """測試閏年：1/31 → 2/29"""
    start_date = datetime(2024, 1, 31, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2024, 2, 29, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_subscription_jan_31_to_feb_29_leap_year")


def test_subscription_mar_31_to_apr_30():
    """測試月末邊界：3/31 → 4/30"""
    start_date = datetime(2026, 3, 31, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2026, 4, 30, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_subscription_mar_31_to_apr_30")


def test_subscription_feb_28_to_mar_28():
    """測試 2/28 → 3/28"""
    start_date = datetime(2025, 2, 28, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2025, 3, 28, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_subscription_feb_28_to_mar_28")


def test_december_to_january():
    """測試跨年：12/15 → 1/15"""
    start_date = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "Tutor Teachers"
    )

    assert end_date.date() == datetime(2026, 1, 15, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_december_to_january")


def test_school_teachers_plan():
    """測試 School Teachers 方案（599元）"""
    start_date = datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
        start_date, "School Teachers"
    )

    assert end_date.date() == datetime(2025, 11, 15, tzinfo=timezone.utc).date()
    assert amount == 599
    assert details["full_price"] == 599
    print("pass test_school_teachers_plan")


def test_renewal_calculation():
    """測試續訂：4/5 → 5/5"""
    current_end_date = datetime(2026, 4, 5, 0, 0, 0, tzinfo=timezone.utc)
    new_end_date, amount = SubscriptionCalculator.calculate_renewal(
        current_end_date, "Tutor Teachers"
    )

    assert new_end_date.date() == datetime(2026, 5, 5, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_renewal_calculation")


def test_renewal_cross_year():
    """測試跨年續訂：12/15 → 1/15"""
    current_end_date = datetime(2025, 12, 15, 0, 0, 0, tzinfo=timezone.utc)
    new_end_date, amount = SubscriptionCalculator.calculate_renewal(
        current_end_date, "Tutor Teachers"
    )

    assert new_end_date.date() == datetime(2026, 1, 15, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_renewal_cross_year")


def test_renewal_month_end_boundary():
    """測試續訂月末邊界：1/31 → 2/28"""
    current_end_date = datetime(2025, 1, 31, 0, 0, 0, tzinfo=timezone.utc)
    new_end_date, amount = SubscriptionCalculator.calculate_renewal(
        current_end_date, "Tutor Teachers"
    )

    assert new_end_date.date() == datetime(2025, 2, 28, tzinfo=timezone.utc).date()
    assert amount == 299
    print("pass test_renewal_month_end_boundary")


if __name__ == "__main__":
    print("=" * 70)
    print("訂閱計算器獨立測試（固定 +1 個月）")
    print("=" * 70)

    tests = [
        test_subscription_normal_day,
        test_subscription_on_first_day,
        test_subscription_jan_31_to_feb_28,
        test_subscription_jan_31_to_feb_29_leap_year,
        test_subscription_mar_31_to_apr_30,
        test_subscription_feb_28_to_mar_28,
        test_december_to_january,
        test_school_teachers_plan,
        test_renewal_calculation,
        test_renewal_cross_year,
        test_renewal_month_end_boundary,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"FAIL {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"FAIL {test_func.__name__}: Unexpected error: {e}")
            failed += 1

    print("=" * 70)
    print(f"結果: {passed}/{len(tests)} 通過")

    if failed == 0:
        print("所有測試通過！")
        exit(0)
    else:
        print(f"{failed} 個測試失敗")
        exit(1)
