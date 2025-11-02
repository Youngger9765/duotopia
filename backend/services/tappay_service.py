"""
TapPay Payment Service
處理 TapPay 金流串接
"""

import os
import requests
import logging
import hmac
import hashlib
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class TapPayService:
    """TapPay 金流服務"""

    def __init__(self):
        self.partner_key = os.getenv(
            "TAPPAY_PARTNER_KEY",
            "***REMOVED_PARTNER_KEY***",
        )
        self.merchant_id = os.getenv("TAPPAY_MERCHANT_ID", "GlobalTesting_CTBC")

        # 根據環境選擇 API URL
        self.environment = os.getenv("TAPPAY_ENV", "sandbox")
        if self.environment == "production":
            self.pay_by_prime_url = (
                "https://prod.tappaysdk.com/tpc/payment/pay-by-prime"
            )
            self.pay_by_token_url = (
                "https://prod.tappaysdk.com/tpc/payment/pay-by-token"
            )
        else:
            self.pay_by_prime_url = (
                "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
            )
            self.pay_by_token_url = (
                "https://sandbox.tappaysdk.com/tpc/payment/pay-by-token"
            )

        # 保持向後相容
        self.api_url = self.pay_by_prime_url

        logger.info(f"TapPay Service initialized in {self.environment} mode")

    def process_payment(
        self,
        prime: str,
        amount: int,
        details: Dict,
        cardholder: Dict,
        order_number: str = None,
        remember: bool = False,
    ) -> Dict:
        """
        處理信用卡付款

        Args:
            prime: TapPay prime token (from frontend)
            amount: 金額 (TWD)
            details: 商品詳情
            cardholder: 持卡人資訊
            order_number: 訂單編號
            remember: 是否記住卡片 (for recurring)

        Returns:
            TapPay API response
        """

        if not order_number:
            order_number = f"DUO_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        payload = {
            "partner_key": self.partner_key,
            "prime": prime,
            "amount": amount,
            "currency": "TWD",
            "details": details.get("item_name", "Duotopia Subscription"),
            "order_number": order_number,
            "cardholder": {
                "phone_number": cardholder.get("phone", "+886912345678"),
                "name": cardholder.get("name", ""),
                "email": cardholder.get("email", ""),
                "zip_code": cardholder.get("zip_code", ""),
                "address": cardholder.get("address", ""),
                "national_id": cardholder.get("national_id", ""),
            },
            "merchant_id": self.merchant_id,
            "remember": remember,  # 是否儲存卡片資訊供後續使用
        }

        # 3D Secure 設定 (選擇性)
        if os.getenv("TAPPAY_USE_3DS", "false").lower() == "true":
            payload["three_domain_secure"] = True
            payload["result_url"] = {
                "frontend_redirect_url": f"{os.getenv('FRONTEND_URL')}/payment/result",
                "backend_notify_url": f"{os.getenv('BACKEND_URL')}/api/payment/webhook",
            }

        try:
            print("🔥 TapPay Service Config:")
            print(f"  - Environment: {self.environment}")
            print(f"  - API URL: {self.api_url}")
            print(f"  - Merchant ID: {self.merchant_id}")
            print(f"  - Partner Key: {self.partner_key[:20]}...")
            print(f"  - Order: {order_number}")

            logger.info(f"Processing payment for order: {order_number}")

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.partner_key,
            }

            print(f"🔥 Sending to TapPay: {self.api_url}")
            print(f"  - Amount: {payload['amount']}")
            print(f"  - Merchant: {payload['merchant_id']}")

            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=30
            )

            response.raise_for_status()
            result = response.json()

            print(
                f"🔥 TapPay Response: status={result.get('status')}, msg={result.get('msg')}"
            )

            # Log response for debugging (注意不要記錄敏感資料)
            logger.info(
                f"TapPay response status: {result.get('status')}, rec_trade_id: {result.get('rec_trade_id')}"
            )

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"TapPay API error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "API_REQUEST_FAILED"}
        except Exception as e:
            logger.error(f"Unexpected error in TapPay service: {str(e)}")
            return {
                "status": -1,
                "msg": "Payment processing failed",
                "error": "INTERNAL_ERROR",
            }

    def pay_by_token(
        self,
        card_key: str,
        card_token: str,
        amount: int,
        details: str,
        cardholder: Dict,
        order_number: str = None,
    ) -> Dict:
        """
        使用儲存的 Card Token 進行扣款（自動續訂）

        Args:
            card_key: TapPay Card Key（永久有效）
            card_token: TapPay Card Token（90天有效）
            amount: 金額 (TWD)
            details: 商品詳情
            cardholder: 持卡人資訊
            order_number: 訂單編號

        Returns:
            TapPay API response（包含更新的 card_token）
        """

        if not order_number:
            order_number = f"AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        payload = {
            "partner_key": self.partner_key,
            "merchant_id": self.merchant_id,
            "card_key": card_key,
            "card_token": card_token,
            "amount": amount,
            "currency": "TWD",
            "details": details
            if isinstance(details, str)
            else details.get("item_name", "Duotopia Auto-Renewal"),
            "order_number": order_number,
            "cardholder": {
                "phone_number": cardholder.get("phone", "+886912345678"),
                "name": cardholder.get("name", ""),
                "email": cardholder.get("email", ""),
                "zip_code": cardholder.get("zip_code", ""),
                "address": cardholder.get("address", ""),
                "national_id": cardholder.get("national_id", ""),
            },
        }

        try:
            logger.info(f"Processing auto-renewal payment for order: {order_number}")
            logger.info(f"  - Card Key: {card_key[:10]}...")
            logger.info(f"  - Amount: TWD {amount}")

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.partner_key,
            }

            response = requests.post(
                self.pay_by_token_url, json=payload, headers=headers, timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info(
                f"TapPay pay-by-token response: status={result.get('status')}, "
                f"rec_trade_id={result.get('rec_trade_id')}"
            )

            # ⚠️ 重要：成功交易會返回新的 card_token，需要更新
            if result.get("status") == 0 and result.get("card_secret"):
                logger.info("New card_token received, caller should update DB")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"TapPay pay-by-token API error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "API_REQUEST_FAILED"}
        except Exception as e:
            logger.error(f"Unexpected error in pay-by-token: {str(e)}")
            return {
                "status": -1,
                "msg": "Auto-renewal payment processing failed",
                "error": "INTERNAL_ERROR",
            }

    def query_transaction(self, rec_trade_id: str) -> Dict:
        """
        查詢交易狀態

        Args:
            rec_trade_id: TapPay 交易編號

        Returns:
            Transaction details
        """
        query_url = f"{self.api_url.replace('pay-by-prime', 'transaction/query')}"

        payload = {"partner_key": self.partner_key, "rec_trade_id": rec_trade_id}

        try:
            response = requests.post(
                query_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Query transaction error: {str(e)}")
            return {"status": -1, "msg": str(e)}

    def refund(self, rec_trade_id: str, amount: int = None) -> Dict:
        """
        處理退款

        Args:
            rec_trade_id: 原始交易編號
            amount: 退款金額 (None = 全額退款)

        Returns:
            Refund result
        """
        refund_url = f"{self.api_url.replace('pay-by-prime', 'transaction/refund')}"

        payload = {"partner_key": self.partner_key, "rec_trade_id": rec_trade_id}

        if amount is not None:
            payload["amount"] = amount  # 部分退款

        try:
            response = requests.post(
                refund_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            logger.info(
                f"Refund processed for {rec_trade_id}: status={result.get('status')}"
            )
            return result

        except Exception as e:
            logger.error(f"Refund error: {str(e)}")
            return {"status": -1, "msg": str(e)}

    def capture(self, rec_trade_id: str, amount: int = None) -> Dict:
        """
        請款 (for auth only transactions)

        Args:
            rec_trade_id: 授權交易編號
            amount: 請款金額

        Returns:
            Capture result
        """
        capture_url = f"{self.api_url.replace('pay-by-prime', 'transaction/capture')}"

        payload = {"partner_key": self.partner_key, "rec_trade_id": rec_trade_id}

        if amount is not None:
            payload["amount"] = amount

        try:
            response = requests.post(
                capture_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Capture error: {str(e)}")
            return {"status": -1, "msg": str(e)}

    def validate_webhook(self, request_body: bytes, signature: str) -> bool:
        """
        驗證 TapPay Webhook 簽名

        Args:
            request_body: 原始請求內容（bytes）
            signature: X-Tappay-Signature header

        Returns:
            是否為合法請求
        """
        if not signature:
            logger.warning("Missing webhook signature")
            return False

        if not self.partner_key:
            logger.error("TAPPAY_PARTNER_KEY not configured")
            return False

        try:
            # 🔐 使用 HMAC-SHA256 計算預期簽名
            # TapPay webhook 簽名算法：HMAC-SHA256(partner_key, request_body)
            expected_signature = hmac.new(
                key=self.partner_key.encode("utf-8"),
                msg=request_body
                if isinstance(request_body, bytes)
                else request_body.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()

            # 🔐 使用 constant-time 比較防止 timing attack
            is_valid = hmac.compare_digest(expected_signature, signature)

            if not is_valid:
                logger.warning(
                    f"Invalid webhook signature. Expected: {expected_signature[:8]}..., "
                    f"Got: {signature[:8]}..."
                )

            return is_valid

        except Exception as e:
            logger.error(f"Webhook signature validation error: {str(e)}")
            return False

    @staticmethod
    def parse_error_code(status: int, msg: str) -> str:
        """
        解析 TapPay 錯誤碼為使用者友善訊息

        Args:
            status: TapPay status code
            msg: TapPay error message

        Returns:
            User-friendly error message
        """
        error_messages = {
            1: "信用卡號錯誤",
            2: "交易失敗",
            3: "信用卡已過期",
            4: "餘額不足",
            5: "CVV 錯誤",
            6: "3D 驗證失敗",
            10041: "信用卡號錯誤",
            10042: "信用卡過期",
            10043: "CVV 錯誤",
            10044: "卡片額度不足",
        }

        return error_messages.get(status, f"付款失敗：{msg}")
