#!/usr/bin/env python3
"""
最終測試個體戶教師登入和資料顯示
"""
from playwright.sync_api import sync_playwright
import time

def test_individual_teacher_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("=== 測試個體戶教師登入和資料顯示 ===\n")
            
            # 1. 清除快取並訪問登入頁面
            print("1. 訪問登入頁面...")
            page.goto("http://localhost:5173/login")
            page.evaluate("localStorage.clear()")
            page.reload()
            page.wait_for_load_state("networkidle")
            
            # 2. 使用測試帳號按鈕
            print("2. 點擊個體戶教師測試帳號按鈕...")
            page.click('button:has-text("個體戶教師")')
            time.sleep(1)
            
            # 3. 檢查表單是否填入
            email_value = page.input_value('input[type="email"]')
            password_value = page.input_value('input[type="password"]')
            print(f"   Email: {email_value}")
            print(f"   密碼: {'*' * len(password_value)}")
            
            # 4. 截圖登入前
            page.screenshot(path="test_01_login_form.png")
            print("3. 已截圖: test_01_login_form.png")
            
            # 5. 點擊登入按鈕
            print("4. 點擊登入按鈕...")
            page.click('button[type="submit"]:has-text("登入")')
            
            # 6. 等待導航
            print("5. 等待導航...")
            try:
                page.wait_for_url("**/individual", timeout=5000)
                print("   ✓ 成功導航到個體戶儀表板")
            except:
                current_url = page.url
                print(f"   當前 URL: {current_url}")
                if "/teacher" in current_url:
                    print("   ⚠️  導航到一般教師儀表板")
                else:
                    print("   ❌ 登入可能失敗")
            
            # 7. 等待頁面載入
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 8. 截圖儀表板
            page.screenshot(path="test_02_dashboard.png")
            print("6. 已截圖: test_02_dashboard.png")
            
            # 9. 檢查使用者資料顯示
            print("\n7. 檢查使用者資料顯示...")
            
            # 查找使用者名稱
            user_name_selectors = page.query_selector_all(".text-sm.font-medium.text-gray-900")
            found_user_name = False
            for element in user_name_selectors:
                text = element.text_content()
                if text and "個體戶" in text and "個體戶教師" not in text:
                    print(f"   ✓ 找到使用者名稱: {text}")
                    found_user_name = True
                    break
            
            # 查找 Email
            email_selectors = page.query_selector_all(".text-xs.text-gray-500")
            found_email = False
            for element in email_selectors:
                text = element.text_content()
                if text and "@" in text:
                    print(f"   ✓ 找到 Email: {text}")
                    found_email = True
                    break
            
            # 查找教學模式標籤
            mode_selectors = page.query_selector_all(".text-xs.text-gray-400")
            found_mode = False
            for element in mode_selectors:
                text = element.text_content()
                if text and "個人教學模式" in text:
                    print(f"   ✓ 找到模式標籤: {text}")
                    found_mode = True
                    break
            
            # 10. 檢查 localStorage
            print("\n8. 檢查 localStorage...")
            storage = page.evaluate("""() => {
                return {
                    token: !!localStorage.getItem('token'),
                    userEmail: localStorage.getItem('userEmail'),
                    userFullName: localStorage.getItem('userFullName'),
                    userRole: localStorage.getItem('userRole'),
                    userId: localStorage.getItem('userId')
                };
            }""")
            
            print(f"   Token: {'✓' if storage['token'] else '✗'}")
            print(f"   Email: {storage['userEmail'] or '未設置'}")
            print(f"   Full Name: {storage['userFullName'] or '未設置'}")
            print(f"   Role: {storage['userRole'] or '未設置'}")
            print(f"   User ID: {storage['userId'] or '未設置'}")
            
            # 總結
            print("\n=== 測試結果 ===")
            if found_user_name and found_email and found_mode:
                print("✅ 成功！使用者資料正確顯示在個體戶儀表板")
            else:
                print("⚠️  部分資料未正確顯示")
                if not found_user_name:
                    print("   - 未找到使用者名稱")
                if not found_email:
                    print("   - 未找到 Email")
                if not found_mode:
                    print("   - 未找到教學模式標籤")
            
            print("\n瀏覽器將在 5 秒後關閉...")
            time.sleep(5)
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
            page.screenshot(path="test_error.png")
            print("已保存錯誤截圖: test_error.png")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_individual_teacher_login()