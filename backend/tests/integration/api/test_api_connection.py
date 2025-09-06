#!/usr/bin/env python3
"""測試 API 連線與環境變數設定"""
import os
import requests


def test_api_connection():
    """測試 API 是否正常運作"""
    print("=" * 50)
    print("🔍 測試 API 連線")
    print("=" * 50)

    # 1. 測試後端直接連線
    backend_url = "http://localhost:8000"
    print(f"\n1️⃣ 測試後端: {backend_url}")

    try:
        response = requests.get(f"{backend_url}/health")
        if response.status_code == 200:
            print(f"   ✅ 後端健康檢查成功: {response.json()}")
        else:
            print(f"   ❌ 後端回應異常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 無法連接後端: {e}")

    # 2. 測試前端環境變數
    print("\n2️⃣ 檢查前端環境變數設定")
    frontend_env_path = "../frontend/.env"

    if os.path.exists(frontend_env_path):
        with open(frontend_env_path, "r") as f:
            env_content = f.read()
            print(f"   📄 .env 內容: {env_content.strip()}")

            if "VITE_API_URL" in env_content:
                vite_url = env_content.split("=")[1].strip()
                print(f"   ✅ VITE_API_URL 已設定: {vite_url}")
            else:
                print("   ❌ VITE_API_URL 未設定")
    else:
        print("   ❌ .env 檔案不存在")

    # 3. 測試前端是否正確載入
    frontend_url = "http://localhost:5173"
    print(f"\n3️⃣ 測試前端: {frontend_url}")

    try:
        response = requests.get(frontend_url)
        if response.status_code == 200:
            print("   ✅ 前端載入成功")
            # 檢查是否有 API 呼叫相關的程式碼
            if "fetch" in response.text or "axios" in response.text:
                print("   ✅ 前端包含 API 呼叫程式碼")
        else:
            print(f"   ❌ 前端回應異常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 無法連接前端: {e}")

    print("\n" + "=" * 50)
    print("測試完成！")
    print("=" * 50)


if __name__ == "__main__":
    test_api_connection()
