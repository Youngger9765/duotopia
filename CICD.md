# CICD.md - Duotopia CI/CD 部署準則

本文件規範 Duotopia 專案的 CI/CD 流程與部署準則，避免重複犯錯。

## 🔴 最高原則：絕不手動創建昂貴資源

### Cloud SQL 創建鐵律
1. **永遠使用 Makefile 創建資源**
   ```bash
   # ✅ 正確
   make db-create
   
   # ❌ 錯誤 - 絕對禁止
   gcloud sql instances create ...
   ```

2. **Tier 必須檢查三次**
   - 只允許 `db-f1-micro`（$11/月）
   - 禁止 `db-g1-small`（$50/月）
   - 禁止任何更大的實例

3. **Edition 必須明確指定**
   ```bash
   --edition=ENTERPRISE  # 必須，否則 db-f1-micro 不可用
   ```

## 📋 部署前檢查清單

### 1. 配置檢查
- [ ] 確認 `gcloud config get-value project` 顯示 `duotopia-469413`
- [ ] 確認區域是 `asia-east1`
- [ ] 確認沒有硬編碼的 localhost URL
- [ ] 確認沒有舊的 import 路徑

### 2. 資源檢查
```bash
# 部署前必須執行
gcloud sql instances list --format="table(name,tier,state)"
# 確保：
# - 沒有 Small 或更大的實例
# - 沒有不必要的 RUNNABLE 實例
```

### 3. 成本預檢
- [ ] Cloud SQL 實例數量 ≤ 1
- [ ] Cloud Run min-instances = 0
- [ ] 沒有遺留的測試資源

## 🚀 標準部署流程

### 開發環境部署
```bash
# 1. 本地測試
npm run typecheck
npm run lint
npm run build
cd backend && python -m pytest

# 2. Docker 測試
docker build -t test-backend backend/
docker run -p 8080:8080 test-backend

# 3. 推送到 staging
git push origin staging

# 4. 監控部署
gh run watch
gh run list --workflow=deploy-staging.yml --limit=1

# 5. 驗證部署
curl https://duotopia-backend-staging-xxx.run.app/health
```

### 生產環境部署（謹慎）
```bash
# 1. 確認 staging 測試通過
make test-staging

# 2. 創建 PR
git checkout -b release/v1.x.x
git push origin release/v1.x.x
gh pr create --base main

# 3. Code Review 後合併

# 4. 監控生產部署
gh run watch
```

## 🔍 部署監控

### 即時監控命令
```bash
# 查看部署進度
gh run watch

# 查看部署日誌
gh run view --log

# 查看服務日誌
gcloud run logs read duotopia-backend --limit=50

# 檢查錯誤
gcloud run logs read duotopia-backend --limit=50 | grep -i error
```

### 健康檢查
```bash
# Backend
curl https://duotopia-backend-staging-xxx.run.app/health
curl https://duotopia-backend-staging-xxx.run.app/api/docs

# Frontend
curl https://duotopia-frontend-staging-xxx.run.app
```

## ⚠️ 常見錯誤與解決

### 1. PORT 配置錯誤
**錯誤**: Container failed to start
**原因**: Cloud Run 需要 PORT=8080
**解決**: 
```python
# main.py
port = int(os.environ.get("PORT", 8080))
```

### 2. 資料庫連線失敗
**錯誤**: Connection refused
**原因**: 啟動時立即連接資料庫
**解決**: 
```python
# 不要在頂層連接
# 使用 Depends(get_db) 延遲連接
```

### 3. Import 路徑錯誤
**錯誤**: Module not found
**原因**: TypeScript 路徑別名
**解決**: 使用相對路徑而非 @/

### 4. Cloud SQL 版本不相容
**錯誤**: Invalid tier for edition
**原因**: Enterprise Plus 不支援 micro
**解決**: 指定 `--edition=ENTERPRISE`

## 💰 成本控制檢查點

### 每日檢查
```bash
# 檢查 Cloud SQL
gcloud sql instances list
# 任何非 micro 或 RUNNABLE 但未使用的立即處理

# 檢查 Cloud Run
gcloud run services list
# 確認 min-instances = 0
```

### 每週檢查
```bash
# 查看帳單
gcloud billing accounts list
gcloud alpha billing budgets list

# 清理未使用資源
gcloud artifacts repositories list
gcloud storage ls
```

## 📊 部署指標

### 成功部署標準
- ✅ 健康檢查通過
- ✅ 無錯誤日誌
- ✅ API 文檔可訪問
- ✅ 前端頁面正常載入
- ✅ 資料庫連線正常

### 性能指標
- 冷啟動時間 < 10s
- 健康檢查回應 < 1s
- Docker 映像 < 500MB
- 記憶體使用 < 512MB

## 🔄 回滾程序

### 快速回滾
```bash
# 1. 找到上一個成功版本
gcloud run revisions list --service=duotopia-backend

# 2. 回滾到特定版本
gcloud run services update-traffic duotopia-backend \
  --to-revisions=duotopia-backend-00002-abc=100

# 3. 或使用 git revert
git revert HEAD
git push origin staging
```

## 📝 部署日誌模板

每次部署後記錄：
```markdown
### 部署記錄 - [日期]
- **版本**: v1.x.x
- **環境**: staging/production
- **部署者**: [姓名]
- **變更內容**: 
  - Feature: xxx
  - Fix: xxx
- **測試結果**: 
  - [ ] 健康檢查通過
  - [ ] API 測試通過
  - [ ] 前端測試通過
- **問題**: 無/[描述問題]
- **Cloud SQL 狀態**: STOPPED/RUNNABLE
- **預估成本影響**: $0
```

## 🚨 緊急聯絡

發現以下情況立即處理：
1. Cloud SQL 實例 tier 不是 micro
2. 每日帳單 > $10 USD
3. 生產環境服務中斷
4. 資料庫被誤刪

處理步驟：
1. 立即停止問題資源
2. 通知團隊
3. 記錄事件
4. 事後檢討

---

**記住**：寧可多檢查一次，不要產生巨額帳單！