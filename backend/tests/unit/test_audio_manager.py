"""
Audio manager service 單元測試 - 目標覆蓋率 80%
"""
import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest  # noqa: E402
from services.audio_manager import AudioManager, get_audio_manager  # noqa: E402


class TestAudioManager:
    """測試 AudioManager"""

    @pytest.fixture
    def manager(self):
        """創建測試用 manager"""
        return AudioManager()

    def test_init(self):
        """測試初始化"""
        manager = AudioManager()
        assert manager.bucket_name == "duotopia-audio"
        assert manager.storage_client is None

    @patch.dict(os.environ, {"GCS_BUCKET_NAME": "custom-bucket"})
    def test_init_with_custom_bucket(self):
        """測試自定義 bucket 名稱"""
        manager = AudioManager()
        assert manager.bucket_name == "custom-bucket"

    @patch("services.audio_manager.storage.Client")
    def test_get_storage_client_success(self, mock_storage_client, manager):
        """測試 storage client 初始化成功"""
        mock_client = Mock()
        mock_storage_client.return_value = mock_client

        result = manager._get_storage_client()

        assert result == mock_client
        assert manager.storage_client == mock_client
        mock_storage_client.assert_called_once()

    @patch("services.audio_manager.storage.Client")
    def test_get_storage_client_cached(self, mock_storage_client, manager):
        """測試 storage client 快取機制"""
        mock_client = Mock()
        manager.storage_client = mock_client

        result = manager._get_storage_client()

        assert result == mock_client
        mock_storage_client.assert_not_called()

    @patch("services.audio_manager.storage.Client")
    @patch("builtins.print")
    def test_get_storage_client_failure(self, mock_print, mock_storage_client, manager):
        """測試 storage client 初始化失敗"""
        mock_storage_client.side_effect = Exception("Auth failed")

        result = manager._get_storage_client()

        assert result is None
        assert manager.storage_client is None
        mock_print.assert_called_once_with(
            "GCS client initialization failed: Auth failed"
        )

    def test_delete_old_audio_empty_url(self, manager):
        """測試刪除空 URL"""
        result = manager.delete_old_audio("")
        assert result is True

        result = manager.delete_old_audio(None)
        assert result is True

    @patch("services.audio_manager.storage.Client")
    def test_delete_old_audio_gcs_url_success(self, mock_storage_client, manager):
        """測試刪除 GCS URL 成功"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        url = "https://storage.googleapis.com/duotopia-audio/recordings/test.mp3"
        result = manager.delete_old_audio(url)

        assert result is True
        mock_client.bucket.assert_called_once_with("duotopia-audio")
        mock_bucket.blob.assert_called_once_with("recordings/test.mp3")
        mock_blob.delete.assert_called_once()

    @patch("services.audio_manager.storage.Client")
    @patch("builtins.print")
    def test_delete_old_audio_gcs_url_with_print(
        self, mock_print, mock_storage_client, manager
    ):
        """測試刪除 GCS URL 並檢查 print 輸出"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        url = "https://storage.googleapis.com/duotopia-audio/recordings/test.mp3"
        manager.delete_old_audio(url)

        mock_print.assert_called_once_with("Deleted GCS file: recordings/test.mp3")

    @patch("services.audio_manager.storage.Client")
    def test_delete_old_audio_gcs_url_no_client(self, mock_storage_client, manager):
        """測試 GCS client 初始化失敗時"""
        mock_storage_client.side_effect = Exception("Auth failed")

        url = "https://storage.googleapis.com/duotopia-audio/recordings/test.mp3"
        result = manager.delete_old_audio(url)

        assert result is False

    @patch("services.audio_manager.storage.Client")
    def test_delete_old_audio_gcs_url_invalid_path(self, mock_storage_client, manager):
        """測試無效的 GCS URL 路徑"""
        url = "https://storage.googleapis.com/invalid-path"
        result = manager.delete_old_audio(url)

        assert result is False

    @patch("os.path.exists")
    @patch("os.remove")
    def test_delete_old_audio_local_file_success(
        self, mock_remove, mock_exists, manager
    ):
        """測試刪除本地檔案成功"""
        mock_exists.return_value = True

        url = "/static/audio/test.mp3"
        result = manager.delete_old_audio(url)

        assert result is True
        mock_exists.assert_called_once_with("static/audio/test.mp3")
        mock_remove.assert_called_once_with("static/audio/test.mp3")

    @patch("os.path.exists")
    @patch("os.remove")
    @patch("builtins.print")
    def test_delete_old_audio_local_file_with_print(
        self, mock_print, mock_remove, mock_exists, manager
    ):
        """測試刪除本地檔案並檢查 print 輸出"""
        mock_exists.return_value = True

        url = "/static/audio/test.mp3"
        manager.delete_old_audio(url)

        mock_print.assert_called_once_with("Deleted local file: static/audio/test.mp3")

    @patch("os.path.exists")
    def test_delete_old_audio_local_file_not_exists(self, mock_exists, manager):
        """測試刪除不存在的本地檔案"""
        mock_exists.return_value = False

        url = "/static/audio/test.mp3"
        result = manager.delete_old_audio(url)

        assert result is False

    @patch("services.audio_manager.storage.Client")
    @patch("builtins.print")
    def test_delete_old_audio_gcs_exception(
        self, mock_print, mock_storage_client, manager
    ):
        """測試 GCS 刪除時發生異常"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.delete.side_effect = Exception("Delete failed")

        url = "https://storage.googleapis.com/duotopia-audio/recordings/test.mp3"
        result = manager.delete_old_audio(url)

        assert result is False
        mock_print.assert_called_once_with("Failed to delete audio file: Delete failed")

    @patch("os.path.exists")
    @patch("os.remove")
    @patch("builtins.print")
    def test_delete_old_audio_local_exception(
        self, mock_print, mock_remove, mock_exists, manager
    ):
        """測試本地檔案刪除時發生異常"""
        mock_exists.return_value = True
        mock_remove.side_effect = Exception("Permission denied")

        url = "/static/audio/test.mp3"
        result = manager.delete_old_audio(url)

        assert result is False
        mock_print.assert_called_once_with(
            "Failed to delete audio file: Permission denied"
        )

    def test_delete_old_audio_unknown_url_type(self, manager):
        """測試未知的 URL 類型"""
        url = "http://example.com/audio/test.mp3"
        result = manager.delete_old_audio(url)

        assert result is False

    @patch.object(AudioManager, "delete_old_audio")
    def test_update_audio_same_url(self, mock_delete, manager):
        """測試更新相同的 URL"""
        old_url = "https://storage.googleapis.com/duotopia-audio/test.mp3"
        new_url = "https://storage.googleapis.com/duotopia-audio/test.mp3"

        result = manager.update_audio(old_url, new_url)

        assert result == new_url
        mock_delete.assert_not_called()

    @patch.object(AudioManager, "delete_old_audio")
    def test_update_audio_different_url(self, mock_delete, manager):
        """測試更新不同的 URL"""
        old_url = "https://storage.googleapis.com/duotopia-audio/old.mp3"
        new_url = "https://storage.googleapis.com/duotopia-audio/new.mp3"

        result = manager.update_audio(old_url, new_url)

        assert result == new_url
        mock_delete.assert_called_once_with(old_url)

    @patch.object(AudioManager, "delete_old_audio")
    def test_update_audio_no_old_url(self, mock_delete, manager):
        """測試沒有舊 URL 的更新"""
        new_url = "https://storage.googleapis.com/duotopia-audio/new.mp3"

        result = manager.update_audio(None, new_url)

        assert result == new_url
        mock_delete.assert_not_called()

    @patch.object(AudioManager, "delete_old_audio")
    def test_update_audio_empty_old_url(self, mock_delete, manager):
        """測試空的舊 URL"""
        new_url = "https://storage.googleapis.com/duotopia-audio/new.mp3"

        result = manager.update_audio("", new_url)

        assert result == new_url
        mock_delete.assert_not_called()

    def test_get_gcs_url(self, manager):
        """測試取得 GCS URL"""
        blob_name = "recordings/test.mp3"
        result = manager.get_gcs_url(blob_name)

        assert (
            result
            == "https://storage.googleapis.com/duotopia-audio/recordings/test.mp3"
        )

    @patch.dict(os.environ, {"GCS_BUCKET_NAME": "custom-bucket"})
    def test_get_gcs_url_custom_bucket(self):
        """測試自定義 bucket 的 GCS URL"""
        manager = AudioManager()
        blob_name = "recordings/test.mp3"
        result = manager.get_gcs_url(blob_name)

        assert (
            result == "https://storage.googleapis.com/custom-bucket/recordings/test.mp3"
        )

    def test_get_gcs_url_with_spaces(self, manager):
        """測試包含空格的 blob 名稱"""
        blob_name = "recordings/test file.mp3"
        result = manager.get_gcs_url(blob_name)

        assert (
            result
            == "https://storage.googleapis.com/duotopia-audio/recordings/test file.mp3"
        )

    def test_get_gcs_url_empty_blob_name(self, manager):
        """測試空的 blob 名稱"""
        result = manager.get_gcs_url("")
        assert result == "https://storage.googleapis.com/duotopia-audio/"


class TestAudioManagerSingleton:
    """測試 AudioManager 單例模式"""

    def test_get_audio_manager_singleton(self):
        """測試單例模式"""
        # 重置全局變數
        import services.audio_manager

        services.audio_manager._audio_manager = None

        manager1 = get_audio_manager()
        manager2 = get_audio_manager()

        assert manager1 is manager2
        assert isinstance(manager1, AudioManager)

    def test_get_audio_manager_persistence(self):
        """測試單例持久性"""
        import services.audio_manager

        services.audio_manager._audio_manager = None

        manager1 = get_audio_manager()
        manager1.custom_attribute = "test_value"

        manager2 = get_audio_manager()
        assert hasattr(manager2, "custom_attribute")
        assert manager2.custom_attribute == "test_value"

    @patch.dict(os.environ, {"GCS_BUCKET_NAME": "test-bucket"})
    def test_get_audio_manager_with_env(self):
        """測試帶環境變數的單例"""
        import services.audio_manager

        services.audio_manager._audio_manager = None

        manager = get_audio_manager()
        assert manager.bucket_name == "test-bucket"
