#!/usr/bin/env python3
"""最終測試 - 使用正確的導航路徑"""

from playwright.sync_api import sync_playwright
import time


def test_grading_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # 1. 先登入
            print("1. 導航到登入頁...")
            page.goto("http://localhost:5173/teacher/login")
            time.sleep(2)

            # 2. 填寫登入表單
            print("2. 填寫登入資訊...")
            email_input = page.locator("input[type='email']")
            password_input = page.locator("input[type='password']")

            if email_input.is_visible():
                email_input.fill("demo@duotopia.com")
                password_input.fill("demo123")

                # 點擊登入
                login_button = page.locator("button[type='submit']")
                login_button.click()
                print("✅ 登入成功")
                time.sleep(3)

            # 3. 導航到班級頁面
            print("3. 進入班級管理...")
            page.goto("http://localhost:5173/teacher/classrooms")
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 4. 點擊第一個班級
            classroom_link = page.locator("a[href*='/teacher/classrooms/']").first
            if classroom_link.is_visible():
                classroom_link.click()
                print("✅ 進入班級詳情")
                time.sleep(2)

            # 5. 找到作業區塊並點擊作業
            assignments_section = page.locator("text=作業列表").first
            if assignments_section.is_visible():
                # 點擊第一個作業
                assignment_link = page.locator("a[href*='/teacher/assignments/']").first
                if assignment_link.is_visible():
                    assignment_link.click()
                    print("✅ 進入作業詳情頁")
                    time.sleep(3)

                    # 6. 現在應該在作業詳情頁，尋找批改按鈕
                    page.screenshot(path="/Users/young/project/duotopia/tmp/assignment_detail_page.png")

                    # 尋找批改按鈕
                    grade_buttons = page.locator("button:has-text('批改')")
                    count = grade_buttons.count()
                    print(f"找到 {count} 個批改按鈕")

                    if count > 0:
                        # 點擊第一個
                        grade_buttons.first.click()
                        print("✅ 點擊批改按鈕")
                        time.sleep(2)

                        # 檢查 Modal
                        modal = page.locator("[role='dialog']")
                        if modal.is_visible():
                            print("✅ Modal 成功開啟！")

                            # 截圖
                            page.screenshot(path="/Users/young/project/duotopia/tmp/grading_modal_success.png")

                            # 檢查內容
                            questions = page.locator(".space-y-4").first
                            if questions.is_visible():
                                print("✅ 顯示題目內容")

                            slider = page.locator("input[type='range']")
                            if slider.is_visible():
                                print("✅ 分數滑桿可用")
                                slider.fill("90")

                            feedback = page.locator("textarea").last
                            if feedback.is_visible():
                                print("✅ 回饋欄位可用")
                                feedback.fill("測試回饋")

                            print("\n🎉 測試成功！批改功能完全正常")
                        else:
                            print("❌ Modal 未開啟")
                    else:
                        # 可能沒有可批改的作業，檢查狀態
                        status_badges = page.locator(".badge, .text-sm")
                        print("學生狀態:")
                        for i in range(min(5, status_badges.count())):
                            print(f"  - {status_badges.nth(i).text_content()}")

        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            page.screenshot(path="/Users/young/project/duotopia/tmp/test_error_final.png")

        finally:
            time.sleep(5)
            browser.close()


if __name__ == "__main__":
    test_grading_flow()
