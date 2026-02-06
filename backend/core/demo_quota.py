"""
Demo Token Daily Quota Manager

Tracks daily usage quota for demo Azure Speech Token.
Supports Redis (if available) or falls back to in-memory storage.

Features:
- 60 tokens per IP per day
- Automatic daily reset (UTC+8 midnight)
- Graceful fallback to memory if Redis unavailable
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

# Configuration
DEMO_TOKEN_DAILY_LIMIT = int(os.getenv("DEMO_TOKEN_DAILY_LIMIT", "60"))
DEMO_ALLOWED_ORIGINS = [
    "https://duotopia.co",
    "https://www.duotopia.co",
    "https://duotopia.net",
    "https://www.duotopia.net",
    "https://staging.duotopia.co",
    "https://develop.duotopia.co",
    # Cloud Run URLs
    "https://duotopia-production-frontend-b2ovkkgl6a-de.a.run.app",
    "https://duotopia-production-frontend-316409492201.asia-east1.run.app",
    "https://duotopia-staging-frontend-316409492201.asia-east1.run.app",
    "https://duotopia-develop-frontend-316409492201.asia-east1.run.app",
    # Local development
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


class DemoQuotaManager:
    """
    Manages daily quota for demo token requests.

    Uses Redis if available, otherwise falls back to in-memory storage.
    In-memory storage is cleaned up periodically to prevent memory leaks.
    """

    REDIS_KEY_PREFIX = "demo:token:daily:"

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        # In-memory storage: {ip: {"count": int, "date": str}}
        self._memory_store: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "date": ""})
        self._lock = threading.Lock()

        if redis_client:
            try:
                redis_client.ping()
                logger.info("✅ Redis connected for demo quota tracking")
            except Exception as e:
                logger.warning(f"⚠️ Redis unavailable for demo quota, using memory: {e}")
                self.redis_client = None

    def _get_today_key(self) -> str:
        """Get today's date key (UTC+8)"""
        utc_now = datetime.utcnow()
        local_now = utc_now + timedelta(hours=8)
        return local_now.strftime("%Y-%m-%d")

    def _get_reset_time(self) -> str:
        """Get next reset time (UTC+8 midnight) as ISO string"""
        utc_now = datetime.utcnow()
        local_now = utc_now + timedelta(hours=8)
        tomorrow = (local_now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # Convert back to UTC for ISO format
        tomorrow_utc = tomorrow - timedelta(hours=8)
        return tomorrow_utc.isoformat() + "Z"

    def check_and_increment(self, ip: str) -> Tuple[bool, Dict]:
        """
        Check if IP is within quota and increment counter.

        Args:
            ip: Client IP address

        Returns:
            Tuple of (allowed: bool, info: dict)
            info contains: remaining, limit, reset_at
        """
        today = self._get_today_key()
        reset_at = self._get_reset_time()

        if self.redis_client:
            return self._check_redis(ip, today, reset_at)
        else:
            return self._check_memory(ip, today, reset_at)

    def _check_redis(self, ip: str, today: str, reset_at: str) -> Tuple[bool, Dict]:
        """Check quota using Redis"""
        key = f"{self.REDIS_KEY_PREFIX}{ip}:{today}"

        try:
            # Get current count
            current = self.redis_client.get(key)
            current_count = int(current) if current else 0

            if current_count >= DEMO_TOKEN_DAILY_LIMIT:
                logger.info(f"Demo quota exceeded: IP={ip}, count={current_count}")
                return False, {
                    "remaining": 0,
                    "limit": DEMO_TOKEN_DAILY_LIMIT,
                    "reset_at": reset_at,
                }

            # Increment and set expiry
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 86400 * 2)  # 2 days TTL for safety
            pipe.execute()

            new_count = current_count + 1
            remaining = DEMO_TOKEN_DAILY_LIMIT - new_count

            logger.info(f"Demo token used: IP={ip}, count={new_count}/{DEMO_TOKEN_DAILY_LIMIT}")

            return True, {
                "remaining": remaining,
                "limit": DEMO_TOKEN_DAILY_LIMIT,
                "reset_at": reset_at,
            }

        except Exception as e:
            logger.error(f"Redis error in demo quota: {e}")
            # Fallback to memory on Redis error
            return self._check_memory(ip, today, reset_at)

    def _check_memory(self, ip: str, today: str, reset_at: str) -> Tuple[bool, Dict]:
        """Check quota using in-memory storage"""
        with self._lock:
            # Clean old entries periodically (every 100 checks)
            if len(self._memory_store) > 100:
                self._cleanup_old_entries(today)

            entry = self._memory_store[ip]

            # Reset if new day
            if entry["date"] != today:
                entry["count"] = 0
                entry["date"] = today

            if entry["count"] >= DEMO_TOKEN_DAILY_LIMIT:
                logger.info(f"Demo quota exceeded (memory): IP={ip}, count={entry['count']}")
                return False, {
                    "remaining": 0,
                    "limit": DEMO_TOKEN_DAILY_LIMIT,
                    "reset_at": reset_at,
                }

            # Increment
            entry["count"] += 1
            remaining = DEMO_TOKEN_DAILY_LIMIT - entry["count"]

            logger.info(
                f"Demo token used (memory): IP={ip}, count={entry['count']}/{DEMO_TOKEN_DAILY_LIMIT}"
            )

            return True, {
                "remaining": remaining,
                "limit": DEMO_TOKEN_DAILY_LIMIT,
                "reset_at": reset_at,
            }

    def _cleanup_old_entries(self, today: str):
        """Remove entries from previous days"""
        old_keys = [k for k, v in self._memory_store.items() if v["date"] != today]
        for key in old_keys:
            del self._memory_store[key]
        if old_keys:
            logger.info(f"Cleaned up {len(old_keys)} old demo quota entries")

    def get_remaining(self, ip: str) -> int:
        """Get remaining quota for an IP (read-only)"""
        today = self._get_today_key()

        if self.redis_client:
            try:
                key = f"{self.REDIS_KEY_PREFIX}{ip}:{today}"
                current = self.redis_client.get(key)
                current_count = int(current) if current else 0
                return max(0, DEMO_TOKEN_DAILY_LIMIT - current_count)
            except Exception:
                pass

        # Memory fallback
        with self._lock:
            entry = self._memory_store.get(ip, {"count": 0, "date": ""})
            if entry["date"] != today:
                return DEMO_TOKEN_DAILY_LIMIT
            return max(0, DEMO_TOKEN_DAILY_LIMIT - entry["count"])


