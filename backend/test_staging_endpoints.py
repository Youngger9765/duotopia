#!/usr/bin/env python3
"""
測試 staging 環境的各種可能端點
"""

import requests
import json

STAGING_URL = "https://duotopia-backend-staging-qchnzlfpda-de.a.run.app"

def test_endpoint(method, path, data=None, headers=None):
    """測試單個端點"""
    url = f"{STAGING_URL}{path}"
    print(f"\n{method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    print("測試 Staging API 端點")
    print("="*60)
    
    # 1. 基本端點
    print("\n### 基本端點測試 ###")
    test_endpoint("GET", "/")
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/api")
    test_endpoint("GET", "/api/health")
    
    # 2. 認證端點（各種可能的路徑）
    print("\n### 認證端點測試 ###")
    login_data = {
        "email": "teacher@individual.com",
        "password": "password123"
    }
    
    # 可能的教師登入端點
    test_endpoint("POST", "/auth/teacher/login", login_data)
    test_endpoint("POST", "/api/auth/teacher/login", login_data)
    test_endpoint("POST", "/api/auth/login", login_data)
    test_endpoint("POST", "/api/auth/dual/login", login_data)
    test_endpoint("POST", "/api/auth/user/login", login_data)
    
    # 3. 測試 validate 端點
    print("\n### Validate 端點測試 ###")
    test_endpoint("GET", "/api/auth/validate")
    test_endpoint("POST", "/api/auth/validate")
    
    # 4. 測試學生登入
    print("\n### 學生登入測試 ###")
    student_data = {
        "email": "alice@example.com",
        "birth_date": "20100315"
    }
    test_endpoint("POST", "/api/auth/student/login", student_data)
    
    # 5. 檢查 API 文檔
    print("\n### API 文檔測試 ###")
    test_endpoint("GET", "/docs")
    test_endpoint("GET", "/redoc")
    test_endpoint("GET", "/openapi.json")

if __name__ == "__main__":
    main()