#!/bin/bash

echo "🧪 執行 Duotopia 後端測試..."
echo "================================"

# 設置測試環境變數
export DATABASE_URL="sqlite:///:memory:"
export SECRET_KEY="test-secret-key"
export TESTING=true

# 執行不同類型的測試
echo "📋 執行基礎認證測試..."
python -m pytest tests/unit/test_auth_basic.py -v --tb=short

echo -e "\n📋 執行現有的單元測試..."
python -m pytest tests/unit/test_classroom_detail_unit.py -v --tb=short

echo -e "\n📋 執行雙系統測試..."
python -m pytest tests/unit/test_dual_system_basic.py -v --tb=short

echo -e "\n📋 執行整合測試..."
python -m pytest tests/integration/ -v --tb=short

echo -e "\n✅ 測試完成！"