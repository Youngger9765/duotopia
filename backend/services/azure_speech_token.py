"""
Azure Speech Token Service

提供短效 Azure Speech Token 給前端直接調用
- Token 有效期 10 分鐘
- Server-side cache 避免重複調用 issueToken endpoint
- 安全性：Subscription Key 不外泄
"""

import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class AzureSpeechTokenService:
    """Azure Speech Token 服務"""

    def __init__(self):
        self.subscription_key = os.getenv("AZURE_SPEECH_KEY")
        self.region = os.getenv("AZURE_SPEECH_REGION", "eastasia")
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        if not self.subscription_key:
            logger.error("AZURE_SPEECH_KEY not configured")
            raise ValueError("AZURE_SPEECH_KEY environment variable is required")

    async def get_token(self) -> Dict[str, any]:
        """
        獲取短效 Azure Speech Token（10分鐘有效）

        Returns:
            {
                "token": "<authorization-token>",
                "region": "eastasia",
                "expires_in": 600
            }

        實施策略：
        - Server-side cache（8分鐘內重用同一 token）
        - 提前2分鐘過期，避免前端使用到期 token
        """
        # Check cache (8分鐘內重用，提前2分鐘過期)
        if self._cached_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=2):
                expires_in_seconds = (
                    self._token_expires_at - datetime.now()
                ).total_seconds()
                logger.info(
                    f"Returning cached token (expires in {expires_in_seconds:.0f}s)"
                )
                return {
                    "token": self._cached_token,
                    "region": self.region,
                    "expires_in": 600,
                }

        # Call Azure issueToken endpoint
        url = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}

        logger.info(f"Requesting new token from Azure (region: {self.region})")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers)
                response.raise_for_status()
                token = response.text

            # Cache token
            self._cached_token = token
            self._token_expires_at = datetime.now() + timedelta(minutes=10)

            logger.info("New token issued and cached successfully")

            return {"token": token, "region": self.region, "expires_in": 600}

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Azure token request failed: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error requesting Azure token: {e}")
            raise


# Singleton instance
_token_service = None


def get_azure_speech_token_service() -> AzureSpeechTokenService:
    """
    獲取 AzureSpeechTokenService 單例實例

    使用單例確保 token cache 在整個應用程式生命週期內共享
    """
    global _token_service
    if _token_service is None:
        _token_service = AzureSpeechTokenService()
    return _token_service
