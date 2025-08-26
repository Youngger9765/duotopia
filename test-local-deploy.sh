#!/bin/bash
# 本地測試部署腳本

echo "=== 測試本地部署 ==="

# 1. 啟動後端容器
echo "啟動後端..."
docker run -d \
  --name duotopia-backend-test \
  -p 8080:8080 \
  -e DATABASE_URL="postgresql://duotopia_user:duotopia_pass@host.docker.internal:5432/duotopia" \
  duotopia-backend-test

# 2. 等待後端啟動
echo "等待後端啟動..."
sleep 5

# 3. 測試後端健康檢查
echo "測試後端健康檢查..."
curl http://localhost:8080/health
echo ""

# 4. 啟動前端容器（模擬 Cloud Run 設定環境變數）
echo "啟動前端..."
docker run -d \
  --name duotopia-frontend-test \
  -p 3000:80 \
  -e BACKEND_URL="http://host.docker.internal:8080" \
  duotopia-frontend-test

# 5. 等待前端啟動
echo "等待前端啟動..."
sleep 5

# 6. 測試前端
echo "測試前端頁面..."
curl -s http://localhost:3000 | head -5

# 7. 測試前端 API 代理
echo "測試前端 API 代理..."
curl http://localhost:3000/api/health
echo ""

# 8. 清理
echo "清理容器..."
docker stop duotopia-backend-test duotopia-frontend-test
docker rm duotopia-backend-test duotopia-frontend-test

echo "=== 測試完成 ==="