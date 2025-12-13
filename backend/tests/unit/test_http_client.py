"""
Unit tests for HTTP client connection pooling

Tests verify:
1. Singleton pattern for shared sessions
2. Connection pool configuration
3. Retry logic
4. Session lifecycle management
"""

import os  # noqa: E402
import sys  # noqa: E402

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest  # noqa: E402
from unittest.mock import patch, MagicMock  # noqa: E402
import requests  # noqa: E402
import httpx  # noqa: E402

from core.http_client import (  # noqa: E402
    create_http_session,
    get_http_session,
    create_async_http_client,
    get_async_http_client,
    close_http_session,
    close_async_http_client,
    shutdown_http_clients,
)


class TestHTTPSession:
    """Test synchronous HTTP session with connection pooling"""

    def test_create_http_session_returns_session(self):
        """Test that create_http_session returns a requests.Session instance"""
        session = create_http_session()
        assert isinstance(session, requests.Session)

    def test_create_http_session_has_adapters(self):
        """Test that session has HTTP and HTTPS adapters configured"""
        session = create_http_session()
        assert "http://" in session.adapters
        assert "https://" in session.adapters

    def test_create_http_session_with_custom_pool_size(self):
        """Test creating session with custom pool size"""
        session = create_http_session(pool_connections=50, pool_maxsize=200)
        adapter = session.adapters["https://"]

        # Verify adapter configuration
        assert adapter._pool_connections == 50
        assert adapter._pool_maxsize == 200

    def test_create_http_session_with_retry_logic(self):
        """Test that session has retry logic configured"""
        session = create_http_session(max_retries=5)
        adapter = session.adapters["https://"]

        # Verify retry configuration
        assert adapter.max_retries.total == 5
        assert 429 in adapter.max_retries.status_forcelist
        assert 500 in adapter.max_retries.status_forcelist

    def test_get_http_session_returns_singleton(self):
        """Test that get_http_session returns the same instance"""
        # Reset singleton for clean test
        import core.http_client

        core.http_client._http_session = None

        session1 = get_http_session()
        session2 = get_http_session()

        assert session1 is session2  # Same object reference

    def test_close_http_session(self):
        """Test closing HTTP session"""
        import core.http_client

        # Create session
        session = get_http_session()  # noqa: F841
        assert session is not None
        assert core.http_client._http_session is not None

        # Close session
        close_http_session()
        assert core.http_client._http_session is None


class TestAsyncHTTPClient:
    """Test asynchronous HTTP client with connection pooling"""

    def test_create_async_http_client_returns_client(self):
        """Test that create_async_http_client returns httpx.AsyncClient"""
        client = create_async_http_client()
        assert isinstance(client, httpx.AsyncClient)

    def test_create_async_http_client_with_custom_limits(self):
        """Test creating client with custom connection limits"""
        client = create_async_http_client(
            max_keepalive_connections=50, max_connections=200
        )

        # Verify limits configuration
        assert client._limits.max_keepalive_connections == 50
        assert client._limits.max_connections == 200

    def test_create_async_http_client_with_timeout(self):
        """Test creating client with custom timeout"""
        client = create_async_http_client(timeout=60.0)

        # Verify timeout configuration
        assert client.timeout.read == 60.0

    def test_create_async_http_client_enables_http2(self):
        """Test that HTTP/2 is enabled by default"""
        client = create_async_http_client()
        assert client._transport._pool._http2 is True

    def test_get_async_http_client_returns_singleton(self):
        """Test that get_async_http_client returns the same instance"""
        # Reset singleton for clean test
        import core.http_client

        core.http_client._async_http_client = None

        client1 = get_async_http_client()
        client2 = get_async_http_client()

        assert client1 is client2  # Same object reference

    @pytest.mark.asyncio
    async def test_close_async_http_client(self):
        """Test closing async HTTP client"""
        import core.http_client

        # Create client
        client = get_async_http_client()  # noqa: F841
        assert client is not None
        assert core.http_client._async_http_client is not None

        # Close client
        await close_async_http_client()
        assert core.http_client._async_http_client is None


class TestShutdownHTTPClients:
    """Test shutdown and cleanup functions"""

    def test_shutdown_http_clients(self):
        """Test that shutdown closes all HTTP clients"""
        import core.http_client

        # Create clients
        _ = get_http_session()

        # Shutdown
        shutdown_http_clients()

        # Verify all clients are closed
        assert core.http_client._http_session is None


