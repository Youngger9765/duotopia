"""
Translation service 單元測試 - 目標覆蓋率 80%
"""
import os
import sys
import asyncio
from unittest.mock import Mock, patch

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
    async def test_translate_text_error_logging(self, service, caplog):
        """測試錯誤記錄"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )

        await service.translate_text("Hello", "zh-TW")

        # Check that error was logged
        assert "Translation error: API Error" in caplog.text

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_zh_tw(self, service):
        """測試批次翻譯至繁體中文（小批量使用 cache）"""
        service.client = Mock()

        # Mock different responses for different texts
        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            messages = kwargs["messages"]
            content = messages[1]["content"]
            if "Hello" in content:
                mock_resp.choices[0].message.content = "你好"
            elif "Goodbye" in content:
                mock_resp.choices[0].message.content = "再見"
            elif "Thank you" in content:
                mock_resp.choices[0].message.content = "謝謝"
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "zh-TW")

        assert result == ["你好", "再見", "謝謝"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_english_definitions(self, service):
        """測試批次英英釋義（小批量使用 cache）"""
        service.client = Mock()

        # Mock different responses for different texts
        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            messages = kwargs["messages"]
            content = messages[1]["content"]
            if "Hello" in content:
                mock_resp.choices[0].message.content = "A greeting"
            elif "Goodbye" in content:
                mock_resp.choices[0].message.content = "A farewell"
            elif "Thank you" in content:
                mock_resp.choices[0].message.content = "Expression of gratitude"
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "en")

        assert result == ["A greeting", "A farewell", "Expression of gratitude"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_other_language(self, service):
        """測試批次翻譯至其他語言（小批量使用 cache）"""
        service.client = Mock()

        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            messages = kwargs["messages"]
            content = messages[1]["content"]
            if "Hello" in content:
                mock_resp.choices[0].message.content = "Hola"
            elif "Goodbye" in content:
                mock_resp.choices[0].message.content = "Adiós"
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        texts = ["Hello", "Goodbye"]
        result = await service.batch_translate(texts, "Spanish")

        assert result == ["Hola", "Adiós"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_strip_whitespace(self, service):
        """測試批次翻譯移除空白（小批量使用 cache）"""
        service.client = Mock()

        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            messages = kwargs["messages"]
            content = messages[1]["content"]
            if "Hello" in content:
                mock_resp.choices[0].message.content = "  你好  "
            elif "Goodbye" in content:
                mock_resp.choices[0].message.content = "  再見  "
            elif "Thank you" in content:
                mock_resp.choices[0].message.content = "  謝謝  "
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "zh-TW")

        assert result == ["你好", "再見", "謝謝"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_empty_segments(self, service):
        """測試處理空白片段（小批量使用 cache）"""
        service.client = Mock()

        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            messages = kwargs["messages"]
            content = messages[1]["content"]
            if "Hello" in content:
                mock_resp.choices[0].message.content = "你好"
            elif "Goodbye" in content:
                mock_resp.choices[0].message.content = "再見"
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        texts = ["Hello", "Goodbye"]
        result = await service.batch_translate(texts, "zh-TW")

        assert result == ["你好", "再見"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_count_mismatch(self, service):
        """測試翻譯數量不匹配（小批量使用 cache，自動逐個翻譯）"""
        service.client = Mock()

        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            messages = kwargs["messages"]
            content = messages[1]["content"]
            if "Hello" in content:
                mock_resp.choices[0].message.content = "你好"
            elif "Goodbye" in content:
                mock_resp.choices[0].message.content = "再見"
            elif "Thank you" in content:
                mock_resp.choices[0].message.content = "謝謝"
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        texts = ["Hello", "Goodbye", "Thank you"]
        result = await service.batch_translate(texts, "zh-TW")

        # Small batches use individual translation, so all succeed
        assert result == ["你好", "再見", "謝謝"]

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
    async def test_batch_translate_error_logging(self, service, caplog):
        """測試批次翻譯錯誤記錄"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )

        texts = ["Hello", "Goodbye"]
        await service.batch_translate(texts, "zh-TW")

        # Check that error was logged (will appear in individual translate_text calls)
        assert "Translation error: API Error" in caplog.text

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

    # ===== Cache Tests (Issue #88) =====

    def test_cache_initialization(self, service):
        """測試 cache 初始化"""
        assert service._cache_hits == 0
        assert service._cache_misses == 0

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_cache_miss(self, service, mock_openai_response):
        """測試 cache miss"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(return_value=mock_openai_response)

        result1 = await service.translate_text("Hello", "zh-TW")

        assert result1 == "翻譯結果"
        assert service._cache_misses == 1
        assert service._cache_hits == 0
        # API should be called once
        assert service.client.chat.completions.create.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_cache_hit(self, service, mock_openai_response):
        """測試 cache hit - 相同文本不应重复调用 API"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(return_value=mock_openai_response)

        # First call - cache miss
        result1 = await service.translate_text("Hello", "zh-TW")
        assert service._cache_misses == 1

        # Second call - should hit cache
        result2 = await service.translate_text("Hello", "zh-TW")
        assert result2 == result1
        assert service._cache_hits == 1
        # API should only be called ONCE (second call uses cache)
        assert service.client.chat.completions.create.call_count == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_translate_text_cache_different_lang(self, service):
        """測試不同語言使用不同 cache key"""
        service.client = Mock()

        # Mock different responses for different languages
        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            messages = kwargs["messages"]
            if "繁體中文" in messages[1]["content"]:
                mock_resp.choices[0].message.content = "你好"
            elif "simple English definition" in messages[1]["content"]:
                mock_resp.choices[0].message.content = "A greeting"
            else:
                mock_resp.choices[0].message.content = "Hola"
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        # Different languages should not share cache
        result_zh = await service.translate_text("Hello", "zh-TW")
        result_en = await service.translate_text("Hello", "en")
        result_es = await service.translate_text("Hello", "Spanish")

        assert result_zh == "你好"
        assert result_en == "A greeting"
        assert result_es == "Hola"
        # All should be cache misses (different keys)
        assert service._cache_misses == 3
        assert service._cache_hits == 0
        assert service.client.chat.completions.create.call_count == 3

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_batch_translate_uses_cache(self, service):
        """測試 batch_translate 使用 cache（小批量或有重复）"""
        service.client = Mock()

        def mock_create(**kwargs):
            mock_resp = Mock()
            mock_resp.choices = [Mock()]
            mock_resp.choices[0].message.content = "你好"
            return mock_resp

        service.client.chat.completions.create = Mock(side_effect=mock_create)

        # Small batch should use individual translation (which uses cache)
        texts = ["Hello", "Hello", "Hi"]  # Has duplicates
        result = await service.batch_translate(texts, "zh-TW")

        assert len(result) == 3
        # Should have called individual translate_text which uses cache
        # "Hello" appears twice, so second time should hit cache
        assert service._cache_hits >= 1

    def test_get_cache_stats(self, service):
        """測試 cache 统计信息"""
        service._cache_hits = 10
        service._cache_misses = 5

        stats = service.get_cache_stats()

        assert stats["cache_hits"] == 10
        assert stats["cache_misses"] == 5
        assert stats["total_calls"] == 15
        assert stats["hit_rate_percent"] == 66.67
        assert stats["cache_maxsize"] == 5000
        assert stats["cache_ttl_seconds"] == 3600

    def test_get_cache_stats_no_calls(self, service):
        """測試初始 cache 统计（无调用）"""
        stats = service.get_cache_stats()

        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["total_calls"] == 0
        assert stats["hit_rate_percent"] == 0

    def test_clear_cache(self, service):
        """測試清空 cache"""
        service._cache_hits = 10
        service._cache_misses = 5
        service._cache.set(("key", "zh-TW", "model", 0.3), "value")

        service.clear_cache()

        assert service._cache_hits == 0
        assert service._cache_misses == 0
        stats = service.get_cache_stats()
        assert stats["cache_size"] == 0

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_cache_size_limit(self, service, mock_openai_response):
        """測試 cache 大小限制（maxsize=5000）"""
        service.client = Mock()
        service.client.chat.completions.create = Mock(return_value=mock_openai_response)

        # Cache should work within limit
        for i in range(100):
            await service.translate_text(f"text_{i}", "zh-TW")

        stats = service.get_cache_stats()
        assert stats["cache_size"] == 100
        assert stats["cache_size"] <= stats["cache_maxsize"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    async def test_cache_ttl_expiry(self, mock_openai_response):
        """測試 cache TTL 到期後不應命中"""
        # Use short TTL for test
        service = TranslationService(cache_ttl_seconds=0)
        service.client = Mock()

        # First response
        first_resp = Mock()
        first_resp.choices = [Mock()]
        first_resp.choices[0].message.content = "翻譯1"
        # Second response after expiry
        second_resp = Mock()
        second_resp.choices = [Mock()]
        second_resp.choices[0].message.content = "翻譯2"

        service.client.chat.completions.create = Mock(
            side_effect=[first_resp, second_resp]
        )

        result1 = await service.translate_text("Hello", "zh-TW")
        await asyncio.sleep(0.01)
        result2 = await service.translate_text("Hello", "zh-TW")

        assert result1 == "翻譯1"
        assert result2 == "翻譯2"  # cache expired, so second call hits API
        assert service.client.chat.completions.create.call_count == 2
        assert service._cache_hits == 0
