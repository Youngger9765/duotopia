"""Unit tests for Demo Token Daily Quota Manager"""

import os
import threading
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

import pytest

from core.demo_quota import (
    DemoQuotaManager,
    validate_referer,
    reset_demo_quota,
    get_demo_quota_manager,
    DEMO_TOKEN_DAILY_LIMIT,
    REDIS_KEY_TTL_DAYS,
)


# ============================================================================
# DemoQuotaManager - Memory Mode
# ============================================================================


class TestDemoQuotaManagerMemory:
    """Tests for in-memory quota tracking"""

    def setup_method(self):
        self.manager = DemoQuotaManager(redis_client=None)

    def test_first_request_allowed(self):
        """First request from an IP should be allowed"""
        allowed, info = self.manager.check_and_increment("1.2.3.4")
        assert allowed is True
        assert info["remaining"] == DEMO_TOKEN_DAILY_LIMIT - 1
        assert info["limit"] == DEMO_TOKEN_DAILY_LIMIT
        assert "reset_at" in info

    def test_quota_decrement(self):
        """Each request should decrement remaining quota"""
        self.manager.check_and_increment("1.2.3.4")
        _, info = self.manager.check_and_increment("1.2.3.4")
        assert info["remaining"] == DEMO_TOKEN_DAILY_LIMIT - 2

    def test_quota_exceeded(self):
        """Should reject after limit is reached"""
        ip = "1.2.3.4"
        for _ in range(DEMO_TOKEN_DAILY_LIMIT):
            self.manager.check_and_increment(ip)

        allowed, info = self.manager.check_and_increment(ip)
        assert allowed is False
        assert info["remaining"] == 0

    def test_different_ips_independent(self):
        """Different IPs should have independent quotas"""
        self.manager.check_and_increment("1.1.1.1")
        _, info = self.manager.check_and_increment("2.2.2.2")
        assert info["remaining"] == DEMO_TOKEN_DAILY_LIMIT - 1

    def test_daily_reset(self):
        """Quota should reset on a new day"""
        ip = "1.2.3.4"
        # Use up all quota
        for _ in range(DEMO_TOKEN_DAILY_LIMIT):
            self.manager.check_and_increment(ip)

        # Simulate a new day by changing the entry date
        with self.manager._lock:
            self.manager._memory_store[ip]["date"] = "2020-01-01"

        allowed, info = self.manager.check_and_increment(ip)
        assert allowed is True
        assert info["remaining"] == DEMO_TOKEN_DAILY_LIMIT - 1

    def test_get_remaining_new_ip(self):
        """get_remaining should return full limit for unknown IPs"""
        remaining = self.manager.get_remaining("new-ip")
        assert remaining == DEMO_TOKEN_DAILY_LIMIT

    def test_get_remaining_after_usage(self):
        """get_remaining should reflect current usage"""
        self.manager.check_and_increment("1.2.3.4")
        self.manager.check_and_increment("1.2.3.4")
        remaining = self.manager.get_remaining("1.2.3.4")
        assert remaining == DEMO_TOKEN_DAILY_LIMIT - 2

    def test_cleanup_old_entries(self):
        """Old entries from previous days should be cleaned up"""
        today = self.manager._get_today_key()

        # Add entries for "yesterday"
        with self.manager._lock:
            for i in range(150):
                self.manager._memory_store[f"ip-{i}"] = {
                    "count": 1,
                    "date": "2020-01-01",
                }

        # Trigger cleanup via a new check
        self.manager.check_and_increment("new-ip")

        # Old entries should be cleaned
        with self.manager._lock:
            remaining_old = sum(
                1
                for v in self.manager._memory_store.values()
                if v["date"] == "2020-01-01"
            )
        assert remaining_old == 0

    def test_thread_safety(self):
        """Concurrent access should not cause race conditions"""
        ip = "shared-ip"
        results = []

        def make_request():
            allowed, info = self.manager.check_and_increment(ip)
            results.append((allowed, info["remaining"]))

        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed, remainders should be unique and decreasing
        assert len(results) == 10
        assert all(allowed for allowed, _ in results)
        remainders = sorted([r for _, r in results], reverse=True)
        expected = list(range(DEMO_TOKEN_DAILY_LIMIT - 1, DEMO_TOKEN_DAILY_LIMIT - 11, -1))
        assert remainders == expected

    def test_no_defaultdict_auto_create(self):
        """Memory store should not auto-create entries (no defaultdict)"""
        # Accessing non-existent key should NOT create an entry
        assert "nonexistent" not in self.manager._memory_store
        # get_remaining reads but should not auto-create
        self.manager.get_remaining("nonexistent")
        assert "nonexistent" not in self.manager._memory_store


