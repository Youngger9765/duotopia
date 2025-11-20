"""
配額系統效能測試

測試目標：
1. current_period 查詢效能（避免 N+1 query）
2. Index 效果驗證
3. 高並發配額扣除
"""

import time
from sqlalchemy import text
from database import get_session_local
from models import Teacher
from services.quota_service import QuotaService


def test_current_period_performance():
    """
    測試 current_period 查詢效能

    目標：1000 次查詢應在 1 秒內完成
    """
    SessionLocal = get_session_local()
    db = SessionLocal()

    # 取得測試 teacher
    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
    if not teacher:
        print("❌ Demo teacher not found")
        db.close()
        return False

    # 預熱（排除第一次查詢的延遲）
    _ = teacher.current_period

    # 效能測試：1000 次 current_period 查詢
    iterations = 1000
    start_time = time.time()

    for _ in range(iterations):
        _ = teacher.current_period

    elapsed = time.time() - start_time
    avg_ms = (elapsed / iterations) * 1000

    print("\n" + "=" * 70)
    print("📊 current_period 效能測試")
    print("=" * 70)
    print(f"總查詢次數: {iterations}")
    print(f"總耗時: {elapsed:.3f} 秒")
    print(f"平均每次: {avg_ms:.2f} ms")
    print(f"QPS (每秒查詢數): {iterations / elapsed:.0f}")

    # 驗證結果
    target_time = 1.0  # 目標：1 秒內完成 1000 次
    if elapsed < target_time:
        print(f"✅ 效能測試通過 ({elapsed:.3f}s < {target_time}s)")
        success = True
    else:
        print(f"⚠️  效能未達標 ({elapsed:.3f}s >= {target_time}s)")
        success = False

    db.close()
    return success


def test_quota_check_performance():
    """
    測試配額檢查效能

    目標：1000 次檢查應在 2 秒內完成
    """
    SessionLocal = get_session_local()
    db = SessionLocal()

    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
    if not teacher:
        print("❌ Demo teacher not found")
        db.close()
        return False

    # 效能測試：1000 次配額檢查
    iterations = 1000
    start_time = time.time()

    for _ in range(iterations):
        QuotaService.check_quota(teacher, 10)  # 檢查是否有 10 秒配額

    elapsed = time.time() - start_time
    avg_ms = (elapsed / iterations) * 1000

    print("\n" + "=" * 70)
    print("📊 QuotaService.check_quota 效能測試")
    print("=" * 70)
    print(f"總查詢次數: {iterations}")
    print(f"總耗時: {elapsed:.3f} 秒")
    print(f"平均每次: {avg_ms:.2f} ms")
    print(f"QPS: {iterations / elapsed:.0f}")

    target_time = 2.0
    if elapsed < target_time:
        print(f"✅ 效能測試通過 ({elapsed:.3f}s < {target_time}s)")
        success = True
    else:
        print(f"⚠️  效能未達標 ({elapsed:.3f}s >= {target_time}s)")
        success = False

    db.close()
    return success


def test_index_coverage():
    """
    驗證 Index 已正確建立
    """
    SessionLocal = get_session_local()
    db = SessionLocal()

    # 檢查 subscription_periods indexes
    result = db.execute(
        text(
            """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'subscription_periods'
        AND indexname LIKE 'ix_%'
    """
        )
    )

    indexes = result.fetchall()

    print("\n" + "=" * 70)
    print("📊 Database Indexes 驗證")
    print("=" * 70)
    print("subscription_periods indexes:")
    for idx in indexes:
        print(f"   - {idx[0]}")

    # 驗證關鍵 index 存在
    index_names = [idx[0] for idx in indexes]
    required_indexes = [
        "ix_subscription_periods_teacher_status",
        "ix_subscription_periods_end_date",
    ]

    missing = [idx for idx in required_indexes if idx not in index_names]

    if not missing:
        print("✅ 所有必要 indexes 已建立")
        success = True
    else:
        print(f"❌ 缺少 indexes: {missing}")
        success = False

    db.close()
    return success


def test_explain_query():
    """
    使用 EXPLAIN ANALYZE 分析查詢計畫
    """
    SessionLocal = get_session_local()
    db = SessionLocal()

    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
    if not teacher:
        print("❌ Demo teacher not found")
        db.close()
        return False

    # EXPLAIN ANALYZE current_period 查詢
    result = db.execute(
        text(
            f"""
        EXPLAIN ANALYZE
        SELECT * FROM subscription_periods
        WHERE teacher_id = {teacher.id}
        AND status = 'active'
        LIMIT 1
    """
        )
    )

    print("\n" + "=" * 70)
    print("📊 Query Plan (EXPLAIN ANALYZE)")
    print("=" * 70)

    for row in result:
        print(row[0])

    # 檢查是否使用 Index Scan（不是 Seq Scan）
    result = db.execute(
        text(
            f"""
        EXPLAIN
        SELECT * FROM subscription_periods
        WHERE teacher_id = {teacher.id}
        AND status = 'active'
        LIMIT 1
    """
        )
    )

    plan = "\n".join([row[0] for row in result])

    if "Index Scan" in plan or "Bitmap Index Scan" in plan:
        print("\n✅ 使用 Index Scan（已優化）")
        success = True
    elif "Seq Scan" in plan:
        print("\n⚠️  使用 Seq Scan（未使用索引）")
        success = False
    else:
        print("\n⚠️  無法判斷查詢計畫")
        success = False

    db.close()
    return success


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 配額系統效能測試")
    print("=" * 70)

    test1 = test_index_coverage()
    test2 = test_explain_query()
    test3 = test_current_period_performance()
    test4 = test_quota_check_performance()

    print("\n" + "=" * 70)
    print("📊 測試總結")
    print("=" * 70)
    print(f"Index 驗證: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Query Plan: {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"current_period 效能: {'✅ PASSED' if test3 else '❌ FAILED'}")
    print(f"check_quota 效能: {'✅ PASSED' if test4 else '❌ FAILED'}")
    print("=" * 70)

    if all([test1, test2, test3, test4]):
        print("\n🎉 所有效能測試通過！")
        exit(0)
    else:
        print("\n❌ 部分測試失敗")
        exit(1)
