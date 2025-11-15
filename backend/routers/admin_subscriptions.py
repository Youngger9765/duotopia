"""
Admin Subscription Management API

純粹基於 subscription_periods 表的訂閱管理系統
不依賴 teacher_subscription_transactions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
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
        # Admin 操作記錄
        admin_id=admin.id,
        admin_reason=request.reason,
        # 初始化 admin_metadata 並記錄創建操作
        admin_metadata={
            "operations": [
                {
                    "action": "create",
                    "timestamp": now.isoformat(),
                    "admin_id": admin.id,
                    "admin_email": admin.email,
                    "admin_name": admin.name,
                    "reason": request.reason,
                    "changes": {
                        "plan_name": request.plan_name,
                        "quota_total": quota_total,
                        "end_date": end_date.isoformat(),
                        "status": "active",
                    },
                }
            ]
        },
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

    # 查詢當前 active 訂閱（只找 active，不找 expired）
    current_period = (
        db.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.teacher_id == teacher.id,
            SubscriptionPeriod.status == "active",
        )
        .order_by(SubscriptionPeriod.end_date.desc())
        .first()
    )

    # 如果沒有 active 訂閱，返回錯誤（應該使用 /create API）
    if not current_period:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found. Use /create to create a new subscription.",
        )

    # 🔐 標記為 admin 操作
    current_period.payment_method = "admin_edit"
    current_period.admin_id = admin.id
    current_period.admin_reason = request.reason

    # 記錄修改前的值（用於 admin_metadata）
    changes = {}

    # 更新 plan_name (如果提供)
    if request.plan_name and request.plan_name != current_period.plan_name:
        changes["plan_name"] = {
            "from": current_period.plan_name,
            "to": request.plan_name,
        }
        current_period.plan_name = request.plan_name

        # VIP 方案：必須提供自訂 quota，否則保持原值
        if request.plan_name == "VIP":
            if request.quota_total and request.quota_total > 0:
                current_period.quota_total = request.quota_total
        else:
            # 其他方案：使用預設 quota
            new_quota = get_plan_quota(request.plan_name)
            if new_quota != current_period.quota_total:
                changes["quota_total"] = {
                    "from": current_period.quota_total,
                    "to": new_quota,
                }
            current_period.quota_total = new_quota

    # 更新 quota_total (如果提供，會覆蓋 plan 的預設值)
    if request.quota_total is not None and request.quota_total > 0:
        if request.quota_total != current_period.quota_total:
            changes["quota_total"] = {
                "from": current_period.quota_total,
                "to": request.quota_total,
            }
        current_period.quota_total = request.quota_total

    # 更新 end_date (如果提供)
    if request.end_date:
        new_end_date = parse_end_date(request.end_date)
        if new_end_date != current_period.end_date:
            changes["end_date"] = {
                "from": current_period.end_date.isoformat()
                if current_period.end_date
                else None,
                "to": new_end_date.isoformat(),
            }
        current_period.end_date = new_end_date

    # 記錄修改歷史到 admin_metadata
    now = datetime.now(timezone.utc)
    if changes:  # 只有真的有修改才記錄
        # 初始化或讀取現有的 metadata
        if current_period.admin_metadata is None:
            current_period.admin_metadata = {"operations": []}
        elif not isinstance(current_period.admin_metadata, dict):
            current_period.admin_metadata = {"operations": []}
        elif "operations" not in current_period.admin_metadata:
            current_period.admin_metadata["operations"] = []

        # 新增操作記錄
        operation = {
            "timestamp": now.isoformat(),
            "admin_id": admin.id,
            "admin_email": admin.email,
            "admin_name": admin.name,
            "action": "edit",
            "changes": changes,
            "reason": request.reason,
        }
        current_period.admin_metadata["operations"].append(operation)

        # 🔑 重要：標記 JSONB 欄位已修改（SQLAlchemy 不會自動偵測 dict 內部變更）
        flag_modified(current_period, "admin_metadata")

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
    old_status = current_period.status
    current_period.status = "cancelled"

    # 記錄取消操作到 admin_metadata
    if not current_period.admin_metadata:
        current_period.admin_metadata = {"operations": []}
    if "operations" not in current_period.admin_metadata:
        current_period.admin_metadata["operations"] = []

    operation = {
        "action": "cancel",
        "timestamp": datetime.utcnow().isoformat(),
        "admin_id": admin.id,
        "admin_email": admin.email,
        "admin_name": admin.name,
        "reason": request.reason,
        "changes": {"status": {"from": old_status, "to": "cancelled"}},
    }

    current_period.admin_metadata["operations"].append(operation)

    # 🔑 重要：標記 JSONB 欄位已修改
    flag_modified(current_period, "admin_metadata")

    db.commit()

    return {
        "success": True,
        "message": "Subscription cancelled",
        "teacher_email": teacher.email,
        "status": "cancelled",
    }


@router.get("/all-teachers")
async def get_all_teachers_subscriptions(
    db: Session = Depends(get_db),
    admin: Teacher = Depends(get_current_admin),
):
    """
    第1層：獲取所有教師及其當前訂閱狀態
    """
    # 子查詢：找出每個教師最新的 active 訂閱
    subq = (
        db.query(
            SubscriptionPeriod.teacher_id,
            func.max(SubscriptionPeriod.id).label("latest_period_id"),
        )
        .filter(SubscriptionPeriod.status == "active")
        .group_by(SubscriptionPeriod.teacher_id)
        .subquery()
    )

    # 主查詢
    teachers_with_subs = (
        db.query(Teacher, SubscriptionPeriod)
        .outerjoin(subq, Teacher.id == subq.c.teacher_id)
        .outerjoin(SubscriptionPeriod, SubscriptionPeriod.id == subq.c.latest_period_id)
        .order_by(Teacher.id.desc())
        .all()
    )

    result = []
    for teacher, period in teachers_with_subs:
        teacher_data = {
            "teacher_id": teacher.id,
            "teacher_name": teacher.name,
            "teacher_email": teacher.email,
            "current_subscription": None,
        }

        if period:
            teacher_data["current_subscription"] = {
                "period_id": period.id,
                "plan_name": period.plan_name,
                "quota_total": period.quota_total,
                "quota_used": period.quota_used,
                "status": period.status,
                "end_date": period.end_date.isoformat() if period.end_date else None,
            }

        result.append(teacher_data)

    return {"teachers": result, "total": len(result)}


@router.get("/teacher/{teacher_id}/periods")
async def get_teacher_periods(
    teacher_id: int,
    db: Session = Depends(get_db),
    admin: Teacher = Depends(get_current_admin),
):
    """
    第2層：獲取指定教師的所有訂閱歷史記錄
    """
    # 查詢教師資訊
    teacher = db.query(Teacher).filter_by(id=teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 查詢該教師的所有訂閱記錄
    AdminTeacher = aliased(Teacher)
    periods = (
        db.query(SubscriptionPeriod, AdminTeacher)
        .outerjoin(AdminTeacher, SubscriptionPeriod.admin_id == AdminTeacher.id)
        .filter(SubscriptionPeriod.teacher_id == teacher_id)
        .order_by(SubscriptionPeriod.created_at.desc())
        .all()
    )

    period_list = []
    for period, admin_teacher in periods:
        period_list.append(
            {
                "id": period.id,
                "plan_name": period.plan_name,
                "quota_total": period.quota_total,
                "quota_used": period.quota_used,
                "start_date": period.start_date.isoformat()
                if period.start_date
                else None,
                "end_date": period.end_date.isoformat() if period.end_date else None,
                "status": period.status,
                "payment_method": period.payment_method,
                "admin_name": admin_teacher.name if admin_teacher else None,
                "admin_email": admin_teacher.email if admin_teacher else None,
                "admin_reason": period.admin_reason,
                "created_at": period.created_at.isoformat(),
            }
        )

    return {
        "teacher": {
            "id": teacher.id,
            "name": teacher.name,
            "email": teacher.email,
        },
        "periods": period_list,
        "total": len(period_list),
    }


@router.get("/period/{period_id}/history")
async def get_period_edit_history(
    period_id: int,
    db: Session = Depends(get_db),
    admin: Teacher = Depends(get_current_admin),
):
    """
    第3層：獲取指定 period 的編輯歷史（從 admin_metadata）
    """
    period = db.query(SubscriptionPeriod).filter_by(id=period_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Subscription period not found")

    # 解析 admin_metadata
    edit_history = []
    if period.admin_metadata and isinstance(period.admin_metadata, dict):
        operations = period.admin_metadata.get("operations", [])
        edit_history = operations

    return {
        "period_id": period.id,
        "plan_name": period.plan_name,
        "edit_history": edit_history,
    }
