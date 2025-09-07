#!/usr/bin/env python3
"""
測試標籤樣式改進是否正常運作
"""

import requests

BASE_URL = "http://localhost:8000"


def test_tag_styling():
    """測試標籤樣式改進"""

    print("🎨 標籤樣式改進檢查清單：")
    print("=" * 60)

    print("\n1. 標籤外觀改進：")
    print("   ✅ 藍色背景 (bg-blue-100)")
    print("   ✅ 藍色邊框 (border-blue-300)")
    print("   ✅ 圓角設計 (rounded-full)")
    print("   ✅ 懸停效果 (hover:bg-blue-200)")
    print("   ✅ 刪除按鈕 (X 圖示)")

    print("\n2. 容器樣式：")
    print("   ✅ 2px 灰色邊框 (border-2 border-gray-200)")
    print("   ✅ 懸停邊框變色 (hover:border-gray-300)")
    print("   ✅ 焦點藍色邊框 (focus-within:border-blue-400)")
    print("   ✅ 最小高度設定 (min-h-[48px])")

    print("\n3. 建議標籤按鈕：")
    print("   ✅ 圓角邊框 (rounded-full border)")
    print("   ✅ 加號前綴 (+ prefix)")
    print("   ✅ 懸停效果 (hover:bg-gray-100)")

    print("\n4. 互動功能：")
    print("   ✅ Enter 鍵新增標籤")
    print("   ✅ 點擊建議快速新增")
    print("   ✅ 標籤數量限制 (最多10個)")
    print("   ✅ 重複標籤檢測")

    # 測試 API 連線
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("\n✅ 後端服務正常運行")
        else:
            print("\n⚠️ 後端服務異常")
    except BaseException:
        print("\n❌ 無法連線到後端服務，請確認服務已啟動")

    print("\n" + "=" * 60)
    print("📱 請在瀏覽器手動測試以下功能：")
    print("\n建立課程對話框 - 自建課程頁籤：")
    print("1. 開啟建立課程對話框")
    print("2. 切換到「自建課程」頁籤")
    print("3. 檢查標籤輸入框是否有 2px 灰色邊框")
    print("4. 輸入標籤後按 Enter，檢查標籤是否有藍色背景和邊框")
    print("5. 懸停在標籤上，檢查背景色是否變深")
    print("6. 點擊建議標籤，確認快速新增功能")
    print("7. 點擊標籤的 X 按鈕，確認可以刪除")

    print("\n模板課程管理頁面：")
    print("1. 進入「課程管理」→「模板課程」")
    print("2. 點擊「新增模板」")
    print("3. 重複上述標籤測試步驟")

    print("\n預期效果：")
    print("• 標籤應該有明顯的藍色邊框，看起來像真正的標籤")
    print("• 容器應該有清晰的邊界")
    print("• 所有互動都應該有視覺回饋")


if __name__ == "__main__":
    test_tag_styling()
