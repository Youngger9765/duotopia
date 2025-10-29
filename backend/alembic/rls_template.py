"""
Alembic Migration RLS Template
用於在建立新資料表時自動加入 Row Level Security (RLS) 配置

使用方式：
1. 從這個檔案複製需要的 RLS 函數
2. 在 migration 檔案中呼叫對應的函數
3. 根據資料表的存取需求選擇適當的 Policy

範例：
    from alembic import op

    def upgrade():
        # 建立資料表
        op.create_table('my_table', ...)

        # 啟用 RLS（必須！）
        enable_rls('my_table')

        # 建立 Policy - 教師只能存取自己的資料
        create_teacher_only_policies('my_table', owner_column='teacher_id')
"""

from alembic import op


# ============================================================
# RLS 啟用函數
# ============================================================


def enable_rls(table_name: str):
    """
    為資料表啟用 Row Level Security

    ⚠️ 重要：建立新資料表時必須呼叫此函數！

    Args:
        table_name: 資料表名稱

    Example:
        enable_rls('teachers')
        enable_rls('classrooms')
    """
    op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")


def disable_rls(table_name: str):
    """
    關閉 Row Level Security（通常用於 downgrade）

    Args:
        table_name: 資料表名稱
    """
    op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")


# ============================================================
# Policy 建立函數 - 教師專用
# ============================================================


def create_teacher_only_policies(
    table_name: str,
    owner_column: str = "teacher_id",
    allow_insert: bool = True,
    allow_update: bool = True,
    allow_delete: bool = True,
):
    """
    建立「教師只能存取自己資料」的完整 Policies

    適用於：classrooms, assignments, courses 等教師專屬資料

    Args:
        table_name: 資料表名稱
        owner_column: 擁有者欄位名稱（預設 'teacher_id'）
        allow_insert: 是否允許 INSERT
        allow_update: 是否允許 UPDATE
        allow_delete: 是否允許 DELETE

    Example:
        create_teacher_only_policies('classrooms', owner_column='teacher_id')
        create_teacher_only_policies('courses', allow_delete=False)
    """
    # SELECT: 教師只能查看自己的資料
    op.execute(
        f"""
        CREATE POLICY {table_name}_select_own ON {table_name}
        FOR SELECT
        USING ({owner_column}::text = auth.uid()::text);
    """
    )

    if allow_insert:
        # INSERT: 教師只能插入自己的資料
        op.execute(
            f"""
            CREATE POLICY {table_name}_insert_own ON {table_name}
            FOR INSERT
            WITH CHECK ({owner_column}::text = auth.uid()::text);
        """
        )

    if allow_update:
        # UPDATE: 教師只能更新自己的資料
        op.execute(
            f"""
            CREATE POLICY {table_name}_update_own ON {table_name}
            FOR UPDATE
            USING ({owner_column}::text = auth.uid()::text)
            WITH CHECK ({owner_column}::text = auth.uid()::text);
        """
        )

    if allow_delete:
        # DELETE: 教師只能刪除自己的資料
        op.execute(
            f"""
            CREATE POLICY {table_name}_delete_own ON {table_name}
            FOR DELETE
            USING ({owner_column}::text = auth.uid()::text);
        """
        )


# ============================================================
# Policy 建立函數 - 學生專用
# ============================================================


def create_student_only_policies(
    table_name: str,
    owner_column: str = "student_id",
    allow_insert: bool = False,
    allow_update: bool = True,
    allow_delete: bool = False,
):
    """
    建立「學生只能存取自己資料」的完整 Policies

    適用於：student_assignments, student_content_progress 等學生專屬資料

    Args:
        table_name: 資料表名稱
        owner_column: 擁有者欄位名稱（預設 'student_id'）
        allow_insert: 是否允許 INSERT（通常學生不能自己建立資料）
        allow_update: 是否允許 UPDATE（通常只能更新進度）
        allow_delete: 是否允許 DELETE（通常學生不能刪除）

    Example:
        create_student_only_policies('student_assignments')
    """
    # SELECT: 學生只能查看自己的資料
    op.execute(
        f"""
        CREATE POLICY {table_name}_select_student ON {table_name}
        FOR SELECT
        USING ({owner_column}::text = auth.uid()::text);
    """
    )

    if allow_insert:
        op.execute(
            f"""
            CREATE POLICY {table_name}_insert_student ON {table_name}
            FOR INSERT
            WITH CHECK ({owner_column}::text = auth.uid()::text);
        """
        )

    if allow_update:
        # UPDATE: 學生可以更新自己的資料（如進度、答案）
        op.execute(
            f"""
            CREATE POLICY {table_name}_update_student ON {table_name}
            FOR UPDATE
            USING ({owner_column}::text = auth.uid()::text)
            WITH CHECK ({owner_column}::text = auth.uid()::text);
        """
        )

    if allow_delete:
        op.execute(
            f"""
            CREATE POLICY {table_name}_delete_student ON {table_name}
            FOR DELETE
            USING ({owner_column}::text = auth.uid()::text);
        """
        )


# ============================================================
# Policy 建立函數 - 教師 + 學生共享
# ============================================================


