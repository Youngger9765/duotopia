"""
Audio upload service 單元測試 - 目標覆蓋率 80%
"""
# flake8: noqa: E402
import os
import sys
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest  # noqa: E402
from fastapi import HTTPException, UploadFile  # noqa: E402
from services.audio_upload import (
    AudioUploadService,
    get_audio_upload_service,
)  # noqa: E402


class TestAudioUploadService:
    """測試 AudioUploadService"""

    @pytest.fixture
    def service(self):
        """創建測試用 service"""
        return AudioUploadService()

    @pytest.fixture
    def mock_upload_file(self):
        """創建 mock UploadFile"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=b"test audio content")
        return mock_file

    def test_init(self):
        """測試初始化"""
        service = AudioUploadService()
        assert service.bucket_name == "duotopia-audio"
        assert service.storage_client is None
        assert service.max_file_size == 2 * 1024 * 1024
        assert "audio/webm" in service.allowed_formats
        assert "audio/mp3" in service.allowed_formats
        assert "video/webm" in service.allowed_formats

    @patch.dict(os.environ, {"GCS_BUCKET_NAME": "custom-bucket"})
    def test_init_with_custom_bucket(self):
        """測試自定義 bucket 名稱"""
        service = AudioUploadService()
        assert service.bucket_name == "custom-bucket"

    @patch("os.path.exists")
    @patch("services.audio_upload.storage.Client.from_service_account_json")
    def test_get_storage_client_with_service_account(self, mock_from_json, mock_exists):
        """測試使用 service account 初始化 client"""
        mock_exists.return_value = True
        mock_client = Mock()
        mock_from_json.return_value = mock_client

        service = AudioUploadService()
        result = service._get_storage_client()

        assert result == mock_client
        assert service.storage_client == mock_client
        mock_from_json.assert_called_once()

    @patch("os.path.exists")
    @patch("services.audio_upload.storage.Client.from_service_account_json")
    @patch("builtins.print")
    def test_get_storage_client_with_service_account_print(
        self, mock_print, mock_from_json, mock_exists
    ):
        """測試 service account 初始化的 print 輸出"""
        mock_exists.return_value = True
        mock_client = Mock()
        mock_from_json.return_value = mock_client

        service = AudioUploadService()
        service._get_storage_client()

        # 檢查 print 輸出
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any(
            "GCS client initialized with service account" in str(call)
            for call in print_calls
        )

    @patch("os.path.exists")
    @patch("services.audio_upload.storage.Client")
    def test_get_storage_client_default_credentials(
        self, mock_storage_client, mock_exists
    ):
        """測試使用預設認證初始化 client"""
        mock_exists.return_value = False
        mock_client = Mock()
        mock_storage_client.return_value = mock_client

        service = AudioUploadService()
        result = service._get_storage_client()

        assert result == mock_client
        assert service.storage_client == mock_client
        mock_storage_client.assert_called_once()

    @patch("os.path.exists")
    @patch("services.audio_upload.storage.Client")
    @patch("builtins.print")
    def test_get_storage_client_default_print(
        self, mock_print, mock_storage_client, mock_exists
    ):
        """測試預設認證的 print 輸出"""
        mock_exists.return_value = False
        mock_client = Mock()
        mock_storage_client.return_value = mock_client

        service = AudioUploadService()
        service._get_storage_client()

        mock_print.assert_called_with("GCS client initialized with default credentials")

    @patch("os.path.exists")
    @patch("services.audio_upload.storage.Client")
    @patch("builtins.print")
    def test_get_storage_client_failure(
        self, mock_print, mock_storage_client, mock_exists
    ):
        """測試 client 初始化失敗"""
        mock_exists.return_value = False
        mock_storage_client.side_effect = Exception("Auth failed")

        service = AudioUploadService()
        result = service._get_storage_client()

        assert result is None
        assert service.storage_client is None
        mock_print.assert_called_with("GCS client initialization failed: Auth failed")

    def test_get_storage_client_cached(self):
        """測試 client 快取機制"""
        service = AudioUploadService()
        mock_client = Mock()
        service.storage_client = mock_client

        result = service._get_storage_client()

        assert result == mock_client

    @pytest.mark.asyncio
    async def test_upload_audio_invalid_content_type(self, service):
        """測試無效的檔案類型"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "text/plain"

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file)

        assert exc_info.value.status_code == 400
        assert "Invalid file type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_audio_file_too_large(self, service):
        """測試檔案太大"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        # 創建超過 2MB 的內容
        large_content = b"x" * (3 * 1024 * 1024)
        mock_file.read = AsyncMock(return_value=large_content)

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file)

        assert exc_info.value.status_code == 400
        assert "File too large" in exc_info.value.detail
        assert "2.0MB" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_audio_duration_too_long(self, service, mock_upload_file):
        """測試錄音時間太長"""
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_upload_file, duration_seconds=35)

        assert exc_info.value.status_code == 400
        assert "Recording too long" in exc_info.value.detail
        assert "30 seconds" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    @patch("services.audio_upload.storage.Client")
    async def test_upload_audio_success(
        self, mock_storage_client, mock_datetime, mock_uuid, service
    ):
        """測試成功上傳音檔"""
        # Mock UUID 和時間
        mock_uuid.return_value = "test-uuid"
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        # Mock upload file
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=b"test audio")

        result = await service.upload_audio(mock_file, duration_seconds=20)

        expected_url = (
            "https://storage.googleapis.com/duotopia-audio/recordings/"
            "recording_20240101_120000_test-uuid.webm"
        )
        assert result == expected_url

        mock_blob.upload_from_string.assert_called_once_with(
            b"test audio", content_type="audio/webm"
        )
        mock_blob.make_public.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    @patch("services.audio_upload.storage.Client")
    async def test_upload_audio_with_content_id(
        self, mock_storage_client, mock_datetime, mock_uuid, service
    ):
        """測試帶 content_id 和 item_index 的上傳"""
        mock_uuid.return_value = "test-uuid"
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/mp4"
        mock_file.read = AsyncMock(return_value=b"test audio")

        result = await service.upload_audio(mock_file, content_id=123, item_index=5)

        expected_url = (
            "https://storage.googleapis.com/duotopia-audio/recordings/"
            "recording_c123_i5_20240101_120000_test-uuid.m4a"
        )
        assert result == expected_url

    @pytest.mark.asyncio
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    @patch("services.audio_upload.storage.Client")
    async def test_upload_audio_different_content_types(
        self, mock_storage_client, mock_datetime, mock_uuid, service
    ):
        """測試不同的 content type 對應的擴展名"""
        mock_uuid.return_value = "test-uuid"
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        test_cases = [
            ("audio/webm", "webm"),
            ("video/webm", "webm"),
            ("audio/mp4", "m4a"),
            ("audio/ogg", "ogg"),
            ("audio/opus", "opus"),
            ("audio/mpeg", "mp3"),
            ("audio/wav", "wav"),
            ("audio/x-m4a", "webm"),  # 不在 ext_map 中，使用預設
        ]

        for content_type, expected_ext in test_cases:
            mock_file = Mock(spec=UploadFile)
            mock_file.content_type = content_type
            mock_file.read = AsyncMock(return_value=b"test")

            result = await service.upload_audio(mock_file)
            assert result.endswith(f".{expected_ext}")

    @pytest.mark.asyncio
    @patch("services.audio_upload.storage.Client")
    async def test_upload_audio_no_gcs_client(self, mock_storage_client, service):
        """測試 GCS client 無法初始化"""
        mock_storage_client.side_effect = Exception("Auth failed")

        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=b"test")

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file)

        assert exc_info.value.status_code == 500
        assert "GCS service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    @patch("services.audio_upload.storage.Client")
    async def test_upload_audio_gcs_upload_failure(
        self, mock_storage_client, mock_datetime, mock_uuid, service
    ):
        """測試 GCS 上傳失敗"""
        mock_uuid.return_value = "test-uuid"
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_string.side_effect = Exception("Upload failed")

        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=b"test")

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file)

        assert exc_info.value.status_code == 500
        assert "Failed to upload recording" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    @patch("services.audio_upload.storage.Client")
    @patch("builtins.print")
    async def test_upload_audio_gcs_failure_print(
        self, mock_print, mock_storage_client, mock_datetime, mock_uuid, service
    ):
        """測試 GCS 上傳失敗的 print 輸出"""
        mock_uuid.return_value = "test-uuid"
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_string.side_effect = Exception("Upload failed")

        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=b"test")

        with pytest.raises(HTTPException):
            await service.upload_audio(mock_file)

        mock_print.assert_called_with("GCS upload failed: Upload failed")

    @pytest.mark.asyncio
    async def test_upload_audio_general_exception(self, service):
        """測試一般異常處理"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(side_effect=Exception("Read failed"))

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file)

        assert exc_info.value.status_code == 500
        assert "Upload failed: Read failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_audio_http_exception_passthrough(self, service):
        """測試 HTTPException 直接傳遞"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "invalid/type"

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file)

        # 確保是原本的 HTTPException，不是被包裝的
        assert exc_info.value.status_code == 400
        assert "Invalid file type" in exc_info.value.detail


class TestAudioUploadServiceSingleton:
    """測試 AudioUploadService 單例模式"""

    def test_get_audio_upload_service_singleton(self):
        """測試單例模式"""
        # 重置全局變數
        import services.audio_upload

        services.audio_upload._audio_upload_service = None

        service1 = get_audio_upload_service()
        service2 = get_audio_upload_service()

        assert service1 is service2
        assert isinstance(service1, AudioUploadService)

    def test_get_audio_upload_service_persistence(self):
        """測試單例持久性"""
        import services.audio_upload

        services.audio_upload._audio_upload_service = None

        service1 = get_audio_upload_service()
        service1.custom_attribute = "test_value"

        service2 = get_audio_upload_service()
        assert hasattr(service2, "custom_attribute")
        assert service2.custom_attribute == "test_value"

    @patch.dict(os.environ, {"GCS_BUCKET_NAME": "test-bucket"})
    def test_get_audio_upload_service_with_env(self):
        """測試帶環境變數的單例"""
        import services.audio_upload

        services.audio_upload._audio_upload_service = None

        service = get_audio_upload_service()
        assert service.bucket_name == "test-bucket"
