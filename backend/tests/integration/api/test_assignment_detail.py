#!/usr/bin/env python3
"""
測試作業詳情 API
TDD: 先寫測試，再實作功能
"""
import requests
from datetime import datetime, timedelta  # noqa: F401

BASE_URL = "http://localhost:8000/api"


def test_student_get_assignment_detail():
    """測試學生獲取作業詳情"""
    print("🔍 測試學生獲取作業詳情...\n")

    # 1. 學生登入
    print("1. 學生登入...")
    response = requests.post(
        f"{BASE_URL}/auth/student/login",
        json={
            "email": "xiaoming.wang.20120101@duotopia.com",
            "password": "mynewpassword123",  # 王小明已更改的密碼
        },
    )

    if response.status_code != 200:
        print(f"❌ 學生登入失敗: {response.text}")
        return

    student_token = response.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("✅ 學生登入成功")

    # 2. 獲取作業列表
    print("\n2. 獲取作業列表...")
    response = requests.get(f"{BASE_URL}/assignments/student", headers=student_headers)

    if response.status_code != 200:
        print(f"❌ 獲取作業列表失敗: {response.text}")
        return

    assignments = response.json()
    if not assignments:
        print("⚠️ 沒有作業，需要先創建測試作業")
        return

    assignment_id = assignments[0]["id"]
    print(f"✅ 找到作業 ID: {assignment_id}")

    # 3. 獲取作業詳情
    print(f"\n3. 獲取作業詳情 (ID: {assignment_id})...")
    response = requests.get(
        f"{BASE_URL}/assignments/{assignment_id}/detail", headers=student_headers
    )

    if response.status_code != 200:
        print(f"❌ 獲取作業詳情失敗: {response.text}")
        return

    detail = response.json()
    print("✅ 成功獲取作業詳情")
    print(f"   標題: {detail.get('title')}")
    print(f"   狀態: {detail.get('status')}")
    print(f"   內容類型: {detail.get('content', {}).get('type')}")
    print(f"   項目數: {len(detail.get('content', {}).get('items', []))}")

    # 驗證必要欄位
    assert "id" in detail
    assert "title" in detail
    assert "status" in detail
    assert "content" in detail
    assert "items" in detail["content"]

    print("\n✅ 作業詳情 API 測試通過！")


def test_student_submit_assignment():
    """測試學生提交作業"""
    print("\n🔍 測試學生提交作業...\n")

    # 1. 學生登入
    print("1. 學生登入...")
    response = requests.post(
        f"{BASE_URL}/auth/student/login",
        json={"email": "student1@demo.com", "password": "20100315"},
    )

    if response.status_code != 200:
        print(f"❌ 學生登入失敗: {response.text}")
        return

    student_token = response.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("✅ 學生登入成功")

    # 2. 獲取一個未完成的作業
    print("\n2. 獲取未完成的作業...")
    response = requests.get(f"{BASE_URL}/assignments/student", headers=student_headers)
    assignments = response.json()

    # 找一個 NOT_STARTED 或 IN_PROGRESS 的作業
    unfinished = next(
        (a for a in assignments if a["status"] in ["NOT_STARTED", "IN_PROGRESS"]), None
    )

    if not unfinished:
        print("⚠️ 沒有未完成的作業")
        return

    assignment_id = unfinished["id"]
    print(f"✅ 找到未完成作業 ID: {assignment_id}")

    # 3. 提交作業
    print(f"\n3. 提交作業 (ID: {assignment_id})...")
    submission_data = {
        "recordings": [
            {
                "item_index": 0,
                "audio_url": "https://storage.googleapis.com/test/recording1.mp3",
                "duration": 5.2,
                "transcript": "Hello, how are you?",
            },
            {
                "item_index": 1,
                "audio_url": "https://storage.googleapis.com/test/recording2.mp3",
                "duration": 4.8,
                "transcript": "I am fine, thank you.",
            },
        ],
        "completed_at": datetime.now().isoformat(),
    }

    response = requests.post(
        f"{BASE_URL}/assignments/{assignment_id}/submit",
        json=submission_data,
        headers=student_headers,
    )

    if response.status_code != 200:
        print(f"❌ 提交作業失敗: {response.text}")
        return

    result = response.json()
    print("✅ 作業提交成功")
    print(f"   狀態: {result.get('status')}")
    print(f"   提交時間: {result.get('submitted_at')}")

    # 驗證
    assert result["status"] == "SUBMITTED"
    assert "submitted_at" in result

    print("\n✅ 作業提交 API 測試通過！")


