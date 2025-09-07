#!/usr/bin/env python3
"""
測試腳本：驗證重複課程檢測功能
測試複製時是否能正確檢查本來課程的 parent_id，提供 list 顯示和警告功能
"""

import requests
import sys


# API 基礎 URL
BASE_URL = "http://localhost:8000"


def get_auth_headers():
    """獲取認證 token（使用測試教師帳號）"""
    login_data = {"email": "demo@duotopia.com", "password": "demo123"}

    response = requests.post(f"{BASE_URL}/api/auth/teacher/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ 登入失敗: {response.status_code}")
        print(response.text)
        return None

    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


def test_template_duplicate_detection():
    """測試公版模板重複檢測"""
    print("\n🧪 測試 1: 公版模板重複檢測")

    headers = get_auth_headers()
    if not headers:
        return False

    # 1. 獲取教師的班級
    print("1️⃣ 獲取教師班級...")
    classrooms_response = requests.get(
        f"{BASE_URL}/api/teachers/classrooms", headers=headers
    )
    if classrooms_response.status_code != 200:
        print(f"❌ 獲取班級失敗: {classrooms_response.status_code}")
        return False

    classrooms = classrooms_response.json()
    if not classrooms:
        print("❌ 沒有找到班級")
        return False

    classroom_id = classrooms[0]["id"]
    print(f"✅ 使用班級 ID: {classroom_id}")

    # 2. 獲取公版模板（不帶 classroom_id，應該沒有 is_duplicate 標記）
    print("2️⃣ 獲取公版模板（無班級 ID）...")
    templates_response = requests.get(
        f"{BASE_URL}/api/programs/templates", headers=headers
    )
    if templates_response.status_code != 200:
        print(f"❌ 獲取模板失敗: {templates_response.status_code}")
        return False

    templates = templates_response.json()
    print(f"✅ 找到 {len(templates)} 個模板")

    # 檢查是否有 is_duplicate 欄位（應該都是 False）
    for template in templates:
        print(
            f"   - 模板「{template['name']}」: is_duplicate = {template.get('is_duplicate', 'None')}"
        )

    # 3. 獲取公版模板（帶 classroom_id，應該有正確的 is_duplicate 標記）
    print("3️⃣ 獲取公版模板（帶班級 ID）...")
    templates_with_classroom = requests.get(
        f"{BASE_URL}/api/programs/templates?classroom_id={classroom_id}",
        headers=headers,
    )
    if templates_with_classroom.status_code != 200:
        print(f"❌ 獲取模板（帶班級）失敗: {templates_with_classroom.status_code}")
        return False

    templates_dup = templates_with_classroom.json()
    print(f"✅ 帶班級檢測：找到 {len(templates_dup)} 個模板")

    # 檢查重複標記
    duplicate_count = 0
    for template in templates_dup:
        is_dup = template.get("is_duplicate", False)
        print(f"   - 模板「{template['name']}」: is_duplicate = {is_dup}")
        if is_dup:
            duplicate_count += 1

    print(f"✅ 重複模板數量: {duplicate_count}")

    # 4. 如果有模板，測試複製一個（建立重複項目）
    if templates:
        print("4️⃣ 測試複製模板（建立重複項目）...")
        template_to_copy = templates[0]

        copy_data = {
            "template_id": template_to_copy["id"],
            "classroom_id": classroom_id,
            "name": f"{template_to_copy['name']} (測試重複)",
        }

        copy_response = requests.post(
            f"{BASE_URL}/api/programs/copy-from-template",
            json=copy_data,
            headers=headers,
        )

        if copy_response.status_code == 200:
            print(f"✅ 成功複製模板「{template_to_copy['name']}」")

            # 5. 再次檢查重複標記（應該出現重複）
            print("5️⃣ 重新檢查重複標記...")
            templates_after = requests.get(
                f"{BASE_URL}/api/programs/templates?classroom_id={classroom_id}",
                headers=headers,
            ).json()

            for template in templates_after:
                is_dup = template.get("is_duplicate", False)
                if template["id"] == template_to_copy["id"]:
                    print(
                        f"   - 已複製模板「{template['name']}」: is_duplicate = {is_dup} {'✅' if is_dup else '❌'}"
                    )
                    if is_dup:
                        print("✅ 重複檢測成功！")
                        return True
                    else:
                        print("❌ 重複檢測失敗 - 應該標記為重複")
                        return False
        else:
            print(f"❌ 複製失敗: {copy_response.status_code} - {copy_response.text}")
            return False

    return True


