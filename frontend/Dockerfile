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

# 複製建置結果
COPY --from=builder /app/dist /usr/share/nginx/html

# 複製 nginx 配置模板
COPY nginx.conf.template /etc/nginx/conf.d/nginx.conf.template

# 複製啟動腳本
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 移除預設的 nginx 配置
RUN rm -f /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 使用啟動腳本
CMD ["/start.sh"]