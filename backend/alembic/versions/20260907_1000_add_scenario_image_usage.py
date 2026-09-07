"""Add scenario_image_usage table (issue #1024)

情境對話 AI 生圖的每月免費次數計數表。生圖比文字生成貴一個量級、又是逐題觸發
（一份 10 題可能按 10 次），在完整配額（#1025）做好之前先用單純的月上限擋住。

與 magic_paste_usage 同形狀：每位老師每個自然月一列，year_month 以 'YYYY-MM' 字串
表示，跨月自然重置；唯一約束 (teacher_id, year_month) 供 UPSERT 累加。

Idempotent（遵守 CLAUDE.md Migration 鐵則）：
  - CREATE TABLE IF NOT EXISTS
  - constraint 先用 pg_constraint + conrelid（以表 OID 鎖定，不會被其他表的同名
    constraint 誤判）檢查後建立
  - CREATE INDEX IF NOT EXISTS
  - 沒有 DROP / RENAME / ALTER TYPE

本表為 JWT-auth 業務表，不使用 Supabase RLS（已加入 deploy-backend.yml 排除清單）。

Revision ID: 20260907_1000
Revises: 20260901_1000
Create Date: 2026-09-07
"""
from typing import Union

from alembic import op


revision: str = "20260907_1000"
down_revision: Union[str, None] = "20260901_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) 建表（冪等）
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS scenario_image_usage (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL
                REFERENCES teachers (id) ON DELETE CASCADE,
            year_month VARCHAR(7) NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
        """
    )

    # 2) 唯一約束（先檢查後建立，pg_constraint 依 table OID 鎖定）
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint c
                JOIN pg_class cls ON c.conrelid = cls.oid
                WHERE c.conname = 'uq_scenario_image_usage_teacher_month'
                  AND cls.relname = 'scenario_image_usage'
            ) THEN
                ALTER TABLE scenario_image_usage
                ADD CONSTRAINT uq_scenario_image_usage_teacher_month
                UNIQUE (teacher_id, year_month);
            END IF;
        END $$;
        """
    )

    # 3) 查詢索引（冪等）
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_scenario_image_usage_teacher_month
        ON scenario_image_usage (teacher_id, year_month)
        """
    )


def downgrade() -> None:
    # 破壞性操作對其他環境不安全，依專案慣例不在 downgrade 刪表。
    pass
