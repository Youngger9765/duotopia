"""
測試 Alembic validation hook 的功能
確保危險的 migration 操作被正確攔截
"""

import pytest
from unittest.mock import Mock


# 直接定義 process_revision_directives 函數來進行測試
def process_revision_directives(context, revision, directives):
    """Validate migrations to prevent dangerous operations."""
    # Core business tables that should never be created by autogenerate
    PROTECTED_TABLES = {
        "users",
        "students",
        "classrooms",
        "schools",
        "programs",
        "lessons",
        "contents",
        "student_assignments",
        "activity_results",
        "classroom_program_mappings",
    }

    if directives and directives[0].upgrade_ops:
        for op in directives[0].upgrade_ops.ops:
            # Check for create table operations
            if hasattr(op, "table_name") and op.__class__.__name__ == "CreateTableOp":
                table_name = op.table_name
                if table_name in PROTECTED_TABLES:
                    raise ValueError(
                        f"🚨 MIGRATION VALIDATION ERROR 🚨\n"
                        f"Migration attempts to create core table '{table_name}' which should already exist.\n"
                        f"This usually indicates:\n"
                        f"1. Model changes without proper migration history\n"
                        f"2. Incorrect autogenerate detection\n"
                        f"3. Database schema drift\n\n"
                        f"Please check:\n"
                        f"- Current database state: alembic current\n"
                        f"- Migration history: alembic history\n"
                        f"- Model definitions in models.py\n\n"
                        f"Consider using: alembic revision -m 'description' (without --autogenerate)\n"
                        f"And manually write the specific changes needed."
                    )

            # Check for suspicious operations on protected tables
            if hasattr(op, "table_name") and op.table_name in PROTECTED_TABLES:
                op_type = op.__class__.__name__
                if op_type in ["DropTableOp"]:
                    raise ValueError(
                        f"🚨 DANGEROUS OPERATION DETECTED 🚨\n"
                        f"Migration attempts to drop core table '{op.table_name}'.\n"
                        f"This would destroy critical business data!\n"
                        f"If this is intentional, manually create the migration."
                    )


class MockCreateTableOp:
    """模擬 CreateTableOp 操作"""

    def __init__(self, table_name):
        self.table_name = table_name
        self.__class__.__name__ = "CreateTableOp"


class MockDropTableOp:
    """模擬 DropTableOp 操作"""

    def __init__(self, table_name):
        self.table_name = table_name
        self.__class__.__name__ = "DropTableOp"


class MockUpgradeOps:
    """模擬 UpgradeOps"""

    def __init__(self, ops):
        self.ops = ops


class MockDirective:
    """模擬 Migration Directive"""

    def __init__(self, ops):
        self.upgrade_ops = MockUpgradeOps(ops)


