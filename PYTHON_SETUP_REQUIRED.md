# 🚨 重要：環境設置指南 (當前狀態)

## 當前檢測結果

### ✅ 已安裝

- **Node.js**: 已在 `C:\Program Files\nodejs` (✓)
- **Git**: v2.52.0 (✓)

### ❌ 未安裝/未在 PATH

- **Python**: 未找到或未在 PATH 中

---

## 立即修復方案

### 選項 A: 安裝 Python (推薦，5 分鐘)

1. 訪問 https://www.python.org/downloads/
2. 下載 **Python 3.12** (最新穩定版)
3. 執行安裝程序
4. ⚠️ **重要**:
   - 勾選 ✓ "Add Python to PATH"
   - 勾選 ✓ "Install for all users" (如果可能)
5. 點擊 "Install Now"
6. 重啟 PowerShell
7. 驗證: `python --version`

### 選項 B: 如果已安裝 Python 但不在 PATH

運行以下命令找出 Python 位置:

```powershell
Get-ChildItem "C:\Users\IDEA3C\AppData\Local\Programs\Python*" -Directory -ErrorAction SilentlyContinue
Get-ChildItem "C:\Program Files\Python*" -Directory -ErrorAction SilentlyContinue
```

然後使用完整路徑執行:

```powershell
# 例如 (調整為你的實際路徑)
& "C:\Users\IDEA3C\AppData\Local\Programs\Python312\python.exe" -m venv venv
```

### 選項 C: 使用系統級 Python

如果你有 Windows Store 的 Python 或其他安裝:

```powershell
# 檢查 Windows Store Python
py --version
py -m venv venv
```

---

## 下一步 (安裝 Python 後)

### 1️⃣ 建立虛擬環境

```powershell
cd C:\Users\IDEA3C\Documents\duotopia\backend
python -m venv venv
```

### 2️⃣ 啟動虛擬環境

```powershell
.\venv\Scripts\Activate.ps1
```

### 3️⃣ 安裝依賴

```powershell
pip install -r requirements.txt
```

### 4️⃣ 啟動後端

```powershell
uvicorn main:app --reload --port 8080
```

---

## 前端設置 (Node.js 已經可用！)

```powershell
cd C:\Users\IDEA3C\Documents\duotopia\frontend
npm install
npm run dev
```

前端會在 http://localhost:5173 運行

---

## 快速檢查命令

```powershell
# 確認 Node.js
node --version
npm --version

# 確認 Python (安裝後)
python --version
py --version  # 替代方案

# 確認 Git
git --version
```

---

## 常見問題

### Q: Python 安裝後仍顯示 "not found"

**A**: 重啟 PowerShell 或重啟電腦讓 PATH 更新

### Q: 我有多個 Python 版本

**A**: 使用 `py --list-paths` 查看所有版本

### Q: 執行政策仍然限制腳本?

**A**: 已在前面設置為 RemoteSigned，應該可以了

---

## 立即行動

👉 **優先級 1**: 安裝 Python
👉 **優先級 2**: 後端虛擬環境設置  
👉 **優先級 3**: 前端依賴安裝

預期總時間: 10-15 分鐘

---

**更新**: 2025-12-21 (由 GitHub Copilot 建立)
