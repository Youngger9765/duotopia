# API Test Runner Guide

## 快速開始

### 執行完整測試套件

```bash
# 下載測試腳本
curl -o /tmp/issue_112_api_test.py https://raw.githubusercontent.com/.../issue_112_api_test.py

# 或直接使用已有的腳本
python3 /tmp/issue_112_api_test.py
```

### 修改測試環境

編輯腳本中的 `BASE_URL`:

```python
# Preview 環境
BASE_URL = "https://duotopia-preview-issue-112-backend-b2ovkkgl6a-de.a.run.app"

# Staging 環境
BASE_URL = "https://duotopia-backend-staging-556925873167.asia-east1.run.app"

# Local 環境
BASE_URL = "http://localhost:8000"
```

---

## 測試腳本功能

### Phase 1: Quick Mode Testing
- Organization CRUD（4 個端點）
- School CRUD（6 個端點）
- Dashboard API（4 個角色）

### Phase 2: Deep Mode Testing
- RBAC 權限邊界測試
- 資料一致性測試
- 複雜查詢測試
- 邊界條件測試

### Phase 4: Performance Testing
- Dashboard 回應時間
- 列表查詢效能

---

## 測試帳號

### Preview/Staging 環境

| 角色 | Email | Password | 用途 |
|-----|-------|----------|------|
| org_owner | owner@duotopia.com | owner123 | 機構擁有者 |
| org_admin | orgadmin@duotopia.com | orgadmin123 | 機構管理員 |
| school_admin | schooladmin@duotopia.com | schooladmin123 | 分校管理員 |
| teacher | orgteacher@duotopia.com | orgteacher123 | 教師 |

### Local 環境
使用 seed data 中的帳號（參考 `backend/seed_data.py`）

---

## 輸出檔案

執行後會生成以下檔案:

1. **測試報告**: `/tmp/issue-112-api-test-report.md`
   - 完整的測試結果（表格形式）
   - 通過率統計
   - 發現的問題

2. **測試日誌**: `/tmp/test_output.log`
   - 詳細的執行過程
   - 每個 API 的回應時間
   - 錯誤訊息

---

## 手動 API 測試

### 使用 curl

```bash
# 1. 登入
TOKEN=$(curl -s -X POST "https://duotopia-preview-issue-112-backend-b2ovkkgl6a-de.a.run.app/api/auth/teacher/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@duotopia.com","password":"owner123"}' \
  | jq -r '.access_token')

# 2. 測試 Dashboard API
curl -H "Authorization: Bearer $TOKEN" \
  "https://duotopia-preview-issue-112-backend-b2ovkkgl6a-de.a.run.app/api/teachers/dashboard" \
  | jq

# 3. 測試 Organizations API
curl -H "Authorization: Bearer $TOKEN" \
  "https://duotopia-preview-issue-112-backend-b2ovkkgl6a-de.a.run.app/api/organizations" \
  | jq

# 4. 測試 Schools API
ORG_ID="21a8a0c7-a5e3-4799-8336-fbb2cf1de91a"
curl -H "Authorization: Bearer $TOKEN" \
  "https://duotopia-preview-issue-112-backend-b2ovkkgl6a-de.a.run.app/api/schools?organization_id=$ORG_ID" \
  | jq
```

### 使用 Swagger UI

1. 訪問 API 文檔: https://duotopia-preview-issue-112-backend-b2ovkkgl6a-de.a.run.app/docs
2. 點擊右上角 "Authorize"
3. 執行 `/api/auth/teacher/login` 獲取 token
4. 複製 `access_token`
5. 在 "Authorize" 對話框中輸入: `Bearer <your_token>`
6. 測試任意端點

---

## 常見問題

### Q1: 登入失敗 (422 Error)
**問題**: `{"detail":[{"type":"missing","loc":["body","email"],"msg":"Field required"}]}`

**原因**: 使用了 `username` 而非 `email`

**解決**:
```python
# ❌ 錯誤
{"username": "owner@duotopia.com", "password": "owner123"}

# ✅ 正確
{"email": "owner@duotopia.com", "password": "owner123"}
```

### Q2: 登入失敗 (404 Error)
**問題**: `404 Page not found`

**原因**: 端點路徑錯誤

**解決**:
```
❌ /api/auth/login
✅ /api/auth/teacher/login
```

### Q3: 所有 API 返回 401
**問題**: `{"detail": "Not authenticated"}`

**原因**: Token 未正確傳遞

**解決**:
```python
# ✅ 正確的 header
headers = {"Authorization": f"Bearer {token}"}
```

### Q4: Schools API 很慢 (>900ms)
**原因**: Preview 環境使用 free tier 資料庫

**解決**: 在 staging/production 環境測試會更快

---

## 效能基準

### 預期回應時間（Production）

| API | Target | Preview (Free Tier) | Staging/Prod (Paid) |
|-----|--------|---------------------|---------------------|
| Dashboard | <500ms | ~920ms | ~200ms (預估) |
| Organizations GET | <300ms | ~470ms | ~150ms (預估) |
| Schools GET | <300ms | ~920ms | ~200ms (預估) |
| CRUD Operations | <500ms | ~850ms | ~300ms (預估) |

**注意**: Preview 環境數據僅供參考，生產環境效能會更好。

---

## CI/CD 整合

### GitHub Actions 範例

```yaml
# .github/workflows/api-test.yml
name: API Tests

on:
  pull_request:
    branches: [main, staging]

jobs:
  api-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Run API Tests
        env:
          BASE_URL: ${{ secrets.STAGING_API_URL }}
        run: python3 backend/api_test.py

      - name: Upload Test Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: api-test-report
          path: /tmp/issue-112-api-test-report.md
```

---

## 延伸閱讀

- [Issue #112 QA Guide](./issue-112-QA.md) - 完整測試指南
- [API Test Report](./issue-112-API-TEST-REPORT.md) - 最新測試報告
- [Test Summary](./issue-112-API-TEST-SUMMARY.md) - 測試總結
- [ORG Implementation Spec](../ORG_IMPLEMENTATION_SPEC.md) - 功能規格

---

**維護者**: Development Team
**最後更新**: 2026-01-01