# ============================================================================
# DemoQuotaManager - Redis Mode
# ============================================================================


class TestDemoQuotaManagerRedis:
    """Tests for Redis-backed quota tracking"""

    def setup_method(self):
        self.redis_mock = MagicMock()
        self.redis_mock.ping.return_value = True
        self.manager = DemoQuotaManager(redis_client=self.redis_mock)

    def test_first_request_via_redis(self):
        """First Redis request should be allowed (atomic INCR)"""
        pipe_mock = MagicMock()
        pipe_mock.execute.return_value = [1, True]  # INCR returns 1, EXPIRE returns True
        self.redis_mock.pipeline.return_value = pipe_mock

        allowed, info = self.manager.check_and_increment("1.2.3.4")
        assert allowed is True
        assert info["remaining"] == DEMO_TOKEN_DAILY_LIMIT - 1
        pipe_mock.incr.assert_called_once()
        pipe_mock.expire.assert_called_once()

    def test_redis_quota_exceeded(self):
        """Should reject when atomic INCR exceeds limit"""
        pipe_mock = MagicMock()
        # INCR returns limit+1 (just exceeded)
        pipe_mock.execute.return_value = [DEMO_TOKEN_DAILY_LIMIT + 1, True]
        self.redis_mock.pipeline.return_value = pipe_mock

        allowed, info = self.manager.check_and_increment("1.2.3.4")
        assert allowed is False
        assert info["remaining"] == 0

    def test_redis_at_exact_limit_still_allowed(self):
        """Request at exactly the limit should still be allowed"""
        pipe_mock = MagicMock()
        pipe_mock.execute.return_value = [DEMO_TOKEN_DAILY_LIMIT, True]
        self.redis_mock.pipeline.return_value = pipe_mock

        allowed, info = self.manager.check_and_increment("1.2.3.4")
        assert allowed is True
        assert info["remaining"] == 0

    def test_redis_fallback_on_error(self):
        """Should fall back to memory on Redis error"""
        self.redis_mock.pipeline.side_effect = Exception("Redis down")

        allowed, info = self.manager.check_and_increment("1.2.3.4")
        # Should still succeed via memory fallback
        assert allowed is True

    def test_redis_ttl_uses_constant(self):
        """Redis key TTL should use REDIS_KEY_TTL_DAYS constant"""
        pipe_mock = MagicMock()
        pipe_mock.execute.return_value = [1, True]
        self.redis_mock.pipeline.return_value = pipe_mock

        self.manager.check_and_increment("1.2.3.4")
        pipe_mock.expire.assert_called_once()
        ttl_arg = pipe_mock.expire.call_args[0][1]
        assert ttl_arg == 86400 * REDIS_KEY_TTL_DAYS

    def test_redis_key_safe_with_ipv6(self):
        """Redis key should not collide with IPv6 colons"""
        pipe_mock = MagicMock()
        pipe_mock.execute.return_value = [1, True]
        self.redis_mock.pipeline.return_value = pipe_mock

        self.manager.check_and_increment("2001:db8::1")
        # Verify the key uses | delimiter, not : which would clash with IPv6
        incr_key = pipe_mock.incr.call_args[0][0]
        assert "2001:db8::1" in incr_key
        # Key format: prefix|ip|date — prefix ends with |, not :
        assert incr_key.startswith("demo:token:daily|")

    def test_redis_unavailable_at_init(self):
        """Should gracefully fall back if Redis unreachable at init"""
        bad_redis = MagicMock()
        bad_redis.ping.side_effect = Exception("Connection refused")
        manager = DemoQuotaManager(redis_client=bad_redis)
        assert manager.redis_client is None

    def test_get_remaining_redis(self):
        """get_remaining should query Redis"""
        self.redis_mock.get.return_value = "5"
        remaining = self.manager.get_remaining("1.2.3.4")
        assert remaining == DEMO_TOKEN_DAILY_LIMIT - 5


