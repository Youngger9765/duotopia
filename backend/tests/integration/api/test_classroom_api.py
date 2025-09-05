#!/usr/bin/env python3
"""
API 測試 - 班級完整功能
包含：學生管理、課程管理、拖拽排序
"""
import requests
from typing import Dict, Any  # noqa: F401

# 測試環境配置
BASE_URL = "https://duotopia-staging-backend-qchnzlfpda-de.a.run.app"
# BASE_URL = "http://localhost:8000"  # 本地測試

# 教師帳號
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


class TestClassroomAPI:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
        self.test_student_id = None
        self.test_program_id = None

    def login(self):
        """教師登入"""
        response = requests.post(
            f"{self.base_url}/api/auth/teacher/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print("✅ 教師登入成功")
            return True
        print(f"❌ 登入失敗: {response.text}")
        return False

    def test_classroom_list(self):
        """測試班級列表（含學生）"""
        print("\n📚 測試班級列表...")

        response = requests.get(
            f"{self.base_url}/api/teachers/classrooms", headers=self.headers
        )

        if response.status_code == 200:
            classrooms = response.json()
            print(f"✅ 找到 {len(classrooms)} 個班級")

            # 檢查是否包含學生資料
            for classroom in classrooms:
                student_count = len(classroom.get("students", []))
                print(f"   - {classroom['name']}: {student_count} 位學生")

                # 驗證學生資料結構
                if classroom.get("students"):
                    student = classroom["students"][0]
                    assert "id" in student
                    assert "name" in student
                    assert "email" in student
                    print(f"     首位學生: {student['name']}")

            return True
        else:
            print(f"❌ 取得班級失敗: {response.text}")
            return False

    def test_student_management(self):
        """測試學生管理功能"""
        print("\n👥 測試學生管理...")

        # 1. 新增學生
        print("  1️⃣ 新增學生")
        response = requests.post(
            f"{self.base_url}/api/teachers/students",
            headers=self.headers,
            json={
                "name": "測試學生_API",
                "email": "api_test_student@duotopia.com",
                "birthdate": "2012-03-15",
                "classroom_id": 1,
            },
        )

        if response.status_code == 200:
            student = response.json()
            self.test_student_id = student["id"]
            print(f"    ✅ 新增成功 (ID: {self.test_student_id})")
            print(f"    預設密碼: {student.get('default_password', 'N/A')}")
        else:
            print(f"    ❌ 新增失敗: {response.text}")
            return False

        # 2. 編輯學生
        print("  2️⃣ 編輯學生")
        response = requests.put(
            f"{self.base_url}/api/teachers/students/{self.test_student_id}",
            headers=self.headers,
            json={"name": "測試學生_已更新"},
        )

        if response.status_code == 200:
            print("    ✅ 編輯成功")
        else:
            print(f"    ❌ 編輯失敗: {response.text}")
            return False

        # 3. 重設密碼
        print("  3️⃣ 重設密碼")
        response = requests.post(
            f"{self.base_url}/api/teachers/students/{self.test_student_id}/reset-password",
            headers=self.headers,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ 密碼已重設: {data.get('default_password', 'N/A')}")
        else:
            print(f"    ❌ 重設失敗: {response.text}")
            return False

        # 4. 刪除學生
        print("  4️⃣ 刪除學生")
        response = requests.delete(
            f"{self.base_url}/api/teachers/students/{self.test_student_id}",
            headers=self.headers,
        )

        if response.status_code == 200:
            print("    ✅ 刪除成功")
            self.test_student_id = None
            return True
        else:
            print(f"    ❌ 刪除失敗: {response.text}")
            return False

    def test_program_management(self):
        """測試課程管理功能"""
        print("\n📖 測試課程管理...")

        # 1. 新增課程
        print("  1️⃣ 新增課程")
        response = requests.post(
            f"{self.base_url}/api/teachers/programs",
            headers=self.headers,
            json={
                "name": "API測試課程",
                "description": "自動測試建立的課程",
                "level": "A1",
                "classroom_id": 1,
            },
        )

        if response.status_code == 200:
            program = response.json()
            self.test_program_id = program["id"]
            print(f"    ✅ 新增成功 (ID: {self.test_program_id})")
        else:
            print(f"    ❌ 新增失敗: {response.text}")
            return False

        # 2. 編輯課程
        print("  2️⃣ 編輯課程")
        response = requests.put(
            f"{self.base_url}/api/teachers/programs/{self.test_program_id}",
            headers=self.headers,
            json={"name": "API測試課程_已更新", "description": "描述已更新"},
        )

        if response.status_code == 200:
            print("    ✅ 編輯成功")
        else:
            print(f"    ❌ 編輯失敗: {response.text}")
            return False

        # 3. 取得課程詳情
        print("  3️⃣ 取得課程詳情")
        response = requests.get(
            f"{self.base_url}/api/teachers/programs/{self.test_program_id}",
            headers=self.headers,
        )

        if response.status_code == 200:
            program = response.json()
            print("    ✅ 取得成功")
            print(f"    單元數: {len(program.get('lessons', []))}")
        else:
            print(f"    ❌ 取得失敗: {response.text}")
            return False

        # 4. 刪除課程
        print("  4️⃣ 刪除課程")
        response = requests.delete(
            f"{self.base_url}/api/teachers/programs/{self.test_program_id}",
            headers=self.headers,
        )

        if response.status_code == 200:
            print("    ✅ 刪除成功")
            self.test_program_id = None
            return True
        else:
            print(f"    ❌ 刪除失敗: {response.text}")
            return False

    def test_drag_drop_reorder(self):
        """測試拖拽排序功能"""
        print("\n🔄 測試拖拽排序...")

        # 1. 課程排序
        print("  1️⃣ 課程排序")
        response = requests.put(
            f"{self.base_url}/api/teachers/programs/reorder",
            headers=self.headers,
            json=[{"id": 1, "order_index": 2}, {"id": 2, "order_index": 1}],
        )

        if response.status_code == 200:
            print("    ✅ 排序成功")

            # 恢復原始順序
            restore = requests.put(
                f"{self.base_url}/api/teachers/programs/reorder",
                headers=self.headers,
                json=[{"id": 1, "order_index": 1}, {"id": 2, "order_index": 2}],
            )
            if restore.status_code == 200:
                print("    ✅ 已恢復原始順序")
        else:
            print(f"    ❌ 排序失敗: {response.text}")
            return False

        # 2. 單元排序
        print("  2️⃣ 單元排序")
        response = requests.put(
            f"{self.base_url}/api/teachers/programs/1/lessons/reorder",
            headers=self.headers,
            json=[
                {"id": 1, "order_index": 2},
                {"id": 2, "order_index": 1},
                {"id": 3, "order_index": 3},
            ],
        )

        if response.status_code == 200:
            print("    ✅ 排序成功")

            # 恢復原始順序
            restore = requests.put(
                f"{self.base_url}/api/teachers/programs/1/lessons/reorder",
                headers=self.headers,
                json=[
                    {"id": 1, "order_index": 1},
                    {"id": 2, "order_index": 2},
                    {"id": 3, "order_index": 3},
                ],
            )
            if restore.status_code == 200:
                print("    ✅ 已恢復原始順序")
                return True
        else:
            print(f"    ❌ 排序失敗: {response.text}")
            return False

    def cleanup(self):
        """清理測試資料"""
        if self.test_student_id:
            requests.delete(
                f"{self.base_url}/api/teachers/students/{self.test_student_id}",
                headers=self.headers,
            )
            print("🧹 已清理測試學生")

        if self.test_program_id:
            requests.delete(
                f"{self.base_url}/api/teachers/programs/{self.test_program_id}",
                headers=self.headers,
            )
            print("🧹 已清理測試課程")

    def run_all_tests(self):
        """執行所有測試"""
        print("=" * 50)
        print("🧪 開始 API 測試 - 班級完整功能")
        print("=" * 50)

        if not self.login():
            return False

        results = {
            "班級列表": self.test_classroom_list(),
            "學生管理": self.test_student_management(),
            "課程管理": self.test_program_management(),
            "拖拽排序": self.test_drag_drop_reorder(),
        }

        # 清理測試資料
        self.cleanup()

        # 顯示結果
        print("\n" + "=" * 50)
        print("📊 測試結果總結")
        print("=" * 50)

        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}: {'通過' if result else '失敗'}")

        all_passed = all(results.values())
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 所有班級功能測試通過！")
        else:
            print("⚠️ 部分測試失敗，請檢查")
        print("=" * 50)

        return all_passed


if __name__ == "__main__":
    tester = TestClassroomAPI()
    tester.run_all_tests()
