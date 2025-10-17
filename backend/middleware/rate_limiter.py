"""
API Rate Limiting Middleware
限制每個 IP 的請求頻率，防止濫用
"""

from collections import defaultdict
from typing import Dict, Tuple
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
import redis
import hashlib


class RateLimiter:
    """速率限制器 - 可以用記憶體或 Redis"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        # 如果沒有 Redis，使用記憶體儲存
        self.memory_store: Dict[str, list] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """取得客戶端識別碼（IP + User Agent）"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0]
        else:
            ip = request.client.host if request.client else "unknown"

        user_agent = request.headers.get("User-Agent", "")
        # 組合 IP 和 User Agent 做為識別碼
        client_id = f"{ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
        return client_id

    def _clean_old_requests(self, requests: list, window_seconds: int) -> list:
        """清理超過時間窗口的請求記錄"""
        now = time.time()
        cutoff = now - window_seconds
        return [req_time for req_time in requests if req_time > cutoff]

    async def check_rate_limit(
        self, request: Request, max_requests: int = 100, window_seconds: int = 60
    ) -> Tuple[bool, dict]:
        """
        檢查是否超過速率限制

        Args:
            request: FastAPI request object
            max_requests: 時間窗口內最大請求數
            window_seconds: 時間窗口（秒）

        Returns:
            (是否允許, 限制資訊)
        """
        client_id = self._get_client_id(request)
        now = time.time()

        if self.redis_client:
            # 使用 Redis 儲存
            key = f"rate_limit:{client_id}"
            try:
                # 使用 Redis sorted set 儲存請求時間
                # 移除過期的記錄
                self.redis_client.zremrangebyscore(key, 0, now - window_seconds)

                # 取得當前請求數
                current_requests = self.redis_client.zcard(key)

                if current_requests >= max_requests:
                    # 計算重試時間
                    oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        retry_after = int(window_seconds - (now - oldest[0][1]))
                    else:
                        retry_after = window_seconds

                    return False, {
                        "limit": max_requests,
                        "remaining": 0,
                        "reset": int(now + retry_after),
                    }

                # 記錄新請求
                self.redis_client.zadd(key, {str(now): now})
                self.redis_client.expire(key, window_seconds)

                return True, {
                    "limit": max_requests,
                    "remaining": max_requests - current_requests - 1,
                    "reset": int(now + window_seconds),
                }

            except Exception as e:
                # Redis 錯誤時降級到記憶體儲存
                print(f"Redis error: {e}, falling back to memory store")

        # 使用記憶體儲存
        requests = self.memory_store[client_id]
        requests = self._clean_old_requests(requests, window_seconds)

        if len(requests) >= max_requests:
            # 計算重試時間
            if requests:
                retry_after = int(window_seconds - (now - requests[0]))
            else:
                retry_after = window_seconds

            return False, {
                "limit": max_requests,
                "remaining": 0,
                "reset": int(now + retry_after),
            }

        # 記錄新請求
        requests.append(now)
        self.memory_store[client_id] = requests

        return True, {
            "limit": max_requests,
            "remaining": max_requests - len(requests),
            "reset": int(now + window_seconds),
        }


class RateLimitMiddleware:
    """FastAPI 中介軟體"""

    # 不同端點的速率限制設定
    ENDPOINT_LIMITS = {
        "/api/auth/": (3, 60),  # 登入：3 次/分鐘 (DDoS 防護)
        "/api/auth/teacher/login": (3, 60),
        "/api/auth/student/login": (3, 60),
        "/api/programs/": (30, 60),  # 一般 API：30 次/分鐘
        "/api/teachers/": (30, 60),
        "/api/students/": (30, 60),
        "/api/classrooms/": (30, 60),
        "/api/assignments/": (50, 60),  # 作業：50 次/分鐘
        "/api/activities/": (100, 60),  # 活動：100 次/分鐘
        "/health": (1000, 60),  # 健康檢查：1000 次/分鐘
    }

    def __init__(self, app, redis_url: str = None):
        self.app = app

        # 初始化 Redis（如果有提供 URL）
        redis_client = None
        if redis_url:
            try:
                redis_client = redis.from_url(redis_url)
                redis_client.ping()
                print("✅ Redis connected for rate limiting")
            except Exception as e:
                print(f"⚠️ Redis not available, using memory store: {e}")
                redis_client = None

        self.limiter = RateLimiter(redis_client)

    def _get_limit_for_path(self, path: str) -> Tuple[int, int]:
        """根據路徑取得速率限制設定"""
        # 精確匹配
        if path in self.ENDPOINT_LIMITS:
            return self.ENDPOINT_LIMITS[path]

        # 前綴匹配
        for endpoint, limits in self.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint):
                return limits

        # 預設限制
        return (60, 60)  # 60 請求/分鐘

    async def __call__(self, request: Request, call_next):
        """處理請求"""
        # 跳過靜態資源
        if request.url.path.startswith("/static") or request.url.path.startswith(
            "/docs"
        ):
            return await call_next(request)

        # 取得限制設定
        max_requests, window = self._get_limit_for_path(request.url.path)

        # 檢查速率限制
        allowed, info = await self.limiter.check_rate_limit(
            request, max_requests=max_requests, window_seconds=window
        )

        if not allowed:
            # 超過限制，返回 429
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": info["reset"] - int(time.time()),
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["reset"] - int(time.time())),
                },
            )

        # 繼續處理請求
        response = await call_next(request)

        # 加入速率限制 headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response
