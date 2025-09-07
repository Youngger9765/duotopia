#!/usr/bin/env python3
"""
測試 Email 綁定系統功能
"""

import asyncio
import aiohttp
from datetime import datetime

API_URL = "http://localhost:8000"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


async def test_email_binding():
    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("🧪 測試 Email 綁定系統")
        print("=" * 60)

        # 1. 教師登入
        print("\n1️⃣ 教師登入...")
        login_response = await session.post(
            f"{API_URL}/api/auth/teacher/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
        )

        if login_response.status != 200:
            print("❌ 登入失敗")
            error = await login_response.text()
            print(f"錯誤: {error}")
            return

        login_data = await login_response.json()
        teacher_token = login_data["access_token"]
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        print("✅ 教師登入成功")

        # 2. 取得班級列表
        print("\n2️⃣ 取得班級列表...")
        classrooms_response = await session.get(f"{API_URL}/api/teachers/classrooms", headers=teacher_headers)

        if classrooms_response.status != 200:
            print("❌ 取得班級失敗")
            return

        classrooms = await classrooms_response.json()
        print(f"✅ 找到 {len(classrooms)} 個班級")

        if len(classrooms) < 2:
            print("⚠️ 需要至少 2 個班級來測試，建立新班級...")

            # 建立第一個班級
            create_class1 = await session.post(
                f"{API_URL}/api/teachers/classrooms",
                headers=teacher_headers,
                json={
                    "name": "測試班級 A",
                    "description": "Email 綁定測試用",
                    "level": "A1",
                },
            )

            if create_class1.status != 200:
                print("❌ 建立班級 A 失敗")
                error = await create_class1.text()
                print(f"錯誤: {error}")
                return

            class1 = await create_class1.json()
            print(f"✅ 建立班級 A: {class1['name']}")

            # 建立第二個班級
            create_class2 = await session.post(
                f"{API_URL}/api/teachers/classrooms",
                headers=teacher_headers,
                json={
                    "name": "測試班級 B",
                    "description": "Email 綁定測試用",
                    "level": "A1",
                },
            )

            if create_class2.status != 200:
                print("❌ 建立班級 B 失敗")
                return

            class2 = await create_class2.json()
            print(f"✅ 建立班級 B: {class2['name']}")

            classrooms = [class1, class2]

        # 3. 在兩個班級建立同名學生（模擬同一個人）
        print("\n3️⃣ 在不同班級建立同名學生...")

        test_email = f"test_student_{int(datetime.now().timestamp())}@gmail.com"
        student_name = "測試學生"
        birthdate = "2010-01-01"
        password = "20100101"  # 生日作為密碼

        students = []

        for i, classroom in enumerate(classrooms[:2]):
            print(f"\n在 {classroom['name']} 建立學生...")

            create_student_response = await session.post(
                f"{API_URL}/api/teachers/students",
                headers=teacher_headers,
                json={
                    "name": student_name,
                    "email": (test_email if i == 0 else None),  # 第一個學生填 email，第二個不填
                    "birthdate": birthdate,
                    "classroom_id": classroom["id"],
                },
            )

            if create_student_response.status == 200:
                student = await create_student_response.json()
                students.append(student)
                print(f"✅ 建立學生成功")
                print(f"   ID: {student['id']}")
                print(f"   Email: {student.get('email', 'None')}")
                print(f"   班級: {classroom['name']}")
            else:
                print(f"❌ 建立學生失敗: {create_student_response.status}")
                error = await create_student_response.text()
                print(f"錯誤: {error}")

        if len(students) < 2:
            print("❌ 需要至少 2 個學生來測試")
            return

        # 4. 第一個學生登入
        print(f"\n4️⃣ 第一個學生登入...")

        # 注意：現在學生可能沒有 email，需要用其他方式登入
        # 這裡我們假設第一個學生有 email
        if students[0].get("email"):
            student1_login = await session.post(
                f"{API_URL}/api/students/validate",
                json={"email": students[0]["email"], "birthdate": password},
            )

            if student1_login.status == 200:
                student1_data = await student1_login.json()
                student1_token = student1_data["access_token"]
                student1_headers = {"Authorization": f"Bearer {student1_token}"}
                student1_id = student1_data["student"]["id"]
                print(f"✅ 學生 1 登入成功 (ID: {student1_id})")
            else:
                print("❌ 學生 1 登入失敗")
                error = await student1_login.text()
                print(f"錯誤: {error}")
                return
        else:
            print("⚠️ 學生 1 沒有 email，無法測試")
            return

        # 5. 請求 email 驗證
        print(f"\n5️⃣ 請求 email 驗證...")
        verify_request = await session.post(
            f"{API_URL}/api/students/{student1_id}/email/request-verification",
            headers=student1_headers,
            json={"email": test_email},
        )

        if verify_request.status == 200:
            verify_data = await verify_request.json()
            print("✅ 驗證信已發送（開發模式）")
            print(f"   Email: {verify_data['email']}")
        else:
            print("❌ 發送驗證信失敗")
            error = await verify_request.text()
            print(f"錯誤: {error}")

        # 6. 檢查 email 狀態
        print(f"\n6️⃣ 檢查 email 驗證狀態...")
        status_response = await session.get(
            f"{API_URL}/api/students/{student1_id}/email-status",
            headers=student1_headers,
        )

        if status_response.status == 200:
            status_data = await status_response.json()
            print("✅ Email 狀態:")
            print(f"   Email: {status_data.get('email')}")
            print(f"   已驗證: {status_data.get('email_verified')}")
            print(f"   驗證時間: {status_data.get('email_verified_at')}")
        else:
            print("❌ 取得狀態失敗")

        # 7. 為第二個學生設定相同的 email
        print(f"\n7️⃣ 更新第二個學生的 email（相同 email）...")
        update_student2 = await session.put(
            f"{API_URL}/api/teachers/students/{students[1]['id']}",
            headers=teacher_headers,
            json={"email": test_email},
        )

        if update_student2.status == 200:
            print(f"✅ 學生 2 email 已更新為: {test_email}")
        else:
            print("❌ 更新失敗")
            error = await update_student2.text()
            print(f"錯誤: {error}")

        # 8. 測試取得連結的帳號（需要先驗證 email）
        print(f"\n8️⃣ 取得連結的帳號...")
        linked_response = await session.get(
            f"{API_URL}/api/students/{student1_id}/linked-accounts",
            headers=student1_headers,
        )

        if linked_response.status == 200:
            linked_data = await linked_response.json()
            print(f"✅ 連結的帳號:")
            if linked_data.get("linked_accounts"):
                for account in linked_data["linked_accounts"]:
                    print(f"   - ID: {account['student_id']}, 姓名: {account['name']}")
                    if account.get("classroom"):
                        print(f"     班級: {account['classroom']['name']}")
            else:
                print(f"   {linked_data.get('message', '無連結帳號')}")
        else:
            print("❌ 取得連結帳號失敗")
            error = await linked_response.text()
            print(f"錯誤: {error}")

        # 8.5 模擬驗證 email (開發模式下取得 token)
        print(f"\n8.5️⃣ 模擬驗證 email...")
        # 在開發模式下，我們可以直接從資料庫取得 token
        # 實際生產環境會發送真實 email

        # 先取得 token (這裡模擬從資料庫或 email 取得)
        # 為了測試，我們先嘗試使用一個假 token 看錯誤訊息
        verify_response = await session.get(
            f"{API_URL}/api/students/verify-email/test-token-123",
        )

        if verify_response.status == 400:
            print("   ⚠️ 模擬 token 無效（預期行為）")

        # 真實情況下，token 會在 email 中或從資料庫取得
        # 這裡我們跳過驗證步驟，直接測試後續功能

        # 9. 測試解除綁定（老師端）
        print(f"\n9️⃣ 測試解除 email 綁定...")
        unbind_response = await session.delete(
            f"{API_URL}/api/students/{student1_id}/email-binding",
            headers=teacher_headers,
        )

        if unbind_response.status == 200:
            unbind_data = await unbind_response.json()
            print("✅ Email 綁定已解除")
            print(f"   舊 Email: {unbind_data.get('old_email')}")
            print(f"   解除者: {unbind_data.get('removed_by')}")
        else:
            print("❌ 解除綁定失敗")
            error = await unbind_response.text()
            print(f"錯誤: {error}")

        print("\n" + "=" * 60)
        print("測試完成！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_email_binding())
