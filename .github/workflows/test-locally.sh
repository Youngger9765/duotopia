#!/bin/bash
# 本地測試 CI/CD 流程的腳本

set -e

echo "🧪 執行本地測試..."

# 後端測試
echo "📦 後端測試..."
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov
pytest tests/ -v --cov=. --cov-report=term || true
cd ..

# 前端測試
echo "📦 前端測試..."
npm ci
npm run typecheck
npm run build

echo "✅ 本地測試完成！"