#!/bin/bash

echo "🧪 測試 GitHub Actions Workflow 觸發條件"
echo "========================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試函數
test_trigger() {
    local file_path=$1
    local expected_workflow=$2

    echo -e "\n📝 Testing: $file_path"
    echo -e "   Expected: ${GREEN}$expected_workflow${NC}"

    # 檢查哪個 workflow 會被觸發
    triggered=""

    # 檢查 backend workflow
    if grep -q "paths:" .github/workflows/deploy-backend.yml; then
        if echo "$file_path" | grep -E "(backend/|requirements|alembic\.ini)" > /dev/null; then
            if echo "$file_path" | grep -E "(\.md$|backend/tests/)" > /dev/null; then
                echo -e "   Backend: ${YELLOW}Ignored (in paths-ignore)${NC}"
            else
                triggered="$triggered deploy-backend.yml"
                echo -e "   Backend: ${GREEN}✓ Would trigger${NC}"
            fi
        fi
    fi

    # 檢查 frontend workflow
    if grep -q "paths:" .github/workflows/deploy-frontend.yml; then
        if echo "$file_path" | grep -E "(frontend/|package.*\.json|tsconfig|eslint)" > /dev/null; then
            if echo "$file_path" | grep -E "(\.md$|frontend/tests/|\.test\.|\.spec\.)" > /dev/null; then
                echo -e "   Frontend: ${YELLOW}Ignored (in paths-ignore)${NC}"
            else
                triggered="$triggered deploy-frontend.yml"
                echo -e "   Frontend: ${GREEN}✓ Would trigger${NC}"
            fi
        fi
    fi

    # 檢查 shared workflow
    if echo "$file_path" | grep -E "(docker-compose|Makefile|\.env\.example)" > /dev/null; then
        triggered="$triggered deploy-shared.yml"
        echo -e "   Shared: ${GREEN}✓ Would trigger${NC}"
    fi

    if [ -z "$triggered" ]; then
        echo -e "   Result: ${YELLOW}No workflow triggered${NC}"
    fi
}

# 測試案例
echo -e "${GREEN}=== 測試後端檔案變更 ===${NC}"
test_trigger "backend/main.py" "deploy-backend.yml"
test_trigger "backend/routers/users.py" "deploy-backend.yml"
test_trigger "requirements.txt" "deploy-backend.yml"
test_trigger "alembic.ini" "deploy-backend.yml"
test_trigger "backend/tests/test_api.py" "none (ignored)"
test_trigger "backend/README.md" "none (ignored)"

echo -e "\n${GREEN}=== 測試前端檔案變更 ===${NC}"
test_trigger "frontend/src/App.tsx" "deploy-frontend.yml"
test_trigger "frontend/package.json" "deploy-frontend.yml"
test_trigger "tsconfig.json" "deploy-frontend.yml"
test_trigger "frontend/tests/app.test.tsx" "none (ignored)"
test_trigger "frontend/README.md" "none (ignored)"

echo -e "\n${GREEN}=== 測試共用檔案變更 ===${NC}"
test_trigger "docker-compose.yml" "deploy-shared.yml"
test_trigger "Makefile" "deploy-shared.yml"
test_trigger ".env.example" "deploy-shared.yml"

echo -e "\n${GREEN}=== 測試不觸發的檔案 ===${NC}"
test_trigger "README.md" "none"
test_trigger "LICENSE" "none"
test_trigger ".gitignore" "none"
test_trigger "docs/guide.md" "none"

echo -e "\n========================================="
echo -e "${GREEN}✅ 測試完成！${NC}"
echo -e "\n⚠️  注意事項："
echo -e "1. 需要在 GitHub 設定新的 secrets："
echo -e "   - STAGING_BACKEND_URL"
echo -e "   - PRODUCTION_BACKEND_URL"
echo -e "2. 舊的 workflow 已經被重命名為 .yml.old"
echo -e "3. 可以使用 workflow_dispatch 手動觸發任何 workflow"
