"""
Admin Subscription Management API

純粹基於 subscription_periods 表的訂閱管理系統
不依賴 teacher_subscription_transactions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from typing import Optional

from database import get_db
from models import Teacher, SubscriptionPeriod
from routers.admin import get_current_admin

router = APIRouter(prefix="/api/admin/subscription", tags=["admin-subscription"])


# ============ Request/Response Models ============
class CreateSubscriptionRequest(BaseModel):
    """創建訂閱請求"""

    teacher_email: EmailStr
    plan_name: str  # "30-Day Trial" | "Tutor Teachers" | "School Teachers" | "Demo Unlimited Plan" | "VIP"
    end_date: str  # YYYY-MM-DD (月底日期)
    quota_total: Optional[int] = None  # VIP 方案可自訂 quota
    reason: str


class EditSubscriptionRequest(BaseModel):
    """編輯訂閱請求"""

    teacher_email: EmailStr
    plan_name: Optional[str] = None
    quota_total: Optional[int] = None
    end_date: Optional[str] = None  # YYYY-MM-DD
    reason: str


class CancelSubscriptionRequest(BaseModel):
    """取消訂閱請求"""

    teacher_email: EmailStr
    reason: str


class SubscriptionResponse(BaseModel):
    """訂閱操作回應"""

    teacher_email: str
    plan_name: str
    quota_total: int
    quota_used: int
    end_date: str
    status: str


# ============ Helper Functions ============
def get_plan_quota(plan_name: str) -> int:
    """根據方案名稱獲取對應的 quota"""
    plan_quotas = {
        "30-Day Trial": 4000,
        "Tutor Teachers": 10000,
        "School Teachers": 25000,
        "Demo Unlimited Plan": 999999,
        "VIP": 0,  # VIP 方案的 quota 由 Admin 自訂
    }
    return plan_quotas.get(plan_name, 0)


def parse_end_date(date_str: str) -> datetime:
    """
    解析日期字串並設定為當天結束時間 (23:59:59)

    Args:
        date_str: YYYY-MM-DD format

    Returns:
        datetime object at end of day (23:59:59.999999)
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return datetime(
        date_obj.year,
        date_obj.month,
        date_obj.day,
        23,
        59,
        59,
        999999,
    )


# ============ API Endpoints ============
@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    db: Session = Depends(get_db),
    admin: Teacher = Depends(get_current_admin),
):
    """
    為教師創建訂閱

    - 只更新 subscription_periods 表
    - payment_method = "admin_create"
    - end_date 設定為月底 23:59:59
    """
    # 查詢教師
    teacher = db.query(Teacher).filter_by(email=request.teacher_email).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 檢查是否已有活躍訂閱
    now = datetime.now(timezone.utc)
    existing = (
        db.query(SubscriptionPeriod)
        .filter_by(teacher_id=teacher.id, status="active")
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Teacher already has an active subscription. Use /edit to modify it.",
        )

    # 計算 quota (VIP 方案可自訂)
    quota_total = get_plan_quota(request.plan_name)

    # VIP 方案：使用自訂 quota
    if request.plan_name == "VIP":
        if not request.quota_total or request.quota_total <= 0:
            raise HTTPException(
                status_code=400,
                detail="VIP plan requires custom quota_total (must be > 0)",
            )
        quota_total = request.quota_total
    # 其他方案：使用預設 quota
    elif quota_total == 0:
        raise HTTPException(status_code=400, detail="Invalid plan name")

    # 解析 end_date (設定為當天 23:59:59)
    end_date = parse_end_date(request.end_date)

    # 創建訂閱週期
    new_period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name=request.plan_name,
        amount_paid=0,  # Admin 創建，不涉及付款
        quota_total=quota_total,
        quota_used=0,
        start_date=now,
        end_date=end_date,
        payment_method="admin_create",
        payment_status="paid",
        status="active",
        created_at=now,
    )
    db.add(new_period)
    db.commit()
    db.refresh(new_period)

    return SubscriptionResponse(
        teacher_email=teacher.email,
        plan_name=new_period.plan_name,
        quota_total=new_period.quota_total,
        quota_used=new_period.quota_used,
        end_date=new_period.end_date.isoformat(),
        status=new_period.status,
    )


