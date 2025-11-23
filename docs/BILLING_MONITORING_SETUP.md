# GCP Billing Monitoring Setup

## 📋 總覽

本文件記錄 Duotopia 專案的 GCP 費用監控系統設置，用於追蹤和預警異常費用增長（如 2025-11-18 的 GCS 費用異常事件）。

## 🎯 目標

1. **即時監控**: 透過 Budget Alert 在費用達到閾值時發送 Email 通知
2. **歷史分析**: 透過 BigQuery 查詢歷史費用資料，產生趨勢圖表
3. **異常偵測**: 自動比較前後期間費用，偵測異常增長

## 🏗️ 架構

```
┌──────────────────┐
│  GCP Billing     │
│  (實際費用)      │
└────────┬─────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ Budget Alert     │            │ BigQuery Export  │
│ (即時通知)       │            │ (歷史資料)       │
└────────┬─────────┘            └────────┬─────────┘
         │                                │
         │                                │
         ▼                                ▼
┌──────────────────┐            ┌──────────────────┐
│ Email / Pub/Sub  │            │ Backend API      │
│ (手動檢查)       │            │ (自動查詢)       │
└──────────────────┘            └────────┬─────────┘
                                         │
                                         ▼
                                ┌──────────────────┐
                                │ Frontend         │
                                │ (費用儀表板)     │
                                └──────────────────┘
```

## ✅ 已完成項目

### 1. GCS Audit Logging（已啟用）

**目的**: 追蹤所有 GCS bucket 操作（read, write, delete）

**配置**:
```bash
# Log bucket
gs://duotopia-logs

# Monitored bucket
gs://duotopia-audio

# Log prefix
gcs-audit/
```

**成本**: ~$0.01/month

**查詢範例**:
```bash
gcloud logging read "resource.type=gcs_bucket AND protoPayload.resourceName:duotopia-audio" \
  --limit 100 \
  --format json \
  --project duotopia-472708
```

### 2. Pub/Sub Topic for Budget Alerts（已創建）

**Topic Name**: `projects/duotopia-472708/topics/budget-alerts`

**用途**: 接收 Budget Alert 通知，可串接 Cloud Functions 實現自動化響應

**未來擴展**:
- Cloud Function 自動發送 Slack 通知
- 費用異常時自動執行 investigation script
- 整合到 Admin Dashboard 顯示即時警報

### 3. BigQuery Billing Export（已啟用）

**Dataset**: `duotopia-472708.billing_export`

**Export Types**:
- **Standard usage cost**: 每日彙總，服務級別
- **Detailed usage cost**: 每小時明細，SKU 級別

**資料可用性**: 啟用後 24 小時開始匯入

**表格名稱**:
```
gcp_billing_export_resource_v1_XXXXXX  (Standard)
gcp_billing_export_v1_XXXXXX           (Detailed)
```

### 4. Backend Billing Service（已開發）

**檔案**: `backend/services/billing_service.py`

**功能**:
- BigQuery client 初始化（支援 service account 和 ADC）
- 費用摘要查詢 (`get_billing_summary`)
- 服務明細查詢 (`get_service_breakdown`)
- 資料可用性檢查 (`_check_tables_exist`)

**特性**:
- 單例模式（singleton pattern）
- 延遲初始化（lazy initialization）
- 優雅錯誤處理（在資料不可用時返回友善訊息）

### 5. Admin Billing API（已開發）

**檔案**: `backend/routers/admin_billing.py`

**端點**:

| Method | Endpoint | 描述 | 權限 |
|--------|----------|------|------|
| GET | `/api/admin/billing/health` | 檢查 BigQuery 連線狀態 | Admin |
| GET | `/api/admin/billing/summary?days=30` | 取得費用摘要 | Admin |
| GET | `/api/admin/billing/service-breakdown?service=Cloud%20Run&days=7` | 取得服務明細 | Admin |
| GET | `/api/admin/billing/anomaly-check?threshold_percent=50&days=7` | 檢查費用異常 | Admin |

**認證**: 使用 `get_current_admin()` dependency，確保只有 admin 用戶可存取

**測試**: `backend/tests/test_billing_api.py`

```bash
cd backend
python tests/test_billing_api.py
```

## 📝 待完成項目

### 1. Budget Alert 設定（需手動在 Web UI 完成）

**原因**: GCP Billing Budget API 不支援程式化創建（已嘗試 gcloud CLI, REST API, Terraform 均失敗）

**操作指南**: `/tmp/budget_manual_guide_final.md`

**推薦配置**:

| 服務 | 每月預算 | 閾值 | 用途 |
|------|---------|------|------|
| Cloud Storage | $1 | 50%, 90%, 100% | 偵測類似 11/18 的異常 |
| Cloud Run | $50 | 50%, 75%, 90% | 監控主要費用來源 |
| Artifact Registry | $5 | 50%, 75%, 90% | Container image 儲存費用 |

**設定步驟**:
1. 開啟 https://console.cloud.google.com/billing/01471C-B12C4F-6AB7B9/budgets?project=duotopia-472708
2. 點擊 `CREATE BUDGET`
3. 依照指南設定（約 5 分鐘）

