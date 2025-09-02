"""
API Endpoints 整合測試
確保所有 API endpoints 都能正確訪問
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db, SessionLocal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

client = TestClient(app)


class TestAPIEndpoints:
    """測試所有 API endpoints 的可訪問性"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """設置測試環境"""
        self.teacher_token = None
        self.student_token = None

        # 登入教師取得 token
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "demo@duotopia.com", "password": "demo123"},
        )
        if response.status_code == 200:
            self.teacher_token = response.json()["access_token"]

    def test_public_endpoints(self):
        """測試公開 endpoints"""
        # 根路徑
        response = client.get("/")
        assert response.status_code == 200

        # 健康檢查
        response = client.get("/health")
        assert response.status_code == 200

        # 公開 API
        response = client.get("/api/public/teachers")
        assert response.status_code == 200

    def test_auth_endpoints(self):
        """測試認證 endpoints"""
        # 教師登入
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": "demo@duotopia.com", "password": "demo123"},
        )
        assert response.status_code == 200

        # Token 驗證
        if self.teacher_token:
            response = client.get(
                "/api/auth/validate",
                headers={"Authorization": f"Bearer {self.teacher_token}"},
            )
            assert response.status_code == 200

    def test_teacher_endpoints(self):
        """測試教師 endpoints"""
        if not self.teacher_token:
            pytest.skip("No teacher token available")

        headers = {"Authorization": f"Bearer {self.teacher_token}"}

        # 教師 API endpoints
        endpoints = [
            ("/api/teachers/classrooms", "GET"),
            ("/api/teachers/programs", "GET"),
            ("/api/teachers/assignments", "GET"),  # 測試 assignments router
            ("/api/teachers/students", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=headers)
                assert response.status_code in [
                    200,
                    404,
                ], f"Endpoint {endpoint} returned {response.status_code}"

    def test_assignment_endpoints(self):
        """測試作業相關 endpoints"""
        if not self.teacher_token:
            pytest.skip("No teacher token available")

        headers = {"Authorization": f"Bearer {self.teacher_token}"}

        # 取得作業列表
        response = client.get("/api/teachers/assignments", headers=headers)
        assert response.status_code == 200, "Assignments list should be accessible"

        assignments = response.json()
        if assignments:
            # 測試取得單一作業
            assignment_id = assignments[0]["id"]
            response = client.get(
                f"/api/teachers/assignments/{assignment_id}", headers=headers
            )
            assert (
                response.status_code == 200
            ), "Assignment details should be accessible"

    def test_router_prefixes(self):
        """檢查所有 router prefixes 是否正確設定"""
        from main import app

        # 取得所有註冊的路由
        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)

        # 檢查預期的路由模式
        expected_patterns = [
            "/api/auth/",
            "/api/teachers/",
            "/api/students/",
            "/api/public/",
        ]

        for pattern in expected_patterns:
            matching_routes = [r for r in routes if r.startswith(pattern)]
            assert len(matching_routes) > 0, f"No routes found with pattern {pattern}"

        # 檢查不應該存在的錯誤模式
        bad_patterns = [
            "/api/assignments/",  # 應該是 /api/teachers/assignments
            "/api/unassign/",  # 應該是 /api/teachers/unassign
        ]

        for pattern in bad_patterns:
            matching_routes = [r for r in routes if r.startswith(pattern)]
            assert (
                len(matching_routes) == 0
            ), f"Found incorrect route pattern {pattern}: {matching_routes}"


if __name__ == "__main__":
    # 執行測試
    test = TestAPIEndpoints()
    test.setup()

    print("🧪 測試 API Endpoints...")

    try:
        test.test_public_endpoints()
        print("✅ Public endpoints OK")
    except AssertionError as e:
        print(f"❌ Public endpoints failed: {e}")

    try:
        test.test_auth_endpoints()
        print("✅ Auth endpoints OK")
    except AssertionError as e:
        print(f"❌ Auth endpoints failed: {e}")

    try:
        test.test_teacher_endpoints()
        print("✅ Teacher endpoints OK")
    except AssertionError as e:
        print(f"❌ Teacher endpoints failed: {e}")

    try:
        test.test_assignment_endpoints()
        print("✅ Assignment endpoints OK")
    except AssertionError as e:
        print(f"❌ Assignment endpoints failed: {e}")

    try:
        test.test_router_prefixes()
        print("✅ Router prefixes OK")
    except AssertionError as e:
        print(f"❌ Router prefixes failed: {e}")

    print("\n✅ All endpoint tests completed!")
