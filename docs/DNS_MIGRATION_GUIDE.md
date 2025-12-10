# DNS 遷移指南 - Duotopia Production 從 VM 遷移至 Cloud Run

## 📋 遷移摘要

**當前狀態**:
- ✅ Production Cloud Run 已部署並完全正常運行
- ✅ 域名 `duotopia.co` 已映射到 Cloud Run Frontend
- ✅ SSL 證書已自動配置
- ⏸️ VM (34.81.38.211) 仍在運行，作為緊急回滾選項

**遷移目標**:
- 無縫切換流量從 VM 到 Cloud Run
- 零停機時間
- 保留 VM 作為回滾選項

---

## 🔍 當前 DNS 配置檢查

### 步驟 1: 確認當前 DNS 記錄

執行以下命令檢查當前 DNS 配置：

```bash
# 檢查 duotopia.co 的 A 記錄
dig duotopia.co A +short

# 檢查 duotopia.co 的 AAAA 記錄（IPv6）
dig duotopia.co AAAA +short

# 檢查完整的 DNS 資訊
dig duotopia.co ANY
```

**預期結果**（當前可能指向 VM）:
```
# A 記錄（IPv4）
34.81.38.211

# 或者已經指向 Cloud Run（如果之前已配置）
216.239.32.21
216.239.34.21
216.239.36.21
216.239.38.21
```

---

## 🎯 Cloud Run DNS 配置資訊

### Cloud Run 要求的 DNS 記錄

根據 Google Cloud 的域名映射配置，您需要設定以下 DNS 記錄：

#### A 記錄（IPv4，必須）
```
Type: A
Name: @（或留空，代表根域名 duotopia.co）
Value:
  - 216.239.32.21
  - 216.239.34.21
  - 216.239.36.21
  - 216.239.38.21
TTL: 300（5 分鐘，建議初期使用較短 TTL）
```

#### AAAA 記錄（IPv6，可選但建議）
```
Type: AAAA
Name: @（或留空）
Value:
  - 2001:4860:4802:32::15
  - 2001:4860:4802:34::15
  - 2001:4860:4802:36::15
  - 2001:4860:4802:38::15
TTL: 300
```

---

## 🚀 遷移執行步驟（需要用戶手動操作）

### 步驟 1: 登入 DNS 提供商控制台

請登入您的域名 DNS 管理控制台（例如：GoDaddy, Namecheap, Cloudflare, Google Domains 等）。

### 步驟 2: 備份當前 DNS 配置

**重要**: 在修改前，請截圖或記錄當前的 DNS 配置，以便回滾。

當前配置（需要刪除或修改）:
```
Type: A
Name: @
Value: 34.81.38.211  # VM IP
```

### 步驟 3: 更新 A 記錄

#### 選項 A: 如果 DNS 提供商支援多個 A 記錄
1. 刪除舊的 A 記錄 (`34.81.38.211`)
2. 添加 4 個新的 A 記錄：
   - `216.239.32.21`
   - `216.239.34.21`
   - `216.239.36.21`
   - `216.239.38.21`

#### 選項 B: 如果 DNS 提供商只支援單一 A 記錄
- 某些 DNS 提供商只允許一個 A 記錄，此時請使用第一個 IP: `216.239.32.21`
- **注意**: 這會降低可用性，建議使用支援多個 A 記錄的 DNS 提供商

### 步驟 4: 添加 AAAA 記錄（推薦）

添加以下 4 個 AAAA 記錄（如果 DNS 提供商支援）:
```
2001:4860:4802:32::15
2001:4860:4802:34::15
2001:4860:4802:36::15
2001:4860:4802:38::15
```

### 步驟 5: 設定 TTL

- **初期**: 設定 TTL 為 `300`（5 分鐘），方便快速回滾
- **穩定後**: 可以增加到 `3600`（1 小時）或 `86400`（1 天）

---

## ✅ 驗證遷移是否成功

### 步驟 1: 等待 DNS 傳播

