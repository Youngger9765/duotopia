"""Admin routes for seeding and managing the database + subscription management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

from database import get_db, get_engine, Base
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    ContentItem,
    Assignment,
    StudentAssignment,
    StudentContentProgress,
    StudentItemProgress,
    TeacherSubscriptionTransaction,
    SubscriptionPeriod,
    TransactionType,
    TransactionStatus,
)
from routers.teachers import get_current_teacher
from services.tappay_service import TapPayService
from schemas import RefundRequest
import os
import subprocess
import sys

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============ Admin 權限檢查 ============
async def get_current_admin(
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Teacher:
    """確認當前用戶是 Admin"""
    if not current_teacher.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Please contact administrator if you need access.",
        )
    return current_teacher


# ============ Request/Response Models ============
# ⚠️ DEPRECATED: ExtendSubscriptionRequest/Response removed (old extend API deleted)
class TeacherSubscriptionInfo(BaseModel):
    """教師訂閱資訊"""

    id: int
    email: str
    name: str
    plan_name: Optional[str] = None
    end_date: Optional[str] = None
    days_remaining: Optional[int] = None
    quota_used: int
    quota_total: Optional[int] = None
    quota_percentage: Optional[float] = None
    status: str  # active/expired/cancelled/none
    total_periods: int  # 總共訂閱過幾期
    created_at: str


class ExtensionHistoryRecord(BaseModel):
    """延展歷史記錄"""

    id: int
    teacher_email: str
    teacher_name: Optional[str] = None
    plan_name: str
    months: int
    amount: float
    extended_at: str
    admin_email: Optional[str] = None
    admin_name: Optional[str] = None
    reason: Optional[str] = None
    quota_granted: Optional[int] = None


@router.post("/database/rebuild")
async def rebuild_database(seed: bool = True, db: Session = Depends(get_db)):
    """重建資料庫 - 刪除所有表格並重新創建"""
    # 檢查是否在允許的環境 (development 或 staging)
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rebuild operation not allowed in production environment",
        )

    try:
        # 關閉當前 session
        db.close()

        # Drop all tables
        engine = get_engine()
        Base.metadata.drop_all(bind=engine)

        # Recreate all tables
        Base.metadata.create_all(bind=engine)

        result = {
            "success": True,
            "message": "Database rebuilt successfully",
            "tables_created": list(Base.metadata.tables.keys()),
        }

        # 如果需要 seed
        if seed:
            try:
                seed_result = subprocess.run(
                    [sys.executable, "seed_data.py"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if seed_result.returncode == 0:
                    result["seed_status"] = "success"
                    result["seed_output"] = seed_result.stdout
                else:
                    result["seed_status"] = "failed"
                    result["seed_error"] = seed_result.stderr
            except Exception as e:
                result["seed_status"] = "error"
                result["seed_error"] = str(e)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rebuild operation failed: {str(e)}",
        )


@router.post("/seed-database")
async def seed_database(db: Session = Depends(get_db)):
    """Seed the database with initial data."""
    # 檢查是否在允許的環境 (development 或 staging)
    env = os.getenv("ENVIRONMENT", "development")  # 預設為 development
    if env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seed operation not allowed in production environment",
        )

    try:
        # 執行 seed_data.py
        result = subprocess.run(
            [sys.executable, "seed_data.py"],
            capture_output=True,
            text=True,
            timeout=300,  # 5分鐘超時
        )

        if result.returncode != 0:
            return {
                "success": False,
                "message": "Seed failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        return {
            "success": True,
            "message": "Database seeded successfully",
            "output": result.stdout,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Seed operation timed out",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seed operation failed: {str(e)}",
        )


@router.get("/database/stats")
def get_database_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """獲取資料庫統計資訊"""

    stats = {
        "teacher": db.query(Teacher).count(),
        "student": db.query(Student).count(),
        "classroom": db.query(Classroom).count(),
        "classroom_student": db.query(ClassroomStudent).count(),
        "program": db.query(Program).count(),
        "lesson": db.query(Lesson).count(),
        "content": db.query(Content).count(),
        "content_item": db.query(ContentItem).count(),
        "assignment": db.query(Assignment).count(),
        "student_assignment": db.query(StudentAssignment).count(),
        "student_content_progress": db.query(StudentContentProgress).count(),
        "student_item_progress": db.query(StudentItemProgress).count(),
        "teacher_subscription_transaction": db.query(
            TeacherSubscriptionTransaction
        ).count(),
    }

    total_records = sum(stats.values())

    return {"entities": stats, "total_records": total_records}


@router.get("/database/entity/{entity_type}")
def get_entity_data(
    entity_type: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
):
    """查詢特定 entity 的資料"""

    entity_map = {
        "teacher": Teacher,
        "student": Student,
        "classroom": Classroom,
        "classroom_student": ClassroomStudent,
        "program": Program,
        "lesson": Lesson,
        "content": Content,
        "content_item": ContentItem,
        "assignment": Assignment,
        "student_assignment": StudentAssignment,
        "student_content_progress": StudentContentProgress,
        "student_item_progress": StudentItemProgress,
        "teacher_subscription_transaction": TeacherSubscriptionTransaction,
    }

    if entity_type not in entity_map:
        raise HTTPException(
            status_code=404, detail=f"Entity type '{entity_type}' not found"
        )

    model = entity_map[entity_type]

    # 獲取資料
    query = db.query(model).offset(offset).limit(limit)
    items = query.all()
    total = db.query(model).count()

    # 轉換為字典格式
    data = []
    for item in items:
        item_dict = {}
        for column in model.__table__.columns:
            value = getattr(item, column.name)
            # 處理日期時間格式
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            item_dict[column.name] = value
        data.append(item_dict)

    return {
        "data": data,
        "total": total,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
        },
    }


# ============ 訂閱管理 API ============
# ⚠️ DEPRECATED: Old admin subscription APIs removed
# Use /api/admin/subscription/* endpoints from admin_subscriptions.py instead
@router.get("/subscription/teachers")
async def list_teachers(
    search: Optional[str] = Query(None, description="搜尋 email 或 name"),
    status_filter: Optional[str] = Query(
        None, description="訂閱狀態: active/expired/all", regex="^(active|expired|all)$"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    查詢所有教師訂閱列表

    支援：
    - 搜尋 email/name
    - 過濾訂閱狀態
    - 分頁
    """
    # 基本查詢
    query = db.query(Teacher)

    # 搜尋條件
    if search:
        query = query.filter(
            or_(Teacher.email.ilike(f"%{search}%"), Teacher.name.ilike(f"%{search}%"))
        )

    # 總數
    total = query.count()

    # 分頁
    teachers = (
        query.order_by(Teacher.created_at.desc()).offset(offset).limit(limit).all()
    )

    # 組裝訂閱資訊
    result = []
    now = datetime.now(timezone.utc)

    for teacher in teachers:
        # 計算總共訂閱過幾期（只計算成功付費的，排除 admin 手動創建、取消的）
        total_periods = (
            db.query(SubscriptionPeriod)
            .filter(
                SubscriptionPeriod.teacher_id == teacher.id,
                SubscriptionPeriod.payment_method.notin_(
                    ["admin_create", "manual_extension", "admin_edit"]
                ),
                SubscriptionPeriod.status != "cancelled",
            )
            .count()
        )

        # 獲取最新的訂閱週期（不限 status，包括 active/cancelled/expired）
        current_period = (
            db.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher.id)
            .order_by(SubscriptionPeriod.end_date.desc())
            .first()
        )

        # 計算訂閱狀態
        if current_period:
            # 檢查是否已取消
            if current_period.status == "cancelled":
                subscription_status = "cancelled"
                days_remaining = 0
            else:
                # 根據 end_date 判斷是否過期
                end_date_utc = (
                    current_period.end_date.replace(tzinfo=timezone.utc)
                    if current_period.end_date.tzinfo is None
                    else current_period.end_date
                )
                days_remaining = (end_date_utc - now).days
                is_active = end_date_utc > now
                subscription_status = "active" if is_active else "expired"

            # 配額百分比
            quota_percentage = (
                (current_period.quota_used / current_period.quota_total * 100)
                if current_period.quota_total > 0
                else 0
            )
        else:
            days_remaining = None
            subscription_status = "none"
            quota_percentage = None

        # 過濾狀態
        if status_filter and status_filter != "all":
            if status_filter != subscription_status:
                continue

        result.append(
            TeacherSubscriptionInfo(
                id=teacher.id,
                email=teacher.email,
                name=teacher.name,
                plan_name=current_period.plan_name if current_period else None,
                end_date=current_period.end_date.isoformat()
                if current_period
                else None,
                days_remaining=days_remaining
                if days_remaining and days_remaining > 0
                else 0,
                quota_used=current_period.quota_used if current_period else 0,
                quota_total=current_period.quota_total if current_period else None,
                quota_percentage=quota_percentage,
                status=subscription_status,
                total_periods=total_periods,
                created_at=teacher.created_at.isoformat()
                if teacher.created_at
                else None,
            )
        )

    return {"total": total, "teachers": result, "limit": limit, "offset": offset}


