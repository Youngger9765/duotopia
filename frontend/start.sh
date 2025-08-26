#!/bin/sh
set -e

# 顯示環境變數以便調試
echo "BACKEND_URL is: ${BACKEND_URL}"

# 使用 sed 替換配置中的 BACKEND_URL
sed "s|\${BACKEND_URL}|${BACKEND_URL}|g" /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

# 顯示生成的配置以便調試
echo "Generated nginx configuration:"
cat /etc/nginx/conf.d/default.conf

# 啟動 nginx
nginx -g "daemon off;"