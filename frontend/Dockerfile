# 多階段建置
FROM node:18-alpine AS builder

WORKDIR /app

# 複製 package files
COPY package*.json ./

# 安裝依賴
RUN npm ci

# 複製原始碼
COPY . .

# 建置
RUN npm run build

# Production stage
FROM nginx:alpine

# 安裝 envsubst (通常已包含在 nginx:alpine 中)
RUN apk add --no-cache gettext

# 複製建置結果
COPY --from=builder /app/dist /usr/share/nginx/html

# 複製 nginx 配置模板
COPY nginx.conf.template /etc/nginx/conf.d/nginx.conf.template

# 複製啟動腳本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 設定預設環境變數
ENV BACKEND_URL=http://localhost:8000

# 暴露端口
EXPOSE 80

# 使用自訂啟動腳本
ENTRYPOINT ["/docker-entrypoint.sh"]