DNS 更新需要時間傳播（通常 5-30 分鐘，取決於 TTL）。

### 步驟 2: 檢查 DNS 解析

```bash
# 檢查 DNS 是否已更新
dig duotopia.co A +short

# 預期結果應該顯示 Cloud Run 的 IP
# 216.239.32.21
# 216.239.34.21
# 216.239.36.21
# 216.239.38.21
```

### 步驟 3: 測試網站訪問

```bash
# 健康檢查
curl -I https://duotopia.co/api/health

# 預期結果: HTTP/2 200
# 並包含 {"status":"healthy","environment":"production"}

# 測試前端
curl -I https://duotopia.co/

# 預期結果: HTTP/2 200
```

### 步驟 4: 瀏覽器測試

1. 訪問 https://duotopia.co
2. 檢查 SSL 證書是否有效（應該由 Google Trust Services 簽發）
3. 測試主要功能（登入、API 調用等）

### 步驟 5: 檢查 SSL 證書

```bash
# 查看證書資訊
openssl s_client -connect duotopia.co:443 -servername duotopia.co < /dev/null 2>/dev/null | openssl x509 -noout -text | grep -A 2 "Subject:"

# 預期結果應該顯示:
# Subject: CN = duotopia.co
# Issuer: Google Trust Services
```

---

## 🔍 監控與觀察期

### 1-7 天觀察期

在 DNS 切換後，建議監控以下指標：

#### Cloud Run 指標
```bash
# 查看 Cloud Run 日誌
gcloud run logs read duotopia-production-backend --limit=50 --region=asia-east1

# 查看 Cloud Run 指標（需要 GCP Console）
# - 請求數量
# - 錯誤率
# - 回應時間
# - 實例數量
```

#### VM 流量監控
```bash
# SSH 到 VM 檢查是否還有流量
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# 查看容器日誌
docker logs -f --tail=50 duotopia-backend

# 如果日誌停止更新，表示流量已完全切換
```

### 觀察重點
1. **Cloud Run 錯誤率**: 應該 < 1%
2. **Cloud Run 回應時間**: 應該 < 1s (首次冷啟動可能 ~3s)
3. **VM 流量**: 應該逐漸減少到零
4. **用戶反饋**: 詢問用戶是否有異常

---

## 🔄 回滾方案（如果出現問題）

### 快速回滾到 VM

如果遷移後發現問題，可以快速回滾：

#### 步驟 1: 恢復 DNS 記錄
```
Type: A
Name: @
Value: 34.81.38.211  # VM IP
TTL: 300
```

#### 步驟 2: 刪除 Cloud Run DNS 記錄
刪除之前添加的 4 個 A 記錄和 4 個 AAAA 記錄

#### 步驟 3: 等待 DNS 傳播（5-30 分鐘）

#### 步驟 4: 驗證回滾
```bash
dig duotopia.co A +short
# 應該顯示: 34.81.38.211

curl -I https://duotopia.co/
# 應該能正常訪問
```

### 部分回滾（灰度發布）

**進階方案**: 如果只想讓部分流量切換到 Cloud Run：
1. 使用支援權重的 DNS 服務（如 Cloudflare Load Balancer）
2. 設定 80% 流量到 Cloud Run，20% 到 VM
3. 逐步增加 Cloud Run 流量比例

---

## 📅 遷移時間建議

### 最佳遷移時間
- **平日**: 週二或週三
- **時間**: 台灣時間上午 10:00 - 12:00（用戶活躍度較低）
- **避免**: 週末、月初月末、重大活動期間

### 遷移執行時間表
```
09:00 - 準備階段
  - 確認 Cloud Run 正常運行
  - 備份當前 DNS 配置
  - 通知團隊進入遷移模式

10:00 - DNS 更新
  - 修改 DNS A 記錄
  - 添加 AAAA 記錄

10:05 - 10:30 - DNS 傳播等待期
  - 每 5 分鐘檢查一次 DNS 解析
  - 監控 Cloud Run 日誌

10:30 - 11:00 - 驗證階段
  - 瀏覽器測試
  - API 測試
  - SSL 證書檢查

11:00 - 12:00 - 穩定觀察期
  - 監控錯誤率
  - 檢查 VM 流量是否下降
  - 準備回滾方案（如需要）

12:00 - 遷移完成（或回滾）
```

