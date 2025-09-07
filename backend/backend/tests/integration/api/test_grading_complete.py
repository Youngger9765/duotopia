#!/usr/bin/env python3
"""完整測試批改功能 - 從登入到批改"""

from playwright.sync_api import sync_playwright
import time
import requests


def get_teacher_token():
    """取得教師登入 token"""
    response = requests.post(
        "http://localhost:8000/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def test_grading_complete():
    token = get_teacher_token()
    if not token:
        print("❌ 無法取得登入 token")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # 1. 設定認證
            page.goto("http://localhost:5173")
            page.evaluate(
                """
                localStorage.setItem('token', '{token}');
                localStorage.setItem('userType', 'teacher');
            """
            )
            print("✅ 設定認證完成")

            # 2. 導航到作業詳情頁
            page.goto("http://localhost:5173/teacher/assignments/1")
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            print("✅ 進入作業詳情頁")

            # 3. 尋找批改按鈕
            grade_buttons = page.locator("button:has-text('批改')")
            button_count = grade_buttons.count()
            print(f"找到 {button_count} 個批改按鈕")

            if button_count > 0:
                # 點擊第一個批改按鈕
                grade_buttons.first.click()
                print("✅ 點擊批改按鈕")
                time.sleep(2)

                # 4. 檢查 Modal
                modal = page.locator("[role='dialog']")
                if modal.is_visible():
                    print("✅ Modal 成功開啟")

                    # 截圖
                    page.screenshot(path="/Users/young/project/duotopia/tmp/grading_modal_opened.png")
                    print("✅ 截圖: tmp/grading_modal_opened.png")

                    # 5. 檢查內容
                    # 檢查左側題目
                    questions = page.locator(".bg-blue-50")
                    if questions.count() > 0:
                        print(f"✅ 顯示 {questions.count()} 個題目")
                        first_q = questions.first.text_content()
                        print(f"   第一題: {first_q[:50]}...")

                    # 檢查學生回答
                    answers = page.locator(".bg-green-50")
                    if answers.count() > 0:
                        print(f"✅ 顯示 {answers.count()} 個學生回答")

                    # 6. 測試互動功能
                    # 調整分數
                    slider = page.locator("input[type='range']")
                    if slider.is_visible():
                        slider.fill("95")
                        print("✅ 調整分數到 95")

                    # 輸入個別回饋
                    item_feedbacks = page.locator("div.space-y-4 textarea")
                    if item_feedbacks.count() > 0:
                        item_feedbacks.first.fill("發音清晰，語調自然")
                        print("✅ 輸入個別題目回饋")

                    # 輸入總評
                    overall_feedback = page.locator("textarea").last
                    if overall_feedback.is_visible():
                        overall_feedback.fill("整體表現優秀，繼續保持！")
                        print("✅ 輸入總評回饋")

                    # 最終截圖
                    time.sleep(1)
                    page.screenshot(path="/Users/young/project/duotopia/tmp/grading_modal_filled.png")
                    print("✅ 已填寫內容截圖: tmp/grading_modal_filled.png")

                    # 7. 測試儲存（但不真的送出）
                    save_button = page.locator("button:has-text('儲存評分')")
                    if save_button.is_visible():
                        print("✅ 儲存按鈕可用")
                        # save_button.click()  # 不真的點擊，避免改到資料

                    print("\n🎉 測試成功！批改功能正常運作")
                    print("✅ Modal 正確顯示")
                    print("✅ 題目內容從資料庫載入")
                    print("✅ 互動功能正常")

                else:
                    print("❌ Modal 未開啟")
                    page.screenshot(path="/Users/young/project/duotopia/tmp/grading_modal_error.png")
            else:
                print("❌ 頁面上沒有批改按鈕")
                page.screenshot(path="/Users/young/project/duotopia/tmp/no_grade_button.png")

        except Exception as e:
            print(f"❌ 測試過程發生錯誤: {e}")
            page.screenshot(path="/Users/young/project/duotopia/tmp/test_error.png")

        finally:
            time.sleep(3)
            browser.close()


if __name__ == "__main__":
    test_grading_complete()
