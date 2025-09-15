#!/usr/bin/env python3
"""
真實 API 合約測試 - 專門抓出前後端參數不匹配的 bug
不用瀏覽器，直接測試 API 端點
"""
import requests
import json
import sys
import os
from typing import Dict, Any

# 測試配置
API_BASE = "http://localhost:8080"  # 本地後端
# API_BASE = "https://api.duotopia-staging.com"  # 線上環境


class APIContractTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None

    def login_and_get_token(self) -> bool:
        """登入取得真實 token"""
        print("🔐 正在登入取得真實 token...")

        # 這裡需要真實的測試帳號
        login_data = {
            "email": "teacher@duotopia.com",
            "password": os.getenv("TEST_PASSWORD", "test-password-placeholder"),
        }

        response = self.session.post(
            f"{API_BASE}/api/auth/teacher/login", json=login_data
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ 登入成功")
            return True
        else:
            print(f"❌ 登入失敗: {response.status_code} - {response.text}")
            return False

    def test_assignment_api_contracts(self, assignment_id: int = 28):
        """測試指派 API 的各種錯誤參數組合"""
        print(f"\n🧪 測試作業 {assignment_id} 的 API 合約...")

        # 測試案例：各種可能的錯誤參數
        test_cases = [
            {
                "name": "❌ 錯誤：使用 'students' 而非 'student_ids'",
                "payload": {"students": [1, 2, 3]},
                "should_fail": True,
            },
            {
                "name": "❌ 錯誤：傳字串 student_number 而非數字 ID",
                "payload": {"student_ids": ["S001", "S002", "S003"]},
                "should_fail": True,
            },
            {
                "name": "❌ 錯誤：混合字串和數字",
                "payload": {"student_ids": [1, "S002", 3]},
                "should_fail": True,
            },
            {
                "name": "✅ 正確：使用 'student_ids' 數字陣列",
                "payload": {"student_ids": [1, 2, 3]},
                "should_fail": False,
            },
            {
                "name": "❌ 錯誤：空的 student_ids",
                "payload": {"student_ids": []},
                "should_fail": True,  # 可能是業務邏輯錯誤
            },
            {"name": "❌ 錯誤：缺少必要參數", "payload": {}, "should_fail": True},
        ]

        results = []

        for case in test_cases:
            print(f"\n🔬 {case['name']}")
            print(f"📤 Payload: {json.dumps(case['payload'], ensure_ascii=False)}")

            # 發送真實 API 請求
            response = self.session.patch(
                f"{API_BASE}/api/teachers/assignments/{assignment_id}",
                json=case["payload"],
                headers={"Content-Type": "application/json"},
            )

            print(f"📥 Status: {response.status_code}")

            # 顯示回應內容
            try:
                response_data = response.json()
                print(
                    f"📄 Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}"
                )
            except Exception:
                print(f"📄 Response: {response.text}")

            # 判斷測試結果
            if case["should_fail"]:
                if response.status_code >= 400:
                    print("✅ 正確：API 正確拒絕了錯誤參數")
                    results.append(("PASS", case["name"]))
                else:
                    print("❌ BUG：API 接受了錯誤參數！")
                    results.append(("FAIL", case["name"]))
            else:
                if response.status_code == 200:
                    print("✅ 正確：API 接受了正確參數")
                    results.append(("PASS", case["name"]))
                else:
                    print("❌ BUG：API 拒絕了正確參數！")
                    results.append(("FAIL", case["name"]))

        return results

    def test_unassign_api_contracts(self, assignment_id: int = 28):
        """測試取消指派 API"""
        print("\n🧪 測試取消指派 API 合約...")

        test_cases = [
            {
                "name": "❌ 錯誤：傳字串 student_number",
                "payload": {"student_ids": ["S001", "S002"]},
                "should_fail": True,
            },
            {
                "name": "✅ 正確：傳數字 student_id",
                "payload": {"student_ids": [1, 2]},
                "should_fail": False,
            },
        ]

        results = []

        for case in test_cases:
            print(f"\n🔬 {case['name']}")

            response = self.session.post(
                f"{API_BASE}/api/teachers/assignments/{assignment_id}/unassign",
                json=case["payload"],
            )

            print(f"📥 Status: {response.status_code}")
            try:
                print(f"📄 Response: {response.json()}")
            except Exception:
                print(f"📄 Response: {response.text}")

            if case["should_fail"] and response.status_code >= 400:
                results.append(("PASS", case["name"]))
            elif not case["should_fail"] and response.status_code == 200:
                results.append(("PASS", case["name"]))
            else:
                results.append(("FAIL", case["name"]))

        return results

    def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始 API 合約測試")
        print("=" * 60)

        # 跳過登入，直接使用假 token 測試錯誤處理
        self.session.headers.update({"Authorization": "Bearer fake-token"})

        all_results = []

        # 測試指派 API
        try:
            results = self.test_assignment_api_contracts()
            all_results.extend(results)
        except Exception as e:
            print(f"❌ 指派 API 測試失敗: {e}")

        # 測試取消指派 API
        try:
            results = self.test_unassign_api_contracts()
            all_results.extend(results)
        except Exception as e:
            print(f"❌ 取消指派 API 測試失敗: {e}")

        # 總結報告
        print("\n" + "=" * 60)
        print("📊 測試結果總結")
        print("=" * 60)

        passed = [r for r in all_results if r[0] == "PASS"]
        failed = [r for r in all_results if r[0] == "FAIL"]

        print(f"✅ 通過: {len(passed)}")
        print(f"❌ 失敗: {len(failed)}")

        if failed:
            print("\n💥 發現的 API 合約 Bug:")
            for _, test_name in failed:
                print(f"  - {test_name}")

        return len(failed) == 0


def main():
    """主函數"""
    print("🔥 真實 API 合約測試 - 專抓前後端參數不匹配 Bug")

    tester = APIContractTester()

    try:
        success = tester.run_all_tests()

        if success:
            print("\n🎉 所有測試通過！API 合約正確")
            sys.exit(0)
        else:
            print("\n💥 發現 API 合約問題！")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 測試執行錯誤: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
