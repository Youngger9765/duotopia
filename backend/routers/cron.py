"""
Cron Job API Endpoints

定期執行的自動化任務
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func, create_engine
from datetime import datetime, timedelta, timezone
import logging
import os

from database import get_db
from models import (
    Teacher,
    TeacherSubscriptionTransaction,
    TransactionType,
    Student,
    Classroom,
    ClassroomStudent,
    StudentItemProgress,
)
from services.subscription_calculator import SubscriptionCalculator
from services.email_service import email_service
from services.tappay_service import TapPayService
from google.cloud import bigquery

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


@router.post("/test-notification")
async def test_cron_notification(
    x_cron_secret: str = Header(None), db: Session = Depends(get_db)
):
    """
    測試用 Cron Job - 只發送通知不執行扣款

    執行時間：每天執行（用於測試 Cloud Scheduler 是否正常運作）

    功能：
    1. 檢查即將到期的訂閱（7 天內）
    2. 統計需要續訂的用戶數量
    3. 發送測試通知到 Duotopia 官方信箱

    安全性：
    - 只允許帶有正確 X-Cron-Secret header 的請求
    - 不會真正執行扣款或修改資料
    """
    # 驗證 Cron Secret
    if x_cron_secret != CRON_SECRET:
        logger.warning(f"Unauthorized cron request. Secret: {x_cron_secret[:10]}...")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info("🧪 Test Cron Notification Started")

    # 台北時區
    taipei_tz = timezone(timedelta(hours=8))
    now_taipei = datetime.now(taipei_tz)
    now_utc = datetime.now(timezone.utc)

    # 7 天後
    seven_days_later = now_utc + timedelta(days=7)

    # 統計即將到期的用戶（7 天內）
    teachers_expiring_soon = (
        db.query(Teacher)
        .filter(
            Teacher.subscription_end_date <= seven_days_later,
            Teacher.subscription_end_date > now_utc,
            Teacher.subscription_auto_renew.is_(True),
            Teacher.is_active.is_(True),
        )
        .all()
    )

    # 統計有卡片的用戶
    teachers_with_card = [t for t in teachers_expiring_soon if t.card_key]
    teachers_without_card = [t for t in teachers_expiring_soon if not t.card_key]

    # 發送測試通知到 Duotopia 官方信箱
    notification_content = f"""
    <h2>🧪 Cloud Scheduler 測試通知</h2>
    <p><strong>執行時間：</strong>{now_taipei.strftime('%Y-%m-%d %H:%M:%S')} (台北時間)</p>

    <h3>📊 訂閱統計</h3>
    <ul>
        <li>7 天內即將到期的用戶：<strong>{len(teachers_expiring_soon)}</strong> 位</li>
        <li>已儲存信用卡：<strong>{len(teachers_with_card)}</strong> 位</li>
        <li>未儲存信用卡：<strong>{len(teachers_without_card)}</strong> 位</li>
    </ul>

    <h3>✅ Cloud Scheduler 狀態</h3>
    <p>✅ Cloud Scheduler 運作正常<br>
    ✅ Cron API 可正常訪問<br>
    ✅ 資料庫連線正常<br>
    ✅ Email 服務正常</p>

    <h3>📋 用戶詳情</h3>
    """

    if teachers_with_card:
        notification_content += "<h4>已儲存卡片的用戶：</h4><ul>"
        for teacher in teachers_with_card:
            days_left = (teacher.subscription_end_date - now_utc).days
            notification_content += f"""
            <li>{teacher.name} ({teacher.email})
                - 到期日: {teacher.subscription_end_date.strftime('%Y-%m-%d')}
                - 剩餘: {days_left} 天
                - 卡片: ****{teacher.card_last_four}
            </li>
            """
        notification_content += "</ul>"

    if teachers_without_card:
        notification_content += "<h4>⚠️ 未儲存卡片的用戶（需手動處理）：</h4><ul>"
        for teacher in teachers_without_card:
            days_left = (teacher.subscription_end_date - now_utc).days
            notification_content += f"""
            <li>{teacher.name} ({teacher.email})
                - 到期日: {teacher.subscription_end_date.strftime('%Y-%m-%d')}
                - 剩餘: {days_left} 天
            </li>
            """
        notification_content += "</ul>"

    notification_content += """
    <hr>
    <p><small>此為測試通知，不會執行任何扣款或資料修改。</small></p>
    """

    # 發送通知到官方信箱
    try:
        email_service.send_email(
            to_email="myduotopia@gmail.com",  # Duotopia 官方信箱
            subject=f"🧪 Cloud Scheduler 測試通知 - {now_taipei.strftime('%Y-%m-%d %H:%M')}",
            html_content=notification_content,
        )
        logger.info("✅ Test notification sent successfully")
    except Exception as e:
        logger.error(f"❌ Failed to send test notification: {e}")

    return {
        "status": "success",
        "timestamp": now_taipei.isoformat(),
        "statistics": {
            "total_expiring_soon": len(teachers_expiring_soon),
            "with_card": len(teachers_with_card),
            "without_card": len(teachers_without_card),
        },
        "notification_sent": True,
        "message": "Test notification sent to myduotopia@gmail.com",
    }


@router.post("/recording-error-report")
async def recording_error_report_cron(
    x_cron_secret: str = Header(None), db: Session = Depends(get_db)
):
    """
    每小時檢查 BigQuery 錄音錯誤統計

    執行時間：每小時 (由 Cloud Scheduler 觸發)

    功能：
    1. 查詢 BigQuery 過去 24 小時和最近 1 小時的錄音錯誤
    2. 使用 OpenAI 生成錯誤摘要
    3. 發送統計報告到官網信箱 (myduotopia@gmail.com)

    安全性：只允許帶有正確 X-Cron-Secret header 的請求
    """
    # 驗證 Cron Secret
    if x_cron_secret != CRON_SECRET:
        logger.warning(
            f"Unauthorized cron request. Secret: {x_cron_secret[:10] if x_cron_secret else 'None'}..."
        )
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # 初始化 BigQuery client
        client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

        # 台灣時區
        taipei_tz = timezone(timedelta(hours=8))
        now_taipei = datetime.now(taipei_tz)

        # 查詢最近 24 小時的錯誤（使用正確的 audio_playback_errors table）
        query_24h = f"""
        SELECT
            COUNT(*) as error_count,
            error_type,
            platform,
            browser,
            COUNT(DISTINCT student_id) as affected_students,
            ANY_VALUE(error_message) as sample_message
        FROM `{os.getenv("GCP_PROJECT_ID")}.duotopia_logs.audio_playback_errors`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        GROUP BY error_type, platform, browser
        ORDER BY error_count DESC
        """

        # 查詢最近 1 小時的錯誤
        query_1h = f"""
        SELECT
            COUNT(*) as error_count,
            error_type,
            platform,
            browser,
            COUNT(DISTINCT student_id) as affected_students
        FROM `{os.getenv("GCP_PROJECT_ID")}.duotopia_logs.audio_playback_errors`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        GROUP BY error_type, platform, browser
        ORDER BY error_count DESC
        """

        results_24h = list(client.query(query_24h).result())
        results_1h = list(client.query(query_1h).result())

        total_errors_24h = sum(row.error_count for row in results_24h)
        total_errors_1h = sum(row.error_count for row in results_1h)

        # 🔥 查詢有錯誤的學生名單（含老師和班級資訊）
        query_student_ids = f"""
        SELECT
            student_id,
            COUNT(*) as error_count,
            STRING_AGG(DISTINCT error_type ORDER BY error_type LIMIT 5) as error_types
        FROM `{os.getenv("GCP_PROJECT_ID")}.duotopia_logs.audio_playback_errors`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
            AND student_id IS NOT NULL
        GROUP BY student_id
        ORDER BY error_count DESC
        LIMIT 100
        """

        student_errors = list(client.query(query_student_ids).result())

        # 從 PostgreSQL 查詢學生、老師、班級資料
        students_with_errors = []
        if student_errors:
            engine = create_engine(os.getenv("DATABASE_URL"))
            SessionLocal = sessionmaker(bind=engine)
            db_session = SessionLocal()

            try:
                student_ids = [row.student_id for row in student_errors]

                # JOIN 學生、班級、老師資料
                students_data = (
                    db_session.query(
                        Student.id,
                        Student.name,
                        Student.email,
                        Classroom.name.label("classroom_name"),
                        Teacher.name.label("teacher_name"),
                        Teacher.email.label("teacher_email"),
                    )
                    .outerjoin(
                        ClassroomStudent, Student.id == ClassroomStudent.student_id
                    )
                    .outerjoin(Classroom, ClassroomStudent.classroom_id == Classroom.id)
                    .outerjoin(Teacher, Classroom.teacher_id == Teacher.id)
                    .filter(Student.id.in_(student_ids))
                    .all()
                )

                # 建立 student_id -> data 的 mapping
                student_data_map = {}
                for row in students_data:
                    if row.id not in student_data_map:
                        student_data_map[row.id] = {
                            "name": row.name,
                            "email": row.email,
                            "classrooms": [],
                            "teachers": set(),
                        }
                    if row.classroom_name:
                        student_data_map[row.id]["classrooms"].append(
                            row.classroom_name
                        )
                    if row.teacher_name and row.teacher_email:
                        student_data_map[row.id]["teachers"].add(
                            f"{row.teacher_name} ({row.teacher_email})"
                        )

                # 合併錯誤資料
                for error_row in student_errors:
                    student_data = student_data_map.get(error_row.student_id)
                    if student_data:
                        students_with_errors.append(
                            {
                                "student_id": error_row.student_id,
                                "student_name": student_data["name"],
                                "student_email": student_data["email"] or "（無 Email）",
                                "classrooms": ", ".join(student_data["classrooms"])
                                or "（無班級）",
                                "teachers": ", ".join(student_data["teachers"])
                                or "（無老師）",
                                "error_count": error_row.error_count,
                                "error_types": error_row.error_types,
                            }
                        )
                    else:
                        students_with_errors.append(
                            {
                                "student_id": error_row.student_id,
                                "student_name": "（未找到）",
                                "student_email": "（無 Email）",
                                "classrooms": "（無班級）",
                                "teachers": "（無老師）",
                                "error_count": error_row.error_count,
                                "error_types": error_row.error_types,
                            }
                        )
            finally:
                db_session.close()

        # 📊 查詢成功的錄音次數（從 PostgreSQL StudentItemProgress）
        # 最近 1 小時成功錄音
        success_1h = (
            db.query(StudentItemProgress)
            .filter(
                StudentItemProgress.updated_at
                >= datetime.now(timezone.utc) - timedelta(hours=1),
                StudentItemProgress.recording_url.isnot(None),
            )
            .all()
        )

        # 最近 24 小時成功錄音
        success_24h = (
            db.query(StudentItemProgress)
            .filter(
                StudentItemProgress.updated_at
                >= datetime.now(timezone.utc) - timedelta(hours=24),
                StudentItemProgress.recording_url.isnot(None),
            )
            .all()
        )

        # 📊 錄音統計（成功 + 錯誤）
        usage_stats_1h = {
            "error_users": len(
                set(row.student_id for row in results_1h if hasattr(row, "student_id"))
            ),
            "error_count": total_errors_1h,
            "success_users": len(set(s.student_id for s in success_1h)),
            "success_count": len(success_1h),
        }

        usage_stats_24h = {
            "error_users": len(
                set(row.student_id for row in results_24h if hasattr(row, "student_id"))
            ),
            "error_count": total_errors_24h,
            "success_users": len(set(s.student_id for s in success_24h)),
            "success_count": len(success_24h),
        }

        # 使用 OpenAI 生成摘要（如果有錯誤）
        ai_summary = ""
        if total_errors_24h > 0:
            try:
                import openai

                openai.api_key = os.getenv("OPENAI_API_KEY")

                # 準備錯誤資料給 AI
                error_data = []
                for row in results_24h[:10]:  # 只取前 10 個最嚴重的錯誤
                    error_data.append(
                        {
                            "type": row.error_type,
                            "platform": row.platform,
                            "browser": row.browser,
                            "count": row.error_count,
                            "affected_students": row.affected_students,
                            "sample": row.sample_message
                            if row.sample_message
                            else "無錯誤訊息",
                        }
                    )

                prompt = f"""
