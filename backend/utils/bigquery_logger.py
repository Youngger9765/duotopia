"""
BigQuery Logger for Transaction Data Collection
收集所有金流交易資料（成功與失敗）到 BigQuery
"""

import os
import json
import traceback
from datetime import datetime, timezone
from typing import Optional, Dict
from google.cloud import bigquery
import logging

logger = logging.getLogger(__name__)


class BigQueryTransactionLogger:
    """金流交易 BigQuery Logger"""

    def __init__(self):
        self.project_id = "duotopia-472708"
        self.dataset_id = "duotopia_analytics"
        self.table_id = "transaction_logs"
        self.environment = os.getenv("ENVIRONMENT", "local")

        try:
            # 先嘗試使用 service account key（本地測試）
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            key_path = os.path.join(backend_dir, "service-account-key.json")

            if os.path.exists(key_path):
                self.client = bigquery.Client.from_service_account_json(
                    key_path, project=self.project_id
                )
                logger.info(
                    f"BigQuery client initialized with service account from {key_path}"
                )
            else:
                # Cloud Run 會自動使用 service account
                self.client = bigquery.Client(project=self.project_id)
                logger.info("BigQuery client initialized with default credentials")

            self.table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            self.client = None

    def log_transaction(
        self,
        # 基本資訊
        transaction_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        user_type: str = "teacher",
        # 交易資訊
        amount: Optional[int] = None,
        plan_name: Optional[str] = None,
        payment_method: str = "credit_card",
        # 狀態
        status: str = "pending",  # success, failed, pending
        error_stage: Optional[
            str
        ] = None,  # authentication, prime_token, tappay_api, database, unknown
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        # TapPay 相關
        tappay_prime_token: Optional[str] = None,
        tappay_response: Optional[Dict] = None,
        tappay_rec_trade_id: Optional[str] = None,
        # 技術細節
        api_endpoint: str = "/api/payment/process",
        request_headers: Optional[Dict] = None,
        request_body: Optional[Dict] = None,
        response_status: Optional[int] = None,
        response_body: Optional[Dict] = None,
        # 前端資訊
        frontend_error: Optional[Dict] = None,
        user_agent: Optional[str] = None,
        client_ip: Optional[str] = None,
        # 診斷資訊
        execution_time_ms: Optional[int] = None,
        stack_trace: Optional[str] = None,
        additional_context: Optional[Dict] = None,
    ) -> bool:
        """
        記錄交易到 BigQuery

        Args:
            所有參數都是可選的，但建議提供盡可能多的資訊

        Returns:
            bool: 是否成功記錄
        """
        if not self.client:
            logger.warning("BigQuery client not available, skipping log")
            return False

        try:
            # 準備資料
            row = {
                "transaction_id": transaction_id,
                "timestamp": datetime.utcnow().isoformat(),
                "environment": self.environment,
                # 用戶資訊
                "user_id": user_id,
                "user_email": user_email,
                "user_type": user_type,
                # 交易資訊
                "amount": amount,
                "plan_name": plan_name,
                "payment_method": payment_method,
                # 狀態
                "status": status,
                "error_stage": error_stage,
                "error_code": error_code,
                "error_message": error_message,
                # TapPay 相關
                "tappay_prime_token": tappay_prime_token[:20] + "..."
                if tappay_prime_token
                else None,
                "tappay_response": json.dumps(
                    self._sanitize_tappay_response(tappay_response)
                )
                if tappay_response
                else None,
                "tappay_rec_trade_id": tappay_rec_trade_id,
                # 技術細節
                "api_endpoint": api_endpoint,
                "request_headers": json.dumps(self._sanitize_headers(request_headers))
                if request_headers
                else None,
                "request_body": json.dumps(self._sanitize_body(request_body))
                if request_body
                else None,
                "response_status": response_status,
                "response_body": json.dumps(self._sanitize_response_body(response_body))
                if response_body
                else None,
                # 前端資訊
                "frontend_error": json.dumps(
                    self._sanitize_frontend_error(frontend_error)
                )
                if frontend_error
                else None,
                "user_agent": user_agent,
                "client_ip": client_ip,
                # 診斷資訊
                "execution_time_ms": execution_time_ms,
                "stack_trace": stack_trace,
                "additional_context": json.dumps(additional_context)
                if additional_context
                else None,
            }

            # 寫入 BigQuery
            errors = self.client.insert_rows_json(self.table_ref, [row])

            if errors:
                logger.error(f"Failed to insert row to BigQuery: {errors}")
                return False

            logger.info(
                f"Successfully logged transaction to BigQuery: {transaction_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error logging to BigQuery: {e}")
            logger.error(traceback.format_exc())
            return False

    def _sanitize_headers(self, headers: Optional[Dict]) -> Dict:
        """移除敏感資訊（如 Authorization token）"""
        if not headers:
            return {}

        sanitized = headers.copy()

        # 移除敏感 headers
        sensitive_keys = ["authorization", "cookie", "x-api-key"]
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "[REDACTED]"
            # 也處理大小寫不同的情況
            for header_key in list(sanitized.keys()):
                if header_key.lower() in sensitive_keys:
                    sanitized[header_key] = "[REDACTED]"

        return sanitized

    def _sanitize_body(self, body: Optional[Dict]) -> Dict:
        """移除敏感資訊（如完整的信用卡號）"""
        if not body:
            return {}

        sanitized = body.copy()

        # 移除或遮蔽敏感欄位
        if "prime" in sanitized and sanitized["prime"]:
            # 只保留 prime token 的前 20 字元
            sanitized["prime"] = sanitized["prime"][:20] + "..."

        # 遮蔽信用卡持卡人資訊中的敏感欄位
        if "cardholder" in sanitized and isinstance(sanitized["cardholder"], dict):
            cardholder = sanitized["cardholder"].copy()
            # 遮蔽信用卡號（如果有）
            if "card_number" in cardholder:
                cardholder["card_number"] = "[REDACTED]"
            if "ccv" in cardholder:
                cardholder["ccv"] = "[REDACTED]"
            if "expiry_date" in cardholder:
                cardholder["expiry_date"] = "[REDACTED]"
            sanitized["cardholder"] = cardholder

        return sanitized

    def _sanitize_tappay_response(self, response: Optional[Dict]) -> Dict:
        """遮蔽 TapPay response 中的敏感資訊"""
        if not response:
            return {}

        sanitized = response.copy()

        # TapPay response 可能包含的敏感欄位
        sensitive_fields = [
            "card_secret",
            "card_token",
            "card_key",
            "bank_transaction_id",
            "acquirer",
        ]

        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"

        # 如果有 card_info，遮蔽卡號
        if "card_info" in sanitized and isinstance(sanitized["card_info"], dict):
            card_info = sanitized["card_info"].copy()
            if "bin_code" in card_info:
                card_info["bin_code"] = "[REDACTED]"
            if "last_four" in card_info:
                # 保留後四碼，這是安全的
                pass
            if "issuer" in card_info:
                # 保留發卡機構，這是安全的
                pass
            sanitized["card_info"] = card_info

        return sanitized

    def _sanitize_response_body(self, response: Optional[Dict]) -> Dict:
        """遮蔽 API response body 中的敏感資訊"""
        if not response:
            return {}

        sanitized = response.copy()

        # 移除可能的敏感欄位
        sensitive_fields = [
            "token",
            "access_token",
            "refresh_token",
            "password",
            "secret",
            "api_key",
        ]

        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"

        return sanitized

    def _sanitize_frontend_error(self, frontend_error: Optional[Dict]) -> Dict:
        """遮蔽前端錯誤資料中的敏感資訊"""
        if not frontend_error:
            return {}

        import copy

        sanitized = copy.deepcopy(frontend_error)  # M-2: 使用 deep copy

        # 移除可能的敏感欄位
        sensitive_fields = [
            "token",
            "access_token",
            "refresh_token",
            "id_token",
            "authorization",
            "bearer",
            "api_key",
            "apikey",
            "api_secret",
            "password",
            "passwd",
            "pwd",
            "secret",
            "client_secret",
            "prime",
            "card_number",
            "cardnumber",
            "credit_card",
            "ccv",
            "cvv",
            "cvc",
            "session",
            "session_id",
            "sessionid",
            "csrf",
            "csrf_token",
            "private_key",
            "privatekey",
            "jwt",
            "cookie",
        ]

        def _normalize_key(key: str) -> str:
            """正規化 key 名稱，處理特殊字元"""
            return key.lower().replace("-", "_").replace(".", "_").replace(":", "_")

        def _is_sensitive_key(key: str) -> bool:
            """檢查 key 是否為敏感欄位（支援 api.key, apiKey 等格式）"""
            normalized = _normalize_key(key)
            return any(sensitive in normalized for sensitive in sensitive_fields)

        def _looks_like_token(s: str) -> bool:
            """判斷字串是否像 token（降低門檻至 30，移除空格漏洞）"""
            if not isinstance(s, str):
                return False
            # H-4: 降低門檻至 30 字元，且空格數量必須少於 2 個
            if len(s) > 30 and s.count(" ") < 2:
                return True
            return False

        # H-1, H-3: 遞迴檢查所有欄位，加入深度限制和循環引用保護
        def sanitize_recursive(obj, depth=0, max_depth=100, seen=None):
            if seen is None:
                seen = set()

            # H-1: 深度限制
            if depth > max_depth:
                return "[REDACTED: MAX_DEPTH_EXCEEDED]"

            # H-3: 循環引用保護
            obj_id = id(obj)
            if obj_id in seen:
                return "[REDACTED: CIRCULAR_REFERENCE]"

            if isinstance(obj, (dict, list)):
                seen.add(obj_id)

            try:
                if isinstance(obj, dict):
                    result = {}
                    for key, value in obj.items():
                        # H-2: 改善 key 匹配邏輯
                        if _is_sensitive_key(key):
                            result[key] = "[REDACTED]"
                        else:
                            result[key] = sanitize_recursive(
                                value, depth + 1, max_depth, seen
                            )
                    return result
                elif isinstance(obj, list):
                    return [
                        sanitize_recursive(item, depth + 1, max_depth, seen)
                        for item in obj
                    ]
                elif isinstance(obj, str):
                    # H-4: 強化 token 偵測
                    if _looks_like_token(obj):
                        return obj[:20] + "...[REDACTED]"
                    return obj
                else:
                    return obj
            finally:
                # 處理完後從 seen 移除
                if isinstance(obj, (dict, list)):
                    seen.discard(obj_id)

        return sanitize_recursive(sanitized)


