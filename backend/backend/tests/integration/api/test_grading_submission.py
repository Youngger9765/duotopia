#!/usr/bin/env python3
"""Test grading submission API endpoint after fix."""

import requests
import json  # noqa: F401
from datetime import datetime  # noqa: F401

# Test configuration
BASE_URL = "http://localhost:8000/api"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"  # Verified password
ASSIGNMENT_ID = 2
STUDENT_ID = 1


def test_grading_submission():
    """Test the grading submission API."""

    # Login as teacher
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

    # Get assignment details
    print(f"\n2. Getting assignment {ASSIGNMENT_ID} details...")
    assignment_response = requests.get(f"{BASE_URL}/teachers/assignments/{ASSIGNMENT_ID}", headers=headers)

    if assignment_response.status_code != 200:
        print(f"❌ Failed to get assignment: {assignment_response.text}")
        return False

    print(f"✅ Assignment retrieved: {assignment_response.json()['title']}")

    # Get student submission
    print(f"\n3. Getting submission for student {STUDENT_ID}...")
    submission_response = requests.get(
        f"{BASE_URL}/teachers/assignments/{ASSIGNMENT_ID}/submissions/{STUDENT_ID}",
        headers=headers,
    )

    if submission_response.status_code != 200:
        print(f"❌ Failed to get submission: {submission_response.text}")
        return False

    submission = submission_response.json()
    # Check the actual structure of the response
    if "id" in submission:
        submission_id = submission["id"]
    elif "submission_id" in submission:
        submission_id = submission["submission_id"]
    else:
        submission_id = STUDENT_ID  # Use student ID as fallback
    print(f"✅ Submission retrieved for student {STUDENT_ID}")

    # Prepare grading data
    grading_data = {
        "submission_id": submission_id,
        "student_id": STUDENT_ID,
        "total_score": 85,
        "feedback": "很好的表現！繼續加油！",
        "item_results": [
            {
                "item_index": 0,
                "score": 90,
                "feedback": "發音清晰，語調自然",
                "passed": True,
            },
            {
                "item_index": 1,
                "score": 80,
                "feedback": "句子結構正確，但可以更流暢",
                "passed": True,
            },
        ],
        "graded_at": datetime.now().isoformat(),
    }

    # Test grading submission
    print(f"\n4. Submitting grading for assignment {ASSIGNMENT_ID}...")
    print(f"   Endpoint: POST {BASE_URL}/teachers/assignments/{ASSIGNMENT_ID}/grade")

    grade_response = requests.post(
        f"{BASE_URL}/teachers/assignments/{ASSIGNMENT_ID}/grade",
        headers=headers,
        json=grading_data,
    )

    print(f"   Status Code: {grade_response.status_code}")

    if grade_response.status_code == 200:
        print("✅ Grading submitted successfully!")
        result = grade_response.json()
        if isinstance(result, dict):
            if "submission_id" in result:
                print(f"   Updated submission ID: {result['submission_id']}")
            if "status" in result:
                print(f"   Status: {result['status']}")
            if "total_score" in result:
                print(f"   Total Score: {result['total_score']}")
        else:
            print(f"   Response: {result}")
        return True
    else:
        print("❌ Grading submission failed!")
        print(f"   Error: {grade_response.text}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Grading Submission API")
    print("=" * 60)

    success = test_grading_submission()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! Grading API is working correctly.")
    else:
        print("❌ Test failed. Please check the error messages above.")
    print("=" * 60)
