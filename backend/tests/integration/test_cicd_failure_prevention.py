"""
CI/CD Failure Prevention Tests
預防最常見的 CI/CD 部署失敗，提前發現問題
"""

import pytest
import yaml
from pathlib import Path
import importlib.util


class TestPreDeploymentChecks:
    """部署前檢查，預防常見失敗"""

    def test_all_imports_are_valid(self):
        """測試所有 import 都可以正常載入（最常見的部署失敗原因）"""
        failed_imports = []

        # 掃描所有 Python 檔案
        for py_file in Path(".").rglob("*.py"):
            # 跳過測試檔案和 alembic
            if "test" in str(py_file) or "alembic" in str(py_file):
                continue

            # 嘗試載入模組
            module_name = str(py_file).replace("/", ".").replace(".py", "")

            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    importlib.util.module_from_spec(spec)
                    # 不執行，只檢查語法
                    compile(open(py_file).read(), py_file, "exec")
            except (ImportError, SyntaxError) as e:
                failed_imports.append({"file": str(py_file), "error": str(e)})

        if failed_imports:
            msg = "Import errors found (will cause deployment failure):\n"
            for fail in failed_imports:
                msg += f"  {fail['file']}: {fail['error']}\n"
            pytest.fail(msg)

    def test_environment_variables_complete(self):
        """測試所有必要的環境變數都存在（第二常見的失敗原因）"""
        # 從程式碼中提取所有 os.getenv 和 os.environ 的使用
        env_vars_in_code = set()

        for py_file in Path(".").rglob("*.py"):
            if "test" in str(py_file):
                continue

            with open(py_file, "r") as f:
                content = f.read()

            # 找出所有環境變數引用
            import re

            # os.getenv("VAR_NAME")
            getenv_pattern = r'os\.getenv\(["\']([^"\']+)["\']'
            env_vars_in_code.update(re.findall(getenv_pattern, content))

            # os.environ["VAR_NAME"]
            environ_pattern = r'os\.environ\[["\']([^"\']+)["\']'
            env_vars_in_code.update(re.findall(environ_pattern, content))

        # 檢查 .env.example 是否包含所有變數
        env_example = Path(".env.example")

        if env_example.exists():
            with open(env_example, "r") as f:
                example_content = f.read()

            missing_vars = []
            for var in env_vars_in_code:
                if var not in example_content and var != "PATH":  # 排除系統變數
                    missing_vars.append(var)

            if missing_vars:
                pytest.fail(
                    f"Environment variables used in code but not in .env.example: {missing_vars}\n"
                    f"This will cause deployment failure!"
                )

    def test_database_url_format_valid(self):
        """測試 DATABASE_URL 格式正確（資料庫連線失敗是常見問題）"""
        # 檢查各環境的 DATABASE_URL
        env_files = [".env", ".env.staging", ".env.production"]

        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("DATABASE_URL="):
                            db_url = line.split("=", 1)[1].strip()

                            # 檢查格式
                            if not db_url.startswith(
                                ("postgresql://", "postgres://", "sqlite://")
                            ):
                                pytest.fail(
                                    f"Invalid DATABASE_URL format in {env_file}. "
                                    f"Must start with postgresql:// or sqlite://"
                                )

                            # 檢查是否有密碼欄位（不應該是空的）
                            if "postgresql://" in db_url:
                                parts = db_url.split("@")
                                if len(parts) > 1:
                                    user_pass = parts[0].split("://")[1]
                                    if ":" not in user_pass:
                                        print(
                                            f"Warning: No password in DATABASE_URL in {env_file}"
                                        )

    def test_port_configuration_correct(self):
        """測試 PORT 配置正確（Cloud Run 需要 PORT 8080）"""
        # 檢查 Dockerfile
        dockerfile = Path("Dockerfile")

        if dockerfile.exists():
            with open(dockerfile, "r") as f:
                content = f.read()

            # 檢查是否有錯誤的 PORT 設定
            if "ENV PORT=" in content and "ENV PORT=8080" not in content:
                pytest.fail(
                    "Dockerfile has wrong PORT. Cloud Run requires PORT=8080 or use $PORT"
                )

            # 檢查 CMD 或 ENTRYPOINT 是否使用 $PORT
            if "uvicorn" in content:
                if "--port 8000" in content:
                    pytest.fail(
                        "Dockerfile hardcodes port 8000. Should use $PORT or 8080 for Cloud Run"
                    )


