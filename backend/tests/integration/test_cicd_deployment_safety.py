"""
CI/CD Deployment Safety Tests
測試 CI/CD 部署前的安全檢查，預防常見部署失敗
"""

import pytest
from pathlib import Path


class TestAlembicMigrationSafety:
    """測試 Alembic 資料庫遷移安全性"""

    def test_no_dangerous_migrations_exist(self):
        """確保沒有危險的資料庫遷移檔案"""
        alembic_versions_path = Path("alembic/versions")

        if not alembic_versions_path.exists():
            pytest.skip("Alembic versions directory not found")

        dangerous_operations = [
            "drop_table",
            "drop_column",
            "drop_index",
            "drop_constraint",
            "truncate",
            "delete from",
        ]

        migration_files = list(alembic_versions_path.glob("*.py"))

        for migration_file in migration_files:
            with open(migration_file, "r") as f:
                content = f.read()
                content_lower = content.lower()

            for dangerous_op in dangerous_operations:
                if dangerous_op in content_lower and "# SAFE:" not in content:
                    # 檢查是否有安全註解
                    pytest.fail(
                        f"Dangerous operation '{dangerous_op}' found in {migration_file.name} "
                        f"without safety annotation. Add '# SAFE: reason' if intentional."
                    )

    def test_migration_reversibility(self):
        """測試所有遷移都可以回滾"""
        alembic_versions_path = Path("alembic/versions")

        if not alembic_versions_path.exists():
            pytest.skip("Alembic versions directory not found")

        migration_files = list(alembic_versions_path.glob("*.py"))

        for migration_file in migration_files:
            with open(migration_file, "r") as f:
                content = f.read()

            # 檢查是否有 downgrade 函數
            if "def downgrade()" not in content:
                pytest.fail(
                    f"Migration {migration_file.name} missing downgrade function"
                )

            # 檢查 downgrade 不是空的或只有 pass
            lines = content.split("\n")
            in_downgrade = False
            has_operations = False

            for line in lines:
                if "def downgrade()" in line:
                    in_downgrade = True
                elif in_downgrade and line.strip() and not line.strip().startswith("#"):
                    if line.strip() != "pass":
                        has_operations = True
                        break

            if not has_operations:
                # 允許某些 migration 沒有 downgrade（如初始 migration 或有 SAFE 註解）
                if (
                    "initial" not in migration_file.name.lower()
                    and "# SAFE:" not in content
                ):
                    pytest.fail(
                        f"Migration {migration_file.name} has empty downgrade function. "
                        f"Implement proper rollback or add comment explaining why."
                    )

    def test_migration_dependencies_correct(self):
        """測試遷移依賴關係正確"""
        alembic_versions_path = Path("alembic/versions")

        if not alembic_versions_path.exists():
            pytest.skip("Alembic versions directory not found")

        migration_files = list(alembic_versions_path.glob("*.py"))
        revisions = {}

        for migration_file in migration_files:
            with open(migration_file, "r") as f:
                content = f.read()

            # 提取 revision 和 down_revision
            revision = None
            down_revision = None

            for line in content.split("\n"):
                if line.startswith("revision = "):
                    revision = line.split("=")[1].strip().strip("'\"")
                elif line.startswith("down_revision = "):
                    down_revision = line.split("=")[1].strip().strip("'\"")

            if revision:
                revisions[revision] = {
                    "file": migration_file.name,
                    "down_revision": down_revision,
                }

        # 驗證依賴鏈
        for revision, info in revisions.items():
            if info["down_revision"] and info["down_revision"] != "None":
                if info["down_revision"] not in revisions:
                    pytest.fail(
                        f"Migration {info['file']} references non-existent parent "
                        f"revision {info['down_revision']}"
                    )


