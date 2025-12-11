"""
Comprehensive tests for TTS service with caching functionality
Tests cache initialization, hits, misses, statistics, and performance
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import os
import tempfile
from services.tts import TTSService, get_tts_service


class TestTTSServiceInitialization:
    """Test TTS service initialization and configuration"""

    def test_service_initialization(self):
        """Test that service initializes with correct default values"""
        service = TTSService()
        assert service.bucket_name == "duotopia-audio"
        assert service._cache_hits == 0
        assert service._cache_misses == 0
        assert service.storage_client is None

    def test_singleton_pattern(self):
        """Test that get_tts_service returns same instance"""
        service1 = get_tts_service()
        service2 = get_tts_service()
        assert service1 is service2

    def test_cache_key_generation(self):
        """Test that cache key is deterministic and unique"""
        service = TTSService()

        # Same input should generate same key
        key1 = service._generate_cache_key("hello", "en-US-JennyNeural", "+0%", "+0%")
        key2 = service._generate_cache_key("hello", "en-US-JennyNeural", "+0%", "+0%")
        assert key1 == key2

        # Different text should generate different key
        key3 = service._generate_cache_key("world", "en-US-JennyNeural", "+0%", "+0%")
        assert key1 != key3

        # Different voice should generate different key
        key4 = service._generate_cache_key(
            "hello", "en-US-ChristopherNeural", "+0%", "+0%"
        )
        assert key1 != key4

        # Different rate should generate different key
        key5 = service._generate_cache_key("hello", "en-US-JennyNeural", "+10%", "+0%")
        assert key1 != key5

        # Cache key should be MD5 hash (32 hex characters)
        assert len(key1) == 32
        assert all(c in "0123456789abcdef" for c in key1)


class TestTTSCaching:
    """Test TTS caching functionality"""

    @pytest.fixture
    def mock_service(self):
        """Create a TTS service with mocked dependencies"""
        service = TTSService()
        # Mock GCS storage client
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        service.storage_client = mock_client
        service.azure_speech_key = "test_key"
        return service

    @pytest.mark.asyncio
    async def test_cache_miss_first_call(self, mock_service):
        """Test that first call results in cache miss and generates audio"""
        # Mock GCS blob doesn't exist
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_service.storage_client.bucket.return_value.blob.return_value = mock_blob

        # Mock Azure TTS synthesis
        with patch("azure.cognitiveservices.speech.SpeechSynthesizer") as mock_synth:
            mock_result = MagicMock()
            mock_result.reason = (
                MagicMock()
            )  # Import the actual enum for proper comparison
            from azure.cognitiveservices.speech import ResultReason

            mock_result.reason = ResultReason.SynthesizingAudioCompleted

            mock_synth_instance = MagicMock()
            mock_synth_instance.speak_text = Mock(return_value=mock_result)
            mock_synth.return_value = mock_synth_instance

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_file = MagicMock()
                mock_file.name = "/tmp/test.mp3"
                mock_temp.return_value = mock_file

                with patch("os.path.exists", return_value=True):
                    with patch("os.unlink"):
                        result = await mock_service.generate_tts(
                            "hello", "en-US-JennyNeural", "+0%", "+0%"
                        )

        # Verify cache statistics
        assert mock_service._cache_hits == 0
        assert mock_service._cache_misses == 1
        assert result.startswith("https://storage.googleapis.com/")

    @pytest.mark.asyncio
    async def test_cache_hit_second_call(self, mock_service):
        """Test that second call with same parameters hits cache"""
        # Mock GCS blob exists
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_service.storage_client.bucket.return_value.blob.return_value = mock_blob

        result = await mock_service.generate_tts(
            "hello", "en-US-JennyNeural", "+0%", "+0%"
        )

        # Verify cache hit
        assert mock_service._cache_hits == 1
        assert mock_service._cache_misses == 0
        assert result.startswith("https://storage.googleapis.com/")
        assert "cached_" in result

    @pytest.mark.asyncio
    async def test_cache_different_parameters(self, mock_service):
        """Test that different parameters result in different cache keys"""
        # Mock GCS blob doesn't exist
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_service.storage_client.bucket.return_value.blob.return_value = mock_blob

        # Generate cache keys for different parameters
        key1 = mock_service._generate_cache_key(
            "hello", "en-US-JennyNeural", "+0%", "+0%"
        )
        key2 = mock_service._generate_cache_key(
            "hello", "en-US-JennyNeural", "+10%", "+0%"
        )
        key3 = mock_service._generate_cache_key(
            "hello", "en-US-ChristopherNeural", "+0%", "+0%"
        )

        # All keys should be different
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    @pytest.mark.asyncio
    async def test_gcs_check_error_handling(self, mock_service):
        """Test that errors in cache check are handled gracefully"""
        # Mock GCS blob check raises exception
        mock_service.storage_client.bucket.side_effect = Exception("GCS error")

        # Should return None and not crash
        result = mock_service._get_cached_audio_url("test_key")
        assert result is None


class TestTTSCacheStatistics:
    """Test cache statistics tracking and reporting"""

    def test_initial_stats(self):
        """Test initial cache statistics"""
        service = TTSService()
        stats = service.get_cache_stats()

        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["total_calls"] == 0
        assert stats["hit_rate_percent"] == 0
        assert stats["estimated_api_calls_saved"] == 0
        assert stats["estimated_cost_savings_usd"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_cache_hits(self):
        """Test statistics after cache hits"""
        service = TTSService()

        # Mock GCS storage
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_client.bucket.return_value = mock_bucket
        service.storage_client = mock_client

        # Simulate 3 cache hits
        for _ in range(3):
            await service.generate_tts("test", "en-US-JennyNeural", "+0%", "+0%")

        stats = service.get_cache_stats()
        assert stats["cache_hits"] == 3
        assert stats["cache_misses"] == 0
        assert stats["total_calls"] == 3
        assert stats["hit_rate_percent"] == 100.0
        assert stats["estimated_api_calls_saved"] == 3
        assert stats["estimated_cost_savings_usd"] > 0

    def test_stats_with_mixed_hits_and_misses(self):
        """Test statistics calculation with mixed hits and misses"""
        service = TTSService()

        # Manually set cache stats
        service._cache_hits = 7
        service._cache_misses = 3

        stats = service.get_cache_stats()
        assert stats["cache_hits"] == 7
        assert stats["cache_misses"] == 3
        assert stats["total_calls"] == 10
        assert stats["hit_rate_percent"] == 70.0

    def test_clear_cache(self):
        """Test cache clearing"""
        service = TTSService()

        # Set some cache stats
        service._cache_hits = 10
        service._cache_misses = 5

        # Clear cache
        service.clear_cache()

        # Verify stats are reset
        assert service._cache_hits == 0
        assert service._cache_misses == 0

        stats = service.get_cache_stats()
        assert stats["total_calls"] == 0
        assert stats["hit_rate_percent"] == 0


class TestTTSBatchGeneration:
    """Test batch TTS generation with caching"""

    @pytest.fixture
    def mock_service(self):
        """Create a TTS service with mocked dependencies"""
        service = TTSService()
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        service.storage_client = mock_client
        service.azure_speech_key = "test_key"
        return service

    @pytest.mark.asyncio
    async def test_batch_generate_with_cache_hits(self, mock_service):
        """Test batch generation benefits from cache"""
        # Mock first text as cache miss, second as cache hit
        call_count = [0]

        def mock_exists():
            call_count[0] += 1
            return call_count[0] > 1  # Second call onwards is cache hit

        mock_blob = MagicMock()
        mock_blob.exists.side_effect = mock_exists
        mock_service.storage_client.bucket.return_value.blob.return_value = mock_blob

        # Mock Azure TTS for first call
        with patch("azure.cognitiveservices.speech.SpeechSynthesizer") as mock_synth:
            mock_result = MagicMock()
            from azure.cognitiveservices.speech import ResultReason

            mock_result.reason = ResultReason.SynthesizingAudioCompleted

            mock_synth_instance = MagicMock()
            mock_synth_instance.speak_text = Mock(return_value=mock_result)
            mock_synth.return_value = mock_synth_instance

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_file = MagicMock()
                mock_file.name = "/tmp/test.mp3"
                mock_temp.return_value = mock_file

                with patch("os.path.exists", return_value=True):
                    with patch("os.unlink"):
                        # Call same text twice
                        texts = ["hello", "hello"]
                        results = await mock_service.batch_generate_tts(
                            texts, "en-US-JennyNeural", "+0%", "+0%"
                        )

        # First call is miss, second is hit
        assert mock_service._cache_misses == 1
        assert mock_service._cache_hits == 1
        assert len(results) == 2


class TestTTSPerformanceMetrics:
    """Test performance improvements from caching"""

    def test_expected_cache_hit_rate(self):
        """Test that high cache hit rate is achievable"""
        service = TTSService()

        # Simulate realistic usage: 90% cache hits
        service._cache_hits = 900
        service._cache_misses = 100

        stats = service.get_cache_stats()
        assert stats["hit_rate_percent"] == 90.0

    def test_cost_savings_calculation(self):
        """Test cost savings calculation is reasonable"""
        service = TTSService()

        # 1000 cache hits should save approximately $16 (1000 * $0.016)
        service._cache_hits = 1000

        stats = service.get_cache_stats()
        assert stats["estimated_cost_savings_usd"] == 16.0

    def test_api_calls_saved(self):
        """Test API calls saved metric"""
        service = TTSService()

        service._cache_hits = 500
        service._cache_misses = 50

        stats = service.get_cache_stats()
        # Each cache hit saves one API call
        assert stats["estimated_api_calls_saved"] == 500


class TestTTSIntegration:
    """Integration tests for TTS caching (requires actual dependencies)"""

    @pytest.mark.skipif(
        not os.getenv("AZURE_SPEECH_KEY"), reason="Azure credentials not configured"
    )
    @pytest.mark.asyncio
    async def test_real_cache_workflow(self):
        """Test real caching workflow with actual Azure and GCS"""
        service = get_tts_service()

        # Clear cache stats
        service.clear_cache()

        test_text = "This is a cache test"
        voice = "en-US-JennyNeural"

        # First call should be cache miss
        url1 = await service.generate_tts(test_text, voice)
        assert service._cache_misses == 1
        assert service._cache_hits == 0

        # Second call with same parameters should be cache hit
        url2 = await service.generate_tts(test_text, voice)
        assert service._cache_misses == 1
        assert service._cache_hits == 1

        # URLs should be identical (same cached file)
        assert url1 == url2

        # Verify cache stats
        stats = service.get_cache_stats()
        assert stats["hit_rate_percent"] == 50.0
        assert stats["total_calls"] == 2
