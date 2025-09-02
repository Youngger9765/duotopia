"""
Router 配置測試
確保所有 router 都有正確的配置，避免重構時出錯
"""
import pytest
import importlib
import os
import sys
from pathlib import Path

# 添加 backend 到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestRouterConfiguration:
    """測試所有 router 的配置是否正確"""

    def test_router_prefixes(self):
        """測試所有 router 的 prefix 設定"""
        # 預期的 router 配置
        expected_configs = {
            "auth": {"prefix": "/api/auth", "tags": ["authentication"]},
            "public": {"prefix": "/api/public", "tags": ["public"]},
            "students": {"prefix": "/api/students", "tags": ["students"]},
            "teachers": {"prefix": "/api/teachers", "tags": ["teachers"]},
            "assignments": {
                "prefix": "/api/teachers",  # 應該在 teachers 下
                "tags": ["assignments"],
            },
            "unassign": {
                "prefix": "/api/teachers",  # 應該在 teachers 下
                "tags": ["unassign"],
            },
        }

        errors = []

        for module_name, expected in expected_configs.items():
            try:
                # 動態載入 router 模組
                module = importlib.import_module(f"routers.{module_name}")

                # 檢查是否有 router 物件
                assert hasattr(module, "router"), f"{module_name} 沒有 router 物件"

                router = module.router

                # 檢查 prefix
                actual_prefix = getattr(router, "prefix", None)
                if actual_prefix != expected["prefix"]:
                    errors.append(
                        f"{module_name}: prefix 錯誤 - "
                        f"預期 '{expected['prefix']}', 實際 '{actual_prefix}'"
                    )

                # 檢查 tags
                actual_tags = getattr(router, "tags", [])
                if actual_tags != expected["tags"]:
                    errors.append(
                        f"{module_name}: tags 錯誤 - "
                        f"預期 {expected['tags']}, 實際 {actual_tags}"
                    )

            except ImportError as e:
                errors.append(f"{module_name}: 無法載入模組 - {e}")
            except Exception as e:
                errors.append(f"{module_name}: 檢查失敗 - {e}")

        # 如果有錯誤，顯示所有錯誤
        if errors:
            error_msg = "\n".join(errors)
            pytest.fail(f"Router 配置錯誤:\n{error_msg}")

    def test_no_conflicting_routes(self):
        """測試沒有衝突的路由"""
        from main import app

        # 收集所有路由
        routes = {}
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                for method in route.methods:
                    key = f"{method} {route.path}"
                    if key in routes:
                        pytest.fail(f"發現重複路由: {key}")
                    routes[key] = route

        # 檢查特定的路由是否存在
        required_routes = [
            "GET /api/teachers/assignments",
            "POST /api/teachers/assignments",
            "GET /api/teachers/assignments/{assignment_id}",
            "POST /api/auth/teacher/login",
            "GET /api/teachers/classrooms",
            "GET /api/teachers/programs",
        ]

        for required in required_routes:
            method, path = required.split(" ", 1)
            # 檢查是否有匹配的路由（考慮參數）
            found = False
            for route_key in routes:
                if method in route_key:
                    route_path = route_key.replace(f"{method} ", "")
                    # 簡單的路徑匹配（忽略參數差異）
                    if path.replace("{", "").replace("}", "") in route_path.replace(
                        "{", ""
                    ).replace("}", ""):
                        found = True
                        break

            if not found:
                pytest.fail(f"找不到必要的路由: {required}")

    def test_router_imports_in_main(self):
        """測試 main.py 是否正確引入所有 router"""
        with open("main.py", "r") as f:
            main_content = f.read()

        # 檢查必要的 import
        required_imports = [
            "from routers import auth",
            "from routers import students",
            "from routers import teachers",
            "from routers import public",
            "from routers import assignments",
            "from routers import unassign",
        ]

        for import_stmt in required_imports:
            if import_stmt not in main_content:
                pytest.fail(f"main.py 缺少引入: {import_stmt}")

        # 檢查 router 是否被註冊
        required_includes = [
            "app.include_router(auth.router)",
            "app.include_router(students.router)",
            "app.include_router(teachers.router)",
            "app.include_router(public.router)",
            "app.include_router(assignments.router)",
            "app.include_router(unassign.router)",
        ]

        for include_stmt in required_includes:
            if include_stmt not in main_content:
                pytest.fail(f"main.py 沒有註冊 router: {include_stmt}")

    def test_router_endpoints_accessible(self):
        """測試 router endpoints 是否可訪問"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # 測試公開端點
        public_endpoints = [
            ("/", 200),
            ("/health", 200),
            ("/api/public/teachers", 200),
        ]

        for endpoint, expected_status in public_endpoints:
            response = client.get(endpoint)
            assert (
                response.status_code == expected_status
            ), f"{endpoint} 返回 {response.status_code}, 預期 {expected_status}"

        # 測試需要認證的端點（應該返回 401 或 422）
        auth_required_endpoints = [
            "/api/teachers/assignments",
            "/api/teachers/classrooms",
            "/api/teachers/programs",
        ]

        for endpoint in auth_required_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [
                401,
                422,
                403,
            ], f"{endpoint} 應該需要認證，但返回 {response.status_code}"


def test_critical_api_flow():
    """測試關鍵 API 流程，確保 router 配置正確"""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)

    # 1. 測試教師登入
    login_response = client.post(
        "/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    assert login_response.status_code == 200, "教師登入失敗"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 測試取得作業列表（測試修復後的 router）
    assignments_response = client.get("/api/teachers/assignments", headers=headers)
    assert (
        assignments_response.status_code == 200
    ), f"無法取得作業列表: {assignments_response.status_code}"

    assignments = assignments_response.json()
    assert isinstance(assignments, list), "作業列表應該是陣列"

    # 3. 如果有作業，測試取得詳情
    if assignments:
        assignment_id = assignments[0]["id"]
        detail_response = client.get(
            f"/api/teachers/assignments/{assignment_id}", headers=headers
        )
        assert (
            detail_response.status_code == 200
        ), f"無法取得作業詳情: {detail_response.status_code}"

    print("✅ 關鍵 API 流程測試通過！")


if __name__ == "__main__":
    # 直接執行測試
    test = TestRouterConfiguration()

    print("🧪 測試 Router 配置...")

    try:
        test.test_router_prefixes()
        print("✅ Router prefixes 正確")
    except AssertionError as e:
        print(f"❌ Router prefixes 錯誤: {e}")

    try:
        test.test_no_conflicting_routes()
        print("✅ 沒有衝突的路由")
    except AssertionError as e:
        print(f"❌ 路由衝突: {e}")

    try:
        test.test_router_imports_in_main()
        print("✅ main.py imports 正確")
    except AssertionError as e:
        print(f"❌ main.py imports 錯誤: {e}")

    try:
        test.test_router_endpoints_accessible()
        print("✅ Router endpoints 可訪問")
    except AssertionError as e:
        print(f"❌ Router endpoints 錯誤: {e}")

    try:
        test_critical_api_flow()
        print("✅ 關鍵 API 流程正常")
    except AssertionError as e:
        print(f"❌ API 流程錯誤: {e}")

    print("\n✅ 所有 Router 測試完成！")
