#!/usr/bin/env python3
"""
測試朗讀評測內容儲存功能
"""

import asyncio
import aiohttp
import json

API_URL = "http://localhost:8000"
TEST_EMAIL = "demo@duotopia.com"
TEST_PASSWORD = "demo123"


async def test_content_save():
    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("🧪 測試朗讀評測內容儲存")
        print("=" * 60)

        # 1. 登入
        print("\n1️⃣ 教師登入...")
        login_response = await session.post(
            f"{API_URL}/api/auth/teacher/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )

        if login_response.status != 200:
            print("❌ 登入失敗")
            error = await login_response.text()
            print(f"錯誤: {error}")
            return

        login_data = await login_response.json()
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登入成功")

        # 2. 獲取課程列表
        print("\n2️⃣ 獲取課程列表...")
        programs_response = await session.get(
            f"{API_URL}/api/teachers/programs", headers=headers
        )

        if programs_response.status != 200:
            print("❌ 獲取課程失敗")
            error = await programs_response.text()
            print(f"錯誤: {error}")
            return

        programs = await programs_response.json()
        print(f"✅ 找到 {len(programs)} 個課程")

        if not programs:
            print("⚠️ 沒有課程，無法測試")
            return

        # 3. 選擇第一個課程的第一個課堂
        program = programs[0]
        print(f"\n使用課程: {program['name']}")

        # 4. 獲取課堂列表
        lessons_response = await session.get(
            f"{API_URL}/api/teachers/programs/{program['id']}/lessons", headers=headers
        )

        if lessons_response.status != 200:
            print("❌ 獲取課堂失敗")
            return

        lessons = await lessons_response.json()
        if not lessons:
            print("⚠️ 沒有課堂，創建新課堂...")
            # 創建新課堂
            create_lesson_response = await session.post(
                f"{API_URL}/api/teachers/programs/{program['id']}/lessons",
                headers=headers,
                json={
                    "name": "測試課堂",
                    "description": "用於測試朗讀評測",
                    "order_index": 1,
                },
            )

            if create_lesson_response.status != 200:
                print("❌ 創建課堂失敗")
                return

            lesson = await create_lesson_response.json()
            print(f"✅ 創建課堂: {lesson['name']}")
        else:
            lesson = lessons[0]
            print(f"使用課堂: {lesson['name']}")

        # 5. 創建朗讀評測內容
        print("\n3️⃣ 創建朗讀評測內容...")
        content_data = {
            "title": "測試朗讀評測",
            "type": "reading_assessment",
            "items": [
                {"text": "apple", "translation": "蘋果", "audio_url": ""},
                {"text": "banana", "translation": "香蕉", "audio_url": ""},
            ],
            "order_index": 1,
            "target_wpm": 80,
            "target_accuracy": 0.85,
            "time_limit_seconds": 180,
            "is_public": False,
        }

        create_response = await session.post(
            f"{API_URL}/api/teachers/lessons/{lesson['id']}/contents",
            headers=headers,
            json=content_data,
        )

        if create_response.status == 200:
            content = await create_response.json()
            print("✅ 成功創建朗讀評測內容!")
            print(f"   ID: {content['id']}")
            print(f"   標題: {content['title']}")
            print(f"   項目數: {len(content['items'])}")
        else:
            print(f"❌ 創建失敗: {create_response.status}")
            error_text = await create_response.text()
            print(f"錯誤內容: {error_text}")

            # 嘗試解析錯誤
            try:
                error_json = json.loads(error_text)
                print("\n錯誤詳情:")
                print(json.dumps(error_json, indent=2, ensure_ascii=False))
            except:
                pass


if __name__ == "__main__":
    asyncio.run(test_content_save())
