# GoDaddy DNS 遷移到 VM 指南

## 🎯 目標

將 Duotopia 網域從 Cloud Run 切換到 VM (34.81.38.211)

**預計時間**：10-15 分鐘
**用戶影響**：零（無縫切換）
**風險**：極低（隨時可回滾）

---

## 📋 前置檢查清單

- [ ] VM 全棧部署完成（前端 + 後端 + Nginx）
- [ ] VM 健康檢查通過：`curl http://34.81.38.211/api/health`
- [ ] 測試 VM 前端：`curl http://34.81.38.211/`
- [ ] GoDaddy 帳號登入資訊準備好
- [ ] 記錄當前 Cloud Run IP（以便回滾）

---

## 🚀 GoDaddy DNS 切換步驟

### 步驟 1：準備階段（提前 24 小時，可選但推薦）

**目的**：降低 TTL 讓切換更快

1. 登入 GoDaddy：https://dcc.godaddy.com/
2. 點擊「DNS」→「管理區域」
3. 找到你的網域 A 記錄
4. 點擊「編輯」
5. **將 TTL 從 1 小時改為 10 分鐘**
6. 儲存

**效果**：24 小時後切換只需要 10 分鐘生效

---

### 步驟 2：切換當天

#### 2.1 登入 GoDaddy DNS 管理

1. 前往：https://dcc.godaddy.com/
2. 我的產品 → 網域
3. 點擊你的網域旁邊的「DNS」按鈕

#### 2.2 修改 A 記錄

找到這樣的記錄：
```
類型    名稱    值                    TTL
A       @       [Cloud Run IP]       1 小時
```

修改為：
```
類型    名稱    值              TTL
A       @       34.81.38.211   10 分鐘
```

**具體操作**：
1. 點擊該記錄旁的「編輯」（鉛筆圖示）
2. 將「指向」欄位改為：`34.81.38.211`
3. 將 TTL 改為：`600 秒`（10 分鐘）
4. 點擊「儲存」

#### 2.3 如果有 www 子網域

找到：
```
類型    名稱    值                    TTL
A       www     [Cloud Run IP]       1 小時
```

同樣修改為：
```
類型    名稱    值              TTL
A       www     34.81.38.211   10 分鐘
```

---

### 步驟 3：驗證切換

#### 3.1 檢查 DNS 傳播（5-10 分鐘後）

```bash
# 檢查 DNS 是否已更新
dig yourdomain.com +short

# 期望看到
34.81.38.211
```

#### 3.2 測試網站訪問

```bash
# 測試主網域
curl http://yourdomain.com/api/health

# 測試 www
curl http://www.yourdomain.com/api/health
```

#### 3.3 瀏覽器測試

1. 清除瀏覽器快取（Cmd+Shift+R 或 Ctrl+Shift+R）
2. 訪問你的網域
3. 確認功能正常：
   - [ ] 登入
   - [ ] 錄音
   - [ ] 查看資料

---

## 🛡️ SSL/HTTPS 配置（切換後）

### 選項 A：Cloudflare（推薦，最簡單）

**優點**：
- ✅ 免費
- ✅ 自動 SSL
- ✅ 免費 CDN
- ✅ DDoS 防護
- ✅ 一鍵設定

**步驟**：
1. 註冊 Cloudflare：https://dash.cloudflare.com/sign-up
2. 新增網站 → 輸入你的網域
3. Cloudflare 會掃描你的 DNS 記錄
4. 確認記錄正確（A 記錄指向 34.81.38.211）
5. 複製 Cloudflare 提供的 Nameservers（2 個）
6. 回到 GoDaddy：
   - 網域設定 → Nameservers
   - 選擇「自訂 Nameservers」
   - 貼上 Cloudflare 的 2 個 Nameservers
7. 儲存並等待（最多 24 小時，通常 1 小時內）
8. 回到 Cloudflare 開啟 SSL：
   - SSL/TLS → 概觀 → 選擇「彈性」
9. 完成！自動 HTTPS ✅

---

### 選項 B：Let's Encrypt（免費，需手動）

**在 VM 上執行**：

```bash
# 1. SSH 到 VM
gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b

# 2. 安裝 Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# 3. 取得並配置 SSL 憑證
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 4. 測試自動續期
sudo certbot renew --dry-run

# 完成！憑證會自動續期
```