# 全域實例
transaction_logger = BigQueryTransactionLogger()


def log_payment_attempt(
    transaction_id: str,
    user_id: int,
    user_email: str,
    amount: int,
    plan_name: str,
    prime_token: str,
    request_data: Dict,
    user_agent: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> None:
    """記錄付款嘗試（開始時）"""
    transaction_logger.log_transaction(
        transaction_id=transaction_id,
        user_id=user_id,
        user_email=user_email,
        amount=amount,
        plan_name=plan_name,
        tappay_prime_token=prime_token,
        status="pending",
        request_body=request_data,
        user_agent=user_agent,
        client_ip=client_ip,
    )


def log_payment_success(
    transaction_id: str,
    user_id: int,
    user_email: str,
    amount: int,
    plan_name: str,
    tappay_response: Dict,
    tappay_rec_trade_id: str,
    execution_time_ms: int,
) -> None:
    """記錄付款成功"""
    transaction_logger.log_transaction(
        transaction_id=transaction_id,
        user_id=user_id,
        user_email=user_email,
        amount=amount,
        plan_name=plan_name,
        status="success",
        tappay_response=tappay_response,
        tappay_rec_trade_id=tappay_rec_trade_id,
        response_status=200,
        execution_time_ms=execution_time_ms,
    )


def log_payment_failure(
    transaction_id: Optional[str],
    user_id: Optional[int],
    user_email: Optional[str],
    amount: Optional[int],
    plan_name: Optional[str],
    error_stage: str,  # authentication, prime_token, tappay_api, database, unknown
    error_code: Optional[str],
    error_message: str,
    request_data: Optional[Dict] = None,
    response_status: Optional[int] = None,
    response_body: Optional[Dict] = None,
    stack_trace: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
) -> None:
    """記錄付款失敗"""
    transaction_logger.log_transaction(
        transaction_id=transaction_id,
        user_id=user_id,
        user_email=user_email,
        amount=amount,
        plan_name=plan_name,
        status="failed",
        error_stage=error_stage,
        error_code=error_code,
        error_message=error_message,
        request_body=request_data,
        response_status=response_status,
        response_body=response_body,
        stack_trace=stack_trace,
        execution_time_ms=execution_time_ms,
    )


def log_refund_event(
    teacher_id: int,
    teacher_email: str,
    original_transaction_id: str,
    refund_transaction_id: Optional[str],
    original_amount: float,
    refund_amount: float,
    refund_type: str,  # "full" or "partial"
    subscription_type: str,  # "月方案" or "季方案"
    days_deducted: int,
    previous_end_date: str,  # ISO format
    new_end_date: str,  # ISO format
    refund_reason: Optional[str] = None,
    gateway_response: Optional[Dict] = None,
    **kwargs,
) -> None:
    """
    記錄退款事件到 BigQuery

    Args:
        teacher_id: 教師 ID
        teacher_email: 教師 email
        original_transaction_id: 原始交易 ID (TapPay rec_trade_id)
        refund_transaction_id: 退款交易 ID (TapPay refund rec_trade_id)
        original_amount: 原始交易金額
        refund_amount: 退款金額
        refund_type: 退款類型 (full/partial)
        subscription_type: 訂閱方案
        days_deducted: 扣除的訂閱天數
        previous_end_date: 退款前到期日
        new_end_date: 退款後到期日
        refund_reason: 退款原因
        gateway_response: 金流商完整回應
    """
    try:
        # 計算退款比例
        refund_ratio = (
            (refund_amount / original_amount * 100) if original_amount > 0 else 0
        )

        # 準備 BigQuery 資料
        refund_data = {
            # 基本資訊
            "event_type": "refund",
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
            # 用戶資訊
            "teacher_id": teacher_id,
            "teacher_email": teacher_email,
            # 交易資訊
            "original_transaction_id": original_transaction_id,
            "refund_transaction_id": refund_transaction_id,
            # 金額資訊
            "original_amount": float(original_amount),
            "refund_amount": float(refund_amount),
            "refund_ratio": round(refund_ratio, 2),
            "currency": "TWD",
            # 退款類型
            "refund_type": refund_type,
            "refund_reason": refund_reason or "customer_service_refund",
            # 訂閱影響
            "subscription_type": subscription_type,
            "days_deducted": days_deducted,
            "previous_end_date": previous_end_date,
            "new_end_date": new_end_date,
            # 業務指標
            "financial_impact": -float(refund_amount),  # 負數表示支出
            "subscription_impact_days": -days_deducted,  # 負數表示減少
            # 金流商資訊
            "payment_provider": "tappay",
            "gateway_response": gateway_response,
            # 環境資訊
            "environment": os.getenv("ENVIRONMENT", "unknown"),
        }

        # 記錄到 BigQuery
        transaction_logger.log_transaction(
            transaction_id=refund_transaction_id or original_transaction_id,
            user_id=teacher_id,
            user_email=teacher_email,
            amount=int(refund_amount),
            plan_name=subscription_type,
            status="refund_completed",
            event_data=refund_data,
        )

        logger.info(
            f"✅ Refund event logged to BigQuery: teacher={teacher_id}, "
            f"amount={refund_amount}, type={refund_type}, days_deducted={days_deducted}"
        )

    except Exception as e:
        logger.error(f"❌ Failed to log refund event to BigQuery: {str(e)}")
        # 不拋出異常，避免影響退款處理主流程
