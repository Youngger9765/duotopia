#!/usr/bin/env python3
"""
測試 Teacher Subscription 頁面配額連動
"""
import requests
import json

BASE_URL = "http://localhost:8080"


# 模擬登入取得 token（使用 demo 帳號）
def get_auth_token():
    """登入並取得 JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/teachers/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"❌ 登入失敗: {response.status_code}")
        print(response.text)
        return None


def test_subscription_status_with_quota():
    """測試 /subscription/status 是否包含 quota_used"""
    print("\n1️⃣ 測試 /subscription/status (需要登入)")

    # 1. 取得 token
    token = get_auth_token()
    if not token:
        print("❌ 無法取得 token，跳過測試")
        return

    # 2. 呼叫 /subscription/status
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/subscription/status", headers=headers)

    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # 3. 檢查是否有 quota_used 欄位
    if "quota_used" in data:
        print(f"✅ quota_used 欄位存在: {data['quota_used']} 秒")
    else:
        print("❌ quota_used 欄位不存在！")

    return data


def test_update_quota_and_check():
    """測試更新配額後，訂閱頁面是否能看到變化"""
    print("\n2️⃣ 測試更新配額並檢查訂閱頁面")

    # 1. 先透過測試 API 更新配額 (+500秒)
    print("\n📝 步驟 1: 使用測試 API 更新配額")
    response = requests.post(
        f"{BASE_URL}/api/test/subscription/update",
        json={"action": "update_quota", "quota_delta": 500},
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    # 2. 再透過正式 API 檢查
    print("\n📝 步驟 2: 檢查正式訂閱頁面 API")
    token = get_auth_token()
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/subscription/status", headers=headers)
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

        if data.get("quota_used") == 500:
            print("✅ 配額已正確更新並顯示在訂閱頁面！")
        else:
            print(f"❌ 配額不一致！預期 500，實際 {data.get('quota_used')}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Teacher Subscription 配額連動測試")
    print("=" * 60)

    # 測試 1: 檢查 API 是否回傳 quota_used
    test_subscription_status_with_quota()

    # 測試 2: 更新配額並檢查
    test_update_quota_and_check()

    print("\n" + "=" * 60)
    print("✅ 測試完成！")
    print("📌 請打開 http://localhost:5173/teacher/subscription 檢查配額顯示")
    print("=" * 60)
