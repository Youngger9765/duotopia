# TapPay 環境切換指南

## 📋 概述

本專案支援 TapPay **Sandbox** 和 **Production** 兩套環境參數，可透過環境變數輕鬆切換。

---

## 🔑 環境參數說明

### Sandbox（測試環境）
- **用途**: 開發測試、功能驗證
- **特點**: 不會真的扣款，使用測試卡號
- **適用場景**: 本地開發、Staging 測試

### Production（正式環境）
- **用途**: 正式金流交易
- **特點**: 使用真實信用卡會真的扣款
- **測試方式**: 使用 TapPay 測試卡號可避免真實扣款
- **適用場景**: Production 部署

---

## 🎯 切換方式

### 方法 1: 修改 `.env` 檔案（推薦）

```bash
# 切換到 Sandbox
TAPPAY_ENV=sandbox

# 切換到 Production
TAPPAY_ENV=production
```

### 方法 2: 環境變數覆蓋

```bash
# 執行時指定環境
TAPPAY_ENV=production npm run dev
TAPPAY_ENV=production python backend/main.py
```

---

## 📁 環境變數配置

### Backend (.env.local / .env.staging / .env.production)

```bash
# ===== TAPPAY CONFIGURATION =====
# 切換環境：sandbox 或 production
TAPPAY_ENV=sandbox

# ----- Sandbox 參數 (測試環境) -----
TAPPAY_SANDBOX_APP_ID=164155
TAPPAY_SANDBOX_APP_KEY=app_xxx...
TAPPAY_SANDBOX_PARTNER_KEY=partner_xxx...
TAPPAY_SANDBOX_MERCHANT_ID=tppf_duotopia_GP_POS_3

# ----- Production 參數 (正式環境) -----
# 待取得 TapPay 正式帳號後填入
TAPPAY_PRODUCTION_APP_ID=YOUR_PRODUCTION_APP_ID_HERE
TAPPAY_PRODUCTION_APP_KEY=YOUR_PRODUCTION_APP_KEY_HERE
TAPPAY_PRODUCTION_PARTNER_KEY=YOUR_PRODUCTION_PARTNER_KEY_HERE
TAPPAY_PRODUCTION_MERCHANT_ID=YOUR_PRODUCTION_MERCHANT_ID_HERE
```

### Frontend (.env / frontend/.env.local)

```bash
# ===== TAPPAY CONFIGURATION =====
# 切換環境：sandbox 或 production
VITE_TAPPAY_SERVER_TYPE=sandbox

# ----- Sandbox 參數 (測試環境) -----
VITE_TAPPAY_SANDBOX_APP_ID=164155
VITE_TAPPAY_SANDBOX_APP_KEY=app_xxx...

# ----- Production 參數 (正式環境) -----
# 待取得 TapPay 正式帳號後填入
VITE_TAPPAY_PRODUCTION_APP_ID=YOUR_PRODUCTION_APP_ID_HERE
VITE_TAPPAY_PRODUCTION_APP_KEY=YOUR_PRODUCTION_APP_KEY_HERE
```

---

## 🚀 部署環境配置

### Local Development
```bash
# backend/.env.local
TAPPAY_ENV=sandbox

# frontend/.env
VITE_TAPPAY_SERVER_TYPE=sandbox
```

### Staging
```bash
# backend/.env.staging
TAPPAY_ENV=sandbox  # 或 production (測試正式環境)

# 部署時設定
gh secret set VITE_TAPPAY_SERVER_TYPE --body "sandbox" --env staging
```

### Production
```bash
# backend/.env.production
TAPPAY_ENV=sandbox  # 目前暫用 sandbox（等待正式帳號）

# 取得正式帳號後改為
TAPPAY_ENV=production
```

---

## 🧪 測試卡號

### TapPay 測試卡（可在 Production 環境使用）

```
卡號: 4242 4242 4242 4242
到期日: 任意未來日期（例：01/26）
CVV: 任意三碼（例：123）
3D 驗證碼: 任意值
```

