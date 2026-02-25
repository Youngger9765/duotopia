"""
Subscription and transaction models
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Numeric,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from .base import UUID, JSONType, TransactionType
import uuid


# ============ Subscription System ============
class SubscriptionPeriod(Base):
    """訂閱週期表 - 記錄每次付款的訂閱週期"""

    __tablename__ = "subscription_periods"
    __table_args__ = (
        Index("ix_subscription_periods_teacher_status", "teacher_id", "status"),
        Index("ix_subscription_periods_end_date", "end_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    # 訂閱資訊
    plan_name = Column(
        String, nullable=False
    )  # "Free Trial", "Tutor Teachers", "School Teachers"
    amount_paid = Column(
        Integer, nullable=False
    )  # 0 (trial), 299 (tutor), 599 (school)
    quota_total = Column(Integer, nullable=False)  # 2000 (trial/tutor), 6000 (school)
    quota_used = Column(Integer, default=0, nullable=False)

    # 時間範圍
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # 付款資訊
    payment_method = Column(String, nullable=False)  # "auto_renew" or "manual"
    payment_id = Column(String, nullable=True)  # TapPay rec_id
    payment_status = Column(
        String, default="paid", nullable=False
    )  # paid/pending/failed/refunded

    # 狀態
    status = Column(
        String, default="active", nullable=False
    )  # active/expired/cancelled
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_reason = Column(String, nullable=True)

    # Admin 操作記錄（結構化欄位 + JSONB metadata）
    admin_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    admin_reason = Column(Text, nullable=True)
    admin_metadata = Column(JSONType, nullable=True)  # 記錄完整操作歷史

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    teacher = relationship(
        "Teacher", foreign_keys=[teacher_id], back_populates="subscription_periods"
    )
    admin = relationship("Teacher", foreign_keys=[admin_id])
    usage_logs = relationship(
        "PointUsageLog",
        back_populates="subscription_period",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        start = self.start_date.date() if self.start_date else "None"
        end = self.end_date.date() if self.end_date else "None"
        return (
            f"<SubscriptionPeriod teacher={self.teacher_id} "
            f"period={start}-{end} method={self.payment_method}>"
        )


class PointUsageLog(Base):
    """點數使用記錄表 - 追蹤每一筆配額消耗"""

    __tablename__ = "point_usage_logs"
    __table_args__ = (
        Index("ix_point_usage_logs_teacher_id", "teacher_id"),
        Index("ix_point_usage_logs_period_id", "subscription_period_id"),
        Index("ix_point_usage_logs_created_at", "created_at"),
        Index("ix_point_usage_logs_feature_type", "feature_type"),
        Index("ix_point_usage_logs_teacher_created", "teacher_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # 關聯
    subscription_period_id = Column(
        Integer,
        ForeignKey("subscription_periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True
    )  # 哪個學生用的
    assignment_id = Column(Integer, nullable=True)  # 哪個作業

    # 功能資訊
    feature_type = Column(
        String, nullable=False
    )  # "speech_recording", "speech_assessment", "text_correction"
    feature_detail = Column(JSON)  # 詳細資訊 {"duration": 30, "file_url": "..."}

    # 點數消耗
    points_used = Column(Integer, nullable=False)  # 本次消耗點數
    quota_before = Column(Integer)  # 使用前配額
    quota_after = Column(Integer)  # 使用後配額

    # 單位資訊
    unit_count = Column(Integer)  # 單位數量（30秒、500字）
    unit_type = Column(String)  # "秒", "字", "張"

    # 時間
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    teacher = relationship("Teacher", back_populates="point_usage_logs")
    student = relationship("Student")
    subscription_period = relationship(
        "SubscriptionPeriod", back_populates="usage_logs"
    )

    def __repr__(self):
        return (
            f"<PointUsageLog teacher={self.teacher_id} "
            f"student={self.student_id} feature={self.feature_type} "
            f"points={self.points_used}>"
        )


class TeacherSubscriptionTransaction(Base):
    """教師訂閱交易記錄 - 支援多種支付方式的完整金流記錄"""

    __tablename__ = "teacher_subscription_transactions"

    # 基本欄位
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    # 1. 用戶識別
    teacher_email = Column(String(255), nullable=True, index=True)  # 直接儲存教師 email

    # 2. 交易基本資訊
    transaction_type = Column(
        String, nullable=False
    )  # Use String instead of Enum for flexibility
    subscription_type = Column(String, nullable=True)  # 訂閱類型
    amount = Column(Numeric(10, 2), nullable=True)  # 充值金額（可為空，如試用期）
    currency = Column(String(3), nullable=True, default="TWD")  # 貨幣
    status = Column(String, nullable=False, default="PENDING", index=True)  # 交易狀態
    months = Column(Integer, nullable=False)  # 訂閱月數

    # 3. 時間相關
    period_start = Column(DateTime(timezone=True), nullable=True)  # 訂閱期間開始
    period_end = Column(DateTime(timezone=True), nullable=True)  # 訂閱期間結束
    previous_end_date = Column(DateTime(timezone=True), nullable=True)  # 交易前的到期日
    new_end_date = Column(DateTime(timezone=True), nullable=False)  # 交易後的到期日
    processed_at = Column(DateTime(timezone=True), nullable=True)  # 實際處理時間
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 過期時間（PENDING 狀態用）

    # 4. 防重複扣款
    idempotency_key = Column(
        String(255), nullable=True, unique=True, index=True
    )  # 防重複扣款
    retry_count = Column(Integer, nullable=False, default=0)  # 重試次數

    # 5. 稽核追蹤
    ip_address = Column(String(45), nullable=True)  # 支援 IPv6
    user_agent = Column(Text, nullable=True)  # 瀏覽器/裝置資訊
    request_id = Column(String(255), nullable=True)  # API 請求 ID

    # 6. 支付詳情
    payment_provider = Column(
        String(50), nullable=True, index=True
    )  # tappay/line_pay/paypal
    payment_method = Column(
        String(50), nullable=True
    )  # credit_card/bank_transfer/e_wallet
    external_transaction_id = Column(String(255), nullable=True, index=True)  # 外部交易 ID

    # 7. 錯誤處理
    failure_reason = Column(Text, nullable=True)  # 失敗原因
    error_code = Column(String(50), nullable=True)  # 錯誤代碼
    gateway_response = Column(JSON, nullable=True)  # 金流商完整回應

    # 8. 退款相關
    refunded_amount = Column(Integer, nullable=True, default=0)  # 已退款金額（TWD 分）
    refund_status = Column(String(20), nullable=True)  # 退款狀態
    refund_amount = Column(Integer, nullable=True)  # 本次退款金額（TWD 元）
    refund_reason = Column(Text, nullable=True)  # 退款原因
    refund_notes = Column(Text, nullable=True)  # 退款備註
    refund_initiated_by = Column(
        Integer, ForeignKey("teachers.id"), nullable=True
    )  # 退款操作者
    refund_initiated_at = Column(DateTime(timezone=True), nullable=True)  # 退款發起時間
    original_transaction_id = Column(
        Integer, ForeignKey("teacher_subscription_transactions.id"), nullable=True
    )  # 原始交易（退款時參照）

    # 9. TapPay 電子發票欄位
    rec_invoice_id = Column(String(30), nullable=True, index=True)  # TapPay 發票 ID
    invoice_number = Column(String(10), nullable=True, index=True)  # 發票號碼
    invoice_status = Column(
        String(20), nullable=True, default="PENDING", index=True
    )  # 發票狀態
    invoice_issued_at = Column(DateTime(timezone=True), nullable=True)  # 發票開立時間
    buyer_tax_id = Column(String(8), nullable=True)  # 統一編號
    buyer_name = Column(String(100), nullable=True)  # 買受人名稱
    buyer_email = Column(String(255), nullable=True)  # 買受人 email
    carrier_type = Column(String(10), nullable=True)  # 載具類型
    carrier_id = Column(String(64), nullable=True)  # 載具號碼
    invoice_response = Column(JSON, nullable=True)  # 發票 API 完整回應

    # 10. 其他
    webhook_status = Column(String(20), nullable=True)  # Webhook 通知狀態
    transaction_metadata = Column("metadata", JSON, nullable=True)  # 額外資料（向後相容）
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )  # 更新時間（與 DB 一致）

    # 關聯
    teacher = relationship(
        "Teacher", foreign_keys=[teacher_id], back_populates="subscription_transactions"
    )

    def __repr__(self):
        return (
            f"<TeacherSubscriptionTransaction({self.teacher_id}, "
            f"{self.transaction_type}, {self.months}個月)>"
        )


class InvoiceStatusHistory(Base):
    """發票狀態變更歷史 - 追蹤發票生命週期與 Notify 事件"""

    __tablename__ = "invoice_status_history"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        Integer,
        ForeignKey("teacher_subscription_transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 狀態轉換
    from_status = Column(String(20), nullable=True)  # 原狀態
    to_status = Column(String(20), nullable=False)  # 新狀態
    action_type = Column(
        String(20), nullable=False
    )  # ISSUE/VOID/ALLOWANCE/REISSUE/NOTIFY
    reason = Column(Text, nullable=True)  # 變更原因

    # Notify 事件相關
    is_notify = Column(
        Integer, nullable=False, default=0
    )  # 是否為 Notify 觸發 (use Integer for SQLite)
    notify_error_code = Column(String(20), nullable=True)  # Notify 錯誤代碼
    notify_error_msg = Column(Text, nullable=True)  # Notify 錯誤訊息

    # 完整 API 記錄
    request_payload = Column(JSON, nullable=True)  # 請求資料
    response_payload = Column(JSON, nullable=True)  # 回應資料

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self):
        return (
            f"<InvoiceStatusHistory({self.transaction_id}, "
            f"{self.from_status}->{self.to_status}, {self.action_type})>"
        )
