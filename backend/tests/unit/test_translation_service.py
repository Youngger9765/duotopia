"""
Translation service 單元測試 - 目標覆蓋率 80%
"""
import os
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest  # noqa: E402
from services.translation import TranslationService  # noqa: E402


class TestTranslationService:
    """測試 TranslationService"""

    @pytest.fixture
    def service(self):
        """創建測試用 service"""
        return TranslationService()

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI 回應"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "翻譯結果"
        return mock_response

    def test_init(self):
        """測試初始化"""
        service = TranslationService()
        assert service.client is None
        assert service.model == "gpt-3.5-turbo"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("services.translation.OpenAI")
    def test_ensure_client_success(self, mock_openai):
        """測試 client 初始化成功"""
        service = TranslationService()
        service._ensure_client()

        assert service.client is not None
        mock_openai.assert_called_once_with(api_key="test-key")

    @patch.dict(os.environ, {}, clear=True)
    def test_ensure_client_no_api_key(self):
        """測試沒有 API key 時的錯誤"""
        service = TranslationService()

        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            service._ensure_client()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("services.translation.OpenAI")
    def test_ensure_client_cached(self, mock_openai):
        """測試 client 快取機制"""
        service = TranslationService()
        mock_client = Mock()
        service.client = mock_client

        service._ensure_client()

        # 不應該再次創建 client
        mock_openai.assert_not_called()
        assert service.client == mock_client

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_zh_tw(self, service, mock_openai_response):
        """測試翻譯至繁體中文"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(return_value=mock_openai_response)

        result = await service.translate_text("Hello", "zh-TW")

        assert result == "翻譯結果"
        service.client.chat.completions.create.assert_called_once()

        # 檢查呼叫參數
        call_args = service.client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-3.5-turbo"
        assert call_args.kwargs["temperature"] == 0.3
        assert call_args.kwargs["max_tokens"] == 100

        # 檢查 messages
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert "professional translator" in messages[0]["content"]
        assert "繁體中文" in messages[1]["content"]
        assert "Hello" in messages[1]["content"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_english_definition(self, service):
        """測試英英釋義"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "A common greeting"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        result = await service.translate_text("Hello", "en")

        assert result == "A common greeting"

        # 檢查呼叫參數
        call_args = service.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "simple English definition" in messages[1]["content"]
        assert "language learners" in messages[1]["content"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_other_language(self, service):
        """測試翻譯至其他語言"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hola"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        result = await service.translate_text("Hello", "Spanish")

        assert result == "Hola"

        # 檢查呼叫參數
        call_args = service.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "translate the following text to Spanish" in messages[1]["content"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_strip_whitespace(self, service):
        """測試移除空白字元"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "  翻譯結果  \n\t"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        result = await service.translate_text("Hello", "zh-TW")

        assert result == "翻譯結果"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_error_handling(self, service):
        """測試錯誤處理"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )

        result = await service.translate_text("Hello", "zh-TW")

        # 錯誤時返回原文
        assert result == "Hello"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("builtins.print")
    async def test_translate_text_error_logging(self, mock_print, service):
        """測試錯誤記錄"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )

        await service.translate_text("Hello", "zh-TW")

        mock_print.assert_called_once_with("Translation error: API Error")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_zh_tw(self, service):
        """測試批次翻譯至繁體中文"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "你好---再見---謝謝"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "zh-TW")

        assert result == ["你好", "再見", "謝謝"]

        # 檢查呼叫參數
        call_args = service.client.chat.completions.create.call_args
        assert call_args.kwargs["max_tokens"] == 500  # 批次需要更多 tokens
        messages = call_args.kwargs["messages"]
        assert "繁體中文" in messages[1]["content"]
        assert "---" in messages[1]["content"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_english_definitions(self, service):
        """測試批次英英釋義"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[
            0
        ].message.content = "A greeting---A farewell---Expression of gratitude"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "en")

        assert result == ["A greeting", "A farewell", "Expression of gratitude"]

        # 檢查呼叫參數
        call_args = service.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "simple English definitions" in messages[1]["content"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_other_language(self, service):
        """測試批次翻譯至其他語言"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hola---Adiós"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = ["Hello", "Goodbye"]
        result = await service.batch_translate(texts, "Spanish")

        assert result == ["Hola", "Adiós"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_strip_whitespace(self, service):
        """測試批次翻譯移除空白"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "  你好  ---  再見  ---  謝謝  "
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "zh-TW")

        assert result == ["你好", "再見", "謝謝"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_empty_segments(self, service):
        """測試處理空白片段"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "你好---   ---再見"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = ["Hello", "Goodbye"]
        result = await service.batch_translate(texts, "zh-TW")

        # 過濾掉空白片段，所以只有兩個結果
        assert result == ["你好", "再見"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("builtins.print")
    async def test_batch_translate_count_mismatch(self, mock_print, service):
        """測試翻譯數量不匹配"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "你好"  # 只有一個翻譯
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "zh-TW")

        # 數量不匹配時返回原文
        assert result == texts
        mock_print.assert_called_with("Warning: Expected 3 translations, got 1")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_error_handling(self, service):
        """測試批次翻譯錯誤處理"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )

        texts = ["Hello", "Goodbye"]
        result = await service.batch_translate(texts, "zh-TW")

        # 錯誤時返回原文列表
        assert result == texts

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("builtins.print")
    async def test_batch_translate_error_logging(self, mock_print, service):
        """測試批次翻譯錯誤記錄"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )

        texts = ["Hello", "Goodbye"]
        await service.batch_translate(texts, "zh-TW")

        mock_print.assert_called_once_with("Batch translation error: API Error")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_single_text(self, service):
        """測試批次翻譯單一文本"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "你好"
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = ["Hello"]
        result = await service.batch_translate(texts, "zh-TW")

        assert result == ["你好"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_empty_list(self, service):
        """測試批次翻譯空列表"""
        service.client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""
        service.client.chat.completions.create = Mock(return_value=mock_response)

        texts = []
        result = await service.batch_translate(texts, "zh-TW")

        assert result == []

    def test_global_instance(self):
        """測試全局實例"""
        from services.translation import translation_service

        assert isinstance(translation_service, TranslationService)
        assert translation_service.model == "gpt-3.5-turbo"
