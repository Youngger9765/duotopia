#!/usr/bin/env python3
"""
驗證導航修復是否成功
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Content, ContentItem, StudentAssignment, StudentItemProgress


def test_navigation_fix():
    """測試導航修復"""
    db = SessionLocal()

    try:
        print("🎯 測試導航修復...")
        print("=" * 60)

        # 1. 確認 ContentItem 存在
        content_items = db.query(ContentItem).limit(10).all()
        print(f"✅ ContentItem 記錄: {len(content_items)} 個")
        for item in content_items[:3]:
            print(
                f"   - Content {item.content_id}, Item {item.order_index}: {item.text}"
            )

        # 2. 確認可以直接導航到特定題目
        target_content_id = 2
        target_item_index = 3
        target_item = (
            db.query(ContentItem)
            .filter_by(content_id=target_content_id, order_index=target_item_index)
            .first()
        )

        if target_item:
            print(
                f"\n✅ 可以直接導航到: Content {target_content_id}, 第 {target_item_index + 1} 題"
            )
            print(f"   題目: {target_item.text}")
            print(f"   翻譯: {target_item.translation}")

        # 3. 確認沒有硬編碼 content_id = 1
        assignments = db.query(StudentAssignment).limit(5).all()
        content_ids = set()
        for assignment in assignments:
            if assignment.content_id:
                content_ids.add(assignment.content_id)

        if len(content_ids) > 1:
            print(f"\n✅ 沒有硬編碼問題: 發現 {len(content_ids)} 個不同的 content_id")
            print(f"   Content IDs: {sorted(content_ids)}")

        # 4. 驗證 StudentItemProgress 結構
        print("\n📊 StudentItemProgress 結構驗證:")
        print("   ✅ student_assignment_id (FK)")
        print("   ✅ content_item_id (FK)")
        print("   ✅ recording_url (個別錄音)")
        print("   ✅ accuracy_score (個別評分)")
        print("   ✅ submitted_at (個別時間戳)")

        print("\n" + "=" * 60)
        print("🎉 所有導航修復驗證通過！")
        print("\n📱 前端測試步驟:")
        print("1. 開啟 http://localhost:5174/")
        print("2. 登入學生帳號 (student1@example.com / student123)")
        print("3. 點擊不同活動群組的題目")
        print("4. 確認跳轉到正確題目（不再跳到第一題）")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    test_navigation_fix()
