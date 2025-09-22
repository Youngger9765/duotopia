"""
測試教師訂閱系統的本地測試腳本
用於測試 API 端點是否正常運作
"""
import requests
import json
from datetime import datetime

# API 基礎 URL
BASE_URL = "http://localhost:8080"


def test_teacher_registration():
    """測試教師註冊"""
    print("\n=== 測試教師註冊 ===")

    # 註冊新教師
    register_data = {
        "email": f"test_teacher_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "password123",
        "password_confirm": "password123",
        "name": "測試教師",
    }

    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/register", json=register_data
    )
    print(f"註冊狀態碼: {response.status_code}")

    if response.status_code == 200:
        print(f"註冊成功: {response.json()}")
        return register_data["email"], register_data["password"]
    else:
        print(f"註冊失敗: {response.text}")
        return None, None


def test_teacher_login(email, password):
    """測試教師登入"""
    print("\n=== 測試教師登入 ===")

    login_data = {"email": email, "password": password}

    response = requests.post(f"{BASE_URL}/api/auth/teacher/login", json=login_data)
    print(f"登入狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("登入成功，取得 token")
        return data.get("access_token")
    else:
        print(f"登入失敗: {response.text}")
        return None


def test_subscription_status(token):
    """測試獲取訂閱狀態"""
    print("\n=== 測試訂閱狀態 ===")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/subscription/status", headers=headers)
    print(f"狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"訂閱狀態: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    else:
        print(f"獲取失敗: {response.text}")
        return None


def test_subscription_recharge(token, months=1):
    """測試訂閱充值"""
    print(f"\n=== 測試充值 {months} 個月 ===")

    headers = {"Authorization": f"Bearer {token}"}

    recharge_data = {"months": months}

    response = requests.post(
        f"{BASE_URL}/api/subscription/recharge", json=recharge_data, headers=headers
    )
    print(f"充值狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"充值成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    else:
        print(f"充值失敗: {response.text}")
        return None


def test_mock_expire(token):
    """測試強制過期（測試用）"""
    print("\n=== 測試強制過期 ===")

    headers = {"Authorization": f"Bearer {token}"}

    expire_data = {"force_expire": True}

    response = requests.post(
        f"{BASE_URL}/api/subscription/mock-expire", json=expire_data, headers=headers
    )
    print(f"過期狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"過期成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    else:
        print(f"過期失敗: {response.text}")
        return None


def main():
    """執行所有測試"""
    print("開始測試教師訂閱系統...")

    # 1. 註冊教師
    email, password = test_teacher_registration()
    if not email:
        print("註冊失敗，終止測試")
        return

    # 2. 嘗試登入（應該失敗，因為未驗證 email）
    token = test_teacher_login(email, password)

    # 如果能登入（可能在測試模式下），繼續測試
    if token:
        # 3. 查看訂閱狀態
        test_subscription_status(token)

        # 4. 充值 3 個月
        test_subscription_recharge(token, 3)

        # 5. 再次查看狀態
        test_subscription_status(token)

        # 6. 測試強制過期
        test_mock_expire(token)

        # 7. 查看過期後的狀態
        test_subscription_status(token)

        print("\n=== 測試完成 ===")
    else:
        print("無法登入，可能是因為 email 未驗證（這是正常的）")
        print("在生產環境中，需要先通過 email 驗證才能登入")


if __name__ == "__main__":
    # 確保後端服務在運行
    try:
        response = requests.get(f"{BASE_URL}/docs")
        # 只要能連接就表示服務在運行
        print(f"後端服務狀態: 運行中 (狀態碼: {response.status_code})")
    except Exception:
        print("無法連接到後端服務，請確保後端運行在 http://localhost:8080")
        exit(1)

    main()
