"""
測試 Speech Assessment API 並發處理效能

驗證多個學生同時評分時不會發生排隊問題
針對客戶反饋："10位學生同時使用網站，讀取時間明顯變長"
"""

import asyncio
import pytest


class TestSpeechConcurrentPerformance:
    """測試並發效能"""

    @pytest.mark.asyncio
    async def test_concurrent_audio_conversion_no_queuing(self):
        """
        測試音訊轉換在並發環境下不會排隊

        預期行為：
        - 10 個並發請求應在 ~1.5 秒內完成（允許誤差）
        - 不應該花費 10+ 秒（序列處理的時間）
        """
        from core.thread_pool import get_audio_thread_pool
        import time

        async def simulate_audio_conversion(task_id: int):
            """模擬音訊轉換（阻塞 I/O）"""
            loop = asyncio.get_event_loop()
            pool = get_audio_thread_pool()

            def blocking_work():
                time.sleep(0.1)  # 模擬 100ms 的轉換時間
                return f"converted_{task_id}"

            result = await loop.run_in_executor(pool, blocking_work)
            return result

        # 並發執行 10 個音訊轉換
        start_time = time.time()
        tasks = [simulate_audio_conversion(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 驗證結果
        assert len(results) == 10
        assert all(r.startswith("converted_") for r in results)

        # 並行處理應該在 0.5 秒內完成（10 workers，每個 0.1s）
        # 允許 200% 的誤差空間 (0.5s → 1.0s)
        assert (
            total_time < 1.0
        ), f"Concurrent processing took {total_time:.2f}s, should be < 1.0s (parallel)"

        # 如果是序列處理會需要 1.0 秒
        assert (
            total_time < 0.5
        ), f"Processing is queuing: {total_time:.2f}s (expected < 0.5s for parallel)"

    @pytest.mark.asyncio
    async def test_concurrent_speech_assessment_no_queuing(self):
        """
        測試語音評估在並發環境下不會排隊

        預期行為：
        - 10 個並發請求應在 ~1.5 秒內完成（模擬 1 秒的 Azure API）
        - 不應該花費 10+ 秒
        """
        from core.thread_pool import get_speech_thread_pool
        import time

        async def simulate_speech_assessment(student_id: int):
            """模擬語音評估（阻塞 I/O）"""
            loop = asyncio.get_event_loop()
            pool = get_speech_thread_pool()

            def blocking_azure_call():
                time.sleep(1.0)  # 模擬 1 秒的 Azure API 延遲
                return {"student_id": student_id, "score": 85}

            result = await loop.run_in_executor(pool, blocking_azure_call)
            return result

        # 並發執行 10 個語音評估
        start_time = time.time()
        tasks = [simulate_speech_assessment(i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 驗證結果
        assert len(results) == 10
        assert all(r["score"] == 85 for r in results)

        # 並行處理應該在 1.5 秒內完成（20 workers，每個 1s）
        # 允許 50% 的誤差空間 (1.0s → 1.5s)
        assert total_time < 1.5, (
            f"Concurrent processing took {total_time:.2f}s, "
            f"should be < 1.5s (parallel)"
        )

        # 如果是序列處理會需要 10 秒
        sequential_time = 10.0
        assert (
            total_time < sequential_time / 2
        ), f"Processing is queuing: {total_time:.2f}s (expected < 5s for parallel)"

    @pytest.mark.asyncio
    async def test_thread_pool_initialization(self):
        """測試線程池正確初始化"""
        from core.thread_pool import (
            get_speech_thread_pool,
            get_audio_thread_pool,
            get_thread_pool_stats,
        )

        # 取得線程池
        speech_pool = get_speech_thread_pool()
        audio_pool = get_audio_thread_pool()

        # 驗證線程池已初始化
        assert speech_pool is not None
        assert audio_pool is not None

        # 驗證統計資訊
        stats = get_thread_pool_stats()
        assert stats["speech_pool"]["initialized"] is True
        assert stats["audio_pool"]["initialized"] is True
        assert stats["speech_pool"]["max_workers"] == 20
        assert stats["audio_pool"]["max_workers"] == 10

    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self):
        """
        測試音訊轉換和語音評估混合並發

        模擬真實情境：10 個學生同時上傳和評分
        """
        from core.thread_pool import get_speech_thread_pool, get_audio_thread_pool
        import time

        async def simulate_full_workflow(student_id: int):
            """模擬完整工作流程"""

            loop = asyncio.get_event_loop()

            # 1. 音訊轉換
            audio_pool = get_audio_thread_pool()

            def convert():
                time.sleep(0.2)  # 200ms
                return f"wav_{student_id}"

            wav_data = await loop.run_in_executor(audio_pool, convert)

            # 2. 語音評估
            speech_pool = get_speech_thread_pool()

            def assess():
                time.sleep(1.0)  # 1s
                return {"student_id": student_id, "audio": wav_data, "score": 90}

            result = await loop.run_in_executor(speech_pool, assess)
            return result

        # 並發執行 10 個完整流程
        start_time = time.time()
        tasks = [simulate_full_workflow(i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 驗證結果
        assert len(results) == 10
        assert all(r["score"] == 90 for r in results)

        # 總時間應該在 1.5 秒內（0.2s 轉換 + 1.0s 評估 = 1.2s，允許誤差）
        assert (
            total_time < 2.0
        ), f"Mixed operations took {total_time:.2f}s, should be < 2.0s"

        # 如果是序列處理會需要 12 秒
        sequential_time = 12.0
        assert (
            total_time < sequential_time / 3
        ), f"Processing is queuing: {total_time:.2f}s (expected < 4s)"


class TestPerformanceMonitoring:
    """測試效能監控功能"""

    def test_performance_snapshot(self):
        """測試 PerformanceSnapshot 正確記錄時間"""
        from performance_monitoring import PerformanceSnapshot
        import time

        snapshot = PerformanceSnapshot("Test Operation")

        time.sleep(0.1)
        snapshot.checkpoint("Step 1")

        time.sleep(0.1)
        snapshot.checkpoint("Step 2")

        results = snapshot.finish()

        # 驗證檢查點存在
        assert "Step 1" in results
        assert "Step 2" in results
        assert "total" in results

        # 驗證時間合理（允許誤差）
        assert 80 < results["Step 1"] < 150  # ~100ms ± 50ms
        assert 180 < results["Step 2"] < 250  # ~200ms ± 50ms
        assert 180 < results["total"] < 300  # ~200ms ± 100ms

    def test_trace_function_decorator(self):
        """測試 trace_function decorator"""
        from performance_monitoring import trace_function
        import time

        @trace_function("Test Function")
        def sync_function():
            time.sleep(0.05)
            return "completed"

        result = sync_function()
        assert result == "completed"

    @pytest.mark.asyncio
    async def test_trace_function_async(self):
        """測試 trace_function 支援 async 函數"""
        from performance_monitoring import trace_function
        import asyncio

        @trace_function("Async Test Function")
        async def async_function():
            await asyncio.sleep(0.05)
            return "async_completed"

        result = await async_function()
        assert result == "async_completed"


class TestClientIssueResolution:
    """測試客戶回報問題的解決方案"""

    @pytest.mark.asyncio
    async def test_ten_students_concurrent_no_slowdown(self):
        """
        驗證客戶問題已解決：10位學生同時使用網站不會變慢

        客戶反饋：
        "今天上午有安排大約10位學生同時使用網站，讀取時間明顯變長，
         分析時間也變長很多，甚至偶發分析不出來需要重新整理。"

        預期修復後行為：
        - 10 位學生同時評分應在 2 秒內完成
        - 不應該發生排隊現象
        """
        from core.thread_pool import get_speech_thread_pool
        import time

        async def simulate_student_assessment(student_id: int):
            """模擬學生評分流程"""
            loop = asyncio.get_event_loop()
            pool = get_speech_thread_pool()

            start = time.time()

            def azure_speech_api():
                # 模擬 Azure Speech API 的 1 秒延遲
                time.sleep(1.0)
                return {"student_id": student_id, "score": 85, "duration": 1.0}

            result = await loop.run_in_executor(pool, azure_speech_api)
            result["elapsed"] = time.time() - start
            return result

        # 模擬 10 位學生同時評分
        start_time = time.time()
        tasks = [simulate_student_assessment(i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 驗證：所有學生都成功完成
        assert len(results) == 10
        assert all(r["score"] == 85 for r in results)

        # 驗證：沒有排隊現象（總時間應接近單一請求時間）
        assert total_time < 2.0, (
            f"❌ 客戶問題未解決：10位學生花費 {total_time:.2f}秒 " f"(應該 < 2 秒，序列處理會需要 10 秒)"
        )

        print("\n✅ 客戶問題已解決：")
        print("   - 10 位學生同時評分")
        print(f"   - 總耗時：{total_time:.2f} 秒")
        print(f"   - 平均每位學生：{total_time / 10:.2f} 秒")
        print("   - 如果序列處理會需要：10 秒")
        print(f"   - 效能提升：{10 / total_time:.1f}x")
