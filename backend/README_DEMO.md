# Duotopia Demo Data Management

這個目錄包含了用於管理 Duotopia 演示數據的工具和腳本。

## 📋 文件概述

- **`seed_demo.py`** - 演示數據種子腳本，將前端 MOCK 數據載入資料庫
- **`init_demo.sh`** - 一鍵初始化演示環境的便利腳本  
- **`check_demo.py`** - 檢查和顯示當前資料庫內容
- **`README_DEMO.md`** - 本說明文件

## 🚀 快速開始

### 方法一：使用一鍵初始化腳本（推薦）

```bash
cd backend
./init_demo.sh
```

這個腳本會：
- 檢查並激活虛擬環境
- 創建資料庫表格（如果不存在）
- 運行資料庫遷移
- 詢問是否清除現有數據
- 載入演示數據
- 可選擇啟動後端服務器

### 方法二：手動執行

```bash
cd backend

# 激活虛擬環境
source venv/bin/activate

# 創建資料庫表格
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"

# 載入演示數據（清除現有數據）
python seed_demo.py --clear

# 或者保留現有數據
python seed_demo.py

# 檢查載入的數據
python check_demo.py
```

## 📊 演示數據內容

基於前端 MOCK 數據，包含以下實體：

### 🏫 學校機構 (3個)
- 台北總校
- 新竹分校  
- 台中補習班

### 👥 用戶 (8個)
- 1個系統管理員
- 4個教師
- 3個機構負責人

### 👨‍🎓 學生 (6個)
- 分布在3個不同機構
- 部分已分班，部分待分班

### 🎓 班級 (4個)
- 六年一班、六年二班（台北總校）
- 五年三班（新竹分校）
- 國一甲班（台中補習班）

### 📚 課程 (9個)
- 基礎到高級不同級別
- 涵蓋會話、文法、寫作等類型

### 📋 作業 (3個)
- 不同類型的學習活動
- 包含進度追蹤

### 🔗 關聯關係
- 學生班級分配
- 班級課程對應
- 教師班級指派

## 🔑 登入憑證

系統提供以下測試帳號：

| 角色 | Email | 密碼 | 說明 |
|------|-------|------|------|
| 管理員 | admin@duotopia.com | admin123 | 系統管理員 |
| 教師 | teacher1@duotopia.com | teacher123 | 王老師 |
| 學生 | student1@duotopia.com | 20090828 | 陳小明 |

## 🛠️ 實用命令

### 檢查資料庫內容
```bash
python check_demo.py
```

### 清除所有數據並重新載入
```bash
python seed_demo.py --clear
```

### 僅新增數據（保留現有）
```bash
python seed_demo.py
```

### 重新創建資料庫表格
```bash
python -c "
from database import engine, Base
from models import *
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('Database recreated')
"
```

## 🔄 開發流程

1. **初始設置**：使用 `./init_demo.sh` 設置演示環境
2. **開發測試**：修改代碼並測試功能  
3. **重置數據**：需要時使用 `python seed_demo.py --clear` 重置
4. **檢查狀態**：使用 `python check_demo.py` 確認數據狀態

## 📝 注意事項

- 確保在 backend 目錄下執行所有腳本
- 虛擬環境必須已安裝所有依賴：`pip install -r requirements.txt`
- 資料庫檔案會創建在 `duotopia.db`
- 演示數據基於前端頁面的 MOCK 數據結構

## 🐛 故障排除

### 虛擬環境問題
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 資料庫連接問題
檢查 `database.py` 中的資料庫 URL 設定

### 權限問題
```bash
chmod +x init_demo.sh
```

### 後端服務器問題
```bash
# 停止現有服務器
pkill -f "uvicorn.*main:app"

# 重新啟動
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

🎉 **Happy Coding!** 如有問題，請檢查日誌檔案或聯繫開發團隊。