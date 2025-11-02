# 🔒 超嚴格資安 Pre-Commit Hooks

**建立日期**: 2025-11-02
**狀態**: ✅ 已啟用並測試

---

## 🎯 目的

**絕對不允許任何 credentials 被 commit 到 git！**

本專案使用多層次的 pre-commit hooks 確保：
1. ✅ TapPay credentials 絕對不會被 commit
2. ✅ 已洩漏的 credentials 永久封鎖
3. ✅ Service Account keys 不會進入 repo
4. ✅ 所有敏感資訊都使用環境變數

---

## 🔥 TapPay Credentials 超嚴格檢查

### 檢查項目：

#### 1. **APP_KEY 模式偵測**
```regex
app_[a-zA-Z0-9]{60,70}
```
- ✅ 偵測所有以 `app_` 開頭 + 64 字元的字串
- ✅ 排除 placeholder: `your-`, `YOUR_`, `PLACEHOLDER`, `example`
- ✅ 排除檢查腳本自身

#### 2. **PARTNER_KEY 模式偵測**
```regex
partner_[a-zA-Z0-9]{60,70}
```
- ✅ 偵測所有以 `partner_` 開頭 + 64 字元的字串
- ✅ 排除 placeholder 和檢查腳本

#### 3. **MERCHANT_ID 模式偵測**
```regex
tppf_[a-zA-Z0-9_]+
```
- ✅ 偵測所有以 `tppf_` 開頭的字串
- ✅ 排除測試檔案中的 assert 驗證
- ✅ 排除使用 `getenv()` 的程式碼

#### 4. **已知洩漏 Credentials 黑名單**

以下 credential patterns 已經洩漏過，**永久封鎖**：
```bash
# ❌ BLACKLIST - 使用 pattern 偵測，不存實際值
app_4H0U1hnw[56 more chars]  # 已洩漏的 APP_KEY pattern
partner_WiCZj1tZ[56 more chars]  # 已洩漏的 PARTNER_KEY pattern
partner_PHgswvYE[56 more chars]  # 已洩漏的舊 PARTNER_KEY pattern
tppf_duotopia_***  # 已洩漏的 MERCHANT_ID pattern
164155  # Sandbox APP_ID
```

**偵測方式**: 使用 regex pattern 比對前綴，不在檔案中存完整 credential

#### 5. **硬編碼環境變數檢查**

檢查以下變數是否硬編碼：
```python
# Backend
TAPPAY_APP_KEY = "actual_value"  # ❌ 會被攔截
TAPPAY_PARTNER_KEY = "actual_value"  # ❌ 會被攔截
TAPPAY_MERCHANT_ID = "actual_value"  # ❌ 會被攔截

# Frontend
const APP_KEY = "actual_value"  # ❌ 會被攔截
```

正確做法：
```python
# Backend ✅
TAPPAY_APP_KEY = os.getenv('TAPPAY_APP_KEY')

# Frontend ✅
const APP_KEY = import.meta.env.VITE_TAPPAY_APP_KEY
```

#### 6. **文檔中的 Credentials 檢查**

文檔（`.md`, `.txt`）中的 credentials 必須脫敏：
```markdown
# ❌ 錯誤
APP_KEY: app_[完整64字元] (暴露完整credential)

# ✅ 正確
APP_KEY: app_XXXX... (已脫敏)
APP_KEY: ***REDACTED***
APP_KEY: [從 TapPay Portal 取得]
```

#### 7. **測試檔案中的 Credentials**

測試檔案不應包含真實 credentials：
```python
# ❌ 錯誤
def test_payment():
    app_key = "app_[real_credential]"  # 硬編碼真實credential

# ✅ 正確
def test_payment():
    app_key = settings.tappay_app_key  # 從環境變數
    # 或
    app_key = "mock_app_key_for_testing"
```

---

## 📋 所有安全檢查清單

### CRITICAL 級別（會阻止 commit）：

