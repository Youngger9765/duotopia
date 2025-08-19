#!/usr/bin/env python3
"""
Test login functionality with demo data
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    print("🔐 Testing login functionality...")
    print("=" * 40)
    
    # Test credentials
    test_accounts = [
        {"email": "admin@duotopia.com", "password": "admin123", "role": "管理員"},
        {"email": "teacher1@duotopia.com", "password": "teacher123", "role": "教師"},
        {"email": "student1@duotopia.com", "password": "20090828", "role": "學生"},
    ]
    
    for account in test_accounts:
        print(f"\n🧪 Testing {account['role']}: {account['email']}")
        
        try:
            # Try login
            login_data = {
                "username": account["email"],
                "password": account["password"]
            }
            
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Login successful")
                print(f"   🔑 Token type: {result.get('token_type', 'N/A')}")
                print(f"   👤 User info available: {'user' in result}")
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                print(f"   📝 Response: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def check_api_endpoints():
    print("\n🔍 Checking API endpoints...")
    print("=" * 40)
    
    endpoints = [
        "/health",
        "/docs",
        "/api/auth/login",  # Should return method not allowed for GET
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"✅ {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

if __name__ == "__main__":
    print("🚀 Duotopia API Testing")
    print("=" * 40)
    
    check_api_endpoints()
    test_login()
    
    print("\n" + "=" * 40)
    print("🎯 Testing completed!")
    print("📋 Check results above for any issues")
    print("=" * 40)