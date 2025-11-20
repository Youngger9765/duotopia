"""
Unit tests for thread pool manager

測試 core.thread_pool 模組的線程池管理功能
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor


class TestThreadPoolManager:
    """測試線程池管理器"""

    def test_get_speech_thread_pool(self):
        """測試取得語音線程池"""
        from core.thread_pool import get_speech_thread_pool

        pool = get_speech_thread_pool()

        assert pool is not None
        assert isinstance(pool, ThreadPoolExecutor)
        assert pool._max_workers == 20

    def test_get_audio_thread_pool(self):
        """測試取得音訊線程池"""
        from core.thread_pool import get_audio_thread_pool

        pool = get_audio_thread_pool()

        assert pool is not None
        assert isinstance(pool, ThreadPoolExecutor)
        assert pool._max_workers == 10

    def test_singleton_pattern(self):
        """測試單例模式：多次呼叫返回同一個實例"""
        from core.thread_pool import get_speech_thread_pool, get_audio_thread_pool

        speech_pool_1 = get_speech_thread_pool()
        speech_pool_2 = get_speech_thread_pool()
        assert speech_pool_1 is speech_pool_2

        audio_pool_1 = get_audio_thread_pool()
        audio_pool_2 = get_audio_thread_pool()
        assert audio_pool_1 is audio_pool_2

    def test_get_thread_pool_stats(self):
        """測試取得線程池統計資訊"""
        from core.thread_pool import (
            get_thread_pool_stats,
            get_speech_thread_pool,
            get_audio_thread_pool,
        )

        # 初始化線程池
        get_speech_thread_pool()
        get_audio_thread_pool()

        stats = get_thread_pool_stats()

        assert "speech_pool" in stats
        assert "audio_pool" in stats
        assert stats["speech_pool"]["initialized"] is True
        assert stats["speech_pool"]["max_workers"] == 20
        assert stats["audio_pool"]["initialized"] is True
        assert stats["audio_pool"]["max_workers"] == 10

    @pytest.mark.asyncio
    async def test_thread_pool_async_execution(self):
        """測試線程池在異步環境中正常工作"""
        from core.thread_pool import get_speech_thread_pool

        pool = get_speech_thread_pool()
        loop = asyncio.get_event_loop()

        def blocking_task(value: int) -> int:
            """模擬阻塞任務"""
            time.sleep(0.1)
            return value * 2

        # 在線程池中執行阻塞任務
        result = await loop.run_in_executor(pool, blocking_task, 5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_multiple_async_tasks_concurrent(self):
        """測試多個異步任務並發執行不會阻塞"""
        from core.thread_pool import get_speech_thread_pool

        pool = get_speech_thread_pool()
        loop = asyncio.get_event_loop()

        def blocking_task(task_id: int) -> dict:
            """模擬阻塞任務"""
            start = time.time()
            time.sleep(0.1)  # 100ms
            return {"task_id": task_id, "elapsed": time.time() - start}

        # 並發執行 5 個任務
        start_time = time.time()
        tasks = [loop.run_in_executor(pool, blocking_task, i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 驗證結果
        assert len(results) == 5
        assert all(r["task_id"] in range(5) for r in results)

        # 並發執行應該在 0.3 秒內完成（不是 0.5 秒）
        assert (
            total_time < 0.3
        ), f"Tasks took {total_time:.2f}s, should be < 0.3s (concurrent)"

    @pytest.mark.asyncio
    async def test_thread_pool_handles_exceptions(self):
        """測試線程池正確處理異常"""
        from core.thread_pool import get_speech_thread_pool

        pool = get_speech_thread_pool()
        loop = asyncio.get_event_loop()

        def failing_task():
            """拋出異常的任務"""
            raise ValueError("Test exception")

        # 驗證異常被正確傳播
        with pytest.raises(ValueError, match="Test exception"):
            await loop.run_in_executor(pool, failing_task)

    @pytest.mark.asyncio
    async def test_speech_pool_capacity(self):
        """測試語音線程池容量（20 workers）"""
        from core.thread_pool import get_speech_thread_pool

        pool = get_speech_thread_pool()
        loop = asyncio.get_event_loop()

        def quick_task(task_id: int) -> int:
            time.sleep(0.05)  # 50ms
            return task_id

        # 提交 20 個任務（應該都能立即執行）
        start_time = time.time()
        tasks = [loop.run_in_executor(pool, quick_task, i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        assert len(results) == 20
        # 20 個任務在 20 workers 下應該在 0.1 秒內完成
        assert total_time < 0.15, f"20 tasks took {total_time:.2f}s, should be < 0.15s"

    @pytest.mark.asyncio
    async def test_audio_pool_capacity(self):
        """測試音訊線程池容量（10 workers）"""
        from core.thread_pool import get_audio_thread_pool

        pool = get_audio_thread_pool()
        loop = asyncio.get_event_loop()

        def quick_task(task_id: int) -> int:
            time.sleep(0.05)  # 50ms
            return task_id

        # 提交 10 個任務（應該都能立即執行）
        start_time = time.time()
        tasks = [loop.run_in_executor(pool, quick_task, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        assert len(results) == 10
        # 10 個任務在 10 workers 下應該在 0.1 秒內完成
        assert total_time < 0.15, f"10 tasks took {total_time:.2f}s, should be < 0.15s"

    @pytest.mark.asyncio
    async def test_mixed_sync_and_async(self):
        """測試同步和異步操作混合使用"""
        from core.thread_pool import get_speech_thread_pool

        pool = get_speech_thread_pool()
        loop = asyncio.get_event_loop()

        def sync_operation(value: int) -> int:
            time.sleep(0.1)
            return value + 10

        async def async_operation(value: int) -> int:
            await asyncio.sleep(0.1)
            return value + 20

        # 混合執行同步和異步操作
        start_time = time.time()
        sync_task = loop.run_in_executor(pool, sync_operation, 5)
        async_task = async_operation(5)

        sync_result, async_result = await asyncio.gather(sync_task, async_task)
        total_time = time.time() - start_time

        assert sync_result == 15
        assert async_result == 25
        # 兩個操作應該並發執行，總時間接近單一操作時間
        assert total_time < 0.2, f"Mixed operations took {total_time:.2f}s"


class TestThreadPoolShutdown:
    """測試線程池關閉功能"""

    def test_shutdown_thread_pools(self):
        """測試優雅關閉線程池"""
        from core.thread_pool import (
            get_speech_thread_pool,
            get_audio_thread_pool,
            shutdown_thread_pools,
            get_thread_pool_stats,
        )

        # 初始化線程池
        speech_pool = get_speech_thread_pool()
        audio_pool = get_audio_thread_pool()

        assert speech_pool is not None
        assert audio_pool is not None

        # 關閉線程池
        shutdown_thread_pools(wait=True)

        # 驗證統計資訊顯示未初始化
        stats = get_thread_pool_stats()
        assert stats["speech_pool"]["initialized"] is False
        assert stats["audio_pool"]["initialized"] is False

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_tasks(self):
        """測試關閉時等待任務完成"""
        from core.thread_pool import get_speech_thread_pool, shutdown_thread_pools
        import threading

        pool = get_speech_thread_pool()
        loop = asyncio.get_event_loop()

        task_completed = threading.Event()

        def long_running_task():
            time.sleep(0.2)
            task_completed.set()
            return "completed"

        # 提交任務
        loop.run_in_executor(pool, long_running_task)

        # 關閉線程池（等待任務完成）
        shutdown_thread_pools(wait=True)

        # 驗證任務已完成
        assert task_completed.is_set()


class TestEnvironmentConfiguration:
    """測試環境變數配置"""

    def test_default_thread_pool_sizes(self, monkeypatch):
        """測試預設線程池大小"""
        # 移除環境變數（使用預設值）
        monkeypatch.delenv("SPEECH_THREAD_POOL_SIZE", raising=False)
        monkeypatch.delenv("AUDIO_THREAD_POOL_SIZE", raising=False)

        # 需要重新導入以清除單例
        import importlib
        import core.thread_pool

        importlib.reload(core.thread_pool)

        from core.thread_pool import get_speech_thread_pool, get_audio_thread_pool

        speech_pool = get_speech_thread_pool()
        audio_pool = get_audio_thread_pool()

        assert speech_pool._max_workers == 20  # 預設值
        assert audio_pool._max_workers == 10  # 預設值

        # 清理
        from core.thread_pool import shutdown_thread_pools

        shutdown_thread_pools()

    def test_custom_thread_pool_sizes(self, monkeypatch):
        """測試自訂線程池大小"""
        # 設定環境變數
        monkeypatch.setenv("SPEECH_THREAD_POOL_SIZE", "30")
        monkeypatch.setenv("AUDIO_THREAD_POOL_SIZE", "15")

        # 重新導入以套用新的環境變數
        import importlib
        import core.thread_pool

        importlib.reload(core.thread_pool)

        from core.thread_pool import get_speech_thread_pool, get_audio_thread_pool

        speech_pool = get_speech_thread_pool()
        audio_pool = get_audio_thread_pool()

        assert speech_pool._max_workers == 30
        assert audio_pool._max_workers == 15

        # 清理
        from core.thread_pool import shutdown_thread_pools

        shutdown_thread_pools()