1. ✅ **TapPay Credentials 超嚴格檢查** - `check-tappay-credentials.sh`
   - APP_KEY, PARTNER_KEY, MERCHANT_ID 模式偵測
   - 黑名單檢查
   - 硬編碼環境變數檢查
   - 文檔/測試檔案檢查

2. ✅ **一般 Credentials 檢查** - `check-credentials.sh`
   - 通用 password/secret/key/token 模式

3. ✅ **Database URLs 檢查** - `check-database-urls.sh`
   - PostgreSQL, MySQL, MongoDB URLs

4. ✅ **API Keys 檢查** - `check-api-keys.sh`
   - OpenAI, GCP, AWS, Azure keys

5. ✅ **JWT Secrets 檢查** - `check-jwt-secrets.sh`
   - JWT secret keys

6. ✅ **.env 檔案檢查** - `check-env-files.sh`
   - 防止 `.env` 檔案被 commit

7. ✅ **全面安全審計** - `security-audit.sh`
   - 11 項檢查（包含 TapPay 增強檢查）
   - Supabase credentials
   - OpenAI API keys
   - Private keys (RSA, EC)
   - AWS credentials
   - Localhost URLs
   - Console.log sensitive data
   - Python logging sensitive data
   - TapPay credentials (enhanced)
   - MERCHANT_ID hardcoding
   - Service account key files
   - Security TODOs

---

## 🔧 使用方式

### 安裝 Pre-commit Hooks

```bash
# 安裝 pre-commit
pip install pre-commit

# 安裝 hooks
pre-commit install

# 測試所有 hooks
pre-commit run --all-files
```

### Commit 流程

```bash
# 1. 修改代碼
# 2. Add files
git add .

# 3. Commit（hooks 會自動執行）
git commit -m "feat: 新功能"

# 如果被攔截：
# ❌ COMMIT BLOCKED - TapPay Credentials Detected!
# 👉 修復問題後重新 commit
```

---

## ⚠️ 被攔截時怎麼辦？

### 錯誤 1: TapPay APP_KEY detected
```bash
❌ TapPay APP_KEY detected!
Pattern: app_XXXX... (64+ chars)
```

**解決方式：**
```python
# 移除硬編碼
- TAPPAY_APP_KEY = "app_[real_value]"
+ TAPPAY_APP_KEY = os.getenv('TAPPAY_APP_KEY')
```

### 錯誤 2: BLOCKED! Known leaked credential pattern
```bash
❌ BLOCKED! Known leaked APP_KEY pattern detected!
This APP_KEY was previously leaked and MUST NOT be committed!
```

**解決方式：**
- 這些 credential patterns 已經洩漏過
- **絕對不能** 再次 commit
- 到 TapPay Portal 重新生成新的 credentials
- 更新所有環境變數為新的 credentials

### 錯誤 3: Hardcoded TapPay environment variables
```bash
❌ Hardcoded TAPPAY_APP_KEY detected!
Use os.getenv('TAPPAY_APP_KEY') or import.meta.env.TAPPAY_APP_KEY instead!
```

**解決方式：**
```python
# Backend
- TAPPAY_APP_KEY = "actual_value"
+ TAPPAY_APP_KEY = os.getenv('TAPPAY_APP_KEY')

# Frontend
- const APP_KEY = "actual_value"
+ const APP_KEY = import.meta.env.VITE_TAPPAY_APP_KEY
```

### 錯誤 4: Service account key files found
```bash
❌ Service account key files found in repository!
./backend/github-actions-key.json
```

**解決方式：**
```bash
# 刪除 SA key 檔案
rm backend/github-actions-key.json

# 確認 .gitignore 包含
echo "*-key.json" >> .gitignore
echo "*-credentials.json" >> .gitignore
```

---

## 🎯 最佳實踐

### 1. 所有 Credentials 使用環境變數

