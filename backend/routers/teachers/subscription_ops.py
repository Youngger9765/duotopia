"""
Subscription Ops operations for teachers.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import Teacher, Classroom, Student, Program, Lesson, Content, ContentItem
from models import ClassroomStudent, Assignment, AssignmentContent
from models import (
    ProgramLevel,
    TeacherOrganization,
    TeacherSchool,
    Organization,
    School,
)
from .dependencies import get_current_teacher
from .validators import *
from .utils import TEST_SUBSCRIPTION_WHITELIST, parse_birthdate
from services.quota_analytics_service import QuotaAnalyticsService

router = APIRouter()


@router.get("/subscription")
async def get_teacher_subscription(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
    organization_id: Optional[str] = Query(None, description="機構工作區的 organization ID"),
):
    """取得教師訂閱資訊（用於顯示配額）

    根據工作區 context 決定顯示哪個配額：
    - 帶 organization_id → 顯示該機構的點數
    - 不帶 → 顯示教師個人配額
    """
    if organization_id:
        # 驗證教師是否為該機構成員
        membership = (
            db.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == current_teacher.id,
                TeacherOrganization.organization_id == organization_id,
                TeacherOrganization.is_active.is_(True),
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization",
            )

        # 機構工作區 → 查機構點數
        org = (
            db.query(Organization)
            .filter(
                Organization.id == organization_id,
                Organization.is_active.is_(True),
            )
            .first()
        )
        if org:
            return {
                "subscription_period": {
                    "quota_total": org.total_points,
                    "quota_used": org.used_points,
                    "plan_name": org.name,
                    "status": "active",
                    "end_date": None,
                },
                "source": "organization",
            }

    # 個人工作區 → 回傳個人配額
    current_period = current_teacher.current_period

    if not current_period:
        return {
            "subscription_period": None,
            "message": "No active subscription",
        }

    return {
        "subscription_period": {
            "quota_total": current_period.quota_total,
            "quota_used": current_period.quota_used,
            "plan_name": current_period.plan_name,
            "status": current_period.status,
            "end_date": current_period.end_date.isoformat(),
        },
        "source": "personal",
    }


@router.post("/subscription/cancel")
async def cancel_subscription(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    取消自動續訂

    - 訂閱繼續有效直到到期日
    - 到期後不會自動續訂
    - 可以隨時重新啟用自動續訂
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Cancel subscription request for teacher: {current_teacher.email}")
        logger.info(f"  subscription_end_date: {current_teacher.subscription_end_date}")
        logger.info(
            f"  subscription_auto_renew: {current_teacher.subscription_auto_renew}"
        )

        # 檢查是否有有效訂閱
        if not current_teacher.subscription_end_date:
            logger.warning(
                f"Teacher {current_teacher.email} has no subscription_end_date"
            )
            raise HTTPException(status_code=400, detail="您目前沒有有效的訂閱")

        # 處理 timezone-aware 和 naive datetime 比較
        now = datetime.now(timezone.utc)
        end_date = current_teacher.subscription_end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if end_date < now:
            logger.warning(
                f"Teacher {current_teacher.email} subscription expired: {end_date} < {now}"
            )
            raise HTTPException(status_code=400, detail="您的訂閱已過期")

        # 檢查是否已經取消過（必須明確是 False，None 代表未設定要當作 True）
        if current_teacher.subscription_auto_renew is False:
            return {
                "success": True,
                "message": "您已經取消過續訂",
                "subscription_end_date": current_teacher.subscription_end_date.isoformat(),
                "auto_renew": False,
            }

        # 如果是 None，先設定為 True（向後相容舊訂閱）
        if current_teacher.subscription_auto_renew is None:
            logger.info(
                f"Teacher {current_teacher.email} subscription_auto_renew was None, "
                "setting to True for backwards compatibility"
            )
            current_teacher.subscription_auto_renew = True

        # 更新自動續訂狀態
        current_teacher.subscription_auto_renew = False
        current_teacher.subscription_cancelled_at = datetime.now(timezone.utc)
        current_teacher.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(current_teacher)

        logger.info(
            f"Teacher {current_teacher.email} cancelled auto-renewal. "
            f"Subscription valid until {current_teacher.subscription_end_date}"
        )

        return {
            "success": True,
            "message": "已成功取消自動續訂",
            "subscription_end_date": current_teacher.subscription_end_date.isoformat(),
            "auto_renew": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail="取消訂閱失敗，請稍後再試")


@router.post("/subscription/reactivate")
async def reactivate_subscription(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    重新啟用自動續訂
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # 檢查是否有有效訂閱
        if not current_teacher.subscription_end_date:
            raise HTTPException(status_code=400, detail="您目前沒有有效的訂閱")

        # 🔴 PRD 規則：必須先綁卡才能啟用自動續訂
        if not current_teacher.card_key or not current_teacher.card_token:
            raise HTTPException(status_code=400, detail="無法啟用自動續訂：尚未綁定信用卡")

        # 檢查是否已經啟用
        if current_teacher.subscription_auto_renew:
            raise HTTPException(status_code=400, detail="自動續訂已經是啟用狀態")

        # 重新啟用自動續訂
        current_teacher.subscription_auto_renew = True
        current_teacher.subscription_cancelled_at = None
        current_teacher.updated_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(f"Teacher {current_teacher.email} reactivated auto-renewal")

        return {
            "success": True,
            "message": "已重新啟用自動續訂",
            "auto_renew": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reactivate subscription: {e}")
        raise HTTPException(status_code=500, detail="重新啟用失敗，請稍後再試")


@router.get("/quota-usage")
async def get_quota_usage_analytics(
    start_date: str = None,
    end_date: str = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    取得配額使用統計分析

    提供：
    - 配額使用摘要
    - 每日使用趨勢
    - 學生使用排行
    - 作業使用排行
    - 功能使用分佈
    """
    # 解析日期（如果提供）
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid start_date format (use ISO format)"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid end_date format (use ISO format)"
            )

    # 取得統計資料
    analytics = QuotaAnalyticsService.get_usage_summary(
        current_teacher, start_date=start_dt, end_date=end_dt
    )

    return analytics
