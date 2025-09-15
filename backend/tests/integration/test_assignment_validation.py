#!/usr/bin/env python3
"""
直接測試後端驗證邏輯 - 繞過認證，專注測試參數驗證
"""
import sys
import os

# 測試檔案在 backend/tests/integration/ 目錄下
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_assignment_request_validation():
    """測試 UpdateAssignmentRequest 的驗證邏輯"""
    print("🧪 測試後端參數驗證邏輯...")

    try:
        from pydantic import ValidationError
        from routers.assignments import UpdateAssignmentRequest

        # 測試案例
        test_cases = [
            {
                "name": "✅ 正確：student_ids 數字陣列",
                "data": {"student_ids": [1, 2, 3]},
                "should_pass": True,
            },
            {
                "name": "❌ 錯誤：student_ids 字串陣列",
                "data": {"student_ids": ["S001", "S002"]},
                "should_pass": False,
            },
            {
                "name": "❌ 錯誤：使用 students 而非 student_ids",
                "data": {"students": [1, 2, 3]},
                "should_pass": False,  # 這個會被忽略，不會報錯，但不會生效
            },
            {
                "name": "❌ 錯誤：混合類型",
                "data": {"student_ids": [1, "S002", 3]},
                "should_pass": False,
            },
        ]

        results = []

        for case in test_cases:
            print(f"\n🔬 {case['name']}")
            print(f"📤 Data: {case['data']}")

            try:
                # 嘗試創建 Pydantic 模型
                request = UpdateAssignmentRequest(**case["data"])
                print(f"✅ 驗證通過: {request}")

                # 檢查是否應該通過
                if case["should_pass"]:
                    results.append(("PASS", case["name"]))
                else:
                    print("❌ BUG: 後端接受了錯誤參數！")
                    results.append(("FAIL", case["name"]))

            except ValidationError as e:
                print(f"❌ 驗證失敗: {e}")

                # 檢查是否應該失敗
                if not case["should_pass"]:
                    results.append(("PASS", case["name"]))
                else:
                    print("❌ BUG: 後端拒絕了正確參數！")
                    results.append(("FAIL", case["name"]))

            except Exception as e:
                print(f"💥 意外錯誤: {e}")
                results.append(("ERROR", case["name"]))

        return results

    except ImportError as e:
        print(f"❌ 無法載入後端模組: {e}")
        return [("ERROR", "模組載入失敗")]


def test_unassign_request_validation():
    """測試 UnassignRequest 的驗證邏輯"""
    print("\n🧪 測試取消指派參數驗證...")

    try:
        from pydantic import ValidationError
        from routers.unassign import UnassignRequest

        test_cases = [
            {
                "name": "✅ 正確：student_ids 數字陣列",
                "data": {"student_ids": [1, 2, 3]},
                "should_pass": True,
            },
            {
                "name": "❌ 錯誤：student_ids 字串陣列",
                "data": {"student_ids": ["S001", "S002"]},
                "should_pass": False,
            },
        ]

        results = []

        for case in test_cases:
            print(f"\n🔬 {case['name']}")

            try:
                request = UnassignRequest(**case["data"])
                print(f"✅ 驗證通過: {request}")

                if case["should_pass"]:
                    results.append(("PASS", case["name"]))
                else:
                    results.append(("FAIL", case["name"]))

            except ValidationError as e:
                print(f"❌ 驗證失敗: {e}")

                if not case["should_pass"]:
                    results.append(("PASS", case["name"]))
                else:
                    results.append(("FAIL", case["name"]))

        return results

    except ImportError as e:
        print(f"❌ 無法載入取消指派模組: {e}")
        return [("ERROR", "模組載入失敗")]


def main():
    """主函數"""
    print("🔥 後端參數驗證測試 - 直接測試 Pydantic 模型")
    print("=" * 60)

    all_results = []

    # 測試指派請求驗證
    results = test_assignment_request_validation()
    all_results.extend(results)

    # 測試取消指派請求驗證
    results = test_unassign_request_validation()
    all_results.extend(results)

    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)

    passed = [r for r in all_results if r[0] == "PASS"]
    failed = [r for r in all_results if r[0] == "FAIL"]
    errors = [r for r in all_results if r[0] == "ERROR"]

    print(f"✅ 通過: {len(passed)}")
    print(f"❌ 失敗: {len(failed)}")
    print(f"💥 錯誤: {len(errors)}")

    if failed:
        print("\n💥 發現的後端驗證 Bug:")
        for _, test_name in failed:
            print(f"  - {test_name}")

    if errors:
        print("\n⚠️ 測試執行問題:")
        for _, test_name in errors:
            print(f"  - {test_name}")

    return len(failed) == 0 and len(errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