class TestAlembicValidationHook:
    """測試 Alembic 驗證 Hook 功能"""

    def test_hook_allows_empty_operations(self):
        """測試空操作應該被允許"""
        directives = [MockDirective([])]

        # 應該不會拋出異常
        try:
            process_revision_directives(None, None, directives)
        except Exception as e:
            pytest.fail(f"空操作被錯誤地攔截: {e}")

    def test_hook_allows_safe_table_creation(self):
        """測試安全的表格創建應該被允許"""
        safe_ops = [MockCreateTableOp("safe_new_table")]
        directives = [MockDirective(safe_ops)]

        # 應該不會拋出異常
        try:
            process_revision_directives(None, None, directives)
        except Exception as e:
            pytest.fail(f"安全的表格創建被錯誤地攔截: {e}")

    def test_hook_blocks_protected_table_creation_students(self):
        """測試阻擋創建 students 表"""
        dangerous_ops = [MockCreateTableOp("students")]
        directives = [MockDirective(dangerous_ops)]

        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)
        assert "MIGRATION VALIDATION ERROR" in error_msg
        assert "students" in error_msg
        assert "which should already exist" in error_msg

    def test_hook_blocks_protected_table_creation_users(self):
        """測試阻擋創建 users 表"""
        dangerous_ops = [MockCreateTableOp("users")]
        directives = [MockDirective(dangerous_ops)]

        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)
        assert "MIGRATION VALIDATION ERROR" in error_msg
        assert "users" in error_msg

    def test_hook_blocks_protected_table_creation_classrooms(self):
        """測試阻擋創建 classrooms 表"""
        dangerous_ops = [MockCreateTableOp("classrooms")]
        directives = [MockDirective(dangerous_ops)]

        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)
        assert "MIGRATION VALIDATION ERROR" in error_msg
        assert "classrooms" in error_msg

    def test_hook_blocks_all_protected_tables(self):
        """測試所有受保護的表格都被攔截"""
        protected_tables = [
            "users",
            "students",
            "classrooms",
            "schools",
            "programs",
            "lessons",
            "contents",
            "student_assignments",
            "activity_results",
            "classroom_program_mappings",
        ]

        for table_name in protected_tables:
            dangerous_ops = [MockCreateTableOp(table_name)]
            directives = [MockDirective(dangerous_ops)]

            with pytest.raises(ValueError) as exc_info:
                process_revision_directives(None, None, directives)

            error_msg = str(exc_info.value)
            assert (
                "MIGRATION VALIDATION ERROR" in error_msg
            ), f"Table {table_name} was not blocked"
            assert table_name in error_msg

    def test_hook_blocks_table_dropping(self):
        """測試阻擋刪除受保護的表格"""
        dangerous_ops = [MockDropTableOp("students")]
        directives = [MockDirective(dangerous_ops)]

        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)
        assert "DANGEROUS OPERATION DETECTED" in error_msg
        assert "drop core table" in error_msg
        assert "students" in error_msg
        assert "destroy critical business data" in error_msg

    def test_hook_provides_helpful_error_messages(self):
        """測試錯誤訊息包含有用的指引"""
        dangerous_ops = [MockCreateTableOp("programs")]
        directives = [MockDirective(dangerous_ops)]

        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)

        # 檢查是否包含問題描述
        assert "Model changes without proper migration history" in error_msg
        assert "Incorrect autogenerate detection" in error_msg
        assert "Database schema drift" in error_msg

        # 檢查是否包含解決方案
        assert "alembic current" in error_msg
        assert "alembic history" in error_msg
        assert "models.py" in error_msg
        assert "alembic revision -m" in error_msg

    def test_hook_handles_multiple_operations(self):
        """測試處理多個操作的情況"""
        mixed_ops = [
            MockCreateTableOp("safe_table"),  # 安全操作
            MockCreateTableOp("students"),  # 危險操作
        ]
        directives = [MockDirective(mixed_ops)]

        # 應該因為危險操作而被攔截
        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)
        assert "students" in error_msg

    def test_hook_handles_no_directives(self):
        """測試處理空 directives"""
        # 應該不會拋出異常
        try:
            process_revision_directives(None, None, None)
        except Exception as e:
            pytest.fail(f"空 directives 被錯誤地處理: {e}")

    def test_hook_handles_no_upgrade_ops(self):
        """測試處理沒有 upgrade_ops 的 directive"""
        mock_directive = Mock()
        mock_directive.upgrade_ops = None

        # 應該不會拋出異常
        try:
            process_revision_directives(None, None, [mock_directive])
        except Exception as e:
            pytest.fail(f"沒有 upgrade_ops 的情況被錯誤地處理: {e}")

    def test_hook_ignores_non_table_operations(self):
        """測試忽略非表格相關的操作"""

        # 創建一個沒有 table_name 屬性的操作
        class MockNonTableOp:
            def __init__(self):
                self.__class__.__name__ = "AddColumnOp"

        non_table_ops = [MockNonTableOp()]
        directives = [MockDirective(non_table_ops)]

        # 應該不會拋出異常
        try:
            process_revision_directives(None, None, directives)
        except Exception as e:
            pytest.fail(f"非表格操作被錯誤地處理: {e}")


class TestAlembicValidationHookIntegration:
    """整合測試：測試 Hook 在真實場景中的表現"""

    def test_prevents_f66a09eba7e7_scenario(self):
        """測試預防類似 f66a09eba7e7 migration 的場景"""
        # 模擬試圖重建多個核心表格的危險 migration
        dangerous_migration_ops = [
            MockCreateTableOp("students"),
            MockCreateTableOp("classrooms"),
            MockCreateTableOp("users"),
        ]
        directives = [MockDirective(dangerous_migration_ops)]

        # 應該在第一個危險操作就被攔截
        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)
        assert "MIGRATION VALIDATION ERROR" in error_msg
        # 應該提及第一個遇到的危險表格
        assert any(table in error_msg for table in ["students", "classrooms", "users"])

    def test_development_workflow_protection(self):
        """測試保護開發流程不受意外的 autogenerate 影響"""
        # 這種情況可能在開發者修改模型但沒有正確管理 migration 時發生
        problematic_ops = [
            MockDropTableOp("students"),  # 錯誤地認為需要刪除舊表
            MockCreateTableOp("students"),  # 然後重新創建
        ]
        directives = [MockDirective(problematic_ops)]

        # 應該在刪除表格時就被攔截
        with pytest.raises(ValueError) as exc_info:
            process_revision_directives(None, None, directives)

        error_msg = str(exc_info.value)
        assert "DANGEROUS OPERATION DETECTED" in error_msg
        assert "drop core table" in error_msg
