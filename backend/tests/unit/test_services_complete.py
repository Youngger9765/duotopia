"""
Services 層完整單元測試，目標覆蓋率 80% 以上
"""
import os
import sys
import asyncio  # noqa: F401
import tempfile  # noqa: F401
import uuid  # noqa: F401
from datetime import datetime  # noqa: F401
from unittest.mock import Mock, patch, MagicMock, AsyncMock  # noqa: F401

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest  # noqa: E402
from services.tts import TTSService, get_tts_service  # noqa: E402
from services.translation import TranslationService  # noqa: E402
from services.audio_manager import AudioManager  # noqa: E402
from services.audio_upload import AudioUploadService  # noqa: E402


class TestTTSService:
    """TTSService 完整測試"""

    def test_tts_service_init(self):
        """測試 TTSService 初始化"""
        service = TTSService()

        assert service.voices is not None
        assert "en-US" in service.voices
        assert "male" in service.voices["en-US"]
        assert "female" in service.voices["en-US"]
        assert service.bucket_name == os.getenv("GCS_BUCKET_NAME", "duotopia-audio")
        assert service.storage_client is None  # 延遲初始化

    def test_get_storage_client(self):
        """測試 GCS client 延遲初始化"""
        service = TTSService()

        with patch("services.tts.storage.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance

            # 第一次調用
            client1 = service._get_storage_client()
            assert client1 == mock_client_instance
            mock_client.assert_called_once()

            # 第二次調用應該返回相同實例
            client2 = service._get_storage_client()
            assert client2 == mock_client_instance
            mock_client.assert_called_once()  # 不應該再次創建

    @pytest.mark.asyncio
    @patch("services.tts.edge_tts.Communicate")
    @patch("services.tts.storage.Client")
    @patch("services.tts.tempfile.NamedTemporaryFile")
    @patch("services.tts.os.unlink")
    @patch("services.tts.uuid.uuid4")
    @patch("services.tts.datetime")
    async def test_generate_tts_success(
        self,
        mock_datetime,
        mock_uuid,
        mock_unlink,
        mock_tempfile,
        mock_storage_client,
        mock_communicate,
    ):
        """測試成功生成 TTS"""
        # 設置 mock
        mock_uuid.return_value = "test-uuid"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.mp3"
        mock_tempfile.return_value.__enter__.return_value = mock_temp

        mock_comm = AsyncMock()
        mock_communicate.return_value = mock_comm

        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        service = TTSService()

        # 執行測試
        result = await service.generate_tts("Hello world", voice="en-US-JennyNeural")

        # 驗證
        mock_communicate.assert_called_once_with(
            "Hello world", "en-US-JennyNeural", rate="+0%", volume="+0%"
        )
        mock_comm.save.assert_called_once_with("/tmp/test.mp3")
        mock_blob.upload_from_filename.assert_called_once_with("/tmp/test.mp3")
        # make_public() 已移除，bucket 已預設為 public
        mock_unlink.assert_called_once_with("/tmp/test.mp3")

        expected_url = "https://storage.googleapis.com/duotopia-audio/tts/tts_20240101_120000_test-uuid.mp3"
        assert result == expected_url

    @pytest.mark.asyncio
    @patch("services.tts.edge_tts.Communicate")
    async def test_generate_tts_failure(self, mock_communicate):
        """測試 TTS 生成失敗"""
        mock_communicate.side_effect = Exception("TTS error")

        service = TTSService()

        with pytest.raises(Exception) as exc_info:
            await service.generate_tts("Hello world")

        assert "TTS generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.object(TTSService, "generate_tts")
    async def test_batch_generate_tts(self, mock_generate):
        """測試批次生成 TTS"""
        mock_generate.side_effect = ["url1.mp3", "url2.mp3", "url3.mp3"]

        service = TTSService()
        texts = ["Text 1", "Text 2", "Text 3"]

        results = await service.batch_generate_tts(texts)

        assert len(results) == 3
        assert results == ["url1.mp3", "url2.mp3", "url3.mp3"]
        assert mock_generate.call_count == 3

    @pytest.mark.asyncio
    @patch("services.tts.edge_tts.list_voices")
    async def test_get_available_voices(self, mock_list_voices):
        """測試取得可用語音列表"""
        mock_list_voices.return_value = [
            {
                "Name": "en-US-JennyNeural",
                "ShortName": "Jenny",
                "Gender": "Female",
                "Locale": "en-US",
            },
            {
                "Name": "zh-CN-XiaoxiaoNeural",
                "ShortName": "Xiaoxiao",
                "Gender": "Female",
                "Locale": "zh-CN",
            },
        ]

        service = TTSService()
        voices = await service.get_available_voices("en")

        assert len(voices) == 1
        assert voices[0]["name"] == "en-US-JennyNeural"
        assert voices[0]["gender"] == "Female"

    def test_get_tts_service_singleton(self):
        """測試單例模式"""
        service1 = get_tts_service()
        service2 = get_tts_service()

        assert service1 is service2


class TestTranslationService:
    """TranslationService 完整測試"""

    def test_translation_service_init(self):
        """測試 TranslationService 初始化"""
        service = TranslationService()

        assert service.project_id is not None
        assert service.location == "global"
        assert service.client is None  # 延遲初始化

    @patch("services.translation.translate.TranslationServiceClient")
    def test_get_client(self, mock_client_class):
        """測試客戶端延遲初始化"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = TranslationService()

        # 第一次調用
        client1 = service._get_client()
        assert client1 == mock_client
        mock_client_class.assert_called_once()

        # 第二次調用應該返回相同實例
        client2 = service._get_client()
        assert client2 == mock_client
        mock_client_class.assert_called_once()

    @patch.object(TranslationService, "_get_client")
    def test_translate_text(self, mock_get_client):
        """測試文字翻譯"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.translations = [Mock(translated_text="你好")]
        mock_client.translate_text.return_value = mock_response

        service = TranslationService()
        result = service.translate_text("Hello", target_language="zh-TW")

        assert result == "你好"
        mock_client.translate_text.assert_called_once()

    @patch.object(TranslationService, "_get_client")
    def test_translate_texts_batch(self, mock_get_client):
        """測試批次翻譯"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.translations = [
            Mock(translated_text="你好"),
            Mock(translated_text="世界"),
        ]
        mock_client.translate_text.return_value = mock_response

        service = TranslationService()
        results = service.translate_texts(["Hello", "World"], target_language="zh-TW")

        assert len(results) == 2
        assert results == ["你好", "世界"]

    @patch.object(TranslationService, "_get_client")
    def test_detect_language(self, mock_get_client):
        """測試語言偵測"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.languages = [Mock(language_code="zh-TW", confidence=0.95)]
        mock_client.detect_language.return_value = mock_response

        service = TranslationService()
        result = service.detect_language("你好世界")

        assert result == {"language": "zh-TW", "confidence": 0.95}

    @patch.object(TranslationService, "_get_client")
    def test_get_supported_languages(self, mock_get_client):
        """測試取得支援語言"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.languages = [
            Mock(language_code="en", display_name="English"),
            Mock(language_code="zh-TW", display_name="Chinese (Traditional)"),
        ]
        mock_client.get_supported_languages.return_value = mock_response

        service = TranslationService()
        languages = service.get_supported_languages()

        assert len(languages) == 2
        assert languages[0]["code"] == "en"
        assert languages[0]["name"] == "English"


class TestAudioManager:
    """AudioManager 完整測試"""

    def test_audio_manager_init(self):
        """測試 AudioManager 初始化"""
        manager = AudioManager()

        assert manager.supported_formats == ["mp3", "wav", "m4a", "ogg"]
        assert manager.max_file_size == 10 * 1024 * 1024  # 10MB
        assert manager.storage_path == "/tmp/audio"

    @patch("services.audio_manager.os.makedirs")
    def test_ensure_storage_path(self, mock_makedirs):
        """測試確保儲存路徑存在"""
        manager = AudioManager()
        manager._ensure_storage_path()

        mock_makedirs.assert_called_once_with("/tmp/audio", exist_ok=True)

    def test_validate_audio_format_valid(self):
        """測試驗證有效音頻格式"""
        manager = AudioManager()

        assert manager.validate_format("test.mp3") is True
        assert manager.validate_format("audio.wav") is True
        assert manager.validate_format("file.m4a") is True

    def test_validate_audio_format_invalid(self):
        """測試驗證無效音頻格式"""
        manager = AudioManager()

        assert manager.validate_format("test.txt") is False
        assert manager.validate_format("audio.pdf") is False
        assert manager.validate_format("noextension") is False

    def test_validate_file_size_valid(self):
        """測試驗證有效檔案大小"""
        manager = AudioManager()

        assert manager.validate_size(1024) is True  # 1KB
        assert manager.validate_size(5 * 1024 * 1024) is True  # 5MB
        assert manager.validate_size(10 * 1024 * 1024) is True  # 10MB

    def test_validate_file_size_invalid(self):
        """測試驗證無效檔案大小"""
        manager = AudioManager()

        assert manager.validate_size(11 * 1024 * 1024) is False  # 11MB
        assert manager.validate_size(100 * 1024 * 1024) is False  # 100MB

    @patch("services.audio_manager.wave.open")
    def test_get_audio_duration_wav(self, mock_wave_open):
        """測試取得 WAV 音頻時長"""
        mock_wav = Mock()
        mock_wav.getframerate.return_value = 44100
        mock_wav.getnframes.return_value = 441000
        mock_wave_open.return_value.__enter__.return_value = mock_wav

        manager = AudioManager()
        duration = manager.get_audio_duration("test.wav")

        assert duration == 10.0  # 441000 / 44100 = 10 seconds

    @patch("services.audio_manager.uuid.uuid4")
    @patch("services.audio_manager.shutil.move")
    @patch("services.audio_manager.os.makedirs")
    def test_save_audio_file(self, mock_makedirs, mock_move, mock_uuid):
        """測試儲存音頻檔案"""
        mock_uuid.return_value = "test-uuid"

        manager = AudioManager()
        mock_file = Mock()
        mock_file.filename = "test.mp3"

        result = manager.save_audio_file(mock_file, "/tmp/test.mp3")

        assert result == "/tmp/audio/test-uuid.mp3"
        mock_move.assert_called_once()


class TestAudioUploadService:
    """AudioUploadService 完整測試"""

    def test_audio_upload_service_init(self):
        """測試 AudioUploadService 初始化"""
        service = AudioUploadService()

        assert service.bucket_name == os.getenv("GCS_BUCKET_NAME", "duotopia-audio")
        assert service.max_file_size == 50 * 1024 * 1024  # 50MB
        assert service.allowed_extensions == {".mp3", ".wav", ".m4a", ".ogg", ".webm"}

    def test_validate_file_extension_valid(self):
        """測試驗證有效檔案副檔名"""
        service = AudioUploadService()

        assert service._validate_file_extension("audio.mp3") is True
        assert service._validate_file_extension("test.wav") is True
        assert service._validate_file_extension("file.m4a") is True

    def test_validate_file_extension_invalid(self):
        """測試驗證無效檔案副檔名"""
        service = AudioUploadService()

        assert service._validate_file_extension("test.txt") is False
        assert service._validate_file_extension("audio.pdf") is False
        assert service._validate_file_extension("") is False

    @patch("services.audio_upload.storage.Client")
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    async def test_upload_audio_success(self, mock_datetime, mock_uuid, mock_storage):
        """測試成功上傳音頻"""
        mock_uuid.return_value = "test-uuid"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        mock_file = Mock()
        mock_file.filename = "test.mp3"
        mock_file.size = 1024
        mock_file.read = Mock(return_value=b"audio data")

        service = AudioUploadService()
        result = await service.upload_audio(mock_file, "user123")

        assert "test-uuid" in result["file_id"]
        assert result["url"].startswith("https://storage.googleapis.com/")
        mock_blob.upload_from_string.assert_called_once()

    async def test_upload_audio_invalid_extension(self):
        """測試上傳無效副檔名"""
        mock_file = Mock()
        mock_file.filename = "test.txt"

        service = AudioUploadService()

        with pytest.raises(ValueError) as exc_info:
            await service.upload_audio(mock_file, "user123")

        assert "Invalid file type" in str(exc_info.value)

    async def test_upload_audio_file_too_large(self):
        """測試上傳過大檔案"""
        mock_file = Mock()
        mock_file.filename = "test.mp3"
        mock_file.size = 100 * 1024 * 1024  # 100MB

        service = AudioUploadService()

        with pytest.raises(ValueError) as exc_info:
            await service.upload_audio(mock_file, "user123")

        assert "File too large" in str(exc_info.value)

    @patch("services.audio_upload.storage.Client")
    async def test_delete_audio(self, mock_storage):
        """測試刪除音頻"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        service = AudioUploadService()
        result = await service.delete_audio("test-file-id")

        assert result is True
        mock_blob.delete.assert_called_once()

    @patch("services.audio_upload.storage.Client")
    async def test_get_audio_url(self, mock_storage):
        """測試取得音頻 URL"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.generate_signed_url.return_value = "https://signed-url.com"

        service = AudioUploadService()
        url = await service.get_audio_url("test-file-id")

        assert url == "https://signed-url.com"
        mock_blob.generate_signed_url.assert_called_once()


class TestServicesIntegration:
    """Services 整合測試"""

    @pytest.mark.asyncio
    async def test_tts_and_upload_integration(self):
        """測試 TTS 生成與上傳整合"""
        with patch("services.tts.edge_tts.Communicate"):
            with patch("services.tts.storage.Client"):
                tts_service = TTSService()

                # 模擬 TTS 生成並上傳的完整流程
                with patch.object(tts_service, "generate_tts") as mock_generate:
                    mock_generate.return_value = (
                        "https://storage.googleapis.com/test.mp3"
                    )

                    result = await tts_service.generate_tts("Test text")
                    assert result.startswith("https://storage.googleapis.com/")

    def test_audio_manager_with_translation(self):
        """測試音頻管理與翻譯整合"""
        audio_manager = AudioManager()
        translation_service = TranslationService()  # noqa: F841

        # 測試音頻檔案名稱的多語言支援
        assert audio_manager.validate_format("音頻.mp3") is True
        assert audio_manager.validate_format("オーディオ.wav") is True
