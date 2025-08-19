"""
Playwright E2E 測試配置
"""
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    """建立瀏覽器實例"""
    with sync_playwright() as p:
        # 使用 Chromium，設定為非無頭模式以便觀察測試過程
        browser = p.chromium.launch(
            headless=False,  # 設為 True 可在背景執行
            slow_mo=500      # 放慢操作速度，方便觀察（毫秒）
        )
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser):
    """為每個測試建立新頁面"""
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        locale='zh-TW'
    )
    page = context.new_page()
    yield page
    context.close()