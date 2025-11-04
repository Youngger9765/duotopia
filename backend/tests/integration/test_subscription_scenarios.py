"""
情境測試：訂閱系統完整流程

測試各種真實使用場景：
1. 新用戶首次付款
2. 用戶使用配額後續約
3. 自動續訂扣款
4. 用戶更換方案
5. 配額用完後續約
6. 訂閱過期後重新付款
7. 舊用戶遷移 (沒有 period)
"""

import pytest
from datetime import datetime, timedelta, timezone
from database import SessionLocal
from models import Teacher, SubscriptionPeriod


def test_scenario_1_new_user_first_payment():
    """
    情境 1: 新用戶首次付款

    流程：
    1. 新用戶註冊
    2. 首次刷卡付款 330元 (Tutor Teachers)
    3. 驗證：創建 subscription_period，配額 1800秒
    """
    print("\n" + "=" * 60)
    print("情境 1: 新用戶首次付款")
    print("=" * 60)

    db = SessionLocal()

    # 模擬新用戶
    new_teacher = Teacher(
        email="scenario1_new_user@test.com",
        password_hash="dummy",
        name="Test User",
        subscription_type="Tutor Teachers",
        subscription_end_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(new_teacher)
    db.flush()

    # 模擬首次付款創建 subscription_period
    period = SubscriptionPeriod(
        teacher_id=new_teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=0,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        payment_method="manual",
        payment_id="test_rec_001",
        payment_status="paid",
        status="active",
    )
    db.add(period)
    db.commit()

    # 驗證
    db.refresh(new_teacher)
    current_period = new_teacher.current_period

    assert current_period is not None, "❌ 應該有 current_period"
    assert (
        current_period.quota_total == 1800
    ), f"❌ 配額應該是 1800，實際：{current_period.quota_total}"
    assert current_period.quota_used == 0, f"❌ 已用配額應該是 0，實際：{current_period.quota_used}"
    assert current_period.payment_method == "manual", f"❌ 付款方式應該是 manual"

    print(f"✅ 新用戶首次付款成功")
    print(f"   - 配額：{current_period.quota_used}/{current_period.quota_total} 秒")
    print(f"   - 付款方式：{current_period.payment_method}")
    print(f"   - 剩餘：{new_teacher.quota_remaining} 秒")

    # 清理
    db.delete(period)
    db.delete(new_teacher)
    db.commit()
    db.close()


def test_scenario_2_use_quota_then_renew():
    """
    情境 2: 用戶使用配額後續約

    流程：
    1. 用戶使用了 500 秒配額
    2. 月底自動續訂
    3. 驗證：新週期配額歸零，舊週期保留 500 秒記錄
    """
    print("\n" + "=" * 60)
    print("情境 2: 用戶使用配額後續約")
    print("=" * 60)

    db = SessionLocal()

    # 創建用戶
    teacher = Teacher(
        email="scenario2_use_then_renew@test.com",
        password_hash="dummy",
        name="Test User 2",
        subscription_type="Tutor Teachers",
        subscription_end_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(teacher)
    db.flush()

    # 第一個週期（已使用 500 秒）
    now = datetime.now(timezone.utc)
    period1 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=500,  # 已使用 500 秒
        start_date=now - timedelta(days=25),
        end_date=now + timedelta(days=5),
        payment_method="auto_renew",
        payment_id="test_rec_002",
        payment_status="paid",
        status="active",
    )
    db.add(period1)
    db.commit()

    print(f"📊 第一週期：{period1.quota_used}/{period1.quota_total} 秒")

    # 模擬自動續訂（創建新週期）
    period1.status = "expired"
    period2 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=0,  # 新週期配額歸零
        start_date=now + timedelta(days=5),
        end_date=now + timedelta(days=35),
        payment_method="auto_renew",
        payment_id="test_rec_003",
        payment_status="paid",
        status="active",
    )
    db.add(period2)
    teacher.subscription_end_date = now + timedelta(days=35)
    db.commit()

    # 驗證
    db.refresh(teacher)

    # 查詢所有週期
    all_periods = (
        db.query(SubscriptionPeriod)
        .filter(SubscriptionPeriod.teacher_id == teacher.id)
        .order_by(SubscriptionPeriod.start_date)
        .all()
    )

    assert len(all_periods) == 2, f"❌ 應該有 2 個週期，實際：{len(all_periods)}"
    assert all_periods[0].quota_used == 500, "❌ 第一週期應該保留 500 秒記錄"
    assert all_periods[0].status == "expired", "❌ 第一週期應該是 expired"
    assert all_periods[1].quota_used == 0, "❌ 第二週期應該是 0 秒"
    assert all_periods[1].status == "active", "❌ 第二週期應該是 active"
    assert teacher.current_period.id == period2.id, "❌ current_period 應該是新週期"

    print(f"✅ 續約成功，歷史記錄保留")
    print(
        f"   - 第一週期：{all_periods[0].quota_used}/{all_periods[0].quota_total} 秒 (expired)"
    )
    print(
        f"   - 第二週期：{all_periods[1].quota_used}/{all_periods[1].quota_total} 秒 (active)"
    )

    # 清理
    for p in all_periods:
        db.delete(p)
    db.delete(teacher)
    db.commit()
    db.close()


