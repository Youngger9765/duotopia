#!/bin/bash
# 重置並重新填充測試資料的腳本

echo "🔄 重置 Duotopia 資料庫..."

cd /Users/young/project/duotopia/backend

# 停止服務
echo "⏹️  停止服務..."
pkill -f "python main.py" || true

# 重置資料庫
echo "🗑️  清空資料庫..."
cd ..
docker-compose exec postgres psql -U duotopia_user -d duotopia -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 重新執行遷移
echo "🔨 執行資料庫遷移..."
cd backend
alembic upgrade head

# 填充測試資料
echo "🌱 填充測試資料..."
python seed.py

echo "✅ 資料庫重置完成！"
echo ""
echo "📝 測試帳號："
echo "教師: teacher1@duotopia.com / password123"
echo "學生: 使用4步驟登入流程"
echo ""
echo "🚀 啟動服務："
echo "cd backend && python main.py"