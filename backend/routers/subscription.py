from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import Teacher
from routers.teachers import get_current_teacher

router = APIRouter()


class UpdateSubscriptionRequest(BaseModel):
    action: str
    months: Optional[int] = 1


class SubscriptionStatusResponse(BaseModel):
    status: str
    plan: Optional[str]  # subscription_type
    end_date: Optional[str]
    days_remaining: int
    is_active: bool
    auto_renew: bool  # 是否自動續訂
    cancelled_at: Optional[str]  # 取消續訂時間
    created_at: str
    quota_used: int = 0  # 已使用配額（秒）


@router.get("/subscription/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """Get current subscription status for authenticated teacher"""

    # Calculate is_active based on subscription_end_date
    is_active = False
    if current_teacher.subscription_end_date:
        now = datetime.now(timezone.utc)
        is_active = current_teacher.subscription_end_date > now

    # 取得配額使用量（從當前訂閱週期）
    current_period = current_teacher.current_period
    quota_used = current_period.quota_used if current_period else 0

    return SubscriptionStatusResponse(
        status=current_teacher.subscription_status or "INACTIVE",
        plan=current_teacher.subscription_type,
        end_date=current_teacher.subscription_end_date.isoformat()
        if current_teacher.subscription_end_date
        else None,
        days_remaining=current_teacher.days_remaining,
        is_active=is_active,
        auto_renew=current_teacher.subscription_auto_renew
        if current_teacher.subscription_auto_renew is not None
        else True,
        cancelled_at=current_teacher.subscription_cancelled_at.isoformat()
        if current_teacher.subscription_cancelled_at
        else None,
        created_at=current_teacher.created_at.isoformat()
        if current_teacher.created_at
        else datetime.now(timezone.utc).isoformat(),
        quota_used=quota_used,
    )


@router.post("/subscription/reset-test-accounts")
async def reset_test_accounts(db: Session = Depends(get_db)):
    """Reset demo and expired test accounts to default state"""
    now = datetime.now(timezone.utc)

    # 1. Reset Demo account (has subscription)
    demo = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
    if demo:
        demo.subscription_end_date = now + timedelta(days=30)
        demo.subscription_type = "Tutor Teachers"

    # 2. Reset Expired account (subscription expired)
    expired = db.query(Teacher).filter_by(email="expired@duotopia.com").first()
    if expired:
        expired.subscription_end_date = now - timedelta(days=1)
        expired.subscription_type = None

    db.commit()

    return {
        "message": "測試帳號已重置",
        "accounts": {
            "demo": {
                "email": "demo@duotopia.com",
                "status": "已訂閱",
                "days_remaining": 30,
            },
            "expired": {
                "email": "expired@duotopia.com",
                "status": "已過期",
                "days_remaining": 0,
            },
        },
    }


@router.post("/subscription/update")
async def update_subscription_status(
    request: UpdateSubscriptionRequest, db: Session = Depends(get_db)
):
    """Update subscription status for testing purposes"""

    # Always use demo account for testing
    demo = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
    if not demo:
        # Create demo account if it doesn't exist
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        demo = Teacher(
            email="demo@duotopia.com",
            name="Demo Teacher",
            password_hash=pwd_context.hash("demo123"),
            email_verified=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(demo)
        db.commit()
    current_teacher = demo

    now = datetime.now(timezone.utc)
    message = ""

    if request.action == "set_subscribed":
        # Set as subscribed (has days remaining)
        current_teacher.subscription_end_date = now + timedelta(days=30)
        message = "設定為已訂閱狀態（30天）"

    elif request.action == "set_expired":
        # Set as expired (no days remaining)
        current_teacher.subscription_end_date = now - timedelta(
            days=1
        )  # Expired yesterday
        message = "設定為未訂閱狀態"

    elif request.action == "add_months":
        # Add months to current subscription
        months = request.months or 1
        if (
            current_teacher.subscription_end_date
            and current_teacher.subscription_end_date > now
        ):
            # Extend existing subscription
            current_teacher.subscription_end_date += timedelta(days=30 * months)
        else:
            # Start new subscription from today
            current_teacher.subscription_end_date = now + timedelta(days=30 * months)
        message = f"已充值 {months} 個月"

    elif request.action == "reset_to_new":
        # Reset to new account with 30 days
        current_teacher.subscription_end_date = now + timedelta(days=30)
        message = "重置為新帳號（30天）"

    elif request.action == "expire_tomorrow":
        # Set to expire tomorrow
        if not current_teacher.subscription_end_date:
            current_teacher.subscription_end_date = now + timedelta(days=1)
        else:
            current_teacher.subscription_end_date = now + timedelta(days=1)
        message = "設定為明天到期"

    elif request.action == "expire_in_week":
        # Set to expire in a week
        if not current_teacher.subscription_end_date:
            current_teacher.subscription_end_date = now + timedelta(days=7)
        else:
            current_teacher.subscription_end_date = now + timedelta(days=7)
        message = "設定為一週後到期"

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

    db.commit()
    db.refresh(current_teacher)

    return {
        "message": message,
        "status": SubscriptionStatusResponse(
            status=current_teacher.subscription_status,
            end_date=current_teacher.subscription_end_date.isoformat()
            if current_teacher.subscription_end_date
            else None,
            days_remaining=current_teacher.days_remaining,
            created_at=current_teacher.created_at.isoformat()
            if current_teacher.created_at
            else now.isoformat(),
        ),
    }
