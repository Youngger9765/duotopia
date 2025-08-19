#!/bin/bash

echo "🧪 開始執行 E2E 測試..."
echo "請確保前端 (http://localhost:5174) 和後端 (http://localhost:8000) 都在運行中"
echo ""

# 安裝 playwright 如果還沒安裝
if ! pip show playwright > /dev/null 2>&1; then
    echo "📦 安裝 Playwright..."
    pip install playwright pytest-playwright
    playwright install chromium
fi

# 執行測試
echo "🚀 執行 InstitutionManagement 測試..."
cd /Users/young/project/duotopia/backend
python3 -m pytest tests/e2e/test_institution_management.py -v -s

echo ""
echo "✅ 測試完成！"