#!/usr/bin/env python
"""
驗證查詢優化的安全性
確認優化後的查詢返回與原始查詢相同的結果
"""

import sys
import traceback

sys.path.append(".")

from sqlalchemy import create_engine, func, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from database import Base  # noqa: E402
from tests.factories import TestDataFactory  # noqa: E402
from models import Classroom, ClassroomStudent  # noqa: E402


def test_student_login_query():
    """驗證學生登入查詢優化的正確性"""
    print("\n" + "=" * 60)
    print("測試：學生登入查詢優化")
    print("=" * 60)

    # 建立測試資料庫
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 建立測試資料
        data = TestDataFactory.create_full_assignment_chain(db)
        student = data["student"]
        expected_classroom = data["classroom"]

        print("✅ 測試資料建立成功")
        print(f"   學生: {student.name} (ID: {student.id})")
        print(f"   預期班級: {expected_classroom.name} (ID: {expected_classroom.id})")

        # 方法1：原始查詢方式（3個查詢）
        print("\n1. 原始查詢方式（3個查詢）:")
        classroom_student = (
            db.query(ClassroomStudent)
            .filter(ClassroomStudent.student_id == student.id)
            .first()
        )
        if classroom_student:
            classroom_old = (
                db.query(Classroom)
                .filter(Classroom.id == classroom_student.classroom_id)
                .first()
            )
            print(f"   結果: {classroom_old.name if classroom_old else 'None'}")

        # 方法2：優化後的查詢（1個 JOIN 查詢）
        print("\n2. 優化後的查詢（1個 JOIN）:")
        classroom_info = (
            db.query(Classroom.id, Classroom.name)
            .join(ClassroomStudent)
            .filter(ClassroomStudent.student_id == student.id)
            .first()
        )
        print(f"   結果: {classroom_info.name if classroom_info else 'None'}")

        # 驗證結果一致性
        if classroom_info and classroom_old:
            if (
                classroom_info.id == classroom_old.id
                and classroom_info.name == classroom_old.name
            ):
                print("\n✅ 驗證通過：兩種查詢方式返回相同結果！")
                return True
            else:
                print("\n❌ 驗證失敗：結果不一致！")
                return False
        else:
            print("\n❌ 查詢失敗！")
            return False

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_teacher_classrooms_query():
    """驗證教師班級列表查詢優化的正確性"""
    print("\n" + "=" * 60)
    print("測試：教師班級列表查詢優化")
    print("=" * 60)

    # 建立測試資料庫
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 建立測試資料
        teacher = TestDataFactory.create_teacher(db)
        expected_results = []

        for i in range(3):
            classroom = TestDataFactory.create_classroom(
                db, teacher, f"Classroom {i+1}"
            )
            student_count = i + 2  # 2, 3, 4 個學生
            for j in range(student_count):
                TestDataFactory.create_student(
                    db,
                    name=f"Student {i}-{j}",
                    email=f"s{i}{j}@test.com",
                    student_number=f"S{i:03d}{j:03d}",
                    classroom=classroom,
                )
            expected_results.append((classroom.id, classroom.name, student_count))

        print("✅ 測試資料建立成功")
        print(f"   教師: {teacher.name}")
        print(f"   班級數: {len(expected_results)}")

        # 方法1：原始查詢方式（1 + N 查詢）
        print("\n1. 原始查詢方式（1 + N 查詢）:")
        classrooms = (
            db.query(Classroom)
            .filter(Classroom.teacher_id == teacher.id, Classroom.is_active.is_(True))
            .all()
        )
        old_results = []
        for classroom in classrooms:
            student_count = (
                db.query(ClassroomStudent)
                .filter(ClassroomStudent.classroom_id == classroom.id)
                .count()
            )
            old_results.append((classroom.id, classroom.name, student_count))
            print(f"   - {classroom.name}: {student_count} 個學生")

        # 方法2：優化後的查詢（1個 JOIN + GROUP BY）
        print("\n2. 優化後的查詢（JOIN + GROUP BY）:")
        classrooms_with_count = (
            db.query(
                Classroom.id,
                Classroom.name,
                func.count(ClassroomStudent.id).label("student_count"),
            )
            .outerjoin(ClassroomStudent)
            .filter(Classroom.teacher_id == teacher.id, Classroom.is_active.is_(True))
            .group_by(Classroom.id, Classroom.name)
            .all()
        )
        new_results = []
        for classroom_id, classroom_name, student_count in classrooms_with_count:
            new_results.append((classroom_id, classroom_name, student_count or 0))
            print(f"   - {classroom_name}: {student_count or 0} 個學生")

        # 驗證結果一致性
        old_results.sort(key=lambda x: x[0])
        new_results.sort(key=lambda x: x[0])

        if old_results == new_results == expected_results:
            print("\n✅ 驗證通過：兩種查詢方式返回相同結果！")
            return True
        else:
            print("\n❌ 驗證失敗：結果不一致！")
            print(f"   預期: {expected_results}")
            print(f"   原始: {old_results}")
            print(f"   優化: {new_results}")
            return False

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_performance_improvement():
    """測試性能改進"""
    print("\n" + "=" * 60)
    print("測試：查詢性能改進")
    print("=" * 60)

    # 建立測試資料庫
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    query_count = 0

    def count_queries(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    try:
        # 建立較多測試資料
        teacher = TestDataFactory.create_teacher(db)
        for i in range(10):  # 10個班級
            classroom = TestDataFactory.create_classroom(db, teacher, f"Class {i}")
            for j in range(5):  # 每班5個學生
                TestDataFactory.create_student(
                    db,
                    name=f"S{i}-{j}",
                    email=f"s{i}{j}@test.com",
                    student_number=f"S{i:03d}{j:03d}",
                    classroom=classroom,
                )

        # 測試原始方式的查詢次數
        event.listen(db.bind, "before_cursor_execute", count_queries)
        query_count = 0

        classrooms = (
            db.query(Classroom).filter(Classroom.teacher_id == teacher.id).all()
        )
        for classroom in classrooms:
            _ = (
                db.query(ClassroomStudent)
                .filter(ClassroomStudent.classroom_id == classroom.id)
                .count()
            )

        old_query_count = query_count
        print(f"原始方式查詢次數: {old_query_count}")

        # 測試優化方式的查詢次數
        query_count = 0
        _ = (
            db.query(Classroom.id, Classroom.name, func.count(ClassroomStudent.id))
            .outerjoin(ClassroomStudent)
            .filter(Classroom.teacher_id == teacher.id)
            .group_by(Classroom.id, Classroom.name)
            .all()
        )

        new_query_count = query_count
        print(f"優化方式查詢次數: {new_query_count}")

        improvement = ((old_query_count - new_query_count) / old_query_count) * 100
        print(
            f"\n✅ 性能提升: {improvement:.1f}% (減少 {old_query_count - new_query_count} 次查詢)"
        )

        return new_query_count < old_query_count

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        return False
    finally:
        event.remove(db.bind, "before_cursor_execute", count_queries)
        db.close()


if __name__ == "__main__":
    print("\n" + "🔍 開始驗證查詢優化安全性 ".center(60, "="))

    results = []
    results.append(("學生登入查詢", test_student_login_query()))
    results.append(("教師班級查詢", test_teacher_classrooms_query()))
    results.append(("性能改進測試", test_performance_improvement()))

    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 所有測試通過！優化是安全的，沒有破壞性！")
        sys.exit(0)
    else:
        print("\n⚠️ 有測試失敗，請檢查優化！")
        sys.exit(1)
