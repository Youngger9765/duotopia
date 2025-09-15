#!/usr/bin/env python3
"""
測試指派功能持久化 - 確保指派後重刷不會消失
遵循 CLAUDE.md TDD 原則
"""
import requests
import json
import time
import os
from typing import Dict, List

# 配置
BASE_URL = "https://api.duotopia-staging.com"
# BASE_URL = "http://localhost:8000"  # 本地測試時使用

# 測試用戶憑證 (從環境變數或安全配置取得)
TEST_EMAIL = "teacher@duotopia.com"
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "test-password-placeholder")


class AssignmentTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.assignment_id = None

    def login(self) -> bool:
        """登入取得 JWT token"""
        print("🔐 正在登入...")

        response = self.session.post(
            f"{BASE_URL}/api/auth/teacher/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.session.headers.update(
                {"Authorization": f"Bearer {self.access_token}"}
            )
            print(f"✅ 登入成功: {data.get('user', {}).get('name')}")
            return True
        else:
            print(f"❌ 登入失敗: {response.status_code} - {response.text}")
            return False

    def get_dashboard(self) -> Dict:
        """取得教師 dashboard"""
        print("📊 取得 dashboard...")

        response = self.session.get(f"{BASE_URL}/api/teachers/dashboard")

        if response.status_code == 200:
            data = response.json()
            print("✅ Dashboard 載入成功")

            # 取得第一個作業 ID 用於測試
            assignments = data.get("recent_assignments", [])
            if assignments:
                self.assignment_id = assignments[0]["id"]
                print(f"📝 使用作業 ID: {self.assignment_id}")

            return data
        else:
            print(f"❌ Dashboard 載入失敗: {response.status_code}")
            return {}

    def get_assignment_detail(self) -> Dict:
        """取得作業詳細資料"""
        if not self.assignment_id:
            print("❌ 沒有作業 ID")
            return {}

        print(f"📄 取得作業詳細資料 (ID: {self.assignment_id})...")

        response = self.session.get(
            f"{BASE_URL}/api/teachers/assignments/{self.assignment_id}"
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ 作業詳細資料載入成功")

            # 顯示目前指派狀態
            assigned_count = sum(
                1 for s in data.get("students", []) if s.get("is_assigned")
            )
            total_count = len(data.get("students", []))
            print(f"📊 目前指派狀態: {assigned_count}/{total_count} 學生")

            return data
        else:
            print(f"❌ 作業詳細資料載入失敗: {response.status_code}")
            return {}

    def test_assignment_operation(self) -> bool:
        """測試指派操作"""
        print("\n🎯 開始測試指派操作...")

        # 1. 取得當前狀態
        current_data = self.get_assignment_detail()
        if not current_data:
            return False

        students = current_data.get("students", [])
        if not students:
            print("❌ 沒有學生資料")
            return False

        # 2. 找出未指派的學生進行測試
        unassigned_students = [s for s in students if not s.get("is_assigned")]
        assigned_students = [s for s in students if s.get("is_assigned")]

        print("📊 測試前狀態:")
        print(f"   - 已指派: {len(assigned_students)} 人")
        print(f"   - 未指派: {len(unassigned_students)} 人")

        if not unassigned_students:
            print("⚠️  所有學生都已指派，跳過指派測試")
            return True

        # 3. 選擇一個學生進行指派測試
        test_student = unassigned_students[0]
        test_student_id = test_student["student_id"]
        test_student_name = test_student.get(
            "student_name", test_student.get("name", f"Student {test_student_id}")
        )

        print(f"🎯 選擇學生進行測試: {test_student_name} (ID: {test_student_id})")

        # 4. 執行指派操作
        current_assigned_ids = [s["student_id"] for s in assigned_students]
        new_assigned_ids = current_assigned_ids + [test_student_id]

        print("📤 執行指派 API...")
        response = self.session.patch(
            f"{BASE_URL}/api/teachers/assignments/{self.assignment_id}",
            json={"student_ids": new_assigned_ids},
        )

        if response.status_code != 200:
            print(f"❌ 指派 API 失敗: {response.status_code} - {response.text}")
            return False

        print("✅ 指派 API 成功返回")

        # 5. 等待一下讓資料庫處理
        time.sleep(1)

        # 6. 重新取得資料驗證持久化
        print("🔄 重新載入驗證持久化...")
        updated_data = self.get_assignment_detail()

        if not updated_data:
            print("❌ 無法重新載入資料")
            return False

        # 7. 檢查學生是否真的被指派
        updated_students = updated_data.get("students", [])
        updated_student = next(
            (s for s in updated_students if s["student_id"] == test_student_id), None
        )

        if not updated_student:
            print(f"❌ 找不到學生資料: {test_student_id}")
            return False

        is_now_assigned = updated_student.get("is_assigned", False)

        if is_now_assigned:
            print(f"✅ 指派持久化成功！學生 {test_student_name} 現在已被指派")

            # 顯示更新後的統計
            new_assigned_count = sum(
                1 for s in updated_students if s.get("is_assigned")
            )
            print(f"📊 更新後狀態: {new_assigned_count}/{len(updated_students)} 學生已指派")

            return True
        else:
            print(f"❌ 指派持久化失敗！學生 {test_student_name} 仍然未被指派")
            return False

    def run_full_test(self) -> bool:
        """執行完整測試"""
        print("🚀 開始指派功能測試")
        print("=" * 50)

        # 1. 登入
        if not self.login():
            return False

        # 2. 取得 dashboard
        if not self.get_dashboard():
            return False

        # 3. 測試指派操作
        if not self.test_assignment_operation():
            return False

        print("\n" + "=" * 50)
        print("✅ 所有測試通過！指派功能正常運作且能持久化")
        return True


def main():
    """主函數"""
    tester = AssignmentTester()

    try:
        success = tester.run_full_test()
        if success:
            print("\n🎉 測試結果: 成功")
            exit(0)
        else:
            print("\n💥 測試結果: 失敗")
            exit(1)
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
