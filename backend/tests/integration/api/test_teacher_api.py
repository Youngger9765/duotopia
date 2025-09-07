#!/usr/bin/env python3
"""
API 測試 - 教師功能
"""
import requests
from typing import Dict, Any  # noqa: F401

# 測試環境配置
BASE_URL = "https://duotopia-staging-backend-qchnzlfpda-de.a.run.app"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


class TestTeacherAPI:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}

    def test_teacher_login(self) -> Dict[str, Any]:
        """測試教師登入"""
        print("\n🔐 測試教師登入...")

        response = requests.post(
            f"{self.base_url}/api/auth/teacher/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
        )

        assert response.status_code == 200, f"登入失敗: {response.status_code}"
        data = response.json()

        assert "access_token" in data, "沒有返回 token"
        assert data["user"]["email"] == TEACHER_EMAIL, "用戶資料不正確"

        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        print("✅ 登入成功")
        print(f"   用戶: {data['user']['name']}")
        print(f"   Token: {self.token[:20]}...")

        return data

    def test_get_dashboard(self) -> Dict[str, Any]:
        """測試取得 Dashboard"""
        print("\n📊 測試 Dashboard API...")

        response = requests.get(
            f"{self.base_url}/api/teachers/dashboard", headers=self.headers
        )

        assert response.status_code == 200, f"取得 Dashboard 失敗: {response.text}"
        data = response.json()

        print("✅ Dashboard 資料:")
        print(f"   班級數: {data.get('total_classrooms', 0)}")
        print(f"   學生數: {data.get('total_students', 0)}")

        return data

    def test_get_classrooms(self) -> list:
        """測試取得班級列表"""
        print("\n🏫 測試取得班級列表...")

        response = requests.get(
            f"{self.base_url}/api/teachers/classrooms", headers=self.headers
        )

        assert response.status_code == 200, f"取得班級失敗: {response.text}"
        classrooms = response.json()

        print(f"✅ 找到 {len(classrooms)} 個班級:")
        for classroom in classrooms:
            print(f"   - {classroom['name']} (ID: {classroom['id']})")
            print(f"     學生數: {classroom.get('student_count', 0)}")

        return classrooms

    def test_get_classroom_detail(self, classroom_id: int) -> Dict[str, Any]:
        """測試取得班級詳情"""
        print(f"\n📋 測試取得班級 {classroom_id} 詳情...")

        response = requests.get(
            f"{self.base_url}/api/teachers/classrooms/{classroom_id}",
            headers=self.headers,
        )

        assert response.status_code == 200, f"取得班級詳情失敗: {response.text}"
        classroom = response.json()

        print("✅ 班級詳情:")
        print(f"   名稱: {classroom['name']}")
        print(f"   描述: {classroom.get('description', 'N/A')}")
        print(f"   學生數: {len(classroom.get('students', []))}")
        print(f"   課程數: {len(classroom.get('programs', []))}")

        # 列出學生
        if classroom.get("students"):
            print("\n   👥 學生列表:")
            for student in classroom["students"]:
                print(
                    f"      - {student.get('name', 'Unknown')} (ID: {student.get('id')})"
                )

        # 列出課程
        if classroom.get("programs"):
            print("\n   📚 課程列表:")
            for program in classroom["programs"]:
                print(
                    f"      - {program.get('name', 'Unknown')} (ID: {program.get('id')})"
                )

        return classroom

    def test_create_student(self, classroom_id: int) -> Dict[str, Any]:
        """測試新增學生"""
        print(f"\n➕ 測試新增學生到班級 {classroom_id}...")

        student_data = {
            "name": "測試學生",
            "email": f"test_student_{classroom_id}@test.com",
            "birth_date": "2012-01-01",
        }

        response = requests.post(
            f"{self.base_url}/api/teachers/classrooms/{classroom_id}/students",
            headers=self.headers,
            json=student_data,
        )

        if response.status_code == 201:
            student = response.json()
            print("✅ 新增學生成功:")
            print(f"   ID: {student['id']}")
            print(f"   姓名: {student['name']}")
            return student
        else:
            print(f"⚠️ 新增學生失敗: {response.text}")
            return {}

    def run_all_tests(self):
        """執行所有測試"""
        print("=" * 50)
        print("🧪 開始 API 測試 - 教師功能")
        print("=" * 50)

        try:
            # 1. 登入
            self.test_teacher_login()

            # 2. Dashboard
            self.test_get_dashboard()

            # 3. 班級列表
            classrooms = self.test_get_classrooms()

            # 4. 班級詳情（測試第一個班級）
            if classrooms:
                self.test_get_classroom_detail(classrooms[0]["id"])

                # 5. 新增學生（選擇性）
                # self.test_create_student(classrooms[0]['id'])

            print("\n" + "=" * 50)
            print("✅ 所有 API 測試通過！")
            print("=" * 50)

        except AssertionError as e:
            print(f"\n❌ 測試失敗: {e}")
            return False
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}")
            return False

        return True


if __name__ == "__main__":
    tester = TestTeacherAPI()
    tester.run_all_tests()
