# 效能監控設定指南 (OpenTelemetry + Cloud Trace)

## 📊 概述

此專案使用 OpenTelemetry + Google Cloud Trace 監控 AI 分析 API 的效能。

### 成本
- ✅ **前 2.5M spans/月免費**
- ✅ 超過才收費：$0.20 / million spans
- ✅ 你們的流量應該遠低於免費額度

---

## 🚀 快速開始

### 1. 安裝套件

```bash
cd backend
pip install -r requirements.txt
```

新增的套件：
- `opentelemetry-api` - OpenTelemetry 核心 API
- `opentelemetry-sdk` - OpenTelemetry SDK
- `opentelemetry-exporter-gcp-trace` - GCP Cloud Trace 匯出器
- `google-cloud-logging` - GCP Logging

---

### 2. 設定 GCP 權限

#### 本機開發

```bash
# 確認已登入 GCP
gcloud auth application-default login

# 設定專案
gcloud config set project duotopia-472708
```

#### Cloud Run 環境

Cloud Run 預設已有 Cloud Trace 和 Logging 權限，無需額外設定。

---

### 3. 環境變數（可選）

在 `.env` 中加入（可選，預設會自動偵測）：

```bash
# GCP Project ID（通常會自動偵測）
GOOGLE_CLOUD_PROJECT=duotopia-472708

# 啟用/停用追蹤（預設啟用）
ENABLE_TRACING=true
```

---

## 📈 查看效能資料

### 方法 1: Cloud Trace UI（推薦）

1. **開啟 Cloud Trace**
   ```bash
   open "https://console.cloud.google.com/traces/list?project=duotopia-472708"
   ```

2. **查看 Trace**
   - 在 Timeline 中可以看到每個 API 請求
   - 點擊任一 trace 可以看到詳細時間分佈
   - 可以看到每個步驟花費的時間

3. **重點關注**
   - `AI Grade Assignment` - 整個 API 的時間
   - `Whisper API Call` - 語音辨識的時間（通常最慢）
   - `Calculate AI Scores` - AI 評分計算時間
   - `Database Update` - 資料庫更新時間

### 方法 2: Cloud Logging

```bash
# 查看效能日誌
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message=~\"⏱️\"" \
  --limit 50 \
  --format json \
  --project duotopia-472708
```

輸出範例：
```
⏱️  Verify Teacher Permission: 2.34ms
⏱️  Database Query - Get Assignment: 15.67ms
⏱️  Whisper API Call: 2345.89ms  ⬅️ 通常最慢
⏱️  Calculate AI Scores: 123.45ms
⏱️  Database Update - Save Results: 34.56ms
🏁 AI_Grade_Assignment_123 - Total: 2521.91ms
```

---

## 🧪 測試效能監控

### 執行測試

```bash
cd backend

# 測試 performance_monitoring 模組
python performance_monitoring.py

# 執行 AI 分析 API（需要有測試資料）
pytest tests/integration/api/test_ai_grading.py -v
```

### 預期輸出

終端會顯示：
```
⏱️  routers.assignments.ai_grade_assignment: 2521.91ms
📍 AI_Grade_Assignment_123 - Permission Check: 2.34ms
📍 AI_Grade_Assignment_123 - Assignment Query: 18.01ms
📍 AI_Grade_Assignment_123 - Whisper API Complete: 2363.90ms
📍 AI_Grade_Assignment_123 - Score Calculation Complete: 2487.35ms
📍 AI_Grade_Assignment_123 - Database Update Complete: 2522.00ms
🏁 AI_Grade_Assignment_123 - Total: 2522.00ms
```

---

## 🎯 優化建議

根據 trace 結果，可能的優化方向：

### 如果 Whisper API 很慢（> 2 秒）
1. **並行處理多個音檔**
   ```python
   import asyncio
   results = await asyncio.gather(*[
       process_audio(url) for url in audio_urls
   ])
   ```

2. **使用更快的 Whisper 模型**
   - `whisper-1` → `whisper-1-turbo`（更快但稍不準確）

3. **預先處理音檔**
   - 壓縮音檔大小
   - 移除靜音片段

### 如果資料庫查詢慢（> 100ms）
1. **加索引**
   ```sql
   CREATE INDEX idx_student_assignment_status
   ON student_assignments(assignment_id, student_id);
   ```

2. **減少查詢次數**
   - 使用 `joinedload` 預先載入關聯資料

### 如果 AI 計算慢（> 500ms）
1. **向量化計算**
   ```python
   import numpy as np
   # 使用 numpy 批次計算相似度
   ```

2. **快取常見計算結果**

---

## 🔧 進階配置

### 自訂 Span

在任何函數中加入效能追蹤：

```python
from performance_monitoring import trace_function, start_span

# 方法 1: Decorator
@trace_function("My Custom Function")
async def my_function():
    # 你的代碼
    pass

# 方法 2: Context Manager
def another_function():
    with start_span("Step 1", {"user_id": 123}):
        # 執行步驟 1
        pass

    with start_span("Step 2"):
        # 執行步驟 2
        pass
```

### 效能快照比較

```python
from performance_monitoring import PerformanceSnapshot

snapshot = PerformanceSnapshot("Optimization Test")

# 執行操作
do_something()
snapshot.checkpoint("Step 1")

# 執行更多操作
do_more()
snapshot.checkpoint("Step 2")

results = snapshot.finish()
# 會自動記錄到 GCP Logging
```

---

## ❓ 常見問題

### Q: 為什麼看不到 trace？
**A**: 確認：
1. `gcloud auth application-default login` 已執行
2. GCP Project ID 正確
3. API 有實際被呼叫（不是 mock 模式）

### Q: Trace 資料多久會出現？
**A**: 通常 10-30 秒內會出現在 Cloud Trace UI

### Q: 本機開發會送 trace 到 GCP 嗎？
**A**: 會！所以本機測試也能看到效能資料

### Q: 如何停用追蹤？
**A**:
```bash
# 方法 1: 環境變數
export ENABLE_TRACING=false

# 方法 2: 移除 @trace_function decorator
```

### Q: 會影響效能嗎？
**A**:
- OpenTelemetry 開銷 < 1ms / span
- 使用批次匯出，不會阻塞 API
- 生產環境可安全使用

---

## 📚 相關連結

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [GCP Cloud Trace](https://cloud.google.com/trace/docs)
- [效能監控模組](../backend/performance_monitoring.py)

---

**🎉 完成！現在你們可以即時監控 AI 分析的效能瓶頸了！**
