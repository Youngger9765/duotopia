#!/usr/bin/env python3
"""
測試標籤儲存功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_tags_save():
    """測試標籤儲存是否正常"""

    # 1. 登入
    print("1. 登入...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if login_response.status_code != 200:
        print(f"❌ 登入失敗: {login_response.status_code}")
        print(login_response.text)
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登入成功")

    # 2. 取得班級
    print("\n2. 取得班級...")
    classrooms = requests.get(f"{BASE_URL}/api/teachers/classrooms", headers=headers).json()
    if not classrooms:
        print("❌ 沒有班級")
        return False

    classroom_id = classrooms[0]["id"]
    classroom_name = classrooms[0]["name"]
    print(f"✅ 使用班級: {classroom_name} (ID: {classroom_id})")

    # 3. 建立帶標籤的自建課程
    print("\n3. 建立帶標籤的自建課程...")
    program_data = {
        "name": "測試標籤課程",
        "description": "測試標籤儲存功能",
        "level": "B1",
        "estimated_hours": 30,
        "tags": ["口說", "聽力", "進階", "商務英語", "TOEIC"],
    }

    print(f"   送出資料：")
    print(f"   - 名稱: {program_data['name']}")
    print(f"   - 標籤: {program_data['tags']}")

    # 先檢查 API endpoint
    print(f"\n   測試 API endpoint: POST {BASE_URL}/api/programs/create-custom?classroom_id={classroom_id}")

    response = requests.post(
        f"{BASE_URL}/api/programs/create-custom?classroom_id={classroom_id}",
        json=program_data,
        headers=headers,
    )

    print(f"   回應狀態碼: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 成功建立課程！")
        print(f"   課程 ID: {result['id']}")
        print(f"   課程名稱: {result['name']}")

        # 檢查標籤是否正確儲存
        if "tags" in result:
            print(f"   儲存的標籤: {result['tags']}")
            if result["tags"] == program_data["tags"]:
                print("✅ 標籤正確儲存！")
                return True
            else:
                print(f"❌ 標籤不符！")
                print(f"   預期: {program_data['tags']}")
                print(f"   實際: {result['tags']}")
                return False
        else:
            print("❌ 回應中沒有 tags 欄位")
            print(f"   完整回應: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return False
    else:
        print(f"\n❌ 建立失敗: {response.status_code}")
        print(f"   錯誤訊息: {response.text[:500]}")

        # 嘗試分析錯誤
        try:
            error = response.json()
            if "detail" in error:
                print(f"   詳細錯誤: {error['detail']}")
        except BaseException:
            pass

        return False


def check_database_schema():
    """檢查資料庫 schema"""
    print("\n4. 檢查資料庫 schema...")

    try:
        import sys

        sys.path.append("/Users/young/project/duotopia/backend")

        from database import engine
        from sqlalchemy import inspect

        inspector = inspect(engine)
        columns = inspector.get_columns("programs")

        tags_column = next((c for c in columns if c["name"] == "tags"), None)

        if tags_column:
            print(f"✅ programs 表有 tags 欄位")
            print(f"   類型: {tags_column['type']}")
            print(f"   可為空: {tags_column['nullable']}")
        else:
            print("❌ programs 表沒有 tags 欄位")
            print("   需要執行 alembic migration")

    except Exception as e:
        print(f"❌ 無法檢查資料庫 schema: {e}")


if __name__ == "__main__":
    print("🔍 開始測試標籤儲存功能...")
    print("=" * 60)

    # 測試標籤儲存
    success = test_tags_save()

    # 檢查資料庫 schema
    check_database_schema()

    print("\n" + "=" * 60)

    if success:
        print("✅ 測試通過！標籤功能正常運作")
    else:
        print("❌ 測試失敗，請檢查以上錯誤訊息")
        print("\n可能的問題：")
        print("1. Program 模型沒有 tags 欄位")
        print("2. ProgramResponse schema 沒有包含 tags")
        print("3. 資料庫表沒有 tags 欄位（需要 migration）")
        print("4. API 路由沒有正確處理 tags")
