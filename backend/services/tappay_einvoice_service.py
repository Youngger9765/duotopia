"""
TapPay E-Invoice Service
處理 TapPay 電子發票串接（基於 Open API 規格 V1.4）

API 文件: docs/payment/電子發票Open_API規格_商戶_V1.4.pdf
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models import TeacherSubscriptionTransaction, InvoiceStatusHistory
from core.http_client import get_http_session

logger = logging.getLogger(__name__)


class TapPayEInvoiceService:
    """TapPay 電子發票服務"""

    def __init__(self):
        self.partner_key = os.getenv("TAPPAY_PARTNER_KEY")
        if not self.partner_key:
            raise ValueError("TAPPAY_PARTNER_KEY environment variable is required")

        self.merchant_id = os.getenv("TAPPAY_MERCHANT_ID")
        if not self.merchant_id:
            raise ValueError("TAPPAY_MERCHANT_ID environment variable is required")

        # 根據環境選擇 API URL
        self.environment = os.getenv("TAPPAY_ENV", "sandbox")
        if self.environment == "production":
            self.base_url = "https://prod.tappaysdk.com/tpc/einvoice"
        else:
            self.base_url = "https://sandbox.tappaysdk.com/tpc/einvoice"

        # Use shared HTTP session with connection pooling
        self.session = get_http_session()

        logger.info(f"TapPay E-Invoice Service initialized in {self.environment} mode")

    def _make_request(self, endpoint: str, payload: Dict, method: str = "POST") -> Dict:
        """
        發送 API 請求的通用方法

        Args:
            endpoint: API 端點
            payload: 請求資料
            method: HTTP 方法

        Returns:
            API 回應
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.partner_key,
        }

        # 自動加入 partner_key
        if "partner_key" not in payload:
            payload["partner_key"] = self.partner_key

        try:
            logger.info(f"TapPay E-Invoice API: {method} {url}")

            # Use connection pool for better performance
            if method == "POST":
                response = self.session.post(
                    url, json=payload, headers=headers, timeout=30
                )
            else:
                response = self.session.get(
                    url, params=payload, headers=headers, timeout=30
                )

            response.raise_for_status()
            result = response.json()

            logger.info(
                f"E-Invoice API response: status={result.get('status')}, "
                f"rec_invoice_id={result.get('rec_invoice_id')}"
            )

            return result

        except Exception as e:
            # Handle both requests exceptions and other errors
            logger.error(f"TapPay E-Invoice API error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "API_REQUEST_FAILED"}

    def issue_invoice(
        self,
        db: Session,
        transaction: TeacherSubscriptionTransaction,
        buyer_email: str,
        buyer_tax_id: Optional[str] = None,
        buyer_name: Optional[str] = None,
        carrier_type: Optional[str] = None,
        carrier_id: Optional[str] = None,
    ) -> Dict:
        """
        開立發票 (Issue API)

        Args:
            db: 資料庫 session
            transaction: 交易記錄
            buyer_email: 買受人 email (必填)
            buyer_tax_id: 統一編號 (B2B 必填)
            buyer_name: 買受人名稱 (B2B 必填)
            carrier_type: 載具類型 (3J0002=手機條碼)
            carrier_id: 載具號碼

        Returns:
            TapPay API 回應
        """
        # 構建 API payload
        payload = {
            "rec_trade_id": transaction.external_transaction_id,  # TapPay 交易編號
            "buyer_email": buyer_email,  # 必填
            "issue_notify_email": "AUTO",  # 自動發送發票 email
        }

        # B2B 發票
        if buyer_tax_id:
            payload["buyer_tax_id"] = buyer_tax_id
            payload["buyer_name"] = buyer_name or "公司名稱"
            payload["invoice_type"] = "B2B"
        else:
            payload["invoice_type"] = "B2C"

        # 載具資訊
        if carrier_type and carrier_id:
            payload["carrier_type"] = carrier_type
            payload["carrier_id"] = carrier_id

        try:
            # 呼叫 TapPay Issue API
            result = self._make_request("issue", payload)

            # 更新資料庫
            if result.get("status") == 0:
                # 成功開立
                transaction.rec_invoice_id = result.get("rec_invoice_id")
                transaction.invoice_number = result.get("invoice_number")
                transaction.invoice_status = "ISSUED"
                transaction.invoice_issued_at = datetime.now()
                transaction.buyer_email = buyer_email
                transaction.buyer_tax_id = buyer_tax_id
                transaction.buyer_name = buyer_name
                transaction.carrier_type = carrier_type
                transaction.carrier_id = carrier_id
                transaction.invoice_response = result

                # 記錄狀態變更歷史
                history = InvoiceStatusHistory(
                    transaction_id=transaction.id,
                    from_status="PENDING",
                    to_status="ISSUED",
                    action_type="ISSUE",
                    reason="開立發票",
                    request_payload=payload,
                    response_payload=result,
                )
                db.add(history)
                db.commit()

                logger.info(
                    f"Invoice issued successfully: rec_invoice_id={result.get('rec_invoice_id')}, "
                    f"invoice_number={result.get('invoice_number')}"
                )
            else:
                # 開立失敗
                transaction.invoice_status = "ERROR"
                transaction.invoice_response = result

                history = InvoiceStatusHistory(
                    transaction_id=transaction.id,
                    from_status="PENDING",
                    to_status="ERROR",
                    action_type="ISSUE",
                    reason=f"開立失敗: {result.get('msg')}",
                    request_payload=payload,
                    response_payload=result,
                )
                db.add(history)
                db.commit()

                logger.error(
                    f"Invoice issue failed: status={result.get('status')}, "
                    f"msg={result.get('msg')}"
                )

            return result

        except Exception as e:
            logger.error(f"Issue invoice error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "ISSUE_FAILED"}

    def void_invoice(
        self,
        db: Session,
        transaction: TeacherSubscriptionTransaction,
        reason: str = "用戶申請退款",
    ) -> Dict:
        """
        作廢發票 (Void API) - 當期發票使用

        Args:
            db: 資料庫 session
            transaction: 交易記錄
            reason: 作廢原因

        Returns:
            TapPay API 回應
        """
        if not transaction.rec_invoice_id:
            return {"status": -1, "msg": "No invoice to void", "error": "NO_INVOICE"}

        payload = {
            "rec_invoice_id": transaction.rec_invoice_id,
            "void_reason": reason,
        }

        try:
            result = self._make_request("void", payload)

            if result.get("status") == 0:
                old_status = transaction.invoice_status
                transaction.invoice_status = "VOIDED"
                transaction.invoice_response = result

                history = InvoiceStatusHistory(
                    transaction_id=transaction.id,
                    from_status=old_status,
                    to_status="VOIDED",
                    action_type="VOID",
                    reason=reason,
                    request_payload=payload,
                    response_payload=result,
                )
                db.add(history)
                db.commit()

                logger.info(
                    f"Invoice voided: rec_invoice_id={transaction.rec_invoice_id}"
                )

            return result

        except Exception as e:
            logger.error(f"Void invoice error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "VOID_FAILED"}

    def issue_allowance(
        self,
        db: Session,
        transaction: TeacherSubscriptionTransaction,
        allowance_amount: int,
        reason: str = "用戶申請退款",
    ) -> Dict:
        """
        開立折讓 (Allowance API) - 跨期退款使用

        Args:
            db: 資料庫 session
            transaction: 交易記錄
            allowance_amount: 折讓金額
            reason: 折讓原因

        Returns:
            TapPay API 回應
        """
        if not transaction.rec_invoice_id:
            return {
                "status": -1,
                "msg": "No invoice for allowance",
                "error": "NO_INVOICE",
            }

        payload = {
            "rec_invoice_id": transaction.rec_invoice_id,
            "allowance_amount": allowance_amount,
            "allowance_reason": reason,
        }

        try:
            result = self._make_request("allowance", payload)

            if result.get("status") == 0:
                old_status = transaction.invoice_status
                transaction.invoice_status = "ALLOWANCED"
                transaction.invoice_response = result

                history = InvoiceStatusHistory(
                    transaction_id=transaction.id,
                    from_status=old_status,
                    to_status="ALLOWANCED",
                    action_type="ALLOWANCE",
                    reason=f"{reason} (金額: {allowance_amount})",
                    request_payload=payload,
                    response_payload=result,
                )
                db.add(history)
                db.commit()

                logger.info(
                    f"Allowance issued: rec_invoice_id={transaction.rec_invoice_id}, "
                    f"amount={allowance_amount}"
                )

            return result

        except Exception as e:
            logger.error(f"Issue allowance error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "ALLOWANCE_FAILED"}

    def query_invoice(self, rec_invoice_id: str) -> Dict:
        """
        查詢發票狀態 (Query API)

        Args:
            rec_invoice_id: TapPay 發票編號

        Returns:
            發票詳細資訊
        """
        payload = {"rec_invoice_id": rec_invoice_id}

        try:
            result = self._make_request("query", payload, method="GET")
            return result

        except Exception as e:
            logger.error(f"Query invoice error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "QUERY_FAILED"}

    def handle_notify(self, db: Session, notify_data: Dict) -> Dict:
        """
        處理 TapPay Notify Webhook (當發票上傳到財政部失敗時觸發)

        Args:
            db: 資料庫 session
            notify_data: Notify webhook payload

        Returns:
            處理結果
        """
        rec_invoice_id = notify_data.get("rec_invoice_id")
        error_code = notify_data.get("error_code")
        error_msg = notify_data.get("error_msg")

        if not rec_invoice_id:
            return {"status": -1, "msg": "Missing rec_invoice_id"}

        try:
            # 查找對應交易
            transaction = (
                db.query(TeacherSubscriptionTransaction)
                .filter_by(rec_invoice_id=rec_invoice_id)
                .first()
            )

            if not transaction:
                logger.warning(
                    f"Transaction not found for rec_invoice_id: {rec_invoice_id}"
                )
                return {"status": -1, "msg": "Transaction not found"}

            # 更新狀態為 ERROR
            old_status = transaction.invoice_status
            transaction.invoice_status = "ERROR"
            transaction.invoice_response = notify_data

            # 記錄 Notify 事件
            history = InvoiceStatusHistory(
                transaction_id=transaction.id,
                from_status=old_status,
                to_status="ERROR",
                action_type="NOTIFY",
                reason=f"Notify: {error_msg}",
                is_notify=True,
                notify_error_code=error_code,
                notify_error_msg=error_msg,
                request_payload=None,
                response_payload=notify_data,
            )
            db.add(history)
            db.commit()

            logger.warning(
                f"Invoice notify received: rec_invoice_id={rec_invoice_id}, "
                f"error_code={error_code}, error_msg={error_msg}"
            )

            return {"status": 0, "msg": "Notify processed"}

        except Exception as e:
            logger.error(f"Handle notify error: {str(e)}")
            return {"status": -1, "msg": str(e), "error": "NOTIFY_FAILED"}

    @staticmethod
    def determine_refund_method(
        invoice_issued_at: datetime,
    ) -> str:
        """
        判斷退款時應使用 Void 或 Allowance

        Args:
            invoice_issued_at: 發票開立時間

        Returns:
            "void" or "allowance"
        """
        current_month = datetime.now().strftime("%Y-%m")
        invoice_month = invoice_issued_at.strftime("%Y-%m")

        if current_month == invoice_month:
            return "void"  # 當期 → 作廢
        else:
            return "allowance"  # 跨期 → 折讓