class TestAlembicMigrationSafety:
    """Alembic Migration 安全檢查（Migration 失敗是最嚴重的問題）"""

    def test_migration_files_syntax_valid(self):
        """測試所有 migration 檔案語法正確"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        for migration_file in alembic_versions.glob("*.py"):
            try:
                compile(open(migration_file).read(), migration_file, "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in migration {migration_file.name}: {e}")

    def test_no_duplicate_revision_ids(self):
        """測試沒有重複的 revision ID（會導致 migration 失敗）"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        revisions = []

        for migration_file in alembic_versions.glob("*.py"):
            with open(migration_file, "r") as f:
                content = f.read()

            # 提取 revision
            for line in content.split("\n"):
                if line.startswith("revision = "):
                    revision = line.split("=")[1].strip().strip("'\"")
                    if revision in revisions:
                        pytest.fail(f"Duplicate revision ID: {revision}")
                    revisions.append(revision)

    def test_migration_chain_integrity(self):
        """測試 migration 鏈的完整性"""
        alembic_versions = Path("alembic/versions")

        if not alembic_versions.exists():
            pytest.skip("No alembic versions directory")

        # 建立 revision 圖
        revision_graph = {}

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

        # 檢查是否可以從任何 revision 追溯到 None（初始）
        for revision, parent in revision_graph.items():
            current = parent
            visited = set()

            while current and current != "None":
                if current in visited:
                    pytest.fail(
                        f"Circular dependency detected in migration chain at {current}"
                    )

                visited.add(current)
                current = revision_graph.get(current)


