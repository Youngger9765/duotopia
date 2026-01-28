"""Fix historical data for auto-graded assignments (rearrangement, word_selection)

Issue #165: 修復歷史資料
1. 將 rearrangement 和 word_selection 類型的作業從 SUBMITTED 改為 GRADED
2. 計算並回填缺失的分數

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-01-28 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "g2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    """
    修復自動批改作業的歷史資料：
    1. 狀態修正：SUBMITTED → GRADED
    2. 分數回填：從 StudentItemProgress 或 calculate_assignment_mastery 計算
    """

    # Step 1: 修正 rearrangement 類型的狀態和分數
    # 計算平均分數從 StudentItemProgress.expected_score
    op.execute(
        """
        WITH rearrangement_scores AS (
            -- 計算每個 student_assignment 的平均分數
            SELECT
                sa.id as student_assignment_id,
                COALESCE(AVG(sip.expected_score), 0) as calculated_score
            FROM student_assignments sa
            INNER JOIN assignments a ON sa.assignment_id = a.id
            LEFT JOIN student_item_progress sip ON sip.student_assignment_id = sa.id
            WHERE a.practice_mode = 'rearrangement'
              AND sa.status = 'SUBMITTED'
              AND sa.is_active = true
            GROUP BY sa.id
        )
        UPDATE student_assignments sa
        SET
            status = 'GRADED',
            graded_at = COALESCE(sa.submitted_at, NOW()),
            score = rs.calculated_score
        FROM rearrangement_scores rs
        WHERE sa.id = rs.student_assignment_id;
    """
    )

    # Step 2: 修正 word_selection 類型的狀態和分數
    # 使用 calculate_assignment_mastery 函數計算分數
    op.execute(
        """
        WITH word_selection_scores AS (
            -- 使用 calculate_assignment_mastery 計算每個作業的熟悉度分數
            SELECT
                sa.id as student_assignment_id,
                LEAST(100, COALESCE(
                    (SELECT current_mastery * 100 FROM calculate_assignment_mastery(sa.id)),
                    0
                )) as calculated_score
            FROM student_assignments sa
            INNER JOIN assignments a ON sa.assignment_id = a.id
            WHERE a.practice_mode = 'word_selection'
              AND sa.status = 'SUBMITTED'
              AND sa.is_active = true
        )
        UPDATE student_assignments sa
        SET
            status = 'GRADED',
            graded_at = COALESCE(sa.submitted_at, NOW()),
            score = ws.calculated_score
        FROM word_selection_scores ws
        WHERE sa.id = ws.student_assignment_id;
    """
    )

    # Step 3: 同時修正 StudentContentProgress 狀態（如果有的話）
    op.execute(
        """
        UPDATE student_content_progress scp
        SET status = 'GRADED'
        FROM student_assignments sa
        INNER JOIN assignments a ON sa.assignment_id = a.id
        WHERE scp.student_assignment_id = sa.id
          AND a.practice_mode IN ('rearrangement', 'word_selection')
          AND scp.status = 'SUBMITTED'
          AND sa.is_active = true;
    """
    )


def downgrade():
    """
    回滾：將 GRADED 改回 SUBMITTED（僅針對沒有 graded_at 早於 submitted_at 的記錄）
    注意：分數無法回滾，因為我們不知道原本是否有分數
    """
    # 這個 downgrade 比較難精確執行，因為我們無法區分
    # 哪些是本次 migration 修改的，哪些是正常流程產生的
    # 因此只記錄警告，不做實際回滾
    op.execute(
        """
        -- Downgrade is not fully reversible
        -- Records that were updated cannot be distinguished from normally graded ones
        -- This is intentional - the data fix is permanent
        SELECT 1;
    """
    )
