import { test } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Student Portal Screenshot Tests', () => {
  const screenshotDir = '/tmp/student-screenshots';

  test.beforeAll(async () => {
    // Create screenshot directory if it doesn't exist
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
  });

  test('Complete student flow with screenshots', async ({ page }) => {
    console.log('🎬 Starting screenshot test for student portal');

    // ========== 1. Home Page ==========
    await page.goto('/');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${screenshotDir}/01-homepage.png`,
      fullPage: true
    });
    console.log('✅ Screenshot: Homepage');

    // ========== 2. Student Login Page ==========
    await page.click('text=學生登入');
    await page.waitForURL('/student/login');
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${screenshotDir}/02-student-login.png`,
      fullPage: true
    });
    console.log('✅ Screenshot: Student Login Page');

    // ========== 3. Direct Navigation to Assignments (for testing UI) ==========
    await page.goto('/student/assignments');
    await page.waitForTimeout(2000);

    // Check if redirected to login or showing assignments
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('⚠️ Redirected to login - need authentication');
      await page.screenshot({
        path: `${screenshotDir}/03-login-required.png`,
        fullPage: true
      });
    } else {
      await page.screenshot({
        path: `${screenshotDir}/03-assignment-list.png`,
        fullPage: true
      });
      console.log('✅ Screenshot: Assignment List');

      // Check for assignment cards
      const hasCards = await page.locator('[data-testid="assignment-card"]').count() > 0;
      if (hasCards) {
        console.log('📋 Found assignment cards');

        // Click first assignment card
        await page.locator('[data-testid="assignment-card"]').first().click();
        await page.waitForTimeout(2000);

        await page.screenshot({
          path: `${screenshotDir}/04-assignment-detail.png`,
          fullPage: true
        });
        console.log('✅ Screenshot: Assignment Detail');
      } else {
        console.log('📭 No assignments found - showing empty state');
        await page.screenshot({
          path: `${screenshotDir}/04-empty-assignments.png`,
          fullPage: true
        });
      }
    }

    // ========== 4. Test Responsive Design ==========
    console.log('📱 Testing responsive layouts...');

    // Mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/student/assignments');
    await page.waitForTimeout(1500);
    await page.screenshot({
      path: `${screenshotDir}/05-mobile-view.png`,
      fullPage: true
    });
    console.log('✅ Screenshot: Mobile View');

    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${screenshotDir}/06-tablet-view.png`,
      fullPage: true
    });
    console.log('✅ Screenshot: Tablet View');

    // Desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: `${screenshotDir}/07-desktop-view.png`,
      fullPage: true
    });
    console.log('✅ Screenshot: Desktop View');

    // ========== 5. Test Direct Component Routes ==========
    console.log('🔍 Testing direct component routes...');

    // Student Dashboard
    await page.goto('/student/dashboard');
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: `${screenshotDir}/08-student-dashboard.png`,
      fullPage: true
    });
    console.log('✅ Screenshot: Student Dashboard');

    // Assignment Detail with ID
    await page.goto('/student/assignment/1/detail');
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: `${screenshotDir}/09-assignment-detail-direct.png`,
      fullPage: true
    });
    console.log('✅ Screenshot: Assignment Detail Direct');

    // ========== 6. Component State Testing ==========
    console.log('🎯 Testing component states...');

    await page.goto('/student/assignments');
    await page.waitForTimeout(2000);

    // Check tabs if they exist
    const hasTab = await page.locator('text=已完成作業').isVisible().catch(() => false);
    if (hasTab) {
      await page.click('text=已完成作業');
      await page.waitForTimeout(1500);
      await page.screenshot({
        path: `${screenshotDir}/10-completed-assignments.png`,
        fullPage: true
      });
      console.log('✅ Screenshot: Completed Assignments Tab');
    }

    console.log('🎉 All screenshots captured successfully!');
    console.log(`📁 Screenshots saved to: ${screenshotDir}`);

    // List all screenshots
    const files = fs.readdirSync(screenshotDir);
    console.log('\n📸 Generated screenshots:');
    files.forEach(file => {
      const stats = fs.statSync(path.join(screenshotDir, file));
      console.log(`  - ${file} (${(stats.size / 1024).toFixed(2)} KB)`);
    });
  });

  test('Verify UI components are rendered', async ({ page }) => {
    console.log('🔍 Verifying UI components...');

    // Go to assignments page
    await page.goto('/student/assignments');
    await page.waitForTimeout(2000);

    // Check if key components exist
    const checks = [
      { selector: 'h1', name: 'Page Title' },
      { selector: '[data-testid="assignment-card"]', name: 'Assignment Cards' },
      { selector: 'button', name: 'Buttons' },
      { selector: 'text=我的作業', name: 'Chinese Text' },
    ];

    for (const check of checks) {
      const exists = await page.locator(check.selector).first().isVisible().catch(() => false);
      console.log(`${exists ? '✅' : '❌'} ${check.name}: ${exists ? 'Found' : 'Not Found'}`);

      if (exists) {
        // Capture element screenshot
        const element = page.locator(check.selector).first();
        await element.screenshot({
          path: `${screenshotDir}/element-${check.name.toLowerCase().replace(/\s+/g, '-')}.png`
        });
      }
    }
  });

  test.afterAll(async () => {
    console.log('\n📊 Test Summary:');
    console.log(`📁 Screenshots location: ${screenshotDir}`);
    console.log('⚠️ Remember to review screenshots and delete when done!');
    console.log('🗑️ To delete: rm -rf ' + screenshotDir);
  });
});
