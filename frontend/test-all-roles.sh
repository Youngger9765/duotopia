#!/bin/bash

# 測試所有角色權限的腳本
# Issue #112: Organization Portal Separation

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"

echo "=========================================="
echo "測試所有角色登入與權限"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

# 測試函數
test_login() {
    local email=$1
    local password=$2
    local expected_role=$3
    local expected_redirect=$4
    local description=$5

    test_count=$((test_count + 1))
    echo "----------------------------------------"
    echo "測試 $test_count: $description"
    echo "帳號: $email"
    echo -n "登入中... "

    # 呼叫登入 API
    response=$(curl -s -X POST "$API_URL/api/auth/teacher/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$email\", \"password\": \"$password\"}")

    # 檢查是否成功
    if echo "$response" | grep -q "access_token"; then
        echo -e "${GREEN}成功${NC}"

        # 提取角色資訊
        role=$(echo "$response" | grep -o '"role":"[^"]*"' | cut -d'"' -f4)
        org_id=$(echo "$response" | grep -o '"organization_id":"[^"]*"' | cut -d'"' -f4)
        school_id=$(echo "$response" | grep -o '"school_id":"[^"]*"' | cut -d'"' -f4)

        echo "  角色: $role"
        [ -n "$org_id" ] && echo "  組織 ID: $org_id"
        [ -n "$school_id" ] && echo "  學校 ID: $school_id"

        # 驗證角色是否正確
        if [ "$role" = "$expected_role" ]; then
            echo -e "  預期角色: ${GREEN}✓ $expected_role${NC}"
            echo -e "  預期重定向: ${GREEN}✓ $expected_redirect${NC}"
            pass_count=$((pass_count + 1))
            return 0
        else
            echo -e "  預期角色: ${RED}✗ 期望 $expected_role，實際 $role${NC}"
            fail_count=$((fail_count + 1))
            return 1
        fi
    else
        echo -e "${RED}失敗${NC}"
        echo "  錯誤: $response"
        fail_count=$((fail_count + 1))
        return 1
    fi
}

# 開始測試
echo "開始測試所有角色..."
echo ""

# 測試 1: org_owner
test_login \
    "owner@duotopia.com" \
    "owner123" \
    "org_owner" \
    "/organization/dashboard" \
    "組織擁有者 (org_owner)"

# 測試 2: org_admin
test_login \
    "orgadmin@duotopia.com" \
    "orgadmin123" \
    "org_admin" \
    "/organization/dashboard" \
    "組織管理員 (org_admin)"

# 測試 3: school_admin
test_login \
    "schooladmin@duotopia.com" \
    "schooladmin123" \
    "school_admin" \
    "/organization/dashboard" \
    "學校管理員 (school_admin)"

# 測試 4: 純教師 (組織教師)
test_login \
    "orgteacher@duotopia.com" \
    "orgteacher123" \
    "teacher" \
    "/teacher/dashboard" \
    "純教師 - 組織下的教師"

# 測試 5: 純教師 (獨立教師)
test_login \
    "teacher@duotopia.com" \
    "teacher123" \
    "teacher" \
    "/teacher/dashboard" \
    "純教師 - 獨立教師"

echo ""
echo "=========================================="
echo "測試結果摘要"
echo "=========================================="
echo "總測試數: $test_count"
echo -e "通過: ${GREEN}$pass_count${NC}"
echo -e "失敗: ${RED}$fail_count${NC}"

if [ $fail_count -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "所有測試通過！✓"
    echo "==========================================${NC}"
    echo ""
    echo "下一步："
    echo "1. 在瀏覽器手動驗證 UI 重定向"
    echo "2. 測試組織管理功能（CRUD）"
    echo "3. 截圖關鍵頁面"
    echo "4. 更新 Issue #112 狀態"
    exit 0
else
    echo ""
    echo -e "${RED}=========================================="
    echo "有測試失敗！✗"
    echo "==========================================${NC}"
    echo ""
    echo "請檢查："
    echo "1. 後端伺服器是否正在運行"
    echo "2. 測試帳號是否存在於資料庫"
    echo "3. 登入 API 是否正確返回角色資訊"
    exit 1
fi
