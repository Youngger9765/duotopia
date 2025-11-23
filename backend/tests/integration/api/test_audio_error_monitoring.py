"""Integration tests for Audio Error Monitoring API"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch


class TestAudioErrorStatsAPI:
    """測試錄音錯誤統計 API"""

    @pytest.mark.asyncio
    async def test_get_error_stats_requires_admin_auth(self, async_client: AsyncClient):
        """未登入應該返回 401"""
        response = await async_client.get("/api/admin/audio-errors/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_error_stats_requires_admin_role(
        self, async_client: AsyncClient, teacher_token: str
    ):
        """非 admin 角色應該返回 403"""
        response = await async_client.get(
            "/api/admin/audio-errors/stats",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.AudioErrorQueryService.get_error_stats")
    async def test_get_error_stats_success(
        self, mock_get_stats, async_client: AsyncClient, admin_token: str
    ):
        """Admin 用戶應該能夠取得統計資料"""
        # Mock 返回資料
        mock_get_stats.return_value = {
            "total_errors": 8,
            "period": {"start": "2025-11-16", "end": "2025-11-23"},
            "error_by_type": [
                {"error_type": "DECODE_ERROR", "count": 5},
                {"error_type": "NETWORK_ERROR", "count": 3},
            ],
            "error_by_date": [{"date": "2025-11-23", "count": 8}],
            "error_by_browser": [{"browser": "Chrome", "count": 8}],
            "data_available": True,
        }

        response = await async_client.get(
            "/api/admin/audio-errors/stats?days=7",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 8
        assert data["data_available"] is True
        assert len(data["error_by_type"]) == 2
        mock_get_stats.assert_called_once_with(days=7, teacher_id=None)

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.AudioErrorQueryService.get_error_stats")
    async def test_get_error_stats_with_teacher_filter(
        self, mock_get_stats, async_client: AsyncClient, admin_token: str
    ):
        """應該支援按老師 ID 過濾"""
        mock_get_stats.return_value = {
            "total_errors": 3,
            "data_available": True,
        }

        response = await async_client.get(
            "/api/admin/audio-errors/stats?days=7&teacher_id=88",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        mock_get_stats.assert_called_once_with(days=7, teacher_id=88)

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.AudioErrorQueryService.get_error_stats")
    async def test_get_error_stats_handles_service_error(
        self, mock_get_stats, async_client: AsyncClient, admin_token: str
    ):
        """應該處理服務錯誤"""
        mock_get_stats.return_value = {
            "error": "BigQuery client not available",
            "data_available": False,
        }

        response = await async_client.get(
            "/api/admin/audio-errors/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data_available"] is False
        assert "error" in data


class TestAudioErrorListAPI:
    """測試錄音錯誤列表 API"""

    @pytest.mark.asyncio
    async def test_get_error_list_requires_admin_auth(self, async_client: AsyncClient):
        """未登入應該返回 401"""
        response = await async_client.get("/api/admin/audio-errors/list")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_error_list_requires_admin_role(
        self, async_client: AsyncClient, teacher_token: str
    ):
        """非 admin 角色應該返回 403"""
        response = await async_client.get(
            "/api/admin/audio-errors/list",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.AudioErrorQueryService.get_error_list")
    @patch(
        "services.audio_error_query_service.AudioErrorQueryService._fetch_student_info"
    )
    async def test_get_error_list_success(
        self,
        mock_fetch_student_info,
        mock_get_list,
        async_client: AsyncClient,
        admin_token: str,
    ):
        """Admin 用戶應該能夠取得錯誤列表（含學生資料）"""
        # Mock 學生資料
        mock_fetch_student_info.return_value = {
            104: {
                "student_id": 104,
                "student_name": "陳慧文06",
                "classroom_id": 714,
                "classroom_name": "楊凱婷的班級",
                "teacher_id": 88,
                "teacher_name": "楊凱婷",
            }
        }

        # Mock 錯誤列表
        mock_get_list.return_value = {
            "total": 1,
            "data": [
                {
                    "timestamp": "2025-11-23T10:00:00",
                    "error_type": "DECODE_ERROR",
                    "error_message": "Cannot decode audio",
                    "student_id": 104,
                    "student_name": "陳慧文06",
                    "classroom_id": 714,
                    "classroom_name": "楊凱婷的班級",
                    "teacher_id": 88,
                    "teacher_name": "楊凱婷",
                    "assignment_id": 1234,
                    "audio_url": "https://storage.googleapis.com/audio.webm",
                    "browser": "Chrome",
                    "platform": "macOS",
                }
            ],
            "has_more": False,
        }

        response = await async_client.get(
            "/api/admin/audio-errors/list?days=7&limit=100&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1

        # 驗證包含學生資料
        error = data["data"][0]
        assert error["student_name"] == "陳慧文06"
        assert error["classroom_name"] == "楊凱婷的班級"
        assert error["teacher_name"] == "楊凱婷"

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.AudioErrorQueryService.get_error_list")
    async def test_get_error_list_with_filters(
        self, mock_get_list, async_client: AsyncClient, admin_token: str
    ):
        """應該支援搜尋和過濾"""
        mock_get_list.return_value = {"total": 0, "data": [], "has_more": False}

        response = await async_client.get(
            "/api/admin/audio-errors/list?days=7&search=DECODE&error_type=DECODE_ERROR",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        mock_get_list.assert_called_once()
        # 驗證參數
        call_kwargs = mock_get_list.call_args.kwargs
        assert call_kwargs["search"] == "DECODE"
        assert call_kwargs["error_type"] == "DECODE_ERROR"

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.AudioErrorQueryService.get_error_list")
    async def test_get_error_list_pagination(
        self, mock_get_list, async_client: AsyncClient, admin_token: str
    ):
        """應該支援分頁"""
        mock_get_list.return_value = {"total": 100, "data": [], "has_more": True}

        response = await async_client.get(
            "/api/admin/audio-errors/list?limit=20&offset=40",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True
        mock_get_list.assert_called_once()
        call_kwargs = mock_get_list.call_args.kwargs
        assert call_kwargs["limit"] == 20
        assert call_kwargs["offset"] == 40


class TestAudioErrorEnvironmentConfiguration:
    """測試環境變數配置"""

    @pytest.mark.asyncio
    @patch(
        "services.audio_error_query_service.AudioErrorQueryService._fetch_student_info"
    )
    async def test_fetch_student_info_uses_prod_db_url(self, mock_fetch):
        """應該使用 PROD_DATABASE_POOLER_URL 環境變數"""
        import os

        # 確認環境變數存在
        prod_url = os.getenv("PROD_DATABASE_POOLER_URL")
        assert prod_url is not None, "PROD_DATABASE_POOLER_URL must be set"
        assert "pooler.supabase.com" in prod_url, "Should use Supabase Pooler URL"

    def test_service_connects_to_production_supabase(self):
        """所有環境都應該連接到生產環境 Supabase"""
        import os

        # 驗證環境變數
        prod_url = os.getenv("PROD_DATABASE_POOLER_URL")
        assert prod_url is not None

        # 驗證是生產環境的 URL
        assert "szjeagbrubcibunofzud" in prod_url  # Production project ID


class TestBigQueryConnection:
    """測試 BigQuery 連接"""

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.bigquery.Client")
    async def test_bigquery_uses_correct_project(self, mock_client_class):
        """應該使用正確的 GCP 專案 ID"""
        from services.audio_error_query_service import AudioErrorQueryService

        service = AudioErrorQueryService()
        service._ensure_client()

        mock_client_class.assert_called_once_with(project="duotopia-472708")

    @pytest.mark.asyncio
    async def test_bigquery_table_path_is_correct(self):
        """應該使用正確的 BigQuery 表格路徑"""
        from services.audio_error_query_service import AudioErrorQueryService

        service = AudioErrorQueryService()

        expected_table = "duotopia-472708.duotopia_logs.audio_playback_errors"
        assert service.table_id == expected_table
