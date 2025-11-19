"""
Shared rate limiter instance

Rate Limit Strategy:
- 按 Email/Student ID 限制 (每個帳號獨立計算)
- 同 IP 的不同用戶不會互相影響
- Fallback 到 IP (無法識別用戶時)
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_user_identifier(request: Request) -> str:
    """
    聰明的識別策略：
    1. 優先使用 email（從 request body）
    2. 其次使用 student id
    3. Fallback 到 IP address

    這樣每個用戶帳號有自己的限制，不會被同 IP 的其他人影響
    """
    try:
        # 嘗試從 request body 取得識別資訊
        if hasattr(request, "_json"):
            # FastAPI 已經 parse 過的 JSON
            body = request._json
        elif hasattr(request, "_body"):
            # 需要手動 parse
            import json

            body = json.loads(request._body.decode())
        else:
            # 無法取得 body，使用 IP
            return get_remote_address(request)

        # 如果有 email，使用 email 作為 key
        if isinstance(body, dict) and "email" in body:
            return f"email:{body['email']}"

        # 如果有 id（student login），使用 student_id
        if isinstance(body, dict) and "id" in body:
            return f"student:{body['id']}"

    except Exception:
        # 任何錯誤都 fallback 到 IP
        pass

    # Fallback: 使用 IP
    return f"ip:{get_remote_address(request)}"


# 🔐 Create limiter with smart identifier
limiter = Limiter(key_func=get_user_identifier)
