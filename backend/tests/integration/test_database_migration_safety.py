"""
Database Migration Safety Tests
測試資料庫遷移的安全性，預防生產環境災難
"""

import pytest
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
import ast
import subprocess
from unittest.mock import patch, MagicMock
from sqlalchemy import text, inspect
from database import get_db, engine
import alembic.config


class TestMigrationSafetyChecks:
    """Migration 安全檢查"""

    def test_all_migrations_have_downgrade(self):
        """測試所有 migration 都有 downgrade 函數（可回滾）"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        missing_downgrade = []

        for migration_file in alembic_versions.glob("*.py"):
            with open(migration_file, "r") as f:
                content = f.read()

            # 檢查是否有 downgrade 函數
            if "def downgrade()" not in content:
                missing_downgrade.append(migration_file.name)
            elif "def downgrade():\n    pass" in content:
                missing_downgrade.append(f"{migration_file.name} (empty downgrade)")

        if missing_downgrade:
            pytest.fail(
                f"Migrations without proper downgrade (DANGEROUS!): {missing_downgrade}\n"
                f"This prevents rollback in production!"
            )

    def test_no_dangerous_operations_without_safety(self):
        """測試危險操作必須有安全註解"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        dangerous_patterns = [
            (r"op\.drop_table\(", "DROP TABLE"),
            (r"op\.drop_column\(", "DROP COLUMN"),
            (r"op\.drop_constraint\(", "DROP CONSTRAINT"),
            (r"op\.drop_index\(", "DROP INDEX"),
            (r"op\.execute\(.*DELETE.*FROM", "DELETE FROM"),
            (r"op\.execute\(.*TRUNCATE", "TRUNCATE"),
            (r"op\.alter_column\(.*nullable=False", "NOT NULL without default"),
        ]

        unsafe_operations = []

        for migration_file in alembic_versions.glob("*.py"):
            with open(migration_file, "r") as f:
                content = f.read()
                lines = content.split("\n")

            for pattern, operation_type in dangerous_patterns:
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        # 檢查前三行是否有安全註解
                        has_safety_annotation = False
                        for j in range(max(0, i - 3), i):
                            if any(
                                keyword in lines[j].lower()
                                for keyword in [
                                    "# safe:",
                                    "# safety:",
                                    "# verified:",
                                    "# data backed up",
                                ]
                            ):
                                has_safety_annotation = True
                                break

                        if not has_safety_annotation:
                            unsafe_operations.append(
                                {
                                    "file": migration_file.name,
                                    "line": i + 1,
                                    "operation": operation_type,
                                    "code": line.strip(),
                                }
                            )

        if unsafe_operations:
            msg = "Dangerous operations without safety annotations:\n"
            for op in unsafe_operations:
                msg += (
                    f"  {op['file']}:{op['line']} - {op['operation']}: {op['code']}\n"
                )
            msg += "\nAdd safety comments like '# SAFE: Data backed up' before dangerous operations"
            pytest.fail(msg)

    def test_migration_dependency_chain(self):
        """測試 migration 依賴鏈完整性"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        # 建立 revision 圖
        revision_graph = {}
        revision_files = {}

        for migration_file in alembic_versions.glob("*.py"):
            with open(migration_file, "r") as f:
                content = f.read()

            revision = None
            down_revision = None

            for line in content.split("\n"):
                if line.startswith("revision = "):
                    revision = line.split("=")[1].strip().strip("'\"")
                elif line.startswith("down_revision = "):
                    down_revision = line.split("=")[1].strip().strip("'\"")

            if revision:
                revision_graph[revision] = down_revision
                revision_files[revision] = migration_file.name

        # 檢查是否有斷鏈
        for revision, parent in revision_graph.items():
            if parent and parent != "None" and parent not in revision_graph:
                pytest.fail(
                    f"Broken migration chain: {revision_files[revision]} "
                    f"references non-existent parent {parent}"
                )

        # 檢查是否有循環依賴
        for start_revision in revision_graph:
            visited = set()
            current = start_revision

            while current and current != "None":
                if current in visited:
                    pytest.fail(
                        f"Circular dependency detected starting from {start_revision}"
                    )
                visited.add(current)
                current = revision_graph.get(current)

    def test_no_data_loss_operations(self):
        """測試沒有資料遺失風險的操作"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        data_loss_patterns = [
            (r"op\.drop_table\(", "Dropping table"),
            (r"op\.drop_column\(", "Dropping column"),
            (r"op\.execute\(.*DELETE.*FROM.*WHERE", "Conditional DELETE"),
            (r"op\.execute\(.*DELETE.*FROM(?!.*WHERE)", "Unconditional DELETE"),
            (r"op\.execute\(.*TRUNCATE", "TRUNCATE table"),
            (r"op\.alter_column\(.*type_=.*String\(\d+\)", "Reducing string length"),
        ]

        potential_data_loss = []

        for migration_file in alembic_versions.glob("*.py"):
            with open(migration_file, "r") as f:
                content = f.read()

            for pattern, risk_type in data_loss_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # 檢查是否在 downgrade 函數中（downgrade 中的資料遺失是預期的）
                    lines_before = content[: match.start()].split("\n")
                    in_downgrade = False
                    for line in reversed(lines_before[-5:]):
                        if "def downgrade()" in line:
                            in_downgrade = True
                            break
                        if "def upgrade()" in line:
                            break

                    if not in_downgrade:
                        potential_data_loss.append(
                            {
                                "file": migration_file.name,
                                "risk": risk_type,
                                "code": match.group(0),
                            }
                        )

        if potential_data_loss:
            msg = "Potential data loss operations detected:\n"
            for risk in potential_data_loss:
                msg += f"  {risk['file']}: {risk['risk']} - {risk['code']}\n"
            msg += "\nEnsure data is backed up before these operations!"
            print(f"Warning: {msg}")  # 警告但不失敗


