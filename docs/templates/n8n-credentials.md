# n8n 認證配置說明

本文件記錄所有已配置到 Cloud Run n8n 服務的外部系統認證資訊。

## 📋 目錄

- [LINE Messaging API](#line-messaging-api)
- [Google Gemini (Vertex AI)](#google-gemini-vertex-ai)
- [GCP Billing API](#gcp-billing-api)
- [Azure Billing API](#azure-billing-api)
- [環境變數使用方式](#環境變數使用方式)

---

## LINE Messaging API

**用途：** LINE 客服機器人、訊息通知

### Cloud Run Secrets

已建立並綁定到 n8n 服務：

| Secret 名稱                 | 環境變數                    | 說明                      |
| --------------------------- | --------------------------- | ------------------------- |
| `line-channel-id`           | `LINE_CHANNEL_ID`           | LINE Channel ID           |
| `line-channel-secret`       | `LINE_CHANNEL_SECRET`       | LINE Channel Secret       |
| `line-channel-access-token` | `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token |

### 原始資訊

```
Channel ID: 2008963724
Channel secret: 42a3dfc37f44093bcf89f1e9514cca2a
Webhook URL: https://n8n-316409492201.asia-east1.run.app/webhook/line-webhook
```

### n8n 使用方式

```javascript
// HTTP Request 節點 - LINE Reply API
URL: https://api.line.me/v2/bot/message/reply
Headers:
  Authorization: Bearer {{$env.LINE_CHANNEL_ACCESS_TOKEN}}
  Content-Type: application/json
```

---

## Google Gemini (Vertex AI)

**用途：** AI 工作流生成、智能客服、內容生成

### Cloud Run Secrets

| Secret 名稱             | 環境變數                | 說明                           |
| ----------------------- | ----------------------- | ------------------------------ |
| `vertex-ai-credentials` | `VERTEX_AI_CREDENTIALS` | Vertex AI Service Account JSON |

### Service Account

```
Email: n8n-vertex-ai@duotopia-472708.iam.gserviceaccount.com
Roles:
  - roles/aiplatform.user (Vertex AI)
  - roles/billing.viewer (GCP Billing - Billing Account 層級)
```

### API 端點

```
Vertex AI: https://asia-east1-aiplatform.googleapis.com
Generative Language (公開): https://generativelanguage.googleapis.com
```

### n8n 使用方式

**選項 A：使用 Google Cloud 憑證**

- 在 n8n Credentials 中新增 Google Cloud
- 貼入 `{{$env.VERTEX_AI_CREDENTIALS}}` JSON

**選項 B：直接 HTTP Request**

```javascript
// 需要先用 Service Account 取得 Access Token
Authorization: Bearer <ACCESS_TOKEN>
```

---

## GCP Billing API

**用途：** GCP 費用監控、帳單通知

### 已啟用的 API

```
cloudbilling.googleapis.com (Cloud Billing API)
```

### 權限配置

- **Billing Account ID:** `017B33-891FD6-C45566` (duotopia - cacafly - 1)
- **Service Account:** `n8n-vertex-ai@duotopia-472708.iam.gserviceaccount.com`
- **Role:** `roles/billing.viewer`

### n8n 使用方式

```javascript
// HTTP Request 節點
Method: GET
URL: https://cloudbilling.googleapis.com/v1/billingAccounts/017B33-891FD6-C45566
Authentication: 使用 Google Cloud 憑證 (Vertex AI Service Account)
```

---

## Azure Billing API

**用途：** Azure 費用監控、帳單下載與通知

### Cloud Run Secrets

| Secret 名稱             | 環境變數                | 說明                        |
| ----------------------- | ----------------------- | --------------------------- |
| `azure-subscription-id` | `AZURE_SUBSCRIPTION_ID` | Azure 訂閱 ID               |
| `azure-tenant-id`       | `AZURE_TENANT_ID`       | Azure 租戶 ID               |
| `azure-client-id`       | `AZURE_CLIENT_ID`       | Service Principal Client ID |
| `azure-client-secret`   | `AZURE_CLIENT_SECRET`   | Service Principal Secret    |

### Service Principal

```
名稱: n8n-azure-billing
App ID (Client ID): 167420c7-cb82-4123-be32-50ec4eb6a6bd
角色: Billing Reader
範圍: /subscriptions/eefabf75-cffc-4208-bb83-4f89ad56cc83
```

### 訂閱資訊

```
名稱: Azure subscription 1
Subscription ID: eefabf75-cffc-4208-bb83-4f89ad56cc83
Tenant ID: d6e155c6-13f2-4984-8269-1e01802abb83
```

### n8n 使用方式

```javascript
// HTTP Request 節點 - Azure Cost Management API
URL: https://management.azure.com/subscriptions/{{$env.AZURE_SUBSCRIPTION_ID}}/providers/Microsoft.CostManagement/query?api-version=2021-10-01
Headers:
  Authorization: Bearer <AZURE_ACCESS_TOKEN>
  Content-Type: application/json

// 取得 Access Token (先執行)
URL: https://login.microsoftonline.com/{{$env.AZURE_TENANT_ID}}/oauth2/v2.0/token
Method: POST
Body (x-www-form-urlencoded):
  grant_type: client_credentials
  client_id: {{$env.AZURE_CLIENT_ID}}
  client_secret: {{$env.AZURE_CLIENT_SECRET}}
  scope: https://management.azure.com/.default
```

---

## 環境變數使用方式

### 在 n8n 工作流中讀取

所有環境變數都可以通過表達式語法讀取：

```javascript
{
  {
    $env.LINE_CHANNEL_ACCESS_TOKEN;
  }
}
{
  {
    $env.VERTEX_AI_CREDENTIALS;
  }
}
{
  {
    $env.AZURE_SUBSCRIPTION_ID;
  }
}
{
  {
    $env.AZURE_TENANT_ID;
  }
}
{
  {
    $env.AZURE_CLIENT_ID;
  }
}
{
  {
    $env.AZURE_CLIENT_SECRET;
  }
}
```

### 列出所有可用的環境變數

在 n8n Function 節點中：

```javascript
return Object.keys(process.env)
  .filter(
    (key) =>
      key.startsWith("LINE_") ||
      key.startsWith("AZURE_") ||
      key.startsWith("VERTEX_"),
  )
  .map((key) => ({ name: key, hasValue: !!process.env[key] }));
```

---

## Secret Manager 管理

### 列出所有 Secrets

```powershell
gcloud secrets list --project=duotopia-472708
```

### 查看 Secret 內容

```powershell
gcloud secrets versions access latest --secret=<SECRET_NAME> --project=duotopia-472708
```

### 更新 Secret

```powershell
echo "NEW_VALUE" | gcloud secrets versions add <SECRET_NAME> --data-file=- --project=duotopia-472708
```

### 綁定到 Cloud Run

```powershell
gcloud run services update n8n --region=asia-east1 `
  --update-secrets "ENV_VAR_NAME=secret-name:latest" `
  --project=duotopia-472708
```

---

## 安全注意事項

1. **永不提交實際密鑰到版本控制**
   - 所有敏感值都已存入 Secret Manager
   - 本地開發使用 `.env` 檔案（已加入 `.gitignore`）

2. **定期輪替密鑰**
   - LINE Channel Access Token: 無過期時間，建議每 6 個月輪替
   - Azure Client Secret: 24 個月後過期，需提前更新
   - Google Service Account Key: 建議每年輪替

3. **最小權限原則**
   - 每個 Service Account / Service Principal 只授予必要權限
   - 定期審查權限配置

4. **監控異常使用**
   - 啟用 GCP Audit Logs
   - 啟用 Azure Activity Logs
   - 監控 API 呼叫頻率與來源

---

## 建立日期與負責人

- **建立日期:** 2026-01-26
- **Cloud Run 服務:** n8n (asia-east1)
- **GCP 專案:** duotopia-472708
- **Azure 訂閱:** Azure subscription 1

---

## 相關文件

- [LINE Messaging API 官方文件](https://developers.line.biz/en/docs/messaging-api/)
- [Google Vertex AI 文件](https://cloud.google.com/vertex-ai/docs)
- [GCP Billing API 文件](https://cloud.google.com/billing/docs/reference/rest)
- [Azure Cost Management API 文件](https://learn.microsoft.com/en-us/rest/api/cost-management/)

---

## 快速參考

### Cloud Run 服務資訊

```
名稱: n8n
區域: asia-east1
URL: https://n8n-316409492201.asia-east1.run.app
服務帳號: 316409492201-compute@developer.gserviceaccount.com
```

### 已授權的 IAM 權限

```
serviceAccount:316409492201-compute@developer.gserviceaccount.com
  - roles/secretmanager.secretAccessor (所有 Secrets)
```

### Service Accounts 清單

```
n8n-vertex-ai@duotopia-472708.iam.gserviceaccount.com
  - roles/aiplatform.user (Project 層級)
  - roles/billing.viewer (Billing Account 層級)
```
