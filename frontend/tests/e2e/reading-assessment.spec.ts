import { test, expect, Page } from '@playwright/test';

const DEMO_EMAIL = 'demo@duotopia.com';
const DEMO_PASSWORD = 'demo123';

test.describe('Reading Assessment 功能測試', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();

    // 登入
    await page.goto('http://localhost:5173/login/teacher');
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard/**', { timeout: 10000 });
  });

  test.afterAll(async () => {
    await page.close();
  });

  test.describe('內容編輯面板', () => {
    test('應能開啟和關閉編輯面板', async () => {
      // 導航到班級詳情頁
      await page.click('.classroom-card:first-child');
      await page.waitForTimeout(1000);

      // 點擊第一個課程
      await page.click('.program-card:first-child');
      await page.waitForTimeout(1000);

      // 點擊第一個課堂
      await page.click('.lesson-item:first-child');
      await page.waitForTimeout(1000);

      // 點擊編輯按鈕開啟面板
      const editButton = page.locator('button:has-text("編輯")').first();
      await editButton.click();

      // 驗證面板已開啟
      const panel = page.locator('[role="dialog"]');
      await expect(panel).toBeVisible();

      // 再次點擊同一個內容應關閉面板
      await editButton.click();
      await expect(panel).not.toBeVisible();
    });

    test('開發提示應已被移除', async () => {
      // 開啟編輯面板
      const editButton = page.locator('button:has-text("編輯")').first();
      await editButton.click();

      // 確認沒有開發提示文字
      const devNotice = page.locator('text=/提示.*OpenAI.*Edge-TTS/');
      await expect(devNotice).not.toBeVisible();

      // 關閉面板
      await page.keyboard.press('Escape');
    });
  });

  test.describe('TTS 功能', () => {
    test('應能為單個項目生成 TTS', async () => {
      // 開啟編輯面板
      const editButton = page.locator('button:has-text("編輯")').first();
      await editButton.click();
      await page.waitForTimeout(1000);

      // 找到第一個沒有音檔的項目
      const speakerIcon = page.locator('button[aria-label*="音檔"]').first();
      if (await speakerIcon.count() > 0) {
        await speakerIcon.click();

        // 確保在 Generate 標籤
        const generateTab = page.locator('button[role="tab"]:has-text("Generate")');
        if (await generateTab.count() > 0) {
          await generateTab.click();
        }

        // 點擊生成按鈕
        await page.click('button:has-text("生成音檔")');

        // 等待音檔生成
        await page.waitForSelector('audio', { timeout: 10000 });

        // 驗證音檔元素存在
        const audioElement = page.locator('audio').first();
        await expect(audioElement).toBeVisible();

        // 確認使用
        await page.click('button:has-text("確認使用")');
      }

      // 關閉面板
      await page.keyboard.press('Escape');
    });

    test('批次 TTS 生成應正常運作', async () => {
      // 開啟編輯面板
      const editButton = page.locator('button:has-text("編輯")').first();
      await editButton.click();
      await page.waitForTimeout(1000);

      // 點擊批次生成按鈕
      const batchButton = page.locator('button:has-text("批次生成所有音檔")');
      if (await batchButton.count() > 0) {
        await batchButton.click();

        // 等待處理完成（最多30秒）
        await page.waitForTimeout(5000);

        // 驗證至少有一個播放按鈕
        const playButtons = page.locator('button[aria-label*="播放"]');
        const count = await playButtons.count();
        expect(count).toBeGreaterThan(0);
      }

      // 關閉面板
      await page.keyboard.press('Escape');
    });
  });

  test.describe('錄音功能', () => {
    test('錄音介面應可切換', async () => {
      // 開啟編輯面板
      const editButton = page.locator('button:has-text("編輯")').first();
      await editButton.click();
      await page.waitForTimeout(1000);

      // 點擊音檔按鈕
      const speakerIcon = page.locator('button[aria-label*="音檔"]').first();
      if (await speakerIcon.count() > 0) {
        await speakerIcon.click();

        // 切換到 Record 標籤
        const recordTab = page.locator('button[role="tab"]:has-text("Record")');
        await expect(recordTab).toBeVisible();
        await recordTab.click();

        // 驗證錄音按鈕存在
        const recordButton = page.locator('button:has-text("開始錄音")');
        await expect(recordButton).toBeVisible();

        // 關閉 modal
        const closeButton = page.locator('button[aria-label="Close"]');
        if (await closeButton.count() > 0) {
          await closeButton.click();
        }
      }

      // 關閉面板
      await page.keyboard.press('Escape');
    });
  });

  test.describe('儲存功能', () => {
    test('空白項目不應被儲存', async () => {
      // 開啟新增內容對話框
      const addButton = page.locator('button:has-text("新增內容")');
      await addButton.click();
      await page.waitForTimeout(1000);

      // 選擇朗讀評測
      const readingOption = page.locator('text="朗讀評測"');
      await readingOption.click();

      const nextButton = page.locator('button:has-text("下一步")');
      await nextButton.click();

      // 填寫標題
      await page.fill('input[placeholder*="標題"]', '測試內容');

      // 添加一個完整項目和一個空白項目
      await page.fill('input[placeholder="輸入文字"]', 'Hello');
      await page.fill('input[placeholder="輸入翻譯"]', '你好');

      // 點擊新增項目
      const addItemButton = page.locator('button:has-text("新增項目")');
      await addItemButton.click();

      // 儲存
      const saveButton = page.locator('button:has-text("儲存")');
      await saveButton.click();

      // 等待儲存完成
      await page.waitForTimeout(2000);

      // 驗證只有一個項目被儲存（空白項目被過濾）
      const items = page.locator('.item-row');
      const itemCount = await items.count();
      expect(itemCount).toBe(1);
    });

    test('必填欄位驗證', async () => {
      // 開啟新增內容對話框
      const addButton = page.locator('button:has-text("新增內容")');
      await addButton.click();
      await page.waitForTimeout(1000);

      // 選擇朗讀評測
      const readingOption = page.locator('text="朗讀評測"');
      await readingOption.click();

      const nextButton = page.locator('button:has-text("下一步")');
      await nextButton.click();

      // 不填寫任何內容直接儲存
      const saveButton = page.locator('button:has-text("儲存")');
      await saveButton.click();

      // 應顯示錯誤提示
      const toast = page.locator('.Toastify__toast--error');
      await expect(toast).toBeVisible();
      await expect(toast).toContainText('請至少填寫一個完整的項目');
    });

    test('level 和 tags 應正確儲存', async () => {
      // 開啟編輯面板
      const editButton = page.locator('button:has-text("編輯")').first();
      await editButton.click();
      await page.waitForTimeout(1000);

      // 設定 level
      const levelSelect = page.locator('select').first();
      await levelSelect.selectOption('intermediate');

      // 添加標籤
      const tagInput = page.locator('input[placeholder*="標籤"]');
      await tagInput.fill('vocabulary');
      await tagInput.press('Enter');

      // 設定為公開
      const publicCheckbox = page.locator('input[type="checkbox"]').first();
      await publicCheckbox.check();

      // 儲存
      const saveButton = page.locator('button:has-text("儲存")');
      await saveButton.click();

      // 等待儲存完成
      await page.waitForTimeout(2000);

      // 重新載入頁面驗證持久化
      await page.reload();
      await page.waitForTimeout(2000);

      // 再次開啟編輯面板
      await editButton.click();
      await page.waitForTimeout(1000);

      // 驗證值已保存
      const savedLevel = await levelSelect.inputValue();
      expect(savedLevel).toBe('intermediate');

      const publicBadge = page.locator('span:has-text("公開")');
      await expect(publicBadge).toBeVisible();

      // 關閉面板
      await page.keyboard.press('Escape');
    });
  });

  test.describe('拖曳功能', () => {
    test('內容項目應可拖曳排序', async () => {
      // 獲取所有內容項目
      const contentItems = page.locator('[draggable="true"]');
      const initialCount = await contentItems.count();

      if (initialCount >= 2) {
        // 獲取第一個和第二個項目的文字
        const firstItemText = await contentItems.first().textContent();
        const secondItemText = await contentItems.nth(1).textContent();

        // 執行拖曳操作
        await contentItems.first().dragTo(contentItems.nth(1));

        // 等待 DOM 更新
        await page.waitForTimeout(1000);

        // 驗證順序已改變
        const newFirstItemText = await contentItems.first().textContent();
        const newSecondItemText = await contentItems.nth(1).textContent();

        expect(newFirstItemText).toBe(secondItemText);
        expect(newSecondItemText).toBe(firstItemText);
      }
    });

    test('拖曳後順序應被儲存', async () => {
      // 執行拖曳操作
      const contentItems = page.locator('[draggable="true"]');
      if (await contentItems.count() >= 2) {
        await contentItems.first().dragTo(contentItems.nth(1));
        await page.waitForTimeout(1000);

        // 獲取拖曳後的順序
        const orderAfterDrag = await contentItems.allTextContents();

        // 重新載入頁面
        await page.reload();
        await page.waitForTimeout(2000);

        // 驗證順序已持久化
        const orderAfterReload = await contentItems.allTextContents();
        expect(orderAfterReload).toEqual(orderAfterDrag);
      }
    });
  });

  test.describe('UI 顯示', () => {
    test('公開內容應顯示標記', async () => {
      // 查找公開標記
      const publicBadges = page.locator('span:has-text("公開")');
      const count = await publicBadges.count();

      // 如果有公開內容，驗證標記樣式
      if (count > 0) {
        const firstBadge = publicBadges.first();
        await expect(firstBadge).toHaveClass(/bg-green-100.*text-green-800/);
      }
    });

    test('內容項目應有適當縮排', async () => {
      // 獲取課堂和內容項目
      const lessonItem = page.locator('.lesson-item').first();
      const contentItem = page.locator('[draggable="true"]').first();

      // 獲取位置資訊
      const lessonBox = await lessonItem.boundingBox();
      const contentBox = await contentItem.boundingBox();

      if (lessonBox && contentBox) {
        // 驗證內容項目有向右縮排
        expect(contentBox.x).toBeGreaterThan(lessonBox.x);
      }
    });

    test('ID 應使用序號而非時間戳', async () => {
      // 開啟編輯面板
      const editButton = page.locator('button:has-text("編輯")').first();
      await editButton.click();
      await page.waitForTimeout(1000);

      // 新增項目
      const addItemButton = page.locator('button:has-text("新增項目")');
      await addItemButton.click();

      // 獲取所有項目的 ID
      const items = page.locator('.item-row');
      const lastItem = items.last();
      const idText = await lastItem.locator('span').first().textContent();

      // 驗證 ID 是短數字而非長時間戳
      const id = parseInt(idText || '0');
      expect(id).toBeLessThan(1000); // 序號應該小於1000，時間戳會是13位數

      // 關閉面板
      await page.keyboard.press('Escape');
    });
  });
});