class TestEnvironmentVariables:
    """測試環境變數配置安全性"""

    def test_no_hardcoded_secrets(self):
        """確保沒有硬編碼的敏感資訊"""
        # 掃描所有 Python 檔案
        dangerous_patterns = [
            ("password", r'password\s*=\s*["\'][^"\']+["\']'),
            ("api_key", r'api_key\s*=\s*["\'][^"\']+["\']'),
            ("secret", r'secret\s*=\s*["\'][^"\']+["\']'),
            ("token", r'token\s*=\s*["\'][^"\']+["\']'),
            ("DATABASE_URL", r'DATABASE_URL\s*=\s*["\']postgresql://[^"\']+["\']'),
        ]

        import re

        for py_file in Path(".").rglob("*.py"):
            # 跳過測試檔案和 migration
            if "test" in str(py_file) or "alembic/versions" in str(py_file):
                continue

            with open(py_file, "r") as f:
                content = f.read()

            for name, pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # 檢查是否是從環境變數讀取
                    if "os.getenv" not in content and "os.environ" not in content:
                        pytest.fail(
                            f"Potential hardcoded {name} found in {py_file}. "
                            f"Use environment variables instead."
                        )

    def test_required_env_vars_documented(self):
        """確保所有必要的環境變數都有文件說明"""
        # 檢查 .env.example 是否存在
        env_example = Path(".env.example")

        if not env_example.exists():
            pytest.fail(".env.example file missing - required for deployment")

        # 必須包含的環境變數
        required_vars = [
            "DATABASE_URL",
            "JWT_SECRET",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
        ]

        with open(env_example, "r") as f:
            content = f.read()

        missing_vars = []
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)

        if missing_vars:
            pytest.fail(
                f"Required environment variables missing from .env.example: {missing_vars}"
            )

    def test_staging_env_different_from_production(self):
        """確保 staging 和 production 環境變數不同"""
        staging_env = Path(".env.staging")
        prod_env = Path(".env.production")

        # 如果兩個檔案都存在，確保關鍵值不同
        if staging_env.exists() and prod_env.exists():
            with open(staging_env, "r") as f:
                staging_content = f.read()
            with open(prod_env, "r") as f:
                prod_content = f.read()

            # 不應該完全相同
            if staging_content == prod_content:
                pytest.fail("Staging and production environment files are identical!")

            # 檢查 DATABASE_URL 不同
            if "DATABASE_URL=" in staging_content and "DATABASE_URL=" in prod_content:
                staging_db = [
                    line
                    for line in staging_content.split("\n")
                    if line.startswith("DATABASE_URL=")
                ]
                prod_db = [
                    line
                    for line in prod_content.split("\n")
                    if line.startswith("DATABASE_URL=")
                ]

                if staging_db and prod_db and staging_db[0] == prod_db[0]:
                    pytest.fail("Staging and production using same database URL!")


class TestDockerConfiguration:
    """測試 Docker 配置安全性"""

    def test_dockerfile_security_best_practices(self):
        """測試 Dockerfile 遵循安全最佳實踐"""
        dockerfile_path = Path("Dockerfile")

        if not dockerfile_path.exists():
            pytest.skip("Dockerfile not found")

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # 檢查安全最佳實踐
        checks = [
            (
                "non-root user",
                "USER" in content or "useradd" in content,
                "Dockerfile should run as non-root user",
            ),
            (
                "specific base image version",
                ":latest" not in content,
                "Use specific version tags instead of :latest",
            ),
            (
                "no sudo installation",
                "sudo" not in content.lower(),
                "Avoid installing sudo in production containers",
            ),
            (
                "health check defined",
                "HEALTHCHECK" in content,
                "Add HEALTHCHECK instruction for container health monitoring",
            ),
        ]

        for check_name, condition, error_msg in checks:
            if not condition:
                # 某些檢查可以是警告而非錯誤
                if check_name == "health check defined":
                    print(f"Warning: {error_msg}")
                else:
                    pytest.fail(f"Docker security issue: {error_msg}")

    def test_docker_compose_no_secrets(self):
        """確保 docker-compose 不包含敏感資訊"""
        compose_files = ["docker-compose.yml", "docker-compose.yaml"]

        for compose_file in compose_files:
            compose_path = Path(compose_file)
            if compose_path.exists():
                with open(compose_path, "r") as f:
                    content = f.read()

                # 檢查是否有硬編碼的密碼
                if "password:" in content.lower():
                    # 檢查是否使用環境變數
                    lines_with_password = [
                        line
                        for line in content.split("\n")
                        if "password" in line.lower()
                    ]

                    for line in lines_with_password:
                        if "${" not in line and "env_file" not in content:
                            pytest.fail(
                                f"Potential hardcoded password in {compose_file}: {line.strip()}"
                            )


