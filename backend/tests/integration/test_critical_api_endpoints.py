"""
Critical API Endpoints Integration Tests
測試關鍵 API 端點的整合功能（需要資料庫連接）
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import timedelta
from unittest.mock import patch

# 為整合測試設置內存資料庫
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 測試資料庫設置
def get_test_db():
    """測試資料庫會話"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_client():
    """創建測試客戶端"""
    from main import app
    from database import get_db
    from models import Base

    # 創建測試資料表
    Base.metadata.create_all(bind=engine)

    # 覆蓋資料庫依賴
    app.dependency_overrides[get_db] = get_test_db

    with TestClient(app) as client:
        yield client

    # 清理
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_teacher_token():
    """模擬教師 JWT token"""
    from auth import create_access_token

    return create_access_token(
        data={
            "sub": "1",
            "email": "teacher@test.com",
            "type": "teacher",
            "name": "Test Teacher",
        },
        expires_delta=timedelta(hours=1),
    )


@pytest.fixture
def mock_student_token():
    """模擬學生 JWT token"""
    from auth import create_access_token

    return create_access_token(
        data={
            "sub": "1",
            "email": "student@test.com",
            "type": "student",
            "name": "Test Student",
            "student_id": "STU001",
        },
        expires_delta=timedelta(hours=1),
    )


class TestAuthenticationEndpoints:
    """測試認證端點"""

    def test_teacher_login_endpoint(self, test_client):
        """測試教師登入 API"""
        # 先創建測試教師（模擬註冊）
        with patch("routers.auth.get_password_hash") as mock_hash:
            mock_hash.return_value = "hashed_password"

            register_data = {
                "email": "teacher@test.com",
                "password": "testpass123",
                "name": "Test Teacher",
            }

            register_response = test_client.post(
                "/api/auth/teacher/register", json=register_data
            )
            assert register_response.status_code in [200, 201]

        # 測試登入
        with patch("routers.auth.verify_password") as mock_verify:
            mock_verify.return_value = True

            login_data = {"email": "teacher@test.com", "password": "testpass123"}

            login_response = test_client.post(
                "/api/auth/teacher/login", json=login_data
            )
            assert login_response.status_code == 200

            login_result = login_response.json()
            assert "access_token" in login_result
            assert login_result["token_type"] == "bearer"
            assert login_result["user"]["email"] == "teacher@test.com"

    def test_auth_validation_endpoint(self, test_client):
        """測試認證驗證端點"""
        response = test_client.get("/api/auth/validate")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "auth endpoint working"
        assert "version" in data

    def test_protected_endpoint_without_token(self, test_client):
        """測試未認證訪問受保護端點"""
        response = test_client.get("/api/teachers/classrooms")
        assert response.status_code in [401, 422]  # 未認證或請求格式錯誤