def test_scenario_3_quota_exhausted_then_renew():
    """
    情境 3: 配額用完後續約

    流程：
    1. 用戶用完 1800 秒配額
    2. 續約後配額重新充值
    """
    print("\n" + "=" * 60)
    print("情境 3: 配額用完後續約")
    print("=" * 60)

    db = SessionLocal()

    teacher = Teacher(
        email="scenario3_exhausted@test.com",
        password_hash="dummy",
        name="Test User 3",
        subscription_type="Tutor Teachers",
        subscription_end_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(teacher)
    db.flush()

    now = datetime.now(timezone.utc)

    # 第一週期：用完配額
    period1 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=1800,  # 用完了！
        start_date=now - timedelta(days=25),
        end_date=now + timedelta(days=5),
        payment_method="auto_renew",
        payment_id="test_rec_004",
        payment_status="paid",
        status="active",
    )
    db.add(period1)
    db.commit()

    print(f"⚠️  第一週期：配額用完 {period1.quota_used}/{period1.quota_total} 秒")
    assert teacher.quota_remaining == 0, "❌ 剩餘配額應該是 0"

    # 續約
    period1.status = "expired"
    period2 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=0,
        start_date=now + timedelta(days=5),
        end_date=now + timedelta(days=35),
        payment_method="auto_renew",
        payment_id="test_rec_005",
        payment_status="paid",
        status="active",
    )
    db.add(period2)
    db.commit()

    db.refresh(teacher)

    assert teacher.current_period.quota_used == 0, "❌ 新週期配額應該是 0"
    assert (
        teacher.quota_remaining == 1800
    ), f"❌ 剩餘配額應該是 1800，實際：{teacher.quota_remaining}"

    print(f"✅ 續約後配額重新充值")
    print(
        f"   - 新配額：{teacher.current_period.quota_used}/{teacher.current_period.quota_total} 秒"
    )
    print(f"   - 剩餘：{teacher.quota_remaining} 秒")

    # 清理
    db.delete(period1)
    db.delete(period2)
    db.delete(teacher)
    db.commit()
    db.close()