---

## 🛠️ 常見問題排查

### Q1: DNS 更新後網站無法訪問
**原因**: DNS 傳播未完成，或本地 DNS 快取
**解決**:
```bash
# 清除本地 DNS 快取
# macOS
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# Windows
ipconfig /flushdns

# Linux
sudo systemd-resolve --flush-caches
```

### Q2: SSL 證書錯誤
**原因**: 瀏覽器快取了舊證書
**解決**:
- 清除瀏覽器快取
- 使用無痕模式測試
- 等待 5-10 分鐘

### Q3: API 回應緩慢
**原因**: Cloud Run 冷啟動
**解決**:
- 這是正常現象，首次請求可能需要 2-3 秒
- 後續請求應該在 500ms 內
- 如果持續緩慢，檢查 Cloud Run 日誌

### Q4: 部分用戶仍然連接到 VM
**原因**: DNS 快取（ISP 或本地）
**解決**:
- 等待 TTL 過期（5-30 分鐘）
- 無需特別處理，會自動切換

---

## 📊 遷移檢查清單

### 遷移前檢查
- [ ] Cloud Run Production Backend 正常運行
- [ ] Cloud Run Production Frontend 正常運行
- [ ] 健康檢查通過 (`curl https://duotopia.co/api/health`)
- [ ] SSL 證書已自動配置
- [ ] VM 保持運行（作為回滾選項）
- [ ] 備份當前 DNS 配置（截圖）

### DNS 更新檢查
- [ ] A 記錄更新為 Cloud Run IP（4 個）
- [ ] AAAA 記錄添加（4 個，可選）
- [ ] TTL 設定為 300（5 分鐘）
- [ ] 刪除或註釋舊的 VM IP 記錄

### 遷移後驗證
- [ ] DNS 解析正確 (`dig duotopia.co A +short`)
- [ ] HTTPS 訪問正常 (`curl -I https://duotopia.co/`)
- [ ] API 健康檢查通過
- [ ] 前端頁面正常載入
- [ ] SSL 證書有效（Google Trust Services）
- [ ] 瀏覽器測試通過（登入、主要功能）

### 1-2 週觀察期
- [ ] Cloud Run 錯誤率 < 1%
- [ ] Cloud Run 回應時間 < 1s
- [ ] VM 流量降至零
- [ ] 無用戶投訴或異常反饋
- [ ] 成本符合預期（$5-10/月）

### 遷移完成後清理（2 週後）
- [ ] 確認 Cloud Run 穩定運行 2 週
- [ ] 停止 VM 容器
- [ ] 刪除 VM 實例
- [ ] 釋放 Static IP (34.81.38.211)
- [ ] 更新文件（標記 VM 已關閉）

---

## 💡 重要提醒

1. **不要刪除 VM**: 在確認 Cloud Run 穩定運行 1-2 週後再刪除
2. **TTL 策略**: 初期使用短 TTL（300s），穩定後再增加
3. **監控**: 遷移後 24 小時內密切監控日誌和指標
4. **通知**: 建議通知重要用戶遷移時間（如有計劃停機）
5. **回滾準備**: 隨時準備好回滾方案，確保能在 10 分鐘內恢復

---

## 📞 支援

如果遷移過程中遇到問題：

1. **檢查日誌**: `gcloud run logs read duotopia-production-backend --limit=100`
2. **健康檢查**: `curl https://duotopia.co/api/health`
3. **回滾**: 立即恢復 DNS 到 VM IP (34.81.38.211)
4. **聯繫**: 查看 GitHub Actions 部署日誌

---

**遷移執行人**: [您的名字]
**遷移日期**: [待定]
**文件版本**: 1.0
**最後更新**: 2025-12-10
