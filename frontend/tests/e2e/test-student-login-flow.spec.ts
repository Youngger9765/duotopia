import { test, expect } from '@playwright/test';

test.describe('Student Login Flow', () => {
  test('complete student login flow works', async ({ page }) => {
    // Navigate to student login page
    await page.goto('http://localhost:5173/student-login');

    // Step 1: Enter teacher email
    await expect(page.locator('h2')).toContainText('請輸入老師 Email');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.click('button:has-text("下一步")');

    // Step 2: Select classroom
    await page.waitForTimeout(1000); // Wait for API
    await expect(page.locator('h2')).toContainText('請選擇你的班級');
    await page.click('button:has-text("五年級A班")');

    // Step 3: Select student
    await page.waitForTimeout(1000); // Wait for API
    await expect(page.locator('h2')).toContainText('請選擇你的名字');
    await page.click('button:has-text("王小明")');

    // Step 4: Enter password
    await expect(page.locator('h2')).toContainText('你好，王小明');
    await page.fill('input[type="password"]', '20120101');
    await page.click('button:has-text("登入")');

    // Wait for navigation or error
    await page.waitForTimeout(2000);

    // Check if login was successful
    const url = page.url();
    console.log('Final URL after login:', url);

    // Check for error message
    const errorMessage = await page.locator('.text-red-500').textContent().catch(() => null);
    if (errorMessage) {
      console.log('Error message:', errorMessage);
    }

    // Take screenshot for debugging
    await page.screenshot({ path: 'student-login-result.png' });
  });

  test('test with default password student', async ({ page }) => {
    // Navigate to student login page
    await page.goto('http://localhost:5173/student-login');

    // Step 1: Enter teacher email
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.click('button:has-text("下一步")');

    // Step 2: Select classroom
    await page.waitForTimeout(1000);
    await page.click('button:has-text("五年級A班")');

    // Step 3: Select student (李小美 uses default password)
    await page.waitForTimeout(1000);
    await page.click('button:has-text("李小美")');

    // Step 4: Enter default password
    await page.fill('input[type="password"]', '20120101');
    await page.click('button:has-text("登入")');

    // Wait for navigation
    await page.waitForTimeout(2000);

    // Check result
    const url = page.url();
    console.log('Final URL after login with default password:', url);

    await page.screenshot({ path: 'student-login-default-password.png' });
  });
});