def create_teacher_student_shared_policies(
    table_name: str,
    teacher_column: str = "teacher_id",
    student_column: str = "student_id",
):
    """
    建立「教師可存取，學生只能查看自己」的 Policies

    適用於：student_assignments（教師派作業，學生做作業）

    Args:
        table_name: 資料表名稱
        teacher_column: 教師欄位名稱
        student_column: 學生欄位名稱

    Example:
        create_teacher_student_shared_policies('student_assignments')
    """
    # SELECT: 教師可查看自己派的作業，學生可查看自己的作業
    op.execute(
        f"""
        CREATE POLICY {table_name}_select_shared ON {table_name}
        FOR SELECT
        USING (
            {teacher_column}::text = auth.uid()::text
            OR {student_column}::text = auth.uid()::text
        );
    """
    )

    # INSERT: 只有教師可以建立（派作業）
    op.execute(
        f"""
        CREATE POLICY {table_name}_insert_teacher ON {table_name}
        FOR INSERT
        WITH CHECK ({teacher_column}::text = auth.uid()::text);
    """
    )

    # UPDATE: 教師可更新自己派的，學生可更新自己的
    op.execute(
        f"""
        CREATE POLICY {table_name}_update_shared ON {table_name}
        FOR UPDATE
        USING (
            {teacher_column}::text = auth.uid()::text
            OR {student_column}::text = auth.uid()::text
        )
        WITH CHECK (
            {teacher_column}::text = auth.uid()::text
            OR {student_column}::text = auth.uid()::text
        );
    """
    )

    # DELETE: 只有教師可以刪除
    op.execute(
        f"""
        CREATE POLICY {table_name}_delete_teacher ON {table_name}
        FOR DELETE
        USING ({teacher_column}::text = auth.uid()::text);
    """
    )


# ============================================================
# Policy 建立函數 - JOIN 關聯存取
# ============================================================


def create_join_based_policies(
    table_name: str,
    join_table: str,
    join_condition: str,
    role: str = "student",
):
    """
    建立「透過 JOIN 判斷存取權限」的 Policies

    適用於：student_content_progress, student_item_progress（沒有直接 student_id）

    Args:
        table_name: 資料表名稱
        join_table: 要 JOIN 的表
        join_condition: JOIN 條件
        role: 使用角色（'student' 或 'teacher'）

    Example:
        create_join_based_policies(
            table_name='student_content_progress',
            join_table='student_assignments',
            join_condition='student_assignments.id = student_content_progress.student_assignment_id',
            role='student'
        )
    """
    # SELECT: 透過 JOIN 檢查權限
    op.execute(
        f"""
        CREATE POLICY {table_name}_select_{role} ON {table_name}
        FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM {join_table}
                WHERE {join_condition}
                AND {join_table}.{role}_id::text = auth.uid()::text
            )
        );
    """
    )

    # INSERT: 同樣透過 JOIN 檢查
    op.execute(
        f"""
        CREATE POLICY {table_name}_insert_{role} ON {table_name}
        FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM {join_table}
                WHERE {join_condition}
                AND {join_table}.{role}_id::text = auth.uid()::text
            )
        );
    """
    )

    # UPDATE
    op.execute(
        f"""
        CREATE POLICY {table_name}_update_{role} ON {table_name}
        FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM {join_table}
                WHERE {join_condition}
                AND {join_table}.{role}_id::text = auth.uid()::text
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM {join_table}
                WHERE {join_condition}
                AND {join_table}.{role}_id::text = auth.uid()::text
            )
        );
    """
    )

    # DELETE
    op.execute(
        f"""
        CREATE POLICY {table_name}_delete_{role} ON {table_name}
        FOR DELETE
        USING (
            EXISTS (
                SELECT 1 FROM {join_table}
                WHERE {join_condition}
                AND {join_table}.{role}_id::text = auth.uid()::text
            )
        );
    """
    )


# ============================================================
# Policy 刪除函數（用於 downgrade）
# ============================================================


def drop_all_policies(table_name: str):
    """
    刪除資料表的所有 Policies（通常用於 migration downgrade）

    Args:
        table_name: 資料表名稱

    Example:
        drop_all_policies('teachers')
    """
    op.execute(
        f"""
        DO $$
        DECLARE
            pol record;
        BEGIN
            FOR pol IN
                SELECT policyname
                FROM pg_policies
                WHERE tablename = '{table_name}'
            LOOP
                EXECUTE 'DROP POLICY IF EXISTS ' || pol.policyname || ' ON {table_name}';
            END LOOP;
        END $$;
    """
    )


# ============================================================
# 完整 Migration 範例
# ============================================================

"""
完整 Migration 範例：建立教師專屬的「課程」資料表

from alembic import op
import sqlalchemy as sa
from alembic.rls_template import (
    enable_rls,
    disable_rls,
    create_teacher_only_policies,
    drop_all_policies,
)

def upgrade() -> None:
    # 1. 建立資料表
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
    )

    # 2. 啟用 RLS（必須！）
    enable_rls('courses')

    # 3. 建立 Policies - 教師只能存取自己的課程
    create_teacher_only_policies(
        'courses',
        owner_column='teacher_id',
        allow_insert=True,
        allow_update=True,
        allow_delete=True,
    )

def downgrade() -> None:
    # 1. 刪除所有 Policies
    drop_all_policies('courses')

    # 2. 關閉 RLS
    disable_rls('courses')

    # 3. 刪除資料表
    op.drop_table('courses')
"""
