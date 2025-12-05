"""
全局 Rate Limiting Middleware
补充 slowapi 的限制，防止异常高频请求

策略：
1. 登录 API: 已由 slowapi 保护（3次/分钟）
2. 其他 API: 全局限制（500次/分钟，保守配置）
3. 观察 1 周后调整为 200次/分钟

为什么需要这个：
- 2025-12-03 发生异常：1分钟内17次相同请求 → OOM
- slowapi 只保护登录，其他 API 无限制
- 需要全局兜底保护

设计：
- 非常宽松的限制（500/分钟）
- 正常用户不会触发（5分钟最多50-100个请求）
- 只阻止极端异常（如12/3那种）
"""

from fastapi import Request
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class GlobalRateLimiter:
    """全局速率限制器（内存版）"""

    def __init__(self):
        # {client_ip: [(timestamp, path), ...]}
        self.requests = defaultdict(list)
        self.cleanup_task = None

    def get_client_ip(self, request: Request) -> str:
        """获取客户端 IP（处理代理）"""
        # 优先使用 X-Forwarded-For（Cloud Run 会设置）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 取第一个 IP（客户端真实 IP）
            return forwarded.split(",")[0].strip()

        # Fallback: 直接连接 IP
        if request.client:
            return request.client.host

        return "unknown"

    async def check_rate_limit(
        self, request: Request, max_requests: int = 500, window_seconds: int = 60
    ) -> tuple[bool, dict]:
        """
        检查是否超限

        Args:
            request: FastAPI request
            max_requests: 时间窗口内最大请求数（默认500，很宽松）
            window_seconds: 时间窗口秒数（默认60秒）

        Returns:
            (是否允许, 限制信息)
        """
        client_ip = self.get_client_ip(request)
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)

        # 清理该 IP 的过期记录
        self.requests[client_ip] = [
            (ts, path) for ts, path in self.requests[client_ip] if ts > window_start
        ]

        # 计数
        current_count = len(self.requests[client_ip])

        # 检查是否超限
        if current_count >= max_requests:
            # 记录被限制的请求（用于分析）
            logger.warning(
                f"⚠️ Rate limit exceeded: "
                f"IP={client_ip}, "
                f"Path={request.url.path}, "
                f"Count={current_count}/{max_requests} in {window_seconds}s"
            )

            return False, {
                "error": "Too many requests",
                "message": f"您的请求过于频繁，请{window_seconds}秒后再试",
                "limit": max_requests,
                "window_seconds": window_seconds,
                "retry_after": window_seconds,
            }

        # 记录本次请求
        self.requests[client_ip].append((now, str(request.url.path)))

        return True, {
            "limit": max_requests,
            "remaining": max_requests - current_count - 1,
            "window_seconds": window_seconds,
        }

    async def cleanup_old_records(self):
        """
        定期清理所有过期记录（防止内存泄漏）
        每5分钟清理一次，删除2分钟前的记录
        """
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟
                now = datetime.now()
                cutoff = now - timedelta(seconds=120)  # 2分钟前

                cleaned_ips = 0
                for ip in list(self.requests.keys()):
                    # 清理过期记录
                    self.requests[ip] = [
                        (ts, path) for ts, path in self.requests[ip] if ts > cutoff
                    ]

                    # 如果该 IP 没有记录了，删除 key
                    if not self.requests[ip]:
                        del self.requests[ip]
                        cleaned_ips += 1

                if cleaned_ips > 0:
                    logger.info(f"🧹 Cleaned {cleaned_ips} expired IP records")

            except Exception as e:
                logger.error(f"❌ Cleanup task error: {e}")

    def start_cleanup_task(self):
        """启动清理任务"""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self.cleanup_old_records())
            logger.info("✅ Rate limiter cleanup task started")


# 创建全局实例
global_rate_limiter = GlobalRateLimiter()
