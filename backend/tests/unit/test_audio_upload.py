"""
Audio upload service 單元測試 - 修正版本，完全 mock 外部依賴
"""
import os
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# noqa: E402
import pytest  # noqa: E402
from fastapi import HTTPException, UploadFile  # noqa: E402


# Mock google.cloud.storage before importing service
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.storage"] = MagicMock()

# noqa: E402
from services.audio_upload import (  # noqa: E402
    AudioUploadService,
    get_audio_upload_service,
)


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

    @patch.dict(os.environ, {"GCS_BUCKET_NAME": "custom-bucket"})
    def test_init_with_custom_bucket(self):
        """測試自定義 bucket 名稱"""
        service = AudioUploadService()
        assert service.bucket_name == "custom-bucket"

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
        """測試檔案過大"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=b"x" * (3 * 1024 * 1024))

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file)

        assert exc_info.value.status_code == 400
        assert "File too large" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_audio_duration_too_long(self, service):
        """測試音檔過長"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=b"test")

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_audio(mock_file, duration_seconds=31)

        assert exc_info.value.status_code == 400
        assert "Recording too long" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    async def test_upload_audio_success(self, mock_datetime, mock_uuid, service):
        """測試成功上傳"""
        # Setup mocks
        mock_uuid.return_value = "test-uuid"
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        service.storage_client = mock_client
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
    async def test_upload_audio_no_gcs_client(self, service):
        """測試 GCS client 無法初始化"""
        service.storage_client = None
        service._get_storage_client = Mock(return_value=None)

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
    async def test_upload_audio_gcs_failure(self, mock_datetime, mock_uuid, service):
        """測試 GCS 上傳失敗"""
        mock_uuid.return_value = "test-uuid"
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        service.storage_client = mock_client
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


class TestAudioUploadServiceSingleton:
    """測試 service singleton pattern"""

    def test_get_audio_upload_service_singleton(self):
        """測試 singleton 實例"""
        service1 = get_audio_upload_service()
        service2 = get_audio_upload_service()
        assert service1 is service2

    @patch.dict(os.environ, {"GCS_BUCKET_NAME": "test-bucket"})
    def test_get_audio_upload_service_with_env(self):
        """測試環境變數設定"""
        # Reset singleton
        import services.audio_upload

        services.audio_upload._audio_upload_service = None

        service = get_audio_upload_service()
        assert service.bucket_name == "test-bucket"
