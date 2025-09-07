import { test } from '@playwright/test';

test('Check student assignments page', async ({ page }) => {
  // 登入學生帳號 - 多步驟流程
  await page.goto('http://localhost:5173/student/login');

  // Step 1: 輸入教師 email
  await page.locator('input[type="email"]').fill('demo@duotopia.com');
  await page.locator('button:has-text("下一步")').click();

  // 等待班級列表載入
  await page.waitForTimeout(1000);

  // Step 2: 選擇班級 (點擊第一個班級)
  await page.locator('button:has-text("五年級A班")').click();

  // 等待學生列表載入
  await page.waitForTimeout(1000);

  // Step 3: 選擇學生 (點擊第一個學生頭像)
  await page.locator('button:has(div.rounded-full)').first().click();

  // Step 4: 輸入密碼
  await page.locator('input[type="password"]').fill('20120101');
  await page.locator('button:has-text("登入")').click();

  // 等待跳轉到 dashboard
  await page.waitForURL('**/student/dashboard', { timeout: 10000 });
  await page.waitForTimeout(2000);

  // 點擊 "我的作業" 或直接導航到作業頁面
  await page.goto('http://localhost:5173/student/assignments');

  // 等待頁面載入
  await page.waitForTimeout(3000);

  // 截圖初始狀態
  await page.screenshot({ path: 'student-assignments-not-started.png', fullPage: true });
  console.log('Screenshot saved as student-assignments-not-started.png');

  // 點擊 "進行中" tab
  await page.locator('button:has-text("進行中")').click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'student-assignments-in-progress.png', fullPage: true });
  console.log('Screenshot saved as student-assignments-in-progress.png');

  // 點擊 "已提交" tab
  await page.locator('button:has-text("已提交")').click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'student-assignments-submitted.png', fullPage: true });
  console.log('Screenshot saved as student-assignments-submitted.png');

  // 檢查控制台錯誤
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('Console error:', msg.text());
    }
  });

  // 檢查網路錯誤
  page.on('response', response => {
    if (response.status() >= 400) {
      console.error(`HTTP ${response.status()} error: ${response.url()}`);
    }
  });

  // 等待一下讓錯誤顯示出來
  await page.waitForTimeout(2000);
});
