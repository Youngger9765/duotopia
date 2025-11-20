"""
Thread Pool Manager for async I/O operations

管理自訂線程池以處理阻塞式 I/O 操作（如 Azure Speech API）
確保並發處理效能並與 Cloud Run concurrency 設定協調
"""

import concurrent.futures
import os
import logging

logger = logging.getLogger(__name__)

# 全域線程池實例
_speech_thread_pool: concurrent.futures.ThreadPoolExecutor = None
_audio_thread_pool: concurrent.futures.ThreadPoolExecutor = None


def get_speech_thread_pool() -> concurrent.futures.ThreadPoolExecutor:
    """
    取得語音處理專用線程池（用於 Azure Speech SDK）

    線程池大小與 Cloud Run concurrency 設定協調：
    - Cloud Run concurrency: 20 (每個 instance 同時處理 20 個請求)
    - Thread pool workers: 20 (確保每個請求都能立即取得線程)

    Returns:
        ThreadPoolExecutor: 語音處理線程池
    """
    global _speech_thread_pool

    if _speech_thread_pool is None:
        # 從環境變數讀取或使用預設值
        max_workers = int(os.getenv("SPEECH_THREAD_POOL_SIZE", "20"))

        _speech_thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="speech_worker"
        )
        logger.info(f"✅ Speech thread pool initialized with {max_workers} workers")

    return _speech_thread_pool


def get_audio_thread_pool() -> concurrent.futures.ThreadPoolExecutor:
    """
    取得音訊處理專用線程池（用於音檔格式轉換）

    Returns:
        ThreadPoolExecutor: 音訊處理線程池
    """
    global _audio_thread_pool

    if _audio_thread_pool is None:
        # 音訊轉換通常較快，使用較小的線程池
        max_workers = int(os.getenv("AUDIO_THREAD_POOL_SIZE", "10"))

        _audio_thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="audio_worker"
        )
        logger.info(f"✅ Audio thread pool initialized with {max_workers} workers")

    return _audio_thread_pool


def shutdown_thread_pools(wait: bool = True):
    """
    關閉所有線程池（應用程式關閉時呼叫）

    Args:
        wait: 是否等待所有任務完成
    """
    global _speech_thread_pool, _audio_thread_pool

    if _speech_thread_pool is not None:
        logger.info("🔄 Shutting down speech thread pool...")
        _speech_thread_pool.shutdown(wait=wait)
        _speech_thread_pool = None
        logger.info("✅ Speech thread pool shutdown complete")

    if _audio_thread_pool is not None:
        logger.info("🔄 Shutting down audio thread pool...")
        _audio_thread_pool.shutdown(wait=wait)
        _audio_thread_pool = None
        logger.info("✅ Audio thread pool shutdown complete")


def get_thread_pool_stats() -> dict:
    """
    取得線程池統計資訊（用於監控）

    Returns:
        dict: 線程池狀態資訊
    """
    stats = {
        "speech_pool": {
            "initialized": _speech_thread_pool is not None,
            "max_workers": int(os.getenv("SPEECH_THREAD_POOL_SIZE", "20")),
        },
        "audio_pool": {
            "initialized": _audio_thread_pool is not None,
            "max_workers": int(os.getenv("AUDIO_THREAD_POOL_SIZE", "10")),
        },
    }

    return stats
