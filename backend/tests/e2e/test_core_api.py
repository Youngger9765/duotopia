"""
Core API Tests - 核心 API 基本測試
只測試最關鍵的端點，確保系統基本運作
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthCheck:
    """健康檢查"""

    def test_health_endpoint(self):
        """測試健康檢查端點"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data

    def test_root_endpoint(self):
        """測試根端點"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestPublicEndpoints:
    """公開端點測試"""

    def test_validate_teacher(self):
        """測試教師驗證端點"""
        response = client.post(
            "/api/public/validate-teacher", json={"email": "demo@duotopia.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data

    def test_get_teacher_classrooms(self):
        """測試獲取教師班級列表"""
        response = client.get(
            "/api/public/teacher-classrooms", params={"email": "demo@duotopia.com"}
        )
        # 可能返回 200 (有資料) 或 404 (沒找到教師)
        assert response.status_code in [200, 404]


class TestAdminEndpoints:
    """管理端點測試"""

    def test_database_stats(self):
        """測試資料庫統計端點"""
        response = client.get("/api/admin/database/stats")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "total_records" in data

    def test_get_entity_data(self):
        """測試獲取 entity 資料"""
        response = client.get("/api/admin/database/entity/teacher?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "pagination" in data


class TestAuthEndpoints:
    """認證端點基本測試"""

    def test_teacher_login_invalid(self):
        """測試無效的教師登入"""
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "invalid@test.com", "password": "wrong"},
        )
        # 可能返回 401 (未授權) 或 404 (找不到用戶)
        assert response.status_code in [401, 404]

    def test_student_login_invalid(self):
        """測試無效的學生登入"""
        response = client.post(
            "/api/auth/student/login",
            json={"email": "invalid@test.com", "password": "wrong"},
        )
        # 可能返回 401 (未授權) 或 422 (驗證錯誤)
        assert response.status_code in [401, 422, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
