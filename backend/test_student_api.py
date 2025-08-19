#!/usr/bin/env python3
"""Test student API endpoints directly"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test student 4-step flow
print("1. Testing send OTP...")
response = requests.post(f"{BASE_URL}/api/auth/student/send-otp", 
                        json={"phone_number": "+1234567890"})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

print("\n2. Testing verify OTP...")
response = requests.post(f"{BASE_URL}/api/auth/student/verify-otp",
                        json={"phone_number": "+1234567890", "otp": "123456"})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    temp_token = response.json()["temp_token"]
    
    print("\n3. Testing submit info...")
    headers = {"Authorization": f"Bearer {temp_token}"}
    response = requests.post(f"{BASE_URL}/api/auth/student/submit-info",
                            json={"name": "Test Student", "grade": 10, "school": "Test High School"},
                            headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")