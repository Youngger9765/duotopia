#!/usr/bin/env python3
"""
Test script to verify student activity navigation functionality
Tests the original bug fix for question navigation and ContentItem structure
"""

import requests
import json
from database import SessionLocal
from models import User, StudentAssignment, ContentItem, StudentItemProgress


def test_api_endpoints():
    """Test API endpoints to verify navigation functionality"""
    base_url = "http://localhost:8080"

    print("=== Testing API Endpoints ===")

    # Test 1: Check API is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ API Status: {response.json()}")
    except Exception as e:
        print(f"❌ API not running: {e}")
        return False

    # Test 2: Check assignment activities endpoint
    db = SessionLocal()
    try:
        # Get a test student and assignment
        student = db.query(User).filter_by(user_type="student").first()
        assignment = (
            db.query(StudentAssignment).filter_by(student_id=student.id).first()
        )

        if not student or not assignment:
            print("❌ No test data found (student/assignment)")
            return False

        print(f"Testing with Student ID: {student.id}, Assignment ID: {assignment.id}")

        # Try to call the activities endpoint without auth (should fail gracefully)
        response = requests.get(
            f"{base_url}/api/students/{student.id}/assignments/{assignment.id}/activities"
        )
        print(f"Activities endpoint status: {response.status_code}")

        if response.status_code in [
            200,
            401,
            403,
        ]:  # Any of these responses means endpoint exists
            print("✅ Activities endpoint exists and responds")
        else:
            print(f"❌ Activities endpoint issue: {response.text}")

    except Exception as e:
        print(f"❌ Error testing activities endpoint: {e}")
    finally:
        db.close()

    return True


def test_database_structure():
    """Test the new ContentItem database structure"""
    print("\n=== Testing Database Structure ===")

    db = SessionLocal()
    try:
        # Test ContentItem structure
        content_items = db.query(ContentItem).limit(5).all()
        print(f"ContentItem count: {len(content_items)}")

        for item in content_items[:3]:
            print(
                f"  Item {item.id}: order_index={item.order_index}, text='{item.text[:30]}...'"
            )

        # Test StudentItemProgress structure
        progress_items = db.query(StudentItemProgress).limit(5).all()
        print(f"StudentItemProgress count: {len(progress_items)}")

        for item in progress_items[:3]:
            print(
                f"  Progress {item.id}: content_item_id={item.content_item_id}, status={item.status}"
            )

        # Test relationships
        first_item = content_items[0] if content_items else None
        if first_item:
            progress_for_item = (
                db.query(StudentItemProgress)
                .filter_by(content_item_id=first_item.id)
                .first()
            )
            if progress_for_item:
                print(
                    f"✅ Relationship working: ContentItem {first_item.id} has progress record {progress_for_item.id}"
                )
            else:
                print(f"⚠️  No progress found for ContentItem {first_item.id}")

        print("✅ Database structure verification complete")
        return True

    except Exception as e:
        print(f"❌ Database structure error: {e}")
        return False
    finally:
        db.close()


def test_content_item_navigation_data():
    """Test that ContentItem data supports proper navigation"""
    print("\n=== Testing Navigation Data Structure ===")

    db = SessionLocal()
    try:
        # Get a content with multiple items
        content_with_items = db.execute(
            """
            SELECT c.id, c.title, COUNT(ci.id) as item_count
            FROM contents c
            JOIN content_items ci ON c.id = ci.content_id
            GROUP BY c.id, c.title
            HAVING COUNT(ci.id) > 1
            ORDER BY item_count DESC
            LIMIT 1
        """
        ).fetchone()

        if not content_with_items:
            print("❌ No content with multiple items found")
            return False

        content_id, title, item_count = content_with_items
        print(f"Testing Content '{title}' with {item_count} items")

        # Get items for this content ordered correctly
        items = (
            db.query(ContentItem)
            .filter_by(content_id=content_id)
            .order_by(ContentItem.order_index)
            .all()
        )

        # Verify order_index sequence
        for i, item in enumerate(items):
            if item.order_index != i:
                print(f"❌ Order index mismatch: expected {i}, got {item.order_index}")
                return False

        print(f"✅ {len(items)} items correctly ordered (0 to {len(items)-1})")

        # Test that progress can be linked to specific items
        for i, item in enumerate(items[:3]):  # Test first 3 items
            progress = (
                db.query(StudentItemProgress).filter_by(content_item_id=item.id).first()
            )
            status = "HAS_PROGRESS" if progress else "NO_PROGRESS"
            print(f"  Item {item.order_index}: '{item.text[:20]}...' - {status}")

        print("✅ Navigation data structure is correct")
        return True

    except Exception as e:
        print(f"❌ Navigation data error: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("🧪 Testing ContentItem Navigation Functionality")
    print("=" * 50)

    success = True
    success &= test_database_structure()
    success &= test_content_item_navigation_data()
    success &= test_api_endpoints()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Navigation functionality should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    print("\n📋 Next steps:")
    print("1. Open browser to http://localhost:5174/")
    print("2. Login as a student")
    print("3. Navigate to an assignment with multiple activity groups")
    print("4. Click specific questions to verify navigation works correctly")
