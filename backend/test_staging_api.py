#!/usr/bin/env python3
"""
Staging API 測試腳本
測試 staging 環境的各項功能
"""

import requests
import json
from datetime import datetime

# Staging API URL
STAGING_URL = "https://duotopia-backend-staging-qchnzlfpda-de.a.run.app"

def print_section(title):
    """打印分隔線"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def test_health_check():
    """測試健康檢查端點"""
    print_section("1. 測試健康檢查 API")
    
    try:
        response = requests.get(f"{STAGING_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nParsed JSON: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"\n❌ 健康檢查失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ 請求失敗: {str(e)}")
        return False

def test_teacher_login():
    """測試教師登入功能"""
    print_section("2. 測試教師登入 (teacher@individual.com)")
    
    login_data = {
        "email": "teacher@individual.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(
            f"{STAGING_URL}/api/auth/teacher/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nParsed JSON: {json.dumps(data, indent=2)}")
            
            # 返回 access_token 供後續測試使用
            if "access_token" in data:
                print(f"\n✅ 登入成功，獲得 token")
                return data["access_token"]
            else:
                print(f"\n❌ 登入回應中沒有 access_token")
                return None
        else:
            print(f"\n❌ 登入失敗: {response.status_code}")
            
            # 如果有錯誤詳情，嘗試解析
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
            return None
    except Exception as e:
        print(f"\n❌ 請求失敗: {str(e)}")
        return None

def test_get_courses(token):
    """測試獲取課程列表"""
    print_section("3. 測試獲取課程列表 (需要認證)")
    
    if not token:
        print("❌ 沒有有效的 token，跳過測試")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{STAGING_URL}/api/courses",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nParsed JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print(f"\n✅ 成功獲取課程列表，共 {len(data)} 個課程")
            return True
        else:
            print(f"\n❌ 獲取課程失敗: {response.status_code}")
            
            # 如果有錯誤詳情，嘗試解析
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
            return False
    except Exception as e:
        print(f"\n❌ 請求失敗: {str(e)}")
        return False

def check_server_logs():
    """檢查是否有 models_dual_system 相關錯誤"""
    print_section("4. 檢查 models_dual_system 相關錯誤")
    
    print("請執行以下命令查看服務器日誌：")
    print("gcloud run logs read duotopia-backend-staging --limit=50 | grep -i 'models_dual_system'")
    print("\n或查看所有錯誤：")
    print("gcloud run logs read duotopia-backend-staging --limit=50 | grep -i 'error'")

def main():
    """主測試流程"""
    print(f"開始測試 Staging API: {STAGING_URL}")
    print(f"測試時間: {datetime.now()}")
    
    # 1. 健康檢查
    health_ok = test_health_check()
    
    # 2. 教師登入
    token = test_teacher_login()
    
    # 3. 獲取課程列表
    if token:
        courses_ok = test_get_courses(token)
    else:
        print("\n❌ 無法測試課程列表，因為登入失敗")
    
    # 4. 提示檢查日誌
    check_server_logs()
    
    print_section("測試總結")
    print(f"健康檢查: {'✅ 通過' if health_ok else '❌ 失敗'}")
    print(f"教師登入: {'✅ 通過' if token else '❌ 失敗'}")
    if token:
        print(f"課程列表: {'✅ 通過' if courses_ok else '❌ 失敗'}")

if __name__ == "__main__":
    main()