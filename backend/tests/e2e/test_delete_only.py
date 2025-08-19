"""
專門測試刪除功能的 E2E 測試
"""
import time
from playwright.sync_api import Page, expect
import pytest

class TestDeleteFunction:
    """專門測試刪除按鈕和對話框功能"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """前置準備：登入並導航到學校管理頁面"""
        # 登入
        page.goto("http://localhost:5174/login")
        page.fill('input[type="email"]', 'teacher1@duotopia.com')
        page.fill('input[type="password"]', 'teacher123')
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        
        # 導航到學校管理頁面
        page.goto("http://localhost:5174/teacher/institutions")
        page.wait_for_load_state("networkidle")
        expect(page.locator('h2:has-text("學校管理")')).to_be_visible()
        
        yield page
    
    def test_delete_button_functionality(self, page: Page):
        """測試刪除按鈕點擊是否觸發對話框"""
        
        print("\n🔍 開始測試刪除按鈕功能...")
        
        # 等待頁面完全載入
        page.wait_for_timeout(2000)
        
        # 找到所有學校卡片
        school_cards = page.locator('div.bg-white.rounded-lg.shadow')
        card_count = school_cards.count()
        print(f"找到 {card_count} 個學校卡片")
        
        if card_count == 0:
            print("❌ 沒有找到任何學校卡片，測試結束")
            return
        
        # 選擇第一個學校卡片
        first_card = school_cards.first
        
        # 獲取學校名稱
        school_name = first_card.locator('h3').inner_text()
        print(f"測試學校: {school_name}")
        
        # 找到這個卡片中的所有按鈕
        buttons = first_card.locator('button')
        button_count = buttons.count()
        print(f"找到 {button_count} 個按鈕")
        
        # 列出所有按鈕的詳細信息
        for i in range(button_count):
            button = buttons.nth(i)
            try:
                # 獲取按鈕的 HTML 內容
                html = button.innerHTML()
                print(f"按鈕 {i}: {html[:100]}...")
                
                # 檢查是否包含 trash 圖示
                if 'trash' in html.lower() or 'delete' in html.lower():
                    print(f"  → 這可能是刪除按鈕")
            except Exception as e:
                print(f"無法獲取按鈕 {i} 的資訊: {e}")
        
        # 找刪除按鈕 - 嘗試多種選擇器
        delete_selectors = [
            'button:has(svg[data-lucide="trash-2"])',  # Lucide trash icon
            'button:has(.lucide-trash-2)',             # Class-based
            'button:has(svg) >> nth=1',                # Second SVG button
            'button[class*="text-red"]',               # Red-colored button
            'button:last-child'                        # Last button in card
        ]
        
        delete_button = None
        for i, selector in enumerate(delete_selectors):
            try:
                candidate = first_card.locator(selector).first
                if candidate.count() > 0:
                    print(f"選擇器 {i+1} 找到刪除按鈕: {selector}")
                    delete_button = candidate
                    break
            except Exception as e:
                print(f"選擇器 {i+1} 失敗: {selector} - {e}")
        
        if not delete_button:
            print("❌ 無法找到刪除按鈕")
            return
        
        # 檢查按鈕是否可見和可點擊
        expect(delete_button).to_be_visible()
        expect(delete_button).to_be_enabled()
        
        print("🖱️ 點擊刪除按鈕...")
        delete_button.click()
        
        # 等待對話框出現
        page.wait_for_timeout(2000)
        
        # 檢查是否有對話框出現
        modal_visible = page.locator('div[class*="fixed inset-0"]').is_visible()
        print(f"對話框是否出現: {modal_visible}")
        
        if modal_visible:
            print("✅ 刪除對話框成功出現")
            
            # 檢查對話框內容
            titles = page.locator('h3').all_inner_texts()
            print(f"對話框標題: {titles}")
            
            button_texts = page.locator('div[class*="fixed inset-0"] button').all_inner_texts()
            print(f"對話框按鈕: {button_texts}")
            
            # 點擊取消按鈕關閉對話框
            cancel_button = page.locator('button:has-text("取消")')
            if cancel_button.is_visible():
                print("點擊取消按鈕關閉對話框")
                cancel_button.click()
                page.wait_for_timeout(1000)
            
            print("✅ 刪除按鈕功能正常")
        else:
            print("❌ 刪除對話框沒有出現")
            
            # 檢查控制台錯誤
            print("檢查是否有 JavaScript 錯誤...")
            
            # 檢查 React 狀態 (如果可能)
            try:
                # 檢查是否有任何錯誤訊息出現
                errors = page.locator('[role="alert"], .error, [class*="error"]').all_inner_texts()
                if errors:
                    print(f"發現錯誤訊息: {errors}")
            except:
                pass

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])