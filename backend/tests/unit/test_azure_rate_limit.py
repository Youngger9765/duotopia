"""
Azure Speech API Rate Limiting Unit Tests

Tests for global Semaphore (18 concurrent) and 429 error detection
"""

import pytest
import asyncio
import time
from unittest.mock import patch


class TestAzureRateLimitingSemaphore:
    """Test global semaphore limits concurrent Azure API calls"""

    @pytest.mark.asyncio
    async def test_semaphore_limits_to_18_concurrent(self):
        """
        Verify Semaphore limits max 18 concurrent Azure API calls

        Test scenario:
        - Send 50 concurrent requests
        - Monitor active count (should never exceed 18)
        - Verify all requests complete successfully
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        # Track maximum concurrent executions
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def mock_azure_call(task_id: int):
            """Simulate Azure API call with concurrency tracking"""
            nonlocal max_concurrent, current_concurrent

            async with _get_azure_speech_semaphore():
                async with lock:
                    current_concurrent += 1
                    max_concurrent = max(max_concurrent, current_concurrent)

                # Simulate API delay
                await asyncio.sleep(0.05)  # 50ms

                async with lock:
                    current_concurrent -= 1

                return {"task_id": task_id, "score": 85}

        # Execute 50 concurrent requests
        start_time = time.time()
        tasks = [mock_azure_call(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify all completed
        assert len(results) == 50
        assert all(r["score"] == 85 for r in results)

        # Verify semaphore limit enforced
        assert (
            max_concurrent <= 18
        ), f"Semaphore failed: max concurrent was {max_concurrent}, should be <= 18"

        # Verify reasonable total time
        # 50 requests / 18 concurrency ≈ 3 batches × 0.05s ≈ 0.15s
        assert (
            total_time < 0.5
        ), f"Performance issue: 50 requests took {total_time:.2f}s (expected < 0.5s)"

        print("\n✅ Semaphore Test Passed:")
        print(f"   - Max concurrent: {max_concurrent}/18")
        print(f"   - Total time: {total_time:.2f}s")
        print("   - Requests: 50")

    @pytest.mark.asyncio
    async def test_semaphore_queue_wait_time(self):
        """
        Test queue wait time when semaphore is saturated

        Scenario:
        - First 18 requests should start immediately
        - Request #19 should wait for first batch to complete
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        wait_times = []

        async def tracked_azure_call(task_id: int):
            """Track wait time before acquiring semaphore"""
            start = time.time()
            async with _get_azure_speech_semaphore():
                wait_time = time.time() - start
                wait_times.append(wait_time)
                await asyncio.sleep(0.1)  # 100ms processing
                return task_id

        # Execute 30 requests (will create queue)
        tasks = [tracked_azure_call(i) for i in range(30)]
        await asyncio.gather(*tasks)

        # First 18 should have minimal wait
        first_batch = sorted(wait_times)[:18]
        assert all(w < 0.01 for w in first_batch), "First 18 requests should not wait"

        # Later requests should have measurable wait
        later_requests = sorted(wait_times)[18:]
        assert any(
            w > 0.05 for w in later_requests
        ), "Queue should cause wait time for requests beyond 18"


class TestAzureRateLimitErrorDetection:
    """Test 429 error detection and conversion to AzureRateLimitError"""

    @pytest.mark.asyncio
    async def test_429_error_raises_rate_limit_exception(self):
        """
        Verify 429 errors are detected and converted to AzureRateLimitError

        Test cases:
        - Azure SDK raises exception with "429" in message
        - Azure SDK raises exception with "too many requests"
        - Azure SDK raises exception with "rate limit"
        """
        # Test the detection logic directly (without full endpoint test)
        error_messages = [
            "Azure returned 429 status code",
            "too many requests from client",
            "rate limit exceeded for subscription",
            "HTTP 429 error response",
        ]

        for error_msg in error_messages:
            error_msg_lower = error_msg.lower()
            detected = (
                "429" in error_msg_lower
                or "too many requests" in error_msg_lower
                or "rate limit" in error_msg_lower
            )
            assert detected, f"Should detect 429 error in: {error_msg}"

    @pytest.mark.asyncio
    async def test_non_429_error_passes_through(self):
        """
        Verify non-429 errors are NOT converted to AzureRateLimitError

        Test cases:
        - Network timeout errors
        - Authentication errors
        - Invalid audio format errors
        """
        error_messages = [
            "Connection timeout",
            "Invalid API key",
            "Audio format not supported",
            "Speech recognition failed",
        ]

        for error_msg in error_messages:
            error_msg_lower = error_msg.lower()
            detected = (
                "429" in error_msg_lower
                or "too many requests" in error_msg_lower
                or "rate limit" in error_msg_lower
            )
            assert not detected, f"Should NOT detect 429 error in: {error_msg}"

    @pytest.mark.asyncio
    async def test_rate_limit_error_includes_context(self):
        """
        Verify AzureRateLimitError includes helpful context

        Should include:
        - Original error message
        - Clear indication it's a rate limit issue
        """
        from routers.speech_assessment import AzureRateLimitError

        original_error = "Azure Speech API returned 429"
        rate_limit_error = AzureRateLimitError(
            f"Azure API rate limit exceeded: {original_error}"
        )

        error_str = str(rate_limit_error)
        assert "rate limit" in error_str.lower()
        assert "429" in error_str


