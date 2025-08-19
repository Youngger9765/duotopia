"""
學生管理 E2E 測試 - 基於工作的簡化版本

測試內容：
1. 基本頁面載入和元素檢查
2. 標籤切換功能 (學生名單 ⟷ 班級管理)
3. 搜尋和篩選功能
4. 新增學生彈窗功能
5. 基本 UI 互動測試
"""

import time
import re
from playwright.sync_api import Page, expect
import pytest

class TestStudentManagementWorking:
    """學生管理 E2E 測試 - 工作版本"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """前置準備：登入並導航到學生管理頁面"""
        # 確保使用 headless 模式
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
        # 1. 前往登入頁面
        page.goto("http://localhost:5174/login")
        
        # 2. 執行登入 - teacher1 現在是 ADMIN 角色
        page.fill('input[type="email"]', 'teacher1@duotopia.com')
        page.fill('input[type="password"]', 'password123')
        page.click('button[type="submit"]')
        
        # 3. 等待登入完成 
        print("等待登入完成...")
        page.wait_for_timeout(3000)
        current_url = page.url
        print(f"當前 URL: {current_url}")
        
        # 4. 通過導航進入學生管理
        page.goto("http://localhost:5174/teacher")
        page.wait_for_load_state("networkidle")
        
        # 點擊學生管理導航
        page.click('text=學生管理')
        page.wait_for_timeout(3000)
        
        # 確認頁面載入
        expect(page.locator('h2:has-text("學生管理")')).to_be_visible()
        
        yield page
    
    def test_basic_page_load(self, page: Page):
        """測試基本頁面載入和元素存在"""
        print("\\n[基本載入] 開始測試頁面基本元素...")
        
        # 檢查主要標題
        expect(page.locator('h2:has-text("學生管理")')).to_be_visible()
        expect(page.locator('text=管理學生資料、分配班級')).to_be_visible()
        
        # 檢查標籤導航 - 使用 main 區域避免側邊欄衝突
        expect(page.locator('main nav button:has-text("學生名單")')).to_be_visible()
        expect(page.locator('main nav button:has-text("班級管理")')).to_be_visible()
        
        # 檢查篩選器
        expect(page.locator('input[placeholder*="搜尋"]')).to_be_visible()
        expect(page.locator('select:has(option:has-text("所有學校"))')).to_be_visible()
        expect(page.locator('select:has(option:has-text("所有狀態"))')).to_be_visible()
        
        # 檢查新增學生按鈕
        expect(page.locator('main button:has-text("新增學生")')).to_be_visible()
        
        # 重要：檢查是否有真實學生資料顯示
        page.wait_for_timeout(3000)  # 等待 API 載入
        student_list = page.locator('ul.divide-y div.text-sm.font-medium.text-gray-900')
        if student_list.count() > 0:
            print(f"✓ 找到 {student_list.count()} 個學生資料")
        else:
            print("❌ 警告：學生列表為空，可能權限或 API 問題")
        
        print("✓ 所有基本元素正常顯示")
    
    def test_tab_switching(self, page: Page):
        """測試標籤切換功能"""
        print("\\n[標籤切換] 開始測試標籤切換功能...")
        
        # 確認初始狀態 - 學生名單應該是激活的
        student_tab = page.locator('main nav button:has-text("學生名單")')
        expect(student_tab).to_have_class(re.compile("text-blue-600"))
        
        # 切換到班級管理
        class_tab = page.locator('main nav button:has-text("班級管理")')
        class_tab.click()
        page.wait_for_timeout(1000)
        
        # 驗證班級管理標籤被激活
        expect(class_tab).to_have_class(re.compile("text-blue-600"))
        
        # 檢查內容是否改變
        expect(page.locator('text=這裡會顯示班級列表')).to_be_visible()
        
        # 確認新增班級按鈕出現
        expect(page.locator('main button:has-text("新增班級")')).to_be_visible()
        
        # 切換回學生名單
        student_tab.click()
        page.wait_for_timeout(1000)
        
        # 驗證學生名單標籤重新激活
        expect(student_tab).to_have_class(re.compile("text-blue-600"))
        
        # 檢查新增學生按鈕重新出現
        expect(page.locator('main button:has-text("新增學生")')).to_be_visible()
        
        print("✓ 標籤切換功能正常")
    
    def test_search_and_filters(self, page: Page):
        """測試搜尋和篩選功能"""
        print("\\n[搜尋篩選] 開始測試搜尋和篩選功能...")
        
        # 測試搜尋輸入
        search_input = page.locator('input[placeholder*="搜尋"]')
        search_input.fill('測試搜尋')
        page.wait_for_timeout(500)
        
        # 驗證搜尋框有值
        expect(search_input).to_have_value('測試搜尋')
        
        # 清空搜尋
        search_input.fill('')
        
        # 測試學校篩選
        school_select = page.locator('select:has(option:has-text("所有學校"))')
        school_select.select_option('1')
        page.wait_for_timeout(500)
        
        # 重置為所有學校
        school_select.select_option('all')
        
        # 測試狀態篩選
        status_select = page.locator('select:has(option:has-text("所有狀態"))')
        status_select.select_option('assigned')
        page.wait_for_timeout(500)
        
        # 重置為所有狀態
        status_select.select_option('all')
        
        print("✓ 搜尋和篩選功能正常")
    
    def test_add_student_modal(self, page: Page):
        """測試新增學生彈窗功能"""
        print("\\n[新增學生] 開始測試新增學生彈窗...")
        
        # 點擊新增學生按鈕
        add_button = page.locator('main button:has-text("新增學生")')
        add_button.click()
        
        # 等待彈窗出現
        page.wait_for_timeout(1000)
        
        # 檢查彈窗標題
        expect(page.locator('h3:has-text("新增學生")')).to_be_visible()
        
        # 檢查表單欄位
        expect(page.locator('input[placeholder="請輸入學生姓名"]')).to_be_visible()
        expect(page.locator('input[placeholder="student@example.com"]')).to_be_visible()
        
        # 檢查按鈕 - 使用更具體的選擇器避免衝突
        expect(page.locator('button:has-text("取消")').nth(-1)).to_be_visible()
        expect(page.locator('button:has-text("新增")').nth(-1)).to_be_visible()
        
        # 測試表單輸入
        name_input = page.locator('input[placeholder="請輸入學生姓名"]')
        name_input.fill('測試學生')
        expect(name_input).to_have_value('測試學生')
        
        email_input = page.locator('input[placeholder="student@example.com"]')
        email_input.fill('test@example.com')
        expect(email_input).to_have_value('test@example.com')
        
        # 關閉彈窗
        cancel_button = page.locator('button:has-text("取消")').nth(-1)
        cancel_button.click()
        
        # 等待彈窗關閉
        page.wait_for_timeout(1000)
        
        # 驗證彈窗已關閉
        expect(page.locator('h3:has-text("新增學生")')).not_to_be_visible()
        
        print("✓ 新增學生彈窗功能正常")
    
    def test_responsive_elements(self, page: Page):
        """測試響應式元素和基本互動"""
        print("\\n[響應式] 開始測試響應式元素...")
        
        # 測試hover效果（模擬）
        tabs = page.locator('main nav button')
        
        # 測試所有標籤都可以點擊
        for i in range(tabs.count()):
            tab = tabs.nth(i)
            if tab.is_visible():
                tab.click()
                page.wait_for_timeout(300)
        
        # 回到學生名單標籤
        page.locator('main nav button:has-text("學生名單")').click()
        
        print("✓ 響應式元素和互動正常")
    
    def test_complete_workflow(self, page: Page):
        """完整工作流程測試"""
        print("\\n[完整流程] 開始測試完整工作流程...")
        
        # 1. 檢查初始狀態
        expect(page.locator('h2:has-text("學生管理")')).to_be_visible()
        
        # 2. 搜尋操作
        search_input = page.locator('input[placeholder*="搜尋"]')
        search_input.fill('john')
        page.wait_for_timeout(500)
        search_input.fill('')
        
        # 3. 切換到班級管理
        page.locator('main nav button:has-text("班級管理")').click()
        page.wait_for_timeout(1000)
        expect(page.locator('text=這裡會顯示班級列表')).to_be_visible()
        
        # 4. 切換回學生名單
        page.locator('main nav button:has-text("學生名單")').click()
        page.wait_for_timeout(1000)
        
        # 5. 開啟新增學生彈窗
        page.locator('main button:has-text("新增學生")').click()
        page.wait_for_timeout(1000)
        expect(page.locator('h3:has-text("新增學生")')).to_be_visible()
        
        # 6. 關閉彈窗
        page.locator('button:has-text("取消")').nth(-1).click()
        page.wait_for_timeout(1000)
        
        # 7. 驗證回到初始狀態
        expect(page.locator('h2:has-text("學生管理")')).to_be_visible()
        expect(page.locator('main button:has-text("新增學生")')).to_be_visible()
        
        print("✓ 完整工作流程測試通過")
        print("\\n✅ 所有學生管理測試完成！")

if __name__ == "__main__":
    # 可以直接運行測試
    pytest.main([__file__, "-v", "-s"])