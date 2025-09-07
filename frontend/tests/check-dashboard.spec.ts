import { test } from '@playwright/test';

test('Check student dashboard', async ({ page }) => {
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

  // 截圖
  await page.screenshot({ path: 'student-dashboard-current.png', fullPage: true });
  console.log('Screenshot saved as student-dashboard-current.png');
});
