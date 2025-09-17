#!/usr/bin/env python3
"""
Data migration script to populate ContentItem table from existing Content.items JSONB data
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import from the backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Content, ContentItem
import json


def migrate_content_items():
    """Migrate existing Content.items JSONB data to ContentItem table"""
    db = SessionLocal()

    try:
        print("🚀 Starting ContentItem migration...")

        # Get all Content records that have items
        contents = db.query(Content).filter(Content.items.isnot(None)).all()
        print(f"Found {len(contents)} Content records with items")

        migrated_count = 0

        for content in contents:
            print(f"\n📝 Processing Content ID {content.id}: {content.title}")

            # Check if already migrated
            existing_items = (
                db.query(ContentItem)
                .filter(ContentItem.content_id == content.id)
                .count()
            )

            if existing_items > 0:
                print(f"  ⏭️  Already has {existing_items} ContentItems, skipping")
                continue

            # Parse items from JSONB
            items_data = content.items
            if not items_data:
                print("  ⚠️  No items data found")
                continue

            if isinstance(items_data, str):
                try:
                    items_data = json.loads(items_data)
                except json.JSONDecodeError:
                    print(f"  ❌ Failed to parse items JSON for content {content.id}")
                    continue

            if not isinstance(items_data, list):
                print(f"  ⚠️  Items data is not a list: {type(items_data)}")
                continue

            print(f"  📦 Creating {len(items_data)} ContentItems...")

            # Create ContentItem records
            for i, item_data in enumerate(items_data):
                if isinstance(item_data, str):
                    # Simple text item
                    content_item = ContentItem(
                        content_id=content.id,
                        order_index=i,
                        text=item_data,
                        translation=None,
                        audio_url=None,
                        item_metadata={},
                    )
                elif isinstance(item_data, dict):
                    # Structured item data
                    content_item = ContentItem(
                        content_id=content.id,
                        order_index=i,
                        text=item_data.get("text", ""),
                        translation=item_data.get("translation"),
                        audio_url=item_data.get("audio_url"),
                        item_metadata=item_data.get("metadata", {}),
                    )
                else:
                    print(
                        f"    ⚠️  Skipping invalid item at index {i}: {type(item_data)}"
                    )
                    continue

                db.add(content_item)
                print(f"    ✅ Created item {i}: {content_item.text[:50]}...")

            migrated_count += 1

        # Commit all changes
        db.commit()
        print(f"\n🎉 Migration completed! Migrated {migrated_count} Content records")

        # Verify results
        total_content_items = db.query(ContentItem).count()
        print(f"📊 Total ContentItems in database: {total_content_items}")

        # Show some examples
        print("\n📋 Sample ContentItems:")
        sample_items = db.query(ContentItem).limit(5).all()
        for item in sample_items:
            print(
                f"  - Content {item.content_id}, Order {item.order_index}: {item.text[:30]}..."
            )

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def verify_migration():
    """Verify that the migration was successful"""
    db = SessionLocal()

    try:
        print("\n🔍 Verifying migration...")

        # Check Content vs ContentItem counts
        contents_with_items = (
            db.query(Content).filter(Content.items.isnot(None)).count()
        )
        content_items_count = db.query(ContentItem).count()

        print(f"Contents with items: {contents_with_items}")
        print(f"ContentItems created: {content_items_count}")

        # Check for any Content that should have items but doesn't
        contents_missing_items = []
        contents = db.query(Content).filter(Content.items.isnot(None)).all()

        for content in contents:
            item_count = (
                db.query(ContentItem)
                .filter(ContentItem.content_id == content.id)
                .count()
            )

            if item_count == 0:
                contents_missing_items.append(content.id)

        if contents_missing_items:
            print(f"⚠️  Contents missing ContentItems: {contents_missing_items}")
        else:
            print("✅ All Contents with items have corresponding ContentItems")

    finally:
        db.close()


if __name__ == "__main__":
    print("ContentItem Migration Script")
    print("=" * 50)

    # Run migration
    migrate_content_items()

    # Verify results
    verify_migration()

    print("\n✨ Migration script completed!")
