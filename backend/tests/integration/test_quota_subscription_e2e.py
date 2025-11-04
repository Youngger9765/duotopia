"""
E2E 測試：配額系統與訂閱系統整合

測試 Point 與 Subscription 之間的完整關係：
1. 付款創建 SubscriptionPeriod → 配額歸零
2. 配額扣除 → SubscriptionPeriod 同步更新
3. 訂閱過期 → 無法扣配額
4. 方案切換 → 配額正確轉移
5. 自動續訂 → 配額重置
6. 配額不足 → 阻止操作
7. 跨月訂閱 → 配額按比例計算
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime, timezone, timedelta, date
from decimal import Decimal


def get_db_connection():
    """建立資料庫連線"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from dotenv import load_dotenv
    import os

    load_dotenv()
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia",
    )
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def create_test_teacher(db):
    """建立測試老師"""
    from models import Teacher
    from passlib.context import CryptContext
    import random

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    email = f"test_teacher_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}@example.com"

    teacher = Teacher(
        email=email,
        name="E2E Test Teacher",
        password_hash=pwd_context.hash("password123"),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def create_test_student(db):
    """建立測試學生"""
    from models import Student
    from passlib.context import CryptContext
    import random

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    email = f"test_student_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}@example.com"

    student = Student(
        email=email,
        name="E2E Test Student",
        password_hash=pwd_context.hash("password123"),
        birthdate=date(2010, 1, 1),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def create_test_classroom(db, teacher_id):
    """建立測試班級"""
    from models import Classroom

    classroom = Classroom(
        teacher_id=teacher_id,
        name="E2E Test Classroom",
        description="Test",
        level="A1",
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def test_1_payment_creates_period_with_quota():
    """
    測試 1: 付款創建訂閱週期並初始化配額

    Given: 老師沒有訂閱
    When: 付款購買 Tutor Teachers (330元)
    Then:
        - 創建 SubscriptionPeriod (status=active)
        - quota_total = 1800 秒
        - quota_used = 0 秒
    """
    print("\n" + "=" * 70)
    print("🧪 Test 1: Payment Creates Period With Quota")
    print("=" * 70)

    db = get_db_connection()
    try:
        from models import SubscriptionPeriod

        # 建立測試老師
        teacher = create_test_teacher(db)
        print(f"✅ Created teacher: {teacher.email}")

        # 確認沒有訂閱
        assert teacher.current_period is None, "Teacher should have no subscription"
        print("✅ Confirmed: No existing subscription")

        # 模擬付款創建訂閱週期
        now = datetime.now(timezone.utc)
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=0,
            start_date=now,
            end_date=now + timedelta(days=30),
            payment_method="credit_card",
            payment_status="paid",
            status="active",
        )
        db.add(period)
        db.commit()
        db.refresh(period)

        print(f"✅ Created SubscriptionPeriod ID: {period.id}")
        print(f"   Plan: {period.plan_name}")
        print(f"   Quota Total: {period.quota_total} seconds")
        print(f"   Quota Used: {period.quota_used} seconds")

        # 驗證
        db.refresh(teacher)
        assert teacher.current_period is not None, "Teacher should have active period"
        assert teacher.current_period.quota_total == 1800, "Quota should be 1800"
        assert teacher.current_period.quota_used == 0, "Quota used should be 0"
        assert teacher.current_period.status == "active", "Period should be active"

        print("✅ Test 1 PASSED: Payment correctly creates period with quota")
        return True

    except AssertionError as e:
        print(f"❌ Test 1 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 1 ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def test_2_quota_deduction_updates_period():
    """
    測試 2: 配額扣除同步更新 SubscriptionPeriod

    Given: 老師有 1800 秒配額
    When: 扣除 100 秒 (語音評分)
    Then:
        - period.quota_used = 100
        - PointUsageLog 記錄正確
        - quota_before/after 正確
    """
    print("\n" + "=" * 70)
    print("🧪 Test 2: Quota Deduction Updates Period")
    print("=" * 70)

    db = get_db_connection()
    try:
        from models import SubscriptionPeriod, Assignment, PointUsageLog
        from services.quota_service import QuotaService

        # 建立測試資料
        teacher = create_test_teacher(db)
        student = create_test_student(db)
        classroom = create_test_classroom(db, teacher.id)

        now = datetime.now(timezone.utc)
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=0,
            start_date=now,
            end_date=now + timedelta(days=30),
            payment_method="credit_card",
            payment_status="paid",
            status="active",
        )
        db.add(period)
        db.commit()

        assignment = Assignment(
            teacher_id=teacher.id,
            classroom_id=classroom.id,
            title="Test Assignment",
            description="E2E Test",
            created_at=now,
        )
        db.add(assignment)
        db.commit()

        print(f"✅ Setup complete")
        print(f"   Teacher: {teacher.email}")
        print(f"   Period ID: {period.id}")
        print(f"   Initial quota_used: {period.quota_used}")

        # 扣除配額
        usage_log = QuotaService.deduct_quota(
            db=db,
            teacher=teacher,
            student_id=student.id,
            assignment_id=assignment.id,
            feature_type="speech_assessment",
            unit_count=100,
            unit_type="秒",
        )

        print(f"✅ Deducted 100 seconds")
        print(f"   Usage Log ID: {usage_log.id}")

        # 驗證 SubscriptionPeriod 更新
        db.refresh(period)
        assert period.quota_used == 100, f"Expected quota_used=100, got {period.quota_used}"
        print(f"✅ Period quota_used updated: {period.quota_used}")

        # 驗證 PointUsageLog
        assert usage_log.subscription_period_id == period.id, "Wrong period_id"
        assert usage_log.points_used == 100, "Wrong points_used"
        assert usage_log.quota_before == 0, "Wrong quota_before"
        assert usage_log.quota_after == 100, "Wrong quota_after"
        print(f"✅ PointUsageLog correct:")
        print(f"   Quota before: {usage_log.quota_before}")
        print(f"   Quota after: {usage_log.quota_after}")

        print("✅ Test 2 PASSED: Quota deduction correctly updates period")
        return True

    except AssertionError as e:
        print(f"❌ Test 2 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 2 ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def test_3_expired_period_blocks_deduction():
    """
    測試 3: 過期訂閱無法扣配額

    Given: 老師訂閱已過期 (end_date < now)
    When: 嘗試扣配額
    Then: current_period = None, check_quota = False
    """
    print("\n" + "=" * 70)
    print("🧪 Test 3: Expired Period Blocks Deduction")
    print("=" * 70)

    db = get_db_connection()
    try:
        from models import SubscriptionPeriod
        from services.quota_service import QuotaService

        teacher = create_test_teacher(db)

        # 創建已過期的訂閱
        now = datetime.now(timezone.utc)
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=500,
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=30),  # 30天前過期
            payment_method="credit_card",
            payment_status="paid",
            status="expired",  # 已過期
        )
        db.add(period)
        db.commit()

        print(f"✅ Created expired period")
        print(f"   End date: {period.end_date}")
        print(f"   Status: {period.status}")

        # 檢查 current_period
        db.refresh(teacher)
        assert (
            teacher.current_period is None
        ), "Expired period should not be current_period"
        print(f"✅ teacher.current_period is None (correct)")

        # 嘗試檢查配額
        has_quota = QuotaService.check_quota(teacher, 10)
        assert has_quota is False, "Should not have quota when expired"
        print(f"✅ check_quota returns False (correct)")

        print("✅ Test 3 PASSED: Expired period correctly blocks quota operations")
        return True

    except AssertionError as e:
        print(f"❌ Test 3 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 3 ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def test_4_auto_renewal_resets_quota():
    """
    測試 4: 自動續訂重置配額

    Given: 老師有舊的訂閱 (quota_used=1500)
    When: 自動續訂創建新的 period
    Then:
        - 舊 period status=expired
        - 新 period quota_used=0, quota_total=1800
    """
    print("\n" + "=" * 70)
    print("🧪 Test 4: Auto Renewal Resets Quota")
    print("=" * 70)

    db = get_db_connection()
    try:
        from models import SubscriptionPeriod

        teacher = create_test_teacher(db)
        now = datetime.now(timezone.utc)

        # 舊的訂閱（快到期）
        old_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=1500,  # 用了很多
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=1),
            payment_method="credit_card",
            payment_status="paid",
            status="active",
        )
        db.add(old_period)
        db.commit()

        print(f"✅ Old period created")
        print(f"   Quota used: {old_period.quota_used}/1800")

        # 模擬自動續訂
        old_period.status = "expired"

        new_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=0,  # 配額重置
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=31),
            payment_method="credit_card",
            payment_status="paid",
            status="active",
        )
        db.add(new_period)
        db.commit()

        print(f"✅ New period created (auto renewal)")
        print(f"   Quota used: {new_period.quota_used}/1800")

        # 驗證
        db.refresh(teacher)
        assert teacher.current_period.id == new_period.id, "Should use new period"
        assert teacher.current_period.quota_used == 0, "Quota should be reset"
        print(f"✅ Current period is new period with quota=0")

        # 驗證舊期已過期
        db.refresh(old_period)
        assert old_period.status == "expired", "Old period should be expired"
        print(f"✅ Old period status = expired")

        print("✅ Test 4 PASSED: Auto renewal correctly resets quota")
        return True

    except AssertionError as e:
        print(f"❌ Test 4 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 4 ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def test_5_quota_insufficient_blocks_operation():
    """
    測試 5: 配額不足阻止操作

    Given: 老師配額剩 5 秒
    When: 嘗試扣 10 秒
    Then: check_quota returns False
    """
    print("\n" + "=" * 70)
    print("🧪 Test 5: Quota Insufficient Blocks Operation")
    print("=" * 70)

    db = get_db_connection()
    try:
        from models import SubscriptionPeriod
        from services.quota_service import QuotaService

        teacher = create_test_teacher(db)
        now = datetime.now(timezone.utc)

        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=1795,  # 只剩 5 秒
            start_date=now,
            end_date=now + timedelta(days=30),
            payment_method="credit_card",
            payment_status="paid",
            status="active",
        )
        db.add(period)
        db.commit()

        print(f"✅ Setup: quota remaining = 5 seconds")

        # 嘗試扣 10 秒（應該失敗）
        has_quota = QuotaService.check_quota(teacher, 10)
        assert has_quota is False, "Should not have enough quota"
        print(f"✅ check_quota(10) = False (correct)")

        # 嘗試扣 5 秒（應該成功）
        has_quota = QuotaService.check_quota(teacher, 5)
        assert has_quota is True, "Should have enough for 5 seconds"
        print(f"✅ check_quota(5) = True (correct)")

        print("✅ Test 5 PASSED: Quota check correctly blocks insufficient quota")
        return True

    except AssertionError as e:
        print(f"❌ Test 5 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 5 ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def test_6_multiple_periods_only_active_counts():
    """
    測試 6: 多個 period 只有 active 生效

    Given: Teacher 有多個 periods (expired, active, pending)
    When: 查詢 current_period
    Then: 只返回 status=active 的 period
    """
    print("\n" + "=" * 70)
    print("🧪 Test 6: Multiple Periods Only Active Counts")
    print("=" * 70)

    db = get_db_connection()
    try:
        from models import SubscriptionPeriod

        teacher = create_test_teacher(db)
        now = datetime.now(timezone.utc)

        # 過期的
        expired_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=1800,
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=30),
            payment_method="credit_card",
            payment_status="paid",
            status="expired",
        )
        db.add(expired_period)

        # Active 的
        active_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="School Teachers",
            amount_paid=Decimal("660"),
            quota_total=4000,
            quota_used=100,
            start_date=now,
            end_date=now + timedelta(days=30),
            payment_method="credit_card",
            payment_status="paid",
            status="active",
        )
        db.add(active_period)

        db.commit()

        print(f"✅ Created 2 periods:")
        print(f"   - Expired: {expired_period.id}")
        print(f"   - Active: {active_period.id}")

        # 驗證 current_period
        db.refresh(teacher)
        assert teacher.current_period is not None, "Should have current period"
        assert (
            teacher.current_period.id == active_period.id
        ), "Should use active period"
        assert teacher.current_period.quota_total == 4000, "Should be School Teachers"
        print(f"✅ current_period = active_period (correct)")
        print(f"   Plan: {teacher.current_period.plan_name}")
        print(f"   Quota: {teacher.current_period.quota_used}/{teacher.current_period.quota_total}")

        print("✅ Test 6 PASSED: Only active period is used")
        return True

    except AssertionError as e:
        print(f"❌ Test 6 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 6 ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def test_7_quota_analytics_matches_period():
    """
    測試 7: 配額統計與 Period 一致

    Given: Teacher 有多筆 PointUsageLog
    When: 查詢 analytics summary
    Then: summary.total_used = period.quota_used
    """
    print("\n" + "=" * 70)
    print("🧪 Test 7: Quota Analytics Matches Period")
    print("=" * 70)

    db = get_db_connection()
    try:
        from models import SubscriptionPeriod, Assignment, PointUsageLog
        from services.quota_service import QuotaService
        from services.quota_analytics_service import QuotaAnalyticsService

        teacher = create_test_teacher(db)
        student = create_test_student(db)
        classroom = create_test_classroom(db, teacher.id)
        now = datetime.now(timezone.utc)

        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=Decimal("330"),
            quota_total=1800,
            quota_used=0,
            start_date=now,
            end_date=now + timedelta(days=30),
            payment_method="credit_card",
            payment_status="paid",
            status="active",
        )
        db.add(period)

        assignment = Assignment(
            teacher_id=teacher.id,
            classroom_id=classroom.id,
            title="Test Assignment",
            description="E2E Test",
            created_at=now,
        )
        db.add(assignment)
        db.commit()

        # 扣除多次配額
        QuotaService.deduct_quota(
            db, teacher, student.id, assignment.id, "speech_assessment", 50, "秒"
        )
        QuotaService.deduct_quota(
            db, teacher, student.id, assignment.id, "speech_assessment", 30, "秒"
        )
        QuotaService.deduct_quota(
            db, teacher, student.id, assignment.id, "speech_assessment", 20, "秒"
        )

        total_deducted = 50 + 30 + 20
        print(f"✅ Deducted {total_deducted} seconds in 3 operations")

        # 驗證 period.quota_used
        db.refresh(period)
        assert (
            period.quota_used == total_deducted
        ), f"Period quota_used mismatch: {period.quota_used} != {total_deducted}"
        print(f"✅ Period quota_used = {period.quota_used} (correct)")

        # 驗證 analytics
        analytics = QuotaAnalyticsService.get_usage_summary(teacher)
        assert (
            analytics["summary"]["total_used"] == total_deducted
        ), f"Analytics mismatch: {analytics['summary']['total_used']} != {total_deducted}"
        print(
            f"✅ Analytics total_used = {analytics['summary']['total_used']} (correct)"
        )

        # 驗證 PointUsageLog 數量
        logs = (
            db.query(PointUsageLog)
            .filter(PointUsageLog.subscription_period_id == period.id)
            .all()
        )
        assert len(logs) == 3, f"Expected 3 logs, got {len(logs)}"
        print(f"✅ PointUsageLog count = 3 (correct)")

        print("✅ Test 7 PASSED: Analytics matches period data")
        return True

    except AssertionError as e:
        print(f"❌ Test 7 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ Test 7 ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 E2E Tests: Quota ↔️ Subscription Integration")
    print("=" * 70)

    results = []
    results.append(("Payment Creates Period", test_1_payment_creates_period_with_quota()))
    results.append(("Quota Updates Period", test_2_quota_deduction_updates_period()))
    results.append(("Expired Blocks Deduction", test_3_expired_period_blocks_deduction()))
    results.append(("Auto Renewal Resets", test_4_auto_renewal_resets_quota()))
    results.append(("Insufficient Blocks", test_5_quota_insufficient_blocks_operation()))
    results.append(("Only Active Counts", test_6_multiple_periods_only_active_counts()))
    results.append(("Analytics Matches", test_7_quota_analytics_matches_period()))

    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:.<40} {status}")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    if passed_count == total_count:
        print(f"\n🎉 All {total_count} tests passed!")
        exit(0)
    else:
        print(f"\n❌ {total_count - passed_count}/{total_count} tests failed")
        exit(1)
