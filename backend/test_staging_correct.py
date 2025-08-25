#!/usr/bin/env python3
"""
使用正確的格式測試 staging API
"""

import requests
import json
from datetime import datetime

STAGING_URL = "https://duotopia-backend-staging-qchnzlfpda-de.a.run.app"

def print_section(title):
    """打印分隔線"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def test_teacher_login_form():
    """測試教師登入 - 使用 form-encoded 格式"""
    print_section("測試教師登入 (Form-encoded)")
    
    # 使用 form data 而不是 JSON
    login_data = {
        "username": "teacher@individual.com",  # 注意是 username 不是 email
        "password": "password123"
    }
    
    try:
        response = requests.post(
            f"{STAGING_URL}/api/auth/login",
            data=login_data,  # 使用 data 而不是 json
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nParsed JSON: {json.dumps(data, indent=2)}")
            
            if "access_token" in data:
                print(f"\n✅ 登入成功")
                return data["access_token"]
        else:
            print(f"\n❌ 登入失敗: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
        return None
    except Exception as e:
        print(f"\n❌ 請求失敗: {str(e)}")
        return None

def test_get_current_user(token):
    """測試獲取當前用戶信息"""
    print_section("測試獲取當前用戶信息")
    
    if not token:
        print("❌ 沒有有效的 token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{STAGING_URL}/api/auth/validate",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nUser Info: {json.dumps(data, indent=2)}")
        print("✅ 成功獲取用戶信息")
        return True
    else:
        print("❌ 獲取用戶信息失敗")
        return False

def test_get_courses(token):
    """測試獲取課程列表"""
    print_section("測試獲取課程列表")
    
    if not token:
        print("❌ 沒有有效的 token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{STAGING_URL}/api/courses",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ 成功獲取 {len(data)} 個課程")
        
        # 顯示前幾個課程
        for i, course in enumerate(data[:3]):
            print(f"\nCourse {i+1}:")
            print(f"  ID: {course.get('id')}")
            print(f"  Title: {course.get('title')}")
            print(f"  Description: {course.get('description')}")
        
        return True
    else:
        print("❌ 獲取課程列表失敗")
        return False

def test_student_login():
    """測試學生登入"""
    print_section("測試學生登入")
    
    # 測試幾個不同的學生
    students = [
        {"email": "alice@example.com", "birth_date": "20100315"},
        {"email": "bob@example.com", "birth_date": "20090720"},
        {"email": "student1@school1.com", "birth_date": "20120101"}
    ]
    
    for student in students:
        print(f"\n嘗試登入: {student['email']}")
        
        response = requests.post(
            f"{STAGING_URL}/api/auth/student/login",
            json=student,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ 登入成功")
            data = response.json()
            print(f"Token: {data.get('access_token', '')[:50]}...")
            return data.get('access_token')
        else:
            print(f"❌ 登入失敗: {response.text}")
    
    return None

def check_api_structure():
    """檢查 API 結構"""
    print_section("檢查 API 結構")
    
    response = requests.get(f"{STAGING_URL}/openapi.json", timeout=10)
    if response.status_code == 200:
        api_spec = response.json()
        
        print("\n可用的 API 端點:")
        for path, methods in api_spec.get("paths", {}).items():
            for method, details in methods.items():
                print(f"{method.upper():6} {path:40} - {details.get('summary', 'No summary')}")
        
        # 檢查是否有 models_dual_system 相關內容
        api_text = json.dumps(api_spec)
        if "models_dual_system" in api_text:
            print("\n⚠️  發現 models_dual_system 相關內容!")
        else:
            print("\n✅ 沒有發現 models_dual_system 相關內容")

def main():
    """主測試流程"""
    print(f"Staging API 測試")
    print(f"URL: {STAGING_URL}")
    print(f"時間: {datetime.now()}")
    
    # 1. 測試教師登入
    teacher_token = test_teacher_login_form()
    
    # 2. 如果教師登入成功，測試其他功能
    if teacher_token:
        test_get_current_user(teacher_token)
        test_get_courses(teacher_token)
    
    # 3. 測試學生登入
    student_token = test_student_login()
    
    # 4. 檢查 API 結構
    check_api_structure()

if __name__ == "__main__":
    main()