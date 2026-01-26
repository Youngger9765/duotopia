# OpenAI → Vertex AI (Gemini) 遷移文件

## 概述

本次遷移將 AI 服務從 OpenAI GPT 切換到 Google Cloud Vertex AI (Gemini)，統一 AI 服務到 GCP 平台。

**保留不動**: Azure Speech Services（發音評估、TTS）

---

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `USE_VERTEX_AI` | `false` | 開關，設為 `true` 啟用 Vertex AI |
| `VERTEX_AI_PROJECT_ID` | `duotopia-472708` | GCP 專案 ID |
| `VERTEX_AI_LOCATION` | `us-central1` | 區域（美國中部，Gemini 2.5 模型支援完整） |

---

## 啟用方式

### 方法一：GitHub CLI

```bash
# 新增 Variable（推薦用於非機密設定）
gh variable set USE_VERTEX_AI --body "true"

# 或使用 Secret（如果需要保密）
gh secret set USE_VERTEX_AI --body "true"
```

### 方法二：GitHub Web UI

1. 進入 Repository → Settings → Secrets and variables → Actions
2. 在 Variables 分頁新增 `USE_VERTEX_AI` = `true`
3. 重新部署 backend

### 回退方式

```bash
# 設為 false 即可回退到 OpenAI
gh variable set USE_VERTEX_AI --body "false"
```

---

## Model 對應

| 用途 | OpenAI Model | Vertex AI Model | 說明 |
|------|--------------|-----------------|------|
| 翻譯、詞性判斷、干擾選項、例句 | gpt-4o-mini | gemini-2.5-flash | 最新穩定版，快速高效能 |
| 帳單分析摘要 | gpt-4 | gemini-2.5-flash | 統一使用 |
| 錄音錯誤報告 | gpt-4o-mini | gemini-2.5-flash | 最新穩定版，快速高效能 |

---

## 修改的檔案

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `backend/services/vertex_ai.py` | Vertex AI 服務封裝 |

### 修改檔案

| 檔案 | 修改內容 |
|------|----------|
| `backend/requirements.txt` | 新增 `google-cloud-aiplatform==1.75.0` |
| `backend/core/config.py` | 新增 Vertex AI 配置項 |
| `backend/services/translation.py` | 所有 AI 方法新增 Vertex AI 分支 |
| `backend/services/billing_analysis_service.py` | AI 摘要生成新增 Vertex AI 支援 |
| `backend/routers/cron.py` | 錄音錯誤報告新增 Vertex AI 支援 |
| `.github/workflows/deploy-backend.yml` | 新增環境變數傳遞 |
| `.github/workflows/deploy-per-issue.yml` | 新增環境變數傳遞 |

---

## VertexAIService API

```python
from services.vertex_ai import get_vertex_ai_service

vertex_ai = get_vertex_ai_service()

# 文字生成
result = await vertex_ai.generate_text(
    prompt="翻譯這段文字",
    model_type="flash",  # "flash" 或 "pro"（目前都使用 gemini-2.5-flash）
    max_tokens=100,
    temperature=0.3,
    system_instruction="你是專業翻譯",
)

# JSON 生成（強制 JSON 輸出格式）
result = await vertex_ai.generate_json(
    prompt="生成干擾選項",
    model_type="flash",
    max_tokens=200,
    temperature=0.8,
)

# 同步版本（用於 cron job）
result = vertex_ai.generate_text_sync(
    prompt="生成報告",
    model_type="flash",
)
```

---

## 遷移的服務

### 1. TranslationService

| 方法 | 功能 |
|------|------|
| `translate_text()` | 單字翻譯 |
| `translate_with_pos()` | 翻譯 + 詞性判斷 |
| `batch_translate()` | 批次翻譯 |
| `batch_translate_with_pos()` | 批次翻譯 + 詞性 |
| `generate_sentences()` | 例句生成 |
| `generate_distractors()` | 干擾選項生成 |
| `batch_generate_distractors()` | 批次干擾選項生成 |

### 2. BillingAnalysisService

| 方法 | 功能 |
|------|------|
| `_generate_ai_summary()` | AI 帳單分析摘要 |

### 3. Cron Job

| 函數 | 功能 |
|------|------|
| `recording_error_report_cron()` | 錄音錯誤報告生成 |

---

## 成本對比（預估）

| 服務 | Model | 價格 (1M tokens) |
|------|-------|-----------------|
| OpenAI | gpt-4o-mini | $0.15 input / $0.60 output |
| OpenAI | gpt-4 | $30 input / $60 output |
| **Vertex AI** | **gemini-2.5-flash** | **$0.15 input / $0.60 output** |

**注意**: gemini-2.5-flash 與 gpt-4o-mini 價格相近，但性能更強；比 gpt-4 便宜非常多。

---

## 認證方式

- **Cloud Run**: 自動使用服務帳戶認證，不需額外配置
- **本地開發**: 需設定 `GOOGLE_APPLICATION_CREDENTIALS` 或使用 `gcloud auth application-default login`

---

## 注意事項

1. **Prompt 相容性**: Gemini 和 GPT 的 prompt 格式略有不同，已在程式碼中處理
2. **JSON 輸出**: Vertex AI 使用 `response_mime_type="application/json"` 強制 JSON 輸出
3. **Rate Limiting**: Vertex AI 有不同的配額限制，如遇問題需申請增加配額
4. **Lazy Init**: 服務使用延遲初始化，避免啟動時錯誤

---

## 相關文件

- [PRD.md](./PRD.md) - 產品需求文檔
- [CICD.md](./CICD.md) - 部署與 CI/CD

---

**文件版本**: v1.3
**建立日期**: 2026-01-08
**更新日期**: 2026-01-08 (升級為 gemini-2.5-flash，區域改為 us-central1)
**作者**: Claude Code