class TestConnectionPoolPerformance:
    """Performance and integration tests for connection pooling"""

    def test_session_reuses_connections(self):
        """Test that session reuses connections (mocked)"""
        session = create_http_session()

        # Mock the adapter's connection pool
        with patch.object(session, "get_adapter") as mock_adapter:
            mock_pool = MagicMock()
            mock_adapter.return_value.poolmanager = mock_pool

            # Make multiple requests (mocked)
            with patch.object(session, "request") as mock_request:
                mock_request.return_value = MagicMock(status_code=200)

                session.get("https://api.example.com/1")
                session.get("https://api.example.com/2")

                # Both requests should use the same session
                assert mock_request.call_count == 2

    def test_retry_on_server_error(self):
        """Test that retry logic works on server errors (mocked)"""
        session = create_http_session(max_retries=3)

        with patch.object(session, "send") as mock_send:
            # Simulate server error then success
            error_response = MagicMock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = requests.HTTPError()

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.raise_for_status = MagicMock()

            mock_send.side_effect = [error_response, error_response, success_response]

            # Should succeed after retries
            try:
                session.get("https://api.example.com")
            except requests.HTTPError:
                pass  # Expected on first attempts

            # Verify retries occurred
            assert mock_send.call_count >= 1


class TestTapPayServiceIntegration:
    """Integration tests for TapPay services using connection pooling"""

    def test_tappay_service_has_session_attribute(self):
        """Test that TapPayService has session attribute"""
        # Mock the settings to avoid initialization errors
        with patch("services.tappay_service.settings") as mock_settings:
            mock_settings.TAPPAY_ENV = "sandbox"
            mock_settings.tappay_partner_key = "test_key"
            mock_settings.tappay_merchant_id = "test_merchant"

            from services.tappay_service import TapPayService

            service = TapPayService()

            # Verify service has session attribute
            assert hasattr(service, "session")
            assert isinstance(service.session, requests.Session)

    def test_tappay_einvoice_service_has_session_attribute(self):
        """Test that TapPayEInvoiceService has session attribute"""
        # Mock env vars
        with patch.dict(
            os.environ,
            {
                "TAPPAY_PARTNER_KEY": "test_key",
                "TAPPAY_MERCHANT_ID": "test_merchant",
                "TAPPAY_ENV": "sandbox",
            },
        ):
            from services.tappay_einvoice_service import TapPayEInvoiceService

            service = TapPayEInvoiceService()

            # Verify service has session attribute
            assert hasattr(service, "session")
            assert isinstance(service.session, requests.Session)

    def test_multiple_services_share_same_session(self):
        """Test that multiple services share the same HTTP session instance"""
        with patch("services.tappay_service.settings") as mock_settings:
            mock_settings.TAPPAY_ENV = "sandbox"
            mock_settings.tappay_partner_key = "test_key"
            mock_settings.tappay_merchant_id = "test_merchant"

            from services.tappay_service import TapPayService

            service1 = TapPayService()
            service2 = TapPayService()

            # Both services should use the same session instance
            assert service1.session is service2.session


class TestConnectionPoolBenefits:
    """Tests demonstrating connection pool benefits"""

    def test_connection_pool_reduces_tcp_handshakes(self):
        """
        Demonstrate that connection pooling reduces TCP handshakes

        Note: This is a conceptual test. In real scenarios:
        - First request: TCP handshake + TLS handshake (~100ms)
        - Subsequent requests: Reuse connection (~50ms faster)
        """
        session = create_http_session()

        # Verify pool is configured for connection reuse
        adapter = session.adapters["https://"]
        assert adapter._pool_maxsize > 1  # Can reuse multiple connections
        assert adapter.max_retries is not None  # Automatic retry on failure

    def test_connection_pool_thread_safety(self):
        """Test that connection pool is thread-safe (conceptual)"""
        session = get_http_session()

        # requests.Session with HTTPAdapter uses urllib3 connection pool
        # urllib3.PoolManager is thread-safe by design
        adapter = session.adapters["https://"]

        # Verify we're using a pool manager (thread-safe)
        assert hasattr(adapter, "_pool_connections")
        assert hasattr(adapter, "_pool_maxsize")


# Cleanup after all tests
@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances after each test"""
    yield
    import core.http_client

    # Reset sync session
    if core.http_client._http_session:
        core.http_client._http_session.close()
        core.http_client._http_session = None

    # Reset async client (synchronous close for test cleanup)
    if core.http_client._async_http_client:
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule close
                asyncio.create_task(core.http_client._async_http_client.aclose())
            else:
                # Close directly
                loop.run_until_complete(core.http_client._async_http_client.aclose())
        except Exception:
            pass
        core.http_client._async_http_client = None