@router.get("/subscription/extension-history")
async def get_extension_history(
    limit: int = Query(100, ge=1, le=500, description="返回記錄數量"),
    offset: int = Query(0, ge=0, description="分頁偏移量"),
    admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    ⚠️ DEPRECATED: 改用 /api/admin/subscription/history

    查詢 Admin 操作歷史 - 從 subscription_periods 撈資料
    """
    # 查詢所有 Admin 操作（從 subscription_periods，不再用 teacher_subscription_transactions）
    periods = (
        db.query(SubscriptionPeriod, Teacher)
        .join(Teacher, SubscriptionPeriod.teacher_id == Teacher.id)
        .filter(
            SubscriptionPeriod.payment_method.in_(
                ["admin_create", "manual_extension", "admin_edit"]
            )
        )
        .order_by(SubscriptionPeriod.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 計算總數
    total = (
        db.query(SubscriptionPeriod)
        .filter(
            SubscriptionPeriod.payment_method.in_(
                ["admin_create", "manual_extension", "admin_edit"]
            )
        )
        .count()
    )

    # 組裝回應（保持舊格式相容）
    history = []
    for period, teacher in periods:
        history.append(
            ExtensionHistoryRecord(
                id=period.id,
                teacher_email=teacher.email,
                teacher_name=teacher.name,
                plan_name=period.plan_name,
                months=0,  # 不再記錄 months
                amount=0.0,  # 不再記錄 amount
                extended_at=period.created_at.isoformat()
                if period.created_at
                else None,
                admin_email=None,  # 不再記錄 admin info
                admin_name=None,
                reason=None,  # 不再記錄 reason
                quota_granted=period.quota_total,  # 使用 quota_total
            )
        )

    return {"total": total, "history": history, "limit": limit, "offset": offset}


@router.get("/subscription/stats")
async def get_admin_stats(
    admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Admin Dashboard 統計資料

    返回：
    - 總用戶數
    - 付費用戶數
    - 本月收入
    - 配額使用率
    """
    now = datetime.now(timezone.utc)

    # 總用戶數
    total_teachers = db.query(Teacher).count()

    # 付費用戶數（有 active subscription）
    active_subscriptions = (
        db.query(SubscriptionPeriod).filter_by(status="active").count()
    )

    # 本月收入
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = (
        db.query(func.sum(TeacherSubscriptionTransaction.amount))
        .filter(
            TeacherSubscriptionTransaction.status == "SUCCESS",
            TeacherSubscriptionTransaction.processed_at >= month_start,
            TeacherSubscriptionTransaction.amount > 0,  # 排除免費延展
        )
        .scalar()
        or 0
    )

    # 配額總使用率
    quota_stats = (
        db.query(
            func.sum(SubscriptionPeriod.quota_used).label("total_used"),
            func.sum(SubscriptionPeriod.quota_total).label("total_quota"),
        )
        .filter_by(status="active")
        .first()
    )

    quota_usage_percentage = (
        (quota_stats.total_used / quota_stats.total_quota * 100)
        if quota_stats.total_quota and quota_stats.total_quota > 0
        else 0
    )

    return {
        "total_teachers": total_teachers,
        "active_subscriptions": active_subscriptions,
        "monthly_revenue": float(monthly_revenue),
        "quota_usage_percentage": round(quota_usage_percentage, 2),
        "generated_at": now.isoformat(),
    }


# ⚠️ DEPRECATED: Old cancel/edit subscription APIs removed
# Use /api/admin/subscription/cancel and /api/admin/subscription/edit from admin_subscriptions.py instead


# ============ Admin Refund API ============
@router.post("/refund")
async def admin_refund(
    refund_request: RefundRequest,
    admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Admin 執行退款操作

    - 全額退款：不提供 amount
    - 部分退款：提供 amount
    - 退款會立即調用 TapPay API
    - 退款成功後會記錄在交易中
    - 實際的 period 和 webhook 更新由 TapPay webhook 自動處理
    """
    logger.info(
        f"Admin {admin.email} requesting refund for {refund_request.rec_trade_id}"
    )

    # 1. 查詢原始交易
    transaction = (
        db.query(TeacherSubscriptionTransaction)
        .filter_by(external_transaction_id=refund_request.rec_trade_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"找不到交易編號 {refund_request.rec_trade_id}",
        )

    # 2. 檢查是否已退款
    if transaction.refund_status == "completed":
        raise HTTPException(
            status_code=400,
            detail=f"交易 {refund_request.rec_trade_id} 已退款，無法重複退款",
        )

    # 3. 調用 TapPay 退款 API
    tappay_service = TapPayService()
    refund_result = tappay_service.refund(
        rec_trade_id=refund_request.rec_trade_id,
        amount=refund_request.amount,  # None = 全額退款
    )

    # 4. 檢查 TapPay 退款結果
    if refund_result.get("status") != 0:
        error_msg = refund_result.get("msg", "Unknown error")
        logger.error(f"TapPay refund failed: {error_msg}")
        raise HTTPException(
            status_code=400,
            detail=f"退款失敗：{error_msg}",
        )

    # 5. 更新交易狀態（TapPay 退款 API 是同步的，成功即完成）
    transaction.refund_status = "completed"  # 同步完成，不需等 webhook
    transaction.refund_amount = refund_request.amount or int(transaction.amount)
    transaction.refund_reason = refund_request.reason
    transaction.refund_notes = refund_request.notes
    transaction.refund_initiated_by = admin.id
    transaction.refund_initiated_at = datetime.now(timezone.utc)

    # 5.5 創建 REFUND transaction 記錄
    # ⚠️ 用 try-except 保護，即使失敗也要 commit 原始 transaction 更新
    try:
        refund_transaction = TeacherSubscriptionTransaction(
            teacher_id=transaction.teacher_id,
            teacher_email=transaction.teacher_email,
            transaction_type=TransactionType.REFUND,
            subscription_type=transaction.subscription_type,
            amount=-abs(refund_request.amount or int(transaction.amount)),  # 負數表示退款
            currency=transaction.currency or "TWD",
            status=TransactionStatus.SUCCESS,
            months=transaction.months or 0,  # 複製原交易的月數
            period_start=transaction.period_start,  # 複製原交易的時間
            period_end=transaction.period_end,
            previous_end_date=transaction.previous_end_date,
            new_end_date=transaction.new_end_date or datetime.now(timezone.utc),  # 必填欄位
            payment_provider="tappay",
            payment_method=transaction.payment_method,
            external_transaction_id=refund_result.get(
                "refund_id"
            ),  # 退款交易編號（TapPay 返回 refund_id）
            original_transaction_id=transaction.id,  # 關聯原始交易
            refund_reason=refund_request.reason,
            refund_notes=refund_request.notes,
            refund_initiated_by=admin.id,
            refund_initiated_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
        )
        db.add(refund_transaction)
        db.flush()  # 先 flush 取得 ID

        logger.info(
            f"✅ Created REFUND transaction {refund_transaction.id} for original transaction {transaction.id}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to create REFUND transaction for {transaction.id}: {e}")
        logger.error(
            "⚠️  TapPay refund succeeded but REFUND transaction creation failed! "
            "Manual intervention may be required."
        )

    # 6. 同步更新對應的 SubscriptionPeriod（如果存在）
    period = (
        db.query(SubscriptionPeriod)
        .filter_by(payment_id=refund_request.rec_trade_id)
        .first()
    )

    if period:
        period.payment_status = "refunded"
        period.status = "cancelled"
        period.cancel_reason = f"Admin refund: {refund_request.reason}"
        period.cancelled_at = datetime.now(timezone.utc)
        period.admin_id = admin.id

        # 記錄退款到 metadata
        if period.admin_metadata is None:
            period.admin_metadata = {}
        period.admin_metadata["refund"] = {
            "amount": refund_request.amount or int(transaction.amount),
            "reason": refund_request.reason,
            "refunded_by": admin.email,
            "refunded_at": datetime.now(timezone.utc).isoformat(),
            "refund_id": refund_result.get("refund_id"),  # TapPay 退款交易編號
        }

        logger.info(
            f"Period {period.id} marked as refunded and cancelled for teacher {transaction.teacher_email}"
        )

    db.commit()

    logger.info(
        f"Refund completed for {refund_request.rec_trade_id}, "
        f"amount: {refund_request.amount or 'full'}, "
        f"reason: {refund_request.reason}"
    )

    return {
        "status": "success",
        "message": "退款已完成",
        "rec_trade_id": refund_request.rec_trade_id,
        "refund_rec_trade_id": refund_result.get("refund_rec_trade_id"),
        "amount": refund_request.amount or transaction.amount,
        "period_updated": period is not None,
    }
