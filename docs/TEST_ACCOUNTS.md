# 測試帳號說明 (Test Accounts)

## 環境變數設定

所有測試帳號的密碼統一使用環境變數 `SEED_DEFAULT_PASSWORD`：

```bash
# 本地開發
export SEED_DEFAULT_PASSWORD="your_dev_password"

# 或在 .env 檔案中設定
SEED_DEFAULT_PASSWORD=your_dev_password
```

**重要**：
- ✅ 本地開發：自行設定 `SEED_DEFAULT_PASSWORD`
- ✅ Staging/Preview：使用 GitHub Secret `SEED_DEFAULT_PASSWORD`
- ❌ **絕不**在程式碼中硬編碼密碼

---

## 測試帳號列表

### 機構層級帳號

| 角色 | Email | 密碼 | 權限 |
|------|-------|------|------|
| 💜 機構擁有者 | owner@duotopia.com | `$SEED_DEFAULT_PASSWORD` | 最高權限 |
| 💙 機構管理員 | chen@duotopia.com | `$SEED_DEFAULT_PASSWORD` | 組織管理 |

### 學校層級帳號

| 角色 | Email | 密碼 | 所屬學校 |
|------|-------|------|----------|
| 🧡 學校管理員 | wang@duotopia.com | `$SEED_DEFAULT_PASSWORD` | 台北分校 |
| 💚 教師 | liu@duotopia.com | `$SEED_DEFAULT_PASSWORD` | 台北分校 |
| 💚 教師 | zhang@duotopia.com | `$SEED_DEFAULT_PASSWORD` | 新竹分校 |
| 💚 教師 | lee@duotopia.com | `$SEED_DEFAULT_PASSWORD` | 台中分校 |

---

## 測試組織資訊

- **組織名稱**: 測試機構
- **組織 ID**: `21a8a0c7-a5e3-4799-8336-fbb2cf1de91a`
- **學校**:
  - 台北分校
  - 新竹分校
  - 台中分校

---

## 如何建立測試資料

### 本地開發

```bash
# 1. 設定密碼環境變數
export SEED_DEFAULT_PASSWORD="dev123"

# 2. 執行 seed scripts
cd backend
python seed_local_org.py   # 建立組織和 owner
python seed_demo_data.py    # 建立學校、教師、教材
```

### Staging/Preview 環境

測試資料由 GitHub Actions 自動建立：
- Workflow: `.github/workflows/maintenance-seed-staging.yml`
- 密碼來源: GitHub Secret `SEED_DEFAULT_PASSWORD`

---

## 安全注意事項

⚠️ **重要**：
1. 本地 `.env` 檔案已加入 `.gitignore`，不會被提交
2. 絕不在程式碼、文檔、commit message 中硬編碼實際密碼
3. Staging/Production 使用不同的強密碼
4. 定期輪換 `SEED_DEFAULT_PASSWORD` (每 90 天)

---

## 疑難排解

### 密碼不正確

```bash
# 檢查環境變數是否設定
echo $SEED_DEFAULT_PASSWORD

# 如果為空，重新設定
export SEED_DEFAULT_PASSWORD="your_password"
```

### 帳號不存在

```bash
# 重新執行 seed scripts
cd backend
python seed_local_org.py
python seed_demo_data.py
```

---

**最後更新**: 2026-01-18
**維護者**: DevOps Team
