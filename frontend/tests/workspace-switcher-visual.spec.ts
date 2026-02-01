import { test } from '@playwright/test';

/**
 * Visual test for Workspace Switcher UI
 *
 * This test simply navigates to the teacher dashboard page
 * and takes screenshots to demonstrate the UI implementation.
 *
 * No functional assertions - just visual proof.
 */

test.describe('Workspace Switcher - Visual Proof', () => {
  test('take screenshot of teacher dashboard with workspace switcher', async ({ page }) => {
    // Set viewport for consistent screenshots
    await page.setViewportSize({ width: 1440, height: 900 });

    // Navigate directly to dashboard (will redirect to login if not authenticated)
    await page.goto('http://localhost:5173/teacher/dashboard');
    await page.waitForTimeout(2000); // Wait for page load

    // Take full page screenshot
    await page.screenshot({
      path: 'workspace-switcher-screenshots/01-dashboard-full.png',
      fullPage: true
    });

    console.log('✅ Screenshot saved: workspace-switcher-screenshots/01-dashboard-full.png');

    // If on login page, take that screenshot too
    const currentURL = page.url();
    if (currentURL.includes('login')) {
      await page.screenshot({
        path: 'workspace-switcher-screenshots/02-login-page.png',
        fullPage: true
      });
      console.log('📸 On login page - screenshot saved');
    }
  });

  test('navigate to teacher page and inspect sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });

    // Go to teacher routes
    await page.goto('http://localhost:5173/teacher');
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: 'workspace-switcher-screenshots/03-teacher-root.png',
      fullPage: true
    });

    console.log('✅ Screenshot saved: workspace-switcher-screenshots/03-teacher-root.png');

    // Try to find any tabs elements
    const tabs = await page.locator('[role="tablist"]').count();
    console.log(`Found ${tabs} tablist elements on page`);

    const personalText = await page.getByText('個人').count();
    const orgText = await page.getByText('機構').count();
    console.log(`Found "個人": ${personalText}, Found "機構": ${orgText}`);
  });

  test('inspect page HTML structure', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/dashboard');
    await page.waitForTimeout(2000);

    // Get page title
    const title = await page.title();
    console.log(`Page title: ${title}`);

    // Check for workspace-related elements in DOM
    const hasWorkspaceContext = await page.evaluate(() => {
      return document.body.innerHTML.includes('workspace');
    });
    console.log(`Page HTML contains "workspace": ${hasWorkspaceContext}`);

    // Take screenshot with browser DevTools-style annotation
    await page.screenshot({
      path: 'workspace-switcher-screenshots/04-html-structure.png',
      fullPage: true
    });
  });
});