# Singleton instance
_quota_manager: Optional[DemoQuotaManager] = None


def get_demo_quota_manager() -> DemoQuotaManager:
    """Get singleton demo quota manager instance"""
    global _quota_manager
    if _quota_manager is None:
        # Try to connect to Redis if URL is configured
        redis_client = None
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")

        _quota_manager = DemoQuotaManager(redis_client)

    return _quota_manager


def reset_demo_quota(ip: Optional[str] = None) -> int:
    """
    Reset demo quota for testing purposes.

    Args:
        ip: Specific IP to reset. If None, resets all quotas.

    Returns:
        Number of entries reset
    """
    manager = get_demo_quota_manager()

    if manager.redis_client:
        # Redis mode
        try:
            if ip:
                today = manager._get_today_key()
                key = f"{manager.REDIS_KEY_PREFIX}{ip}:{today}"
                deleted = manager.redis_client.delete(key)
                logger.info(f"Reset demo quota for IP {ip}: {deleted} keys deleted")
                return deleted
            else:
                # Delete all demo quota keys
                pattern = f"{manager.REDIS_KEY_PREFIX}*"
                keys = manager.redis_client.keys(pattern)
                if keys:
                    deleted = manager.redis_client.delete(*keys)
                    logger.info(f"Reset all demo quotas: {deleted} keys deleted")
                    return deleted
                return 0
        except Exception as e:
            logger.error(f"Failed to reset Redis quota: {e}")
            return 0
    else:
        # Memory mode
        with manager._lock:
            if ip:
                if ip in manager._memory_store:
                    del manager._memory_store[ip]
                    logger.info(f"Reset demo quota for IP {ip}")
                    return 1
                return 0
            else:
                count = len(manager._memory_store)
                manager._memory_store.clear()
                logger.info(f"Reset all demo quotas: {count} entries cleared")
                return count


def validate_referer(referer: Optional[str]) -> bool:
    """
    Validate request referer against allowed origins.

    Args:
        referer: Referer header value

    Returns:
        True if referer is valid, False otherwise
    """
    if not referer:
        # Allow requests without referer (some browsers/privacy settings)
        # But log for monitoring
        logger.debug("Demo token request without referer")
        return True

    for origin in DEMO_ALLOWED_ORIGINS:
        if referer.startswith(origin):
            return True

    logger.warning(f"Demo token rejected - invalid referer: {referer}")
    return False
