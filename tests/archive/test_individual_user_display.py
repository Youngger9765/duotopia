#!/usr/bin/env python3
"""
測試個體戶教師登入後的使用者資料顯示
"""
import requests
import time

# API 基礎 URL
API_BASE_URL = "http://localhost:8000"

def test_individual_teacher_login():
    """測試個體戶教師登入並檢查返回的資料"""
    
    # 1. 登入
    print("1. 測試個體戶教師登入...")
    login_data = {
        "username": "individual_teacher@gmail.com",
        "password": "teacher123"
    }
    
    response = requests.post(f"{API_BASE_URL}/api/auth/login", data=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print("✓ 登入成功")
        print(f"  - Token: {data['access_token'][:20]}...")
        print(f"  - User ID: {data.get('user_id')}")
        print(f"  - Full Name: {data.get('full_name')}")
        print(f"  - Email: {data.get('email')}")
        print(f"  - Is Individual Teacher: {data.get('is_individual_teacher')}")
        print(f"  - User Type: {data.get('user_type')}")
        
        # 檢查返回的資料
        assert data.get('is_individual_teacher') == True, "應該是個體戶教師"
        assert data.get('full_name') is not None, "應該有 full_name"
        assert data.get('user_id') is not None, "應該有 user_id"
        
        return data['access_token']
    else:
        print(f"✗ 登入失敗: {response.status_code}")
        print(f"  錯誤: {response.text}")
        return None

def test_role_current_api(token):
    """測試 /api/role/current 端點"""
    print("\n2. 測試 /api/role/current 端點...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{API_BASE_URL}/api/role/current", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✓ 成功獲取當前角色資訊")
        print(f"  - Full Name: {data.get('full_name')}")
        print(f"  - Email: {data.get('email')}")
        print(f"  - Is Individual Teacher: {data.get('is_individual_teacher')}")
        print(f"  - Has Multiple Roles: {data.get('has_multiple_roles')}")
        
        # 檢查返回的資料
        assert data.get('is_individual_teacher') == True, "應該是個體戶教師"
        assert data.get('full_name') is not None, "應該有 full_name"
        assert data.get('email') is not None, "應該有 email"
        
        return True
    else:
        print(f"✗ 獲取角色資訊失敗: {response.status_code}")
        print(f"  錯誤: {response.text}")
        return False

def main():
    print("=== 測試個體戶教師使用者資料顯示 ===\n")
    
    # 測試登入
    token = test_individual_teacher_login()
    
    if token:
        # 測試獲取當前角色資訊
        test_role_current_api(token)
        
        print("\n✅ 測試完成！")
        print("\n建議：")
        print("1. 確認前端已經正確顯示使用者名稱和 email")
        print("2. 檢查 localStorage 是否有儲存正確的資料")
        print("3. 在瀏覽器開發者工具中檢查：")
        print("   - localStorage.getItem('userFullName')")
        print("   - localStorage.getItem('userEmail')")
        print("   - localStorage.getItem('userRole')")
    else:
        print("\n❌ 測試失敗：無法登入")

if __name__ == "__main__":
    main()