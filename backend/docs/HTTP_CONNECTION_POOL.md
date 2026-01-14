# HTTP Connection Pool Implementation

## Overview

This document describes the HTTP connection pool implementation for Duotopia backend, addressing issue #91: reducing TCP handshake latency for external API calls.

## Problem Statement

Previously, services using OpenAI/Azure SDK created new HTTP connections for each request, causing:
- TCP handshake latency (50-100ms overhead per request)
- Inefficient resource usage
- Slower API response times

## Solution

Implemented a global `httpx.AsyncClient` singleton with connection pooling to:
- ✅ Reuse TCP connections to same hosts
- ✅ Reduce API call latency by 50-100ms
- ✅ Improve resource efficiency
- ✅ Enable HTTP/2 multiplexing

## Architecture

### Global HTTP Client Singleton

**Location**: `backend/utils/http_client.py`

```python
from utils.http_client import get_http_client

# Get shared client
client = get_http_client()

# Use for HTTP requests
response = await client.get("https://api.example.com")
```

### Configuration

```python
httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,  # Reuse up to 20 connections
        max_connections=100,            # Total concurrent connections
    ),
    timeout=30.0,                       # 30 second timeout
    http2=True,                         # Enable HTTP/2
)
```

### Lifecycle Management

The HTTP client is managed by FastAPI lifecycle events:

**Startup** (`main.py`):
```python
@app.on_event("startup")
async def startup_event():
    # Initialize HTTP client connection pool
    from utils.http_client import get_http_client
    get_http_client()
```

**Shutdown** (`main.py`):
```python
@app.on_event("shutdown")
async def shutdown_event():
    # Close HTTP client connection pool
    from utils.http_client import close_http_client
    await close_http_client()
```

## Migrated Services

### 1. Translation Service

**File**: `backend/services/translation.py`

**Changes**:
- Migrated from synchronous `OpenAI` to `AsyncOpenAI`
- All API calls now use `await` (async)
- Uses shared `http_client` for connection pooling

**Before**:
```python
from openai import OpenAI

self.client = OpenAI(api_key=api_key)
response = self.client.chat.completions.create(...)  # Sync call
```

**After**:
```python
from openai import AsyncOpenAI
from utils.http_client import get_http_client

self.client = AsyncOpenAI(
    api_key=api_key,
    http_client=get_http_client()
)
response = await self.client.chat.completions.create(...)  # Async call
```

### 2. Billing Analysis Service

**File**: `backend/services/billing_analysis_service.py`

**Changes**:
- Already using `AsyncOpenAI`, added shared `http_client`

**Before**:
```python
self.client = AsyncOpenAI(api_key=self.openai_api_key)
```

**After**:
```python
from utils.http_client import get_http_client

self.client = AsyncOpenAI(
    api_key=self.openai_api_key,
    http_client=get_http_client()
)
```

### 3. Azure Speech Token Service

**File**: `backend/services/azure_speech_token.py`

**Changes**:
- Removed per-request `AsyncClient` context manager
- Now uses shared global client

**Before**:
```python
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.post(url, headers=headers)
```

**After**:
```python
from utils.http_client import get_http_client

client = get_http_client()
response = await client.post(url, headers=headers, timeout=10.0)
```

### 4. TapPay Service (Not Migrated)

**File**: `backend/services/tappay_service.py`

**Status**: Uses synchronous `requests` library, not migrated

**Reason**:
- Service runs in synchronous context
- TapPay calls are infrequent (payment transactions)
- Migration would require async/await refactoring of entire payment flow

**Future Consideration**: Can be migrated if TapPay service is refactored to async

## Testing

### Unit Tests

**File**: `backend/tests/unit/test_http_client.py`

Tests cover:
- ✅ Singleton pattern (same instance returned)
- ✅ Connection pool configuration
- ✅ HTTP/2 enabled
- ✅ Lifecycle management (startup/shutdown)
- ✅ Concurrent requests
- ✅ Connection reuse
- ✅ Timeout configuration

**Run tests**:
```bash
pytest tests/unit/test_http_client.py -v
```

### Regression Tests

Updated tests for services using HTTP client:
- `tests/unit/test_azure_speech_token_api.py` - Mock `get_http_client` instead of `httpx.AsyncClient`

**Run regression tests**:
```bash
pytest tests/unit/test_azure_speech_token_api.py -v
```

## Performance Benefits

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| TCP Handshake | Every request | Reused | -50 to -100ms |
| Connection Setup | 3-way handshake | Keep-alive | -30 to -50ms |
| TLS Handshake | Every request (HTTPS) | Reused | -50 to -200ms |
| Total Latency Reduction | - | - | **-130 to -350ms per request** |

### Monitoring

Monitor connection pool usage in logs:
```
✅ HTTP client initialized with connection pool (keepalive: 20, max: 100, timeout: 30s)
```

## Usage Guidelines

### ✅ DO

- Use `get_http_client()` for all external HTTP calls
- Use `await` for all HTTP requests (async)
- Let the singleton manage connection lifecycle

### ❌ DON'T

- Create new `httpx.AsyncClient` instances
- Use context managers (`async with`) for client
- Close the client manually (handled by app shutdown)

### Example: New Service Using HTTP Client

```python
from utils.http_client import get_http_client

class MyService:
    async def call_api(self):
        client = get_http_client()
        response = await client.get("https://api.example.com/data")
        return response.json()
```

## Troubleshooting

### Issue: "RuntimeError: Session is closed"

**Cause**: HTTP client was closed but service tried to use it

**Solution**: Ensure service is not called after app shutdown

### Issue: Connection pool exhausted

**Symptoms**:
```
httpx.PoolTimeout: No available connection
```

**Solution**:
1. Increase `max_connections` limit
2. Review if connections are being held too long
3. Check for connection leaks

### Issue: Tests failing with httpx mocks

**Cause**: Tests mocking wrong import path

**Solution**: Mock `get_http_client` instead of `httpx.AsyncClient`

```python
# ❌ Wrong
@patch("services.my_service.httpx.AsyncClient")

# ✅ Correct
@patch("services.my_service.get_http_client")
```

## Future Enhancements

1. **Connection pool metrics**: Track pool usage, wait times
2. **Per-service clients**: Separate pools for different APIs
3. **Retry logic**: Automatic retry with exponential backoff
4. **Circuit breaker**: Prevent cascade failures
5. **TapPay migration**: Migrate to async when payment flow refactored

## References

- GitHub Issue: #91
- httpx documentation: https://www.python-httpx.org/advanced/
- OpenAI Python SDK: https://github.com/openai/openai-python
- FastAPI lifecycle events: https://fastapi.tiangolo.com/advanced/events/

## Changelog

### 2026-01-11 - Initial Implementation
- Created global HTTP client singleton
- Migrated translation.py to AsyncOpenAI
- Migrated billing_analysis_service.py
- Migrated azure_speech_token.py
- Added lifecycle management
- Added comprehensive tests
- Registered azure_speech_token router in main.py
