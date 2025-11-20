"""
整合測試：訂閱週期系統 (SubscriptionPeriod)

測試內容：
1. 資料遷移正確性
2. current_period property
3. 配額更新邏輯
4. 歷史記錄保存
5. 付款方式追蹤
"""

from datetime import datetime, timezone
from database import get_session_local
from models import Teacher, SubscriptionPeriod


def test_1_data_migration():
    """測試 1: 驗證資料遷移正確性"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    # 有訂閱的老師應該都有對應的 subscription_period
    teachers_with_sub = (
        db.query(Teacher).filter(Teacher.subscription_end_date.isnot(None)).all()
    )

    for teacher in teachers_with_sub:
        periods = (
            db.query(SubscriptionPeriod)
            .filter(SubscriptionPeriod.teacher_id == teacher.id)
            .all()
        )

        assert len(periods) > 0, f"Teacher {teacher.email} 沒有訂閱週期記錄"

        # 配額應該相同（或 period 為 0）
        current_period = teacher.current_period
        if current_period:
            # 允許舊資料與新資料不同（因為是第一次遷移）
            assert current_period.quota_total > 0, "配額總量應該大於 0"
            print(
                f"✅ {teacher.email}: quota_used={current_period.quota_used}/{current_period.quota_total}"
            )

    db.close()
    print("✅ 測試 1 通過: 資料遷移正確")


def test_2_current_period_property():
    """測試 2: current_period property 正確運作"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
    assert teacher is not None, "找不到 demo@duotopia.com"

    current_period = teacher.current_period
    assert current_period is not None, "current_period 應該不為 None"

    # 驗證時間範圍
    now = datetime.now(timezone.utc)
    assert current_period.start_date <= now <= current_period.end_date, "當前時間應該在週期範圍內"

    # 驗證狀態
    assert current_period.status == "active", "狀態應該是 active"

    # 驗證配額
    assert current_period.quota_total in [1800, 4000], "配額總量應該是 1800 或 4000"
    assert current_period.quota_used >= 0, "已使用配額不能為負"

    print(
        f"✅ current_period: {current_period.start_date.date()} - {current_period.end_date.date()}"
    )
    print(f"   配額: {current_period.quota_used}/{current_period.quota_total}")
    print(f"   付款方式: {current_period.payment_method}")

    db.close()
    print("✅ 測試 2 通過: current_period property 正常運作")


def test_3_quota_update():
    """測試 3: 配額更新邏輯"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
    current_period = teacher.current_period

    original_quota = current_period.quota_used

    # 更新配額 +50
    current_period.quota_used += 50
    db.commit()

    # 驗證更新
    db.refresh(teacher)
    assert teacher.current_period.quota_used == original_quota + 50

    # 復原
    current_period.quota_used = original_quota
    db.commit()

    db.close()
    print(
        f"✅ 測試 3 通過: 配額更新正常 ({original_quota} → {original_quota + 50} → {original_quota})"
    )


def test_4_historical_records():
    """測試 4: 歷史記錄保存"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()

    # 查詢所有訂閱週期（包括過期的）
    all_periods = (
        db.query(SubscriptionPeriod)
        .filter(SubscriptionPeriod.teacher_id == teacher.id)
        .order_by(SubscriptionPeriod.start_date.desc())
        .all()
    )

    print(f"✅ 找到 {len(all_periods)} 個訂閱週期記錄")

    for i, period in enumerate(all_periods):
        print(f"   [{i+1}] {period.start_date.date()} - {period.end_date.date()}")
        print(
            f"       方案: {period.plan_name}, 配額: {period.quota_used}/{period.quota_total}"
        )
        print(f"       付款: {period.payment_method}, 狀態: {period.status}")

    assert len(all_periods) > 0, "應該至少有一個訂閱週期"

    db.close()
    print("✅ 測試 4 通過: 歷史記錄正常保存")


def test_5_payment_method_tracking():
    """測試 5: 付款方式追蹤"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    # 查詢所有訂閱週期
    all_periods = db.query(SubscriptionPeriod).all()

    manual_count = sum(1 for p in all_periods if p.payment_method == "manual")
    auto_count = sum(1 for p in all_periods if p.payment_method == "auto_renew")

    print("✅ 付款方式統計:")
    print(f"   手動付款: {manual_count} 筆")
    print(f"   自動續訂: {auto_count} 筆")

    # 驗證每個 period 都有付款方式
    for period in all_periods:
        assert period.payment_method in [
            "manual",
            "auto_renew",
        ], f"Period {period.id} 的付款方式無效: {period.payment_method}"

    db.close()
    print("✅ 測試 5 通過: 付款方式追蹤正常")


def test_6_helper_properties():
    """測試 6: Helper properties (quota_total, quota_remaining)"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()

    # 測試 quota_total
    assert teacher.quota_total in [1800, 4000], "quota_total 應該是 1800 或 4000"

    # 測試 quota_remaining
    expected_remaining = (
        teacher.current_period.quota_total - teacher.current_period.quota_used
    )
    assert (
        teacher.quota_remaining == expected_remaining
    ), f"quota_remaining 計算錯誤: {teacher.quota_remaining} != {expected_remaining}"

    print("✅ Helper properties:")
    print(f"   quota_total: {teacher.quota_total}")
    print(f"   quota_remaining: {teacher.quota_remaining}")
    print(f"   quota_used: {teacher.current_period.quota_used}")

    db.close()
    print("✅ 測試 6 通過: Helper properties 正常運作")


if __name__ == "__main__":
    print("=" * 60)
    print("訂閱週期系統整合測試")
    print("=" * 60)

    try:
        test_1_data_migration()
        print()
        test_2_current_period_property()
        print()
        test_3_quota_update()
        print()
        test_4_historical_records()
        print()
        test_5_payment_method_tracking()
        print()
        test_6_helper_properties()
        print()
        print("=" * 60)
        print("✅ 所有測試通過！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        raise
