#!/usr/bin/env python3
"""
E2E Demo: 多重身份系統展示
展示教師如何在機構管理員和個人教師之間切換
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "hybrid@test.com"  # 混合型使用者（可切換角色）
TEACHER_PASSWORD = "test123"

def type_text(page, selector, text):
    """輸入文字"""
    page.locator(selector).fill(text)

def demo_role_switching():
    with sync_playwright() as p:
        # 啟動瀏覽器（顯示視窗）
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500  # 每個動作延遲 0.5 秒
        )
        context = browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = context.new_page()
        
        try:
            print("\n=== 多重身份系統 E2E 展示 ===\n")
            
            # Step 1: 登入
            print("1. 前往登入頁面...")
            page.goto(f"{BASE_URL}/login")
            time.sleep(2)
            
            print("2. 輸入教師帳號密碼...")
            type_text(page, "input[type='email']", TEACHER_EMAIL)
            time.sleep(1)
            type_text(page, "input[type='password']", TEACHER_PASSWORD)
            time.sleep(1)
            
            print("3. 點擊登入按鈕...")
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            time.sleep(2)
            
            # Step 2: 檢查預設角色
            print("\n4. 檢查當前角色和導航選單...")
            time.sleep(2)
            
            # 檢查是否有角色切換器
            role_switcher = page.locator("text=機構管理").or_(page.locator("text=個人教師"))
            if role_switcher.count() > 0:
                print("   ✓ 找到角色切換器！用戶擁有多重角色")
                current_role = role_switcher.first.text_content()
                print(f"   當前角色：{current_role}")
            else:
                print("   ✗ 沒有找到角色切換器")
            
            # 檢查導航選單項目
            print("\n5. 檢查導航選單項目...")
            time.sleep(1)
            
            nav_items = {
                "機構管理": ["學校管理", "教職員管理"],
                "教學管理": ["教室管理", "學生管理", "課程管理"]
            }
            
            for section, items in nav_items.items():
                if page.locator(f"text={section}").count() > 0:
                    print(f"   ✓ {section}區塊")
                    for item in items:
                        if page.locator(f"text={item}").count() > 0:
                            print(f"     - {item}")
            
            # Step 3: 切換角色
            print("\n6. 切換到個人教師角色...")
            time.sleep(2)
            
            # 點擊角色切換器
            role_switcher.first.click()
            time.sleep(1)
            
            # 點擊個人教師選項
            page.locator("text=個人教師").click()
            print("   等待頁面重新載入...")
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Step 4: 檢查個人教師介面
            print("\n7. 檢查個人教師角色的導航選單...")
            time.sleep(2)
            
            # 應該看不到機構管理區塊
            if page.locator("text=機構管理").count() == 0:
                print("   ✓ 機構管理區塊已隱藏（正確）")
            else:
                print("   ✗ 機構管理區塊仍然顯示（錯誤）")
            
            # 應該看到教學管理區塊
            if page.locator("text=教學管理").count() > 0:
                print("   ✓ 教學管理區塊顯示")
                teaching_items = ["教室管理", "學生管理", "課程管理"]
                for item in teaching_items:
                    if page.locator(f"text={item}").count() > 0:
                        print(f"     - {item}")
            
            # Step 5: 建立個人教室
            print("\n8. 測試個人教師建立教室...")
            time.sleep(2)
            
            # 點擊教室管理
            page.locator("text=教室管理").first.click()
            time.sleep(2)
            
            # 點擊新增教室
            if page.locator("text=新增教室").count() > 0:
                page.locator("text=新增教室").click()
                time.sleep(2)
                print("   ✓ 進入新增教室頁面")
            
            # Step 6: 切換回機構管理員
            print("\n9. 切換回機構管理角色...")
            time.sleep(2)
            
            # 點擊角色切換器
            role_switcher = page.locator("text=個人教師")
            role_switcher.click()
            time.sleep(1)
            
            # 點擊機構管理選項
            page.locator("text=機構管理").click()
            print("   等待頁面重新載入...")
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Step 7: 檢查機構管理員介面
            print("\n10. 檢查機構管理員角色的導航選單...")
            time.sleep(2)
            
            # 應該看到機構管理區塊
            if page.locator("text=機構管理").count() > 0:
                print("   ✓ 機構管理區塊顯示")
                inst_items = ["學校管理", "教職員管理"]
                for item in inst_items:
                    if page.locator(f"text={item}").count() > 0:
                        print(f"     - {item}")
            
            # 測試機構特有功能
            print("\n11. 測試機構管理員特有功能...")
            time.sleep(2)
            
            # 點擊學校管理
            if page.locator("text=學校管理").count() > 0:
                page.locator("text=學校管理").first.click()
                time.sleep(2)
                print("   ✓ 成功進入學校管理頁面")
            
            print("\n=== 展示完成！===")
            print("\n總結：")
            print("1. 用戶可以在機構管理員和個人教師角色之間切換")
            print("2. 不同角色看到不同的導航選單")
            print("3. 個人教師只能存取教學相關功能")
            print("4. 機構管理員可以存取所有功能")
            
        except Exception as e:
            print(f"\n錯誤：{e}")
            page.screenshot(path="error_screenshot.png")
            print("已儲存錯誤截圖：error_screenshot.png")
        
        finally:
            print("\n10 秒後自動關閉瀏覽器...")
            time.sleep(10)
            browser.close()

if __name__ == "__main__":
    demo_role_switching()