def test_teacher_view_submissions():
    """測試教師查看學生提交"""
    print("\n🔍 測試教師查看學生提交...\n")

    # 1. 教師登入
    print("1. 教師登入...")
    response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.text}")
        return

    teacher_token = response.json()["access_token"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    print("✅ 教師登入成功")

    # 2. 獲取班級作業
    print("\n2. 獲取班級作業...")
    response = requests.get(
        f"{BASE_URL}/assignments/teacher?classroom_id=1", headers=teacher_headers
    )

    if response.status_code != 200:
        print(f"❌ 獲取作業失敗: {response.text}")
        return

    assignments = response.json()
    if not assignments:
        print("⚠️ 沒有作業")
        return

    # 找一個已提交的作業
    submitted = next((a for a in assignments if a["submissions_count"] > 0), None)

    if not submitted:
        print("⚠️ 沒有已提交的作業")
        return

    assignment_id = submitted["id"]
    print(f"✅ 找到有提交的作業 ID: {assignment_id}")

    # 3. 查看提交詳情
    print("\n3. 查看提交詳情...")
    response = requests.get(
        f"{BASE_URL}/assignments/{assignment_id}/submissions", headers=teacher_headers
    )

    if response.status_code != 200:
        print(f"❌ 獲取提交詳情失敗: {response.text}")
        return

    submissions = response.json()
    print(f"✅ 成功獲取 {len(submissions)} 個提交")

    for sub in submissions[:2]:  # 顯示前2個
        print(f"\n   學生: {sub.get('student_name')}")
        print(f"   狀態: {sub.get('status')}")
        print(f"   提交時間: {sub.get('submitted_at')}")
        print(f"   分數: {sub.get('score')}")

    print("\n✅ 教師查看提交 API 測試通過！")


def test_teacher_manual_grade():
    """測試教師手動評分"""
    print("\n🔍 測試教師手動評分...\n")

    # 1. 教師登入
    print("1. 教師登入...")
    response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    teacher_token = response.json()["access_token"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    print("✅ 教師登入成功")

    # 2. 找一個已提交的作業
    print("\n2. 尋找已提交的作業...")
    response = requests.get(
        f"{BASE_URL}/assignments/teacher?classroom_id=1", headers=teacher_headers
    )

    assignments = response.json()
    submitted = next(
        (a for a in assignments if a.get("submissions_count", 0) > 0), None
    )

    if not submitted:
        print("⚠️ 沒有已提交的作業，跳過測試")
        return

    assignment_id = submitted["id"]

    # 3. 獲取提交列表
    response = requests.get(
        f"{BASE_URL}/assignments/{assignment_id}/submissions", headers=teacher_headers
    )

    submissions = response.json()
    if not submissions:
        print("⚠️ 沒有提交記錄")
        return

    student_assignment_id = submissions[0]["assignment_id"]

    # 4. 手動評分
    print(f"\n3. 手動評分 (作業 ID: {student_assignment_id})...")
    grade_data = {
        "score": 95,
        "feedback": "Excellent work! Your pronunciation is very clear.",
        "detailed_scores": {"pronunciation": 95, "fluency": 93, "accuracy": 97},
    }

    response = requests.post(
        f"{BASE_URL}/assignments/{student_assignment_id}/manual-grade",
        json=grade_data,
        headers=teacher_headers,
    )

    if response.status_code != 200:
        print(f"❌ 評分失敗: {response.text}")
        return

    result = response.json()
    print("✅ 評分成功")
    print(f"   分數: {result.get('score')}")
    print(f"   狀態: {result.get('status')}")
    print(f"   評語: {result.get('feedback')}")

    print("\n✅ 教師手動評分 API 測試通過！")


if __name__ == "__main__":
    print("=" * 50)
    print("作業系統完整功能測試")
    print("=" * 50)

    # 執行所有測試
    test_student_get_assignment_detail()
    test_student_submit_assignment()
    test_teacher_view_submissions()
    test_teacher_manual_grade()

    print("\n" + "=" * 50)
    print("🎉 所有測試完成！")
    print("=" * 50)
