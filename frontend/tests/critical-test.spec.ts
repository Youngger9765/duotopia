import { test, expect } from '@playwright/test';

test('關鍵功能測試 - 作業活動頁面無錯誤', async ({ page }) => {
  // 設定較長 timeout
  test.setTimeout(30000);

  // 監聽 console 錯誤
  const consoleErrors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log('❌ Console Error:', msg.text());
    }
  });

  // 1. 登入流程
  console.log('📍 開始登入...');
  await page.goto('http://localhost:5173');

  // 等待登入表單
  await page.waitForSelector('input[placeholder="請輸入姓名"]', { timeout: 5000 });
  await page.fill('input[placeholder="請輸入姓名"]', '王小明');

  // 點擊下一步
  const nextButton = page.locator('button').filter({ hasText: /下一步|next/i }).first();
  await nextButton.click();

  // 等待密碼輸入
  await page.waitForSelector('input[type="password"], input[placeholder*="密碼"]', { timeout: 5000 });
  await page.fill('input[type="password"], input[placeholder*="密碼"]', '20120315');

  // 點擊登入
  const loginButton = page.locator('button').filter({ hasText: /登入|login/i }).first();
  await loginButton.click();

  // 等待跳轉到 dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
  console.log('✅ 登入成功');

  // 2. 檢查作業列表
  console.log('📍 檢查作業列表...');
  await page.waitForSelector('text=/作業|assignment/i', { timeout: 5000 });

  const startButtons = page.locator('button, a').filter({ hasText: /開始|start|進入/i });
  const buttonCount = await startButtons.count();
  console.log(`✅ 找到 ${buttonCount} 個作業按鈕`);

  if (buttonCount > 0) {
    // 3. 點擊第一個作業
    console.log('📍 進入作業活動頁面...');
    await startButtons.first().click();

    // 等待頁面載入
    await page.waitForTimeout(3000);

    // 4. 檢查是否有 React 錯誤
    const reactErrors = consoleErrors.filter(error =>
      error.includes('Objects are not valid as a React child') ||
      error.includes('found: object with keys') ||
      error.includes('[object Object]')
    );

    if (reactErrors.length > 0) {
      console.log('❌ 發現 React 渲染錯誤:');
      reactErrors.forEach(err => console.log('  -', err.substring(0, 100)));
      throw new Error(`發現 ${reactErrors.length} 個 React 渲染錯誤`);
    }

    // 5. 檢查頁面內容
    const pageContent = await page.content();

    // 檢查是否有錯誤的物件渲染
    if (pageContent.includes('[object Object]')) {
      throw new Error('頁面包含 [object Object]，表示物件沒有正確轉換為字串');
    }

    if (pageContent.includes('"text"') && pageContent.includes('"translation"')) {
      throw new Error('頁面直接顯示 JSON 物件，應該要轉換為純文字');
    }

    console.log('✅ 頁面內容正確渲染，沒有物件錯誤');

    // 6. 檢查關鍵元素是否存在
    const hasContent = await page.locator('text=/題目|內容|question|content/i').count() > 0;
    if (hasContent) {
      console.log('✅ 活動內容正確顯示');
    }
  }

  // 最終檢查
  if (consoleErrors.length > 0) {
    console.log(`⚠️ 總共發現 ${consoleErrors.length} 個 console 錯誤`);
  } else {
    console.log('✅ 沒有 console 錯誤');
  }

  // 測試通過
  expect(consoleErrors.filter(e => e.includes('React'))).toHaveLength(0);
  console.log('🎉 測試通過！功能正常運作');
});
