# Duotopia Browser MCP Server

使用 Playwright 控制瀏覽器進行自動化測試和除錯的 MCP Server

## 🎯 功能

- ✅ 自動化瀏覽器控制（導航、點擊、填寫表單）
- ✅ 截圖功能
- ✅ Console 日誌收集
- ✅ 執行 JavaScript
- ✅ Duotopia 專屬測試場景

## 📦 安裝

```bash
# 1. 安裝 Python 依賴
cd mcp-servers/browser
pip3 install -r requirements.txt

# 2. 安裝 Playwright 瀏覽器
playwright install chromium

# 3. 給 server.py 執行權限
chmod +x server.py
```

## ⚙️ 配置 Claude Code

### 方式一：全域配置（推薦用於多專案）

編輯 `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "duotopia-browser": {
      "command": "python3",
      "args": ["/Users/young/project/duotopia/mcp-servers/browser/server.py"],
      "env": {}
    }
  }
}
```

### 方式二：專案配置（推薦用於此專案）

在專案根目錄建立 `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "duotopia-browser": {
      "command": "python3",
      "args": ["./mcp-servers/browser/server.py"],
      "env": {}
    }
  }
}
```

## 🚀 使用方式

### 在 Claude Code 中使用

```typescript
// 我: "幫我測試新增學生功能"

Claude 會呼叫 MCP tools:
1. navigate → http://localhost:5173/teacher/login
2. fill → email input
3. fill → password input
4. click → submit button
5. wait_for_selector → dashboard
6. click → 新增學生
7. screenshot → 截圖結果
```

### 可用的 MCP Tools

| Tool | 說明 | 參數 |
|------|------|------|
| `navigate` | 導航到 URL | `url: string` |
| `click` | 點擊元素 | `selector: string` |
| `fill` | 填寫輸入欄位 | `selector: string, value: string` |
| `screenshot` | 截圖 | `path?: string, fullPage?: boolean` |
| `get_console_logs` | 取得 console 日誌 | - |
| `execute_js` | 執行 JavaScript | `code: string` |
| `wait_for_selector` | 等待元素出現 | `selector: string, timeout?: number` |
| `close_browser` | 關閉瀏覽器 | - |

## 🎬 內建測試場景

### 1. 教師登入
```python
DuotopiaScenarios.teacher_login()
```

### 2. 學生登入
```python
DuotopiaScenarios.student_login()
```

### 3. 新增學生完整流程
```python
DuotopiaScenarios.add_student_workflow()
```

### 4. 派作業流程
```python
DuotopiaScenarios.create_assignment_workflow()
```

### 5. 測試 Bug 修復（新增學生後派作業）
```python
DuotopiaScenarios.test_add_student_then_assign()
```

### 6. iOS Safari 錄音測試
```python
DuotopiaScenarios.test_ios_safari_recording()
```

## 📝 使用範例

### 範例 1: 快速測試登入功能

```
我: "測試教師登入功能"

Claude:
1. navigate("http://localhost:5173/teacher/login")
2. fill("input[name='email']", "teacher@example.com")
3. fill("input[name='password']", "password")
4. click("button[type='submit']")
5. screenshot()
結果: ✅ 登入成功
```

### 範例 2: 測試修復的 Bug

```
我: "測試新增學生後不重新整理頁面，直接派作業是否能看到新學生"

Claude 會自動執行:
1. 教師登入
2. 進入班級管理
3. 新增學生
4. 不重新整理頁面
5. 打開派作業對話框
6. 截圖學生列表
7. 驗證新學生是否出現
```

### 範例 3: 除錯 Production 問題

```
我: "重現用戶回報的「派作業時學生列表顯示錯誤」"

Claude:
1. 打開 production site
2. 用測試帳號登入
3. 打開 DevTools
4. 監聽 Network requests
5. 點選「指派新作業」
6. 截圖介面
7. 擷取 API response
8. 檢查 Console 錯誤
```

## 🔧 開發指南

### 新增測試場景

編輯 `scenarios/duotopia_scenarios.py`:

```python
@staticmethod
def my_custom_scenario(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
    """自訂測試場景"""
    return {
        "name": "my_custom_scenario",
        "description": "場景說明",
        "steps": [
            {"action": "navigate", "url": f"{base_url}/path"},
            {"action": "click", "selector": "button"},
            # ... more steps
        ]
    }
```

### 除錯 MCP Server

```bash
# 直接執行 server 檢查錯誤
python3 mcp-servers/browser/server.py

# 查看 Claude Code MCP logs
tail -f ~/.local/share/claude-code/logs/mcp-*.log
```

## 🐛 常見問題

### Q: MCP Server 無法啟動
**A**: 檢查 Python 版本（需要 3.10+）和依賴安裝

```bash
python3 --version
pip3 list | grep -E "mcp|playwright"
```

### Q: 瀏覽器無法開啟
**A**: 重新安裝 Playwright browsers

```bash
playwright install chromium --force
```

### Q: Claude Code 找不到 MCP Server
**A**: 檢查 `.claude/mcp.json` 的路徑是否正確（必須是絕對路徑）

```bash
pwd  # 取得當前目錄的絕對路徑
```

### Q: 如何測試 iOS Safari?
**A**: 需要實體 iOS 設備或完整的 iOS 模擬器，Playwright Webkit 引擎只是近似模擬

## 📊 效能優化

- 瀏覽器實例會持久化（不每次重啟）
- 使用 `headless=False` 方便除錯，production 可改為 `True`
- Network 和 Console logs 自動收集

## 🔐 安全注意事項

- ⚠️ 不要在測試場景中 hardcode 真實的帳密
- ⚠️ 使用 `.env` 檔案管理測試帳號
- ⚠️ 截圖檔案可能包含敏感資訊，注意儲存位置

## 📚 參考資料

- [Playwright 官方文件](https://playwright.dev/)
- [MCP 官方文件](https://modelcontextprotocol.io/)
- [Claude Code 文件](https://docs.claude.com/)

---

**建立日期**: 2025-10-29
**維護者**: Duotopia Team
**版本**: 1.0.0
