import { test } from '@playwright/test';

// Staging environment URLs
const STAGING_URL = 'https://duotopia-staging-frontend-b2ovkkgl6a-de.a.run.app';

test.describe('Staging I18n Visual Tests', () => {
  test('should display home page with language switcher', async ({ page }) => {
    await page.goto(STAGING_URL);

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Take screenshot of home page
    await page.screenshot({ path: 'staging-home-page.png', fullPage: true });

    // Check for language switcher
    const languageSwitcher = page.locator('text=繁體中文, text=English').first();
    if (await languageSwitcher.isVisible()) {
      await languageSwitcher.click();
      await page.screenshot({ path: 'staging-language-switcher.png' });
    }
  });

  test('should display teacher login page in Chinese', async ({ page }) => {
    await page.goto(`${STAGING_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'staging-teacher-login-zh.png', fullPage: true });

    // Check for Chinese text
    const pageContent = await page.textContent('body');
    console.log('Teacher login page contains Chinese:', pageContent?.includes('登入'));
  });

  test('should display student login page in Chinese', async ({ page }) => {
    await page.goto(`${STAGING_URL}/student/login`);
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'staging-student-login-zh.png', fullPage: true });

    // Check for Chinese text
    const pageContent = await page.textContent('body');
    console.log('Student login page contains Chinese:', pageContent?.includes('學生'));
  });

  test('should display pricing page with i18n', async ({ page }) => {
    await page.goto(`${STAGING_URL}/pricing`);
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'staging-pricing-page.png', fullPage: true });
  });
});
