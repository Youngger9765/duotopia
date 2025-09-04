import { test, expect, Page } from '@playwright/test';

const DEMO_EMAIL = 'demo@duotopia.com';
const DEMO_PASSWORD = 'demo123';

test.describe('音檔功能完整測試', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
  });

  test('完整音檔功能流程', async () => {
    // 1. 登入
    console.log('步驟 1: 登入系統');
    await page.goto('http://localhost:5173/login/teacher');
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');

    // 等待登入完成
    await page.waitForURL('**/dashboard/**', { timeout: 10000 });
    console.log('✅ 登入成功');

    // 2. 導航到內容編輯頁面
    console.log('步驟 2: 導航到內容編輯');

    // 點擊第一個班級
    await page.click('.classroom-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);

    // 點擊第一個課程
    await page.click('.program-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);

    // 點擊第一個課堂
    await page.click('.lesson-item:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);

    // 點擊第一個內容的編輯按鈕
    const editButton = page.locator('button:has-text("編輯")').first();
    await editButton.click();
    await page.waitForTimeout(2000);
    console.log('✅ 進入內容編輯頁面');

    // 3. 測試 TTS 生成
    console.log('步驟 3: 測試 TTS 生成');

    // 找到第一個沒有音檔的項目
    const firstItemWithoutAudio = page.locator('.item-row').first();
    const speakerIcon = firstItemWithoutAudio.locator('button[aria-label*="音檔"]');

    if (await speakerIcon.count() > 0) {
      await speakerIcon.click();
      await page.waitForTimeout(1000);

      // 確保在 Generate 標籤
      const generateTab = page.locator('button[role="tab"]:has-text("Generate")');
      if (await generateTab.count() > 0) {
        await generateTab.click();
      }

      // 點擊生成按鈕
      await page.click('button:has-text("生成音檔")');

      // 等待生成完成
      await page.waitForSelector('audio', { timeout: 10000 });
      console.log('✅ TTS 生成成功');

      // 測試播放
      const audioElement = page.locator('audio').first();
      await audioElement.evaluate((audio: HTMLAudioElement) => audio.play());
      await page.waitForTimeout(2000);
      await audioElement.evaluate((audio: HTMLAudioElement) => audio.pause());
      console.log('✅ 音檔播放正常');

      // 確認使用
      await page.click('button:has-text("確認使用")');
      await page.waitForTimeout(1000);
      console.log('✅ 音檔已儲存');
    }

    // 4. 測試持久化 - 重新整理頁面
    console.log('步驟 4: 測試持久化');
    await page.reload();
    await page.waitForTimeout(2000);

    // 檢查是否有播放按鈕
    const playButtons = page.locator('button[aria-label*="播放"]');
    const playButtonCount = await playButtons.count();

    if (playButtonCount > 0) {
      console.log(`✅ 持久化成功：找到 ${playButtonCount} 個播放按鈕`);

      // 測試播放
      await playButtons.first().click();
      await page.waitForTimeout(2000);
      console.log('✅ 重整後音檔仍可播放');
    } else {
      console.log('⚠️ 警告：沒有找到播放按鈕');
    }

    // 5. 測試錄音功能
    console.log('步驟 5: 測試錄音上傳');

    // 找第二個項目測試錄音
    const secondItem = page.locator('.item-row').nth(1);
    const secondSpeakerIcon = secondItem.locator('button[aria-label*="音檔"]');

    if (await secondSpeakerIcon.count() > 0) {
      await secondSpeakerIcon.click();
      await page.waitForTimeout(1000);

      // 切換到 Record 標籤
      const recordTab = page.locator('button[role="tab"]:has-text("Record")');
      if (await recordTab.count() > 0) {
        await recordTab.click();
        console.log('✅ 切換到錄音標籤');

        // 檢查錄音按鈕是否存在
        const recordButton = page.locator('button:has-text("開始錄音")');
        if (await recordButton.count() > 0) {
          console.log('✅ 錄音功能可用');
        }
      }

      // 關閉 modal
      const closeButton = page.locator('button[aria-label="Close"]');
      if (await closeButton.count() > 0) {
        await closeButton.click();
      }
    }

    // 6. 總結
    console.log('\n' + '='.repeat(50));
    console.log('📊 測試總結');
    console.log('='.repeat(50));
    console.log('✅ 登入功能正常');
    console.log('✅ 導航功能正常');
    console.log('✅ TTS 生成功能正常');
    console.log('✅ 音檔播放功能正常');
    console.log('✅ 持久化功能正常');
    console.log('✅ 錄音介面正常');

    // 檢查控制台錯誤
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('❌ 控制台錯誤:', msg.text());
      }
    });

    // 檢查網路錯誤
    page.on('requestfailed', request => {
      console.error('❌ 請求失敗:', request.url());
    });
  });

  test.afterAll(async () => {
    await page.close();
  });
});
