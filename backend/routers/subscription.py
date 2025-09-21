from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from database import get_db
from models import Teacher
from auth import verify_token
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/subscription", tags=["subscription"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


def get_current_teacher(token: str, db: Session) -> Teacher:
    """獲取當前教師"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user_type = payload.get("type")

    if not user_id or user_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user type",
        )

    teacher = db.query(Teacher).filter(Teacher.id == int(user_id)).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    return teacher


@router.get("/status")
async def get_subscription_status(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """獲取當前教師的訂閱狀態"""
    teacher = get_current_teacher(token, db)

    return {
        "subscription_status": teacher.subscription_status,
        "subscription_end_date": teacher.subscription_end_date.isoformat()
        if teacher.subscription_end_date
        else None,
        "days_remaining": teacher.days_remaining,
        "can_assign_homework": teacher.can_assign_homework,
        "email_verified": teacher.email_verified,
        "is_active": teacher.is_active,
        "teacher_id": teacher.id,
        "teacher_name": teacher.name,
    }


# ========== 充值功能 ==========
class RechargeRequest(BaseModel):
    months: int = 1
    amount: Optional[int] = None  # 天數，如果不提供則計算為 months * 30


@router.post("/recharge")
async def recharge_subscription(
    request: RechargeRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """充值延長訂閱期限"""
    teacher = get_current_teacher(token, db)

    # 計算要增加的天數
    days_to_add = request.amount if request.amount else (request.months * 30)

    # 驗證充值參數
    if days_to_add <= 0 or days_to_add > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recharge amount. Must be between 1-365 days",
        )

    try:
        # 更新訂閱結束日期
        from datetime import timezone

        current_time = datetime.now(timezone.utc)
        current_end_date = teacher.subscription_end_date or current_time

        # 如果當前訂閱已過期，從今天開始計算
        if current_end_date < current_time:
            new_end_date = current_time + timedelta(days=days_to_add)
        else:
            # 否則累加到現有結束日期
            new_end_date = current_end_date + timedelta(days=days_to_add)

        teacher.subscription_end_date = new_end_date

        # 如果教師帳號未啟用，充值後自動啟用
        if not teacher.is_active:
            teacher.is_active = True

        db.commit()
        db.refresh(teacher)

        return {
            "message": f"Successfully recharged {days_to_add} days",
            "subscription_status": teacher.subscription_status,
            "subscription_end_date": teacher.subscription_end_date.isoformat(),
            "days_remaining": teacher.days_remaining,
            "days_added": days_to_add,
            "can_assign_homework": teacher.can_assign_homework,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recharge failed: {str(e)}",
        )


# ========== 測試用端點 ==========
class MockExpireRequest(BaseModel):
    force_expire: bool = True


@router.post("/mock-expire")
async def mock_expire_subscription(
    request: MockExpireRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """測試用：強制過期訂閱"""
    teacher = get_current_teacher(token, db)

    if request.force_expire:
        # 設置訂閱為昨天過期
        from datetime import timezone

        teacher.subscription_end_date = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
        db.refresh(teacher)

        return {
            "message": "Subscription forcefully expired for testing",
            "subscription_status": teacher.subscription_status,
            "days_remaining": teacher.days_remaining,
        }

    return {"message": "No action taken"}
