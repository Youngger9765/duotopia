# 🚀 Duotopia Browser MCP 快速上手指南

## 📝 什麼是 Browser MCP？

Browser MCP 讓 Claude Code 能夠**直接控制瀏覽器**，實現：
- ✅ 自動化 E2E 測試（不需要寫代碼）
- ✅ 互動式除錯（重現 bug 並截圖）
- ✅ 跨瀏覽器測試（Chrome, Safari, Firefox）
- ✅ Production 監控（背景自動測試）

---

## ⚡ 5 分鐘快速開始

### 1. 確認環境（已完成 ✅）

```bash
# 檢查安裝
cd /Users/young/project/duotopia
ls mcp-servers/browser/server.py  # 應該存在
cat .claude/mcp.json               # 應該有配置
```

### 2. 啟動開發環境

```bash
# Terminal 1: 啟動 Backend
cd backend && uvicorn main:app --reload

# Terminal 2: 啟動 Frontend
cd frontend && npm run dev
```

### 3. 在 Claude Code 中使用

**重要**：Claude Code 需要重啟才能載入 MCP Server

```bash
# 重啟 Claude Code
# macOS: Cmd+Q 退出，重新開啟
```

### 4. 測試 MCP 是否正常

在 Claude Code 中輸入：

```
我：測試 MCP browser 是否可用
```

Claude 應該會回應類似：
```
✅ MCP Browser Server 已連接
可用工具：navigate, click, fill, screenshot, get_console_logs...
```

---

## 🎯 實用案例

### 案例 1: 快速測試登入功能

```
我：測試教師登入功能

Claude 自動執行：
1. 打開 http://localhost:5173/teacher/login
2. 填寫 email 和 password
3. 點擊登入按鈕
4. 截圖成功畫面
5. 檢查 console 是否有錯誤

回報：✅ 登入成功，無 console 錯誤
```

### 案例 2: 測試我們剛修復的 Bug

```
我：測試新增學生後不重新整理頁面，直接派作業是否能看到新學生

Claude 自動執行：
1. 教師登入
2. 進入班級管理
3. 新增學生「測試學生A」
4. 不重新整理頁面
5. 打開派作業對話框
6. 截圖學生列表
7. 驗證「測試學生A」是否出現

回報：✅ 測試通過，新學生出現在列表中
```

### 案例 3: 互動式除錯

```
我：重現用戶回報的「派作業時學生列表顯示錯誤」

Claude：
1. 打開 production site
2. 用測試帳號登入
3. 打開 DevTools
4. 監聽 Network requests
5. 點選「指派新作業」
6. 截圖介面
7. 擷取 API response
8. 檢查 Console 錯誤

回報：❌ 發現問題
- API /api/teachers/classrooms/5/students 返回 []
- 但實際 DB 有 23 個學生
- 截圖：[顯示空列表的畫面]
```

### 案例 4: iOS Safari 測試

```
我：測試 iOS Safari 的錄音功能

Claude：
1. 啟動 iOS 模擬器
2. 打開 Safari
3. 進入學生作業頁面
4. 檢查 MediaRecorder API 支援
5. 嘗試錄音
6. 截圖結果

回報：❌ MediaRecorder is not defined
建議：iOS Safari 需要使用 WebRTC
```

---

## 🎬 內建測試場景（開箱即用）

無需寫任何代碼，直接使用！

### 1. 教師登入
```
我：執行教師登入測試
```

### 2. 學生登入
```
我：執行學生登入測試
```

### 3. 新增學生完整流程
```
我：測試新增學生功能
```

### 4. 派作業流程
```
我：測試派作業功能
```

### 5. Bug 修復驗證
```
我：測試新增學生後派作業的 bug 是否已修復
```

---

## 🔧 進階用法

### 自訂測試步驟

```
我：幫我測試以下流程：
1. 教師登入
2. 進入班級詳情
3. 切換到「作業管理」tab
4. 檢查是否有作業
5. 截圖作業列表
6. 檢查 console 是否有錯誤
```

