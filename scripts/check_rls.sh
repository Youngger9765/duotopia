#!/bin/bash
# RLS 安全檢查腳本
# 檢查 Supabase 資料庫中哪些表沒有啟用 RLS

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 檢查 Supabase RLS 配置..."

# 檢查環境變數
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ 錯誤：DATABASE_URL 環境變數未設定${NC}"
    echo "請執行："
    echo "  export DATABASE_URL=\$STAGING_SUPABASE_POOLER_URL"
    echo "  或"
    echo "  export DATABASE_URL=\$PRODUCTION_SUPABASE_POOLER_URL"
    exit 1
fi

# 1️⃣ 檢查沒有啟用 RLS 的表
echo ""
echo "1️⃣ 檢查未啟用 RLS 的資料表..."
TABLES_WITHOUT_RLS=$(psql "$DATABASE_URL" -t -c "
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
      AND NOT rowsecurity
      AND tablename != 'alembic_version'
    ORDER BY tablename;
" | xargs)

if [ -z "$TABLES_WITHOUT_RLS" ]; then
    echo -e "${GREEN}✅ 所有業務資料表都已啟用 RLS${NC}"
else
    echo -e "${RED}❌ 以下資料表未啟用 RLS：${NC}"
    for table in $TABLES_WITHOUT_RLS; do
        echo -e "${RED}   - $table${NC}"
    done
    HAS_ERROR=1
fi

# 2️⃣ 檢查啟用了 RLS 但沒有 Policy 的表
echo ""
echo "2️⃣ 檢查已啟用 RLS 但缺少 Policy 的資料表..."
TABLES_WITHOUT_POLICIES=$(psql "$DATABASE_URL" -t -c "
    SELECT t.tablename
    FROM pg_tables t
    WHERE t.schemaname = 'public'
      AND t.rowsecurity = true
      AND NOT EXISTS (
        SELECT 1 FROM pg_policies p
        WHERE p.tablename = t.tablename
      )
    ORDER BY t.tablename;
" | xargs)

if [ -z "$TABLES_WITHOUT_POLICIES" ]; then
    echo -e "${GREEN}✅ 所有啟用 RLS 的表都有 Policy${NC}"
else
    echo -e "${YELLOW}⚠️  以下資料表啟用了 RLS 但沒有 Policy：${NC}"
    for table in $TABLES_WITHOUT_POLICIES; do
        echo -e "${YELLOW}   - $table${NC}"
    done
    echo -e "${YELLOW}   注意：沒有 Policy 的表會拒絕所有存取${NC}"
    HAS_WARNING=1
fi

# 3️⃣ 顯示 RLS 狀態摘要
echo ""
echo "3️⃣ RLS 配置摘要..."
psql "$DATABASE_URL" -c "
    SELECT
        t.tablename,
        CASE WHEN t.rowsecurity THEN '✅' ELSE '❌' END as rls_enabled,
        COALESCE(p.policy_count, 0) as policies
    FROM pg_tables t
    LEFT JOIN (
        SELECT tablename, COUNT(*) as policy_count
        FROM pg_policies
        GROUP BY tablename
    ) p ON t.tablename = p.tablename
    WHERE t.schemaname = 'public'
      AND t.tablename != 'alembic_version'
    ORDER BY t.tablename;
"

# 4️⃣ 檢查結果
echo ""
if [ ! -z "$HAS_ERROR" ]; then
    echo -e "${RED}❌ RLS 檢查失敗：有資料表未啟用 RLS${NC}"
    echo ""
    echo "修復方法："
    echo "  1. 執行 backend/migrations/enable_rls_all_tables.sql"
    echo "  2. 或在 Alembic migration 中加入 RLS 啟用指令"
    exit 1
elif [ ! -z "$HAS_WARNING" ]; then
    echo -e "${YELLOW}⚠️  RLS 檢查通過但有警告${NC}"
    exit 0
else
    echo -e "${GREEN}✅ RLS 檢查全部通過${NC}"
    exit 0
fi
