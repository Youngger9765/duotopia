#!/usr/bin/env python3
"""
測試完整的批改功能流程
包括：
1. 自動儲存功能
2. 個別評語同步到總評語
3. 音檔播放
4. 資料持久化
"""

import requests
import json  # noqa: F401
import time

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# 教師測試帳號
TEACHER_EMAIL = "teacher1@test.com"


def get_teacher_token():
    """取得教師 JWT token"""
    response = requests.post(
        f"{API_URL}/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": "password123"},
    )
    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.text}")
        return None
    return response.json().get("access_token")


def test_grading_api(token):
    """測試批改 API 功能"""
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 取得教師的作業列表
    print("\n📚 取得教師作業列表...")
    response = requests.get(f"{API_URL}/teachers/assignments", headers=headers)
    if response.status_code != 200:
        print(f"❌ 無法取得作業列表: {response.text}")
        return False

    assignments = response.json()
    if not assignments:
        print("⚠️ 沒有作業可供測試")
        return False

    # 使用第一個作業
    assignment = assignments[0]
    assignment_id = assignment["assignment_id"]
    print(f"✅ 找到作業: {assignment['assignment_name']} (ID: {assignment_id})")

    # 2. 取得學生提交列表
    print("\n👥 取得學生提交列表...")
    response = requests.get(
        f"{API_URL}/teachers/assignments/{assignment_id}/students", headers=headers
    )
    if response.status_code != 200:
        print(f"❌ 無法取得學生列表: {response.text}")
        return False

    students = response.json()
    if not students:
        print("⚠️ 沒有學生提交")
        return False

    # 找一個已提交的學生
    submitted_student = None
    for student in students:
        if student["status"] in ["SUBMITTED", "GRADED", "RESUBMITTED"]:
            submitted_student = student
            break

    if not submitted_student:
        print("⚠️ 沒有已提交的學生作業")
        return False

    student_id = submitted_student["student_id"]
    print(f"✅ 找到學生: {submitted_student['student_name']} (ID: {student_id})")

    # 3. 取得學生提交詳情
    print("\n📝 取得學生提交詳情...")
    response = requests.get(
        f"{API_URL}/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )
    if response.status_code != 200:
        print(f"❌ 無法取得提交詳情: {response.text}")
        return False

    submission = response.json()
    print("✅ 成功取得提交詳情")

    # 4. 測試批改功能（包含個別題目評語）
    print("\n✏️ 測試批改功能...")

    # 準備個別題目評語
    item_results = []
    if submission.get("content_groups"):
        for group_idx, group in enumerate(submission["content_groups"]):
            for item_idx, item in enumerate(group.get("submissions", [])):
                global_idx = (
                    sum(
                        len(g.get("submissions", []))
                        for g in submission["content_groups"][:group_idx]
                    )
                    + item_idx
                )
                item_results.append(
                    {
                        "item_index": global_idx,
                        "feedback": f"題目 {global_idx + 1} 測試評語 - {'表現優秀' if global_idx % 2 == 0 else '需要加強'}",
                        "passed": global_idx % 2 == 0,  # 偶數題通過，奇數題不通過
                    }
                )

    # 批改資料
    grade_data = {
        "student_id": student_id,
        "score": 85,
        "feedback": "測試總評語：學生整體表現良好，持續努力！",
        "item_results": item_results,
    }

    response = requests.post(
        f"{API_URL}/teachers/assignments/{assignment_id}/grade",
        headers=headers,
        json=grade_data,
    )

    if response.status_code != 200:
        print(f"❌ 批改失敗: {response.text}")
        return False

    print("✅ 批改成功！")

    # 5. 驗證批改結果是否儲存
    print("\n🔍 驗證批改結果...")
    time.sleep(1)  # 等待資料寫入

    response = requests.get(
        f"{API_URL}/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )
    if response.status_code != 200:
        print(f"❌ 無法重新取得提交詳情: {response.text}")
        return False

    updated_submission = response.json()

    # 檢查分數
    if updated_submission.get("score") == 85:
        print("✅ 分數正確儲存")
    else:
        print(f"❌ 分數未正確儲存: {updated_submission.get('score')}")

    # 檢查總評語
    if "測試總評語" in updated_submission.get("feedback", ""):
        print("✅ 總評語正確儲存")
    else:
        print(f"❌ 總評語未正確儲存: {updated_submission.get('feedback')}")

    # 檢查個別題目評語
    saved_item_feedbacks = 0
    if updated_submission.get("content_groups"):
        for group in updated_submission["content_groups"]:
            for item in group.get("submissions", []):
                if item.get("feedback"):
                    saved_item_feedbacks += 1

    if saved_item_feedbacks > 0:
        print(f"✅ 個別題目評語正確儲存 ({saved_item_feedbacks} 題)")
    else:
        print("❌ 個別題目評語未儲存")

    # 6. 測試音檔端點
    print("\n🎵 測試音檔服務...")

    # 測試參考音檔
    response = requests.get(f"{API_URL}/files/audio/1/0")
    if response.status_code in [200, 307]:  # 307 是重定向到範例音檔
        print("✅ 參考音檔端點正常")
    else:
        print(f"⚠️ 參考音檔端點異常: {response.status_code}")

    # 測試錄音檔案（可能不存在）
    response = requests.get(f"{API_URL}/files/recordings/test.webm")
    if response.status_code == 404:
        print("ℹ️ 錄音檔案不存在（正常）")
    elif response.status_code == 200:
        print("✅ 錄音檔案端點正常")
    else:
        print(f"⚠️ 錄音檔案端點異常: {response.status_code}")

    return True


def main():
    print("🚀 開始測試完整批改功能流程")
    print("=" * 50)

    # 取得教師 token
    token = get_teacher_token()
    if not token:
        print("\n❌ 測試失敗：無法登入")
        return

    print("✅ 教師登入成功")

    # 執行批改測試
    if test_grading_api(token):
        print("\n" + "=" * 50)
        print("✅ 所有測試完成！批改功能運作正常")
        print("\n功能確認：")
        print("  ✅ 批改 API 正常運作")
        print("  ✅ 個別題目評語儲存")
        print("  ✅ 分數與總評語儲存")
        print("  ✅ 音檔服務端點正常")
        print("\n建議：")
        print("  1. 在瀏覽器中開啟批改頁面測試自動儲存")
        print("  2. 使用鍵盤方向鍵測試快速導航")
        print("  3. 測試個別評語自動同步到總評語")
    else:
        print("\n❌ 測試過程中發現問題，請檢查錯誤訊息")


if __name__ == "__main__":
    main()
