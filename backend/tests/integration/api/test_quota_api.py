#!/usr/bin/env python3
"""
測試配額 API 功能
"""
import requests
import json

BASE_URL = "http://localhost:8080"


def test_get_status():
    """測試取得訂閱狀態（包含配額）"""
    print("\n1️⃣ 測試取得訂閱狀態")
    response = requests.get(f"{BASE_URL}/api/test/subscription/status")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def test_update_quota(delta):
    """測試更新配額"""
    print(f"\n2️⃣ 測試更新配額 ({delta:+d} 秒)")
    payload = {"action": "update_quota", "quota_delta": delta}
    response = requests.post(f"{BASE_URL}/api/test/subscription/update", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def test_reset_quota():
    """測試重置配額"""
    print("\n3️⃣ 測試重置配額")
    # 先取得當前使用量
    status = test_get_status()
    current_used = status.get("quota_used", 0)

    # 重置（減去當前使用量）
    if current_used > 0:
        return test_update_quota(-current_used)
    else:
        print("配額已經是 0，無需重置")
        return status


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 配額 API 測試")
    print("=" * 60)

    # 1. 先取得狀態
    status = test_get_status()

    # 2. 增加配額
    test_update_quota(500)

    # 3. 再次取得狀態確認
    test_get_status()

    # 4. 減少配額
    test_update_quota(-100)

    # 5. 最後取得狀態
    test_get_status()

    # 6. 重置配額
    test_reset_quota()

    # 7. 確認已重置
    final = test_get_status()

    print("\n" + "=" * 60)
    print(f"✅ 測試完成！最終配額使用量: {final.get('quota_used', 0)} 秒")
    print("=" * 60)
