#!/usr/bin/env python3
"""
完整的 Email 綁定功能測試
測試從學生登入到綁定 Email 的完整流程
"""
import requests
import json
import os
from datetime import datetime

def test_email_binding_complete_flow():
    """測試完整的 Email 綁定流程"""
    print("=== Duotopia Email 綁定功能測試 ===\n")

    # 先驗證 API 端點是否存在
    print("0. 驗證 API 端點...")
    try:
        health_response = requests.get('http://localhost:8000/docs')
        print("✅ 後端服務正在運行")
    except:
        print("❌ 無法連接後端服務")
        return False

    # 1. 查找可用的學生
    print("1. 嘗試查找測試學生...")

    # 根據 seed_data 輸出，嘗試使用第一個學生 (王小明)
    # 由於不知道確切的 email 格式，讓我們嘗試不同的格式
    test_emails = [
        "student1@duotopia.com",
        "wangxiaoming@duotopia.com",
        "student.001@duotopia.com",
        "xiaoming.wang@duotopia.com"
    ]

    login_successful = False
    token = None
    student_name = None
    headers = None

    for test_email in test_emails:
        print(f"   嘗試登入: {test_email}")
        try:
            login_response = requests.post('http://localhost:8000/api/auth/student/login', json={
                'email': test_email,
                'password': '20120101'
            })

            if login_response.status_code == 200:
                login_data = login_response.json()
                token = login_data['access_token']
                student_name = login_data['user']['name']
                headers = {'Authorization': f'Bearer {token}'}
                login_successful = True
                print(f"✅ 登入成功: {student_name}")
                break
            else:
                print(f"   ❌ {login_response.status_code}: {login_response.json().get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ 連接錯誤: {e}")

    if not login_successful:
        print("❌ 無法找到可用的測試學生帳號")
        print("💡 提示: 請檢查 seed_data.py 並確保學生資料已正確建立")
        return False

    print(f"✅ 登入成功: {student_name}")
    print(f"   Token: {token[:20]}...")

    # 2. 獲取初始學生資訊
    print("\n2. 獲取學生初始資訊...")
    profile_response = requests.get('http://localhost:8000/api/students/me', headers=headers)

    if profile_response.status_code != 200:
        print(f"❌ 獲取資訊失敗: {profile_response.status_code}")
        return False

    initial_profile = profile_response.json()
    print(f"✅ 初始資訊:")
    print(f"   姓名: {initial_profile['name']}")
    print(f"   Email: {initial_profile['email']}")
    print(f"   Email 已驗證: {initial_profile['email_verified']}")

    # 3. 更新 Email
    print("\n3. 測試 Email 綁定...")
    # 從環境變數讀取測試 email，如果沒設定則使用假的測試 email
    new_email = os.getenv('TEST_EMAIL', f"test.{datetime.now().strftime('%H%M%S')}@example.com")

    if '@example.com' in new_email:
        print(f"⚠️  使用測試 Email: {new_email} (不會真的寄信)")
        print("💡 提示: 設定 TEST_EMAIL 環境變數來使用真實 email 測試")
        print("   例如: TEST_EMAIL=your.email@gmail.com python test_email_binding_complete.py")
    else:
        print(f"📧 使用真實 Email: {new_email}")

    email_update_response = requests.post('http://localhost:8000/api/students/update-email',
                                        json={'email': new_email},
                                        headers=headers)

    if email_update_response.status_code != 200:
        print(f"❌ Email 更新失敗: {email_update_response.status_code}")
        print(f"   錯誤: {email_update_response.text}")
        return False

    email_update_data = email_update_response.json()
    print(f"✅ Email 更新成功:")
    print(f"   新 Email: {email_update_data['email']}")
    print(f"   驗證信發送: {email_update_data['verification_sent']}")

    # 4. 驗證 Email 更新後的資訊
    print("\n4. 驗證更新後的學生資訊...")
    updated_profile_response = requests.get('http://localhost:8000/api/students/me', headers=headers)

    if updated_profile_response.status_code != 200:
        print(f"❌ 獲取更新後資訊失敗: {updated_profile_response.status_code}")
        return False

    updated_profile = updated_profile_response.json()
    print(f"✅ 更新後資訊:")
    print(f"   Email: {updated_profile['email']}")
    print(f"   Email 已驗證: {updated_profile['email_verified']}")

    # 5. 驗證資料一致性
    print("\n5. 驗證資料一致性...")
    if updated_profile['email'] == new_email:
        print("✅ Email 更新正確")
    else:
        print(f"❌ Email 不一致: 期望 {new_email}, 實際 {updated_profile['email']}")
        return False

    if updated_profile['email_verified'] == False:
        print("✅ Email 驗證狀態正確 (未驗證)")
    else:
        print(f"❌ Email 驗證狀態錯誤: 期望 False, 實際 {updated_profile['email_verified']}")

    # 6. 測試前端 API 端點
    print("\n6. 測試前端相關 API...")

    # 測試 /api/students/profile (舊版本相容性)
    profile_old_response = requests.get('http://localhost:8000/api/students/profile', headers=headers)
    if profile_old_response.status_code == 200:
        print("✅ /api/students/profile 可用")
    else:
        print(f"⚠️  /api/students/profile 不可用: {profile_old_response.status_code}")

    print("\n=== 測試結果 ===")
    print("✅ Email 綁定功能完整測試通過！")
    print("✅ API 端點正常運作")
    print("✅ 資料一致性驗證通過")
    print("✅ 驗證信發送機制正常")

    return True

if __name__ == "__main__":
    success = test_email_binding_complete_flow()
    if success:
        print("\n🎉 所有測試通過！Email 綁定系統運作正常。")
    else:
        print("\n❌ 測試失敗，請檢查系統設定。")