@router.post("/edit", response_model=SubscriptionResponse)
async def edit_subscription(
    request: EditSubscriptionRequest,
    db: Session = Depends(get_db),
    admin: Teacher = Depends(get_current_admin),
):
    """
    編輯教師的訂閱

    - 可以修改 plan_name, quota_total, end_date
    - 只更新現有的 subscription_period
    """
    # 查詢教師
    teacher = db.query(Teacher).filter_by(email=request.teacher_email).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 查詢最新的訂閱週期（允許 active 或 expired，但不包括 cancelled）
    current_period = (
        db.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.status.in_(["active", "expired"]),
        )
        .order_by(SubscriptionPeriod.end_date.desc())
        .first()
    )

    # 如果沒有訂閱，自動創建一個新的
    if not current_period:
        # 必須提供 plan_name 和 end_date
        if not request.plan_name or not request.end_date:
            raise HTTPException(
                status_code=400,
                detail="Creating new subscription requires plan_name and end_date",
            )

        # 計算 quota
        quota_total = get_plan_quota(request.plan_name)
        if request.plan_name == "VIP":
            if not request.quota_total or request.quota_total <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="VIP plan requires custom quota_total (must be > 0)",
                )
            quota_total = request.quota_total
        elif quota_total == 0:
            raise HTTPException(status_code=400, detail="Invalid plan name")

        # 創建新訂閱
        now = datetime.now(timezone.utc)
        current_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name=request.plan_name,
            amount_paid=0,
            quota_total=quota_total,
            quota_used=0,
            start_date=now,
            end_date=parse_end_date(request.end_date),
            payment_method="admin_create",
            payment_status="paid",
            status="active",
            created_at=now,
        )
        db.add(current_period)
        db.commit()
        db.refresh(current_period)

        return SubscriptionResponse(
            teacher_email=teacher.email,
            plan_name=current_period.plan_name,
            quota_total=current_period.quota_total,
            quota_used=current_period.quota_used,
            end_date=current_period.end_date.isoformat(),
            status=current_period.status,
        )

    # 如果是過期訂閱，編輯時自動重新激活
    if current_period.status == "expired":
        current_period.status = "active"

    # 🔐 標記為 admin 操作
    current_period.payment_method = "admin_edit"

    # 更新 plan_name (如果提供)
    if request.plan_name:
        current_period.plan_name = request.plan_name

        # VIP 方案：必須提供自訂 quota，否則保持原值
        if request.plan_name == "VIP":
            if request.quota_total and request.quota_total > 0:
                current_period.quota_total = request.quota_total
            # 如果沒提供 quota_total，保持現有值（可能已經是 VIP 方案）
        else:
            # 其他方案：使用預設 quota
            current_period.quota_total = get_plan_quota(request.plan_name)

    # 更新 quota_total (如果提供，會覆蓋 plan 的預設值)
    if request.quota_total is not None and request.quota_total > 0:
        current_period.quota_total = request.quota_total

    # 更新 end_date (如果提供)
    if request.end_date:
        current_period.end_date = parse_end_date(request.end_date)

    db.commit()
    db.refresh(current_period)

    return SubscriptionResponse(
        teacher_email=teacher.email,
        plan_name=current_period.plan_name,
        quota_total=current_period.quota_total,
        quota_used=current_period.quota_used,
        end_date=current_period.end_date.isoformat(),
        status=current_period.status,
    )


@router.post("/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    db: Session = Depends(get_db),
    admin: Teacher = Depends(get_current_admin),
):
    """
    取消教師的訂閱

    - 將 status 改為 "cancelled"
    """
    # 查詢教師
    teacher = db.query(Teacher).filter_by(email=request.teacher_email).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 查詢當前活躍訂閱
    current_period = (
        db.query(SubscriptionPeriod)
        .filter_by(teacher_id=teacher.id, status="active")
        .first()
    )
    if not current_period:
        raise HTTPException(status_code=404, detail="No active subscription found")

    # 取消訂閱
    current_period.status = "cancelled"
    db.commit()

    return {
        "success": True,
        "message": "Subscription cancelled",
        "teacher_email": teacher.email,
        "status": "cancelled",
    }


@router.get("/history")
async def get_operation_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: Teacher = Depends(get_current_admin),
):
    """
    獲取所有 Admin 操作歷史

    從 subscription_periods 撈取所有 payment_method 為 admin 相關的記錄
    """
    # 查詢所有 Admin 操作
    periods = (
        db.query(SubscriptionPeriod, Teacher)
        .join(Teacher, SubscriptionPeriod.teacher_id == Teacher.id)
        .filter(
            SubscriptionPeriod.payment_method.in_(
                ["admin_create", "manual_extension", "admin_edit"]
            )
        )
        .order_by(SubscriptionPeriod.created_at.desc())
        .limit(limit)
        .all()
    )

    history = []
    for period, teacher in periods:
        history.append(
            {
                "id": period.id,
                "teacher_email": teacher.email,
                "teacher_name": teacher.name,
                "plan_name": period.plan_name,
                "quota_total": period.quota_total,
                "end_date": period.end_date.isoformat() if period.end_date else None,
                "payment_method": period.payment_method,
                "created_at": period.created_at.isoformat(),
                "status": period.status,
            }
        )

    return {"history": history, "total": len(history)}
