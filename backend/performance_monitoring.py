"""
效能監控模組 - OpenTelemetry + GCP Cloud Trace
使用方式：
1. 在需要監控的函數上加 @trace_function decorator
2. 在函數內部使用 with start_span("操作名稱") 記錄子步驟
"""

import time
import logging
from functools import wraps
from typing import Optional, Dict, Any
from contextlib import contextmanager

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource

# Google Cloud Logging
from google.cloud import logging as cloud_logging

# 初始化 GCP Logging
try:
    client = cloud_logging.Client()
    client.setup_logging()
    logger = logging.getLogger(__name__)
except Exception as e:
    print(f"⚠️  Warning: Failed to initialize GCP logging: {e}")
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# 初始化 OpenTelemetry
try:
    import os

    # 檢查是否有 Application Default Credentials
    adc_path = os.path.expanduser(
        "~/.config/gcloud/application_default_credentials.json"
    )

    if not os.path.exists(adc_path):
        logger.warning(
            "⚠️  Cloud Trace 需要 GCP 認證。請執行: gcloud auth application-default login"
        )
        raise FileNotFoundError("Application Default Credentials not found")

    # 設定 resource（標記你的服務）
    resource = Resource.create({"service.name": "duotopia-backend"})

    # 設定 tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))

    # 添加 Cloud Trace exporter
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(CloudTraceSpanExporter())
    )

    tracer = trace.get_tracer(__name__)
    TRACING_ENABLED = True
    logger.info("✅ OpenTelemetry + Cloud Trace initialized")
except Exception as e:
    logger.warning(f"⚠️  Cloud Trace not available: {e}. Using simple timing.")
    tracer = None
    TRACING_ENABLED = False


# ============ Decorator for automatic function tracing ============


def trace_function(span_name: Optional[str] = None):
    """
    Decorator to automatically trace function execution time

    使用範例：
    @trace_function()
    def my_slow_function():
        time.sleep(1)

    @trace_function("Custom Span Name")
    def another_function():
        pass
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"

            if TRACING_ENABLED and tracer:
                with tracer.start_as_current_span(name) as span:
                    start_time = time.perf_counter()
                    try:
                        result = await func(*args, **kwargs)
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        span.set_attribute("duration_ms", duration_ms)
                        print(f"⏱️  {name}: {duration_ms:.2f}ms")  # 直接 print
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        raise
            else:
                # Fallback: simple timing
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    print(f"⏱️  {name}: {duration_ms:.2f}ms")  # 直接 print
                    return result
                except Exception as e:
                    logger.error(f"❌ {name} failed: {e}")
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"

            if TRACING_ENABLED and tracer:
                with tracer.start_as_current_span(name) as span:
                    start_time = time.perf_counter()
                    try:
                        result = func(*args, **kwargs)
                        duration_ms = (time.perf_counter() - start_time) * 1000
                        span.set_attribute("duration_ms", duration_ms)
                        print(f"⏱️  {name}: {duration_ms:.2f}ms")  # 直接 print
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        raise
            else:
                # Fallback: simple timing
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    print(f"⏱️  {name}: {duration_ms:.2f}ms")  # 直接 print
                    return result
                except Exception as e:
                    logger.error(f"❌ {name} failed: {e}")
                    raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============ Context manager for manual span creation ============


@contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager to manually create a span

    使用範例：
    with start_span("Database Query", {"query": "SELECT * FROM users"}):
        result = db.execute(query)
    """
    if TRACING_ENABLED and tracer:
        with tracer.start_as_current_span(name) as span:
            start_time = time.perf_counter()
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                span.set_attribute("duration_ms", duration_ms)
                print(f"⏱️  {name}: {duration_ms:.2f}ms")  # 直接 print
    else:
        # Fallback: simple timing
        start_time = time.perf_counter()
        try:
            yield None
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            print(f"⏱️  {name}: {duration_ms:.2f}ms")  # 直接 print


# ============ Performance snapshot utility ============


class PerformanceSnapshot:
    """記錄效能快照，用於比較不同版本的效能差異"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = time.perf_counter()
        self.checkpoints: Dict[str, float] = {}

    def checkpoint(self, label: str):
        """記錄檢查點"""
        elapsed = (time.perf_counter() - self.start_time) * 1000
        self.checkpoints[label] = elapsed
        print(f"📍 {self.name} - {label}: {elapsed:.2f}ms")  # 直接 print

    def finish(self) -> Dict[str, float]:
        """完成並返回所有檢查點"""
        total = (time.perf_counter() - self.start_time) * 1000
        self.checkpoints["total"] = total
        print(f"🏁 {self.name} - Total: {total:.2f}ms")  # 直接 print
        print(f"📊 Breakdown: {self.checkpoints}")  # 直接 print
        return self.checkpoints


# ============ Example usage ============

if __name__ == "__main__":
    # 測試 trace_function decorator
    @trace_function()
    def slow_function():
        time.sleep(0.5)
        return "done"

    # 測試 start_span context manager
    with start_span("Test Operation", {"test_id": 123}):
        time.sleep(0.2)

    # 測試 PerformanceSnapshot
    snapshot = PerformanceSnapshot("Test Workflow")
    time.sleep(0.1)
    snapshot.checkpoint("Step 1")
    time.sleep(0.2)
    snapshot.checkpoint("Step 2")
    results = snapshot.finish()

    print("\n✅ Performance monitoring test completed")
    print(f"📊 Results: {results}")