```bash
# .env (gitignored)
TAPPAY_PRODUCTION_APP_KEY=app_xxx...
TAPPAY_PRODUCTION_PARTNER_KEY=partner_xxx...
TAPPAY_PRODUCTION_MERCHANT_ID=tppf_xxx...
```

### 2. 測試使用 Mock 或 Settings

```python
# ❌ 不要硬編碼
def test_payment():
    app_key = "app_[real_credential]"  # 真實credential

# ✅ 使用 settings
def test_payment():
    app_key = settings.tappay_app_key

# ✅ 使用 mock
def test_payment():
    app_key = "mock_test_key"
```

### 3. 文檔脫敏

```markdown
# ❌ 不要暴露完整 key
APP_KEY: app_[完整64字元credential]

# ✅ 脫敏處理
APP_KEY: app_XXXX... (64 chars, get from TapPay Portal)
APP_KEY: ***REDACTED***
```

### 4. GitHub Secrets 管理

```bash
# 設定 GitHub Secrets
gh secret set TAPPAY_PRODUCTION_APP_KEY --body "[YOUR_KEY]"
gh secret set TAPPAY_PRODUCTION_PARTNER_KEY --body "[YOUR_KEY]"
gh secret set TAPPAY_PRODUCTION_MERCHANT_ID --body "[YOUR_ID]"
```

---

## 🔍 檢查腳本位置

所有 security hooks 位於：
```
.github/hooks/security/
├── check-tappay-credentials.sh  # 🔥 TapPay 超嚴格檢查
├── check-credentials.sh          # 通用 credentials
├── check-database-urls.sh        # Database URLs
├── check-api-keys.sh             # API keys
├── check-jwt-secrets.sh          # JWT secrets
├── check-env-files.sh            # .env 檔案
└── security-audit.sh             # 全面審計 (11 項檢查)
```

---

## 📊 測試報告

```bash
# 執行完整測試
pre-commit run --all-files

# 結果範例：
TypeScript Check.........................................................Passed
Check for problematic Python import patterns.............................Passed
🔥 CRITICAL - Check TapPay credentials (STRICT)..........................Passed
Check for hardcoded credentials..........................................Passed
Check for exposed database URLs..........................................Passed
Check for exposed API keys...............................................Passed
Check for exposed JWT secrets............................................Passed
Prevent .env files from being committed..................................Passed
Comprehensive security audit (Enhanced)..................................Passed
Prevent database files from being committed..............................Passed
Check test files are in correct location.................................Passed
Check RLS in Alembic migrations..........................................Passed
check for added large files..............................................Passed
check for merge conflicts................................................Passed
```

---

## 🚨 絕對不能做的事

1. ❌ **絕對不要** 使用 `--no-verify` 跳過 hooks
   ```bash
   git commit --no-verify  # ❌ 絕對禁止！
   ```

2. ❌ **絕對不要** 硬編碼任何 TapPay credentials

3. ❌ **絕對不要** commit `.env` 檔案

4. ❌ **絕對不要** commit service account keys

5. ❌ **絕對不要** 在文檔中暴露完整 credentials

---

## ✅ 資安檢查清單

每次 commit 前自動檢查：
- [ ] 無 TapPay APP_KEY 硬編碼
- [ ] 無 TapPay PARTNER_KEY 硬編碼
- [ ] 無 TapPay MERCHANT_ID 硬編碼
- [ ] 無已知洩漏 credentials
- [ ] 無其他 API keys
- [ ] 無 database URLs
- [ ] 無 JWT secrets
- [ ] 無 .env 檔案
- [ ] 無 service account keys
- [ ] 文檔中 credentials 已脫敏
- [ ] 測試檔案使用 mock/settings

---

**最後更新**: 2025-11-02
**維護者**: Claude Code + Happy Engineering
**狀態**: ✅ Production Ready

**記住**: 資安無小事，每一個 commit 都要嚴格檢查！
