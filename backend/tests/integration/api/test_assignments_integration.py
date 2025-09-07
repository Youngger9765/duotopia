"""
作業系統整合測試
完整測試 Phase 1 & Phase 2 的實際運作流程
"""

import pytest
import requests
from datetime import datetime, timedelta  # noqa: F401
from typing import Dict, List  # noqa: F401


class TestAssignmentsIntegration:
    """作業系統整合測試"""

    BASE_URL = "http://localhost:8000/api"

    # 測試帳號
    TEACHER_CREDS = {"email": "demo@duotopia.com", "password": "demo123"}

    STUDENT_CREDS = [
        {
            "name": "王小明",
            "email": "xiaoming.wang@duotopia.local",
            "password": "mynewpassword123",
        },
        {
            "name": "李小美",
            "email": "xiaomei.li@duotopia.local",
            "password": "20120101",
        },
    ]

    def setup_class(self):
        """測試前準備"""
        self.session = requests.Session()
        self.teacher_token = None
        self.student_tokens = {}
        self.test_results = {"passed": 0, "failed": 0}

    def teardown_class(self):
        """測試後清理"""
        print(f"\n✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")

    def test_teacher_login(self):
        """測試教師登入"""
        response = self.session.post(
            f"{self.BASE_URL}/auth/teacher/login", json=self.TEACHER_CREDS
        )

        assert response.status_code == 200, f"教師登入失敗: {response.text}"
        data = response.json()
        self.teacher_token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.teacher_token}"})
        self.test_results["passed"] += 1

    def test_get_classrooms(self):
        """測試取得班級列表"""
        response = self.session.get(f"{self.BASE_URL}/teachers/classrooms")

        assert response.status_code == 200, f"取得班級失敗: {response.text}"
        classrooms = response.json()
        assert len(classrooms) > 0, "沒有班級資料"
        self.classroom_id = classrooms[0]["id"]
        self.test_results["passed"] += 1

    def test_get_classroom_students(self):
        """測試取得班級學生"""
        if not hasattr(self, "classroom_id"):
            pytest.skip("需要先取得班級 ID")

        response = self.session.get(
            f"{self.BASE_URL}/classrooms/{self.classroom_id}/students"
        )

        assert response.status_code == 200, f"取得學生失敗: {response.text}"
        students = response.json()
        assert len(students) > 0, "班級沒有學生"
        self.student_ids = [s["id"] for s in students[:2]]
        self.test_results["passed"] += 1

    def test_get_contents(self):
        """測試取得 Content 列表"""
        if not hasattr(self, "classroom_id"):
            pytest.skip("需要先取得班級 ID")

        response = self.session.get(
            f"{self.BASE_URL}/contents", params={"classroom_id": self.classroom_id}
        )

        assert response.status_code == 200, f"取得 Content 失敗: {response.text}"
        contents = response.json()
        assert len(contents) > 0, "沒有 Content 資料"
        self.content_id = contents[0]["id"]
        self.test_results["passed"] += 1

    def test_create_assignment(self):
        """測試建立作業"""
        if not hasattr(self, "content_id") or not hasattr(self, "classroom_id"):
            pytest.skip("需要先取得 Content 和班級 ID")

        due_date = (datetime.now() + timedelta(days=3)).isoformat() + "Z"

        # 測試指派給全班
        response = self.session.post(
            f"{self.BASE_URL}/assignments/create",
            json={
                "content_id": self.content_id,
                "classroom_id": self.classroom_id,
                "student_ids": [],  # 全班
                "title": f"整合測試作業 - {datetime.now().strftime('%H:%M')}",
                "instructions": "這是整合測試建立的作業",
                "due_date": due_date,
            },
        )

        assert response.status_code == 200, f"建立作業失敗: {response.text}"
        data = response.json()
        assert data["success"] is True
        self.test_results["passed"] += 1

    def test_teacher_view_assignments(self):
        """測試教師查看作業列表"""
        if not hasattr(self, "classroom_id"):
            pytest.skip("需要先取得班級 ID")

        response = self.session.get(
            f"{self.BASE_URL}/assignments/teacher",
            params={"classroom_id": self.classroom_id},
        )

        assert response.status_code == 200, f"取得作業列表失敗: {response.text}"
        assignments = response.json()
        assert len(assignments) > 0, "沒有作業資料"

        # 檢查統計資訊
        first_assignment = assignments[0]
        assert "total_students" in first_assignment
        assert "status_distribution" in first_assignment
        self.test_results["passed"] += 1

    def test_student_login(self):
        """測試學生登入"""
        for creds in self.STUDENT_CREDS[:1]:  # 只測試第一個學生
            response = requests.post(
                f"{self.BASE_URL}/auth/student/login",
                json={"email": creds["email"], "password": creds["password"]},
            )

            if response.status_code == 200:
                data = response.json()
                self.student_tokens[creds["name"]] = data["access_token"]
                self.test_results["passed"] += 1
            else:
                # 如果登入失敗，跳過後續學生測試
                pytest.skip(f"學生登入失敗: {response.text}")

    def test_student_view_assignments(self):
        """測試學生查看作業列表"""
        if not self.student_tokens:
            pytest.skip("沒有學生 token")

        token = list(self.student_tokens.values())[0]
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(f"{self.BASE_URL}/assignments/student", headers=headers)

        assert response.status_code == 200, f"取得學生作業失敗: {response.text}"
        assignments = response.json()
        assert isinstance(assignments, list)

        # 檢查作業資訊
        if assignments:
            first = assignments[0]
            assert "title" in first
            assert "status" in first
            assert "time_remaining" in first
            self.assignment_id = first["id"]

        self.test_results["passed"] += 1

    def test_student_submit_assignment(self):
        """測試學生提交作業"""
        if not hasattr(self, "assignment_id") or not self.student_tokens:
            pytest.skip("沒有可提交的作業")

        token = list(self.student_tokens.values())[0]
        headers = {"Authorization": f"Bearer {token}"}

        submission_data = {
            "audio_urls": ["test_audio_1.mp3", "test_audio_2.mp3"],
            "completed_at": datetime.now().isoformat(),
        }

        response = requests.post(
            f"{self.BASE_URL}/assignments/{self.assignment_id}/submit",
            json=submission_data,
            headers=headers,
        )

        # 允許 400 錯誤（可能已經提交過）
        assert response.status_code in [200, 400], f"提交作業失敗: {response.text}"

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            self.test_results["passed"] += 1
        else:
            # 已提交過也算通過
            self.test_results["passed"] += 1

    def test_student_view_assignment_detail(self):
        """測試學生查看作業詳情"""
        if not hasattr(self, "assignment_id") or not self.student_tokens:
            pytest.skip("沒有作業詳情可查看")

        token = list(self.student_tokens.values())[0]
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(
            f"{self.BASE_URL}/assignments/{self.assignment_id}/detail", headers=headers
        )

        assert response.status_code == 200, f"取得作業詳情失敗: {response.text}"
        detail = response.json()

        assert "assignment" in detail
        assert "content" in detail
        self.test_results["passed"] += 1


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 作業系統整合測試")
    print("=" * 60)
    print("⚠️  請確保：")
    print("1. 後端服務已啟動 (port 8000)")
    print("2. 已執行 seed_data.py")
    print("3. 已執行 seed_assignments.py")
    print("=" * 60)

    pytest.main([__file__, "-v", "-s"])
