"""
測試 Billing API 端點

此腳本測試所有 Billing API 端點的基本功能。
在本地開發環境，BigQuery client 可能無法初始化，但 API 應該優雅地處理錯誤。

執行方式:
    python tests/test_billing_api.py

前置要求:
    - Backend 服務運行在 localhost:8000
    - Demo 老師帳號已設為 admin (is_admin=True)
"""

import requests
import json


BASE_URL = "http://localhost:8000"


def login_as_admin() -> str:
    """以 Admin 身份登入，取得 JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]


def test_health_check(token: str):
    """測試 Billing Health Check 端點"""
    print("\n📊 測試: GET /api/admin/billing/health")
    response = requests.get(
        f"{BASE_URL}/api/admin/billing/health",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

    # 驗證回應結構
    assert "status" in data, "Response should have 'status' field"
    assert (
        "bigquery_connected" in data
    ), "Response should have 'bigquery_connected' field"

    # 在本地環境，BigQuery client 可能無法初始化，這是預期的
    if data["status"] == "unhealthy":
        print("   ✅ 預期行為: 本地環境 BigQuery 未連線")
    elif data["status"] == "waiting_for_data":
        print("   ✅ BigQuery 已連線，等待資料匯出")
    elif data["status"] == "healthy":
        print("   ✅ BigQuery 已連線且資料可用")


def test_billing_summary(token: str):
    """測試 Billing Summary 端點"""
    print("\n📊 測試: GET /api/admin/billing/summary?days=30")
    response = requests.get(
        f"{BASE_URL}/api/admin/billing/summary?days=30",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

    # 驗證回應結構
    if "error" in data:
        assert (
            "data_available" in data
        ), "Error response should have 'data_available' field"
        assert (
            data["data_available"] is False
        ), "data_available should be False when error"
        print("   ✅ 預期行為: BigQuery 資料尚未可用")
    else:
        # 如果資料可用，驗證完整結構
        assert "total_cost" in data
        assert "period" in data
        assert "top_services" in data
        assert "daily_costs" in data
        assert "data_available" in data
        assert data["data_available"] is True
        print(f"   ✅ 資料已可用: 總費用 ${data['total_cost']}")


def test_service_breakdown(token: str):
    """測試 Service Breakdown 端點"""
    print("\n📊 測試: GET /api/admin/billing/service-breakdown?service=Cloud%20Run&days=7")
    response = requests.get(
        f"{BASE_URL}/api/admin/billing/service-breakdown?service=Cloud%20Run&days=7",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

    # 驗證回應結構
    if "error" in data:
        print("   ✅ 預期行為: BigQuery 資料尚未可用")
    else:
        assert "service" in data
        assert "total_cost" in data
        assert "data_available" in data
        print(f"   ✅ 資料已可用: {data['service']} 費用 ${data['total_cost']}")


def test_anomaly_check(token: str):
    """測試 Anomaly Check 端點"""
    print("\n📊 測試: GET /api/admin/billing/anomaly-check?threshold_percent=50&days=7")
    response = requests.get(
        f"{BASE_URL}/api/admin/billing/anomaly-check?threshold_percent=50&days=7",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

    # 驗證回應結構
    if "message" in data and data.get("data_available") is False:
        print("   ✅ 預期行為: 等待 BigQuery 資料")
    else:
        assert "has_anomaly" in data
        assert "current_period" in data
        assert "previous_period" in data
        if data["has_anomaly"]:
            assert "anomalies" in data
            print(f"   ⚠️  偵測到 {len(data['anomalies'])} 個費用異常")
        else:
            print("   ✅ 無費用異常")


def test_unauthorized_access():
    """測試未授權存取 (應該返回 401)"""
    print("\n🔒 測試: 未授權存取 (無 token)")
    response = requests.get(f"{BASE_URL}/api/admin/billing/health")
    print(f"   Status: {response.status_code}")
    assert response.status_code == 401, "Should return 401 Unauthorized"
    print("   ✅ 正確拒絕未授權請求")


def test_non_admin_access(token: str):
    """測試非 Admin 存取 (應該返回 403)

    注意: 此測試需要有一個非 admin 的測試帳號
    如果 demo@duotopia.com 被設為 admin，此測試會被跳過
    """
    print("\n🔒 測試: 非 Admin 存取 (已省略，需要非 admin 測試帳號)")
    # 此測試在實際專案中需要創建一個非 admin 的測試用戶


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Billing API 測試")
    print("=" * 60)

    try:
        # 1. 登入取得 admin token
        print("\n🔑 步驟 1: 登入取得 Admin Token")
        token = login_as_admin()
        print(f"   ✅ Token: {token[:50]}...")

        # 2. 測試所有端點
        test_health_check(token)
        test_billing_summary(token)
        test_service_breakdown(token)
        test_anomaly_check(token)

        # 3. 測試權限控制
        test_unauthorized_access()
        # test_non_admin_access(token)  # 需要非 admin 測試帳號

        print("\n" + "=" * 60)
        print("✅ 所有測試通過！")
        print("=" * 60)
        print("\n📝 注意事項:")
        print("   - 本地環境 BigQuery client 可能無法初始化 (預期行為)")
        print("   - BigQuery 資料需在啟用 Billing Export 後 24 小時才會出現")
        print("   - 部署到 Cloud Run 後，API 將自動使用服務帳號連線 BigQuery")
        print()

    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ 無法連線到 Backend (請確認服務運行在 localhost:8000)")
        exit(1)
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