### 2. Frontend Billing Dashboard（待開發）

**建議實作**:

```typescript
// frontend/src/pages/Admin/BillingDashboard.tsx

interface BillingSummary {
  total_cost: number;
  period: { start: string; end: string };
  top_services: Array<{ service: string; cost: number }>;
  daily_costs: Array<{ date: string; cost: number }>;
  data_available: boolean;
}

const BillingDashboard = () => {
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBillingSummary();
  }, []);

  const fetchBillingSummary = async () => {
    const response = await api.get("/api/admin/billing/summary?days=30");
    setSummary(response.data);
    setLoading(false);
  };

  return (
    <div className="billing-dashboard">
      <h1>GCP 費用監控</h1>

      {/* 總覽卡片 */}
      <div className="summary-cards">
        <Card>
          <h3>本月總費用</h3>
          <p className="cost">${summary?.total_cost || 0}</p>
        </Card>
      </div>

      {/* 服務費用排行 */}
      <Card>
        <h3>Top 服務費用</h3>
        <BarChart data={summary?.top_services || []} />
      </Card>

      {/* 每日費用趨勢 */}
      <Card>
        <h3>每日費用趨勢</h3>
        <LineChart data={summary?.daily_costs || []} />
      </Card>

      {/* 異常警報 */}
      <AnomalyAlerts />
    </div>
  );
};
```

**UI 元件**:
- 📊 總費用卡片（顯示本月總額）
- 📈 每日費用折線圖（使用 Chart.js 或 Recharts）
- 🏆 Top 服務費用排行（Bar Chart）
- ⚠️ 異常警報列表（費用增長超過閾值）

**路由**: `/admin/billing`

## 🔍 使用情境

### 情境 1: 每日檢查費用

```bash
# 登入 Admin Dashboard
# 查看 /admin/billing 頁面
# 檢查是否有紅色警報標記
```

### 情境 2: 調查費用異常

當收到 Budget Alert Email:

1. **確認異常服務**
   ```
   GET /api/admin/billing/summary?days=7
   # 查看 top_services 找出異常服務
   ```

2. **查看服務明細**
   ```
   GET /api/admin/billing/service-breakdown?service=Cloud%20Storage&days=7
   # 查看 sku_breakdown 找出具體 SKU
   ```

3. **查詢 Audit Logs**（針對 GCS）
   ```bash
   gcloud logging read "resource.type=gcs_bucket AND protoPayload.resourceName:duotopia-audio" \
     --limit 1000 \
     --format json \
     --project duotopia-472708 | jq '.[] | {time: .timestamp, method: .protoPayload.methodName}'
   ```

4. **對比代碼變更**
   ```bash
   git log --since="7 days ago" --oneline
   # 查看是否有新功能上線
   ```

### 情境 3: 定期成本優化

每月檢查:
1. 查看 `/api/admin/billing/summary?days=30` 總費用
2. 找出 Top 3 服務
3. 評估是否可優化:
   - Cloud Run: 調整 min-instances, CPU/Memory
   - Cloud Storage: 清理舊資料, 啟用 Lifecycle Policy
   - Artifact Registry: 刪除舊 image tags

## 📊 預期成本

| 項目 | 成本 |
|------|------|
| GCS Audit Logging | ~$0.01/month |
| BigQuery Storage (Billing Export) | Free (10GB limit) |
| BigQuery Queries | Free (1TB/month limit) |
| Pub/Sub Topic | Free (10GB/month limit) |
| Budget Alerts | Free |
| **Total** | **~$0.01/month** |

## 🚀 部署到 Cloud Run

部署後，Backend API 將自動使用 Cloud Run 的 service account 連接 BigQuery，無需額外配置。

**確認步驟**:
1. 確認 Cloud Run service account 有 BigQuery 讀取權限
2. 部署後測試 `GET /api/admin/billing/health`
3. 應返回 `"status": "waiting_for_data"` 或 `"status": "healthy"`

## 📚 參考資料

- [GCP Billing Export to BigQuery](https://cloud.google.com/billing/docs/how-to/export-data-bigquery)
- [GCP Budget Alerts](https://cloud.google.com/billing/docs/how-to/budgets)
- [GCS Audit Logging](https://cloud.google.com/storage/docs/audit-logging)
- [BigQuery Standard SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)

## 🐛 已知問題

### GCP Billing Budget API 無法程式化創建

**問題**: 所有程式化方法（gcloud CLI, REST API, Terraform）均返回 403/400 錯誤

**原因**: GCP Billing Budget API 設計缺陷
- API 要求使用 Service Account 認證
- 但創建 Budget 需要 Billing Admin 權限
- Billing Admin 只能授予 User Account（組織層級）
- Service Account 無法獲得足夠權限

**解法**: 必須手動在 Web UI 創建（一次性操作）

**影響**: 無法用 Terraform 管理 Budget（其他資源可正常使用 Terraform）

## 📞 聯絡資訊

如有問題請聯絡:
- GitHub: https://github.com/anthropics/claude-code/issues
- Email: myduotopia@gmail.com
