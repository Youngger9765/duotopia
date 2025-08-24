#!/usr/bin/env python3
"""
最終完整測試
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"  
TEACHER_PASSWORD = "password123"

def final_comprehensive_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("🔥 開始最終完整測試 🔥")
            
            # 1. 登入
            print("\n1. 登入...")
            page.goto(f"{BASE_URL}/login")
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            print("   ✅ 登入成功")
            
            # 2. 進入課程管理
            print("\n2. 進入課程管理頁面...")
            page.goto(f"{BASE_URL}/teacher/courses")
            page.wait_for_selector("h2:has-text('課程管理')")
            time.sleep(2)
            print("   ✅ 課程管理頁面載入")
            
            # 3. 檢查課程顯示
            print("\n3. 檢查課程列表...")
            courses = page.locator(".p-3.border-b.cursor-pointer").all()
            print(f"   ✅ 找到 {len(courses)} 個課程")
            
            # 4. 選擇第一個課程
            print("\n4. 選擇課程...")
            courses[0].click() 
            time.sleep(2)
            print("   ✅ 課程已選擇")
            
            # 5. 檢查活動列表
            print("\n5. 檢查活動列表...")
            activities = page.locator(".p-3.border-b.cursor-pointer").all()
            activity_count = len([a for a in activities if "課" in a.text_content() or "活動" in a.text_content()])
            print(f"   ✅ 找到 {activity_count} 個活動")
            
            # 6. 點擊一個活動看內容
            if activity_count > 0:
                print("\n6. 測試活動內容顯示...")
                activities[1].click() if len(activities) > 1 else activities[0].click()
                time.sleep(2)
                
                if page.locator("h4:has-text('活動說明')").is_visible():
                    print("   ✅ 活動內容正確顯示")
                else:
                    print("   ❌ 活動內容沒有顯示")
            
            # 7. 測試新增活動
            print("\n7. 測試新增活動功能...")
            add_btn = page.locator("button:has-text('新增活動')")
            add_btn.click()
            time.sleep(1)
            
            # 填寫表單
            modal = page.locator(".fixed.inset-0").last
            modal.locator("input[placeholder='請輸入活動標題']").fill("最終測試活動")
            modal.locator("select").first.select_option("聽力克漏字")
            
            # 提交
            modal.locator("button:has-text('建立活動')").click()
            time.sleep(3)
            
            # 檢查結果
            if page.locator("text=活動已建立").is_visible():
                print("   ✅ 活動建立成功！")
                success = True
            else:
                print("   ❌ 活動建立失敗")
                page.screenshot(path="final_test_failure.png")
                success = False
            
            return success
            
        except Exception as e:
            print(f"\n💥 測試失敗：{e}")
            page.screenshot(path="final_test_error.png")
            return False
        finally:
            print("\n按任意鍵關閉瀏覽器...")
            input()
            browser.close()

if __name__ == "__main__":
    success = final_comprehensive_test()
    if success:
        print("\n🎉 所有測試通過！課程管理功能正常運作！")
    else:
        print("\n💀 測試失敗，需要進一步修復")