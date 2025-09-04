#!/usr/bin/env python3
"""
測試拖拽排序 API
"""
import requests
import json

# 測試環境配置
BASE_URL = "https://duotopia-staging-backend-qchnzlfpda-de.a.run.app"
# BASE_URL = "http://localhost:8000"  # 本地測試

# 教師帳號
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


class TestReorderAPI:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None

    def login(self):
        """教師登入"""
        response = requests.post(
            f"{self.base_url}/api/auth/teacher/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ 登入成功")
            return True
        print(f"❌ 登入失敗: {response.text}")
        return False

    def test_program_reorder(self):
        """測試課程排序"""
        print("\n📝 測試課程排序...")

        # 注意：使用 order_index 而非 order
        response = requests.put(
            f"{self.base_url}/api/teachers/programs/reorder",
            headers={"Authorization": f"Bearer {self.token}"},
            json=[{"id": 1, "order_index": 2}, {"id": 2, "order_index": 1}],
        )

        if response.status_code == 200:
            print("✅ 課程排序成功")

            # 恢復原始順序
            restore = requests.put(
                f"{self.base_url}/api/teachers/programs/reorder",
                headers={"Authorization": f"Bearer {self.token}"},
                json=[{"id": 1, "order_index": 1}, {"id": 2, "order_index": 2}],
            )
            if restore.status_code == 200:
                print("✅ 已恢復原始順序")
            return True
        else:
            print(f"❌ 課程排序失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return False

    def test_lesson_reorder(self):
        """測試單元排序"""
        print("\n📝 測試單元排序...")

        # 注意：使用 order_index 而非 order
        response = requests.put(
            f"{self.base_url}/api/teachers/programs/1/lessons/reorder",
            headers={"Authorization": f"Bearer {self.token}"},
            json=[
                {"id": 1, "order_index": 2},
                {"id": 2, "order_index": 1},
                {"id": 3, "order_index": 3},
            ],
        )

        if response.status_code == 200:
            print("✅ 單元排序成功")

            # 恢復原始順序
            restore = requests.put(
                f"{self.base_url}/api/teachers/programs/1/lessons/reorder",
                headers={"Authorization": f"Bearer {self.token}"},
                json=[
                    {"id": 1, "order_index": 1},
                    {"id": 2, "order_index": 2},
                    {"id": 3, "order_index": 3},
                ],
            )
            if restore.status_code == 200:
                print("✅ 已恢復原始順序")
            return True
        else:
            print(f"❌ 單元排序失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return False

    def run_all_tests(self):
        """執行所有測試"""
        print("=" * 50)
        print("🧪 開始測試拖拽排序 API")
        print("=" * 50)

        if not self.login():
            return False

        success = True
        success = self.test_program_reorder() and success
        success = self.test_lesson_reorder() and success

        print("\n" + "=" * 50)
        if success:
            print("✅ 所有排序 API 測試通過！")
        else:
            print("❌ 部分測試失敗")
        print("=" * 50)

        return success


if __name__ == "__main__":
    tester = TestReorderAPI()
    tester.run_all_tests()