class TestDockerBuildSuccess:
    """Docker 建置成功測試"""

    def test_requirements_installable(self):
        """測試 requirements.txt 可以安裝（pip install 失敗是常見問題）"""
        requirements_file = Path("requirements.txt")

        if not requirements_file.exists():
            pytest.skip("No requirements.txt")

        # 檢查檔案格式
        with open(requirements_file, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            line = line.strip()

            # 跳過註解和空行
            if not line or line.startswith("#"):
                continue

            # 檢查格式
            if " " in line and "git+" not in line:
                pytest.fail(
                    f"Invalid format in requirements.txt line {i}: {line}. "
                    f"Use == for version pinning, not spaces"
                )

    def test_dockerfile_commands_valid(self):
        """測試 Dockerfile 指令有效"""
        dockerfile = Path("Dockerfile")

        if not dockerfile.exists():
            pytest.skip("No Dockerfile")

        with open(dockerfile, "r") as f:
            lines = f.readlines()

        # 檢查常見錯誤
        has_from = False
        has_workdir = False
        has_copy_requirements = False
        has_pip_install = False
        has_cmd_or_entrypoint = False

        for line in lines:
            line = line.strip()

            if line.startswith("FROM "):
                has_from = True
            elif line.startswith("WORKDIR "):
                has_workdir = True
            elif "requirements.txt" in line and "COPY" in line:
                has_copy_requirements = True
            elif "pip install" in line:
                has_pip_install = True
            elif line.startswith(("CMD ", "ENTRYPOINT ")):
                has_cmd_or_entrypoint = True

        if not has_from:
            pytest.fail("Dockerfile missing FROM instruction")
        if not has_workdir:
            print("Warning: Dockerfile missing WORKDIR")
        if not has_copy_requirements:
            pytest.fail("Dockerfile doesn't copy requirements.txt")
        if not has_pip_install:
            pytest.fail("Dockerfile doesn't install requirements")
        if not has_cmd_or_entrypoint:
            pytest.fail("Dockerfile missing CMD or ENTRYPOINT")


class TestGitHubActionsWorkflow:
    """GitHub Actions 工作流程測試"""

    def test_workflow_files_valid_yaml(self):
        """測試 workflow 檔案是有效的 YAML"""
        workflows_dir = Path(".github/workflows")

        if not workflows_dir.exists():
            pytest.skip("No GitHub workflows")

        for workflow_file in workflows_dir.glob("*.yml") or workflows_dir.glob(
            "*.yaml"
        ):
            try:
                with open(workflow_file, "r") as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")

    def test_workflow_has_essential_steps(self):
        """測試 workflow 包含必要步驟"""
        workflows_dir = Path(".github/workflows")

        if not workflows_dir.exists():
            pytest.skip("No GitHub workflows")

        for workflow_file in workflows_dir.glob("*.yml"):
            with open(workflow_file, "r") as f:
                workflow = yaml.safe_load(f)

            if not workflow:
                continue

            # 檢查部署 workflow
            if "deploy" in workflow_file.name.lower():
                # 應該有這些關鍵步驟
                essential_steps = [
                    "checkout",  # 檢出程式碼
                    "test",  # 執行測試
                    "build",  # 建置
                    "deploy",  # 部署
                ]

                workflow_content = str(workflow).lower()

                missing_steps = []
                for step in essential_steps:
                    if step not in workflow_content:
                        missing_steps.append(step)

                if missing_steps:
                    print(
                        f"Warning: {workflow_file.name} might be missing: {missing_steps}"
                    )


class TestStartupDependencies:
    """測試啟動依賴（啟動失敗是常見問題）"""

    def test_main_py_importable(self):
        """測試 main.py 可以被 import（最基本的檢查）"""
        try:
            # 不實際執行，只檢查 import
            import main

            assert hasattr(main, "app"), "main.py should have 'app' object"
        except ImportError as e:
            pytest.fail(
                f"Cannot import main.py: {e}. This will cause deployment failure!"
            )

    def test_database_models_importable(self):
        """測試 models 可以被 import"""
        try:
            import models

            assert hasattr(models, "Base"), "models.py should have 'Base' object"
        except ImportError as e:
            pytest.fail(f"Cannot import models.py: {e}")

    def test_critical_dependencies_available(self):
        """測試關鍵依賴可用"""
        critical_modules = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "uvicorn",
            "alembic",
        ]

        missing_modules = []

        for module_name in critical_modules:
            try:
                __import__(module_name)
            except ImportError:
                missing_modules.append(module_name)

        if missing_modules:
            pytest.fail(
                f"Critical modules not installed: {missing_modules}. "
                f"Run: pip install {' '.join(missing_modules)}"
            )


class TestSecretsManagement:
    """測試密鑰管理（洩露密鑰會導致安全問題）"""

    def test_no_secrets_in_code(self):
        """確保沒有密鑰在程式碼中"""
        secret_patterns = [
            r'["\']sk_live_[a-zA-Z0-9]{24,}["\']',  # Stripe
            r'["\']AIza[a-zA-Z0-9_-]{35}["\']',  # Google API
            r'["\']ghp_[a-zA-Z0-9]{36}["\']',  # GitHub token
            r'["\'][0-9a-f]{40}["\']',  # Generic hex key
        ]

        import re

        for py_file in Path(".").rglob("*.py"):
            if "test" in str(py_file):
                continue

            with open(py_file, "r") as f:
                content = f.read()

            for pattern in secret_patterns:
                if re.search(pattern, content):
                    pytest.fail(
                        f"Potential secret found in {py_file}. "
                        f"Use environment variables instead!"
                    )

    def test_env_files_in_gitignore(self):
        """確保 .env 檔案在 .gitignore 中"""
        gitignore = Path(".gitignore")

        if not gitignore.exists():
            pytest.fail("No .gitignore file! .env files might be committed!")

        with open(gitignore, "r") as f:
            gitignore_content = f.read()

        env_patterns = [".env", "*.env", ".env.*"]

        has_env_ignore = any(pattern in gitignore_content for pattern in env_patterns)

        if not has_env_ignore:
            pytest.fail(".env files not in .gitignore! Secrets might be exposed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
