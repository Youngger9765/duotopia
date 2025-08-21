#!/bin/bash

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 監控 GitHub Actions 狀態${NC}"
echo "================================"

# 取得最新的 run
latest_run=$(gh run list --limit 1 --json databaseId,status,name,workflowName | jq -r '.[0]')
run_id=$(echo $latest_run | jq -r '.databaseId')
status=$(echo $latest_run | jq -r '.status')
name=$(echo $latest_run | jq -r '.name')
workflow=$(echo $latest_run | jq -r '.workflowName')

echo -e "📋 最新的 Workflow Run:"
echo -e "   ID: ${YELLOW}$run_id${NC}"
echo -e "   名稱: $name"
echo -e "   Workflow: $workflow"
echo ""

# 監控直到完成
while [ "$status" = "in_progress" ] || [ "$status" = "queued" ]; do
    echo -ne "\r⏳ 狀態: ${YELLOW}$status${NC} - $(date '+%H:%M:%S')"
    sleep 5
    
    latest_run=$(gh run list --limit 1 --json databaseId,status | jq -r '.[0]')
    status=$(echo $latest_run | jq -r '.status')
done

echo ""
echo ""

# 顯示最終結果
if [ "$status" = "completed" ]; then
    # 取得結論
    conclusion=$(gh run view $run_id --json conclusion | jq -r '.conclusion')
    
    if [ "$conclusion" = "success" ]; then
        echo -e "${GREEN}✅ Workflow 成功完成！${NC}"
    else
        echo -e "${RED}❌ Workflow 失敗 (結論: $conclusion)${NC}"
        echo ""
        echo "查看錯誤詳情："
        echo "gh run view $run_id --log | less"
        echo ""
        echo "或在瀏覽器中查看："
        echo "gh run view $run_id --web"
    fi
else
    echo -e "${RED}❌ Workflow 狀態異常: $status${NC}"
fi

echo ""
echo "📊 最近的 Workflow 運行："
gh run list --limit 5

echo ""
echo "💡 提示："
echo "- 查看特定 job 的日誌: gh run view $run_id --log --job [job-id]"
echo "- 重新運行失敗的 jobs: gh run rerun $run_id --failed"
echo "- 查看所有 secrets: gh secret list"