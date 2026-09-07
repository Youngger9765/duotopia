"""情境對話 AI 生圖的每月計數 model（issue #1024）。

生圖比文字生成貴一個量級，而且是**逐題觸發**的（一份 10 題就可能按 10 次），所以在
完整配額系統（#1025）做好之前，先用一個單純的月上限擋住。

與 `magic_paste_usage` 同一個形狀：每位老師每個自然月一列，`year_month` 用
'YYYY-MM' 字串，唯一約束 (teacher_id, year_month) 供 UPSERT 累加，跨月自然重置。

**與 magic_paste 的差別**：這裡只有「用完就擋」，沒有接點數 waterfall。等 #1025 決定
好計價方式再換掉；那時這張表可以直接沿用（欄位一樣）。

本表為 JWT-auth 業務表，不使用 Supabase RLS（已加入 deploy-backend.yml 排除清單）。
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.sql import func
from database import Base


class ScenarioImageUsage(Base):
    """情境對話生圖的每月使用計數（每位老師每個自然月一列）。"""

    __tablename__ = "scenario_image_usage"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id", "year_month", name="uq_scenario_image_usage_teacher_month"
        ),
        Index("ix_scenario_image_usage_teacher_month", "teacher_id", "year_month"),
    )

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    # 'YYYY-MM'，代表計數所屬的自然月
    year_month = Column(String(7), nullable=False)
    count = Column(Integer, nullable=False, default=0, server_default="0")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
