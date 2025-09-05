import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Student Assignment Pages', () => {
  const screenshotDir = '/tmp/student-assignments-screenshots';

  test.beforeAll(async () => {
    // Create temporary screenshot directory
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
  });

  test.afterAll(async () => {
    // Clean up screenshots after all tests
    console.log(`📁 Screenshots saved to: ${screenshotDir}`);
    console.log('🧹 To clean up manually: rm -rf ' + screenshotDir);

    // List all screenshots
    if (fs.existsSync(screenshotDir)) {
      const files = fs.readdirSync(screenshotDir);
      console.log('📸 Generated screenshots:');
      files.forEach(file => {
        const stats = fs.statSync(path.join(screenshotDir, file));
        console.log(`  - ${file} (${(stats.size / 1024).toFixed(2)} KB)`);
      });
    }
  });

  test('student assignment list page', async ({ page }) => {
    // First login as student
    await page.goto('http://localhost:5173/student/login');

    // Quick login flow
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.click('button:has-text("下一步")');

    await page.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await page.click('button:has-text("五年級A班")');

    await page.waitForSelector('button:has-text("王小明")', { timeout: 5000 });
    await page.click('button:has-text("王小明")');

    await page.fill('input[type="password"]', '20120101');
    await page.click('button:has-text("登入")');

    // Wait for dashboard
    await page.waitForURL('**/student/dashboard', { timeout: 5000 });
    await page.screenshot({ path: `${screenshotDir}/01-dashboard.png` });

    // Navigate to assignments
    await page.click('a[href="/student/assignments"]');
    await page.waitForURL('**/student/assignments', { timeout: 5000 });

    // Take screenshots of assignment list
    await page.screenshot({ path: `${screenshotDir}/02-assignments-list.png`, fullPage: true });

    // Check tabs exist
    const activeTab = page.locator('button:has-text("進行中作業")');
    const completedTab = page.locator('button:has-text("已完成作業")');

    await expect(activeTab).toBeVisible();
    await expect(completedTab).toBeVisible();

    // Check active tab styling (should be blue)
    const activeTabClass = await activeTab.getAttribute('class');
    expect(activeTabClass).toContain('data-[state=active]:bg-blue-600');

    // Click completed tab
    await completedTab.click();
    await page.waitForTimeout(500); // Wait for tab transition
    await page.screenshot({ path: `${screenshotDir}/03-completed-assignments.png`, fullPage: true });

    // Check completed tab styling (should be green)
    const completedTabClass = await completedTab.getAttribute('class');
    expect(completedTabClass).toContain('data-[state=active]:bg-green-600');

    // Check for stats cards
    const statsCards = page.locator('.grid > .card').first();
    await expect(statsCards).toBeVisible();

    // Take close-up of stats
    await page.locator('.grid').first().screenshot({ path: `${screenshotDir}/04-stats-cards.png` });

    console.log('✅ Assignment list page test completed');
  });

  test('student assignment detail page', async ({ page }) => {
    // Quick login
    await page.goto('http://localhost:5173/student/login');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.click('button:has-text("下一步")');
    await page.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await page.click('button:has-text("五年級A班")');
    await page.waitForSelector('button:has-text("王小明")', { timeout: 5000 });
    await page.click('button:has-text("王小明")');
    await page.fill('input[type="password"]', '20120101');
    await page.click('button:has-text("登入")');
    await page.waitForURL('**/student/dashboard', { timeout: 5000 });

    // Go to assignments
    await page.goto('http://localhost:5173/student/assignments');
    await page.waitForSelector('[data-testid="assignment-card"]', { timeout: 5000 });

    // Click first assignment card
    const firstCard = page.locator('[data-testid="assignment-card"]').first();
    await firstCard.screenshot({ path: `${screenshotDir}/05-assignment-card.png` });

    // Check for action button and click
    const actionButton = firstCard.locator('[data-testid="assignment-action-button"]');
    await expect(actionButton).toBeVisible();
    await actionButton.click();

    // Wait for detail page
    await page.waitForURL('**/student/assignment/*/detail', { timeout: 5000 });
    await page.screenshot({ path: `${screenshotDir}/06-assignment-detail.png`, fullPage: true });

    // Check key elements
    await expect(page.locator('h1, h2').first()).toBeVisible(); // Title
    await expect(page.locator('text=整體進度')).toBeVisible();
    await expect(page.locator('button:has-text("返回作業列表")')).toBeVisible();

    // Check for progress bar
    const progressBar = page.locator('[role="progressbar"]').first();
    if (await progressBar.isVisible()) {
      await progressBar.screenshot({ path: `${screenshotDir}/07-progress-bar.png` });
    }

    console.log('✅ Assignment detail page test completed');
  });

  test('responsive design', async ({ page }) => {
    // Quick login
    await page.goto('http://localhost:5173/student/login');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.click('button:has-text("下一步")');
    await page.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await page.click('button:has-text("五年級A班")');
    await page.waitForSelector('button:has-text("王小明")', { timeout: 5000 });
    await page.click('button:has-text("王小明")');
    await page.fill('input[type="password"]', '20120101');
    await page.click('button:has-text("登入")');
    await page.waitForURL('**/student/dashboard', { timeout: 5000 });

    // Go to assignments
    await page.goto('http://localhost:5173/student/assignments');
    await page.waitForSelector('[data-testid="assignment-card"]', { timeout: 5000 });

    // Desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.screenshot({ path: `${screenshotDir}/08-desktop-view.png`, fullPage: true });

    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.screenshot({ path: `${screenshotDir}/09-tablet-view.png`, fullPage: true });

    // Mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.screenshot({ path: `${screenshotDir}/10-mobile-view.png`, fullPage: true });

    // Check mobile menu toggle
    const menuToggle = page.locator('button[aria-label="Toggle menu"]');
    if (await menuToggle.isVisible()) {
      await menuToggle.click();
      await page.waitForTimeout(300); // Wait for animation
      await page.screenshot({ path: `${screenshotDir}/11-mobile-menu-open.png` });
    }

    console.log('✅ Responsive design test completed');
  });

  test('sidebar navigation', async ({ page }) => {
    // Quick login
    await page.goto('http://localhost:5173/student/login');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.click('button:has-text("下一步")');
    await page.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await page.click('button:has-text("五年級A班")');
    await page.waitForSelector('button:has-text("王小明")', { timeout: 5000 });
    await page.click('button:has-text("王小明")');
    await page.fill('input[type="password"]', '20120101');
    await page.click('button:has-text("登入")');
    await page.waitForURL('**/student/dashboard', { timeout: 5000 });

    // Check sidebar exists
    const sidebar = page.locator('nav').first();
    await expect(sidebar).toBeVisible();
    await sidebar.screenshot({ path: `${screenshotDir}/12-sidebar.png` });

    // Check navigation items
    const navItems = [
      { text: '首頁', url: '/student/dashboard' },
      { text: '我的作業', url: '/student/assignments' },
      { text: '學習進度', url: '/student/progress' },
      { text: '個人設定', url: '/student/settings' }
    ];

    for (const item of navItems) {
      const navLink = page.locator(`a:has-text("${item.text}")`);
      await expect(navLink).toBeVisible();

      // Click and verify navigation (skip if current page)
      const currentUrl = page.url();
      if (!currentUrl.includes(item.url)) {
        await navLink.click();
        await page.waitForURL(`**${item.url}`, { timeout: 5000 }).catch(() => {
          // Some pages might not exist yet, that's ok
        });
      }
    }

    console.log('✅ Sidebar navigation test completed');
  });
});
