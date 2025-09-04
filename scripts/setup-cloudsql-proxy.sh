#!/bin/bash

# Cloud SQL Proxy 設定腳本
echo "🔒 設定 Cloud SQL Proxy..."

# 1. 下載 Cloud SQL Proxy
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.11.0/cloud-sql-proxy.darwin.amd64
else
    # Linux
    curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.11.0/cloud-sql-proxy.linux.amd64
fi

chmod +x cloud-sql-proxy

# 2. 建立 service account（如果需要）
echo "📝 建立 Service Account..."
gcloud iam service-accounts create cloudsql-proxy \
    --display-name="Cloud SQL Proxy Service Account" \
    --project=duotopia-469413

# 3. 授予權限
gcloud projects add-iam-policy-binding duotopia-469413 \
    --member="serviceAccount:cloudsql-proxy@duotopia-469413.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# 4. 下載金鑰
gcloud iam service-accounts keys create key.json \
    --iam-account=cloudsql-proxy@duotopia-469413.iam.gserviceaccount.com

echo "✅ Cloud SQL Proxy 設定完成"
echo ""
echo "使用方式："
echo "1. 本地開發："
echo "   ./cloud-sql-proxy --credentials-file=key.json duotopia-469413:asia-east1:duotopia-staging-0827"
echo ""
echo "2. 連線字串改為："
echo "   postgresql://duotopia_user:password@localhost:5432/duotopia"
