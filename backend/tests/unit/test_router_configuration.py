"""
Router 配置測試
確保所有 router 都有正確的配置，避免重構時出錯
"""

import pytest
import importlib
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

        # 檢查必要的 router 名稱是否在 import 區域中出現
        required_routers = [
            "auth",
            "students",
            "teachers",
            "public",
            "assignments",
            "unassign",
        ]

        # 檢查是否有 from routers import 語句包含這些模組
        import_section = main_content[
            main_content.find("from routers import") : main_content.find(
                "app = FastAPI"
            )
        ]

        for router_name in required_routers:
            if router_name not in import_section:
                pytest.fail(f"main.py 缺少引入 router: {router_name}")

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

        # 測試基本端點
        basic_endpoints = [
            ("/", 200),
            ("/health", 200),
        ]

        for endpoint, expected_status in basic_endpoints:
            response = client.get(endpoint)
            assert (
                response.status_code == expected_status
            ), f"{endpoint} 返回 {response.status_code}, 預期 {expected_status}"

        # 測試 public 端點需要參數，所以只檢查 404 不是 500 (表示路由存在)
        public_response = client.get("/api/public/teacher-classrooms")
        # GET 請求沒有 teacher_email 參數會返回 422 (驗證錯誤)，這表示路由存在
        assert public_response.status_code in [
            422,
            400,
        ], f"/api/public/teacher-classrooms 返回 {public_response.status_code}，應該是參數錯誤而不是 404"

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

    # 1. 測試基本端點存在
    basic_endpoints = [("/", 200), ("/health", 200)]

    for endpoint, expected_status in basic_endpoints:
        response = client.get(endpoint)
        assert (
            response.status_code == expected_status
        ), f"基本端點 {endpoint} 失敗: {response.status_code}"

    # 2. 測試 OpenAPI 規範可用 (表示所有 router 正確載入)
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200, "OpenAPI 規範不可用"

    openapi_data = openapi_response.json()

    # 檢查關鍵端點是否在 OpenAPI 中定義
    required_paths = [
        "/api/auth/teacher/login",
        "/api/auth/student/login",
        "/api/auth/validate",
        "/api/public/validate-teacher",
    ]

    available_paths = list(openapi_data.get("paths", {}).keys())

    for path in required_paths:
        assert path in available_paths, f"關鍵端點 {path} 未在 OpenAPI 中定義"

    print("✅ 關鍵 API 流程測試通過！所有 router 正確配置。")


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
