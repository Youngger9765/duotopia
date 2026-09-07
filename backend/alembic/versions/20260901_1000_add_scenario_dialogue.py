"""Add scenario dialogue storage (Issue #1013)

情境對話（SCENARIO_DIALOGUE）的後端儲存：

1. ``contents.scenario_settings`` (JSONB, nullable) —— 整份設定：情境內容、
   題目難度、作答指引、整體評分標準（時態／語態穩定代碼）、翻譯語言、TTS 設定。
   只有 ``type = 'SCENARIO_DIALOGUE'`` 的列會有值，其餘恆為 NULL。
2. ``practice_sessions.check_practice_mode`` 白名單加入 ``scenario_dialogue``，
   讓新的 PracticeMode 之後真的存得進去。

逐題資料（tense_override / voice_override / keywords / reference_answer /
rubric_note / image_prompt）放在既有的 ``content_items.item_metadata`` JSON 底下
``"scenario_dialogue"`` 這個 key，**不需要 DDL**，也因此所有既有的作業副本／
教材複製路徑（都已整包 copy item_metadata）自動跟著搬。

``ContentType.SCENARIO_DIALOGUE`` 這個 enum 值早在 20251202_0307 就加過了，
本 migration 不再碰 ``contenttype``（ALTER TYPE 為禁止操作）。

Idempotent（可重複執行）:
  - 欄位：``information_schema.columns`` 守衛，且限定 ``table_schema = 'public'``
    （避免 Supabase 的 auth / storage 等其他 schema 同名欄位誤判）。
  - CHECK 約束：先用 ``pg_constraint`` + ``conrelid``（以表 OID 鎖定，不會被其他
    表的同名 constraint 誤判）判斷後 DROP，再重建整份白名單。DROP + 重建同一個
    CHECK 不動任何資料，且與本專案既有三支同類 migration（20260127_1954 /
    20260422_1500 / 20260601_1000 / 20260602_1000）寫法一致。
  - 整段包在 ``to_regclass`` 的存在性守衛裡，表不存在時直接略過。

Revision ID: 20260901_1000
Revises: 20260824_1000
Create Date: 2026-09-01
"""
from typing import Union

from alembic import op


revision: str = "20260901_1000"
down_revision: Union[str, None] = "20260824_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- 1) contents.scenario_settings ----
    # 欄位守衛：information_schema 一定要限定 table_schema = 'public'
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'contents'
                  AND column_name = 'scenario_settings'
            ) THEN
                ALTER TABLE public.contents
                    ADD COLUMN scenario_settings JSONB;
            END IF;
        END $$;
        """
    )

    # ---- 2) practice_sessions.check_practice_mode += scenario_dialogue ----
    op.execute(
        """
        DO $$ BEGIN
            IF to_regclass('public.practice_sessions') IS NULL THEN
                RETURN;
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_constraint c
                JOIN pg_class cls ON c.conrelid = cls.oid
                JOIN pg_namespace n ON cls.relnamespace = n.oid
                WHERE c.conname = 'check_practice_mode'
                  AND cls.relname = 'practice_sessions'
                  AND n.nspname = 'public'
            ) THEN
                ALTER TABLE public.practice_sessions
                    DROP CONSTRAINT check_practice_mode;
            END IF;

            ALTER TABLE public.practice_sessions
            ADD CONSTRAINT check_practice_mode
            CHECK (practice_mode IN (
                'listening',
                'writing',
                'word_selection',
                'word_selection_quiz',
                'word_reading',
                'word_spelling',
                'word_cloze',
                'word_spelling_quiz',
                'word_cloze_quiz',
                'rearrangement',
                'tug_of_war',
                'scenario_dialogue'
            ));
        END $$;
        """
    )


def downgrade() -> None:
    """No-op: forward-only migration per project policy."""
    pass
