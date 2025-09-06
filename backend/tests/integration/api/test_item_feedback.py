#!/usr/bin/env python3
"""Test item-level feedback persistence."""

import requests
import json  # noqa: F401

# Test configuration
BASE_URL = "http://localhost:8000/api"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"
ASSIGNMENT_ID = 2
STUDENT_ID = 1


def test_item_feedback():
    """Test saving and retrieving item-level feedback."""

    # 1. Login as teacher
    print("1. Logging in as teacher...")
    login_response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # 2. Submit grade with item-level feedback
    print("\n2. Submitting grade with item feedback...")
    grading_data = {
        "student_id": STUDENT_ID,
        "score": 88,
        "feedback": "整體表現良好，繼續保持！",
        "item_results": [
            {"item_index": 0, "score": 95, "feedback": "第一題：發音清晰，表達流暢", "passed": True},
            {"item_index": 1, "score": 85, "feedback": "第二題：語調需要加強練習", "passed": True},
            {"item_index": 2, "score": 70, "feedback": "第三題：請注意重音位置", "passed": False},
        ],
    }

    grade_response = requests.post(
        f"{BASE_URL}/teachers/assignments/{ASSIGNMENT_ID}/grade",
        headers=headers,
        json=grading_data,
    )

    if grade_response.status_code == 200:
        print("✅ Grade with item feedback submitted successfully!")
    else:
        print(f"❌ Grading submission failed: {grade_response.text}")
        return False

    # 3. Retrieve submission to verify feedback persists
    print("\n3. Retrieving submission to verify feedback...")
    submission_response = requests.get(
        f"{BASE_URL}/teachers/assignments/{ASSIGNMENT_ID}/submissions/{STUDENT_ID}",
        headers=headers,
    )

    if submission_response.status_code != 200:
        print(f"❌ Failed to retrieve submission: {submission_response.text}")
        return False

    submission = submission_response.json()

    # 4. Check if item feedback is present
    print("\n4. Checking item feedback...")
    has_feedback = False

    if "submissions" in submission:
        for i, item in enumerate(submission["submissions"][:3]):
            if "feedback" in item or "passed" in item:
                has_feedback = True
                print(f"   題目 {i+1}:")
                print(f"     - Feedback: {item.get('feedback', 'N/A')}")
                print(f"     - Passed: {item.get('passed', 'N/A')}")

    if not has_feedback:
        print("❌ No item feedback found in response")
        print(
            f"   Response structure: {json.dumps(submission, indent=2, ensure_ascii=False)[:500]}..."
        )
        return False

    print("\n✅ Item feedback successfully persists!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Item-Level Feedback Persistence")
    print("=" * 60)

    success = test_item_feedback()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! Item feedback is working correctly.")
    else:
        print("❌ Test failed. Item feedback is not persisting.")
    print("=" * 60)
