import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Student Login Flow', () => {
  const screenshotDir = '/tmp/student-e2e-screenshots';

  test.beforeAll(async () => {
    // Create temporary screenshot directory
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
  });

  test.afterAll(async () => {
    // Clean up screenshots after all tests
    if (fs.existsSync(screenshotDir)) {
      const files = fs.readdirSync(screenshotDir);
      files.forEach(file => {
        fs.unlinkSync(path.join(screenshotDir, file));
      });
      fs.rmdirSync(screenshotDir);
      console.log('✅ Screenshots cleaned up');
    }
  });

  test('complete student login flow works', async ({ page }) => {
    // Navigate to student login page
    await page.goto('http://localhost:5173/student/login');

    // Take initial screenshot
    await page.screenshot({ path: `${screenshotDir}/01-login-page.png` });

    // Step 1: Enter teacher email
    await expect(page.locator('h2')).toContainText('請輸入老師 Email');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.screenshot({ path: `${screenshotDir}/02-email-entered.png` });
    await page.click('button:has-text("下一步")');

    // Step 2: Select classroom
    await page.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await expect(page.locator('h2')).toContainText('請選擇你的班級');
    await page.screenshot({ path: `${screenshotDir}/03-classroom-selection.png` });
    await page.click('button:has-text("五年級A班")');

    // Step 3: Select student
    await page.waitForSelector('button:has-text("王小明")', { timeout: 5000 });
    await expect(page.locator('h2')).toContainText('五年級A班');
    await expect(page.locator('text=請選擇你的名字')).toBeVisible();
    await page.screenshot({ path: `${screenshotDir}/04-student-selection.png` });
    await page.click('button:has-text("王小明")');

    // Step 4: Enter password
    await expect(page.locator('h2')).toContainText('你好，王小明');
    await page.fill('input[type="password"]', '20120101');
    await page.screenshot({ path: `${screenshotDir}/05-password-entry.png` });
    await page.click('button:has-text("登入")');

    // Wait for navigation to dashboard
    await page.waitForURL('**/student/dashboard', { timeout: 5000 });

    // Verify successful login
    await expect(page).toHaveURL(/.*\/student\/dashboard/);
    await page.screenshot({ path: `${screenshotDir}/06-dashboard-after-login.png` });

    console.log(`✅ Login successful! Screenshots saved to ${screenshotDir}`);
  });

  test('test with another student (李小美)', async ({ page }) => {
    // Navigate to student login page
    await page.goto('http://localhost:5173/student/login');

    // Step 1: Enter teacher email
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.click('button:has-text("下一步")');

    // Step 2: Select classroom
    await page.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await page.click('button:has-text("五年級A班")');

    // Step 3: Select student (李小美)
    await page.waitForSelector('button:has-text("李小美")', { timeout: 5000 });
    await page.click('button:has-text("李小美")');

    // Step 4: Enter password
    await page.fill('input[type="password"]', '20120102');
    await page.click('button:has-text("登入")');

    // Wait for navigation
    await page.waitForURL('**/student/dashboard', { timeout: 5000 });

    // Verify successful login
    await expect(page).toHaveURL(/.*\/student\/dashboard/);
    await page.screenshot({ path: `${screenshotDir}/07-li-xiaomei-dashboard.png` });

    console.log('✅ 李小美 login successful!');
  });

  test('URL parameter flow: auto-validate teacher email', async ({ page }) => {
    // Navigate to student login page with teacher_email parameter
    await page.goto('http://localhost:5173/student/login?teacher_email=demo@duotopia.com');

    // Should automatically skip step 1 and go to step 2 (classroom selection)
    // Wait for classroom selection to appear (step 1 should be skipped)
    await page.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await expect(page.locator('h2')).toContainText('請選擇你的班級');
    await page.screenshot({ path: `${screenshotDir}/08-url-param-classroom-selection.png` });

    // Select classroom
    await page.click('button:has-text("五年級A班")');

    // Step 3: Select student
    await page.waitForSelector('button:has-text("王小明")', { timeout: 5000 });
    await page.click('button:has-text("王小明")');

    // Step 4: Enter password
    await page.fill('input[type="password"]', '20120101');
    await page.screenshot({ path: `${screenshotDir}/09-url-param-password-entry.png` });
    await page.click('button:has-text("登入")');

    // Wait for navigation to dashboard
    await page.waitForURL('**/student/dashboard', { timeout: 5000 });

    // Verify successful login
    await expect(page).toHaveURL(/.*\/student\/dashboard/);
    await page.screenshot({ path: `${screenshotDir}/10-url-param-dashboard.png` });

    console.log('✅ URL parameter login successful! Step 1 was skipped.');
  });
});
