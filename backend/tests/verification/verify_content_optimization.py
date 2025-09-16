#!/usr/bin/env python
"""
驗證 Content 查詢優化的安全性
確認優化後的查詢返回與原始查詢相同的結果
"""

import sys
import traceback

sys.path.append(".")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from database import Base  # noqa: E402
from tests.factories import TestDataFactory  # noqa: E402
from models import Content, StudentContentProgress, AssignmentStatus  # noqa: E402


def test_content_query_consistency():
    """驗證優化前後查詢結果一致性"""
    print("\n" + "=" * 60)
    print("測試：Content 查詢優化一致性驗證")
    print("=" * 60)

    # 建立測試資料庫
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 建立測試資料
        data = TestDataFactory.create_full_assignment_chain(db)

        # 建立更多 content 和對應的 progress
        additional_contents = []
        for i in range(3):
            content = Content(
                lesson_id=data["lesson"].id,
                title=f"Test Content {i+1}",
                type="READING_ASSESSMENT",
                items=[{"text": f"Content {i+1} text", "translation": f"內容 {i+1}"}],
            )
            db.add(content)
            db.commit()
            additional_contents.append(content)

            progress = StudentContentProgress(
                student_assignment_id=data["student_assignment"].id,
                content_id=content.id,
                order_index=i + 1,
                status=AssignmentStatus.NOT_STARTED,
            )
            db.add(progress)

        db.commit()

        print("✅ 測試資料建立成功")
        print(f"   學生作業: {data['assignment'].title}")
        print(f"   Content 總數: {len(additional_contents) + 1}")

        # 取得 progress_records
        progress_records = (
            db.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id
                == data["student_assignment"].id
            )
            .order_by(StudentContentProgress.order_index)
            .all()
        )

        print(f"   Progress 記錄: {len(progress_records)} 個")

        # 方法1：原始查詢方式（N+1）
        print("\n1. 原始查詢方式（N+1）:")
        old_activities = []
        for progress in progress_records:
            content = (
                db.query(Content).filter(Content.id == progress.content_id).first()
            )
            if content:
                old_activities.append(
                    {
                        "id": progress.id,
                        "content_id": content.id,
                        "title": content.title,
                        "type": content.type.value
                        if content.type
                        else "reading_assessment",
                        "items_count": len(content.items) if content.items else 0,
                    }
                )

        print(f"   結果: {len(old_activities)} 個活動")

        # 方法2：優化後的查詢方式（批次查詢）
        print("\n2. 優化後的查詢方式（批次查詢）:")
        content_ids = [progress.content_id for progress in progress_records]
        contents = db.query(Content).filter(Content.id.in_(content_ids)).all()
        content_dict = {content.id: content for content in contents}

        new_activities = []
        for progress in progress_records:
            content = content_dict.get(progress.content_id)
            if content:
                new_activities.append(
                    {
                        "id": progress.id,
                        "content_id": content.id,
                        "title": content.title,
                        "type": content.type.value
                        if content.type
                        else "reading_assessment",
                        "items_count": len(content.items) if content.items else 0,
                    }
                )

        print(f"   結果: {len(new_activities)} 個活動")

        # 驗證結果一致性
        if len(old_activities) == len(new_activities):
            # 按 content_id 排序以確保比較順序一致
            old_sorted = sorted(old_activities, key=lambda x: x["content_id"])
            new_sorted = sorted(new_activities, key=lambda x: x["content_id"])

            differences = []
            for old, new in zip(old_sorted, new_sorted):
                if old != new:
                    differences.append({"old": old, "new": new})

            if not differences:
                print("\n✅ 驗證通過：兩種查詢方式返回相同結果！")

                # 顯示詳細結果
                print("\n📋 結果詳情：")
                for activity in old_sorted:
                    print(
                        f"   - {activity['title']} ({activity['type']}, {activity['items_count']} items)"
                    )

                return True
            else:
                print(f"\n❌ 驗證失敗：發現 {len(differences)} 個差異")
                for diff in differences:
                    print(f"   差異: {diff}")
                return False
        else:
            print(
                f"\n❌ 驗證失敗：結果數量不一致 (原始: {len(old_activities)}, 優化: {len(new_activities)})"
            )
            return False

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_edge_cases():
    """測試邊界情況"""
    print("\n" + "=" * 60)
    print("測試：邊界情況")
    print("=" * 60)

    # 建立測試資料庫
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 測試空列表情況
        print("\n1. 測試空 progress_records 列表:")
        progress_records = []

        # 優化的查詢方式
        content_ids = [progress.content_id for progress in progress_records]
        contents = db.query(Content).filter(Content.id.in_(content_ids)).all()
        content_dict = {content.id: content for content in contents}

        activities = []
        for progress in progress_records:
            content = content_dict.get(progress.content_id)
            if content:
                activities.append({"content_id": content.id, "title": content.title})

        assert len(activities) == 0
        print("   ✅ 空列表處理正確")

        # 測試無效的 content_id
        print("\n2. 測試無效的 content_id:")
        data = TestDataFactory.create_full_assignment_chain(db)

        # 建立一個 progress 但刪除對應的 content
        progress = StudentContentProgress(
            student_assignment_id=data["student_assignment"].id,
            content_id=99999,  # 不存在的 content_id
            order_index=0,
            status=AssignmentStatus.NOT_STARTED,
        )
        db.add(progress)
        db.commit()

        progress_records = [progress]
        content_ids = [progress.content_id for progress in progress_records]
        contents = db.query(Content).filter(Content.id.in_(content_ids)).all()
        content_dict = {content.id: content for content in contents}

        activities = []
        for progress in progress_records:
            content = content_dict.get(progress.content_id)
            if content:  # 這裡會是 None，所以不會加入
                activities.append({"content_id": content.id, "title": content.title})

        assert len(activities) == 0
        print("   ✅ 無效 content_id 處理正確")

        print("\n✅ 所有邊界情況測試通過")
        return True

    except Exception as e:
        print(f"\n❌ 邊界測試失敗: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "🔍 開始驗證 Content 查詢優化安全性 ".center(60, "="))

    results = []
    results.append(("查詢結果一致性", test_content_query_consistency()))
    results.append(("邊界情況處理", test_edge_cases()))

    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 所有測試通過！Content 查詢優化是安全的！")
        sys.exit(0)
    else:
        print("\n⚠️ 有測試失敗，請檢查優化！")
        sys.exit(1)