**效果**：
- ✅ 免費 SSL
- ✅ 自動續期
- ✅ Nginx 自動配置 HTTPS
- ❌ 需要手動在 VM 上操作

---

## 🔄 回滾計畫（如果需要）

### 快速回滾（2-10 分鐘）

如果 VM 有問題，立即切回 Cloud Run：

1. 登入 GoDaddy DNS
2. 將 A 記錄改回：`[Cloud Run IP]`
3. TTL 設為：`300 秒`（5 分鐘）
4. 儲存
5. 5-10 分鐘後生效

**Cloud Run IP 在哪裡找**：
```bash
# 查詢 Cloud Run 服務 URL
gcloud run services describe duotopia-production-backend \
  --region=asia-east1 \
  --format='value(status.url)'

# 解析 IP
nslookup [上面的 URL]
```

---

## 📊 切換時間表

| 時間點 | 操作 | 預計耗時 |
|--------|------|---------|
| **D-1 天** | 降低 GoDaddy DNS TTL 到 10 分鐘 | 2 分鐘 |
| **D-Day 00:00** | 修改 GoDaddy A 記錄 | 2 分鐘 |
| **D-Day 00:10** | 驗證 DNS 傳播 | 1 分鐘 |
| **D-Day 00:15** | 測試網站功能 | 5 分鐘 |
| **D-Day 01:00** | 配置 SSL（Cloudflare 或 Certbot） | 5-10 分鐘 |
| **D+1 天** | 確認穩定，TTL 改回 1 小時 | 2 分鐘 |

**總操作時間**：15-20 分鐘
**等待時間**：10-30 分鐘（DNS 傳播）

---

## ✅ 驗證清單

切換完成後確認：

### DNS 層
- [ ] `dig yourdomain.com +short` 回傳 `34.81.38.211`
- [ ] `dig www.yourdomain.com +short` 回傳 `34.81.38.211`

### HTTP 層
- [ ] `curl http://yourdomain.com/` 回傳前端頁面
- [ ] `curl http://yourdomain.com/api/health` 回傳 `{"status":"healthy"}`

### HTTPS 層（如果已配置 SSL）
- [ ] `curl https://yourdomain.com/` 正常訪問
- [ ] 瀏覽器顯示綠色鎖頭

### 功能測試
- [ ] 登入功能正常
- [ ] 錄音功能正常
- [ ] 資料顯示正常
- [ ] 支付功能正常（測試環境）

---

## 💰 成本影響

### 切換期間（24 小時）
- Cloud Run：繼續運行（NTD 8）
- VM：已經運行（NTD 14）
- **額外成本**：約 NTD 8（可忽略）

### 切換後
- Cloud Run：可關閉或保留作為備援
- VM：正式運行
- **月成本**：NTD 430（省 93%）

---

## 🆘 緊急聯絡

如果切換過程有問題：

1. **立即回滾**（參考上面的回滾計畫）
2. **檢查 VM 狀態**：
   ```bash
   gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
     --command="docker ps -a"
   ```
3. **查看日誌**：
   ```bash
   gcloud compute ssh young@duotopia-prod-vm --zone=asia-east1-b \
     --command="docker logs duotopia-nginx"
   ```

---

## 📝 注意事項

1. **提前通知用戶**（可選）：
   - 「系統維護通知：將於 XX 時間進行伺服器優化」
   - 實際上用戶不會感知，但預告可以避免疑慮

2. **選擇低峰時段**（推薦）：
   - 半夜 2-4 AM
   - 週末早晨
   - 用戶量最少時

3. **保留 Cloud Run**（推薦保留 1 週）：
   - 確認 VM 穩定後再關閉
   - 作為緊急備援

4. **監控成本**：
   - 切換後每天檢查 GCP 帳單
   - 確認成本確實下降

---

## 🎯 下一步

部署完成後：
1. [ ] 測試 VM 全功能（登入、錄音、支付）
2. [ ] 執行 7 天穩定性測試
3. [ ] 選擇切換日期
4. [ ] 提前 24 小時降低 GoDaddy TTL
5. [ ] 執行切換
6. [ ] 配置 SSL
7. [ ] 驗證功能
8. [ ] 監控 1 週
9. [ ] 關閉 Cloud Run（可選）

---

**準備好了隨時可以切換！** 🚀