# ============================================================================
# validate_referer
# ============================================================================


class TestValidateReferer:
    """Tests for referer validation"""

    @patch.dict(os.environ, {"ENVIRONMENT": "development"})
    def test_missing_referer_allowed_in_dev(self):
        """Missing referer should be allowed in development"""
        assert validate_referer(None) is True
        assert validate_referer("") is True

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_missing_referer_rejected_in_production(self):
        """Missing referer should be rejected in production"""
        assert validate_referer(None) is False

    @patch.dict(os.environ, {
        "DEMO_ALLOWED_ORIGINS": "https://duotopia.co,https://staging.duotopia.co"
    })
    def test_valid_referer(self):
        """Known origins should be accepted"""
        # Need to reload the module to pick up the env var, but since
        # DEMO_ALLOWED_ORIGINS is evaluated at import time, we test with
        # the current value which includes localhost in dev
        assert validate_referer("http://localhost:3000/some/page") is True

    def test_invalid_referer(self):
        """Unknown origins should be rejected"""
        assert validate_referer("https://evil-site.com/steal") is False
        assert validate_referer("https://notduotopia.co/page") is False

    def test_subdomain_bypass_blocked(self):
        """Subdomain spoofing like localhost.evil.com should be rejected"""
        assert validate_referer("http://localhost:3000.evil.com/page") is False
        assert validate_referer("http://localhost:5173.attacker.io") is False

    def test_valid_referer_with_path(self):
        """Referer with path should still match origin"""
        assert validate_referer("http://localhost:5173/demo/76") is True


# ============================================================================
# reset_demo_quota
# ============================================================================


class TestResetDemoQuota:
    """Tests for quota reset functionality"""

    def test_reset_specific_ip(self):
        """Should reset quota for a specific IP"""
        import core.demo_quota as mod

        # Create a fresh manager
        manager = DemoQuotaManager(redis_client=None)
        manager.check_and_increment("1.2.3.4")
        mod._quota_manager = manager

        count = reset_demo_quota("1.2.3.4")
        assert count == 1
        assert manager.get_remaining("1.2.3.4") == DEMO_TOKEN_DAILY_LIMIT

        # Cleanup
        mod._quota_manager = None

    def test_reset_nonexistent_ip(self):
        """Should return 0 when resetting unknown IP"""
        import core.demo_quota as mod

        manager = DemoQuotaManager(redis_client=None)
        mod._quota_manager = manager

        count = reset_demo_quota("unknown-ip")
        assert count == 0

        mod._quota_manager = None

    def test_reset_all(self):
        """Should reset all quotas"""
        import core.demo_quota as mod

        manager = DemoQuotaManager(redis_client=None)
        manager.check_and_increment("1.1.1.1")
        manager.check_and_increment("2.2.2.2")
        mod._quota_manager = manager

        count = reset_demo_quota(None)
        assert count == 2

        mod._quota_manager = None


# ============================================================================
# get_demo_quota_manager
# ============================================================================


class TestGetDemoQuotaManager:
    """Tests for singleton factory"""

    def test_singleton(self):
        """Should return the same instance"""
        import core.demo_quota as mod

        mod._quota_manager = None

        m1 = get_demo_quota_manager()
        m2 = get_demo_quota_manager()
        assert m1 is m2

        mod._quota_manager = None

    @patch.dict(os.environ, {"REDIS_URL": ""})
    def test_no_redis_when_url_empty(self):
        """Should not attempt Redis when URL is empty"""
        import core.demo_quota as mod

        mod._quota_manager = None
        manager = get_demo_quota_manager()
        assert manager.redis_client is None

        mod._quota_manager = None