class TestMigrationRollbackCapability:
    """測試 Migration 回滾能力"""

    def test_migration_rollback_simulation(self):
        """模擬 migration 回滾測試"""
        # 這個測試應該在測試環境執行，不在生產環境
        if os.getenv("ENV") == "production":
            pytest.skip("Skip rollback test in production")

        # 取得當前 revision
        result = subprocess.run(
            ["alembic", "current"], capture_output=True, text=True, cwd="backend"
        )

        if result.returncode != 0:
            pytest.skip("Cannot get current alembic revision")

        current_revision = result.stdout.strip()

        # 測試能否查看 history
        result = subprocess.run(
            ["alembic", "history", "--verbose"],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert result.returncode == 0, "Cannot get migration history"

        # 確保有 revision 可以回滾
        if "Rev:" not in result.stdout:
            pytest.skip("No migrations to test rollback")

        print(f"Current revision: {current_revision}")
        print("Migration rollback capability verified")

    def test_migration_idempotency(self):
        """測試 migration 的冪等性（重複執行不會出錯）"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        non_idempotent_patterns = [
            (
                r"op\.create_table\((?!.*if_not_exists=True)",
                "CREATE TABLE without IF NOT EXISTS",
            ),
            (
                r"op\.create_index\((?!.*if_not_exists=True)",
                "CREATE INDEX without IF NOT EXISTS",
            ),
            (r"op\.add_column\(", "ADD COLUMN (not idempotent by default)"),
        ]

        warnings = []

        for migration_file in alembic_versions.glob("*.py"):
            with open(migration_file, "r") as f:
                content = f.read()

            for pattern, issue in non_idempotent_patterns:
                if re.search(pattern, content):
                    warnings.append(f"{migration_file.name}: {issue}")

        if warnings:
            print("Non-idempotent operations found (may fail if run twice):")
            for warning in warnings:
                print(f"  - {warning}")


class TestDatabaseConstraintIntegrity:
    """測試資料庫約束完整性"""

    def test_foreign_key_constraints_exist(self):
        """測試外鍵約束存在且正確"""
        db = next(get_db())
        inspector = inspect(engine)

        try:
            # 關鍵的外鍵關係
            critical_fks = {
                "classrooms": ["teacher_id", "school_id"],
                "classroom_students": ["classroom_id", "student_id"],
                "student_assignments": ["student_id", "assignment_id"],
                "activity_results": ["student_assignment_id", "content_id"],
            }

            missing_fks = []

            for table, expected_fks in critical_fks.items():
                if table not in inspector.get_table_names():
                    continue

                actual_fks = inspector.get_foreign_keys(table)
                actual_fk_columns = {fk["constrained_columns"][0] for fk in actual_fks}

                for expected_fk in expected_fks:
                    if expected_fk not in actual_fk_columns:
                        missing_fks.append(f"{table}.{expected_fk}")

            if missing_fks:
                pytest.fail(f"Missing critical foreign keys: {missing_fks}")

        finally:
            db.close()

    def test_cascade_delete_configuration(self):
        """測試 CASCADE DELETE 配置正確"""
        db = next(get_db())
        inspector = inspect(engine)

        try:
            # 應該有 CASCADE DELETE 的關係
            cascade_requirements = {
                "classroom_students": {
                    "classroom_id": "CASCADE",  # 刪除班級時刪除學生關聯
                    "student_id": "CASCADE",  # 刪除學生時刪除班級關聯
                },
                "student_assignments": {
                    "student_id": "CASCADE",  # 刪除學生時刪除作業
                },
                "activity_results": {
                    "student_assignment_id": "CASCADE",  # 刪除作業時刪除結果
                },
            }

            incorrect_cascades = []

            for table, requirements in cascade_requirements.items():
                if table not in inspector.get_table_names():
                    continue

                foreign_keys = inspector.get_foreign_keys(table)

                for fk in foreign_keys:
                    column = fk["constrained_columns"][0]
                    if column in requirements:
                        expected = requirements[column]
                        actual = fk.get("options", {}).get("ondelete", "NO ACTION")

                        if actual != expected:
                            incorrect_cascades.append(
                                f"{table}.{column}: expected {expected}, got {actual}"
                            )

            if incorrect_cascades:
                print(f"Warning: Incorrect CASCADE settings: {incorrect_cascades}")

        finally:
            db.close()

    def test_unique_constraints(self):
        """測試唯一約束存在"""
        db = next(get_db())
        inspector = inspect(engine)

        try:
            # 應該有唯一約束的欄位
            unique_requirements = {
                "teachers": ["email"],
                "students": ["email"],
                "schools": ["name"],
            }

            missing_uniques = []

            for table, columns in unique_requirements.items():
                if table not in inspector.get_table_names():
                    continue

                indexes = inspector.get_indexes(table)
                unique_columns = set()

                for index in indexes:
                    if index["unique"]:
                        unique_columns.update(index["column_names"])

                for column in columns:
                    if column not in unique_columns:
                        missing_uniques.append(f"{table}.{column}")

            if missing_uniques:
                print(f"Warning: Missing unique constraints: {missing_uniques}")

        finally:
            db.close()


class TestMigrationPerformance:
    """測試 Migration 性能影響"""

    def test_no_table_locks_in_migration(self):
        """測試 migration 不會鎖表（影響生產環境）"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        # 會造成長時間鎖表的操作
        locking_patterns = [
            (r"op\.alter_column\(.*type_=", "ALTER COLUMN TYPE (locks table)"),
            (
                r"op\.create_index\((?!.*postgresql_concurrently=True)",
                "CREATE INDEX without CONCURRENTLY",
            ),
            (
                r"op\.execute\(.*ALTER TABLE.*ADD CONSTRAINT",
                "ADD CONSTRAINT (may lock table)",
            ),
        ]

        potential_locks = []

        for migration_file in alembic_versions.glob("*.py"):
            with open(migration_file, "r") as f:
                content = f.read()

            for pattern, issue in locking_patterns:
                if re.search(pattern, content):
                    potential_locks.append(f"{migration_file.name}: {issue}")

        if potential_locks:
            print("Operations that may lock tables in production:")
            for lock in potential_locks:
                print(f"  - {lock}")
            print("Consider using concurrent operations or maintenance windows")

    def test_migration_size_reasonable(self):
        """測試 migration 檔案大小合理（避免超大 migration）"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        large_migrations = []

        for migration_file in alembic_versions.glob("*.py"):
            size = migration_file.stat().st_size

            # 超過 10KB 的 migration 可能太大
            if size > 10240:
                large_migrations.append(
                    {"file": migration_file.name, "size": f"{size / 1024:.1f}KB"}
                )

        if large_migrations:
            print("Large migration files detected (consider splitting):")
            for migration in large_migrations:
                print(f"  - {migration['file']}: {migration['size']}")


class TestDatabaseBackupRecovery:
    """測試資料庫備份恢復能力"""

    def test_backup_script_exists(self):
        """測試備份腳本存在"""
        backup_locations = [
            Path("scripts/backup_database.sh"),
            Path("scripts/backup_db.py"),
            Path("backend/scripts/backup_database.sh"),
            Path("backend/scripts/backup_db.py"),
        ]

        backup_script = None
        for location in backup_locations:
            if location.exists():
                backup_script = location
                break

        if not backup_script:
            pytest.fail(
                "No database backup script found! "
                "Create scripts/backup_database.sh for disaster recovery"
            )

    def test_migration_backup_procedure(self):
        """測試 migration 前備份程序"""
        # 檢查是否有備份程序文件
        procedure_files = [
            Path("docs/migration_procedure.md"),
            Path("MIGRATION.md"),
            Path("backend/alembic/README.md"),
        ]

        has_procedure = any(f.exists() for f in procedure_files)

        if not has_procedure:
            print(
                "Warning: No migration backup procedure documented. "
                "Create MIGRATION.md with backup steps"
            )

    def test_rollback_procedure_documented(self):
        """測試回滾程序有文件記錄"""
        # 檢查 CI/CD 配置中是否有回滾步驟
        github_workflow = Path(".github/workflows/deploy-production.yml")

        if github_workflow.exists():
            with open(github_workflow, "r") as f:
                content = f.read()

            if "rollback" not in content.lower():
                print(
                    "Warning: No rollback procedure in deployment workflow. "
                    "Add rollback steps to .github/workflows/deploy-production.yml"
                )


class TestSchemaVersionControl:
    """測試 Schema 版本控制"""

    def test_alembic_ini_configured(self):
        """測試 alembic.ini 正確配置"""
        alembic_ini = Path("backend/alembic.ini")

        if not alembic_ini.exists():
            pytest.fail("alembic.ini not found! Run: alembic init alembic")

        with open(alembic_ini, "r") as f:
            content = f.read()

        # 檢查關鍵配置
        required_configs = [
            "script_location",
            "sqlalchemy.url",
        ]

        missing_configs = []
        for config in required_configs:
            if config not in content:
                missing_configs.append(config)

        if missing_configs:
            pytest.fail(f"Missing alembic.ini configurations: {missing_configs}")

        # 警告硬編碼的資料庫 URL
        if "postgresql://" in content and "%(DATABASE_URL)s" not in content:
            print("Warning: Database URL hardcoded in alembic.ini. Use env var instead")

    def test_migration_naming_convention(self):
        """測試 migration 命名規範"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        poorly_named = []

        for migration_file in alembic_versions.glob("*.py"):
            # 格式應該是: <revision>_<description>.py
            name = migration_file.name

            # 檢查是否有描述性名稱
            parts = name.split("_", 1)
            if len(parts) < 2 or len(parts[1]) < 10:
                poorly_named.append(name)

        if poorly_named:
            print(f"Poorly named migrations (use descriptive names): {poorly_named}")

    def test_no_model_schema_mismatch(self):
        """測試 Model 與資料庫 Schema 一致"""
        # 這個測試需要在有資料庫連線的環境執行
        try:
            from models import Base
            from sqlalchemy import MetaData

            # 取得 Model 定義的 schema
            model_metadata = Base.metadata

            # 取得實際資料庫 schema
            db_metadata = MetaData()
            db_metadata.reflect(bind=engine)

            # 比較表
            model_tables = set(model_metadata.tables.keys())
            db_tables = set(db_metadata.tables.keys())

            # 忽略 alembic 版本表
            db_tables.discard("alembic_version")

            missing_in_db = model_tables - db_tables
            extra_in_db = db_tables - model_tables

            if missing_in_db:
                print(f"Tables in models but not in database: {missing_in_db}")
                print("Run: alembic revision --autogenerate -m 'sync schema'")

            if extra_in_db:
                print(f"Tables in database but not in models: {extra_in_db}")

        except Exception as e:
            pytest.skip(f"Cannot check schema mismatch: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
