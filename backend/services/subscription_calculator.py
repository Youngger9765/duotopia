"""
訂閱計算服務 - 統一每月 1 號扣款

規則：
1. 所有用戶統一在每月 1 號續訂
2. 首次訂閱收全額，直接用到下個月 1 號
3. 如果剩餘天數 < 7 天，跳到下下個月 1 號
"""

from datetime import datetime, timedelta, timezone
from typing import Tuple
from calendar import monthrange


class SubscriptionCalculator:
    """訂閱計算器"""

    # 方案價格
    PLAN_PRICES = {
        "Tutor Teachers": 230,
        "School Teachers": 330,
    }

    # 月底優惠門檻（剩餘天數少於此數字，跳到下下個月）
    GRACE_PERIOD_DAYS = 7

    @staticmethod
    def calculate_first_subscription(
        start_date: datetime, plan_name: str
    ) -> Tuple[datetime, int, dict]:
        """
        計算首次訂閱的到期日和金額

        Args:
            start_date: 訂閱開始日期
            plan_name: 方案名稱 ("Tutor Teachers" or "School Teachers")

        Returns:
            (到期日, 應付金額, 詳細資訊)
        """
        # 取得方案價格（完整月）
        full_price = SubscriptionCalculator.PLAN_PRICES.get(plan_name, 230)

        # 計算下個月 1 號
        next_month_first = SubscriptionCalculator._get_next_month_first(start_date)

        # 計算剩餘天數（使用日期計算，不含時間）
        # 例：1/15 任何時間訂閱 → 算作 1/15 一整天
        start_date_only = start_date.date()
        next_month_date_only = next_month_first.date()
        days_until_next_month = (next_month_date_only - start_date_only).days

        # 如果剩餘天數太少（< 7 天），跳到下下個月
        if days_until_next_month < SubscriptionCalculator.GRACE_PERIOD_DAYS:
            # 跳過下個月，直接到下下個月 1 號
            end_date = SubscriptionCalculator._get_next_month_first(next_month_first)
            # 使用日期計算，確保一致性
            actual_days = (end_date.date() - start_date_only).days

            # 收全額（因為給了超過 30 天）
            amount = full_price
            grace_period_applied = True
            bonus_days = actual_days - 30  # 超過 30 天的部分是贈送

        else:
            # 正常情況：到下個月 1 號
            end_date = next_month_first
            actual_days = days_until_next_month

            # 取得當月實際天數（考慮閏年）
            days_in_current_month = monthrange(start_date.year, start_date.month)[1]

            # 按當月實際天數比例計算金額（四捨五入）
            amount = round(full_price * (actual_days / days_in_current_month))
            grace_period_applied = False
            bonus_days = 0

        details = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "actual_days": actual_days,
            "full_price": full_price,
            "amount": amount,
            "bonus_days": bonus_days,
            "grace_period_applied": grace_period_applied,
            "plan_name": plan_name,
            "pricing_method": "grace_period" if grace_period_applied else "prorated"
        }

        return end_date, amount, details

    @staticmethod
    def calculate_renewal(
        current_end_date: datetime, plan_name: str
    ) -> Tuple[datetime, int]:
        """
        計算續訂的到期日和金額

        Args:
            current_end_date: 當前到期日（應該是某月 1 號）
            plan_name: 方案名稱

        Returns:
            (新到期日, 應付金額)
        """
        # 續訂：延長到下個月 1 號
        next_month_first = SubscriptionCalculator._get_next_month_first(
            current_end_date
        )
        amount = SubscriptionCalculator.PLAN_PRICES.get(plan_name, 230)

        return next_month_first, amount

    @staticmethod
    def _get_next_month_first(date: datetime) -> datetime:
        """
        取得下個月的 1 號 00:00:00

        Args:
            date: 基準日期

        Returns:
            下個月 1 號的 datetime
        """
        # 計算下個月
        if date.month == 12:
            next_month = 1
            next_year = date.year + 1
        else:
            next_month = date.month + 1
            next_year = date.year

        # 建立下個月 1 號 00:00:00
        next_month_first = datetime(
            year=next_year,
            month=next_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=date.tzinfo or timezone.utc,
        )

        return next_month_first

    @staticmethod
    def get_days_until_renewal(subscription_end_date: datetime) -> int:
        """
        計算距離續訂還有幾天

        Args:
            subscription_end_date: 訂閱到期日

        Returns:
            剩餘天數
        """
        now = datetime.now(timezone.utc)
        if subscription_end_date <= now:
            return 0

        return (subscription_end_date - now).days

    @staticmethod
    def should_renew_today(subscription_end_date: datetime) -> bool:
        """
        檢查今天是否應該續訂

        Args:
            subscription_end_date: 訂閱到期日

        Returns:
            True if 今天是到期日
        """
        today = datetime.now(timezone.utc).date()
        end_date = subscription_end_date.date()

        return today == end_date


# ============ 使用範例 ============
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 訂閱計算測試")
    print("=" * 70)

    # 測試情境
    test_cases = [
        ("10/1 訂閱", datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.utc)),
        ("10/5 訂閱", datetime(2025, 10, 5, 10, 0, 0, tzinfo=timezone.utc)),
        ("10/15 訂閱", datetime(2025, 10, 15, 10, 0, 0, tzinfo=timezone.utc)),
        ("10/25 訂閱", datetime(2025, 10, 25, 10, 0, 0, tzinfo=timezone.utc)),
        ("10/28 訂閱", datetime(2025, 10, 28, 10, 0, 0, tzinfo=timezone.utc)),
    ]

    for name, start_date in test_cases:
        end_date, amount, details = SubscriptionCalculator.calculate_first_subscription(
            start_date, "Tutor Teachers"
        )

        print(f"\n{name}")
        print(f"  訂閱日期: {start_date.date()}")
        print(f"  到期日: {end_date.date()}")
        print(f"  應付金額: TWD {amount}")
        print(f"  實際天數: {details['actual_days']} 天")
        print(f"  贈送天數: {details['bonus_days']} 天")
        if details["grace_period_applied"]:
            print(f"  ✨ 優惠：跳過下個月 1 號，直接到下下個月！")

    print("\n" + "=" * 70)
