from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional, Dict, Any
import secrets
import logging
import uuid
import os

from database import get_db
from models import Teacher, TeacherSubscriptionTransaction, TransactionType
from routers.teachers import get_current_teacher
from services.tappay_service import TapPayService

logger = logging.getLogger(__name__)

router = APIRouter()


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


@router.post("/payment/process", response_model=PaymentResponse)
async def process_payment(
    request: Request,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """Process payment using TapPay"""
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

        # Process payment with TapPay
        use_mock = os.getenv("USE_MOCK_PAYMENT", "false").lower() == "true"
        logger.info(f"USE_MOCK_PAYMENT={use_mock}")

        if use_mock:
            # Mock response for development
            logger.info("Using mock payment processing")
            gateway_response = {
                "status": 0,
                "msg": "Success",
                "rec_trade_id": f"MOCK_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "bank_transaction_id": f"BNK{secrets.token_hex(6).upper()}",
                "auth_code": secrets.token_hex(3).upper(),
                "bank_result_code": "00",
                "bank_result_msg": "Success",
                "card_info": {
                    "bin_code": "424242",
                    "last_four": "4242",
                    "card_type": 1,
                    "funding": 0,
                    "issuer": "Test Bank",
                },
                "transaction_time_millis": int(now.timestamp() * 1000),
            }
        else:
            # Real TapPay API call
            logger.info(f"Processing real payment for order: {order_number}")
            tappay_service = TapPayService()

            gateway_response = tappay_service.process_payment(
                prime=payment_request.prime,
                amount=payment_request.amount,
                details=payment_request.details
                or {"item_name": payment_request.plan_name},
                cardholder=payment_request.cardholder
                or {"name": current_teacher.name, "email": current_teacher.email},
                order_number=order_number,
                remember=False,  # 暫不儲存卡片
            )

        # Check if payment was successful
        if gateway_response.get("status") != 0:
            # Payment failed
            error_msg = TapPayService.parse_error_code(
                gateway_response.get("status"), gateway_response.get("msg")
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

        logger.info(
            f"Webhook received for transaction: {rec_trade_id}, status: {status}"
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

        # Update transaction status based on webhook
        if status == 0:
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
