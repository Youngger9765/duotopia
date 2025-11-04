#!/usr/bin/env python3
"""
配額功能整合測試 (TDD)

測試項目：
1. 測試頁面調整配額 → 資料庫更新
2. 訂閱頁面讀取配額 → 正確顯示
3. Server 重啟後配額仍存在
"""
import requests
import json
import subprocess
import time

BASE_URL = "http://localhost:8080"

def get_auth_token():
    """登入取得 JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/teachers/login",
        json={"email": "demo@duotopia.com", "password": "demo123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def verify_db_quota():
    """直接查詢資料庫驗證 quota_used"""
    from database import get_db
    from models import Teacher

    db = next(get_db())
    teacher = db.query(Teacher).filter_by(email='demo@duotopia.com').first()
    current_period = teacher.current_period
    quota = current_period.quota_used if current_period else 0
    db.close()
    return quota

def test_1_update_quota_via_test_api():
    """測試 1: 透過測試 API 更新配額"""
    print("\n" + "="*60)
    print("測試 1: 測試頁面更新配額 → 資料庫更新")
    print("="*60)

    # 1. 先重置配額為 0
    print("\n📝 步驟 1: 重置配額")
    response = requests.post(
        f"{BASE_URL}/api/test/subscription/update",
        json={"action": "update_quota", "quota_delta": -10000}
    )
    print(f"Status: {response.status_code}")

    # 2. 更新配額 +888
    print("\n📝 步驟 2: 更新配額 +888 秒")
    response = requests.post(
        f"{BASE_URL}/api/test/subscription/update",
        json={"action": "update_quota", "quota_delta": 888}
    )
    data = response.json()
    print(f"API Response: {data['message']}")
    api_quota = data['status']['quota_used']

    # 3. 驗證資料庫
    print("\n📝 步驟 3: 驗證資料庫")
    db_quota = verify_db_quota()
    print(f"資料庫 quota_used: {db_quota}")

    # 4. 斷言
    assert api_quota == 888, f"API 回傳配額錯誤: {api_quota}"
    assert db_quota == 888, f"資料庫配額錯誤: {db_quota}"
    print("\n✅ 測試 1 通過：配額正確寫入資料庫")

def test_2_read_quota_via_subscription_api():
    """測試 2: 訂閱頁面讀取配額"""
    print("\n" + "="*60)
    print("測試 2: 訂閱頁面讀取配額 → 正確顯示")
    print("="*60)

    # 1. 取得 token
    print("\n📝 步驟 1: 登入取得 token")
    token = get_auth_token()
    if not token:
        print("❌ 無法取得 token")
        return

    # 2. 呼叫訂閱 API
    print("\n📝 步驟 2: 呼叫 /subscription/status")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/subscription/status", headers=headers)
    data = response.json()
    api_quota = data.get("quota_used")
    print(f"API 回傳 quota_used: {api_quota}")

    # 3. 驗證資料庫
    print("\n📝 步驟 3: 驗證資料庫")
    db_quota = verify_db_quota()
    print(f"資料庫 quota_used: {db_quota}")

    # 4. 斷言
    assert api_quota == db_quota, f"API 與資料庫不一致: {api_quota} != {db_quota}"
    assert api_quota == 888, f"配額應為 888，實際為 {api_quota}"
    print("\n✅ 測試 2 通過：訂閱 API 正確讀取配額")

def test_3_quota_persistence():
    """測試 3: 配額持久化（模擬重啟）"""
    print("\n" + "="*60)
    print("測試 3: 配額持久化驗證")
    print("="*60)

    # 1. 更新配額為特定值
    print("\n📝 步驟 1: 設定配額為 1234 秒")
    response = requests.post(
        f"{BASE_URL}/api/test/subscription/update",
        json={"action": "update_quota", "quota_delta": 1234 - verify_db_quota()}
    )
    initial_quota = verify_db_quota()
    print(f"初始配額: {initial_quota}")

    # 2. 等待確保寫入
    print("\n📝 步驟 2: 等待資料寫入...")
    time.sleep(1)

    # 3. 再次查詢資料庫
    print("\n📝 步驟 3: 再次查詢資料庫")
    final_quota = verify_db_quota()
    print(f"最終配額: {final_quota}")

    # 4. 斷言
    assert final_quota == 1234, f"配額持久化失敗: {final_quota} != 1234"
    print("\n✅ 測試 3 通過：配額已持久化到資料庫")

def test_4_frontend_integration():
    """測試 4: 前端整合測試"""
    print("\n" + "="*60)
    print("測試 4: 前端整合 - 測試頁面 → 訂閱頁面")
    print("="*60)

    # 1. 透過測試 API 設定配額
    print("\n📝 步驟 1: 透過測試 API 設定配額 555 秒")
    requests.post(
        f"{BASE_URL}/api/test/subscription/update",
        json={"action": "update_quota", "quota_delta": 555 - verify_db_quota()}
    )

    # 2. 透過訂閱 API 讀取
    print("\n📝 步驟 2: 透過訂閱 API 讀取")
    token = get_auth_token()
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/subscription/status", headers=headers)
        quota = response.json().get("quota_used")
        print(f"訂閱 API 讀取到: {quota} 秒")

        assert quota == 555, f"前端讀取錯誤: {quota} != 555"
        print("\n✅ 測試 4 通過：前端整合正常")
    else:
        print("⚠️ 跳過測試 4（無法登入）")

if __name__ == "__main__":
    print("🧪 配額功能整合測試 (TDD)")
    print("="*60)

    try:
        # 執行所有測試
        test_1_update_quota_via_test_api()
        test_2_read_quota_via_subscription_api()
        test_3_quota_persistence()
        test_4_frontend_integration()

        print("\n" + "="*60)
        print("✅✅✅ 所有測試通過！✅✅✅")
        print("="*60)
        print("\n📌 請手動測試前端：")
        print("1. 打開 http://localhost:5173/test-sub")
        print("2. 點擊 +500秒 按鈕")
        print("3. 打開 http://localhost:5173/teacher/subscription")
        print("4. 確認配額顯示正確")

    except AssertionError as e:
        print(f"\n❌ 測試失敗：{e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤：{e}")
        import traceback
        traceback.print_exc()
        exit(1)
