#!/bin/sh
set -e

# 診斷資訊
echo "=========================================="
echo "START.SH DIAGNOSTIC INFO"
echo "=========================================="
echo "Script started at: $(date)"
echo "BACKEND_URL: ${BACKEND_URL}"
echo "PWD: $(pwd)"
echo "USER: $(whoami)"
echo "All ENV vars:"
env | sort
echo "=========================================="

# 檢查檔案是否存在
if [ ! -f /etc/nginx/conf.d/nginx.conf.template ]; then
    echo "ERROR: nginx.conf.template not found!"
    exit 1
fi

# 使用 sed 替換配置中的 BACKEND_URL
echo "Replacing BACKEND_URL in nginx config..."
sed "s|\${BACKEND_URL}|${BACKEND_URL}|g" /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

# 顯示生成的配置以便調試
echo "Generated nginx configuration:"
cat /etc/nginx/conf.d/default.conf

# 檢查 nginx 配置語法
echo "Testing nginx configuration..."
nginx -t

# 列出所有 nginx 配置檔案
echo "All nginx config files:"
ls -la /etc/nginx/conf.d/

# 啟動 nginx
echo "Starting nginx..."
nginx -g "daemon off;"