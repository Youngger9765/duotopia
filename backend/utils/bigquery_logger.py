"""
BigQuery Logger for Transaction Data Collection
收集所有金流交易資料（成功與失敗）到 BigQuery
"""

import os
import json
import traceback
from datetime import datetime
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
            self.client = bigquery.Client(project=self.project_id)
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
                "tappay_response": json.dumps(tappay_response)
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
                "response_body": json.dumps(response_body) if response_body else None,
                # 前端資訊
                "frontend_error": json.dumps(frontend_error)
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

        if "cardholder" in sanitized:
            # 保留 cardholder 但移除可能的敏感資訊
            pass

        return sanitized


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
