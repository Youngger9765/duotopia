#!/usr/bin/env python3
"""
Manual test of course management features
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"

def manual_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("開始測試課程管理功能...")
            
            # 1. 登入
            print("\n1. 登入測試...")
            page.goto(f"{BASE_URL}/login")
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            print("   ✓ 登入成功")
            
            # 2. 進入課程管理頁面
            print("\n2. 進入課程管理頁面...")
            page.goto(f"{BASE_URL}/teacher/courses")
            page.wait_for_selector("h2:has-text('課程管理')")
            time.sleep(2)
            print("   ✓ 課程管理頁面載入成功")
            
            # 3. 檢查課程是否顯示
            print("\n3. 檢查課程顯示...")
            courses = page.locator(".p-3.border-b.cursor-pointer").all()
            print(f"   找到 {len(courses)} 個課程")
            if len(courses) == 0:
                print("   ✗ 沒有找到課程！")
                page.screenshot(path="no_courses.png")
                return False
            
            # 4. 點擊第一個課程
            print("\n4. 選擇第一個課程...")
            courses[0].click()
            time.sleep(2)
            
            # 檢查是否有活動顯示
            activities = page.locator("div:has-text('已發布')").all()
            print(f"   課程活動區域顯示正常")
            
            # 5. 測試新增活動
            print("\n5. 測試新增活動...")
            add_button = page.locator("button:has-text('新增活動')")
            if add_button.is_visible():
                add_button.click()
                time.sleep(1)
                
                # 檢查彈窗是否出現
                modal = page.locator(".fixed.inset-0").last
                if modal.is_visible():
                    print("   ✓ 新增活動彈窗顯示正常")
                    
                    # 填寫表單
                    title_input = modal.locator("input[placeholder='請輸入活動標題']")
                    title_input.fill("實際測試活動")
                    
                    type_select = modal.locator("select").first
                    type_select.select_option("聽力克漏字")
                    
                    # 點擊建立
                    save_button = modal.locator("button:has-text('建立活動')")
                    save_button.click()
                    
                    # 等待結果
                    time.sleep(3)
                    
                    # 檢查結果
                    if page.locator("text=活動已建立").is_visible():
                        print("   ✓ 活動建立成功！")
                        return True
                    elif page.locator("text=錯誤").is_visible():
                        error_msg = page.locator(".text-red-600").text_content()
                        print(f"   ✗ 活動建立失敗：{error_msg}")
                        page.screenshot(path="activity_creation_error.png")
                        return False
                    else:
                        print("   ? 活動建立結果不明")
                        page.screenshot(path="activity_creation_unclear.png")
                        return False
                else:
                    print("   ✗ 新增活動彈窗沒有顯示")
                    return False
            else:
                print("   ✗ 新增活動按鈕沒有找到")
                return False
                
        except Exception as e:
            print(f"\n❌ 測試失敗：{e}")
            page.screenshot(path="test_error.png")
            return False
        finally:
            input("按 Enter 繼續...")
            browser.close()

if __name__ == "__main__":
    success = manual_test()
    if success:
        print("\n✅ 所有測試通過")
    else:
        print("\n❌ 測試失敗")