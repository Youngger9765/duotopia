#!/usr/bin/env python3
"""
使用 Playwright 測試個體戶教師登入後的使用者資料顯示
"""
from playwright.sync_api import sync_playwright
import time

def test_individual_teacher_user_display():
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # 1. 訪問登入頁面
            print("1. 訪問登入頁面...")
            page.goto("http://localhost:5173/login")
            page.wait_for_load_state("networkidle")
            
            # 2. 填寫登入表單
            print("2. 填寫個體戶教師登入資訊...")
            page.fill('input[type="email"]', "individual_teacher@gmail.com")
            page.fill('input[type="password"]', "teacher123")
            
            # 3. 點擊登入按鈕
            print("3. 點擊登入...")
            page.click('button[type="submit"]')
            
            # 4. 等待導航到個體戶儀表板
            print("4. 等待導航到個體戶儀表板...")
            page.wait_for_url("**/individual", timeout=10000)
            
            # 5. 檢查使用者資料是否顯示
            print("5. 檢查使用者資料顯示...")
            
            # 等待頁面載入完成
            page.wait_for_load_state("networkidle")
            time.sleep(2)  # 給一點額外時間讓資料載入
            
            # 截圖儀表板
            page.screenshot(path="individual_dashboard_with_user.png")
            print("   - 已截圖儀表板: individual_dashboard_with_user.png")
            
            # 檢查使用者名稱是否顯示
            user_name_elements = page.query_selector_all(".text-sm.font-medium.text-gray-900")
            user_info_found = False
            
            for element in user_name_elements:
                text = element.text_content()
                if text and "個體戶教師" not in text and text.strip():
                    print(f"   ✓ 找到使用者名稱: {text}")
                    user_info_found = True
                    break
            
            # 檢查 email 是否顯示
            email_elements = page.query_selector_all(".text-xs.text-gray-500")
            email_found = False
            
            for element in email_elements:
                text = element.text_content()
                if text and "@" in text:
                    print(f"   ✓ 找到 Email: {text}")
                    email_found = True
                    break
            
            # 檢查個人教學模式標籤
            mode_elements = page.query_selector_all(".text-xs.text-gray-400")
            mode_found = False
            
            for element in mode_elements:
                text = element.text_content()
                if text and "個人教學模式" in text:
                    print(f"   ✓ 找到模式標籤: {text}")
                    mode_found = True
                    break
            
            # 檢查 localStorage
            print("\n6. 檢查 localStorage 資料...")
            local_storage = page.evaluate("""() => {
                return {
                    token: localStorage.getItem('token'),
                    userEmail: localStorage.getItem('userEmail'),
                    userFullName: localStorage.getItem('userFullName'),
                    userId: localStorage.getItem('userId'),
                    userRole: localStorage.getItem('userRole')
                };
            }""")
            
            print(f"   - Token: {'✓' if local_storage['token'] else '✗'}")
            print(f"   - Email: {local_storage['userEmail'] or '✗ 未找到'}")
            print(f"   - Full Name: {local_storage['userFullName'] or '✗ 未找到'}")
            print(f"   - User ID: {local_storage['userId'] or '✗ 未找到'}")
            print(f"   - User Role: {local_storage['userRole'] or '✗ 未找到'}")
            
            # 總結
            print("\n=== 測試結果總結 ===")
            if user_info_found and email_found and mode_found:
                print("✅ 成功！使用者資料已正確顯示在個體戶儀表板上")
            else:
                print("⚠️  部分資料未正確顯示：")
                if not user_info_found:
                    print("   - 使用者名稱未顯示")
                if not email_found:
                    print("   - Email 未顯示")
                if not mode_found:
                    print("   - 教學模式標籤未顯示")
            
            # 保持瀏覽器開啟幾秒讓使用者查看
            print("\n瀏覽器將在 5 秒後關閉...")
            time.sleep(5)
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
            page.screenshot(path="individual_test_error.png")
            print("   已保存錯誤截圖: individual_test_error.png")
        
        finally:
            browser.close()

if __name__ == "__main__":
    print("=== 測試個體戶教師使用者資料顯示 ===\n")
    test_individual_teacher_user_display()