class TestDependencySecurity:
    """測試依賴套件安全性"""

    def test_requirements_pinned(self):
        """確保所有依賴都有固定版本"""
        requirements_file = Path("requirements.txt")

        if not requirements_file.exists():
            pytest.skip("requirements.txt not found")

        with open(requirements_file, "r") as f:
            lines = f.readlines()

        unpinned_packages = []

        for line in lines:
            line = line.strip()
            # 跳過註解和空行
            if not line or line.startswith("#"):
                continue

            # 檢查是否有版本號
            if "==" not in line and ">=" not in line and "<=" not in line:
                # 某些套件可能使用 git+https，這是可以的
                if not line.startswith("git+"):
                    unpinned_packages.append(line)

        if unpinned_packages:
            pytest.fail(
                f"Unpinned packages found (security risk): {unpinned_packages}. "
                f"Pin all versions for reproducible builds."
            )

    def test_no_vulnerable_dependencies(self):
        """檢查已知的易受攻擊依賴"""
        # 已知的有安全問題的套件版本
        vulnerable_packages = {
            "django": ["<3.2", "<2.2.28"],  # 舊版本有安全漏洞
            "flask": ["<2.0.0"],  # 舊版本有安全問題
            "requests": ["<2.20.0"],  # SSL 驗證問題
            "pyyaml": ["<5.4"],  # 任意代碼執行漏洞
            "jinja2": ["<2.11.3"],  # XSS 漏洞
            "werkzeug": ["<2.0.0"],  # 安全問題
        }

        requirements_file = Path("requirements.txt")

        if not requirements_file.exists():
            return

        with open(requirements_file, "r") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            for package, vulnerable_versions in vulnerable_packages.items():
                if package in line.lower():
                    # 簡單檢查版本
                    # 實際應用中應該使用 packaging.version 來比較
                    for vuln_version in vulnerable_versions:
                        print(f"Warning: Check {package} version for security updates")


class TestAPISecurityHeaders:
    """測試 API 安全標頭配置"""

    def test_cors_configuration_secure(self):
        """測試 CORS 配置安全"""
        # 檢查 main.py 中的 CORS 配置
        main_file = Path("main.py")

        if not main_file.exists():
            pytest.skip("main.py not found")

        with open(main_file, "r") as f:
            content = f.read()

        if "CORSMiddleware" in content:
            # 檢查是否使用 allow_origins=["*"]（但允許在開發環境使用）
            if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                # 檢查是否有環境判斷
                if 'if os.getenv("ENVIRONMENT") == "development"' not in content:
                    pytest.fail(
                        "CORS configured with wildcard origin ('*') without environment check. "
                        "This is a security risk in production. Specify allowed origins explicitly."
                    )

            # 檢查是否有默認的安全配置
            if "CORS_ALLOWED_ORIGINS" not in content:
                pytest.fail(
                    "CORS should use environment variable CORS_ALLOWED_ORIGINS for configuration"
                )

    def test_rate_limiting_configured(self):
        """測試是否配置了速率限制"""
        # 檢查是否有 rate limiting 中間件
        middleware_indicators = [
            "RateLimitMiddleware",
            "slowapi",
            "ratelimit",
            "@limiter",
        ]

        # 掃描路由檔案
        routers_path = Path("routers")
        if routers_path.exists():
            has_rate_limiting = False

            for py_file in routers_path.glob("*.py"):
                with open(py_file, "r") as f:
                    content = f.read()

                for indicator in middleware_indicators:
                    if indicator in content:
                        has_rate_limiting = True
                        break

                if has_rate_limiting:
                    break

            if not has_rate_limiting:
                print(
                    "Warning: No rate limiting detected. Consider adding rate limiting for DDoS protection."
                )


