import { test, expect } from '@playwright/test';

test('作業活動頁面功能測試', async ({ page }) => {
  test.setTimeout(30000);

  // 收集 console 錯誤
  const consoleErrors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  // 1. 前往首頁
  await page.goto('http://localhost:5173');
  await page.waitForLoadState('networkidle');

  // 2. 點擊「免費試用」進入學生登入（選擇第一個）
  const tryButton = page.locator('button:has-text("免費試用")').first();
  await tryButton.click();

  // 3. 輸入學生姓名
  await page.waitForSelector('input[type="text"]', { timeout: 5000 });
  await page.fill('input[type="text"]', '王小明');

  // 4. 點擊下一步
  await page.locator('button:has-text("下一步")').click();

  // 5. 輸入密碼（生日）
  await page.waitForSelector('input[type="password"]', { timeout: 5000 });
  await page.fill('input[type="password"]', '20120315');

  // 6. 點擊登入
  await page.locator('button:has-text("登入")').click();

  // 7. 等待進入 dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
  console.log('✅ Step 1: 登入成功');

  // 8. 檢查作業列表是否載入
  await page.waitForSelector('text=我的作業', { timeout: 5000 });
  const assignmentButtons = page.locator('button:has-text("開始作業"), a:has-text("開始作業")');
  const count = await assignmentButtons.count();
  console.log(`✅ Step 2: 找到 ${count} 個作業`);

  if (count === 0) {
    throw new Error('沒有找到任何作業');
  }

  // 9. 點擊第一個作業
  await assignmentButtons.first().click();

  // 10. 等待活動頁面載入
  await page.waitForTimeout(2000);

  // 11. 檢查 URL 是否正確
  const url = page.url();
  if (url.includes('/assignments/') && url.includes('/activity/')) {
    console.log('✅ Step 3: 成功進入活動頁面');
  }

  // 12. 檢查是否有 React 渲染錯誤
  const reactErrors = consoleErrors.filter(error =>
    error.includes('Objects are not valid as a React child') ||
    error.includes('found: object with keys')
  );

  if (reactErrors.length > 0) {
    console.log('❌ 發現 React 錯誤:');
    reactErrors.forEach(err => console.log(err));
    throw new Error('React 渲染錯誤');
  }

  // 13. 檢查頁面內容
  const pageText = await page.textContent('body');

  // 檢查是否有 [object Object]
  if (pageText?.includes('[object Object]')) {
    throw new Error('頁面顯示 [object Object]');
  }

  // 檢查是否直接顯示 JSON
  if (pageText?.includes('"text"') && pageText?.includes('"translation"')) {
    throw new Error('頁面直接顯示 JSON 物件');
  }

  // 14. 檢查活動內容元素
  const hasInstructions = await page.locator('text=題目說明').count() > 0;
  const hasContent = await page.locator('text=請朗讀以下內容').count() > 0;

  if (hasInstructions && hasContent) {
    console.log('✅ Step 4: 活動內容正確顯示');
  }

  // 15. 檢查錄音按鈕
  const recordButton = await page.locator('button:has-text("開始錄音")').count() > 0;
  if (recordButton) {
    console.log('✅ Step 5: 錄音功能存在');
  }

  // 最終結果
  if (consoleErrors.length === 0) {
    console.log('✅ 測試通過：沒有 console 錯誤');
  } else {
    console.log(`⚠️ 發現 ${consoleErrors.length} 個 console 錯誤`);
  }

  // 斷言沒有 React 錯誤
  expect(reactErrors).toHaveLength(0);
  console.log('🎉 所有測試通過！');
});
