"""
測試訂閱 API - 用於模擬充值，不經過 TapPay
僅供開發測試使用
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
from models import Teacher
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/test/subscription", tags=["Test Subscription"])

# 測試帳號白名單
TEST_ACCOUNTS = [
    "demo@duotopia.com",
    "trial@duotopia.com",
    "expired@duotopia.com",
]


class SubscriptionStatus(BaseModel):
    status: str
    days_remaining: int
    end_date: Optional[str] = None


class UpdateRequest(BaseModel):
    action: str
    months: Optional[int] = None


class UpdateResponse(BaseModel):
    status: SubscriptionStatus
    message: str


def calculate_days_remaining(subscription_end_date: Optional[datetime]) -> int:
    """計算剩餘天數"""
    if not subscription_end_date:
        return 0

    # 確保時區一致
    now = datetime.utcnow()

    # 如果 subscription_end_date 有時區，移除時區資訊
    if subscription_end_date.tzinfo is not None:
        subscription_end_date = subscription_end_date.replace(tzinfo=None)

    if subscription_end_date <= now:
        return 0

    delta = subscription_end_date - now
    return delta.days


def get_subscription_status(teacher: Teacher) -> SubscriptionStatus:
    """取得訂閱狀態"""
    days_remaining = calculate_days_remaining(teacher.subscription_end_date)

    return SubscriptionStatus(
        status="subscribed" if days_remaining > 0 else "expired",
        days_remaining=days_remaining,
        end_date=teacher.subscription_end_date.isoformat()
        if teacher.subscription_end_date
        else None,
    )


@router.get("/status", response_model=SubscriptionStatus)
async def get_status(db: Session = Depends(get_db)):
    """
    取得當前訂閱狀態

    注意：這個端點會根據請求來源判斷使用哪個測試帳號
    預設使用 demo@duotopia.com
    """
    # 預設使用 demo 帳號
    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()

    if not teacher:
        raise HTTPException(status_code=404, detail="測試帳號不存在")

    return get_subscription_status(teacher)


@router.post("/update", response_model=UpdateResponse)
async def update_subscription(request: UpdateRequest, db: Session = Depends(get_db)):
    """
    更新訂閱狀態（測試用）

    支援的操作：
    - set_subscribed: 設定為已訂閱（30天）
    - set_expired: 設定為未訂閱
    - add_months: 增加月數
    - reset_to_new: 重置為新帳號（30天試用）
    - expire_tomorrow: 設定明天到期
    - expire_in_week: 設定一週後到期
    """
    # 預設使用 demo 帳號
    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()

    if not teacher:
        raise HTTPException(status_code=404, detail="測試帳號不存在")

    now = datetime.utcnow()
    message = ""

    if request.action == "set_subscribed":
        # 設定為已訂閱（30天）
        teacher.subscription_end_date = now + timedelta(days=30)
        message = "已設定為已訂閱狀態（30天）"

    elif request.action == "set_expired":
        # 設定為未訂閱
        teacher.subscription_end_date = now - timedelta(days=1)
        message = "已設定為未訂閱狀態"

    elif request.action == "add_months":
        # 增加月數
        months = request.months or 1
        # 確保時區一致
        end_date = teacher.subscription_end_date
        if end_date and end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)

        if not end_date or end_date <= now:
            # 如果已過期，從現在開始計算
            teacher.subscription_end_date = now + timedelta(days=30 * months)
        else:
            # 如果未過期，從到期日開始延長
            teacher.subscription_end_date = end_date + timedelta(days=30 * months)
        message = f"已增加 {months} 個月"

    elif request.action == "reset_to_new":
        # 重置為新帳號（30天試用）
        teacher.subscription_end_date = now + timedelta(days=30)
        message = "已重置為新帳號（30天試用期）"

    elif request.action == "expire_tomorrow":
        # 設定明天到期
        teacher.subscription_end_date = now + timedelta(days=1)
        message = "已設定明天到期"

    elif request.action == "expire_in_week":
        # 設定一週後到期
        teacher.subscription_end_date = now + timedelta(days=7)
        message = "已設定一週後到期"

    else:
        raise HTTPException(status_code=400, detail=f"不支援的操作: {request.action}")

    db.commit()
    db.refresh(teacher)

    return UpdateResponse(status=get_subscription_status(teacher), message=message)


@router.post("/{email}/update", response_model=UpdateResponse)
async def update_subscription_by_email(
    email: str, request: UpdateRequest, db: Session = Depends(get_db)
):
    """
    更新指定帳號的訂閱狀態（測試用）
    支援三個測試帳號：demo, trial, expired
    """
    # 檢查是否為測試帳號
    if email not in TEST_ACCOUNTS:
        raise HTTPException(
            status_code=403, detail=f"此功能僅限測試帳號使用。允許的帳號: {', '.join(TEST_ACCOUNTS)}"
        )

    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        raise HTTPException(status_code=404, detail=f"帳號不存在: {email}")

    now = datetime.utcnow()
    message = ""

    if request.action == "set_subscribed":
        teacher.subscription_end_date = now + timedelta(days=30)
        message = f"已設定 {email} 為已訂閱狀態（30天）"

    elif request.action == "set_expired":
        teacher.subscription_end_date = now - timedelta(days=1)
        message = f"已設定 {email} 為未訂閱狀態"

    elif request.action == "add_months":
        months = request.months or 1
        # 確保時區一致
        end_date = teacher.subscription_end_date
        if end_date and end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)

        if not end_date or end_date <= now:
            teacher.subscription_end_date = now + timedelta(days=30 * months)
        else:
            teacher.subscription_end_date = end_date + timedelta(days=30 * months)
        message = f"已為 {email} 增加 {months} 個月"

    elif request.action == "reset_to_new":
        teacher.subscription_end_date = now + timedelta(days=30)
        message = f"已將 {email} 重置為新帳號（30天試用期）"

    elif request.action == "expire_tomorrow":
        teacher.subscription_end_date = now + timedelta(days=1)
        message = f"已設定 {email} 明天到期"

    elif request.action == "expire_in_week":
        teacher.subscription_end_date = now + timedelta(days=7)
        message = f"已設定 {email} 一週後到期"

    else:
        raise HTTPException(status_code=400, detail=f"不支援的操作: {request.action}")

    db.commit()
    db.refresh(teacher)

    return UpdateResponse(status=get_subscription_status(teacher), message=message)


@router.get("/{email}/status", response_model=SubscriptionStatus)
async def get_status_by_email(email: str, db: Session = Depends(get_db)):
    """
    取得指定帳號的訂閱狀態
    """
    # 檢查是否為測試帳號
    if email not in TEST_ACCOUNTS:
        raise HTTPException(
            status_code=403, detail=f"此功能僅限測試帳號使用。允許的帳號: {', '.join(TEST_ACCOUNTS)}"
        )

    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        raise HTTPException(status_code=404, detail=f"帳號不存在: {email}")

    return get_subscription_status(teacher)
