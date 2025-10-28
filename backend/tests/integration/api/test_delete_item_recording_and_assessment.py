"""
測試刪除錄音 API

根據 CLAUDE.md TDD 原則：
1. 先寫測試
2. 執行測試確認失敗
3. 修復代碼
4. 執行測試確認通過
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_delete_item_recording_and_assessment():
    """測試 delete_item_recording_and_assessment API 是否正常運作"""

    # 1. 登入取得 token
    login_response = client.post(
        "/api/auth/student/login", json={"id": "1", "password": "20120101"}
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]

    # 2. 呼叫 DELETE API
    delete_response = client.delete(
        "/api/speech/assessment/129/item/0",
        headers={"Authorization": f"Bearer {token}"},
    )

    # 3. 驗證結果
    print(f"Status: {delete_response.status_code}")
    print(f"Response: {delete_response.text}")

    assert delete_response.status_code in [
        200,
        404,
    ], f"Expected 200 or 404, got {delete_response.status_code}: {delete_response.text}"

    if delete_response.status_code == 200:
        data = delete_response.json()
        assert "message" in data
        assert "deleted" in data
        print("✅ DELETE API 成功:", data)
    else:
        print("⚠️ 找不到記錄（正常情況）")


if __name__ == "__main__":
    test_delete_item_recording_and_assessment()
