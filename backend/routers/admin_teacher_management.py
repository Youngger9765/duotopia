"""
Admin - Teacher Management API

管理員後台：教師帳號管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import logging

from database import get_db
from models import Teacher
from services.email_service import email_service

router = APIRouter(prefix="/api/admin/teacher-management", tags=["admin-teacher-management"])
logger = logging.getLogger(__name__)

# Admin Secret（用於簡單的管理員認證）
ADMIN_SECRET = "duotopia-admin-secret-2025"  # TODO: 移到環境變數


def verify_admin(x_admin_secret: str = Header(None)):
    """驗證管理員權限"""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin secret")
    return True


# ============ Request/Response Models ============

class TeacherQueryResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str]
    email_verified: bool
    is_active: bool
    created_at: datetime
    email_verified_at: Optional[datetime]
    subscription_end_date: Optional[datetime]
    subscription_status: str
    days_remaining: Optional[int]
    email_verification_token: Optional[str]
    email_verification_sent_at: Optional[datetime]


class AdjustSubscriptionRequest(BaseModel):
    email: EmailStr
    days: int  # 正數增加，負數減少


# ============ API Endpoints ============

@router.get("/query")
async def query_teacher_by_email(
    email: str,
    db: Session = Depends(get_db),
    _admin: bool = Depends(verify_admin)
):
    """
    根據 Email 查詢教師帳號狀態

    需要 Header: X-Admin-Secret
    """
    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        raise HTTPException(status_code=404, detail=f"找不到教師帳號: {email}")

    return {
        "id": teacher.id,
        "email": teacher.email,
        "name": teacher.name,
        "phone": teacher.phone,
        "email_verified": teacher.email_verified,
        "is_active": teacher.is_active,
        "created_at": teacher.created_at,
        "email_verified_at": teacher.email_verified_at,
        "subscription_end_date": teacher.subscription_end_date,
        "subscription_status": teacher.subscription_status,
        "days_remaining": teacher.days_remaining,
        "email_verification_token": teacher.email_verification_token,
        "email_verification_sent_at": teacher.email_verification_sent_at,
    }


@router.post("/activate")
async def activate_teacher(
    email: EmailStr,
    db: Session = Depends(get_db),
    _admin: bool = Depends(verify_admin)
):
    """
    直接開通教師帳號（跳過 Email 驗證）

    - 設定 email_verified = True
    - 設定 is_active = True
    - 給予 30 天訂閱
    - 清除驗證 token

    需要 Header: X-Admin-Secret
    """
    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        raise HTTPException(status_code=404, detail=f"找不到教師帳號: {email}")

    # 直接啟用帳號
    teacher.email_verified = True
    teacher.is_active = True
    teacher.email_verified_at = datetime.utcnow()
    teacher.email_verification_token = None

    # 如果沒有訂閱，給予 30 天
    if not teacher.subscription_end_date or teacher.subscription_end_date < datetime.utcnow():
        teacher.subscription_end_date = datetime.utcnow() + timedelta(days=30)

    db.commit()
    db.refresh(teacher)

    logger.info(f"Admin activated teacher: {email}")

    return {
        "message": f"已開通教師帳號: {email}",
        "teacher": {
            "id": teacher.id,
            "email": teacher.email,
            "name": teacher.name,
            "email_verified": teacher.email_verified,
            "is_active": teacher.is_active,
            "subscription_end_date": teacher.subscription_end_date,
            "days_remaining": teacher.days_remaining,
        }
    }


@router.post("/resend-verification")
async def resend_verification_email(
    email: EmailStr,
    db: Session = Depends(get_db),
    _admin: bool = Depends(verify_admin)
):
    """
    重新發送驗證信

    需要 Header: X-Admin-Secret
    """
    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        raise HTTPException(status_code=404, detail=f"找不到教師帳號: {email}")

    if teacher.email_verified:
        raise HTTPException(status_code=400, detail="帳號已經驗證過，無需重新發送")

    # 使用 email service 發送驗證信
    success = email_service.send_teacher_verification_email(db, teacher)

    if not success:
        raise HTTPException(status_code=500, detail="發送驗證信失敗")

    logger.info(f"Admin resent verification email to: {email}")

    return {
        "message": f"已重新發送驗證信到: {email}",
        "email": teacher.email,
        "token": teacher.email_verification_token,
        "verification_url": f"https://duotopia.co/teacher/verify-email?token={teacher.email_verification_token}"
    }


@router.post("/adjust-subscription")
async def adjust_subscription(
    request: AdjustSubscriptionRequest,
    db: Session = Depends(get_db),
    _admin: bool = Depends(verify_admin)
):
    """
    調整教師訂閱天數

    - days > 0: 增加天數
    - days < 0: 減少天數

    需要 Header: X-Admin-Secret
    """
    teacher = db.query(Teacher).filter(Teacher.email == request.email).first()

    if not teacher:
        raise HTTPException(status_code=404, detail=f"找不到教師帳號: {request.email}")

    # 計算新的到期日
    if teacher.subscription_end_date and teacher.subscription_end_date > datetime.utcnow():
        # 如果有有效訂閱，在此基礎上調整
        new_end_date = teacher.subscription_end_date + timedelta(days=request.days)
    else:
        # 如果沒有訂閱或已過期，從現在開始計算
        new_end_date = datetime.utcnow() + timedelta(days=request.days)

    old_end_date = teacher.subscription_end_date
    teacher.subscription_end_date = new_end_date

    db.commit()
    db.refresh(teacher)

    logger.info(f"Admin adjusted subscription for {request.email}: {request.days} days")

    return {
        "message": f"已調整訂閱天數: {request.days} 天",
        "teacher": {
            "email": teacher.email,
            "name": teacher.name,
            "old_subscription_end": old_end_date,
            "new_subscription_end": teacher.subscription_end_date,
            "days_remaining": teacher.days_remaining,
        }
    }


@router.post("/deactivate")
async def deactivate_teacher(
    email: EmailStr,
    db: Session = Depends(get_db),
    _admin: bool = Depends(verify_admin)
):
    """
    停用教師帳號

    需要 Header: X-Admin-Secret
    """
    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        raise HTTPException(status_code=404, detail=f"找不到教師帳號: {email}")

    teacher.is_active = False
    db.commit()

    logger.info(f"Admin deactivated teacher: {email}")

    return {
        "message": f"已停用教師帳號: {email}",
        "email": teacher.email,
        "is_active": teacher.is_active,
    }
