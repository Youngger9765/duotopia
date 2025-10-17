"""
測試批次翻譯 JSON 格式
"""
import asyncio
from services.translation import translation_service


async def test_batch_translate():
    # 測試資料
    test_words = [
        "put",
        "Put it away.",
        "It's time to put everything away. Right now.",
        "take",
        "Take your shoes off.",
        "Don't take too long.",
        "clean",
        "Clean your room.",
    ]

    print(f"🔍 測試批次翻譯 {len(test_words)} 個項目...\n")

    # 測試繁體中文翻譯
    print("=" * 50)
    print("測試 zh-TW 翻譯:")
    print("=" * 50)

    import time

    start = time.time()
    translations = await translation_service.batch_translate(test_words, "zh-TW")
    elapsed = time.time() - start

    print(f"\n翻譯結果 ({elapsed:.2f} 秒):")
    for i, (original, translation) in enumerate(zip(test_words, translations), 1):
        print(f"{i}. {original:50} → {translation}")

    # 檢查翻譯數量
    if len(translations) != len(test_words):
        print(f"\n❌ 錯誤：翻譯數量不符（預期 {len(test_words)}，實際 {len(translations)}）")
    else:
        print(f"\n✅ 翻譯數量正確：{len(translations)} 個")

    # 檢查是否有原文（代表翻譯失敗）
    failed = [
        (i, word)
        for i, (word, trans) in enumerate(zip(test_words, translations), 1)
        if word == trans
    ]
    if failed:
        print("\n❌ 以下項目翻譯失敗（返回原文）:")
        for i, word in failed:
            print(f"  {i}. {word}")
    else:
        print("\n✅ 所有項目都成功翻譯")


if __name__ == "__main__":
    asyncio.run(test_batch_translate())
