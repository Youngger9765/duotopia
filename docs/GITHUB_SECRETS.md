# GitHub Secrets 設定指南

## 必須設定的 Secrets

在 GitHub Repository Settings → Secrets and variables → Actions 中設定以下 secrets：

### Staging 環境
- `STAGING_DATABASE_URL`: `postgresql://[USERNAME]:[PASSWORD]@[IP]:5432/[DATABASE]`
- `STAGING_JWT_SECRET`: (使用安全的隨機字串)

### Production 環境（未來使用）
- `PROD_DATABASE_URL`: (待設定)
- `PROD_JWT_SECRET`: (待產生安全金鑰)

## 設定步驟

1. 進入 GitHub Repository 頁面
2. 點擊 Settings
3. 左側選單選擇 Secrets and variables → Actions
4. 點擊 "New repository secret"
5. 輸入 Name 和 Secret value
6. 點擊 "Add secret"

## 注意事項

- **絕對不要**在程式碼中直接寫入密碼或 IP
- **絕對不要**在 commit message 中包含敏感資訊
- 定期更換密碼和 JWT secret
- 使用強密碼（建議 32 字元以上）

## 安全最佳實踐

1. **資料庫密碼**：使用複雜密碼，定期更換
2. **JWT Secret**：使用隨機產生的長字串
3. **IP 限制**：考慮使用 Cloud SQL Proxy 而非公開 IP
4. **存取控制**：限制誰可以存取這些 secrets