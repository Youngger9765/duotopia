#!/bin/bash
# Setup pre-commit hooks for Duotopia project
# This ensures all code quality checks are enforced before commits

set -e

echo "🔧 設定 Duotopia pre-commit hooks..."

# 安裝 pre-commit
if ! command -v pre-commit &> /dev/null; then
    echo "📦 安裝 pre-commit..."
    pip install pre-commit
fi

# 安裝 git hooks
echo "🔗 安裝 git hooks..."
pre-commit install

# 設定為 fail fast（第一個錯誤就停止）
git config hooks.failFast true

# 執行初始檢查
echo "✅ 執行初始檢查..."
pre-commit run --all-files || true

echo "
✨ Pre-commit hooks 設定完成！

重要提醒：
- 每次 commit 前會自動執行以下檢查：
  ✓ Black (Python 格式化)
  ✓ Flake8 (Python linting)
  ✓ ESLint (TypeScript linting)
  ✓ TypeScript 編譯檢查
  ✓ 安全檢查（密碼、API keys 等）
  ✓ Alembic migration 檢查

- 如果任何檢查失敗，commit 會被阻止
- 絕對禁止使用 --no-verify 跳過檢查！

手動執行所有檢查：
  pre-commit run --all-files
"
