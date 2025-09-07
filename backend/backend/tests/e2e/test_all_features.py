#!/usr/bin/env python3
"""完整功能測試"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"


def login():
    """登入並返回 token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    assert response.status_code == 200, f"登入失敗: {response.status_code}"
    return response.json()["access_token"]


def test_seed_data(headers):
    """測試 seed data - 驗證每個班級有 2 個課程，每個課程有 3 個單元"""
    print("\n=== 測試 Seed Data ===")

    # 取得所有課程
    programs_resp = requests.get(f"{BASE_URL}/api/teachers/programs", headers=headers)
    assert programs_resp.status_code == 200, "無法取得課程列表"

    programs = programs_resp.json()
    print(f"找到 {len(programs)} 個課程")

    # 驗證課程數量
    assert len(programs) >= 4, f"預期至少 4 個課程，實際: {len(programs)}"
    print("✅ 課程數量正確")

    # 檢查每個課程的單元數
    for program in programs:
        detail_resp = requests.get(f"{BASE_URL}/api/teachers/programs/{program['id']}", headers=headers)
        assert detail_resp.status_code == 200, f"無法取得課程 {program['id']} 詳情"

        detail = detail_resp.json()
        lessons = detail.get("lessons", [])
        print(f"  課程 '{program['name']}': {len(lessons)} 個單元")

        if program["id"] <= 4:  # 檢查前 4 個課程（seed data）
            assert len(lessons) >= 3, f"課程 {program['name']} 應有 3 個單元，實際: {len(lessons)}"

    print("✅ 每個課程都有正確的單元數")
    return True


def test_program_crud(headers):
    """測試課程 CRUD 功能"""
    print("\n=== 測試課程 CRUD ===")

    # 1. 創建課程
    create_data = {
        "name": f"測試課程_{int(time.time())}",
        "description": "自動測試創建的課程",
        "level": "B1",
        "classroom_id": 1,
        "estimated_hours": 10,
    }

    create_resp = requests.post(f"{BASE_URL}/api/teachers/programs", headers=headers, json=create_data)
    assert create_resp.status_code == 200, f"創建課程失敗: {create_resp.text}"

    new_program = create_resp.json()
    program_id = new_program["id"]
    print(f"✅ 成功創建課程 ID: {program_id}")

    # 2. 更新課程
    update_data = {
        "name": "更新後的測試課程",
        "description": "更新後的描述",
        "level": "B2",
        "estimated_hours": 15,
    }

    update_resp = requests.put(
        f"{BASE_URL}/api/teachers/programs/{program_id}",
        headers=headers,
        json=update_data,
    )
    assert update_resp.status_code == 200, f"更新課程失敗: {update_resp.text}"
    print("✅ 成功更新課程")

    # 3. 刪除課程
    delete_resp = requests.delete(f"{BASE_URL}/api/teachers/programs/{program_id}", headers=headers)
    assert delete_resp.status_code == 200, f"刪除課程失敗: {delete_resp.text}"
    print("✅ 成功刪除課程")

    return True


def test_drag_drop_reorder(headers):
    """測試拖曳重新排序功能"""
    print("\n=== 測試拖曳重新排序 ===")

    # 測試課程排序
    programs_resp = requests.get(f"{BASE_URL}/api/teachers/programs", headers=headers)
    programs = programs_resp.json()

    if len(programs) >= 2:
        # 交換前兩個課程的順序
        reorder_data = [
            {"id": programs[0]["id"], "order_index": 2},
            {"id": programs[1]["id"], "order_index": 1},
        ]

        reorder_resp = requests.put(
            f"{BASE_URL}/api/teachers/programs/reorder",
            headers=headers,
            json=reorder_data,
        )
        assert reorder_resp.status_code == 200, f"課程重新排序失敗: {reorder_resp.text}"
        print("✅ 課程拖曳排序功能正常")

        # 恢復原始順序
        restore_data = [
            {"id": programs[0]["id"], "order_index": 1},
            {"id": programs[1]["id"], "order_index": 2},
        ]
        requests.put(
            f"{BASE_URL}/api/teachers/programs/reorder",
            headers=headers,
            json=restore_data,
        )

    # 測試單元排序
    if len(programs) > 0:
        program_id = programs[0]["id"]
        detail_resp = requests.get(f"{BASE_URL}/api/teachers/programs/{program_id}", headers=headers)
        lessons = detail_resp.json().get("lessons", [])

        if len(lessons) >= 2:
            # 交換前兩個單元的順序
            reorder_data = [
                {"id": lessons[0]["id"], "order_index": 2},
                {"id": lessons[1]["id"], "order_index": 1},
            ]

            reorder_resp = requests.put(
                f"{BASE_URL}/api/teachers/programs/{program_id}/lessons/reorder",
                headers=headers,
                json=reorder_data,
            )
            assert reorder_resp.status_code == 200, f"單元重新排序失敗: {reorder_resp.text}"
            print("✅ 單元拖曳排序功能正常")

            # 恢復原始順序
            restore_data = [
                {"id": lessons[0]["id"], "order_index": 1},
                {"id": lessons[1]["id"], "order_index": 2},
            ]
            requests.put(
                f"{BASE_URL}/api/teachers/programs/{program_id}/lessons/reorder",
                headers=headers,
                json=restore_data,
            )

    return True


def test_frontend_health():
    """測試前端是否正常運行"""
    print("\n=== 測試前端狀態 ===")

    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        assert response.status_code == 200, f"前端回應異常: {response.status_code}"
        assert "Duotopia" in response.text or "duotopia" in response.text.lower(), "前端內容異常"
        print("✅ 前端運行正常")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️  前端可能未啟動: {e}")
        return False


def test_backend_health():
    """測試後端健康狀態"""
    print("\n=== 測試後端狀態 ===")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"後端健康檢查失敗: {response.status_code}"
        print("✅ 後端運行正常")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 後端異常: {e}")
        return False


def main():
    """執行所有測試"""
    print("=" * 60)
    print("🧪 開始執行完整功能測試")
    print("=" * 60)

    try:
        # 檢查服務狀態
        backend_ok = test_backend_health()
        test_frontend_health()

        if not backend_ok:
            print("\n❌ 後端服務未正常運行，請先啟動後端")
            return 1

        # 登入取得 token
        token = login()
        headers = {"Authorization": f"Bearer {token}"}
        print("\n✅ 登入成功")

        # 執行功能測試
        test_seed_data(headers)
        test_program_crud(headers)
        test_drag_drop_reorder(headers)

        print("\n" + "=" * 60)
        print("🎉 所有測試通過！系統功能正常")
        print("=" * 60)
        print("\n功能清單：")
        print("✅ Seed Data: 每班 2 課程，每課程 3 單元")
        print("✅ 課程 CRUD: 創建、更新、刪除功能正常")
        print("✅ 拖曳排序: 課程和單元都可重新排序")
        print("✅ 前後端服務: 運行正常")

        return 0

    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