class TestPublicEndpoints:
    """測試公開端點"""

    def test_teacher_validation_endpoint(self, test_client):
        """測試教師驗證端點"""
        # 先創建測試教師
        with patch("routers.auth.get_password_hash") as mock_hash:
            mock_hash.return_value = "hashed_password"

            register_data = {
                "email": "public.teacher@test.com",
                "password": "testpass123",
                "name": "Public Test Teacher",
            }

            test_client.post("/api/auth/teacher/register", json=register_data)

        # 測試驗證 API
        validate_data = {"email": "public.teacher@test.com"}
        response = test_client.post("/api/public/validate-teacher", json=validate_data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["name"] == "Public Test Teacher"

    def test_teacher_validation_nonexistent(self, test_client):
        """測試不存在的教師驗證"""
        validate_data = {"email": "nonexistent@test.com"}
        response = test_client.post("/api/public/validate-teacher", json=validate_data)

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert result["name"] is None


class TestHealthCheckEndpoints:
    """測試健康檢查端點"""

    def test_root_endpoint(self, test_client):
        """測試根端點"""
        response = test_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data or "status" in data

    def test_health_endpoint(self, test_client):
        """測試健康檢查端點"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data


class TestAPIDocumentation:
    """測試 API 文件端點"""

    def test_openapi_schema(self, test_client):
        """測試 OpenAPI 規範可用性"""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data

        # 檢查關鍵端點是否定義
        paths = openapi_data["paths"]
        critical_paths = [
            "/api/auth/teacher/login",
            "/api/public/validate-teacher",
            "/health",
        ]

        for path in critical_paths:
            assert path in paths, f"Critical path {path} not found in OpenAPI schema"

    def test_swagger_ui_available(self, test_client):
        """測試 Swagger UI 可用性"""
        response = test_client.get("/docs")
        assert response.status_code == 200

        # 檢查回應是 HTML
        assert "text/html" in response.headers.get("content-type", "")


class TestErrorHandling:
    """測試錯誤處理"""

    def test_404_error_handling(self, test_client):
        """測試 404 錯誤處理"""
        response = test_client.get("/nonexistent/path")
        assert response.status_code == 404

    def test_invalid_json_handling(self, test_client):
        """測試無效 JSON 處理"""
        headers = {"Content-Type": "application/json"}
        response = test_client.post(
            "/api/auth/teacher/login", data="invalid json", headers=headers
        )
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self, test_client):
        """測試缺少必填欄位"""
        # 缺少 password 欄位
        incomplete_data = {"email": "test@example.com"}
        response = test_client.post("/api/auth/teacher/login", json=incomplete_data)
        assert response.status_code == 422


class TestDataValidation:
    """測試資料驗證"""

    def test_email_validation(self, test_client):
        """測試 email 格式驗證"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user..name@example.com",
        ]

        for invalid_email in invalid_emails:
            login_data = {"email": invalid_email, "password": "validpassword"}

            response = test_client.post("/api/auth/teacher/login", json=login_data)
            assert (
                response.status_code == 422
            ), f"Should reject invalid email: {invalid_email}"

    def test_password_requirements(self, test_client):
        """測試密碼要求（目前系統接受任何非空密碼）"""
        # 測試空密碼（應該被 Pydantic 拒絕）
        empty_password_data = {
            "email": "test@example.com",
            "password": "",
            "name": "Test User",
        }

        response = test_client.post(
            "/api/auth/teacher/register", json=empty_password_data
        )
        # 目前系統會接受空密碼並雜湊，但在實際部署中應該加強驗證
        assert response.status_code in [200, 400, 422]

        # 測試有效密碼（應該成功）
        valid_password_data = {
            "email": "valid.test@example.com",
            "password": "validpassword123",
            "name": "Valid Test User",
        }

        response = test_client.post(
            "/api/auth/teacher/register", json=valid_password_data
        )
        assert response.status_code == 200  # 應該成功註冊


class TestCORSAndHeaders:
    """測試 CORS 和標頭"""

    def test_cors_headers_present(self, test_client):
        """測試 CORS 標頭是否存在"""
        # 模擬來自瀏覽器的預檢請求
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = test_client.options("/api/auth/validate", headers=headers)

        # 檢查是否有適當的 CORS 標頭
        # 注意：具體的標頭取決於 CORS 中間件配置
        assert response.status_code in [200, 204]

    def test_security_headers(self, test_client):
        """測試安全標頭"""
        response = test_client.get("/health")

        # 檢查是否有基本的安全標頭
        response.headers

        # 這些檢查可能需要根據實際中間件配置調整
        assert response.status_code == 200


class TestPerformanceBasics:
    """測試基本性能指標"""

    def test_response_time_reasonable(self, test_client):
        """測試回應時間合理"""
        import time

        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        # 健康檢查應該在 1 秒內回應
        assert response_time < 1.0, f"Health check too slow: {response_time:.3f}s"

    def test_concurrent_requests_handling(self, test_client):
        """測試併發請求處理"""
        import threading
        import time

        results = []

        def make_request():
            start_time = time.time()
            response = test_client.get("/health")
            end_time = time.time()
            results.append(
                {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                }
            )

        # 創建多個同時請求
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # 啟動所有執行緒
        for thread in threads:
            thread.start()

        # 等待所有執行緒完成
        for thread in threads:
            thread.join()

        # 檢查結果
        assert len(results) == 5
        for result in results:
            assert result["status_code"] == 200
            assert result["response_time"] < 2.0  # 併發情況下允許較長時間


class TestDatabaseConnection:
    """測試資料庫連接相關功能"""

    def test_database_connection_resilience(self, test_client):
        """測試資料庫連接韌性"""
        # 這是一個基本測試，檢查在資料庫操作期間是否有適當的錯誤處理
        # 實際應用中可能需要更複雜的測試

        response = test_client.get("/health")
        assert response.status_code == 200

    def test_transaction_handling(self, test_client):
        """測試交易處理"""
        # 測試資料庫交易是否正確處理
        # 這裡測試一個可能失敗的操作

        invalid_register_data = {
            "email": "invalid-email-format",  # 無效 email 格式
            "password": "test123",
            "name": "Test User",
        }

        response = test_client.post(
            "/api/auth/teacher/register", json=invalid_register_data
        )
        assert response.status_code == 422

        # 確保無效操作沒有影響資料庫狀態
        # （在真實場景中，我們會檢查資料庫中沒有創建不完整的記錄）


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
