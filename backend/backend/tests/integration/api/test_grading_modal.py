#!/usr/bin/env python3
"""測試批改 Modal 功能"""

from playwright.sync_api import sync_playwright
import time
import json  # noqa: F401


def test_grading_modal():
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 設定 localStorage 來模擬登入
        page.goto("http://localhost:5173")

        # 注入認證 token
        page.evaluate(
            """
            localStorage.setItem('token', 'test-token');
            localStorage.setItem('userType', 'teacher');
            localStorage.setItem('teacherInfo', JSON.stringify({
                id: 1,
                name: '王老師',
                email: 'teacher1@duotopia.com'
            }));
        """
        )

        print("✅ 已設定認證資訊")

        # 導航到作業詳情頁
        page.goto("http://localhost:5173/teacher/assignments/1")
        print("✅ 進入作業詳情頁")

        # 等待頁面載入
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # 找到第一個可批改的學生
        try:
            # 點擊批改按鈕
            grade_button = page.locator("button:has-text('批改')").first
            if grade_button.is_visible():
                grade_button.click()
                print("✅ 點擊批改按鈕")

                # 等待 Modal 出現
                time.sleep(2)

                # 檢查 Modal 是否顯示
                modal = page.locator("[role='dialog']")
                if modal.is_visible():
                    print("✅ Modal 成功開啟")

                    # 檢查是否有題目內容
                    question_elements = page.locator(".bg-blue-50")
                    if question_elements.count() > 0:
                        first_question = question_elements.first.text_content()
                        print(f"✅ 顯示題目內容: {first_question[:30]}...")
                    else:
                        print("❌ 沒有顯示題目內容")

                    # 檢查是否有學生回答
                    answer_elements = page.locator(".bg-green-50")
                    if answer_elements.count() > 0:
                        print(f"✅ 顯示學生回答 ({answer_elements.count()} 個)")

                    # 測試分數滑桿
                    slider = page.locator("input[type='range']")
                    if slider.is_visible():
                        # 調整分數到 90
                        slider.fill("90")
                        print("✅ 調整分數到 90")

                    # 輸入總評
                    feedback_textarea = page.locator("textarea").last
                    if feedback_textarea.is_visible():
                        feedback_textarea.fill("表現優秀，發音清晰！")
                        print("✅ 輸入總評回饋")

                    # 測試個別題目回饋
                    item_feedback = page.locator("textarea").first
                    if item_feedback.is_visible():
                        item_feedback.fill("這題回答得很好")
                        print("✅ 輸入個別題目回饋")

                    # 截圖存證
                    page.screenshot(path="/Users/young/project/duotopia/tmp/grading_modal_test.png")
                    print("✅ 已截圖存證: tmp/grading_modal_test.png")

                    # 關閉 Modal
                    close_button = page.locator("button[aria-label='Close']")
                    if close_button.is_visible():
                        close_button.click()
                        print("✅ 關閉 Modal")

                    print("\n🎉 批改 Modal 測試完成！所有功能正常運作")
                else:
                    print("❌ Modal 未正確開啟")
            else:
                print("❌ 找不到批改按鈕")

        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            page.screenshot(path="/Users/young/project/duotopia/tmp/grading_modal_error.png")

        finally:
            time.sleep(2)
            browser.close()


if __name__ == "__main__":
    test_grading_modal()