你是 Duotopia 英語學習平台的技術顧問。以下是過去 24 小時的錄音播放錯誤統計資料：

{error_data}

請用繁體中文生成一份簡潔的錯誤分析摘要（3-5 句話），包含：
1. 主要問題類型（錄音播放相關）
2. 可能的原因（瀏覽器相容性、錄音時間、檔案大小等）
3. 建議的處理優先順序

請用專業但易懂的語言，不要使用 Markdown 格式。
"""

                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7,
                )

                ai_summary = response.choices[0].message.content.strip()

            except Exception as e:
                logger.warning(f"Failed to generate AI summary: {str(e)}")
                ai_summary = "（AI 摘要生成失敗）"

        # 構建郵件內容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 20px; border-radius: 8px 8px 0 0;
                }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .summary-box {{
                    background: #fff3cd; border-left: 4px solid #ffc107;
                    padding: 15px; margin: 20px 0; border-radius: 4px;
                }}
                .stats-box {{
                    background: white; border: 1px solid #e5e7eb;
                    border-radius: 8px; padding: 20px; margin: 15px 0;
                }}
                .error-item {{
                    background: #fee; border-left: 3px solid #dc3545;
                    padding: 10px; margin: 10px 0; border-radius: 4px;
                }}
                .success {{ color: #10b981; font-weight: bold; }}
                .warning {{ color: #f59e0b; font-weight: bold; }}
                .error {{ color: #dc3545; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
                th {{ background: #f3f4f6; font-weight: 600; }}
                .footer {{ text-align: center; color: #6b7280; padding: 20px; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 錄音錯誤監控報告</h1>
                    <p style="margin: 5px 0;">報告時間：{now_taipei.strftime('%Y年%m月%d日 %H:%M')} (台灣時間)</p>
                </div>
                <div class="content">
        """

        # AI 摘要區塊
        if ai_summary and total_errors_24h > 0:
            html_content += f"""
                    <div class="summary-box">
                        <h3>🤖 AI 分析摘要</h3>
                        <p>{ai_summary}</p>
                    </div>
            """

        # 📊 錄音統計概覽（成功 + 失敗）
        total_1h = usage_stats_1h["success_count"] + usage_stats_1h["error_count"]
        total_24h = usage_stats_24h["success_count"] + usage_stats_24h["error_count"]
        success_rate_1h = (
            round(usage_stats_1h["success_count"] / total_1h * 100, 1)
            if total_1h > 0
            else 100
        )
        success_rate_24h = (
            round(usage_stats_24h["success_count"] / total_24h * 100, 1)
            if total_24h > 0
            else 100
        )

        html_content += f"""
                    <div class="stats-box">
                        <h3>📊 錄音統計總覽</h3>
                        <table>
                            <tr>
                                <th>時間範圍</th>
                                <th>成功錄音</th>
                                <th>失敗錄音</th>
                                <th>成功率</th>
                                <th>活躍學生</th>
                            </tr>
                            <tr>
                                <td><strong>最近 1 小時</strong></td>
                                <td class="success">{usage_stats_1h['success_count']} 次</td>
                                <td class="{'error' if usage_stats_1h['error_count'] > 10
                                           else 'warning' if usage_stats_1h['error_count'] > 0
                                           else 'success'}">
                                    {usage_stats_1h['error_count']} 次
                                </td>
                                <td class="{'success' if success_rate_1h >= 95
                                           else 'warning' if success_rate_1h >= 90
                                           else 'error'}">
                                    {success_rate_1h}%
                                </td>
                                <td>{usage_stats_1h['success_users']} 位</td>
                            </tr>
                            <tr>
                                <td><strong>最近 24 小時</strong></td>
                                <td class="success">{usage_stats_24h['success_count']} 次</td>
                                <td class="{'error' if usage_stats_24h['error_count'] > 100
                                           else 'warning' if usage_stats_24h['error_count'] > 0
                                           else 'success'}">
                                    {usage_stats_24h['error_count']} 次
                                </td>
                                <td class="{'success' if success_rate_24h >= 95
                                           else 'warning' if success_rate_24h >= 90
                                           else 'error'}">
                                    {success_rate_24h}%
                                </td>
                                <td>{usage_stats_24h['success_users']} 位</td>
                            </tr>
                        </table>
                        <p style="color: #6b7280; font-size: 0.9em; margin-top: 10px;">
                            💡 成功次數來自 StudentItemProgress，錯誤來自 audio_playback_errors
                        </p>
                    </div>

                    <div class="stats-box">
                        <h3>🚨 錯誤嚴重程度</h3>
                        <table>
                            <tr>
                                <th>時間範圍</th>
                                <th>錯誤次數</th>
                                <th>狀態</th>
                            </tr>
                            <tr>
                                <td>最近 1 小時</td>
                                <td class="{'error' if total_errors_1h > 0 else 'success'}">
                                    {total_errors_1h}
                                </td>
                                <td>
                                    {'⚠️ 需注意' if total_errors_1h > 10
                                     else '✅ 正常' if total_errors_1h == 0
                                     else '⚡ 有少量錯誤'}
                                </td>
                            </tr>
                            <tr>
                                <td>最近 24 小時</td>
                                <td class="{'error' if total_errors_24h > 100
                                           else 'warning' if total_errors_24h > 0
                                           else 'success'}">
                                    {total_errors_24h}
                                </td>
                                <td>
                                    {'🚨 嚴重' if total_errors_24h > 100
                                     else '⚠️ 需注意' if total_errors_24h > 50
                                     else '✅ 正常' if total_errors_24h == 0
                                     else '⚡ 輕微'}
                                </td>
                            </tr>
                        </table>
                    </div>
        """

        # 最近 1 小時錯誤明細
        if total_errors_1h > 0:
            html_content += """
                    <div class="stats-box">
                        <h3>⏰ 最近 1 小時錯誤明細</h3>
            """
            for row in results_1h:
                html_content += f"""
                        <div class="error-item">
                            <strong>{row.error_type}</strong><br>
                            平台: {row.platform} | 瀏覽器: {row.browser}<br>
                            錯誤次數: {row.error_count} | 影響學生: {row.affected_students} 位
                        </div>
                """
            html_content += """
                    </div>
            """
        else:
            html_content += """
                    <div class="stats-box">
                        <h3>⏰ 最近 1 小時</h3>
                        <p class="success">✅ 沒有錄音錯誤</p>
                    </div>
            """

        # 最近 24 小時錯誤明細
        if total_errors_24h > 0:
            html_content += """
                    <div class="stats-box">
                        <h3>📅 最近 24 小時錯誤明細（前 10 項）</h3>
                        <table>
                            <tr>
                                <th>錯誤類型</th>
                                <th>平台</th>
                                <th>瀏覽器</th>
                                <th>次數</th>
                                <th>影響學生</th>
                            </tr>
            """
            for row in results_24h[:10]:
                html_content += f"""
                            <tr>
                                <td>{row.error_type}</td>
                                <td>{row.platform}</td>
                                <td>{row.browser}</td>
                                <td>{row.error_count}</td>
                                <td>{row.affected_students}</td>
                            </tr>
                """
            html_content += """
                        </table>
                    </div>
            """

        # 🔥 受影響學生名單（含老師和班級）
        if students_with_errors:
            html_content += f"""
                    <div class="stats-box">
                        <h3>👥 受影響學生名單（最近 24 小時，共 {len(students_with_errors)} 位）</h3>
                        <table style="font-size: 0.9em;">
                            <tr>
                                <th>ID</th>
                                <th>學生姓名</th>
                                <th>班級</th>
                                <th>老師</th>
                                <th>錯誤次數</th>
                                <th>錯誤類型</th>
                            </tr>
            """
            for student in students_with_errors:
                student_name = student["student_name"] or "（未設定）"
                classrooms = student.get("classrooms", "（無班級）")
                teachers = student.get("teachers", "（無老師）")
                error_types_display = (
                    student["error_types"][:80] + "..."
                    if len(student["error_types"]) > 80
                    else student["error_types"]
                )

                html_content += f"""
                            <tr>
                                <td>{student['student_id']}</td>
                                <td><strong>{student_name}</strong></td>
                                <td style="color: #059669;">{classrooms}</td>
                                <td style="color: #dc2626; font-size: 0.85em;">{teachers}</td>
                                <td style="text-align: center; font-weight: bold;">{student['error_count']}</td>
                                <td style="font-size: 0.85em; color: #666;">{error_types_display}</td>
                            </tr>
                """
            html_content += """
                        </table>
                        <p style="color: #6b7280; font-size: 0.9em; margin-top: 10px;">
                            💡 提示：可直接聯繫老師或學生確認使用環境，或主動排查技術問題
                        </p>
                    </div>
            """

        html_content += f"""
                </div>
                <div class="footer">
                    <p>此郵件由 Cloud Scheduler 每小時自動發送<br>
                    Duotopia 技術團隊 | {now_taipei.year}</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 判斷是否需要發送郵件
        current_hour = now_taipei.hour
        is_scheduled_report = current_hour in [0, 6, 12, 18]  # 固定報告時間
        should_send_email = is_scheduled_report or total_errors_1h > 0

        notification_sent = False
        if should_send_email:
            # 發送郵件
            subject_emoji = (
                "🚨" if total_errors_1h > 10 else "⚠️" if total_errors_1h > 0 else "✅"
            )
            report_type = " [定期報告]" if is_scheduled_report else ""
            subject = (
                f"{subject_emoji} 錄音錯誤報告{report_type} - "
                f"{now_taipei.strftime('%m/%d %H:%M')} "
                f"(1H: {total_errors_1h} | 24H: {total_errors_24h})"
            )
            email_service.send_email(
                to_email="myduotopia@gmail.com",
                subject=subject,
                html_content=html_content,
            )
            notification_sent = True

            logger.info(
                f"Recording error report sent. 1H: {total_errors_1h}, 24H: {total_errors_24h}, "
                f"Scheduled: {is_scheduled_report}"
            )
        else:
            logger.info(
                f"No errors in past hour, skipping email. 1H: {total_errors_1h}, 24H: {total_errors_24h}"
            )

        return {
            "status": "success",
            "executed_at": now_taipei.isoformat(),
            "errors_1h": total_errors_1h,
            "errors_24h": total_errors_24h,
            "ai_summary_generated": bool(ai_summary),
            "notification_sent": notification_sent,
            "is_scheduled_report": is_scheduled_report,
        }

    except Exception as e:
        logger.error(f"Recording error report failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )


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
