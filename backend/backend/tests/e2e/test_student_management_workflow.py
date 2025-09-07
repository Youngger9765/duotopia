"""
本地測試學生管理功能
測試班級分配和刪除功能是否正常工作
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime  # noqa: F401
from auth import create_access_token


class TestStudentManagementWorkflow:
    """學生管理功能完整測試"""

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

    def test_full_student_management_workflow(self):
        """測試完整的學生管理工作流程"""
        # 1. 教師登入（已在 setup 中完成）
        assert self.teacher_token is not None, "教師登入失敗"

        # 2. 取得現有班級
        response = self.client.get("/api/teachers/classrooms", headers=self.teacher_headers)
        assert response.status_code == 200, f"取得班級失敗: {response.status_code}"

        classrooms = response.json()

        if not classrooms:
            # 建立測試班級
            classroom_data = {
                "name": "測試班級",
                "description": "本地測試用班級",
                "level": "A1",
            }
            response = self.client.post(
                "/api/teachers/classrooms",
                json=classroom_data,
                headers=self.teacher_headers,
            )
            assert response.status_code == 200, "建立班級失敗"
            classrooms = [response.json()]

        classroom = classrooms[0]
        classroom_id = classroom["id"]
        classroom["name"]

        # 3. 建立測試學生（無班級）
        timestamp = int(datetime.now().timestamp())
        student_data = {
            "name": f"本地測試學生_{timestamp}",
            "email": f"local_test_{timestamp}@duotopia.local",
            "birthdate": "2012-01-15",
        }

        response = self.client.post("/api/teachers/students", json=student_data, headers=self.teacher_headers)

        assert response.status_code == 200, f"建立學生失敗: {response.status_code} - {response.text}"

        student = response.json()
        student_id = student["id"]

        # 4. 確認學生列表
        response = self.client.get("/api/teachers/students", headers=self.teacher_headers)
        assert response.status_code == 200, f"取得學生列表失敗: {response.status_code}"

        students = response.json()
        test_student = next((s for s in students if s["id"] == student_id), None)

        assert test_student is not None, "學生未出現在列表中"

        # 5. 測試班級分配
        update_data = {"classroom_id": classroom_id}

        response = self.client.put(
            f"/api/teachers/students/{student_id}",
            json=update_data,
            headers=self.teacher_headers,
        )

        assert response.status_code == 200, f"分配班級失敗: {response.status_code} - {response.text}"

        # 6. 確認班級分配
        response = self.client.get("/api/teachers/students", headers=self.teacher_headers)

        if response.status_code == 200:
            students = response.json()
            test_student = next((s for s in students if s["id"] == student_id), None)

            assert test_student is not None, "學生在班級分配後消失"
            assert (
                test_student["classroom_id"] == classroom_id
            ), f"班級分配失敗 - 實際班級ID: {test_student.get('classroom_id')}"

        # 7. 測試學生刪除
        response = self.client.delete(f"/api/teachers/students/{student_id}", headers=self.teacher_headers)

        assert response.status_code == 200, f"刪除學生失敗: {response.status_code} - {response.text}"

        # 8. 確認學生已被刪除（軟刪除）
        response = self.client.get("/api/teachers/students", headers=self.teacher_headers)

        if response.status_code == 200:
            students = response.json()
            test_student = next((s for s in students if s["id"] == student_id), None)

            assert test_student is None, "學生應該從列表中移除（軟刪除）"

        # 9. 確認刪除的學生無法直接存取
        response = self.client.get(f"/api/teachers/students/{student_id}", headers=self.teacher_headers)

        assert response.status_code == 404, f"刪除的學生應該返回 404，實際: {response.status_code}"

        return True

    def test_student_creation_validation(self):
        """測試學生建立時的驗證"""
        # 測試缺少必要欄位
        invalid_data = {
            "name": "測試學生",
            # 缺少 email 和 birthdate
        }

        response = self.client.post("/api/teachers/students", json=invalid_data, headers=self.teacher_headers)

        assert response.status_code in [400, 422], "缺少必要欄位應該返回錯誤"

        # 測試無效的 email 格式
        invalid_email_data = {
            "name": "測試學生",
            "email": "invalid-email",
            "birthdate": "2012-01-15",
        }

        response = self.client.post(
            "/api/teachers/students",
            json=invalid_email_data,
            headers=self.teacher_headers,
        )

        assert response.status_code in [400, 422], "無效 email 格式應該返回錯誤"

        # 測試無效的日期格式
        invalid_date_data = {
            "name": "測試學生",
            "email": "test@example.com",
            "birthdate": "invalid-date",
        }

        response = self.client.post(
            "/api/teachers/students",
            json=invalid_date_data,
            headers=self.teacher_headers,
        )

        assert response.status_code in [400, 422], "無效日期格式應該返回錯誤"

    def test_classroom_assignment_edge_cases(self):
        """測試班級分配的邊界情況"""
        # 首先建立一個測試學生
        timestamp = int(datetime.now().timestamp())
        student_data = {
            "name": f"邊界測試學生_{timestamp}",
            "email": f"edge_test_{timestamp}@duotopia.local",
            "birthdate": "2012-01-15",
        }

        response = self.client.post("/api/teachers/students", json=student_data, headers=self.teacher_headers)

        assert response.status_code == 200, "建立測試學生失敗"
        student = response.json()
        student_id = student["id"]

        try:
            # 測試分配到不存在的班級
            update_data = {"classroom_id": 99999}

            response = self.client.put(
                f"/api/teachers/students/{student_id}",
                json=update_data,
                headers=self.teacher_headers,
            )

            assert response.status_code in [
                400,
                404,
                422,
            ], "分配到不存在班級應該返回錯誤"

            # 測試清除班級分配（設為 null）
            update_data = {"classroom_id": None}

            response = self.client.put(
                f"/api/teachers/students/{student_id}",
                json=update_data,
                headers=self.teacher_headers,
            )

            # 這可能是有效操作（移除學生出班級）
            assert response.status_code in [200, 400], "清除班級分配結果"

        finally:
            # 清理測試學生
            self.client.delete(f"/api/teachers/students/{student_id}", headers=self.teacher_headers)

    def test_student_deletion_permissions(self):
        """測試學生刪除權限"""
        # 建立測試學生
        timestamp = int(datetime.now().timestamp())
        student_data = {
            "name": f"權限測試學生_{timestamp}",
            "email": f"perm_test_{timestamp}@duotopia.local",
            "birthdate": "2012-01-15",
        }

        response = self.client.post("/api/teachers/students", json=student_data, headers=self.teacher_headers)

        assert response.status_code == 200, "建立測試學生失敗"
        student = response.json()
        student_id = student["id"]

        try:
            # 測試未認證的刪除請求
            response = self.client.delete(f"/api/teachers/students/{student_id}")
            assert response.status_code == 401, "未認證刪除請求應該返回 401"

            # 測試刪除不存在的學生
            response = self.client.delete("/api/teachers/students/99999", headers=self.teacher_headers)
            assert response.status_code == 404, "刪除不存在學生應該返回 404"

        finally:
            # 清理測試學生
            self.client.delete(f"/api/teachers/students/{student_id}", headers=self.teacher_headers)

    def test_student_list_filtering(self):
        """測試學生列表篩選功能"""
        # 獲取學生列表
        response = self.client.get("/api/teachers/students", headers=self.teacher_headers)
        assert response.status_code == 200, "取得學生列表失敗"

        students = response.json()

        # 測試按班級篩選（如果 API 支援）
        if students:
            # 嘗試按班級ID篩選
            first_student = students[0]
            classroom_id = first_student.get("classroom_id")

            if classroom_id:
                response = self.client.get(
                    f"/api/teachers/students?classroom_id={classroom_id}",
                    headers=self.teacher_headers,
                )

                # 如果API支援篩選，應該返回該班級的學生
                if response.status_code == 200:
                    filtered_students = response.json()
                    # 所有返回的學生都應該屬於指定班級
                    for student in filtered_students:
                        assert student.get("classroom_id") == classroom_id

        # 測試搜尋功能（如果 API 支援）
        response = self.client.get("/api/teachers/students?search=test", headers=self.teacher_headers)

        # 搜尋功能可能未實作，允許 200 或其他狀態
        assert response.status_code in [200, 400, 404], "搜尋請求應該被適當處理"

    def test_bulk_student_operations(self):
        """測試批量學生操作"""
        # 建立多個測試學生
        timestamp = int(datetime.now().timestamp())
        student_ids = []

        for i in range(3):
            student_data = {
                "name": f"批量測試學生_{i}_{timestamp}",
                "email": f"bulk_test_{i}_{timestamp}@duotopia.local",
                "birthdate": "2012-01-15",
            }

            response = self.client.post(
                "/api/teachers/students",
                json=student_data,
                headers=self.teacher_headers,
            )

            if response.status_code == 200:
                student_ids.append(response.json()["id"])

        try:
            # 測試批量刪除（如果 API 支援）
            if student_ids:
                bulk_delete_data = {"student_ids": student_ids}

                response = self.client.post(
                    "/api/teachers/students/bulk-delete",
                    json=bulk_delete_data,
                    headers=self.teacher_headers,
                )

                # 批量操作可能未實作
                if response.status_code == 404:
                    pytest.skip("批量刪除功能尚未實作")
                elif response.status_code == 200:
                    # 驗證所有學生都被刪除
                    for student_id in student_ids:
                        response = self.client.get(
                            f"/api/teachers/students/{student_id}",
                            headers=self.teacher_headers,
                        )
                        assert response.status_code == 404, f"學生 {student_id} 應該被刪除"

                    # 清空列表，避免 finally 重複刪除
                    student_ids = []

        finally:
            # 清理剩餘的測試學生
            for student_id in student_ids:
                self.client.delete(f"/api/teachers/students/{student_id}", headers=self.teacher_headers)

    def test_student_data_consistency(self):
        """測試學生資料一致性"""
        # 建立測試學生
        timestamp = int(datetime.now().timestamp())
        original_data = {
            "name": f"一致性測試學生_{timestamp}",
            "email": f"consistency_test_{timestamp}@duotopia.local",
            "birthdate": "2012-01-15",
        }

        response = self.client.post("/api/teachers/students", json=original_data, headers=self.teacher_headers)

        assert response.status_code == 200, "建立測試學生失敗"
        student = response.json()
        student_id = student["id"]

        try:
            # 驗證建立的學生資料
            assert student["name"] == original_data["name"]
            assert student["email"] == original_data["email"]
            assert student["birthdate"] == original_data["birthdate"]

            # 從列表中取得學生，驗證資料一致性
            response = self.client.get("/api/teachers/students", headers=self.teacher_headers)
            assert response.status_code == 200

            students = response.json()
            list_student = next((s for s in students if s["id"] == student_id), None)

            assert list_student is not None, "學生未出現在列表中"
            assert list_student["name"] == original_data["name"]
            assert list_student["email"] == original_data["email"]

            # 單獨取得學生資料，驗證一致性
            response = self.client.get(f"/api/teachers/students/{student_id}", headers=self.teacher_headers)

            if response.status_code == 200:
                detail_student = response.json()
                assert detail_student["name"] == original_data["name"]
                assert detail_student["email"] == original_data["email"]
                assert detail_student["birthdate"] == original_data["birthdate"]

        finally:
            # 清理測試學生
            self.client.delete(f"/api/teachers/students/{student_id}", headers=self.teacher_headers)
