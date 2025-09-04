#!/usr/bin/env python3
"""
API 測試 - 學生功能
"""
import requests
import json  # noqa: F401
from typing import Dict, Any  # noqa: F401

# 測試環境配置
BASE_URL = "https://duotopia-staging-backend-qchnzlfpda-de.a.run.app"  # 正式環境
# BASE_URL = "http://localhost:8000"  # 本地測試

# 測試學生資料 (與 seed_data.py 一致)
STUDENTS = [
    {
        "name": "王小明",
        "email": "student1@duotopia.com",
        "password": "mynewpassword123",
        "classroom_id": 1,
    },
    {
        "name": "李小美",
        "email": "student2@duotopia.com",
        "password": "20120101",
        "classroom_id": 1,
    },
    {
        "name": "陳大雄",
        "email": "student3@duotopia.com",
        "password": "student456",
        "classroom_id": 1,
    },
    {
        "name": "張志豪",
        "email": "student4@duotopia.com",
        "password": "20120101",
        "classroom_id": 2,
    },
    {
        "name": "林靜香",
        "email": "student5@duotopia.com",
        "password": "password789",
        "classroom_id": 2,
    },
]


class TestStudentAPI:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}

    def test_student_login(
        self, student_name: str, email: str, password: str, classroom_id: int
    ) -> Dict[str, Any]:
        """測試學生登入"""
        print(f"\n🔐 測試學生登入: {student_name} ({email})...")

        # 直接使用單一登入 endpoint
        response = requests.post(
            f"{self.base_url}/api/auth/student/login",
            json={"email": email, "password": password},
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print("✅ 登入成功!")
            return data
        else:
            print(f"❌ 登入失敗: {response.text}")
            return {}

    def test_get_assignments(self) -> list:
        """測試取得作業列表"""
        print("\n📝 測試取得作業列表...")

        response = requests.get(
            f"{self.base_url}/api/students/assignments", headers=self.headers
        )

        if response.status_code == 200:
            assignments = response.json()
            print(f"✅ 找到 {len(assignments)} 個作業")
            # 只顯示前3個作業
            display_count = min(3, len(assignments))
            for i in range(display_count):
                assignment = assignments[i]
                print(f"   - {assignment.get('title', 'Unknown')}")
                print(f"     狀態: {assignment.get('status', 'N/A')}")
            return assignments
        else:
            print(f"⚠️ 取得作業失敗: {response.text}")
            return []

    def test_student_profile(self) -> Dict[str, Any]:
        """測試取得學生資料"""
        print("\n👤 測試取得學生資料...")

        response = requests.get(
            f"{self.base_url}/api/students/profile", headers=self.headers
        )

        if response.status_code == 200:
            profile = response.json()
            print("✅ 學生資料:")
            print(f"   姓名: {profile.get('name', 'N/A')}")
            print(f"   班級: {profile.get('classroom_name', 'N/A')}")
            return profile
        else:
            print(f"⚠️ 取得資料失敗: {response.text}")
            return {}

    def run_all_tests(self):
        """執行所有學生測試"""
        print("=" * 50)
        print("🧪 開始 API 測試 - 學生功能")
        print("=" * 50)

        success_count = 0
        fail_count = 0

        # 測試每個學生
        for student in STUDENTS[:2]:  # 只測試前2個學生以節省時間
            print(f"\n{'='*30}")
            print(f"測試學生: {student['name']}")
            print(f"{'='*30}")

            try:
                # 登入
                login_result = self.test_student_login(
                    student["name"],
                    student["email"],
                    student["password"],
                    student["classroom_id"],
                )

                if login_result:
                    # 測試其他 API
                    self.test_student_profile()
                    self.test_get_assignments()
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                print(f"❌ 測試失敗: {e}")
                fail_count += 1

        print("\n" + "=" * 50)
        print(f"測試結果: {success_count} 成功, {fail_count} 失敗")
        print("=" * 50)

        return fail_count == 0


if __name__ == "__main__":
    tester = TestStudentAPI()
    tester.run_all_tests()
