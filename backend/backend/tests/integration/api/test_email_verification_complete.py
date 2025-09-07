#!/usr/bin/env python3
"""
測試完整的 Email 驗證流程
包含實際驗證 token 和連結帳號功能
"""

import asyncio
import aiohttp
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

API_URL = "http://localhost:8000"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"

# 資料庫連線（開發模式用）
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia"
)


def get_verification_token_from_db(student_id):
    """從資料庫取得驗證 token（開發模式用）"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute(
        "SELECT email_verification_token FROM students WHERE id = %s", (student_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result["email_verification_token"] if result else None


async def test_email_verification_complete():
    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("🧪 測試完整 Email 驗證流程")
        print("=" * 60)

        # 1. 教師登入
        print("\n1️⃣ 教師登入...")
        login_response = await session.post(
            f"{API_URL}/api/auth/teacher/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
        )

        if login_response.status != 200:
            print("❌ 登入失敗")
            return

        login_data = await login_response.json()
        teacher_token = login_data["access_token"]
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        print("✅ 教師登入成功")

        # 2. 取得班級
        print("\n2️⃣ 取得班級列表...")
        classrooms_response = await session.get(
            f"{API_URL}/api/teachers/classrooms", headers=teacher_headers
        )
        classrooms = await classrooms_response.json()

        if len(classrooms) < 2:
            print("❌ 需要至少 2 個班級")
            return

        print(f"✅ 找到 {len(classrooms)} 個班級")

        # 3. 建立兩個學生（模擬同一人在不同班級）
        print("\n3️⃣ 建立兩個學生...")

        test_email = f"verify_test_{int(datetime.now().timestamp())}@gmail.com"
        student_name = "驗證測試學生"
        birthdate = "2010-05-15"

        students_created = []

        for i, classroom in enumerate(classrooms[:2]):
            print(f"\n在 {classroom['name']} 建立學生...")

            # 第一個學生有 email，第二個沒有
            create_response = await session.post(
                f"{API_URL}/api/teachers/students",
                headers=teacher_headers,
                json={
                    "name": student_name,
                    "email": test_email if i == 0 else None,
                    "birthdate": birthdate,
                    "classroom_id": classroom["id"],
                },
            )

            if create_response.status == 200:
                student = await create_response.json()
                students_created.append(student)
                print(
                    f"✅ 建立成功 - ID: {student['id']}, Email: {student.get('email', 'None')}"
                )
            else:
                print("❌ 建立失敗")
                error = await create_response.text()
                print(f"錯誤: {error}")
                return

        student1, student2 = students_created

        # 4. 第一個學生登入
        print("\n4️⃣ 學生 1 登入...")
        student1_login = await session.post(
            f"{API_URL}/api/students/validate",
            json={"email": student1["email"], "birthdate": "20100515"},  # YYYYMMDD 格式
        )

        if student1_login.status != 200:
            print("❌ 學生登入失敗")
            error = await student1_login.text()
            print(f"錯誤: {error}")
            return

        student1_data = await student1_login.json()
        student1_token = student1_data["access_token"]
        student1_headers = {"Authorization": f"Bearer {student1_token}"}
        print("✅ 學生 1 登入成功")

        # 5. 請求 email 驗證
        print("\n5️⃣ 請求 email 驗證...")
        verify_request = await session.post(
            f"{API_URL}/api/students/{student1['id']}/email/request-verification",
            headers=student1_headers,
            json={"email": test_email},
        )

        if verify_request.status != 200:
            print("❌ 發送驗證信失敗")
            error = await verify_request.text()
            print(f"錯誤: {error}")
            return

        print("✅ 驗證信已發送")

        # 6. 從資料庫取得 token（開發模式）
        print("\n6️⃣ 取得驗證 token（開發模式）...")
        token = get_verification_token_from_db(student1["id"])

        if not token:
            print("❌ 無法取得 token")
            return

        print(f"✅ Token: {token[:20]}...")

        # 7. 驗證 email
        print("\n7️⃣ 驗證 email...")
        verify_response = await session.get(
            f"{API_URL}/api/students/verify-email/{token}"
        )

        if verify_response.status == 200:
            verify_data = await verify_response.json()
            print("✅ Email 驗證成功！")
            print(f"   學生: {verify_data['student_name']}")
            print(f"   Email: {verify_data['email']}")
        else:
            print("❌ Email 驗證失敗")
            error = await verify_response.text()
            print(f"錯誤: {error}")
            return

        # 8. 檢查驗證狀態
        print("\n8️⃣ 檢查 email 狀態...")
        status_response = await session.get(
            f"{API_URL}/api/students/{student1['id']}/email-status",
            headers=student1_headers,
        )

        if status_response.status == 200:
            status_data = await status_response.json()
            print("✅ Email 狀態:")
            print(f"   Email: {status_data.get('email')}")
            print(f"   已驗證: {status_data.get('email_verified')}")
            print(f"   驗證時間: {status_data.get('email_verified_at')}")

        # 9. 為第二個學生設定相同 email 並驗證
        print("\n9️⃣ 為學生 2 設定相同 email...")
        update_student2 = await session.put(
            f"{API_URL}/api/teachers/students/{student2['id']}",
            headers=teacher_headers,
            json={"email": test_email},
        )

        if update_student2.status == 200:
            print("✅ 學生 2 email 已更新")

            # 學生 2 登入
            print("\n登入學生 2...")
            student2_login = await session.post(
                f"{API_URL}/api/students/validate",
                json={"email": test_email, "birthdate": "20100515"},
            )

            if student2_login.status == 200:
                student2_data = await student2_login.json()
                student2_token = student2_data["access_token"]
                student2_headers = {"Authorization": f"Bearer {student2_token}"}
                print("✅ 學生 2 登入成功")

                # 學生 2 請求驗證
                verify2_request = await session.post(
                    f"{API_URL}/api/students/{student2['id']}/email/request-verification",
                    headers=student2_headers,
                    json={"email": test_email},
                )

                if verify2_request.status == 200:
                    print("✅ 學生 2 驗證信已發送")

                    # 取得並驗證 token
                    token2 = get_verification_token_from_db(student2["id"])
                    if token2:
                        verify2_response = await session.get(
                            f"{API_URL}/api/students/verify-email/{token2}"
                        )
                        if verify2_response.status == 200:
                            print("✅ 學生 2 email 驗證成功！")

        # 10. 取得連結的帳號
        print("\n🔟 取得連結的帳號...")
        linked_response = await session.get(
            f"{API_URL}/api/students/{student1['id']}/linked-accounts",
            headers=student1_headers,
        )

        if linked_response.status == 200:
            linked_data = await linked_response.json()
            print("✅ 連結的帳號:")

            if linked_data.get("linked_accounts"):
                for account in linked_data["linked_accounts"]:
                    print(f"   - ID: {account['student_id']}, 姓名: {account['name']}")
                    if account.get("classroom"):
                        print(f"     班級: {account['classroom']['name']}")
            else:
                print(f"   {linked_data.get('message', '無連結帳號')}")

        # 11. 測試帳號切換
        print("\n1️⃣1️⃣ 測試帳號切換...")
        switch_response = await session.post(
            f"{API_URL}/api/students/switch-account",
            headers=student1_headers,
            json={"target_student_id": student2["id"], "password": "20100515"},
        )

        if switch_response.status == 200:
            switch_data = await switch_response.json()
            print("✅ 帳號切換成功！")
            print(f"   現在登入為: {switch_data['student']['name']}")
            classroom = switch_data["student"].get("classroom")
            classroom_name = classroom["name"] if classroom else "None"
            print(f"   班級: {classroom_name}")
        else:
            print("❌ 帳號切換失敗")
            error = await switch_response.text()
            print(f"錯誤: {error}")

        # 12. 測試解除綁定
        print("\n1️⃣2️⃣ 測試解除 email 綁定...")
        unbind_response = await session.delete(
            f"{API_URL}/api/students/{student1['id']}/email-binding",
            headers=teacher_headers,
        )

        if unbind_response.status == 200:
            unbind_data = await unbind_response.json()
            print("✅ Email 綁定已解除")
            print(f"   舊 Email: {unbind_data.get('old_email')}")

        print("\n" + "=" * 60)
        print("✅ 完整測試成功！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_email_verification_complete())
