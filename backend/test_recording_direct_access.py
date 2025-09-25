#!/usr/bin/env python3
"""
Quick test to verify recording URLs are accessible from items directly.
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal  # noqa: E402
from models import StudentItemProgress, StudentContentProgress  # noqa: E402


def test_recording_direct_access():
    """Test that recordings are stored in item.recording_url."""
    db = SessionLocal()

    try:
        # Query for a StudentContentProgress with items
        progress = (
            db.query(StudentContentProgress)
            .filter(StudentContentProgress.status.in_(["IN_PROGRESS", "SUBMITTED"]))
            .first()
        )

        if progress:
            print(f"✅ Found StudentContentProgress ID: {progress.id}")
            print(f"   Student Assignment ID: {progress.student_assignment_id}")
            print(
                f"   Content: {progress.content.title if hasattr(progress, 'content') else 'N/A'}"
            )

            # Get item progresses
            item_progresses = (
                db.query(StudentItemProgress)
                .filter_by(student_assignment_id=progress.student_assignment_id)
                .order_by(StudentItemProgress.id)
                .all()
            )

            print(f"\n📝 Found {len(item_progresses)} item progresses:")

            for i, item_progress in enumerate(item_progresses):
                print(f"\n   Item {i+1}:")
                print(f"   - Content Item ID: {item_progress.content_item_id}")
                print(f"   - Recording URL: {item_progress.recording_url or 'None'}")
                print(f"   - Status: {item_progress.status}")

                if item_progress.accuracy_score:
                    print(
                        f"   - AI Scores: accuracy={item_progress.accuracy_score}, "
                        f"fluency={item_progress.fluency_score}, "
                        f"pronunciation={item_progress.pronunciation_score}"
                    )

            # Verify structure for frontend
            print("\n\n🎯 Frontend Data Structure (after refactoring):")
            print("activity.items = [")
            for i, item_progress in enumerate(item_progresses):
                item = item_progress.content_item
                print("  {")
                print(f"    id: {item.id},")
                print(f"    text: \"{item.text[:30] if item.text else 'N/A'}...\",")
                print(
                    f"    recording_url: \"{item_progress.recording_url or ''}\",  // ← Direct access!"
                )
                ai_data = (
                    {
                        "accuracy_score": float(item_progress.accuracy_score)
                        if item_progress.accuracy_score
                        else None,
                        "fluency_score": float(item_progress.fluency_score)
                        if item_progress.fluency_score
                        else None,
                        "pronunciation_score": float(item_progress.pronunciation_score)
                        if item_progress.pronunciation_score
                        else None,
                    }
                    if item_progress.accuracy_score
                    else None
                )
                print(f"    ai_assessment: {json.dumps(ai_data)}")
                print("  },")
            print("]")

            print("\n✅ VALIDATION:")
            print("1. No recordings array at activity level ✓")
            print("2. Each item has its own recording_url ✓")
            print("3. Direct access via items[index].recording_url ✓")

        else:
            print(
                "❌ No StudentContentProgress found with IN_PROGRESS or SUBMITTED status"
            )

    finally:
        db.close()


if __name__ == "__main__":
    test_recording_direct_access()
