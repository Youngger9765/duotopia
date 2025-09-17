#!/usr/bin/env python3
"""Test script to verify read-only mode functionality"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"
STUDENT_ID = 1
ASSIGNMENT_ID = 1

def get_student_token():
    """Get authentication token for student"""
    response = requests.post(f"{BASE_URL}/api/students/auth",
                           json={"username": "student1", "password": "password123"})
    if response.status_code == 200:
        return response.json().get("token")
    print(f"Failed to get student token: {response.status_code}")
    return None

def check_assignment_status():
    """Check assignment status and activities"""
    token = get_student_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Get assignment activities
    response = requests.get(
        f"{BASE_URL}/api/students/{STUDENT_ID}/assignments/{ASSIGNMENT_ID}/activities",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print("Assignment Activities Response:")
        print(f"Assignment ID: {data.get('assignment_id')}")
        print(f"Title: {data.get('title')}")
        print(f"Status: {data.get('status')}")
        print(f"Total Activities: {data.get('total_activities')}")

        # Check if status indicates read-only mode
        if data.get('status') in ['SUBMITTED', 'GRADED']:
            print("\n✅ Assignment is in read-only mode (SUBMITTED/GRADED)")
        else:
            print(f"\n⚠️ Assignment status is: {data.get('status')}")

        return data
    else:
        print(f"Failed to get activities: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    print("Testing Read-Only Mode Functionality\n")
    print("=" * 50)
    check_assignment_status()
