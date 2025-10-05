#!/usr/bin/env python3
"""
測試訂閱 API 端點
"""
import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:8080"


def test_subscription_apis():
    """測試訂閱相關 API"""

    print("\n" + "=" * 60)
    print("  🧪 測試訂閱 API")
    print("=" * 60 + "\n")

    # 1. 先登入取得 token
    print("1️⃣ 登入取得 token...")
    login_data = {"username": "demo@duotopia.com", "password": "demo123"}

    login_response = requests.post(f"{BASE_URL}/api/teachers/login", data=login_data)

    if login_response.status_code != 200:
        print(f"❌ 登入失敗: {login_response.status_code}")
        print(login_response.text)
        return

    token = login_response.json()["access_token"]
    print(f"✅ 取得 token: {token[:30]}...")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2. 測試訂閱狀態 API
    print("\n2️⃣ 測試訂閱狀態 API...")
    sub_response = requests.get(
        f"{BASE_URL}/api/teachers/subscription/status", headers=headers
    )

    print(f"Status Code: {sub_response.status_code}")
    if sub_response.status_code == 200:
        sub_data = sub_response.json()
        print("✅ 訂閱狀態:")
        print(json.dumps(sub_data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 失敗: {sub_response.text}")

    # 3. 測試付款歷史 API
    print("\n3️⃣ 測試付款歷史 API...")
    payment_response = requests.get(f"{BASE_URL}/api/payment/history", headers=headers)

    print(f"Status Code: {payment_response.status_code}")
    if payment_response.status_code == 200:
        payment_data = payment_response.json()
        print("✅ 付款歷史:")
        print(json.dumps(payment_data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 失敗: {payment_response.text}")

    print("\n" + "=" * 60)
    print("  ✅ 測試完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_subscription_apis()
