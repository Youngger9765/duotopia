#!/usr/bin/env python3
"""E2E 測試：學生密碼管理功能"""
import asyncio
import requests
import json

BASE_URL = "http://localhost:8000"

def test_student_password_management():
    """測試學生密碼管理功能"""
    
    print("🧪 E2E 測試：密碼管理功能")
    print("=" * 50)
    
    # 假設的認證token (實際使用時需要真實登入)
    headers = {
        "Authorization": "Bearer fake-token-for-testing",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. 測試建立學生 (email可選)
        print("1. 測試建立學生...")
        student_data = {
            "full_name": "測試學生",
            "birth_date": "2010-01-01",
            "referred_by": "朋友推薦",
            "learning_goals": "提升英語能力"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/individual/students",
            json=student_data,
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            student = response.json()
            print(f"✅ 學生建立成功")
            print(f"   ID: {student['id']}")
            print(f"   姓名: {student['full_name']}")
            print(f"   預設密碼: {student.get('default_password', 'N/A')}")
            print(f"   密碼狀態: {'預設' if student.get('is_default_password') else '自訂'}")
            student_id = student['id']
        else:
            print(f"❌ 建立失敗: {response.text}")
            return
        
        # 2. 測試獲取學生列表
        print("\n2. 測試獲取學生列表...")
        response = requests.get(f"{BASE_URL}/api/individual/students", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            students = response.json()
            print(f"✅ 獲取成功，共 {len(students)} 個學生")
            for s in students:
                print(f"   - {s['full_name']}: {'預設密碼' if s.get('is_default_password') else '自訂密碼'}")
        else:
            print(f"❌ 獲取失敗: {response.text}")
        
        # 3. 測試重置密碼
        print("\n3. 測試重置密碼...")
        response = requests.post(
            f"{BASE_URL}/api/individual/students/{student_id}/reset-password",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 密碼重置成功")
            print(f"   訊息: {result['message']}")
            print(f"   新密碼: {result.get('default_password', 'N/A')}")
        else:
            print(f"❌ 重置失敗: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務 (http://localhost:8000)")
        print("請確保後端服務正在運行")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_student_password_management()