from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import uuid
import os

from database import get_db
from models import Teacher, TeacherSubscriptionTransaction, TransactionType
from routers.teachers import get_current_teacher
from services.tappay_service import TapPayService
from services.email_service import email_service
from services.subscription_calculator import SubscriptionCalculator
from utils.bigquery_logger import (
    log_payment_attempt,
    log_payment_success,
    log_payment_failure,
    log_refund_event,
    transaction_logger,
)
import time
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

# 🔐 環境配置：是否啟用付款功能
ENABLE_PAYMENT = os.getenv("ENABLE_PAYMENT", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")


class PaymentRequest(BaseModel):
    """TapPay payment request"""

    prime: str  # TapPay prime token
    amount: int  # Amount in TWD
    plan_name: str  # Subscription plan name
    details: Optional[Dict[str, Any]] = None
    cardholder: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Payment response"""

    success: bool
    transaction_id: Optional[str] = None
    message: str
    subscription_end_date: Optional[str] = None


class FrontendErrorLog(BaseModel):
    """前端錯誤記錄"""

    timestamp: str
    environment: str
    error_stage: str
    error_message: str
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    amount: Optional[int] = None
    plan_name: Optional[str] = None
    tappay_status: Optional[str] = None
    tappay_message: Optional[str] = None
    can_get_prime: Optional[bool] = None
    user_agent: str
    url: str
    additional_context: Optional[Dict[str, Any]] = None


@router.post("/payment/process", response_model=PaymentResponse)
async def process_payment(
    request: Request,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """Process payment using TapPay"""
    # 🚫 檢查是否啟用付款功能
    if not ENABLE_PAYMENT:
        logger.info(f"付款功能未啟用 (ENVIRONMENT={ENVIRONMENT}), 返回免費優惠期提醒")
        return PaymentResponse(
            success=False,
            transaction_id=None,
            message="目前仍在免費優惠期間，未來將會開放儲值功能。感謝您的支持！",
        )

    # 先取得原始請求體來debug
    try:
        body = await request.body()
        import json

        body_json = json.loads(body)
        logger.info(f"收到付款請求 - Teacher: {current_teacher.email}")
        logger.info(f"請求內容: {body_json}")

        # 手動解析 PaymentRequest
        payment_request = PaymentRequest(**body_json)
        logger.info(
            f"解析成功 - Plan: {payment_request.plan_name}, Amount: {payment_request.amount}"
        )
    except Exception as e:
        logger.error(f"解析請求失敗: {str(e)}")
        raise

    # 📊 開始計時
    start_time = time.time()

    try:
        # Generate idempotency key to prevent duplicate charges
        idempotency_key = str(uuid.uuid4())
        order_number = (
            f"DUO_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_teacher.id}"
        )

        # Get client info for audit trail
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # 📊 Log payment attempt to BigQuery
        log_payment_attempt(
            transaction_id=order_number,
            user_id=current_teacher.id,
            user_email=current_teacher.email,
            amount=payment_request.amount,
            plan_name=payment_request.plan_name,
            prime_token=payment_request.prime,
            request_data=body_json,
            user_agent=user_agent,
            client_ip=client_host,
        )

        # Get current time (needed for exception handling)
        now = datetime.now(timezone.utc)

        # Calculate subscription months based on plan
        if payment_request.plan_name == "Tutor Teachers":
            months = 1
            expected_amount = 230
        elif payment_request.plan_name == "School Teachers":
            months = 1
            expected_amount = 330
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown plan: {payment_request.plan_name}"
            )

        # Verify amount matches plan price
        if payment_request.amount != expected_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Amount mismatch. Expected {expected_amount}, got {payment_request.amount}",
            )

        # 🔄 統一每月 1 號續訂邏輯
        if (
            current_teacher.subscription_end_date
            and current_teacher.subscription_end_date > now
        ):
            # 延長現有訂閱（續訂）
            previous_end_date = current_teacher.subscription_end_date
            new_end_date, _ = SubscriptionCalculator.calculate_renewal(
                previous_end_date, payment_request.plan_name
            )
            logger.info(
                f"Renewal: extending subscription from {previous_end_date.date()} "
                f"to {new_end_date.date()}"
            )
        else:
            # 首次訂閱
            previous_end_date = None
            (
                new_end_date,
                _,
                details,
            ) = SubscriptionCalculator.calculate_first_subscription(
                now, payment_request.plan_name
            )
            logger.info(
                f"First subscription: {now.date()} -> {new_end_date.date()} "
                f"({details['actual_days']} days, bonus: {details['bonus_days']} days)"
            )

        # Process payment with TapPay (Sandbox or Production based on env)
        logger.info(f"Processing payment for order: {order_number}")
        tappay_service = TapPayService()

        gateway_response = tappay_service.process_payment(
            prime=payment_request.prime,
            amount=payment_request.amount,
            details=payment_request.details or {"item_name": payment_request.plan_name},
            cardholder=payment_request.cardholder
            or {"name": current_teacher.name, "email": current_teacher.email},
            order_number=order_number,
            remember=True,  # ✅ 儲存信用卡資訊以供自動續訂使用
        )

        # Check if payment was successful
        if gateway_response.get("status") != 0:
            # Payment failed
            error_msg = TapPayService.parse_error_code(
                gateway_response.get("status"), gateway_response.get("msg")
            )

            # 📊 Log payment failure to BigQuery
            execution_time = int((time.time() - start_time) * 1000)
            log_payment_failure(
                transaction_id=order_number,
                user_id=current_teacher.id,
                user_email=current_teacher.email,
                amount=payment_request.amount,
                plan_name=payment_request.plan_name,
                error_stage="tappay_api",
                error_code=str(gateway_response.get("status")),
                error_message=error_msg,
                request_data=body_json,
                response_status=400,
                response_body=gateway_response,
                execution_time_ms=execution_time,
            )

            # Log failed transaction
            failed_transaction = TeacherSubscriptionTransaction(
                teacher_id=current_teacher.id,
                teacher_email=current_teacher.email,
                transaction_type=TransactionType.RECHARGE,
                subscription_type=payment_request.plan_name,
                amount=payment_request.amount,
                currency="TWD",
                status="FAILED",
                months=months,
                new_end_date=now,
                idempotency_key=idempotency_key,
                ip_address=client_host,
                user_agent=user_agent,
                request_id=request_id,
                payment_provider="tappay",
                payment_method="credit_card",
                external_transaction_id=gateway_response.get("rec_trade_id"),
                failure_reason=error_msg,
                error_code=str(gateway_response.get("status")),
                gateway_response=gateway_response,
                processed_at=now,
            )
            db.add(failed_transaction)
            db.commit()

            raise HTTPException(status_code=400, detail=error_msg)

        # Payment successful - update teacher's subscription
        current_teacher.subscription_end_date = new_end_date
        current_teacher.subscription_type = payment_request.plan_name

        # Get transaction ID from response
        external_transaction_id = gateway_response.get("rec_trade_id")

        # 💳 儲存信用卡 Token（用於自動續訂）
        # 根據 TapPay 文件，交易授權成功才會返回有效的 card_key 和 card_token
        if gateway_response.get("card_secret"):
            card_secret = gateway_response["card_secret"]
            card_info = gateway_response.get("card_info", {})

            current_teacher.card_key = card_secret.get("card_key")
            current_teacher.card_token = card_secret.get("card_token")
            current_teacher.card_last_four = card_info.get("last_four")
            current_teacher.card_bin_code = card_info.get("bin_code")
            current_teacher.card_type = card_info.get("type")
            current_teacher.card_funding = card_info.get("funding")
            current_teacher.card_issuer = card_info.get("issuer")
            current_teacher.card_country = card_info.get("country")
            current_teacher.card_saved_at = now

            logger.info(
                f"Card saved for auto-renewal: {current_teacher.email} - "
                f"****{current_teacher.card_last_four} ({current_teacher.card_issuer})"
            )

        # ⚠️ CRITICAL FIX: Commit teacher's subscription update FIRST
        # This ensures subscription is activated even if transaction record creation fails
        db.commit()
        logger.info(
            f"Teacher subscription updated: {current_teacher.email} -> {new_end_date}"
        )

        # Now create subscription transaction record with all security fields
        try:
            transaction = TeacherSubscriptionTransaction(
                # User identification
                teacher_id=current_teacher.id,
                teacher_email=current_teacher.email,  # Store email directly
                # Transaction basic info
                transaction_type=TransactionType.RECHARGE,
                subscription_type=payment_request.plan_name,
                amount=payment_request.amount,
                currency="TWD",
                status="SUCCESS",
                months=months,
                # Time related
                period_start=now,
                period_end=new_end_date,
                previous_end_date=previous_end_date,
                new_end_date=new_end_date,
                processed_at=now,
                # Security & audit
                idempotency_key=idempotency_key,
                retry_count=0,
                ip_address=client_host,
                user_agent=user_agent,
                request_id=request_id,
                # Payment details
                payment_provider="tappay",
                payment_method="credit_card",
                external_transaction_id=external_transaction_id,
                # Gateway response
                gateway_response=gateway_response,
                # Legacy metadata field (for backward compatibility)
                transaction_metadata={
                    "plan_name": payment_request.plan_name,
                    "cardholder": payment_request.cardholder,
                    "prime_token": payment_request.prime[:10]
                    + "...",  # Store partial for debugging
                },
            )

            db.add(transaction)
            db.commit()
            logger.info(
                f"Payment processed successfully for teacher {current_teacher.email}: {external_transaction_id}"
            )

            # 📊 Log payment success to BigQuery
            execution_time = int((time.time() - start_time) * 1000)
            log_payment_success(
                transaction_id=external_transaction_id,
                user_id=current_teacher.id,
                user_email=current_teacher.email,
                amount=payment_request.amount,
                plan_name=payment_request.plan_name,
                tappay_response=gateway_response,
                tappay_rec_trade_id=external_transaction_id,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            # Transaction record creation failed, but subscription is already updated (acceptable)
            logger.error(
                f"Failed to create transaction record: {e}, but subscription is already updated"
            )
            # Continue execution - the important part (subscription update) is done

        return PaymentResponse(
            success=True,
            transaction_id=external_transaction_id,
            message=f"成功訂閱 {payment_request.plan_name} 方案",
            subscription_end_date=new_end_date.isoformat(),
        )

    except HTTPException as he:
        # 📊 Log HTTP exception failure to BigQuery
        execution_time = int((time.time() - start_time) * 1000)

        # 判斷錯誤階段
        error_stage = "unknown"
        if he.status_code == 400:
            if "prime" in str(he.detail).lower():
                error_stage = "prime_token"
            elif "plan" in str(he.detail).lower():
                error_stage = "validation"
            else:
                error_stage = "tappay_api"
        elif he.status_code == 401:
            error_stage = "authentication"

        log_payment_failure(
            transaction_id=order_number if "order_number" in locals() else None,
            user_id=current_teacher.id,
            user_email=current_teacher.email,
            amount=payment_request.amount,
            plan_name=payment_request.plan_name,
            error_stage=error_stage,
            error_code=str(he.status_code),
            error_message=str(he.detail),
            request_data=body_json,
            response_status=he.status_code,
            execution_time_ms=execution_time,
        )

        # Log failed transaction attempt
        try:
            failed_transaction = TeacherSubscriptionTransaction(
                teacher_id=current_teacher.id,
                teacher_email=current_teacher.email,
                transaction_type=TransactionType.RECHARGE,
                subscription_type=payment_request.plan_name,
                amount=payment_request.amount,
                currency="TWD",
                status="FAILED",
                months=months,
                new_end_date=now,  # Default value
                idempotency_key=str(uuid.uuid4()),  # New key to avoid duplicate
                ip_address=client_host,
                user_agent=user_agent,
                request_id=request_id,
                payment_provider="tappay",
                payment_method="credit_card",
                failure_reason=str(he.detail),
                error_code=str(he.status_code),
                processed_at=now,
            )
            db.add(failed_transaction)
            db.commit()
        except Exception as log_error:
            logger.error(f"Failed to log failed transaction: {log_error}")
            db.rollback()

        # Return error response instead of raising exception
        return PaymentResponse(
            success=False, transaction_id=None, message=str(he.detail)
        )
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}", exc_info=True)

        # 📊 Log unexpected exception to BigQuery
        execution_time = int((time.time() - start_time) * 1000)
        log_payment_failure(
            transaction_id=order_number if "order_number" in locals() else None,
            user_id=current_teacher.id,
            user_email=current_teacher.email,
            amount=payment_request.amount if payment_request else None,
            plan_name=payment_request.plan_name if payment_request else None,
            error_stage="database" if "database" in str(e).lower() else "unknown",
            error_code="INTERNAL_ERROR",
            error_message=str(e),
            request_data=body_json if "body_json" in locals() else None,
            response_status=500,
            stack_trace=traceback.format_exc(),
            execution_time_ms=execution_time,
        )

        # Try to log failed transaction
        try:
            failed_transaction = TeacherSubscriptionTransaction(
                teacher_id=current_teacher.id,
                teacher_email=current_teacher.email,
                transaction_type=TransactionType.RECHARGE,
                subscription_type=payment_request.plan_name,
                amount=payment_request.amount,
                currency="TWD",
                status="FAILED",
                months=months,
                new_end_date=now,  # Default value
                idempotency_key=str(uuid.uuid4()),  # New key to avoid duplicate
                ip_address=client_host,
                user_agent=user_agent,
                request_id=request_id,
                payment_provider="tappay",
                payment_method="credit_card",
                failure_reason=str(e),
                error_code="INTERNAL_ERROR",
                processed_at=now,
            )
            db.add(failed_transaction)
            db.commit()
        except Exception as log_error:
            logger.error(f"Failed to log transaction: {log_error}")
            db.rollback()

        # Return error response instead of raising exception
        return PaymentResponse(
            success=False, transaction_id=None, message=f"系統錯誤：{str(e)}"
        )


@router.post("/payment/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """
    TapPay Webhook handler
    處理支付狀態更新、3D驗證結果等
    """
    try:
        # Get raw body for signature verification
        body = await request.body()

        # Get signature from header
        signature = request.headers.get("X-TapPay-Signature", "")

        # Verify webhook signature
        if not TapPayService.validate_webhook(body, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse webhook data
        data = await request.json()

        rec_trade_id = data.get("rec_trade_id")
        status = data.get("status")
        msg = data.get("msg")
        event = data.get("event", "payment")  # TapPay 事件類型：payment, refund, etc.

        logger.info(
            f"Webhook received - event: {event}, rec_trade_id: {rec_trade_id}, status: {status}"
        )

        # Find transaction in database
        transaction = (
            db.query(TeacherSubscriptionTransaction)
            .filter(
                TeacherSubscriptionTransaction.external_transaction_id == rec_trade_id
            )
            .first()
        )

        if not transaction:
            logger.error(f"Transaction not found: {rec_trade_id}")
            return {"status": "error", "message": "Transaction not found"}

        # 🔧 處理退款事件
        if event == "refund" or data.get("is_refund"):
            logger.info(f"Processing refund for transaction: {rec_trade_id}")

            # 檢查是否已處理過（避免重複處理）
            if transaction.refund_status == "completed":
                logger.warning(
                    f"Refund already processed for transaction: {rec_trade_id}"
                )
                return {"status": "success", "message": "Refund already processed"}

            # 記錄退款前狀態
            previous_end_date = transaction.teacher.subscription_end_date
            teacher = transaction.teacher

            # 計算退款金額和類型
            refund_amount = float(data.get("refund_amount", transaction.amount))
            original_amount = float(transaction.amount)
            is_full_refund = refund_amount >= original_amount
            refund_type = "full" if is_full_refund else "partial"

            # 計算扣除天數
            if is_full_refund:
                # 全額退款 - 扣除完整訂閱天數
                days_to_deduct = 30 if transaction.subscription_type == "月方案" else 90
            else:
                # 部分退款 - 按比例調整
                refund_ratio = refund_amount / original_amount
                days_to_deduct = int(
                    (30 if transaction.subscription_type == "月方案" else 90)
                    * refund_ratio
                )

            # 更新原始交易狀態
            transaction.status = "REFUNDED"
            transaction.webhook_status = "PROCESSED"
            transaction.failure_reason = f"退款處理: {msg}"
            transaction.refunded_amount = refund_amount
            transaction.refund_status = "completed"
            transaction.processed_at = datetime.now(timezone.utc)

            # 建立獨立退款交易記錄
            refund_transaction = TeacherSubscriptionTransaction(
                teacher_id=transaction.teacher_id,
                teacher_email=transaction.teacher_email,
                transaction_type=TransactionType.REFUND,
                subscription_type=transaction.subscription_type,
                amount=-refund_amount,  # 負數表示退款
                currency="TWD",
                status="SUCCESS",
                months=transaction.months,
                period_start=transaction.period_start,
                period_end=transaction.period_end,
                previous_end_date=previous_end_date,
                new_end_date=teacher.subscription_end_date
                - timedelta(days=days_to_deduct),
                processed_at=datetime.now(timezone.utc),
                payment_provider="tappay",
                payment_method=transaction.payment_method,
                external_transaction_id=data.get("refund_rec_trade_id"),
                original_transaction_id=transaction.id,
                gateway_response=data,
                webhook_status="PROCESSED",
            )

            # 調整訂閱到期日
            if teacher.subscription_end_date:
                teacher.subscription_end_date -= timedelta(days=days_to_deduct)
                teacher.updated_at = datetime.now(timezone.utc)

                logger.info(
                    f"{refund_type.capitalize()} refund: deducted {days_to_deduct} days from subscription. "
                    f"New end date: {teacher.subscription_end_date}"
                )

            # 儲存退款交易
            db.add(refund_transaction)
            db.flush()  # 確保取得 refund_transaction.id

            # 📊 記錄到 BigQuery
            try:
                log_refund_event(
                    teacher_id=teacher.id,
                    teacher_email=teacher.email,
                    original_transaction_id=rec_trade_id,
                    refund_transaction_id=data.get("refund_rec_trade_id"),
                    original_amount=original_amount,
                    refund_amount=refund_amount,
                    refund_type=refund_type,
                    subscription_type=transaction.subscription_type or "unknown",
                    days_deducted=days_to_deduct,
                    previous_end_date=previous_end_date.isoformat()
                    if previous_end_date
                    else None,
                    new_end_date=teacher.subscription_end_date.isoformat()
                    if teacher.subscription_end_date
                    else None,
                    refund_reason=msg,
                    gateway_response=data,
                )
            except Exception as e:
                logger.error(f"Failed to log refund to BigQuery: {str(e)}")

            # 📧 發送退款通知 Email
            try:
                email_service.send_refund_notification(
                    teacher_email=teacher.email,
                    teacher_name=teacher.name,
                    refund_amount=refund_amount,
                    original_amount=original_amount,
                    refund_type=refund_type,
                    subscription_type=transaction.subscription_type or "未知方案",
                    days_deducted=days_to_deduct,
                    new_end_date=teacher.subscription_end_date,
                )
            except Exception as e:
                logger.error(f"Failed to send refund notification email: {str(e)}")

        # 🔧 處理付款事件
        elif status == 0:
            # Payment successful
            transaction.status = "SUCCESS"
            transaction.webhook_status = "PROCESSED"

            # Update teacher subscription if not already updated
            teacher = transaction.teacher
            if teacher.subscription_end_date < transaction.new_end_date:
                teacher.subscription_end_date = transaction.new_end_date

        else:
            # Payment failed
            transaction.status = "FAILED"
            transaction.webhook_status = "PROCESSED"
            transaction.failure_reason = msg
            transaction.error_code = str(status)

        # Store full webhook data
        transaction.gateway_response = data
        db.commit()

        return {"status": "success", "message": "Webhook processed"}

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/payment/history")
async def get_payment_history(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """Get payment history for current teacher"""
    transactions = (
        db.query(TeacherSubscriptionTransaction)
        .filter_by(teacher_id=current_teacher.id)
        .order_by(TeacherSubscriptionTransaction.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "transactions": [
            {
                "id": t.id,
                "type": t.transaction_type.value,
                "amount": float(t.amount) if t.amount else 0,
                "currency": t.currency,
                "status": t.status,
                "months": t.months,
                "created_at": t.created_at.isoformat(),
                "subscription_type": t.subscription_type,
            }
            for t in transactions
        ]
    }


@router.post("/payment/log-frontend-error")
async def log_frontend_error(
    error_data: FrontendErrorLog,
    request: Request,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """接收前端錯誤並記錄到 BigQuery"""
    try:
        # 📊 記錄前端錯誤到 BigQuery
        transaction_logger.log_transaction(
            user_id=current_teacher.id,
            user_email=current_teacher.email,
            amount=error_data.amount,
            plan_name=error_data.plan_name,
            status="failed",
            error_stage=error_data.error_stage,
            error_code=error_data.error_code,
            error_message=error_data.error_message,
            frontend_error={
                "timestamp": error_data.timestamp,
                "tappay_status": error_data.tappay_status,
                "tappay_message": error_data.tappay_message,
                "can_get_prime": error_data.can_get_prime,
                "url": error_data.url,
                "additional_context": error_data.additional_context,
            },
            user_agent=error_data.user_agent,
            client_ip=request.client.host if request.client else None,
            stack_trace=error_data.stack_trace,
        )

        return {"success": True, "message": "Error logged"}

    except Exception as e:
        logger.error(f"Failed to log frontend error: {e}")
        return {"success": False, "message": str(e)}


@router.post("/subscription/cancel")
async def cancel_subscription(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    取消自動續訂
    - 已付費的訂閱期限繼續有效
    - 到期後不再自動扣款
    - 可隨時重新訂閱
    """
    try:
        # 檢查是否有有效訂閱
        if not current_teacher.subscription_end_date:
            raise HTTPException(status_code=400, detail="您目前沒有訂閱")

        # 處理 timezone-aware 和 naive datetime 比較
        now = datetime.now(timezone.utc)
        end_date = current_teacher.subscription_end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if end_date < now:
            raise HTTPException(status_code=400, detail="您的訂閱已過期")

        # 檢查是否已經取消
        if not current_teacher.subscription_auto_renew:
            return {
                "success": True,
                "message": "您已經取消過續訂",
                "subscription_end_date": current_teacher.subscription_end_date.isoformat(),
                "auto_renew": False,
            }

        # 取消自動續訂
        current_teacher.subscription_auto_renew = False
        current_teacher.subscription_cancelled_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            f"Teacher {current_teacher.id} cancelled auto-renew. "
            f"Subscription valid until {current_teacher.subscription_end_date}"
        )

        return {
            "success": True,
            "message": f"已取消自動續訂，您的訂閱將於 {current_teacher.subscription_end_date.strftime('%Y/%m/%d')} 到期",
            "subscription_end_date": current_teacher.subscription_end_date.isoformat(),
            "auto_renew": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="取消訂閱失敗")


