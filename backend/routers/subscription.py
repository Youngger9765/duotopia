from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import Optional
import random

from database import get_db
from models import (
    Teacher,
    Student,
    PointUsageLog,
    Classroom,
    ClassroomStudent,
    StudentAssignment,
)

router = APIRouter(prefix="/api/test", tags=["test-subscription"])


class UpdateSubscriptionRequest(BaseModel):
    action: str
    months: Optional[int] = 1
    quota_delta: Optional[int] = None  # For update_quota action
    plan: Optional[str] = None  # For change_plan action


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
async def get_subscription_status(db: Session = Depends(get_db)):
    """Get current subscription status for demo account (no auth required for testing)"""

    # Always use demo account for testing
    demo = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
    if not demo:
        raise HTTPException(status_code=404, detail="Demo account not found")

    current_teacher = demo

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

    elif request.action == "update_quota":
        # Update quota usage
        if request.quota_delta is None:
            raise HTTPException(
                status_code=400,
                detail="quota_delta is required for update_quota action",
            )

        current_period = current_teacher.current_period
        if not current_period:
            raise HTTPException(status_code=404, detail="No active subscription period")

        # Update quota_used
        current_period.quota_used = max(
            0, current_period.quota_used + request.quota_delta
        )
        message = (
            f"配額使用量已調整 {request.quota_delta:+d} 秒 (當前: {current_period.quota_used}秒)"
        )

    elif request.action == "change_plan":
        # Change subscription plan
        new_plan = request.plan
        if new_plan not in ["Tutor Teachers", "School Teachers"]:
            raise HTTPException(status_code=400, detail="Invalid plan name")

        # Update teacher subscription type
        current_teacher.subscription_type = new_plan

        # Update current period's quota_total
        current_period = current_teacher.current_period
        if current_period:
            new_quota = 25000 if new_plan == "School Teachers" else 10000
            current_period.quota_total = new_quota
            current_period.plan_name = new_plan
            message = f"已切換方案至 {new_plan}，配額已更新為 {new_quota} 點"
        else:
            message = f"已切換方案至 {new_plan}（無有效訂閱週期）"

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

    db.commit()
    db.refresh(current_teacher)

    # Calculate is_active
    is_active = False
    if current_teacher.subscription_end_date:
        is_active = current_teacher.subscription_end_date > now

    # Get quota used
    current_period = current_teacher.current_period
    quota_used = current_period.quota_used if current_period else 0

    return {
        "message": message,
        "status": SubscriptionStatusResponse(
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
            else now.isoformat(),
            quota_used=quota_used,
        ),
    }


@router.post("/subscription/create-demo-usage-data")
async def create_demo_usage_data(db: Session = Depends(get_db)):
    """為 demo 帳號建立學生使用作業的假資料（用於展示圖表）"""
    # 獲取 demo 老師帳號
    demo = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
    if not demo:
        raise HTTPException(status_code=404, detail="Demo account not found")

    # 獲取當前訂閱週期
    current_period = demo.current_period
    if not current_period:
        raise HTTPException(status_code=404, detail="No active subscription period")

    # 清除現有假資料
    db.query(PointUsageLog).filter(
        PointUsageLog.teacher_id == demo.id,
        PointUsageLog.subscription_period_id == current_period.id,
    ).delete()

    # 獲取 demo 老師的學生
    students = (
        db.query(Student)
        .join(ClassroomStudent)
        .join(Classroom)
        .filter(Classroom.teacher_id == demo.id)
        .limit(10)
        .all()
    )

    # 獲取 demo 老師的作業
    assignments = (
        db.query(StudentAssignment)
        .join(Classroom)
        .filter(Classroom.teacher_id == demo.id)
        .limit(10)
        .all()
    )

    if not students:
        return {"message": "請先建立學生資料"}
    if not assignments:
        return {"message": "請先建立作業"}

    # 建立過去 30 天的假資料
    now = datetime.now(timezone.utc)
    feature_types = [
        "speech_recording",
        "speech_assessment",
        "text_correction",
        "image_correction",
    ]
    total_created = 0
    total_seconds = 0

    for days_ago in range(30):
        daily_logs = random.randint(1, 5)

        for _ in range(daily_logs):
            student = random.choice(students)
            assignment = random.choice(assignments)
            feature_type = random.choice(feature_types)

            # 根據功能類型決定消耗
            if "speech" in feature_type:
                seconds = random.randint(5, 30)
                points_used = seconds
                unit_count = seconds
                unit_type = "秒"
            elif "text" in feature_type:
                points_used = random.randint(5, 20)
                unit_count = random.randint(50, 200)
                unit_type = "字"
                seconds = points_used
            else:
                points_used = random.randint(5, 15)
                unit_count = 1
                unit_type = "張"
                seconds = points_used

            total_seconds += seconds

            log = PointUsageLog(
                subscription_period_id=current_period.id,
                teacher_id=demo.id,
                student_id=student.id,
                assignment_id=assignment.id,
                feature_type=feature_type,
                feature_detail={"duration": seconds}
                if "speech" in feature_type
                else {},
                points_used=points_used,
                quota_before=current_period.quota_total,
                quota_after=current_period.quota_total - total_seconds,
                unit_count=unit_count,
                unit_type=unit_type,
                created_at=now - timedelta(days=days_ago, hours=random.randint(0, 23)),
            )
            db.add(log)
            total_created += 1

    # 更新當前週期的已使用配額
    current_period.quota_used = min(total_seconds, current_period.quota_total)
    db.commit()

    return {
        "message": f"成功建立 {total_created} 筆學生使用記錄",
        "total_logs": total_created,
        "quota_used": current_period.quota_used,
        "quota_total": current_period.quota_total,
    }
