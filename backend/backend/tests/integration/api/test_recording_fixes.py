#!/usr/bin/env python3
"""
測試錄音集活動的修復
"""

import requests
from datetime import datetime

API_URL = "http://localhost:8000"

# 教師登入資訊
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


def login_teacher():
    """教師登入"""
    response = requests.post(
        f"{API_URL}/api/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ 教師登入成功")
        return {"Authorization": f"Bearer {token}"}
    else:
        print(f"❌ 教師登入失敗: {response.text}")
        return None


def test_batch_translation(headers):
    """測試批次翻譯功能"""
    print("\n📝 測試批次翻譯...")

    # 測試批次翻譯 API
    test_texts = ["apple", "banana", "orange", "watermelon"]

    response = requests.post(
        f"{API_URL}/api/teachers/translate/batch",
        headers=headers,
        json={"texts": test_texts, "target_lang": "zh-TW"},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 批次翻譯成功")
        print(f"   原文: {data.get('originals', [])}")
        print(f"   翻譯: {data.get('translations', [])}")

        # 檢查是否有翻譯結果
        translations = data.get("translations", [])
        if translations and translations[0] != test_texts[0]:
            print("   ✅ 翻譯結果不同於原文（正確）")
            return True
        else:
            print("   ❌ 翻譯結果與原文相同（錯誤）")
            return False
    else:
        print(f"❌ 批次翻譯失敗: {response.text}")
        return False


def test_single_translation(headers):
    """測試單一翻譯功能"""
    print("\n🌍 測試單一翻譯...")

    # 測試中文翻譯
    response = requests.post(
        f"{API_URL}/api/teachers/translate",
        headers=headers,
        json={"text": "computer", "target_lang": "zh-TW"},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 中文翻譯成功: computer -> {data.get('translation')}")
    else:
        print(f"❌ 中文翻譯失敗: {response.text}")
        return False

    # 測試英文翻譯（英英釋義）
    response = requests.post(
        f"{API_URL}/api/teachers/translate",
        headers=headers,
        json={"text": "computer", "target_lang": "en"},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 英文釋義成功: computer -> {data.get('translation')}")
        return True
    else:
        print(f"❌ 英文釋義失敗: {response.text}")
        return False


def test_tts_generation(headers):
    """測試 TTS 生成"""
    print("\n🔊 測試 TTS 生成...")

    response = requests.post(
        f"{API_URL}/api/teachers/tts",
        headers=headers,
        json={
            "text": "Hello, this is a test",
            "voice": "en-US-JennyNeural",
            "rate": "+0%",
            "volume": "+0%",
        },
    )

    if response.status_code == 200:
        data = response.json()
        audio_url = data.get("audio_url")
        if audio_url:
            print(f"✅ TTS 生成成功: {audio_url}")
            return True
        else:
            print("❌ TTS 生成失敗：沒有返回音檔 URL")
            return False
    else:
        print(f"❌ TTS 生成失敗: {response.text}")
        return False


def test_content_creation(headers):
    """測試內容創建與保存"""
    print("\n💾 測試內容創建...")

    # 先獲取一個課程的 lesson
    response = requests.get(f"{API_URL}/api/teachers/programs", headers=headers)

    if response.status_code != 200 or not response.json():
        print("❌ 無法獲取課程列表")
        return False

    programs = response.json()
    if not programs:
        print("❌ 沒有可用的課程")
        return False

    program_id = programs[0]["id"]

    # 獲取 lessons
    response = requests.get(f"{API_URL}/api/teachers/programs/{program_id}/lessons", headers=headers)

    if response.status_code != 200:
        print("❌ 無法獲取課程單元")
        return False

    lessons = response.json()
    if not lessons:
        print("⚠️ 沒有課程單元，嘗試創建...")
        # 創建一個新的 lesson
        response = requests.post(
            f"{API_URL}/api/teachers/programs/{program_id}/lessons",
            headers=headers,
            json={
                "name": f"測試單元 {datetime.now().strftime('%H%M%S')}",
                "description": "用於測試錄音集活動",
            },
        )
        if response.status_code != 200:
            print("❌ 無法創建課程單元")
            return False
        lesson_id = response.json()["id"]
    else:
        lesson_id = lessons[0]["id"]

    # 創建朗讀評測內容
    content_data = {
        "type": "reading_assessment",
        "title": f"測試錄音集 {datetime.now().strftime('%H%M%S')}",
        "items": [
            {
                "text": "apple",
                "definition": "蘋果",
                "audio_url": "",
                "translation": "蘋果",
            },
            {
                "text": "banana",
                "definition": "香蕉",
                "audio_url": "",
                "translation": "香蕉",
            },
            {
                "text": "orange",
                "definition": "橘子",
                "audio_url": "",
                "translation": "橘子",
            },
        ],
        "target_wpm": 60,
        "target_accuracy": 90,
        "time_limit_seconds": 300,
    }

    response = requests.post(
        f"{API_URL}/api/teachers/lessons/{lesson_id}/contents",
        headers=headers,
        json=content_data,
    )

    if response.status_code == 200:
        created = response.json()
        print(f"✅ 內容創建成功")
        print(f"   ID: {created.get('id')}")
        print(f"   標題: {created.get('title')}")
        print(f"   項目數: {len(created.get('items', []))}")

        # 驗證項目不是空的
        items = created.get("items", [])
        if items and items[0].get("text"):
            print("   ✅ 項目資料正確保存")
            return True
        else:
            print("   ❌ 項目資料為空")
            return False
    else:
        print(f"❌ 內容創建失敗: {response.text}")
        return False


def main():
    print("🚀 開始測試錄音集活動修復...")
    print("=" * 50)

    # 登入
    headers = login_teacher()
    if not headers:
        print("無法繼續測試")
        return

    # 執行測試
    results = []

    # 測試批次翻譯
    results.append(("批次翻譯", test_batch_translation(headers)))

    # 測試單一翻譯（含語言選擇）
    results.append(("單一翻譯", test_single_translation(headers)))

    # 測試 TTS 生成
    results.append(("TTS 生成", test_tts_generation(headers)))

    # 測試內容創建（驗證 modal 保存）
    results.append(("內容創建", test_content_creation(headers)))

    # 總結
    print("\n" + "=" * 50)
    print("📊 測試結果總結：")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {name}: {status}")

    print(f"\n總計: {passed}/{total} 測試通過")

    if passed == total:
        print("🎉 所有測試通過！")
    else:
        print("⚠️ 部分測試失敗，請檢查")


if __name__ == "__main__":
    main()
