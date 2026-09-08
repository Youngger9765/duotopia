"""Add student_item_progress.scenario_grading_data (issue #1035)

情境對話的 AI 評分建議存放處。

為什麼不寫進既有的 accuracy_score / fluency_score / pronunciation_score：那四欄是
Azure 發音評測的語意（唸得多準），作業層報告 `services/analysis_service.py` 也直接
讀 accuracy_score。情境對話評的是開放式回答的語言特徵（資訊完整度、時態句型、用字
水準、必用字詞），塞進去會讓兩邊的數字互相污染。

沿用本表既有的分模式 JSONB 慣例（rearrangement_data、word_selection_data），
一題一列，存 AI 的逐字稿、四個面向分數、回饋與建議通過與否。

**這是建議，不是定案** —— 老師的判定仍寫在 teacher_review_score / teacher_passed。

Idempotent（遵守 CLAUDE.md Migration 鐵則）：
  - ADD COLUMN 包在 information_schema 守衛裡（scoped to table_schema='public'）
  - 欄位 nullable，既有資料列不受影響
  - 沒有 DROP / RENAME / ALTER TYPE

Revision ID: 20260908_1000
Revises: 20260907_1000
Create Date: 2026-09-08
"""
from typing import Union

from alembic import op


revision: str = "20260908_1000"
down_revision: Union[str, None] = "20260907_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'student_item_progress'
                  AND column_name = 'scenario_grading_data'
            ) THEN
                ALTER TABLE student_item_progress
                ADD COLUMN scenario_grading_data JSONB;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # 破壞性操作對其他環境不安全，依專案慣例不在 downgrade 刪欄位。
    pass