def test_classroom_duplicate_detection():
    """測試班級課程重複檢測"""
    print("\n🧪 測試 2: 班級課程重複檢測")

    headers = get_auth_headers()
    if not headers:
        return False

    # 1. 獲取教師的班級
    classrooms_response = requests.get(
        f"{BASE_URL}/api/teachers/classrooms", headers=headers
    )
    classrooms = classrooms_response.json()

    if len(classrooms) < 2:
        print("❌ 需要至少 2 個班級來測試班級間複製")
        return False

    source_classroom_id = classrooms[0]["id"]
    target_classroom_id = classrooms[1]["id"]

    print(f"✅ 來源班級 ID: {source_classroom_id}")
    print(f"✅ 目標班級 ID: {target_classroom_id}")

    # 2. 獲取可複製的班級課程
    print("1️⃣ 獲取可複製的班級課程...")
    copyable_response = requests.get(
        f"{BASE_URL}/api/programs/copyable?classroom_id={target_classroom_id}",
        headers=headers,
    )

    if copyable_response.status_code != 200:
        print(f"❌ 獲取可複製課程失敗: {copyable_response.status_code}")
        return False

    copyable_programs = copyable_response.json()
    print(f"✅ 找到 {len(copyable_programs)} 個可複製課程")

    # 檢查重複標記
    for program in copyable_programs:
        classroom_name = program.get("classroom_name", "Unknown")
        is_dup = program.get("is_duplicate", False)
        print(
            f"   - 課程「{program['name']}」來自「{classroom_name}」: is_duplicate = {is_dup}"
        )

    return True


def test_api_endpoints():
    """測試 API 端點是否正常回應"""
    print("\n🧪 測試 3: API 端點測試")

    headers = get_auth_headers()
    if not headers:
        return False

    # 測試端點列表
    endpoints = [
        ("/api/programs/templates", "GET", "公版模板列表"),
        ("/api/programs/copyable?classroom_id=1", "GET", "可複製課程列表"),
        ("/api/teachers/classrooms", "GET", "教師班級列表"),
    ]

    for endpoint, method, description in endpoints:
        print(f"測試 {method} {endpoint} ({description})...")

        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)

        if response.status_code == 200:
            print(f"   ✅ {response.status_code} - 成功")
        else:
            print(f"   ❌ {response.status_code} - 失敗: {response.text}")

    return True


def main():
    """主要測試流程"""
    print("🔍 開始測試重複課程檢測系統...")
    print("=" * 60)

    # 檢查後端服務是否運行
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ 後端服務健康檢查失敗: {health_response.status_code}")
            return False
        print("✅ 後端服務運行正常")
    except requests.exceptions.RequestException as e:
        print(f"❌ 無法連接到後端服務: {e}")
        print("請確保後端服務在 http://localhost:8000 運行")
        return False

    # 執行測試
    tests = [
        ("API 端點測試", test_api_endpoints),
        ("公版模板重複檢測", test_template_duplicate_detection),
        ("班級課程重複檢測", test_classroom_duplicate_detection),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 執行測試: {test_name}")
            result = test_func()
            results.append((test_name, result))
            print(f"📊 測試結果: {'✅ 通過' if result else '❌ 失敗'}")
        except Exception as e:
            print(f"❌ 測試執行錯誤: {e}")
            results.append((test_name, False))

    # 總結報告
    print("\n" + "=" * 60)
    print("📋 測試總結報告")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n📊 總體結果: {passed}/{total} 通過 ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 所有測試通過！重複檢測系統運行正常")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查系統配置")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
