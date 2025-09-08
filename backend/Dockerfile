FROM python:3.11-slim

WORKDIR /app

# 複製依賴檔案
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY *.py ./
COPY alembic ./alembic/
COPY alembic.ini ./
# 複製其他目錄（如果存在）
COPY service[s] ./services/
COPY router[s] ./routers/
COPY cor[e] ./core/

# 複製 GCS service account key（如果存在）
COPY service-account-key.jso[n] ./service-account-key.json

# 暴露端口 (Cloud Run 使用 8080)
EXPOSE 8080

# 設定環境變數
ENV PORT=8080

# 啟動應用
CMD ["python", "main.py"]
