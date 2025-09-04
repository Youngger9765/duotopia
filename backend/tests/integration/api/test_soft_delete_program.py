#!/usr/bin/env python3
"""
測試課程軟刪除功能
"""
import requests
import json  # noqa: F401

BASE_URL = "http://localhost:8000/api"


def test_soft_delete():
    print("🔍 測試課程軟刪除功能...\n")

    # 1. 教師登入
    print("1. 教師登入...")
    response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if response.status_code != 200:
        print(f"❌ 登入失敗: {response.text}")
        return

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登入成功")

    # 2. 取得課程列表
    print("\n2. 取得課程列表...")
    response = requests.get(f"{BASE_URL}/teachers/programs", headers=headers)

    if response.status_code != 200:
        print(f"❌ 取得課程失敗: {response.text}")
        return

    programs = response.json()
    if not programs:
        print("❌ 沒有課程")
        return

    program = programs[0]
    program_id = program["id"]
    print(f"✅ 找到課程: {program['name']} (ID: {program_id})")

    # 3. 刪除課程
    print(f"\n3. 刪除課程 ID {program_id}...")
    response = requests.delete(
        f"{BASE_URL}/teachers/programs/{program_id}", headers=headers
    )

    if response.status_code != 200:
        print(f"❌ 刪除失敗: {response.text}")
        return

    result = response.json()
    print(f"✅ {result['message']}")

    if "details" in result:
        details = result["details"]
        print("\n📊 刪除詳情:")
        print(f"  - 課程名稱: {details['program_name']}")
        print(f"  - 已停用: {details['deactivated']}")
        print("  - 相關資料:")
        print(f"    • Lessons: {details['related_data']['lessons']}")
        print(f"    • Contents: {details['related_data']['contents']}")
        print(f"    • Assignments: {details['related_data']['assignments']}")
        print(f"  - 備註: {details['note']}")

    # 4. 確認課程列表（不應顯示已停用的課程）
    print("\n4. 重新取得課程列表...")
    response = requests.get(f"{BASE_URL}/teachers/programs", headers=headers)

    if response.status_code == 200:
        new_programs = response.json()
        active_programs = [p for p in new_programs if p.get("is_active", True)]
        print(f"✅ 現有活躍課程數: {len(active_programs)}")

        # 檢查被刪除的課程是否還在列表中
        deleted_still_visible = any(p["id"] == program_id for p in new_programs)
        if deleted_still_visible:
            print("⚠️ 已停用的課程仍在列表中（需要前端過濾）")
        else:
            print("✅ 已停用的課程不在列表中")

    print("\n🎉 軟刪除測試完成！")


if __name__ == "__main__":
    test_soft_delete()
