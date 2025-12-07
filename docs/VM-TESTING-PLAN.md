# VM 測試計畫

## 📅 測試期間：2025-12-07 ~ 2025-12-14（7天）

## 🎯 測試目標

1. **穩定性驗證** - 確保 VM 能穩定運行 7x24 小時
2. **效能比較** - 與 Cloud Run 對比回應時間和錯誤率
3. **成本驗證** - 確認實際成本是否符合預期（NTD 430/月）
4. **資源監控** - 確保 2GB 記憶體足夠使用

---

## 🔍 每日檢查項目

### 1. 健康檢查（每天執行 2 次：早上 + 晚上）

```bash
# 健康狀態
curl -s http://34.81.38.211/api/health | jq '{status, db: .database.status, latency: .database.latency_ms}'

# 容器狀態
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker stats duotopia-backend --no-stream"

# 容器日誌（檢查錯誤）
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker logs duotopia-backend --tail=50 | grep -i error"
```

### 2. 效能測試（週一、週三、週五）

```bash
# 測試 10 次請求，記錄回應時間
for i in {1..10}; do
  time curl -s http://34.81.38.211/api/health > /dev/null
done
```

### 3. 資源監控（每天）

```bash
# VM 資源使用
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="free -h && df -h"
```

---

## 📊 測試記錄表

| 日期 | 健康狀態 | DB 延遲 (ms) | 記憶體使用 (MB) | CPU (%) | 錯誤數 | 備註 |
|------|---------|-------------|----------------|---------|--------|------|
| 12/07 | ✅ healthy | 298 | 122 | 0.27 | 0 | 初次部署 |
| 12/08 |  |  |  |  |  |  |
| 12/09 |  |  |  |  |  |  |
| 12/10 |  |  |  |  |  |  |
| 12/11 |  |  |  |  |  |  |
| 12/12 |  |  |  |  |  |  |
| 12/13 |  |  |  |  |  |  |
| 12/14 |  |  |  |  |  |  |

---

## 🚨 異常處理

### 如果健康檢查失敗：

```bash
# 1. 檢查容器狀態
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker ps -a"

# 2. 查看容器日誌
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker logs duotopia-backend --tail=100"

# 3. 重啟容器（最後手段）
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
  --command="docker restart duotopia-backend"
```

### 如果記憶體不足（>80%）：

```bash
# 升級到 e2-medium (4GB RAM)
gcloud compute instances set-machine-type duotopia-prod-vm \
  --zone=asia-east1-b \
  --machine-type=e2-medium

# 成本影響：NTD 430/月 → NTD 860/月（仍省 86%）
```

---

## 💰 成本追蹤

### 預期成本（12/07-12/14，7天）

```
VM (e2-small):    NTD 10/天 × 7 = NTD 70
靜態 IP (使用中): NTD 0
網路流量:         < NTD 5
────────────────────────────
總計:             約 NTD 75
```

### 實際成本檢查

```bash
# 查看 GCP 帳單（每 2 天檢查一次）
# https://console.cloud.google.com/billing/01D4D5-9A4E5D-5F8F8F/reports

# 或使用 CLI
gcloud billing accounts list
gcloud billing projects describe duotopia-472708
```

---

## ✅ 測試完成標準

測試期結束時，以下條件**全部滿足**才能正式切換：

- [ ] 7 天內健康檢查通過率 > 99.5%
- [ ] 平均回應時間 < Cloud Run（或相近）
- [ ] 資料庫連線穩定（無 degraded 狀態）
- [ ] 記憶體使用 < 70%（有足夠餘裕）
- [ ] 無重大錯誤或崩潰
- [ ] 實際成本符合預期（約 NTD 75/週）

---

## 📝 測試日誌

### 2025-12-07 17:30 - 初次部署

**狀態**：✅ 成功
- 健康檢查：✅ healthy
- 資料庫：✅ healthy (298ms)
- 記憶體：122 MB / 1.9 GB (6%)
- CPU：0.27%
- 問題修復：IPv6 連線問題（已改用 DATABASE_POOLER_URL）

**下次檢查**：2025-12-08 09:00

---

## 🔗 相關連結

- **VM 控制台**: https://console.cloud.google.com/compute/instances?project=duotopia-472708
- **部署工作流程**: https://github.com/Youngger9765/duotopia/actions/workflows/deploy-vm-prod.yml
- **健康檢查**: http://34.81.38.211/api/health
- **API 文件**: http://34.81.38.211/api/docs

---

## 📞 緊急聯絡

如果測試期間發現嚴重問題，可以快速回滾到 Cloud Run（不影響服務）：

```bash
# Cloud Run 仍在運行，只需要切換流量即可
# 無需執行任何指令，繼續使用原網域即可
```

VM 和 Cloud Run 可以並行運行，互不影響。
