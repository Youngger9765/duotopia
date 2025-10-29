#!/usr/bin/env python3
"""
Duotopia Browser MCP Server
使用 Playwright 控制瀏覽器進行自動化測試和除錯
"""

import base64
from datetime import datetime
from typing import Optional

# FastMCP (最簡單的 MCP Server 框架)
from mcp.server.fastmcp import FastMCP

# Playwright
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# 初始化 MCP Server
mcp = FastMCP("duotopia-browser")

# 全域變數
_playwright = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_page: Optional[Page] = None
_console_logs = []


async def get_page() -> Page:
    """取得或建立 Page instance"""
    global _playwright, _browser, _context, _page

    if _page is None:
        if _playwright is None:
            _playwright = await async_playwright().start()
        if _browser is None:
            _browser = await _playwright.chromium.launch(
                headless=False,  # 顯示瀏覽器視窗
                args=['--no-sandbox']
            )
        if _context is None:
            _context = await _browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='zh-TW',
                timezone_id='Asia/Taipei'
            )
        _page = await _context.new_page()

        # 設定 console 監聽
        _page.on("console", lambda msg: _console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "timestamp": datetime.now().isoformat()
        }))

    return _page


@mcp.tool()
async def navigate(url: str) -> str:
    """導航到指定 URL

    Args:
        url: 要訪問的 URL (例如: http://localhost:5173)

    Returns:
        str: 導航結果訊息
    """
    try:
        page = await get_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        return f"✅ 已導航到: {url}\n當前 URL: {page.url}"
    except Exception as e:
        return f"❌ 導航失敗: {str(e)}"


@mcp.tool()
async def click(selector: str) -> str:
    """點擊指定的元素

    Args:
        selector: CSS 選擇器 (例如: button[type='submit'])

    Returns:
        str: 點擊結果訊息
    """
    try:
        page = await get_page()
        await page.click(selector, timeout=10000)
        return f"✅ 已點擊: {selector}"
    except Exception as e:
        return f"❌ 點擊失敗: {str(e)}"


@mcp.tool()
async def fill(selector: str, value: str) -> str:
    """填寫輸入欄位

    Args:
        selector: CSS 選擇器 (例如: input[name='email'])
        value: 要填入的值

    Returns:
        str: 填寫結果訊息
    """
    try:
        page = await get_page()
        await page.fill(selector, value, timeout=10000)
        return f"✅ 已填寫: {selector} = {value}"
    except Exception as e:
        return f"❌ 填寫失敗: {str(e)}"


@mcp.tool()
async def screenshot(path: str = "", full_page: bool = False) -> str:
    """截圖當前頁面

    Args:
        path: 儲存路徑（可選，預設為 /tmp/screenshot_時間戳.png）
        full_page: 是否全頁截圖（預設 false）

    Returns:
        str: 截圖結果訊息（包含 base64 preview）
    """
    try:
        page = await get_page()
        if not path:
            path = f"/tmp/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        screenshot_bytes = await page.screenshot(path=path, full_page=full_page)
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode()

        return f"✅ 截圖已儲存: {path}\n\n[截圖 Base64 Preview]\n{screenshot_base64[:100]}...(已截斷，完整檔案請查看 {path})"
    except Exception as e:
        return f"❌ 截圖失敗: {str(e)}"


@mcp.tool()
async def get_console_logs() -> str:
    """取得瀏覽器 console 日誌

    Returns:
        str: Console 日誌內容
    """
    global _console_logs

    if not _console_logs:
        return "ℹ️ 沒有 console 日誌"

    logs = _console_logs.copy()
    _console_logs.clear()  # 清空已讀取的 logs

    log_text = "📋 Console 日誌:\n\n"
    for log in logs:
        log_text += f"[{log['timestamp']}] {log['type'].upper()}: {log['text']}\n"

    return log_text


@mcp.tool()
async def execute_js(code: str) -> str:
    """在頁面中執行 JavaScript

    Args:
        code: 要執行的 JavaScript 代碼

    Returns:
        str: JavaScript 執行結果
    """
    try:
        page = await get_page()
        result = await page.evaluate(code)
        return f"✅ JavaScript 執行結果:\n{str(result)}"
    except Exception as e:
        return f"❌ 執行失敗: {str(e)}"


@mcp.tool()
async def wait_for_selector(selector: str, timeout: int = 30000) -> str:
    """等待元素出現

    Args:
        selector: CSS 選擇器
        timeout: 超時時間（毫秒，預設 30000）

    Returns:
        str: 等待結果訊息
    """
    try:
        page = await get_page()
        await page.wait_for_selector(selector, timeout=timeout)
        return f"✅ 元素已出現: {selector}"
    except Exception as e:
        return f"❌ 等待超時: {str(e)}"


@mcp.tool()
async def close_browser() -> str:
    """關閉瀏覽器

    Returns:
        str: 關閉結果訊息
    """
    global _browser, _context, _page, _playwright

    try:
        if _page:
            await _page.close()
            _page = None
        if _context:
            await _context.close()
            _context = None
        if _browser:
            await _browser.close()
            _browser = None
        if _playwright:
            await _playwright.stop()
            _playwright = None

        return "✅ 瀏覽器已關閉"
    except Exception as e:
        return f"⚠️ 關閉時發生錯誤: {str(e)}"


# 啟動 server
if __name__ == "__main__":
    mcp.run()
