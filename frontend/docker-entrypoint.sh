#!/bin/sh

# 替換 nginx 配置中的環境變數
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

# 啟動 nginx
exec nginx -g "daemon off;"
