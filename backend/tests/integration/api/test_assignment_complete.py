#!/usr/bin/env python3
"""
完整測試作業系統功能
包含教師端和學生端的所有操作
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """打印分段標題"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print("=" * 60)


def print_success(message: str):
    """打印成功訊息"""
    print(f"✅ {message}")


def print_error(message: str):
    """打印錯誤訊息"""
    print(f"❌ {message}")


def print_info(message: str):
    """打印資訊"""
    print(f"ℹ️  {message}")


class TestAssignmentSystem:
    def __init__(self):
        self.teacher_token = None
        self.student_token = None
        self.teacher_id = None
        self.classroom_id = 1  # 使用五年級A班
        self.created_assignment_id = None

    def test_teacher_login(self) -> bool:
        """測試教師登入"""
        print_section("測試教師登入")

        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/teacher/login",
                json={"email": "demo@duotopia.com", "password": "demo123"},
            )

            if response.status_code == 200:
                data = response.json()
                self.teacher_token = data["access_token"]
                self.teacher_id = data["user"]["id"]
                print_success(f"教師登入成功: {data['user']['name']}")
                print_info(f"Teacher ID: {self.teacher_id}")
                return True
            else:
                print_error(f"教師登入失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"教師登入異常: {str(e)}")
            return False

    def test_get_assignments(self) -> bool:
        """測試查詢作業列表"""
        print_section("測試查詢作業列表")

        headers = {"Authorization": f"Bearer {self.teacher_token}"}

        try:
            # 查詢特定班級的作業
            response = requests.get(
                f"{BASE_URL}/api/assignments?classroom_id={self.classroom_id}",
                headers=headers,
            )

            if response.status_code == 200:
                assignments = response.json()
                print_success(f"成功取得作業列表，共 {len(assignments)} 個作業")

                # 顯示每個作業的詳細資訊
                for idx, assignment in enumerate(assignments, 1):
                    print(f"\n  作業 {idx}: {assignment['title']}")
                    print(f"    - ID: {assignment['id']}")
                    print(f"    - 內容數: {len(assignment.get('contents', []))}")
                    print(
                        f"    - 學生數: {len(assignment.get('student_assignments', []))}"
                    )

                    # 顯示學生狀態分布
                    if "student_assignments" in assignment:
                        status_count = {}
                        for sa in assignment["student_assignments"]:
                            status = sa.get("status", "UNKNOWN")
                            status_count[status] = status_count.get(status, 0) + 1

                        if status_count:
                            print(f"    - 狀態分布: {status_count}")

                return True
            else:
                print_error(f"查詢作業失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"查詢作業異常: {str(e)}")
            return False

    def test_create_assignment(self) -> bool:
        """測試建立作業"""
        print_section("測試建立新作業")

        headers = {"Authorization": f"Bearer {self.teacher_token}"}

        # 準備新作業資料
        new_assignment = {
            "title": "API測試作業 - " + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "description": "這是透過API測試建立的作業",
            "classroom_id": self.classroom_id,
            "content_ids": [1, 2],  # 使用前兩個內容
            "student_ids": [1, 2],  # 指派給王小明和李小美
            "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/assignments/create",
                headers=headers,
                json=new_assignment,
            )

            if response.status_code == 200:
                data = response.json()
                self.created_assignment_id = data["assignment_id"]
                print_success(f"成功建立作業 ID: {data['assignment_id']}")
                print_info(f"包含 {data.get('content_count', 0)} 個內容")
                print_info(f"指派給 {data.get('student_count', 0)} 位學生")
                print_info(f"訊息: {data.get('message', '')}")
                return True
            else:
                print_error(f"建立作業失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"建立作業異常: {str(e)}")
            return False

    def test_get_assignment_detail(self) -> bool:
        """測試查詢作業詳情"""
        print_section("測試查詢作業詳情")

        if not self.created_assignment_id:
            print_error("沒有可查詢的作業ID")
            return False

        headers = {"Authorization": f"Bearer {self.teacher_token}"}

        try:
            response = requests.get(
                f"{BASE_URL}/api/assignments/{self.created_assignment_id}",
                headers=headers,
            )

            if response.status_code == 200:
                assignment = response.json()
                print_success(f"成功取得作業詳情: {assignment['title']}")
                print_info(f"描述: {assignment.get('description', '無')}")
                print_info(f"到期日: {assignment.get('due_date', '無')}")

                # 顯示內容列表
                if "contents" in assignment:
                    print_info(f"包含內容:")
                    for content in assignment["contents"]:
                        # title 可能是字串或字典
                        title = content.get("title", "未命名")
                        if isinstance(title, dict):
                            title = title.get("zh_TW", "未命名")
                        print(f"    - {title}")

                # 顯示學生列表
                if "student_assignments" in assignment:
                    print_info(f"學生狀態:")
                    for sa in assignment["student_assignments"]:
                        student = sa.get("student", {})
                        print(
                            f"    - {student.get('name', '未知')}: {sa.get('status', 'UNKNOWN')}"
                        )

                return True
            else:
                print_error(f"查詢作業詳情失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"查詢作業詳情異常: {str(e)}")
            return False

    def test_update_assignment(self) -> bool:
        """測試編輯作業"""
        print_section("測試編輯作業")

        if not self.created_assignment_id:
            print_error("沒有可編輯的作業ID")
            return False

        headers = {"Authorization": f"Bearer {self.teacher_token}"}

        # 準備更新資料
        update_data = {
            "title": "API測試作業 - 已更新",
            "description": "這是更新後的描述",
            "classroom_id": self.classroom_id,  # 需要包含 classroom_id
            "content_ids": [1, 2, 3],  # 增加一個內容
            "student_ids": [1, 2, 3],  # 增加一位學生
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
        }

        try:
            response = requests.put(
                f"{BASE_URL}/api/assignments/{self.created_assignment_id}",
                headers=headers,
                json=update_data,
            )

            if response.status_code == 200:
                result = response.json()
                print_success(f"成功更新作業 ID: {self.created_assignment_id}")
                print_info(f"訊息: {result.get('message', '')}")
                print_info(f"更新標題為: {update_data['title']}")
                print_info(f"更新內容數為: {len(update_data['content_ids'])}")
                return True
            else:
                print_error(f"更新作業失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"更新作業異常: {str(e)}")
            return False

    def test_delete_assignment(self) -> bool:
        """測試刪除作業（軟刪除）"""
        print_section("測試刪除作業")

        if not self.created_assignment_id:
            print_error("沒有可刪除的作業ID")
            return False

        headers = {"Authorization": f"Bearer {self.teacher_token}"}

        try:
            response = requests.delete(
                f"{BASE_URL}/api/assignments/{self.created_assignment_id}",
                headers=headers,
            )

            if response.status_code == 200:
                print_success(f"成功刪除作業 ID: {self.created_assignment_id}")

                # 驗證軟刪除 - 作業應該從列表中消失
                response = requests.get(
                    f"{BASE_URL}/api/assignments?classroom_id={self.classroom_id}",
                    headers=headers,
                )

                if response.status_code == 200:
                    assignments = response.json()
                    deleted_found = any(
                        a["id"] == self.created_assignment_id for a in assignments
                    )

                    if not deleted_found:
                        print_success("確認作業已從列表中移除（軟刪除）")
                    else:
                        print_error("作業仍在列表中，軟刪除可能失敗")

                return True
            else:
                print_error(f"刪除作業失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"刪除作業異常: {str(e)}")
            return False

    def test_student_login(self) -> bool:
        """測試學生登入"""
        print_section("測試學生登入")

        try:
            # 使用學生 email 和密碼直接登入
            response = requests.post(
                f"{BASE_URL}/api/auth/student/login",
                json={
                    "email": "student1@duotopia.com",  # 王小明的 email
                    "password": "mynewpassword123",  # 王小明的密碼
                },
            )

            if response.status_code == 200:
                data = response.json()
                self.student_token = data["access_token"]
                print_success(f"學生登入成功: {data.get('user', {}).get('name', '未知')}")
                return True
            else:
                print_error(f"學生登入失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"學生登入異常: {str(e)}")
            return False

    def test_student_view_assignments(self) -> bool:
        """測試學生查看作業"""
        print_section("測試學生查看作業")

        if not self.student_token:
            print_error("沒有學生 token")
            return False

        headers = {"Authorization": f"Bearer {self.student_token}"}

        try:
            response = requests.get(
                f"{BASE_URL}/api/assignments/student", headers=headers
            )

            if response.status_code == 200:
                assignments = response.json()
                print_success(f"學生成功取得作業列表，共 {len(assignments)} 個作業")

                # 顯示每個作業的狀態
                for idx, assignment in enumerate(assignments, 1):
                    print(f"\n  作業 {idx}: {assignment['title']}")
                    print(f"    - 狀態: {assignment.get('status', 'UNKNOWN')}")
                    print(f"    - 到期日: {assignment.get('due_date', '無')}")

                    # 如果有進度資訊
                    if "progress" in assignment:
                        progress = assignment["progress"]
                        print(
                            f"    - 進度: {progress.get('completed', 0)}/{progress.get('total', 0)}"
                        )

                return True
            else:
                print_error(f"學生查看作業失敗: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print_error(f"學生查看作業異常: {str(e)}")
            return False

    def run_all_tests(self):
        """執行所有測試"""
        print("\n" + "=" * 60)
        print("🚀 開始執行作業系統完整測試")
        print("=" * 60)

        results = []

        # 教師端測試
        tests = [
            ("教師登入", self.test_teacher_login),
            ("查詢作業列表", self.test_get_assignments),
            ("建立新作業", self.test_create_assignment),
            ("查詢作業詳情", self.test_get_assignment_detail),
            ("編輯作業", self.test_update_assignment),
            ("刪除作業", self.test_delete_assignment),
            ("學生登入", self.test_student_login),
            ("學生查看作業", self.test_student_view_assignments),
        ]

        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print_error(f"{test_name} 發生異常: {str(e)}")
                results.append((test_name, False))

        # 測試總結
        print("\n" + "=" * 60)
        print("📊 測試結果總結")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"  {test_name}: {status}")

        print(f"\n總計: {passed}/{total} 測試通過")

        if passed == total:
            print("\n🎉 所有測試通過！作業系統運作正常")
        else:
            print(f"\n⚠️ 有 {total - passed} 個測試失敗，請檢查問題")

        return passed == total


if __name__ == "__main__":
    tester = TestAssignmentSystem()
    success = tester.run_all_tests()
    exit(0 if success else 1)
