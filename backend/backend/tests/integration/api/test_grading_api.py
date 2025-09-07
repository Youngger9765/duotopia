#!/usr/bin/env python3
"""測試批改功能 API"""

import requests

# API 基礎 URL
BASE_URL = "http://localhost:8000"

# 教師登入憑證
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


def login_teacher():
    """登入教師帳號"""
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 教師登入成功: {data['user']['name']}")
        return data["access_token"]
    else:
        print(f"❌ 教師登入失敗: {response.status_code}")
        print(response.text)
        return None


def test_get_submission(token, assignment_id=2, student_id=1):
    """測試取得學生作業提交內容"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/api/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )

    if response.status_code == 200:
        data = response.json()
        print("\n✅ 成功取得學生作業提交內容")
        print(f"學生: {data.get('student_name')} ({data.get('student_email')})")
        print(f"狀態: {data.get('status')}")

        # 檢查是否有 content_groups
        if data.get("content_groups"):
            print(f"\n📚 內容分組 (共 {len(data['content_groups'])} 組):")
            for i, group in enumerate(data["content_groups"]):
                print(f"  Content {chr(65+i)}: {group['content_title']} - {len(group['submissions'])} 題")
                # 顯示第一題
                if group["submissions"]:
                    first_q = group["submissions"][0]
                    print(f"    第1題: {first_q.get('question_text', 'N/A')}")

        # 檢查是否有 submissions（平面化的題目列表）
        if data.get("submissions"):
            print(f"\n題目總數: {len(data['submissions'])} 題")
            for i, sub in enumerate(data["submissions"][:3]):  # 只顯示前3題
                print(f"  題目 {i+1}: {sub.get('question_text', 'N/A')}")
                if sub.get("question_text", "").startswith("[MOCK]"):
                    print("    ⚠️ 這是 MOCK 資料！")

        return data
    else:
        print(f"❌ 取得作業失敗: {response.status_code}")
        print(response.text)
        return None


def test_grade_submission(token, assignment_id=2, student_id=1):
    """測試批改作業"""
    headers = {"Authorization": f"Bearer {token}"}

    grade_data = {
        "student_id": student_id,
        "score": 85,
        "feedback": "很棒的表現！發音清晰，語調自然。建議多練習連音的部分。",
    }

    response = requests.post(
        f"{BASE_URL}/api/teachers/assignments/{assignment_id}/grade",
        headers=headers,
        json=grade_data,
    )

    if response.status_code == 200:
        data = response.json()
        print("\n✅ 成功批改作業")
        print(f"訊息: {data.get('message')}")
        return True
    else:
        print(f"❌ 批改失敗: {response.status_code}")
        print(response.text)
        return False


def main():
    print("=" * 50)
    print("測試批改功能 API")
    print("=" * 50)

    # 1. 登入教師
    token = login_teacher()
    if not token:
        print("\n⚠️ 無法登入，測試中止")
        return

    # 2. 測試取得學生作業
    print("\n" + "=" * 50)
    print("測試取得學生作業內容")
    print("=" * 50)
    submission = test_get_submission(token, assignment_id=2, student_id=1)

    # 3. 測試批改功能
    if submission:
        print("\n" + "=" * 50)
        print("測試批改功能")
        print("=" * 50)
        test_grade_submission(token, assignment_id=2, student_id=1)

    # 4. 再次取得確認批改結果
    print("\n" + "=" * 50)
    print("驗證批改結果")
    print("=" * 50)
    updated = test_get_submission(token, assignment_id=2, student_id=1)
    if updated and updated.get("current_score"):
        print(f"\n✅ 批改成功！分數: {updated['current_score']}")
        print(f"評語: {updated.get('current_feedback', 'N/A')}")


if __name__ == "__main__":
    main()
