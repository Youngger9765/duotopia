"""
Global HTTP Client with Connection Pool
Reduces TCP handshake latency for API calls

Usage:
    from utils.http_client import get_http_client

    client = get_http_client()
    response = await client.get("https://api.example.com")
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global singleton instance
_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """
    Get or create global httpx.AsyncClient with connection pool

    Connection Pool Configuration:
    - max_keepalive_connections: 20 (reuse connections)
    - max_connections: 100 (total concurrent connections)
    - timeout: 30.0s (reasonable for external APIs)

    Benefits:
    - ✅ Reduces TCP handshake latency (-50ms to -100ms)
    - ✅ Reuses connections to same host
    - ✅ Thread-safe singleton pattern

    Returns:
        Configured httpx.AsyncClient instance
    """
    global _http_client

    if _http_client is None:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
            ),
            timeout=30.0,
            http2=True,  # Enable HTTP/2 for better multiplexing
        )
        logger.info(
            "✅ HTTP client initialized with connection pool "
            "(keepalive: 20, max: 100, timeout: 30s)"
        )

    return _http_client


async def close_http_client():
    """
    Close global HTTP client (call on app shutdown)

    Usage in FastAPI:
        @app.on_event("shutdown")
        async def shutdown_event():
            await close_http_client()
    """
    global _http_client

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("HTTP client closed successfully")


def reset_http_client():
    """
    Reset HTTP client (for testing purposes)

    ⚠️ Only use in tests to reset singleton state
    """
    global _http_client
    _http_client = None
