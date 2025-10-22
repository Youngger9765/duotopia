"""
Cron Job API Endpoints

定期執行的自動化任務
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
import logging
import os

from database import get_db
from models import Teacher, TeacherSubscriptionTransaction, TransactionType
from services.subscription_calculator import SubscriptionCalculator
from services.email_service import email_service
from services.tappay_service import TapPayService

router = APIRouter(prefix="/api/cron", tags=["cron"])
logger = logging.getLogger(__name__)

# Cron Secret（用於驗證請求來源）
CRON_SECRET = os.getenv("CRON_SECRET", "dev-secret-change-me")


@router.post("/monthly-renewal")
async def monthly_renewal_cron(
    x_cron_secret: str = Header(None), db: Session = Depends(get_db)
):
    """
    每月 1 號執行的自動續訂任務

    執行時間：每月 1 號凌晨 2:00（由 Cloud Scheduler 觸發）

    功能：
    1. 找出今天到期且開啟自動續訂的用戶
    2. 自動延長訂閱到下個月 1 號
    3. 發送續訂通知 Email

    安全性：
    - 只允許帶有正確 X-Cron-Secret header 的請求
    - Cloud Scheduler 設定中需配置此 header
    """
    # 驗證 Cron Secret
    if x_cron_secret != CRON_SECRET:
        logger.warning(f"Unauthorized cron request. Secret: {x_cron_secret[:10]}...")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 使用台北時區（因為 Cloud Scheduler 設定為 Asia/Taipei）
    from zoneinfo import ZoneInfo

    taipei_tz = ZoneInfo("Asia/Taipei")
    now_taipei = datetime.now(taipei_tz)
    today_taipei = now_taipei.date()

    # 同時記錄 UTC 時間
    now_utc = datetime.now(timezone.utc)

    logger.info("🔄 Monthly renewal cron started")
    logger.info(f"   Taipei time: {now_taipei}")
    logger.info(f"   UTC time: {now_utc}")

    # 檢查是否為每月 1 號（台北時間）
    if today_taipei.day != 1:
        logger.info(
            f"Not the 1st of the month (Taipei: {today_taipei}), skipping renewal"
        )
        return {
            "status": "skipped",
            "message": f"Not the 1st of the month. Today is {today_taipei}",
            "date": today_taipei.isoformat(),
        }

    # 找出今天到期且開啟自動續訂的用戶（用台北時間的日期）
    teachers_to_renew = (
        db.query(Teacher)
        .filter(
            func.date(Teacher.subscription_end_date) == today_taipei,
            Teacher.subscription_auto_renew.is_(True),
            Teacher.is_active.is_(True),
        )
        .all()
    )

    logger.info(f"Found {len(teachers_to_renew)} teachers to renew")

    results = {
        "status": "completed",
        "date": today_taipei.isoformat(),
        "total": len(teachers_to_renew),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
    }

    # 初始化 TapPay 服務
    tappay_service = TapPayService()

    for teacher in teachers_to_renew:
        try:
            # 檢查訂閱類型
            if not teacher.subscription_type:
                logger.warning(
                    f"Teacher {teacher.email} has no subscription_type, skipping"
                )
                results["skipped"] += 1
                continue

            # 💳 檢查是否有儲存的信用卡 Token
            if not teacher.card_key or not teacher.card_token:
                logger.warning(
                    f"Teacher {teacher.email} has no saved card (auto_renew enabled but no card), "
                    f"skipping auto-charge"
                )
                results["skipped"] += 1
                results["errors"].append(
                    {
                        "teacher": teacher.email,
                        "error": "No saved card for auto-renewal",
                    }
                )
                continue

            # 計算新的到期日和應付金額
            current_end_date = teacher.subscription_end_date
            new_end_date, amount = SubscriptionCalculator.calculate_renewal(
                current_end_date, teacher.subscription_type
            )

            # 生成訂單編號
            order_number = f"RENEWAL_{teacher.id}_{today_taipei.strftime('%Y%m%d')}"

            # 💳 使用 TapPay Card Token 進行扣款
            logger.info(
                f"💳 Auto-charging {teacher.email}: TWD {amount} "
                f"(Card: ****{teacher.card_last_four})"
            )

            gateway_response = tappay_service.pay_by_token(
                card_key=teacher.card_key,
                card_token=teacher.card_token,
                amount=amount,
                details=f"{teacher.subscription_type} Monthly Renewal",
                cardholder={
                    "name": teacher.name,
                    "email": teacher.email,
                    "phone": "+886912345678",  # TODO: 未來可加入電話欄位
                },
                order_number=order_number,
            )

            # 檢查扣款是否成功
            if gateway_response.get("status") != 0:
                # 扣款失敗
                error_msg = TapPayService.parse_error_code(
                    gateway_response.get("status"), gateway_response.get("msg")
                )
                logger.error(f"❌ Auto-charge failed for {teacher.email}: {error_msg}")

                # 記錄失敗交易
                failed_transaction = TeacherSubscriptionTransaction(
                    teacher_id=teacher.id,
                    teacher_email=teacher.email,
                    transaction_type=TransactionType.RECHARGE,
                    subscription_type=teacher.subscription_type,
                    amount=amount,
                    currency="TWD",
                    status="FAILED",
                    months=1,
                    period_start=current_end_date,
                    period_end=new_end_date,
                    previous_end_date=current_end_date,
                    new_end_date=current_end_date,  # 失敗不延長
                    processed_at=now_utc,
                    payment_provider="tappay",
                    payment_method="card_token",
                    external_transaction_id=gateway_response.get("rec_trade_id"),
                    failure_reason=error_msg,
                    error_code=str(gateway_response.get("status")),
                    gateway_response=gateway_response,
                )
                db.add(failed_transaction)
                db.commit()

                results["failed"] += 1
                results["errors"].append(
                    {
                        "teacher": teacher.email,
                        "error": error_msg,
                        "status_code": gateway_response.get("status"),
                    }
                )

                # 發送扣款失敗通知（TODO: 未來實作）
                # email_service.send_renewal_failed(...)

                continue

            # ✅ 扣款成功 - 更新訂閱
            previous_end_date = teacher.subscription_end_date
            teacher.subscription_end_date = new_end_date
            teacher.subscription_renewed_at = now_utc

            # ⚠️ 重要：更新 card_token（TapPay 每次交易會刷新 token）
            if gateway_response.get("card_secret"):
                new_card_token = gateway_response["card_secret"].get("card_token")
                if new_card_token:
                    teacher.card_token = new_card_token
                    logger.info(f"Card token refreshed for {teacher.email}")

            # 建立成功交易記錄
            transaction = TeacherSubscriptionTransaction(
                teacher_id=teacher.id,
                teacher_email=teacher.email,
                transaction_type=TransactionType.RECHARGE,
                subscription_type=teacher.subscription_type,
                amount=amount,
                currency="TWD",
                status="SUCCESS",
                months=1,
                period_start=current_end_date,
                period_end=new_end_date,
                previous_end_date=previous_end_date,
                new_end_date=new_end_date,
                processed_at=now_utc,
                payment_provider="tappay",
                payment_method="card_token",
                external_transaction_id=gateway_response.get("rec_trade_id"),
                gateway_response=gateway_response,
            )
            db.add(transaction)

            # 提交變更
            db.commit()

            logger.info(
                f"✅ Auto-renewal success: {teacher.email} - "
                f"{previous_end_date.date()} -> {new_end_date.date()} "
                f"(TWD {amount} charged)"
            )

            # 發送續訂成功通知
            try:
                email_service.send_renewal_success(
                    teacher_email=teacher.email,
                    teacher_name=teacher.name,
                    new_end_date=new_end_date,
                    plan_name=teacher.subscription_type,
                )
            except Exception as e:
                logger.error(f"Failed to send renewal email to {teacher.email}: {e}")

            results["success"] += 1

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to renew {teacher.email}: {e}")
            results["failed"] += 1
            results["errors"].append({"teacher": teacher.email, "error": str(e)})

    logger.info(
        f"🔄 Monthly renewal completed: "
        f"{results['success']} success, {results['failed']} failed, "
        f"{results['skipped']} skipped"
    )

    return results


@router.post("/renewal-reminder")
async def renewal_reminder_cron(
    x_cron_secret: str = Header(None), db: Session = Depends(get_db)
):
    """
    續訂提醒 Cron Job

    執行時間：每天凌晨 3:00（由 Cloud Scheduler 觸發）

    功能：
    - 找出 7 天內到期的用戶
    - 發送續訂提醒 Email
    """
    # 驗證 Cron Secret
    if x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 使用 UTC 時間（提醒不需要嚴格時區對齊）
    now_utc = datetime.now(timezone.utc)
    seven_days_later = now_utc + timedelta(days=7)

    logger.info(f"📧 Renewal reminder cron started at {now_utc}")

    # 找出 7 天內到期的用戶（且尚未取消自動續訂）
    teachers_to_remind = (
        db.query(Teacher)
        .filter(
            Teacher.subscription_end_date <= seven_days_later,
            Teacher.subscription_end_date > now_utc,
            Teacher.subscription_auto_renew.is_(True),
            Teacher.is_active.is_(True),
        )
        .all()
    )

    logger.info(f"Found {len(teachers_to_remind)} teachers to remind")

    results = {
        "status": "completed",
        "total": len(teachers_to_remind),
        "success": 0,
        "failed": 0,
    }

    for teacher in teachers_to_remind:
        try:
            days_remaining = (teacher.subscription_end_date - now_utc).days

            # 發送提醒 Email
            email_service.send_renewal_reminder(
                teacher_email=teacher.email,
                teacher_name=teacher.name,
                end_date=teacher.subscription_end_date,
                days_remaining=days_remaining,
                plan_name=teacher.subscription_type or "訂閱方案",
            )

            results["success"] += 1
            logger.info(
                f"✅ Reminder sent to {teacher.email} ({days_remaining} days left)"
            )

        except Exception as e:
            logger.error(f"❌ Failed to send reminder to {teacher.email}: {e}")
            results["failed"] += 1

    logger.info(
        f"📧 Renewal reminder completed: "
        f"{results['success']} success, {results['failed']} failed"
    )

    return results


@router.get("/health")
async def cron_health_check():
    """
    Cron 健康檢查

    用於確認 Cron API 是否正常運作
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cron_secret_configured": bool(
            CRON_SECRET and CRON_SECRET != "dev-secret-change-me"
        ),
    }
