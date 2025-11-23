"""Unit tests for Audio Error Query Service"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.audio_error_query_service import AudioErrorQueryService


class TestAudioErrorQueryServiceInit:
    """測試 AudioErrorQueryService 初始化"""

    def test_init_sets_project_id_from_env(self):
        """應該從環境變數讀取 project_id"""
        with patch.dict("os.environ", {"GCP_PROJECT_ID": "test-project"}):
            service = AudioErrorQueryService()
            assert service.project_id == "test-project"

    def test_init_uses_default_project_id(self):
        """沒有環境變數時應該使用預設 project_id"""
        with patch.dict("os.environ", {}, clear=True):
            service = AudioErrorQueryService()
            assert service.project_id == "duotopia-472708"

    def test_init_sets_table_id_correctly(self):
        """應該正確設定 table_id"""
        service = AudioErrorQueryService()
        assert "duotopia_logs.audio_playback_errors" in service.table_id

    def test_init_client_is_none_before_initialization(self):
        """初始化時 client 應該是 None（延遲初始化）"""
        service = AudioErrorQueryService()
        assert service.client is None
        assert service._initialized is False


class TestAudioErrorQueryServiceClientInit:
    """測試 BigQuery client 延遲初始化"""

    @patch("services.audio_error_query_service.bigquery.Client")
    def test_ensure_client_initializes_successfully(self, mock_client_class):
        """_ensure_client 應該成功初始化 BigQuery client"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = AudioErrorQueryService()
        service._ensure_client()

        assert service.client == mock_client
        assert service._initialized is True
        mock_client_class.assert_called_once_with(project=service.project_id)

    @patch("services.audio_error_query_service.bigquery.Client")
    def test_ensure_client_handles_initialization_failure(self, mock_client_class):
        """_ensure_client 應該處理初始化失敗"""
        mock_client_class.side_effect = Exception("Connection failed")

        service = AudioErrorQueryService()
        service._ensure_client()

        assert service.client is None
        assert service._initialized is False

    @patch("services.audio_error_query_service.bigquery.Client")
    def test_ensure_client_only_initializes_once(self, mock_client_class):
        """_ensure_client 應該只初始化一次"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = AudioErrorQueryService()
        service._ensure_client()
        service._ensure_client()  # 第二次呼叫

        # 只應該呼叫一次
        mock_client_class.assert_called_once()


class TestFetchStudentInfo:
    """測試從生產環境 Supabase 查詢學生資料"""

    @pytest.mark.asyncio
    async def test_fetch_student_info_requires_prod_db_url(self):
        """應該從環境變數讀取 PROD_DATABASE_POOLER_URL"""
        with patch.dict("os.environ", {}, clear=True):
            service = AudioErrorQueryService()
            result = await service._fetch_student_info([1, 2, 3])

            # 沒有環境變數應該返回空字典
            assert result == {}

    @pytest.mark.asyncio
    @patch("sqlalchemy.orm.Session")
    @patch("sqlalchemy.create_engine")
    async def test_fetch_student_info_with_valid_url(
        self, mock_create_engine, mock_session_class
    ):
        """有正確的環境變數應該查詢學生資料"""
        # Mock database session
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Mock query results
        mock_row = Mock()
        mock_row.student_id = 104
        mock_row.student_name = "測試學生"
        mock_row.classroom_id = 714
        mock_row.classroom_name = "測試班級"
        mock_row.teacher_id = 88
        mock_row.teacher_name = "測試老師"

        mock_result = Mock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        with patch.dict(
            "os.environ",
            {"PROD_DATABASE_POOLER_URL": "postgresql://test:test@localhost/test"},
        ):
            service = AudioErrorQueryService()
            result = await service._fetch_student_info([104])

            assert 104 in result
            assert result[104]["student_name"] == "測試學生"
            assert result[104]["classroom_name"] == "測試班級"
            assert result[104]["teacher_name"] == "測試老師"

    @pytest.mark.asyncio
    @patch("sqlalchemy.create_engine")
    async def test_fetch_student_info_handles_db_error(self, mock_create_engine):
        """應該處理資料庫連接錯誤"""
        mock_create_engine.side_effect = Exception("Database connection failed")

        with patch.dict(
            "os.environ",
            {"PROD_DATABASE_POOLER_URL": "postgresql://test:test@localhost/test"},
        ):
            service = AudioErrorQueryService()
            result = await service._fetch_student_info([104])

            # 發生錯誤應該返回空字典
            assert result == {}


class TestGetErrorStats:
    """測試取得錄音錯誤統計資料"""

    @pytest.mark.asyncio
    async def test_get_error_stats_returns_empty_when_client_unavailable(self):
        """BigQuery client 不可用時應該返回錯誤訊息"""
        service = AudioErrorQueryService()
        # 不初始化 client

        result = await service.get_error_stats(days=7)

        assert result["data_available"] is False
        assert "error" in result

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.bigquery.Client")
    async def test_get_error_stats_returns_empty_when_table_not_exists(
        self, mock_client_class
    ):
        """表格不存在時應該返回空統計"""
        mock_client = Mock()
        mock_client.get_table.side_effect = Exception("Table not found")
        mock_client_class.return_value = mock_client

        service = AudioErrorQueryService()
        service._ensure_client()

        result = await service.get_error_stats(days=7)

        assert result["data_available"] is False
        assert result["total_errors"] == 0
        assert result["error_by_type"] == []


class TestGetErrorList:
    """測試取得錄音錯誤詳細列表"""

    @pytest.mark.asyncio
    async def test_get_error_list_returns_empty_when_client_unavailable(self):
        """BigQuery client 不可用時應該返回空列表"""
        service = AudioErrorQueryService()
        # 不初始化 client

        result = await service.get_error_list(days=7)

        assert "error" in result
        assert result["data"] == []

    @pytest.mark.asyncio
    @patch("services.audio_error_query_service.bigquery.Client")
    async def test_get_error_list_returns_empty_when_table_not_exists(
        self, mock_client_class
    ):
        """表格不存在時應該返回空列表"""
        mock_client = Mock()
        mock_client.get_table.side_effect = Exception("Table not found")
        mock_client_class.return_value = mock_client

        service = AudioErrorQueryService()
        service._ensure_client()

        result = await service.get_error_list(days=7)

        assert result["total"] == 0
        assert result["data"] == []
        assert result["has_more"] is False


class TestGetAudioErrorService:
    """測試單例模式"""

    def test_get_audio_error_service_returns_singleton(self):
        """應該返回同一個實例（單例模式）"""
        from services.audio_error_query_service import get_audio_error_service

        service1 = get_audio_error_service()
        service2 = get_audio_error_service()

        assert service1 is service2