Claude 會自動分解步驟並執行！

### 執行 JavaScript 檢查

```
我：檢查頁面中有多少個學生

Claude 執行：
execute_js(`
  return document.querySelectorAll('.student-card').length
`)

回報：找到 15 個學生元素
```

### 多步驟除錯

```
我：
1. 打開派作業對話框
2. 執行 JS 取得當前的 students state
3. 截圖
4. 檢查 Network tab 的 API 請求
5. 對比 API 返回的學生數和頁面顯示的學生數
```

---

## 🐛 疑難排解

### 問題 1: MCP Server 無法連接

**症狀**：Claude Code 找不到 `navigate`, `click` 等工具

**解決方法**：
```bash
# 1. 檢查 MCP 配置
cat .claude/mcp.json

# 2. 確認路徑正確
ls /Users/young/project/duotopia/mcp-servers/browser/server.py

# 3. 重啟 Claude Code（Cmd+Q）
```

### 問題 2: 瀏覽器無法開啟

**症狀**：執行 navigate 時報錯

**解決方法**：
```bash
# 重新安裝 Playwright browsers
playwright install chromium --force
```

### 問題 3: 測試太慢

**症狀**：每個測試都要重新登入

**解決方法**：
```
我：保持瀏覽器登入狀態，執行多個測試

Claude 會重用已登入的瀏覽器 session
```

### 問題 4: 截圖找不到

**症狀**：截圖存在哪裡？

**解決方法**：
```bash
# 預設路徑
ls /tmp/screenshot_*.png

# 或指定路徑
我：截圖並存到 ~/Downloads/test.png
```

---

## 💡 最佳實踐

### 1. 測試前先啟動本地環境

```bash
# 確保 frontend 和 backend 都在運行
curl http://localhost:5173  # Frontend
curl http://localhost:8000/api/health  # Backend
```

### 2. 使用語意化的問題描述

❌ 不好：「測試功能」
✅ 好：「測試新增學生後不重新整理頁面，直接派作業是否能看到新學生」

### 3. 善用截圖

```
我：每個步驟都截圖，方便我確認
```

### 4. 測試完關閉瀏覽器

```
我：測試完成，關閉瀏覽器
```

---

## 📊 與 Playwright 測試的比較

| 特性 | Playwright 測試 | Browser MCP |
|------|----------------|-------------|
| 需要寫代碼 | ✅ 需要 | ❌ 不需要 |
| 動態調整 | ❌ 固定流程 | ✅ 即時調整 |
| 視覺驗證 | ⚠️ 需要設定 | ✅ 自動截圖 |
| 除錯 | ❌ 需要重新執行 | ✅ 互動式探索 |
| 學習曲線 | ⚠️ 需要學 API | ✅ 自然語言 |
| CI/CD 整合 | ✅ 很好 | ⚠️ 需要額外設定 |

**建議**：
- ✅ 開發時用 Browser MCP（快速驗證）
- ✅ CI/CD 用 Playwright 測試（自動化回歸）

---

## 🎯 下一步

### 1. 試試看第一個測試

```
我：測試教師登入功能
```

### 2. 測試我們修復的 Bug

```
我：測試新增學生後派作業的功能
```

### 3. 自訂測試場景

參考 `mcp-servers/browser/scenarios/duotopia_scenarios.py`
新增你常用的測試流程

### 4. 整合到開發工作流程

每次修改代碼後：
```
我：
1. 測試相關功能
2. 截圖結果
3. 檢查 console 錯誤
4. 如果通過，我再 commit
```

---

## 📚 參考資料

- [詳細 README](../mcp-servers/browser/README.md)
- [Playwright 文件](https://playwright.dev/)
- [MCP 文件](https://modelcontextprotocol.io/)

---

**準備好了嗎？試試你的第一個測試吧！** 🚀

```
我：測試教師登入功能
```