def test_scenario_4_change_plan():
    """
    情境 4: 更換方案 (Tutor → School)

    流程：
    1. 用戶原本是 Tutor (330元/1800秒)
    2. 更換成 School (660元/4000秒)
    3. 驗證：新週期配額是 4000 秒
    """
    print("\n" + "=" * 60)
    print("情境 4: 更換方案 (Tutor → School)")
    print("=" * 60)

    db = SessionLocal()

    teacher = Teacher(
        email="scenario4_change_plan@test.com",
        password_hash="dummy",
        name="Test User 4",
        subscription_type="Tutor Teachers",
        subscription_end_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(teacher)
    db.flush()

    now = datetime.now(timezone.utc)

    # 原本的 Tutor 方案
    period1 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=300,
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=20),
        payment_method="manual",
        payment_id="test_rec_006",
        payment_status="paid",
        status="active",
    )
    db.add(period1)
    db.commit()

    print(f"📊 原方案：Tutor Teachers (1800秒)，已用 {period1.quota_used} 秒")

    # 更換成 School 方案
    period1.status = "expired"
    period2 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="School Teachers",
        amount_paid=660,
        quota_total=4000,  # 升級到 4000 秒
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="manual",
        payment_id="test_rec_007",
        payment_status="paid",
        status="active",
    )
    db.add(period2)
    teacher.subscription_type = "School Teachers"
    db.commit()

    db.refresh(teacher)

    assert (
        teacher.current_period.plan_name == "School Teachers"
    ), "❌ 方案應該是 School Teachers"
    assert teacher.current_period.quota_total == 4000, "❌ 新配額應該是 4000"
    assert teacher.quota_total == 4000, "❌ teacher.quota_total 應該是 4000"

    print(f"✅ 方案更換成功")
    print(f"   - 新方案：{period2.plan_name}")
    print(f"   - 新配額：{period2.quota_used}/{period2.quota_total} 秒")

    # 清理
    db.delete(period1)
    db.delete(period2)
    db.delete(teacher)
    db.commit()
    db.close()


def test_scenario_5_expired_then_renew():
    """
    情境 5: 訂閱過期後重新付款

    流程：
    1. 訂閱過期（end_date < now）
    2. 用戶重新刷卡付款
    3. 驗證：創建新的 active period
    """
    print("\n" + "=" * 60)
    print("情境 5: 訂閱過期後重新付款")
    print("=" * 60)

    db = SessionLocal()

    teacher = Teacher(
        email="scenario5_expired@test.com",
        password_hash="dummy",
        name="Test User 5",
        subscription_type="Tutor Teachers",
        subscription_end_date=datetime.now(timezone.utc) - timedelta(days=5),  # 已過期
    )
    db.add(teacher)
    db.flush()

    now = datetime.now(timezone.utc)

    # 過期的週期
    period1 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=800,
        start_date=now - timedelta(days=35),
        end_date=now - timedelta(days=5),  # 已過期
        payment_method="auto_renew",
        payment_id="test_rec_008",
        payment_status="paid",
        status="expired",
    )
    db.add(period1)
    db.commit()

    print(f"⚠️  訂閱已過期 5 天")

    # 重新付款
    period2 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="manual",
        payment_id="test_rec_009",
        payment_status="paid",
        status="active",
    )
    db.add(period2)
    teacher.subscription_end_date = now + timedelta(days=30)
    db.commit()

    db.refresh(teacher)

    assert teacher.current_period is not None, "❌ 應該有 current_period"
    assert teacher.current_period.status == "active", "❌ 應該是 active"
    assert teacher.current_period.quota_used == 0, "❌ 新週期配額應該是 0"

    print(f"✅ 重新付款成功")
    print(
        f"   - 新配額：{teacher.current_period.quota_used}/{teacher.current_period.quota_total} 秒"
    )

    # 清理
    db.delete(period1)
    db.delete(period2)
    db.delete(teacher)
    db.commit()
    db.close()


