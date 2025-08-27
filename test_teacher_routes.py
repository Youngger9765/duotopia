#!/usr/bin/env python3
"""
測試教師後台路由功能
"""
import requests
import json

BASE_URL = "http://localhost:5173"

def test_teacher_routes():
    print("🚀 測試教師路由功能")
    print("=" * 50)
    
    # 測試各個路由是否可以訪問
    routes = [
        "/teacher/login",
        "/teacher/dashboard", 
        "/teacher/classrooms",
        "/teacher/students",
        "/teacher/programs"
    ]
    
    print("\n📍 檢查路由是否可訪問：")
    for route in routes:
        url = f"{BASE_URL}{route}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # 檢查是否包含 React app
                if "root" in response.text:
                    print(f"✅ {route} - 可訪問 (React App 載入成功)")
                else:
                    print(f"⚠️  {route} - 可訪問但內容可能有問題")
            else:
                print(f"❌ {route} - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {route} - 錯誤: {e}")
    
    print("\n" + "=" * 50)
    print("測試完成！")
    print("\n💡 提示：")
    print("1. 請確保前端開發服務器正在運行 (npm run dev)")
    print("2. 登入後才能看到完整的教師後台功能")
    print("3. 可以使用 demo@duotopia.com / demo123 測試登入")

if __name__ == "__main__":
    test_teacher_routes()