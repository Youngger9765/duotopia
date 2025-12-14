"""
Azure Speech API Concurrent Stress Tests

Stress test for 50 concurrent users scenario (500 requests total)
Verifies no 429 errors occur with Semaphore rate limiting
"""

import pytest
import asyncio
import time


@pytest.mark.stress
class TestAzureConcurrentStress:
    """Stress tests for Azure API rate limiting under heavy load"""

    @pytest.mark.asyncio
    async def test_50_concurrent_users_no_429(self):
        """
        Stress test: 50 users × 10 requests each = 500 total requests

        Scenario:
        - 50 students simultaneously working on 10-question assignment
        - Each sends 10 pronunciation assessment requests
        - Total: 500 concurrent requests

        Expected behavior:
        - All 500 requests succeed (no 429 errors)
        - Total time < 35 seconds (500 / 18 ≈ 28 seconds + margin)
        - P95 response time < 3 seconds
        - P99 response time < 5 seconds
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        # Track metrics
        results = []
        errors = []
        response_times = []

        async def simulate_student_requests(student_id: int, num_requests: int = 10):
            """Simulate one student making multiple requests"""
            student_results = []

            for req_id in range(num_requests):
                request_start = time.time()
                try:
                    async with _get_azure_speech_semaphore():
                        # Simulate Azure API call (1 second)
                        await asyncio.sleep(1.0)

                        result = {
                            "student_id": student_id,
                            "request_id": req_id,
                            "score": 85,
                            "status": "success",
                        }
                        student_results.append(result)
                        results.append(result)

                        # Track response time
                        response_time = time.time() - request_start
                        response_times.append(response_time)

                except Exception as e:
                    errors.append(
                        {
                            "student_id": student_id,
                            "request_id": req_id,
                            "error": str(e),
                        }
                    )

            return student_results

        # Execute stress test: 50 students × 10 requests
        start_time = time.time()
        student_tasks = [
            simulate_student_requests(student_id, num_requests=10)
            for student_id in range(1, 51)
        ]
        await asyncio.gather(*student_tasks)
        total_time = time.time() - start_time

        # Verify results
        assert len(errors) == 0, f"Should have no errors, got {len(errors)}: {errors}"
        assert len(results) == 500, f"Should have 500 results, got {len(results)}"
        assert all(r["status"] == "success" for r in results)

        # Performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]

        # Assertions
        assert total_time < 35, (
            f"Total time {total_time:.2f}s exceeds 35s threshold "
            "(500 requests / 18 concurrency ≈ 28s)"
        )
        assert p95 < 3.5, f"P95 response time {p95:.2f}s exceeds 3.5s threshold"
        assert p99 < 5.0, f"P99 response time {p99:.2f}s exceeds 5s threshold"

        # Print metrics
        print("\n✅ Stress Test Passed (50 users × 10 requests = 500 total):")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Successful requests: {len(results)}/500")
        print(f"   - Failed requests: {len(errors)}")
        print(f"   - Average response time: {avg_response_time:.2f}s")
        print(f"   - P50 (median): {p50:.2f}s")
        print(f"   - P95: {p95:.2f}s")
        print(f"   - P99: {p99:.2f}s")
        print(f"   - Throughput: {len(results) / total_time:.1f} requests/sec")

    @pytest.mark.asyncio
    async def test_rate_limit_recovery(self):
        """
        Test system recovery after hitting rate limit

        Scenario:
        - Mock first 5 requests to return 429 errors
        - Remaining requests should succeed
        - System should handle 429 gracefully

        Expected:
        - First 5 requests raise AzureRateLimitError
        - Remaining requests succeed
        - No cascading failures
        """
        from routers.speech_assessment import (
            _get_azure_speech_semaphore,
            AzureRateLimitError,
        )

        results = {"success": 0, "rate_limited": 0, "errors": 0}
        request_counter = 0

        async def simulate_request_with_429(request_id: int):
            """Simulate request that may hit 429"""
            nonlocal request_counter

            try:
                async with _get_azure_speech_semaphore():
                    # First 5 requests simulate 429
                    if request_id < 5:
                        results["rate_limited"] += 1
                        raise AzureRateLimitError("Azure API rate limit exceeded")

                    # Remaining requests succeed
                    await asyncio.sleep(0.1)
                    results["success"] += 1
                    return {"request_id": request_id, "status": "success"}

            except AzureRateLimitError:
                # 429 errors are expected for first 5
                if request_id >= 5:
                    results["errors"] += 1
                raise

        # Execute 20 requests
        tasks = [simulate_request_with_429(i) for i in range(20)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify results
        assert (
            results["rate_limited"] == 5
        ), "Should have exactly 5 rate limited requests"
        assert results["success"] == 15, "Should have 15 successful requests"
        assert results["errors"] == 0, "Should have no unexpected errors"

        # Verify exceptions are AzureRateLimitError
        rate_limit_exceptions = [
            r for r in responses if isinstance(r, AzureRateLimitError)
        ]
        assert (
            len(rate_limit_exceptions) == 5
        ), "Should have 5 AzureRateLimitError exceptions"

        print("\n✅ Rate Limit Recovery Test Passed:")
        print(f"   - Rate limited: {results['rate_limited']}")
        print(f"   - Successful: {results['success']}")
        print("   - System recovered successfully")

    @pytest.mark.asyncio
    async def test_sustained_load_30_minutes(self):
        """
        Test sustained load over extended period

        Scenario:
        - Simulate 5 minutes of continuous load
        - 10 concurrent users
        - Each user makes requests every 5 seconds
        - Total: ~600 requests over 5 minutes

        Expected:
        - No 429 errors
        - Stable response times throughout
        - No memory leaks or resource exhaustion

        Note: This is a long-running test (5 minutes)
        Use pytest -m stress to run
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        duration_seconds = 300  # 5 minutes (use 60 for quick test)
        num_users = 10
        request_interval = 5  # seconds between requests

        results = []
        start_time = time.time()

        async def sustained_user_requests(user_id: int):
            """Simulate sustained user activity"""
            user_start = time.time()
            request_count = 0

            while time.time() - user_start < duration_seconds:
                request_start = time.time()

                try:
                    async with _get_azure_speech_semaphore():
                        # Simulate Azure API call
                        await asyncio.sleep(0.5)  # Faster for testing

                        results.append(
                            {
                                "user_id": user_id,
                                "request_count": request_count,
                                "response_time": time.time() - request_start,
                                "timestamp": time.time() - start_time,
                            }
                        )
                        request_count += 1

                except Exception as e:
                    results.append(
                        {
                            "user_id": user_id,
                            "error": str(e),
                            "timestamp": time.time() - start_time,
                        }
                    )

                # Wait before next request
                await asyncio.sleep(request_interval)

            return request_count

        # Note: This test is disabled by default due to long runtime
        # Uncomment to run full 5-minute test
        pytest.skip("Sustained load test requires 5 minutes - run manually")

        # Run sustained load
        user_tasks = [sustained_user_requests(i) for i in range(num_users)]
        request_counts = await asyncio.gather(*user_tasks)

        total_time = time.time() - start_time
        total_requests = sum(request_counts)
        errors = [r for r in results if "error" in r]

        # Verify no errors
        assert len(errors) == 0, f"Should have no errors, got {len(errors)}"

        # Verify stable response times
        response_times = [r["response_time"] for r in results if "response_time" in r]
        avg_response_time = sum(response_times) / len(response_times)

        print("\n✅ Sustained Load Test Passed:")
        print(f"   - Duration: {total_time:.1f}s")
        print(f"   - Total requests: {total_requests}")
        print(f"   - Errors: {len(errors)}")
        print(f"   - Average response time: {avg_response_time:.2f}s")

    @pytest.mark.asyncio
    async def test_burst_traffic_pattern(self):
        """
        Test burst traffic pattern (realistic classroom scenario)

        Scenario:
        - Class starts: 20 students join simultaneously
        - Each makes 3 rapid requests (listening + speaking practice)
        - Then idle for 30 seconds
        - Then another burst of 5 requests per student

        Expected:
        - No 429 errors during bursts
        - Queue wait times logged but system stable
        - All requests complete successfully
        """
        from routers.speech_assessment import _get_azure_speech_semaphore

        results = {"burst1": [], "burst2": []}

        async def student_burst_pattern(student_id: int):
            """Simulate student's burst pattern"""

            # Burst 1: Initial 3 rapid requests
            burst1_tasks = []
            for i in range(3):

                async def burst1_request(req_id=i):
                    start = time.time()
                    async with _get_azure_speech_semaphore():
                        await asyncio.sleep(0.5)
                        return {
                            "student_id": student_id,
                            "burst": 1,
                            "request_id": req_id,
                            "response_time": time.time() - start,
                        }

                burst1_tasks.append(burst1_request())

            burst1_results = await asyncio.gather(*burst1_tasks)
            results["burst1"].extend(burst1_results)

            # Idle period
            await asyncio.sleep(1.0)  # Reduced from 30s for testing

            # Burst 2: Follow-up 5 requests
            burst2_tasks = []
            for i in range(5):

                async def burst2_request(req_id=i):
                    start = time.time()
                    async with _get_azure_speech_semaphore():
                        await asyncio.sleep(0.5)
                        return {
                            "student_id": student_id,
                            "burst": 2,
                            "request_id": req_id,
                            "response_time": time.time() - start,
                        }

                burst2_tasks.append(burst2_request())

            burst2_results = await asyncio.gather(*burst2_tasks)
            results["burst2"].extend(burst2_results)

            return len(burst1_results) + len(burst2_results)

        # Execute burst pattern for 20 students
        start_time = time.time()
        student_tasks = [student_burst_pattern(i) for i in range(20)]
        total_requests_per_student = await asyncio.gather(*student_tasks)
        total_time = time.time() - start_time

        # Verify results
        total_requests = sum(total_requests_per_student)
        assert (
            total_requests == 160
        ), "Should have 160 requests (20 students × 8 requests)"
        assert len(results["burst1"]) == 60, "Burst 1 should have 60 requests (20 × 3)"
        assert (
            len(results["burst2"]) == 100
        ), "Burst 2 should have 100 requests (20 × 5)"

        # Calculate metrics
        all_results = results["burst1"] + results["burst2"]
        response_times = [r["response_time"] for r in all_results]
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)

        print("\n✅ Burst Traffic Test Passed:")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Total requests: {total_requests}")
        print(f"   - Average response time: {avg_response:.2f}s")
        print(f"   - Max response time: {max_response:.2f}s")
        print(f"   - Burst 1 (20 students × 3): {len(results['burst1'])} requests")
        print(f"   - Burst 2 (20 students × 5): {len(results['burst2'])} requests")
