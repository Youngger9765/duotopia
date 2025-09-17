#!/usr/bin/env python3
"""
Populate ContentItem table from existing Content data
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Content, ContentItem
import json


def populate_content_items():
    """將現有 Content 的 items 轉換為 ContentItem records"""
    db = SessionLocal()

    try:
        # 獲取所有有 items 的 content
        contents = db.query(Content).all()

        created_count = 0
        for content in contents:
            if content.items:
                # Parse items from JSONB
                items_data = content.items if isinstance(content.items, list) else []

                for idx, item_data in enumerate(items_data):
                    # 檢查是否已存在
                    existing = (
                        db.query(ContentItem)
                        .filter_by(content_id=content.id, order_index=idx)
                        .first()
                    )

                    if not existing:
                        # 建立新的 ContentItem
                        content_item = ContentItem(
                            content_id=content.id,
                            order_index=idx,
                            text=item_data.get("text", ""),
                            translation=item_data.get("translation", ""),
                        )
                        db.add(content_item)
                        created_count += 1

        db.commit()
        print(f"✅ 成功建立 {created_count} 個 ContentItem 記錄")

        # 顯示統計
        total = db.query(ContentItem).count()
        print(f"📊 ContentItem 總數: {total}")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    populate_content_items()
