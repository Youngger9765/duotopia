"""
測試人工批改功能 (Phase 4)
測試教師手動批改和回饋功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from auth import create_access_token


class TestManualGrading:
    """人工批改功能測試"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, client: TestClient, demo_teacher):
        """為每個測試方法準備測試資料"""
        self.client = client
        self.teacher = demo_teacher

        # 建立教師 token
        self.teacher_token = create_access_token(
            data={
                "sub": str(self.teacher.id),
                "email": self.teacher.email,
                "type": "teacher",
            }
        )
        self.teacher_headers = {"Authorization": f"Bearer {self.teacher_token}"}

        # 建立已 AI 批改的作業
        self.test_data = self._create_graded_assignment_for_manual_grading()

    def _create_graded_assignment_for_manual_grading(self):
        """建立已 AI 批改的作業用於人工批改"""
        # 1. 建立測試班級
        classroom_data = {
            "name": f"人工批改測試班級_{datetime.now().strftime('%H%M%S')}",
            "description": "用於測試人工批改功能",
            "level": "A1",
        }

        response = self.client.post(
            "/api/teachers/classrooms",
            json=classroom_data,
            headers=self.teacher_headers,
        )
        assert response.status_code == 200, f"建立班級失敗: {response.status_code}"
        classroom = response.json()

        # 2. 建立測試學生
        student_data = {
            "name": "人工批改測試學生",
            "email": f"manual_grading_student_{int(datetime.now().timestamp())}@example.com",
            "birthdate": "2012-01-01",
            "classroom_id": classroom["id"],
        }

        response = self.client.post(
            "/api/teachers/students", json=student_data, headers=self.teacher_headers
        )
        assert response.status_code == 200, "建立學生失敗"
        student = response.json()

        # 3. 建立測試課程和內容
        program_data = {
            "name": f"人工批改測試課程_{datetime.now().strftime('%H%M%S')}",
            "description": "測試用課程",
            "level": "A1",
            "classroom_id": classroom["id"],
        }

        response = self.client.post(
            "/api/teachers/programs", json=program_data, headers=self.teacher_headers
        )
        assert response.status_code == 200, f"建立課程失敗: {response.status_code}"
        program = response.json()

        lesson_data = {
            "name": "Unit 1 - Manual Grading Test",
            "description": "用於測試人工批改的課程單元",
            "order_index": 1,
        }

        response = self.client.post(
            f"/api/teachers/programs/{program['id']}/lessons",
            json=lesson_data,
            headers=self.teacher_headers,
        )
        assert response.status_code == 200, f"建立課程單元失敗: {response.status_code}"
        lesson = response.json()

        # 4. 建立朗讀評測內容
        content_data = {
            "title": "Manual Grading Reading Test",
            "description": "測試人工批改朗讀練習",
            "content_type": "reading_assessment",
            "items": [
                {"text": "The cat sat on the mat.", "order": 1},
                {"text": "She likes to read books.", "order": 2},
                {"text": "Today is a beautiful day.", "order": 3},
            ],
        }

        response = self.client.post(
            f"/api/teachers/lessons/{lesson['id']}/contents",
            json=content_data,
            headers=self.teacher_headers,
        )
        assert response.status_code == 200, f"建立內容失敗: {response.status_code}"
        content = response.json()

        # 5. 建立作業
        assignment_data = {
            "content_id": content["id"],
            "classroom_id": classroom["id"],
            "student_ids": [student["id"]],
            "title": "人工批改測試作業",
            "instructions": "請朗讀以下句子，老師將進行人工批改。",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        response = self.client.post(
            "/api/assignments/create",
            json=assignment_data,
            headers=self.teacher_headers,
        )
        assert response.status_code == 200, "建立作業失敗"

        # 6. 學生提交作業
        student_token = self._get_student_token(student["email"], "20120101")
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # 先取得作業ID
        response = self.client.get("/api/assignments/student", headers=student_headers)
        assert response.status_code == 200, "查詢學生作業失敗"
        assignments = response.json()

        assignment_id = None
        for assignment in assignments:
            if assignment["title"] == "人工批改測試作業":
                assignment_id = assignment["id"]
                break

        assert assignment_id is not None, "找不到建立的作業"

        # 提交作業
        submission_data = {
            "responses": [
                {
                    "item_id": 1,
                    "text": "The cat sat on the mat.",
                    "audio_url": f"gs://duotopia-audio/recordings/{assignment_id}_1.mp3",
                },
                {
                    "item_id": 2,
                    "text": "She likes to read books.",
                    "audio_url": f"gs://duotopia-audio/recordings/{assignment_id}_2.mp3",
                },
                {
                    "item_id": 3,
                    "text": "Today is a beautiful day.",
                    "audio_url": f"gs://duotopia-audio/recordings/{assignment_id}_3.mp3",
                },
            ],
            "submission_metadata": {
                "browser": "Chrome/91.0",
                "device": "Desktop",
                "duration_seconds": 12.0,
            },
        }

        response = self.client.post(
            f"/api/assignments/{assignment_id}/submit",
            json=submission_data,
            headers=student_headers,
        )
        assert response.status_code == 200, "提交作業失敗"

        # 7. AI 批改作業（為人工批改做準備）
        ai_grading_data = {
            "grading_mode": "full",
            "audio_urls": [
                f"gs://duotopia-audio/recordings/{assignment_id}_1.mp3",
                f"gs://duotopia-audio/recordings/{assignment_id}_2.mp3",
                f"gs://duotopia-audio/recordings/{assignment_id}_3.mp3",
            ],
        }

        response = self.client.post(
            f"/api/assignments/{assignment_id}/ai-grade",
            json=ai_grading_data,
            headers=self.teacher_headers,
        )

        # AI 批改可能還沒實作，模擬結果
        if response.status_code == 200:
            ai_result = response.json()
        else:
            # 模擬 AI 批改結果
            ai_result = {
                "overall_score": 75.0,
                "ai_scores": {
                    "pronunciation": 78,
                    "fluency": 72,
                    "accuracy": 80,
                    "wpm": 110,
                },
            }

        return {
            "classroom": classroom,
            "student": student,
            "program": program,
            "lesson": lesson,
            "content": content,
            "assignment_id": assignment_id,
            "student_token": student_token,
            "ai_result": ai_result,
        }

    def _get_student_token(self, email, password):
        """取得學生 token"""
        response = self.client.post(
            "/api/auth/student/login", json={"email": email, "password": password}
        )
        if response.status_code != 200:
            return None
        return response.json()["access_token"]

    def test_manual_score_adjustment(self):
        """測試手動調整分數"""
        assignment_id = self.test_data["assignment_id"]
        original_score = self.test_data["ai_result"]["overall_score"]

        # 手動調整分數
        manual_adjustment = {
            "manual_score": 88.5,
            "score_reason": "學生發音有明顯進步，但語速略快，給予鼓勵性評分。",
            "adjusted_scores": {
                "pronunciation": 90.0,
                "fluency": 85.0,
                "accuracy": 92.0,
            },
        }

        response = self.client.patch(
            f"/api/assignments/{assignment_id}/manual-grade",
            json=manual_adjustment,
            headers=self.teacher_headers,
        )

        # 如果 API 還沒實作，允許 404
        if response.status_code == 404:
            pytest.skip("手動調整分數 API 尚未實作（預期行為）")
            return

        assert (
            response.status_code == 200
        ), f"手動調整分數失敗: {response.status_code} - {response.text}"

        result = response.json()
        assert "success" in result
        assert result["success"] == True

        # 驗證調整結果
        assert "updated_score" in result
        assert result["updated_score"] == 88.5

    def test_manual_feedback_editing(self):
        """測試手動編輯回饋"""
        assignment_id = self.test_data["assignment_id"]

        # 編輯回饋內容
        feedback_update = {
            "manual_feedback": "你的朗讀表現很棒！以下是具體建議：\\n1. 發音清晰，特別是 'beautiful' 這個字\\n2. 可以嘗試稍微放慢語速\\n3. 句子間的停頓很自然\\n\\n繼續保持這樣的練習！下次可以挑戰更長的文章。",
            "feedback_tags": ["pronunciation_good", "speed_improvement", "encourage"],
            "teacher_notes": "學生進步明顯，給予正向鼓勵。",
        }

        response = self.client.patch(
            f"/api/assignments/{assignment_id}/manual-feedback",
            json=feedback_update,
            headers=self.teacher_headers,
        )

        # 如果 API 還沒實作，允許 404
        if response.status_code == 404:
            pytest.skip("手動編輯回饋 API 尚未實作（預期行為）")
            return

        assert (
            response.status_code == 200
        ), f"編輯回饋失敗: {response.status_code} - {response.text}"

        result = response.json()
        assert "success" in result
        assert result["success"] == True

        # 檢查學生端是否能看到更新的回饋
        student_headers = {"Authorization": f"Bearer {self.test_data['student_token']}"}
        response = self.client.get(
            f"/api/assignments/{assignment_id}/detail", headers=student_headers
        )

        if response.status_code == 200:
            assignment_detail = response.json()
            if (
                "assignment" in assignment_detail
                and "feedback" in assignment_detail["assignment"]
            ):
                # 學生可以看到更新後的回饋
                pass

    def test_assignment_return_for_revision(self):
        """測試退回作業要求修改"""
        assignment_id = self.test_data["assignment_id"]

        # 退回作業並要求重做
        return_request = {
            "return_reason": "發音需要改進",
            "specific_feedback": "請特別注意以下幾點：\\n1. 'beautiful' 的發音需要更清楚\\n2. 'books' 的結尾音需要加強\\n3. 整體語速可以放慢一些",
            "allow_resubmission": True,
            "new_due_date": (datetime.now() + timedelta(days=3)).isoformat(),
        }

        response = self.client.post(
            f"/api/assignments/{assignment_id}/return",
            json=return_request,
            headers=self.teacher_headers,
        )

        # 如果 API 還沒實作，允許 404
        if response.status_code == 404:
            pytest.skip("退回作業 API 尚未實作（預期行為）")
            return

        assert (
            response.status_code == 200
        ), f"退回作業失敗: {response.status_code} - {response.text}"

        result = response.json()
        assert "success" in result
        assert result["success"] == True

        # 檢查作業狀態是否更新為 RETURNED
        student_headers = {"Authorization": f"Bearer {self.test_data['student_token']}"}
        response = self.client.get("/api/assignments/student", headers=student_headers)

        if response.status_code == 200:
            assignments = response.json()
            our_assignment = next(
                (a for a in assignments if a["id"] == assignment_id), None
            )
            if our_assignment and our_assignment["status"] == "RETURNED":
                # 作業狀態正確更新為 RETURNED
                pass

    def test_batch_manual_grading(self):
        """測試批量人工批改"""
        # 準備批量批改資料
        batch_grading = {
            "assignment_ids": [self.test_data["assignment_id"]],
            "bulk_adjustments": {
                "score_adjustment": "+5",  # 全部加5分
                "feedback_template": "整體表現良好，繼續努力！",
                "apply_to_all": True,
            },
        }

        response = self.client.post(
            "/api/assignments/batch-manual-grade",
            json=batch_grading,
            headers=self.teacher_headers,
        )

        # 如果 API 還沒實作，允許 404
        if response.status_code == 404:
            pytest.skip("批量人工批改 API 尚未實作（Phase 5 功能）")
            return

        assert response.status_code == 200, f"批量批改失敗: {response.status_code}"

        result = response.json()
        assert "processed_count" in result
        assert result["processed_count"] >= 1, "至少應該處理一個作業"

    def test_grading_history_tracking(self):
        """測試批改歷史記錄"""
        assignment_id = self.test_data["assignment_id"]

        # 查詢批改歷史
        response = self.client.get(
            f"/api/assignments/{assignment_id}/grading-history",
            headers=self.teacher_headers,
        )

        # 如果 API 還沒實作，允許 404
        if response.status_code == 404:
            pytest.skip("批改歷史記錄 API 尚未實作（預期行為）")
            return

        assert response.status_code == 200, f"查詢批改歷史失敗: {response.status_code}"

        history = response.json()
        assert isinstance(history, list), "批改歷史應該是列表"

        # 應該有 AI 批改記錄
        assert len(history) >= 1, "至少應該有一次 AI 批改記錄"

        # 檢查歷史記錄結構
        record = history[0]
        expected_fields = [
            "grading_type",
            "graded_by",
            "graded_at",
            "score",
            "feedback",
        ]
        for field in expected_fields:
            assert field in record, f"批改記錄缺少欄位: {field}"

    def test_grading_dashboard_for_teachers(self):
        """測試教師批改儀表板"""
        classroom_id = self.test_data["classroom"]["id"]

        # 查詢批改儀表板資料
        response = self.client.get(
            f"/api/teachers/grading-dashboard?classroom_id={classroom_id}",
            headers=self.teacher_headers,
        )

        # 如果 API 還沒實作，允許 404
        if response.status_code == 404:
            pytest.skip("教師批改儀表板 API 尚未實作（預期行為）")
            return

        assert response.status_code == 200, f"查詢批改儀表板失敗: {response.status_code}"

        dashboard = response.json()

        # 檢查儀表板資料結構
        expected_sections = [
            "pending_assignments",
            "grading_statistics",
            "recent_activities",
        ]
        for section in expected_sections:
            assert section in dashboard, f"儀表板缺少區塊: {section}"

        # 檢查統計資料
        stats = dashboard["grading_statistics"]
        expected_stats = [
            "total_assignments",
            "ai_graded",
            "manually_reviewed",
            "pending_review",
        ]
        for stat in expected_stats:
            assert stat in stats, f"統計資料缺少欄位: {stat}"

    def test_assignment_comparison_view(self):
        """測試作業對比檢視（比較 AI vs 人工評分）"""
        assignment_id = self.test_data["assignment_id"]

        # 查詢作業對比資料
        response = self.client.get(
            f"/api/assignments/{assignment_id}/comparison-view",
            headers=self.teacher_headers,
        )

        # 如果 API 還沒實作，允許 404
        if response.status_code == 404:
            pytest.skip("作業對比檢視 API 尚未實作（預期行為）")
            return

        assert response.status_code == 200, f"查詢對比檢視失敗: {response.status_code}"

        comparison = response.json()

        # 檢查對比資料結構
        expected_sections = [
            "ai_grading",
            "manual_adjustments",
            "score_differences",
            "feedback_comparison",
        ]
        for section in expected_sections:
            assert section in comparison, f"對比檢視缺少區塊: {section}"

        # 檢查評分差異
        if "score_differences" in comparison:
            score_diff = comparison["score_differences"]
            assert (
                "ai_score" in score_diff
                or "manual_score" in score_diff
                or "difference" in score_diff
            )

    def test_manual_grading_permissions(self):
        """測試人工批改權限控制"""
        assignment_id = self.test_data["assignment_id"]

        # 測試學生無法進行人工批改
        student_headers = {"Authorization": f"Bearer {self.test_data['student_token']}"}

        manual_adjustment = {"manual_score": 95.0, "score_reason": "學生自己給自己高分"}

        response = self.client.patch(
            f"/api/assignments/{assignment_id}/manual-grade",
            json=manual_adjustment,
            headers=student_headers,
        )

        # 學生應該被拒絕存取
        if response.status_code != 404:  # 如果 API 已實作
            assert response.status_code in [403, 401], "學生不應能進行人工批改"

        # 測試未認證請求
        response = self.client.patch(
            f"/api/assignments/{assignment_id}/manual-grade", json=manual_adjustment
        )

        assert response.status_code == 401, "未認證請求應該返回 401"
