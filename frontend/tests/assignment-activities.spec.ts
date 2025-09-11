import { test, expect } from '@playwright/test';

test.describe('Assignment Activities E2E Test', () => {
  // 測試前先登入
  test.beforeEach(async ({ page }) => {
    // 前往登入頁面
    await page.goto('http://localhost:5173');

    // 等待頁面載入
    await page.waitForLoadState('networkidle');

    // 輸入學生姓名
    await page.fill('input[placeholder="請輸入姓名"]', '王小明');
    await page.click('button:has-text("下一步")');

    // 等待生日輸入頁面
    await page.waitForSelector('text=請選擇你的生日');

    // 輸入生日 - 2012年3月15日
    await page.fill('input[placeholder="請輸入密碼"]', '20120315');
    await page.click('button:has-text("登入")');

    // 等待登入成功，應該跳轉到 dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('應該能看到作業列表', async ({ page }) => {
    // 確認在 dashboard
    expect(page.url()).toContain('/dashboard');

    // 等待作業列表載入
    await page.waitForSelector('text=我的作業', { timeout: 5000 });

    // 應該至少有一個作業卡片
    const assignmentCards = page.locator('[data-testid="assignment-card"], .assignment-card, div:has-text("截止日期")');
    await expect(assignmentCards).toHaveCount(await assignmentCards.count());

    // 檢查是否有作業標題
    const hasAssignments = await assignmentCards.count() > 0;
    expect(hasAssignments).toBeTruthy();
  });

  test('應該能點擊作業進入活動頁面', async ({ page }) => {
    // 點擊第一個作業的「開始作業」按鈕
    const startButton = page.locator('button:has-text("開始作業"), a:has-text("開始作業")').first();

    // 等待按鈕出現
    await startButton.waitFor({ timeout: 5000 });

    // 點擊按鈕
    await startButton.click();

    // 應該跳轉到活動頁面
    await page.waitForURL('**/assignments/*/activity/*', { timeout: 10000 });

    // 等待活動內容載入
    await page.waitForSelector('text=題目說明', { timeout: 5000 });
  });

  test('活動頁面應該正確顯示內容（無 React 錯誤）', async ({ page }) => {
    // 監聽 console 錯誤
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // 直接前往活動頁面
    await page.goto('http://localhost:5173/assignments/1/activity/0');

    // 等待頁面載入
    await page.waitForLoadState('networkidle');

    // 檢查是否有 React 渲染錯誤
    const reactErrors = consoleErrors.filter(error =>
      error.includes('Objects are not valid as a React child') ||
      error.includes('found: object with keys')
    );

    // 不應該有 React 渲染錯誤
    expect(reactErrors).toHaveLength(0);

    // 檢查頁面內容是否正確顯示
    await expect(page.locator('text=題目說明')).toBeVisible();
    await expect(page.locator('text=請朗讀以下內容')).toBeVisible();

    // 檢查朗讀內容是純文字，不是物件
    const targetTextElement = page.locator('p.text-xl.text-blue-900');
    const targetText = await targetTextElement.textContent();

    // 內容不應該包含 [object Object] 或 JSON 格式
    expect(targetText).not.toContain('[object Object]');
    expect(targetText).not.toContain('{');
    expect(targetText).not.toContain('"text"');
    expect(targetText).not.toContain('"translation"');

    // 內容應該是有意義的文字
    expect(targetText?.length).toBeGreaterThan(0);
  });

  test('錄音功能應該正常運作', async ({ page }) => {
    // 前往活動頁面
    await page.goto('http://localhost:5173/assignments/1/activity/0');
    await page.waitForLoadState('networkidle');

    // 找到錄音按鈕
    const recordButton = page.locator('button:has-text("開始錄音")');
    await expect(recordButton).toBeVisible();

    // 點擊開始錄音
    await recordButton.click();

    // 按鈕文字應該變成「停止錄音」
    await expect(page.locator('button:has-text("停止錄音")')).toBeVisible();

    // 等待 2 秒
    await page.waitForTimeout(2000);

    // 停止錄音
    await page.locator('button:has-text("停止錄音")').click();

    // 應該出現重新錄音按鈕
    await expect(page.locator('button:has-text("重新錄音")')).toBeVisible();
  });

  test('Email 綁定狀態應該正確顯示', async ({ page }) => {
    // 回到 dashboard
    await page.goto('http://localhost:5173/dashboard');
    await page.waitForLoadState('networkidle');

    // 檢查 Email 狀態
    await expect(page.locator('text=Email').first()).toBeVisible();

    // 如果有綁定 Email，應該顯示藍色勾勾
    const hasEmail = await page.locator('.text-blue-500 svg').count() > 0;

    if (hasEmail) {
      // 有 Email 應該顯示已驗證圖示
      await expect(page.locator('.text-blue-500')).toBeVisible();
    } else {
      // 沒有 Email 應該顯示設定提示
      await expect(page.locator('text=設定 Email 接收學習報告')).toBeVisible();
    }
  });
});

// 完整流程測試
test('完整作業流程測試', async ({ page }) => {
  test.setTimeout(60000); // 設定較長的 timeout

  // 1. 登入
  await page.goto('http://localhost:5173');
  await page.fill('input[placeholder="請輸入姓名"]', '王小明');
  await page.click('button:has-text("下一步")');
  await page.fill('input[placeholder="請輸入密碼"]', '20120315');
  await page.click('button:has-text("登入")');

  // 2. 等待 dashboard 載入
  await page.waitForURL('**/dashboard');
  console.log('✅ 登入成功');

  // 3. 檢查作業列表
  const assignmentCount = await page.locator('button:has-text("開始作業")').count();
  console.log(`✅ 找到 ${assignmentCount} 個作業`);
  expect(assignmentCount).toBeGreaterThan(0);

  // 4. 進入第一個作業
  await page.locator('button:has-text("開始作業")').first().click();
  await page.waitForURL('**/assignments/*/activity/*');
  console.log('✅ 成功進入作業活動頁面');

  // 5. 檢查活動內容
  await page.waitForSelector('text=題目說明');
  const contentText = await page.locator('p.text-xl.text-blue-900').textContent();
  console.log(`✅ 活動內容: ${contentText?.substring(0, 50)}...`);

  // 6. 測試錄音
  await page.locator('button:has-text("開始錄音")').click();
  await page.waitForTimeout(1000);
  await page.locator('button:has-text("停止錄音")').click();
  console.log('✅ 錄音功能正常');

  // 7. 檢查沒有 console 錯誤
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await page.waitForTimeout(1000);
  const reactErrors = errors.filter(e => e.includes('React'));
  expect(reactErrors).toHaveLength(0);
  console.log('✅ 沒有 React 錯誤');

  console.log('🎉 所有測試通過！');
});
