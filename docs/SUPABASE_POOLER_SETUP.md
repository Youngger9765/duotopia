# Supabase Pooler URL Setup for GitHub Actions

## 問題
Supabase 新專案只提供 IPv6 地址，GitHub Actions 不支援 IPv6，導致 CI/CD 無法連接資料庫。

## 解決方案（必須設定）
使用 Supabase Pooler (Supavisor) 連線，它提供 IPv4 地址。**這是 CI/CD 正常運作的必要設定！**

## 設定步驟

### 1. 取得 Pooler URL
1. 登入 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的專案
3. 進入 **Settings** → **Database**
4. 找到 **Connection string** 區塊
5. 選擇 **Connection pooling** 標籤
6. 複製 **Transaction** 模式的連線字串

連線字串格式應該類似：
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

### 2. 設定 GitHub Secret
1. 到你的 GitHub repository
2. Settings → Secrets and variables → Actions
3. 點擊 **New repository secret**
4. 名稱：`STAGING_SUPABASE_POOLER_URL`
5. 值：貼上 Pooler URL

### 3. 驗證設定
推送程式碼後，CI/CD 應該能成功執行 Alembic migrations。

## 注意事項

### Pooler vs Direct Connection
- **Direct Connection** (db.xxx.supabase.co)：用於應用程式長連線
- **Pooler Connection** (pooler.supabase.com)：用於短連線、CI/CD、serverless

### Transaction vs Session Mode
- **Transaction Mode**：每個 transaction 使用新連線（適合 migrations）
- **Session Mode**：保持連線狀態（適合需要 prepared statements 的應用）

## 其他解決方案（備選）

### 1. IPv4 Add-on ($4/月)
Supabase Pro 方案可購買專屬 IPv4 地址。

### 2. CloudFlare Warp
在 GitHub Actions 中使用 CloudFlare Warp 獲得 IPv6 支援。

### 3. 升級 Supabase CLI
升級到 1.136.3+ 版本，CLI 會自動使用 Supavisor。

## 參考資料
- [Supabase IPv6 Documentation](https://supabase.com/docs/guides/troubleshooting/supabase--your-network-ipv4-and-ipv6-compatibility)
- [Network Restrictions](https://supabase.com/docs/guides/platform/network-restrictions)