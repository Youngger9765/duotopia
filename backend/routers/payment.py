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
from utils.bigquery_logger import (
    log_payment_attempt,
    log_payment_success,
    log_payment_failure,
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

        # Get current subscription end date or start from now
        if (
            current_teacher.subscription_end_date
            and current_teacher.subscription_end_date > now
        ):
            # Extend existing subscription
            previous_end_date = current_teacher.subscription_end_date
            new_end_date = previous_end_date + timedelta(days=30 * months)
        else:
            # New subscription
            previous_end_date = None
            new_end_date = now + timedelta(days=30 * months)

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
            remember=False,
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

            # 更新交易狀態為已退款
            transaction.status = "REFUNDED"
            transaction.webhook_status = "PROCESSED"
            transaction.failure_reason = f"退款處理: {msg}"

            # 🔧 計算並調整訂閱到期日
            teacher = transaction.teacher
            if teacher.subscription_end_date:
                # 計算退款比例（如果是部分退款）
                refund_amount = data.get("refund_amount", transaction.amount)
                if refund_amount >= transaction.amount:
                    # 全額退款 - 回復訂閱天數
                    days_to_deduct = (
                        30 if transaction.subscription_type == "月方案" else 90
                    )
                    teacher.subscription_end_date -= timedelta(days=days_to_deduct)
                    logger.info(
                        f"Full refund: deducted {days_to_deduct} days from subscription"
                    )
                else:
                    # 部分退款 - 按比例調整
                    refund_ratio = refund_amount / transaction.amount
                    days_to_deduct = int(
                        (30 if transaction.subscription_type == "月方案" else 90)
                        * refund_ratio
                    )
                    teacher.subscription_end_date -= timedelta(days=days_to_deduct)
                    logger.info(
                        f"Partial refund: deducted {days_to_deduct} days from subscription"
                    )

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