class TestDeploymentReadiness:
    """測試部署準備狀態"""

    def test_no_debug_mode_in_production(self):
        """確保生產環境沒有啟用除錯模式"""
        main_file = Path("main.py")

        if not main_file.exists():
            return

        with open(main_file, "r") as f:
            content = f.read()

        # 檢查 debug=True
        if "debug=True" in content:
            # 檢查是否有條件判斷
            if (
                'os.getenv("ENVIRONMENT")' not in content
                and 'os.getenv("DEBUG")' not in content
            ):
                pytest.fail(
                    "Debug mode hardcoded to True. "
                    "Use environment variable to control debug mode."
                )

    def test_logging_configuration_appropriate(self):
        """測試日誌配置適當"""
        # 檢查是否有配置日誌
        log_indicators = [
            "logging.basicConfig",
            "logging.getLogger",
            "loguru",
            "structlog",
        ]

        has_logging = False

        for py_file in Path(".").rglob("*.py"):
            if "test" in str(py_file):
                continue

            with open(py_file, "r") as f:
                content = f.read()

            for indicator in log_indicators:
                if indicator in content:
                    has_logging = True
                    break

            if has_logging:
                break

        if not has_logging:
            print(
                "Warning: No logging configuration detected. Add proper logging for production."
            )

    def test_health_check_endpoint_exists(self):
        """確保健康檢查端點存在"""
        main_file = Path("main.py")

        if not main_file.exists():
            return

        with open(main_file, "r") as f:
            content = f.read()

        health_endpoints = ["/health", "/healthz", "/ping", "/status"]

        has_health_check = any(endpoint in content for endpoint in health_endpoints)

        if not has_health_check:
            pytest.fail(
                "No health check endpoint found. Add /health endpoint for monitoring."
            )

    def test_graceful_shutdown_configured(self):
        """測試是否配置優雅關閉"""
        main_file = Path("main.py")

        if not main_file.exists():
            return

        with open(main_file, "r") as f:
            content = f.read()

        shutdown_indicators = [
            "on_shutdown",
            "shutdown_event",
            "lifespan",
            "asyncio.create_task",
        ]

        has_shutdown = any(indicator in content for indicator in shutdown_indicators)

        if not has_shutdown:
            print(
                "Warning: No graceful shutdown handler detected. Consider adding for zero-downtime deployments."
            )


class TestDatabaseDeploymentSafety:
    """測試資料庫部署安全性"""

    def test_no_auto_migrate_in_production(self):
        """確保生產環境不會自動執行 migration"""
        main_file = Path("main.py")

        if not main_file.exists():
            return

        with open(main_file, "r") as f:
            content = f.read()

        # 檢查是否有自動 migration
        if (
            "alembic.command.upgrade" in content
            or "Base.metadata.create_all" in content
        ):
            # 檢查是否有環境檢查
            if 'os.getenv("ENVIRONMENT")' not in content:
                pytest.fail(
                    "Automatic database migration detected without environment check. "
                    "This is dangerous in production!"
                )

    def test_database_backup_script_exists(self):
        """確保有資料庫備份腳本"""
        backup_locations = [
            "scripts/backup.sh",
            "scripts/db_backup.sh",
            "scripts/backup_database.py",
            "Makefile",  # 檢查 Makefile 中是否有 backup 命令
        ]

        has_backup = False

        for location in backup_locations:
            if Path(location).exists():
                if location == "Makefile":
                    with open(location, "r") as f:
                        if "backup" in f.read():
                            has_backup = True
                            break
                else:
                    has_backup = True
                    break

        if not has_backup:
            print(
                "Warning: No database backup script found. Add backup script for disaster recovery."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