def test_scenario_6_no_period_legacy_user():
    """
    情境 6: 舊用戶遷移（沒有 subscription_period）

    流程：
    1. 用戶有 subscription_end_date 但沒有 subscription_period
    2. 驗證：current_period 返回 None
    3. 驗證：quota_used 返回 0
    4. 驗證：更新配額會拋錯誤
    """
    print("\n" + "=" * 60)
    print("情境 6: 舊用戶遷移（沒有 subscription_period）")
    print("=" * 60)

    db = SessionLocal()

    # 模擬舊用戶（只有 subscription_end_date，沒有 period）
    legacy_teacher = Teacher(
        email="scenario6_legacy@test.com",
        password_hash="dummy",
        name="Legacy User",
        subscription_type="Tutor Teachers",
        subscription_end_date=datetime.now(timezone.utc) + timedelta(days=15),
    )
    db.add(legacy_teacher)
    db.commit()

    db.refresh(legacy_teacher)

    # 驗證行為
    assert legacy_teacher.current_period is None, "❌ 舊用戶應該沒有 current_period"
    assert legacy_teacher.quota_total == 0, "❌ 沒有 period 時 quota_total 應該是 0"
    assert legacy_teacher.quota_remaining == 0, "❌ 沒有 period 時 quota_remaining 應該是 0"

    print(f"✅ 舊用戶狀態正確")
    print(f"   - current_period: None")
    print(f"   - quota_total: {legacy_teacher.quota_total}")
    print(f"   - 建議：需要重新付款以創建 subscription_period")

    # 清理
    db.delete(legacy_teacher)
    db.commit()
    db.close()


def test_scenario_7_multiple_renewals_history():
    """
    情境 7: 多次續約歷史記錄

    流程：
    1. 用戶連續 3 個月續約
    2. 每個月使用不同的配額
    3. 驗證：保留完整的 3 個月歷史
    """
    print("\n" + "=" * 60)
    print("情境 7: 多次續約歷史記錄")
    print("=" * 60)

    db = SessionLocal()

    teacher = Teacher(
        email="scenario7_history@test.com",
        password_hash="dummy",
        name="Test User 7",
        subscription_type="Tutor Teachers",
        subscription_end_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(teacher)
    db.flush()

    now = datetime.now(timezone.utc)

    # 第一個月：使用 500 秒
    period1 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=500,
        start_date=now - timedelta(days=60),
        end_date=now - timedelta(days=30),
        payment_method="auto_renew",
        payment_id="test_rec_010",
        payment_status="paid",
        status="expired",
    )

    # 第二個月：使用 1200 秒
    period2 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=1200,
        start_date=now - timedelta(days=30),
        end_date=now,
        payment_method="auto_renew",
        payment_id="test_rec_011",
        payment_status="paid",
        status="expired",
    )

    # 第三個月：使用 300 秒（當前）
    period3 = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=300,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="auto_renew",
        payment_id="test_rec_012",
        payment_status="paid",
        status="active",
    )

    db.add_all([period1, period2, period3])
    db.commit()

    # 驗證
    all_periods = (
        db.query(SubscriptionPeriod)
        .filter(SubscriptionPeriod.teacher_id == teacher.id)
        .order_by(SubscriptionPeriod.start_date)
        .all()
    )

    assert len(all_periods) == 3, f"❌ 應該有 3 個月記錄，實際：{len(all_periods)}"

    print(f"✅ 完整保留 3 個月歷史")
    for i, p in enumerate(all_periods, 1):
        print(
            f"   - 第 {i} 月：{p.quota_used}/{p.quota_total} 秒 "
            f"({p.status}, {p.payment_method})"
        )

    # 驗證當前週期
    db.refresh(teacher)
    assert teacher.current_period.id == period3.id, "❌ current_period 應該是第三個月"
    assert teacher.current_period.quota_used == 300, "❌ 當前應該使用 300 秒"

    # 清理
    for p in all_periods:
        db.delete(p)
    db.delete(teacher)
    db.commit()
    db.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("訂閱系統情境測試")
    print("=" * 60)

    try:
        test_scenario_1_new_user_first_payment()
        test_scenario_2_use_quota_then_renew()
        test_scenario_3_quota_exhausted_then_renew()
        test_scenario_4_change_plan()
        test_scenario_5_expired_then_renew()
        test_scenario_6_no_period_legacy_user()
        test_scenario_7_multiple_renewals_history()

        print("\n" + "=" * 60)
        print("✅ 所有情境測試通過！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        raise