@router.post("/subscription/resume")
async def resume_subscription(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    重新啟用自動續訂
    - 恢復自動扣款
    - 下次到期時會自動續訂
    """
    try:
        # 檢查是否有訂閱
        if not current_teacher.subscription_end_date:
            raise HTTPException(status_code=400, detail="您目前沒有訂閱，請先購買方案")

        # 檢查是否已啟用
        if current_teacher.subscription_auto_renew:
            return {
                "success": True,
                "message": "您的訂閱已設定為自動續訂",
                "auto_renew": True,
            }

        # 重新啟用自動續訂
        current_teacher.subscription_auto_renew = True
        current_teacher.subscription_cancelled_at = None
        db.commit()

        logger.info(f"Teacher {current_teacher.id} resumed auto-renew")

        return {
            "success": True,
            "message": "已啟用自動續訂，到期時將自動扣款",
            "auto_renew": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="啟用自動續訂失敗")


@router.get("/subscription/status")
async def get_subscription_status(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    查詢訂閱狀態
    - 到期日
    - 是否自動續訂
    - 取消時間
    """
    return {
        "subscription_end_date": (
            current_teacher.subscription_end_date.isoformat()
            if current_teacher.subscription_end_date
            else None
        ),
        "auto_renew": current_teacher.subscription_auto_renew,
        "cancelled_at": (
            current_teacher.subscription_cancelled_at.isoformat()
            if current_teacher.subscription_cancelled_at
            else None
        ),
        "is_active": (
            (
                current_teacher.subscription_end_date.replace(tzinfo=timezone.utc)
                if current_teacher.subscription_end_date.tzinfo is None
                else current_teacher.subscription_end_date
            )
            > datetime.now(timezone.utc)
            if current_teacher.subscription_end_date
            else False
        ),
    }


# ==================== 💳 卡片管理 API ====================


@router.get("/api/payment/saved-card")
async def get_saved_card(
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    查詢用戶儲存的信用卡資訊（只返回顯示用資訊，不返回 token）
    """
    if not current_teacher.card_key:
        return {"has_card": False, "card": None}

    # 卡別名稱映射
    card_type_names = {
        1: "VISA",
        2: "MasterCard",
        3: "JCB",
        4: "Union Pay",
        5: "American Express",
    }

    return {
        "has_card": True,
        "card": {
            "last_four": current_teacher.card_last_four,
            "card_type": card_type_names.get(current_teacher.card_type, "Unknown"),
            "card_type_code": current_teacher.card_type,
            "issuer": current_teacher.card_issuer,
            "saved_at": current_teacher.card_saved_at.isoformat()
            if current_teacher.card_saved_at
            else None,
        },
    }


@router.delete("/api/payment/saved-card")
async def delete_saved_card(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    刪除儲存的信用卡資訊

    注意：刪除卡片後，自動續訂將無法執行
    """
    if not current_teacher.card_key:
        raise HTTPException(status_code=404, detail="沒有儲存的信用卡")

    # 記錄刪除前的卡片資訊（用於 log）
    deleted_card_info = (
        f"****{current_teacher.card_last_four} ({current_teacher.card_issuer})"
    )

    # 刪除所有卡片相關欄位
    current_teacher.card_key = None
    current_teacher.card_token = None
    current_teacher.card_last_four = None
    current_teacher.card_bin_code = None
    current_teacher.card_type = None
    current_teacher.card_funding = None
    current_teacher.card_issuer = None
    current_teacher.card_country = None
    current_teacher.card_saved_at = None

    db.commit()

    logger.info(f"Card deleted for {current_teacher.email}: {deleted_card_info}")

    return {"success": True, "message": "信用卡資訊已刪除"}


class UpdateCardRequest(BaseModel):
    """更新信用卡請求（需要進行 1 元授權驗證）"""

    prime: str  # TapPay prime token
    cardholder: Optional[Dict[str, Any]] = None


@router.post("/api/payment/update-card")
async def update_saved_card(
    request: UpdateCardRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    更新儲存的信用卡（透過 1 元授權測試）

    流程：
    1. 使用新卡片進行 1 元授權（不請款）
    2. 授權成功後儲存新的 card_key 和 card_token
    3. 取消授權（不實際扣款）
    """
    tappay_service = TapPayService()

    # 生成訂單編號
    order_number = f"CARD_UPDATE_{current_teacher.id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    try:
        # 🔐 進行 1 元授權測試（暫不請款）
        logger.info(f"Testing new card for {current_teacher.email}")

        gateway_response = tappay_service.process_payment(
            prime=request.prime,
            amount=1,  # 1 元授權測試
            details={"item_name": "Card Verification"},
            cardholder=request.cardholder
            or {"name": current_teacher.name, "email": current_teacher.email},
            order_number=order_number,
            remember=True,  # 記住卡片
        )

        # 檢查授權是否成功
        if gateway_response.get("status") != 0:
            error_msg = TapPayService.parse_error_code(
                gateway_response.get("status"), gateway_response.get("msg")
            )
            logger.error(f"Card verification failed: {error_msg}")
            raise HTTPException(status_code=400, detail=f"信用卡驗證失敗：{error_msg}")

        # ✅ 授權成功，儲存新卡片資訊
        if gateway_response.get("card_secret"):
            card_secret = gateway_response["card_secret"]
            card_info = gateway_response.get("card_info", {})

            # 更新卡片資訊
            current_teacher.card_key = card_secret.get("card_key")
            current_teacher.card_token = card_secret.get("card_token")
            current_teacher.card_last_four = card_info.get("last_four")
            current_teacher.card_bin_code = card_info.get("bin_code")
            current_teacher.card_type = card_info.get("type")
            current_teacher.card_funding = card_info.get("funding")
            current_teacher.card_issuer = card_info.get("issuer")
            current_teacher.card_country = card_info.get("country")
            current_teacher.card_saved_at = datetime.now(timezone.utc)

            db.commit()

            logger.info(
                f"Card updated for {current_teacher.email}: "
                f"****{current_teacher.card_last_four} ({current_teacher.card_issuer})"
            )

            # 🔄 取消 1 元授權（不實際扣款）
            rec_trade_id = gateway_response.get("rec_trade_id")
            if rec_trade_id:
                try:
                    # 使用 refund API 取消授權
                    refund_response = tappay_service.refund(rec_trade_id, amount=1)
                    if refund_response.get("status") == 0:
                        logger.info(f"1 元授權已取消: {rec_trade_id}")
                    else:
                        logger.warning(f"取消 1 元授權失敗，但卡片已更新: {rec_trade_id}")
                except Exception as e:
                    logger.error(f"取消 1 元授權時發生錯誤: {e}")

            return {
                "success": True,
                "message": "信用卡已更新",
                "card": {
                    "last_four": current_teacher.card_last_four,
                    "issuer": current_teacher.card_issuer,
                    "card_type": current_teacher.card_type,
                },
            }
        else:
            raise HTTPException(status_code=500, detail="無法取得卡片資訊")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update card error: {e}")
        raise HTTPException(status_code=500, detail=f"更新信用卡失敗：{str(e)}")
