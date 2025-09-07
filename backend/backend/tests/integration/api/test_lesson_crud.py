#!/usr/bin/env python3
"""
測試 Lesson CRUD 功能
"""
import requests
import json  # noqa: F401

BASE_URL = "http://localhost:8000/api"


def test_lesson_crud():
    print("🔍 測試 Lesson CRUD 功能...\n")

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

    # 2. 取得第一個 Program 的 Lessons
    print("\n2. 取得 Program 的 Lessons...")
    response = requests.get(f"{BASE_URL}/teachers/programs", headers=headers)
    programs = response.json()

    if not programs:
        print("❌ 沒有 Programs")
        return

    # 找一個活躍的 program
    active_program = next((p for p in programs if p.get("is_active", True)), None)
    if not active_program:
        print("❌ 沒有活躍的 Program")
        return

    program_id = active_program["id"]
    print(f"✅ 使用 Program: {active_program['name']} (ID: {program_id})")

    # 取得 lessons
    response = requests.get(f"{BASE_URL}/teachers/programs/{program_id}/lessons", headers=headers)
    lessons = response.json()

    if lessons:
        lesson = lessons[0]
        lesson_id = lesson["id"]
        print(f"✅ 找到 {len(lessons)} 個 Lessons")

        # 3. 更新 Lesson
        print(f"\n3. 更新 Lesson ID {lesson_id}...")
        update_data = {
            "name": lesson["name"] + " (已更新)",
            "description": "這是更新後的描述",
            "order_index": lesson.get("order_index", 0),
            "estimated_minutes": 45,
        }

        response = requests.put(
            f"{BASE_URL}/teachers/lessons/{lesson_id}",
            json=update_data,
            headers=headers,
        )

        if response.status_code == 200:
            updated = response.json()
            print(f"✅ 更新成功: {updated['name']}")
        else:
            print(f"❌ 更新失敗: {response.text}")

    # 4. 建立新 Lesson
    print("\n4. 建立新 Lesson...")
    new_lesson_data = {
        "name": "測試單元",
        "description": "這是測試建立的單元",
        "order_index": 99,
        "estimated_minutes": 30,
    }

    response = requests.post(
        f"{BASE_URL}/teachers/programs/{program_id}/lessons",
        json=new_lesson_data,
        headers=headers,
    )

    if response.status_code == 200:
        new_lesson = response.json()
        new_lesson_id = new_lesson["id"]
        print(f"✅ 建立成功: {new_lesson['name']} (ID: {new_lesson_id})")

        # 5. 刪除新建的 Lesson（應該成功，因為沒有內容）
        print("\n5. 刪除空的 Lesson...")
        response = requests.delete(f"{BASE_URL}/teachers/lessons/{new_lesson_id}", headers=headers)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            if "details" in result:
                print(f"   原因: {result['details']['reason']}")
        else:
            print(f"❌ 刪除失敗: {response.text}")
    else:
        print(f"❌ 建立失敗: {response.text}")

    # 6. 測試刪除有內容的 Lesson
    print("\n6. 測試刪除有內容的 Lesson...")
    # 先找一個有內容的 lesson
    for lesson in lessons:
        response = requests.get(f"{BASE_URL}/teachers/lessons/{lesson['id']}/contents", headers=headers)
        contents = response.json()

        if contents:
            print(f"嘗試刪除 '{lesson['name']}' (有 {len(contents)} 個內容)")
            response = requests.delete(f"{BASE_URL}/teachers/lessons/{lesson['id']}", headers=headers)

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
                if "details" in result:
                    print(f"   刪除了 {result['details'].get('deleted_contents', 0)} 個內容")
            elif response.status_code == 400:
                error = response.json()
                print(f"⚠️ 無法刪除: {error['detail']['message']}")
                print(f"   內容數: {error['detail']['content_count']}")
                print(f"   作業數: {error['detail']['assignment_count']}")
            else:
                print(f"❌ 刪除失敗: {response.text}")
            break

    print("\n🎉 Lesson CRUD 測試完成！")


if __name__ == "__main__":
    test_lesson_crud()