**重要**: 即使在 Production 環境，使用此測試卡號也**不會真的扣款**。

---

## 📊 環境切換檢查清單

### 切換到 Production 前必須確認：

- [ ] 已取得 TapPay 正式環境 credentials
- [ ] 已在 `.env` 填入正式參數
- [ ] Backend `settings.tappay_partner_key` 正確讀取
- [ ] Frontend `import.meta.env.VITE_TAPPAY_PRODUCTION_APP_KEY` 有值
- [ ] 使用測試卡號進行測試
- [ ] 確認 API 回應正確（不是 sandbox 的 mock 資料）
- [ ] 付款流程完整測試通過

### 切換指令範例：

```bash
# 1. 修改環境變數
# backend/.env.staging
TAPPAY_ENV=production

# frontend/.env.staging
VITE_TAPPAY_SERVER_TYPE=production

# 2. 重新部署
git add .
git commit -m "chore: switch TapPay to production mode"
git push origin staging

# 3. 驗證環境
curl https://staging-backend.example.com/api/health | jq '.tappay_env'
# 應該顯示 "production"
```

---

## 🔐 取得 Production Credentials

### 步驟：

1. 登入 TapPay Portal: https://portal.tappaysdk.com/
2. 切換到「正式環境」（Production）
3. 複製以下資訊：
   - **APP_ID**
   - **APP_KEY**
   - **PARTNER_KEY**
   - **MERCHANT_ID**
4. 填入對應的 `.env` 檔案：
   ```bash
   TAPPAY_PRODUCTION_APP_ID=<你的 APP_ID>
   TAPPAY_PRODUCTION_APP_KEY=<你的 APP_KEY>
   TAPPAY_PRODUCTION_PARTNER_KEY=<你的 PARTNER_KEY>
   TAPPAY_PRODUCTION_MERCHANT_ID=<你的 MERCHANT_ID>
   ```

---

## ⚠️ 注意事項

### 🚨 絕對不要在 Production 使用測試 Merchant

```bash
# ❌ 錯誤（使用公用測試 Merchant）
TAPPAY_PRODUCTION_MERCHANT_ID=GlobalTesting_CTBC

# ✅ 正確（使用你自己的 Merchant）
TAPPAY_PRODUCTION_MERCHANT_ID=tppf_duotopia_xxx
```

### 🔒 安全建議

1. **不要 commit credentials** - 所有 `.env` 檔案已在 `.gitignore`
2. **使用 GitHub Secrets** - CI/CD 環境變數使用 `gh secret set`
3. **定期輪換金鑰** - 建議每季度更新 PARTNER_KEY
4. **監控異常交易** - 設定 TapPay webhook 接收交易通知

---

## 🛠️ 程式碼實現

### Backend 自動切換邏輯

```python
# backend/core/config.py
class Settings:
    TAPPAY_ENV: Literal["sandbox", "production"] = os.getenv("TAPPAY_ENV", "sandbox")

    @property
    def tappay_partner_key(self) -> str:
        if self.TAPPAY_ENV == "production":
            return os.getenv("TAPPAY_PRODUCTION_PARTNER_KEY", "")
        return os.getenv("TAPPAY_SANDBOX_PARTNER_KEY", "")
```

### Frontend 自動切換邏輯

```typescript
// frontend/src/components/payment/TapPayPayment.tsx
const SERVER_TYPE = import.meta.env.VITE_TAPPAY_SERVER_TYPE || "sandbox";

const APP_KEY =
  SERVER_TYPE === "production"
    ? import.meta.env.VITE_TAPPAY_PRODUCTION_APP_KEY
    : import.meta.env.VITE_TAPPAY_SANDBOX_APP_KEY;
```

---

## 📞 支援

遇到問題？

1. 檢查 `.env` 檔案參數是否正確
2. 確認 `TAPPAY_ENV` / `VITE_TAPPAY_SERVER_TYPE` 設定
3. 查看 TapPay 文件: https://docs.tappaysdk.com/
4. 聯絡 TapPay 技術支援

---

**最後更新**: 2025-11-02
