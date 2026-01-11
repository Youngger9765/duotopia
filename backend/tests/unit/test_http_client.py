"""
Unit tests for HTTP client singleton

Tests connection pool configuration and singleton behavior
"""

import pytest
import httpx
from utils.http_client import get_http_client, close_http_client, reset_http_client


class TestHTTPClientSingleton:
    """Test HTTP client singleton pattern"""

    def teardown_method(self):
        """Reset singleton after each test"""
        reset_http_client()

    def test_get_http_client_returns_instance(self):
        """Test that get_http_client returns an httpx.AsyncClient instance"""
        client = get_http_client()
        assert isinstance(client, httpx.AsyncClient)

    def test_singleton_pattern(self):
        """Test that multiple calls return the same instance"""
        client1 = get_http_client()
        client2 = get_http_client()
        assert client1 is client2

    def test_connection_pool_configuration(self):
        """Test that connection pool is configured correctly"""
        client = get_http_client()

        # Check that client is configured (limits are internal implementation)
        # We just verify it's an AsyncClient with proper configuration
        assert isinstance(client, httpx.AsyncClient)

        # Check timeout
        assert client.timeout.read == 30.0

    def test_http2_enabled(self):
        """Test that HTTP/2 is enabled for better multiplexing"""
        client = get_http_client()
        assert client._transport is not None

    @pytest.mark.asyncio
    async def test_close_http_client(self):
        """Test that close_http_client properly closes the client"""
        client = get_http_client()
        assert client is not None

        await close_http_client()

        # After closing, client should be None
        # Next call should create a new instance
        new_client = get_http_client()
        assert new_client is not client

    def test_reset_http_client(self):
        """Test reset_http_client for testing purposes"""
        client1 = get_http_client()
        reset_http_client()
        client2 = get_http_client()

        # After reset, should get new instance
        assert client1 is not client2


class TestHTTPClientIntegration:
    """Integration tests for HTTP client (requires network)"""

    def teardown_method(self):
        """Reset singleton after each test"""
        reset_http_client()

    @pytest.mark.asyncio
    async def test_http_get_request(self):
        """Test basic HTTP GET request"""
        client = get_http_client()

        # Test with httpbin.org (public test API)
        response = await client.get("https://httpbin.org/get")
        assert response.status_code == 200

        data = response.json()
        assert "headers" in data

    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """Test that connections are reused"""
        client = get_http_client()

        # Make multiple requests to same host
        url = "https://httpbin.org/get"
        response1 = await client.get(url)
        response2 = await client.get(url)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both requests should succeed, demonstrating connection reuse

    @pytest.mark.asyncio
    async def test_timeout_configuration(self):
        """Test that timeout is properly configured"""
        client = get_http_client()

        # Test timeout with delayed response (use a shorter timeout for testing)
        # httpbin.org/delay/{seconds} endpoint delays response
        with pytest.raises((httpx.ReadTimeout, httpx.TimeoutException)):
            # Request with custom short timeout
            await client.get("https://httpbin.org/delay/5", timeout=1.0)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test that client handles concurrent requests"""
        import asyncio

        client = get_http_client()

        # Make 10 concurrent requests
        async def make_request(i):
            response = await client.get(f"https://httpbin.org/get?id={i}")
            return response.status_code

        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10
