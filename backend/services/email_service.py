"""Email 服務 - 處理 email 驗證和通知"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from sqlalchemy.orm import Session

from models import Student, Teacher

logger = logging.getLogger(__name__)


class EmailService:
    """Email 服務類別"""

    def __init__(self):
        # 從環境變數讀取 SMTP 設定
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@duotopia.com")
        self.from_name = os.getenv("FROM_NAME", "Duotopia")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    def generate_verification_token(self) -> str:
        """生成驗證 token"""
        return secrets.token_urlsafe(32)

    def send_verification_email(
        self, db: Session, student: Student, email: str = None
    ) -> bool:
        """發送驗證 email

        Args:
            db: 資料庫 session
            student: 學生物件
            email: 要驗證的 email（若無則使用 student.email）

        Returns:
            是否成功發送
        """
        try:
            # 使用提供的 email 或學生現有的 email
            target_email = email or student.email

            # 生成驗證 token
            token = self.generate_verification_token()

            # 更新學生資料
            if email and student.email != email:
                student.email = email  # 更新 email
            student.email_verification_token = token
            student.email_verification_sent_at = datetime.utcnow()
            db.commit()

            # 建立驗證連結
            verification_url = f"{self.frontend_url}/verify-email?token={token}"

            # 建立 email 內容
            subject = f"【Duotopia】請驗證您的 Email - {student.name} 的學習帳號"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4A90E2; color: white; padding: 20px;
                               text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; padding: 12px 30px; background-color: #4A90E2;
                               color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px;
                               font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Duotopia Email 驗證</h1>
                    </div>
                    <div class="content">
                        <h2>親愛的家長您好，</h2>
                        <p>您的孩子 <strong>{student.name}</strong> 在 Duotopia 英語學習平台的帳號需要驗證您的 Email。</p>
                        <p>驗證後，您將可以：</p>
                        <ul>
                            <li>📧 收到學習進度通知</li>
                            <li>📊 查看每週學習報告</li>
                            <li>🎯 了解孩子的學習成就</li>
                        </ul>
                        <p>請點擊下方按鈕完成驗證：</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">驗證 Email</a>
                        </div>
                        <p style="font-size: 12px; color: #666;">
                            如果按鈕無法點擊，請複製以下連結到瀏覽器：<br>
                            <a href="{verification_url}" style="color: #4A90E2; word-break: break-all;">
                                {verification_url}</a>
                        </p>
                        <p style="font-size: 12px; color: #666;">
                            此驗證連結將在 24 小時後失效。
                        </p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Duotopia. All rights reserved.</p>
                        <p>如果您沒有申請此驗證，請忽略此信件。</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # 如果 SMTP 未設定，只記錄日誌（開發模式）
            if not self.smtp_user or not self.smtp_password:
                logger.info(f"開發模式：驗證連結 - {verification_url}")
                print("\n📧 驗證 Email 已發送（開發模式）")
                print(f"   收件人: {target_email}")
                print(f"   學生: {student.name}")
                print(f"   驗證連結: {verification_url}\n")
                return True

            # 發送實際 email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = target_email

            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"驗證 email 已發送到 {target_email}")
            return True

        except Exception as e:
            logger.error(f"發送驗證 email 失敗: {str(e)}")
            return False

    def verify_email_token(self, db: Session, token: str) -> Optional[Student]:
        """驗證 email token

        Args:
            db: 資料庫 session
            token: 驗證 token

        Returns:
            驗證成功的學生物件，或 None
        """
        try:
            # 查找擁有此 token 的學生 (直接比對，不需要 hash)
            student = (
                db.query(Student)
                .filter(Student.email_verification_token == token)
                .first()
            )

            if not student:
                return None

            # 檢查 token 是否過期（24 小時）
            if student.email_verification_sent_at:
                # 處理時區問題：確保兩個時間都是 UTC
                now_utc = datetime.utcnow().replace(tzinfo=None)
                sent_at = (
                    student.email_verification_sent_at.replace(tzinfo=None)
                    if student.email_verification_sent_at.tzinfo
                    else student.email_verification_sent_at
                )
                time_diff = now_utc - sent_at
                if time_diff > timedelta(hours=24):
                    logger.warning(f"Token 已過期: {token}")
                    return None

            # 標記為已驗證
            student.email_verified = True
            student.email_verified_at = datetime.utcnow()
            student.email_verification_token = None  # 清除 token
            db.commit()

            logger.info(f"Email 驗證成功: {student.email}")
            return student

        except Exception as e:
            logger.error(f"驗證 email token 失敗: {str(e)}")
            db.rollback()
            return None

    def resend_verification_email(self, db: Session, student: Student) -> bool:
        """重新發送驗證 email

        Args:
            db: 資料庫 session
            student: 學生物件

        Returns:
            是否成功發送
        """
        # 檢查是否已經驗證
        if student.email_verified:
            return False

        # 檢查是否有 email
        if not student.email:
            return False

        # 檢查發送頻率限制（5 分鐘內不能重複發送）
        if student.email_verification_sent_at:
            time_diff = datetime.utcnow() - student.email_verification_sent_at
            if time_diff < timedelta(minutes=5):
                logger.warning(f"發送過於頻繁: {student.email}")
                return False

        # 重新發送
        return self.send_verification_email(db, student)

    # ========== 教師 Email 驗證功能 ==========

    def send_teacher_verification_email(self, db: Session, teacher: Teacher) -> bool:
        """發送教師驗證 email

        Args:
            db: 資料庫 session
            teacher: 教師物件

        Returns:
            是否成功發送
        """
        try:
            # 生成新的驗證 token
            verification_token = self.generate_verification_token()

            # 更新教師的驗證資訊
            teacher.email_verification_token = verification_token
            teacher.email_verification_sent_at = datetime.utcnow()
            db.commit()

            # 構建驗證連結
            verification_url = (
                f"{self.frontend_url}/teacher/verify-email?token={verification_token}"
            )

            # 構建 email 內容
            html_content = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2563eb; color: white; padding: 20px;
                        text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #2563eb; color: white;
                        padding: 12px 24px; text-decoration: none; border-radius: 6px;
                        font-weight: bold; }}
                    .warning {{ background: #fef3c7; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 歡迎加入 Duotopia！</h1>
                    </div>
                    <div class="content">
                        <h2>親愛的 {teacher.name} 老師：</h2>

                        <p>感謝您註冊 Duotopia 教學平台！為了確保您的帳號安全，請點擊下方按鈕完成 email 驗證：</p>

                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" class="button">驗證我的 Email</a>
                        </p>

                        <div class="warning">
                            <strong>🎁 專屬福利：</strong><br>
                            完成 email 驗證後，您將立即獲得 <strong>30 天免費試用</strong>，可以使用 Duotopia 的所有功能！
                        </div>

                        <p>驗證完成後，您可以：</p>
                        <ul>
                            <li>✅ 創建和管理班級</li>
                            <li>✅ 指派作業給學生</li>
                            <li>✅ 使用 AI 輔助批改功能</li>
                            <li>✅ 追蹤學生學習進度</li>
                        </ul>

                        <p><small>此驗證連結將在 24 小時後失效。如果您沒有申請此帳號，請忽略此信件。</small></p>

                        <hr style="margin: 30px 0;">
                        <p style="color: #6b7280; font-size: 14px;">
                            Duotopia 團隊<br>
                            讓英語學習更有趣！
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            # 純文字版本
            text_content = f"""
            歡迎加入 Duotopia！

            親愛的 {teacher.name} 老師：

            感謝您註冊 Duotopia 教學平台！請點擊以下連結完成 email 驗證：

            {verification_url}

            完成驗證後，您將獲得 30 天免費試用，可以使用 Duotopia 的所有功能！

            此驗證連結將在 24 小時後失效。

            Duotopia 團隊
            """

            # 創建 email 訊息
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Duotopia - 請驗證您的 Email 地址"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = teacher.email

            # 添加內容
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # 如果 SMTP 未設定，只記錄日誌（開發模式）
            if not self.smtp_user or not self.smtp_password:
                logger.info(f"開發模式：教師驗證連結 - {verification_url}")
                print("\n📧 教師驗證 Email 已發送（開發模式）")
                print(f"   收件人: {teacher.email}")
                print(f"   教師: {teacher.name}")
                print(f"   驗證連結: {verification_url}\n")
                return True

            # 發送實際 email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"教師驗證 email 已發送到 {teacher.email}")
            return True

        except Exception as e:
            logger.error(f"發送教師驗證 email 失敗: {str(e)}")
            return False

    def verify_teacher_email_token(self, db: Session, token: str) -> Optional[Teacher]:
        """驗證教師 email token 並啟動訂閱

        Args:
            db: 資料庫 session
            token: 驗證 token

        Returns:
            驗證成功的教師物件，或 None
        """
        try:
            # 查找擁有此 token 的教師
            teacher = (
                db.query(Teacher)
                .filter(Teacher.email_verification_token == token)
                .first()
            )

            if not teacher:
                return None

            # 檢查 token 是否過期（24 小時）
            if teacher.email_verification_sent_at:
                now_utc = datetime.utcnow().replace(tzinfo=None)
                sent_at = (
                    teacher.email_verification_sent_at.replace(tzinfo=None)
                    if teacher.email_verification_sent_at.tzinfo
                    else teacher.email_verification_sent_at
                )
                time_diff = now_utc - sent_at
                if time_diff > timedelta(hours=24):
                    logger.warning(f"教師驗證 token 已過期: {token}")
                    return None

            # 標記為已驗證並啟動帳號
            teacher.email_verified = True
            teacher.email_verified_at = datetime.utcnow()
            teacher.email_verification_token = None
            teacher.is_active = True

            # 🎯 重要：啟動 30 天訂閱！
            teacher.subscription_end_date = datetime.utcnow() + timedelta(days=30)

            db.commit()

            logger.info(f"教師 email 驗證成功並啟動 30 天訂閱: {teacher.email}")
            return teacher

        except Exception as e:
            logger.error(f"驗證教師 email token 失敗: {str(e)}")
            db.rollback()
            return None

    def resend_teacher_verification_email(self, db: Session, teacher: Teacher) -> bool:
        """重新發送教師驗證 email

        Args:
            db: 資料庫 session
            teacher: 教師物件

        Returns:
            是否成功發送
        """
        # 檢查是否已驗證
        if teacher.email_verified:
            return False

        # 檢查發送頻率限制（5 分鐘內不能重複發送）
        if teacher.email_verification_sent_at:
            time_diff = datetime.utcnow() - teacher.email_verification_sent_at
            if time_diff < timedelta(minutes=5):
                logger.warning(f"教師驗證信發送過於頻繁: {teacher.email}")
                return False

        # 重新發送
        return self.send_teacher_verification_email(db, teacher)


# 全域 email 服務實例
email_service = EmailService()