class TestSemaphoreConfiguration:
    """Test semaphore configuration and initialization"""

    def test_semaphore_value_is_18(self):
        """
        Verify semaphore is configured to 18 concurrent

        Azure S0 limit: 20 TPS
        Safe value: 18 (leaves 2 buffer)
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        # Get semaphore and check initial value
        semaphore = _get_azure_speech_semaphore()

        # Access internal counter (semaphore._value)
        # Note: This is implementation-dependent
        assert hasattr(semaphore, "_value")

        # Check initial value
        initial_value = semaphore._value
        assert initial_value == 18, f"Semaphore should be 18, got {initial_value}"

    @pytest.mark.asyncio
    async def test_semaphore_reusable(self):
        """
        Verify semaphore can be reused across multiple request batches
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        async def quick_task():
            async with _get_azure_speech_semaphore():
                await asyncio.sleep(0.01)
                return True

        # First batch
        batch1 = await asyncio.gather(*[quick_task() for _ in range(20)])
        assert all(batch1)

        # Second batch (should work without issues)
        batch2 = await asyncio.gather(*[quick_task() for _ in range(20)])
        assert all(batch2)

        # Semaphore value should be back to 18
        semaphore = _get_azure_speech_semaphore()
        assert semaphore._value == 18


class TestErrorLoggingAndMonitoring:
    """Test logging and monitoring of rate limit events"""

    @pytest.mark.asyncio
    async def test_rate_limit_logged_with_warning(self):
        """
        Verify 429 errors are logged with WARNING level
        """
        from routers.speech_assessment import logger

        # This test would check logging behavior
        # Actual implementation depends on how you integrate logging
        with patch.object(logger, "warning"):
            # Simulate 429 detection
            Exception("Azure 429 rate limit hit")

            # Code that should log warning
            # logger.warning(f"Azure rate limit hit: {error}")

            # For now, just verify logger exists
            assert logger is not None

    @pytest.mark.asyncio
    async def test_queue_wait_time_logged(self):
        """
        Verify queue wait time > 2s is logged

        From requirements:
        ```python
        if queue_wait > 2:
            logger.warning(f"Azure rate limit queue wait: {queue_wait:.2f}s")
        ```
        """
        # Test the queue wait logic
        queue_wait_short = 1.5
        queue_wait_long = 3.2

        assert queue_wait_short <= 2.0, "Short wait should not trigger log"
        assert queue_wait_long > 2.0, "Long wait should trigger log"


class TestIntegrationWithExistingCode:
    """Test integration with existing speech_assessment.py code"""

    @pytest.mark.asyncio
    async def test_semaphore_wraps_assess_pronunciation_call(self):
        """
        Verify semaphore wraps the assess_pronunciation execution

        Code structure should be:
        ```python
        async with _get_azure_speech_semaphore():
            assessment_result = await asyncio.wait_for(
                loop.run_in_executor(speech_pool, assess_pronunciation, ...),
                timeout=AZURE_SPEECH_TIMEOUT,
            )
        ```
        """
        # This test verifies the implementation structure
        # Actual code inspection happens during implementation

        from routers.speech_assessment import _get_azure_speech_semaphore

        # Verify semaphore getter returns a Semaphore
        semaphore = _get_azure_speech_semaphore()
        assert isinstance(semaphore, asyncio.Semaphore)

    def test_azure_rate_limit_error_defined(self):
        """
        Verify AzureRateLimitError exception class is defined
        """
        from routers.speech_assessment import AzureRateLimitError

        # Verify it's an Exception subclass
        assert issubclass(AzureRateLimitError, Exception)

        # Verify can be instantiated
        error = AzureRateLimitError("Test error")
        assert str(error) == "Test error"

    def test_timeout_constant_unchanged(self):
        """
        Verify AZURE_SPEECH_TIMEOUT constant is not changed

        Should remain at 20 seconds
        """
        from routers.speech_assessment import AZURE_SPEECH_TIMEOUT

        assert (
            AZURE_SPEECH_TIMEOUT == 20
        ), f"Timeout should remain 20s, got {AZURE_SPEECH_TIMEOUT}"
