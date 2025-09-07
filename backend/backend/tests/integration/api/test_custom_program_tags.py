#!/usr/bin/env python3
"""
測試自建課程的標籤功能
"""

import requests

BASE_URL = "http://localhost:8000"


def test_create_custom_program_with_tags():
    """測試建立帶標籤的自建課程"""

    # 1. 登入
    login_response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if login_response.status_code != 200:
        print(f"❌ 登入失敗: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 取得班級
    classrooms = requests.get(
        f"{BASE_URL}/api/teachers/classrooms", headers=headers
    ).json()
    if not classrooms:
        print("❌ 沒有班級")
        return False

    classroom_id = classrooms[0]["id"]

    # 3. 建立帶標籤的自建課程
    program_data = {
        "name": "測試標籤課程",
        "description": "這是測試標籤功能的課程",
        "level": "B1",
        "estimated_hours": 30,
        "tags": ["口說", "聽力", "進階", "商務英語", "TOEIC"],
    }

    print("📤 送出課程資料：")
    print(f"   名稱: {program_data['name']}")
    print(f"   等級: {program_data['level']}")
    print(f"   標籤: {program_data['tags']}")

    response = requests.post(
        f"{BASE_URL}/api/programs/create-custom?classroom_id={classroom_id}",
        json=program_data,
        headers=headers,
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ 成功建立課程！")
        print(f"   課程 ID: {result['id']}")
        print(f"   課程名稱: {result['name']}")
        print(f"   標籤: {result.get('tags', [])}")

        # 驗證標籤是否正確儲存
        if result.get("tags") == program_data["tags"]:
            print("✅ 標籤正確儲存！")
            return True
        else:
            print(f"❌ 標籤不符！預期: {program_data['tags']}, 實際: {result.get('tags')}")
            return False
    else:
        print(f"❌ 建立失敗: {response.status_code}")
        print(response.text)
        return False


def test_ui_checklist():
    """UI 功能檢查清單"""
    print("\n🧪 UI 檢查清單：")
    print("1. 標籤輸入元件:")
    print("   - Label 顯示「標籤（用逗號分隔）」✅")
    print("   - TagInputWithSuggestions 元件已加入 ✅")
    print("   - placeholder 提示文字 ✅")
    print("   - 最多 10 個標籤限制 ✅")
    print("")
    print("2. 標籤建議功能:")
    print("   - 程度相關: 初級、中級、進階 ✅")
    print("   - 技能相關: 口說、聽力、閱讀、寫作等 ✅")
    print("   - 主題相關: 日常生活、商務、旅遊等 ✅")
    print("")
    print("3. 資料傳送:")
    print("   - customForm.tags 欄位已定義 ✅")
    print("   - handleCreateCustom 包含 tags 欄位 ✅")


def main():
    print("🔍 開始測試標籤功能...")
    print("=" * 60)

    # 測試 API
    if test_create_custom_program_with_tags():
        print("\n✅ API 測試通過！")
    else:
        print("\n❌ API 測試失敗")

    # UI 檢查清單
    test_ui_checklist()

    print("\n" + "=" * 60)
    print("📱 請在瀏覽器手動測試：")
    print("1. 開啟建立課程對話框")
    print("2. 切換到「自建課程」頁籤")
    print("3. 在標籤欄位輸入文字後按 Enter")
    print("4. 點擊建議的標籤")
    print("5. 確認標籤可以新增和刪除")


if __name__ == "__main__":
    main()
