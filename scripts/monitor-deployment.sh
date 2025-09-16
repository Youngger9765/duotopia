#!/bin/bash

# 監控 GitHub Actions 部署腳本
# 使用方式: ./scripts/monitor-deployment.sh

echo "🚀 監控部署中..."

# 獲取最新的 workflow run ID
RUN_ID=$(gh run list --workflow deploy-staging-supabase.yml --limit 1 --json databaseId -q '.[0].databaseId')

if [ -z "$RUN_ID" ]; then
    echo "❌ 找不到正在執行的部署"
    exit 1
fi

echo "📋 部署 ID: $RUN_ID"
echo "🔗 URL: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs/$RUN_ID"
echo ""

# 監控部署直到完成
gh run watch "$RUN_ID" --exit-status

# 檢查結果
if [ $? -eq 0 ]; then
    echo "✅ 部署成功!"
    echo ""
    echo "🌐 Staging URLs:"
    echo "   Frontend: https://duotopia-staging-lcmd2ianga-de.a.run.app"
    echo "   Backend: https://duotopia-backend-staging-lcmd2ianga-de.a.run.app"
    echo ""
    echo "📝 測試步驟:"
    echo "   1. 打開 Frontend URL"
    echo "   2. 檢查 /debug 頁面"
    echo "   3. 測試 AI 評估功能"
else
    echo "❌ 部署失敗! 請檢查錯誤:"
    gh run view "$RUN_ID" --log-failed
fi
