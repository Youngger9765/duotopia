#!/usr/bin/env python3
"""測試課程 CRUD 功能"""

import requests
import json
import time

# 登入取得 token
login_response = requests.post(
    "http://localhost:8000/api/auth/teacher/login",
    json={"email": "demo@duotopia.com", "password": "demo123"},
)

if login_response.status_code != 200:
    print(f"登入失敗: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== 測試課程 CRUD 功能 ===\n")

# 1. 創建新課程
print("1. 測試創建新課程...")
create_response = requests.post(
    "http://localhost:8000/api/teachers/programs",
    headers=headers,
    json={
        "name": "測試課程 - " + str(int(time.time())),
        "description": "這是測試用的課程描述",
        "level": "B1",
        "classroom_id": 1,  # 五年級A班
        "estimated_hours": 15,
    },
)

if create_response.status_code == 200:
    new_program = create_response.json()
    print(f"✅ 成功創建課程: ID={new_program['id']}, 名稱={new_program['name']}")
    program_id = new_program["id"]
else:
    print(f"❌ 創建失敗: {create_response.status_code}")
    print(create_response.json())
    exit(1)

# 2. 更新課程
print("\n2. 測試更新課程...")
update_response = requests.put(
    f"http://localhost:8000/api/teachers/programs/{program_id}",
    headers=headers,
    json={
        "name": "更新後的測試課程",
        "description": "更新後的描述",
        "level": "B2",
        "estimated_hours": 20,
    },
)

if update_response.status_code == 200:
    updated_program = update_response.json()
    print(f"✅ 成功更新課程: {updated_program['name']}")
else:
    print(f"❌ 更新失敗: {update_response.status_code}")

# 3. 取得課程詳情
print("\n3. 測試取得課程詳情...")
detail_response = requests.get(
    f"http://localhost:8000/api/teachers/programs/{program_id}", headers=headers
)

if detail_response.status_code == 200:
    detail = detail_response.json()
    print("✅ 成功取得課程詳情:")
    print(f"   名稱: {detail['name']}")
    print(f"   描述: {detail['description']}")
    print(f"   程度: {detail['level']}")
    print(f"   時數: {detail['estimated_hours']}")
    print(f"   單元數: {len(detail.get('lessons', []))}")
else:
    print(f"❌ 取得失敗: {detail_response.status_code}")

# 4. 刪除課程
print("\n4. 測試刪除課程...")
delete_response = requests.delete(
    f"http://localhost:8000/api/teachers/programs/{program_id}", headers=headers
)

if delete_response.status_code == 200:
    print(f"✅ 成功刪除課程 ID={program_id}")
else:
    print(f"❌ 刪除失敗: {delete_response.status_code}")

# 5. 驗證刪除
print("\n5. 驗證課程已刪除...")
verify_response = requests.get(
    f"http://localhost:8000/api/teachers/programs/{program_id}", headers=headers
)

if verify_response.status_code == 404:
    print("✅ 確認課程已被刪除")
else:
    print(f"❌ 課程仍然存在: {verify_response.status_code}")

print("\n=== 測試完成 ===")
