"""
GCS Upload 整合測試 - 真實連線測試
只在有 GCS 認證的環境執行（CI/CD 或本地有設定）
"""
import os
import pytest
from fastapi import UploadFile
from unittest.mock import Mock

# Skip if no GCS credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("GCS_BUCKET_NAME") and not os.path.exists("service-account-key.json"),
    reason="GCS credentials not available",
)


@pytest.mark.integration
@pytest.mark.gcs
class TestGCSUploadIntegration:
    """測試真實 GCS 上傳功能"""

    @pytest.fixture
    def setup_test_env(self):
        """設定測試環境"""
        # 保存原始環境變數
        original_env = os.environ.get("ENVIRONMENT")

        # 設為 staging 以使用 GCS
        os.environ["ENVIRONMENT"] = "staging"

        yield

        # 恢復原始環境
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        else:
            os.environ.pop("ENVIRONMENT", None)

    @pytest.mark.asyncio
    async def test_real_gcs_upload(self, setup_test_env):
        """測試真實的 GCS 上傳"""
        from services.audio_upload import AudioUploadService

        service = AudioUploadService()

        # 檢查是否能初始化 GCS client
        client = service._get_storage_client()
        if not client:
            pytest.skip("Cannot initialize GCS client")

        # 創建測試檔案
        test_content = b"test audio content for integration test"
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = pytest.AsyncMock(return_value=test_content)

        try:
            # 執行上傳
            url = await service.upload_audio(
                mock_file, duration_seconds=5, content_id=999, item_index=0
            )

            # 驗證 URL 格式
            assert url.startswith(
                "https://storage.googleapis.com/duotopia-audio/recordings/"
            )
            assert "recording_c999_i0_" in url
            assert url.endswith(".webm")

            # 可選：測試檔案是否真的存在
            # 這需要額外的權限來讀取

        except Exception as e:
            # 如果是權限問題，跳過測試
            if "403" in str(e) or "Permission" in str(e):
                pytest.skip(f"GCS permission denied: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_gcs_bucket_exists(self, setup_test_env):
        """測試 GCS bucket 是否存在"""
        try:
            from google.cloud import storage

            client = storage.Client()
            bucket_name = os.getenv("GCS_BUCKET_NAME", "duotopia-audio")
            bucket = client.bucket(bucket_name)

            # 嘗試獲取 bucket metadata
            assert bucket.exists()

        except ImportError:
            pytest.skip("google-cloud-storage not installed")
        except Exception as e:
            if "403" in str(e):
                pytest.skip(f"No permission to check bucket: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_gcs_upload_with_cleanup(self, setup_test_env):
        """測試上傳並清理測試檔案"""
        from services.audio_upload import AudioUploadService

        service = AudioUploadService()
        client = service._get_storage_client()

        if not client:
            pytest.skip("Cannot initialize GCS client")

        # 使用測試檔案
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.read = pytest.AsyncMock(return_value=b"test")

        uploaded_blob_name = None

        try:
            # 上傳檔案
            url = await service.upload_audio(mock_file)

            # 從 URL 提取 blob name
            uploaded_blob_name = url.split("/recordings/")[-1]

            # 驗證檔案存在
            bucket = client.bucket(service.bucket_name)
            blob = bucket.blob(f"recordings/{uploaded_blob_name}")
            assert blob.exists()

        finally:
            # 清理測試檔案
            if uploaded_blob_name and client:
                try:
                    bucket = client.bucket(service.bucket_name)
                    blob = bucket.blob(f"recordings/{uploaded_blob_name}")
                    blob.delete()
                    print(f"Cleaned up test file: {uploaded_blob_name}")
                except Exception as e:
                    print(f"Failed to clean up test file: {e}")


# 標記為整合測試，可以單獨執行
# pytest -m integration tests/integration/test_gcs_upload_real.py
# 或跳過整合測試
# pytest -m "not integration"
