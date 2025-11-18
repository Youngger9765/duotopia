import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('Language Persistence Across Pages', () => {
  test('should persist language selection when navigating between pages', async ({ page }) => {
    // Start at home page
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Switch to English
    const languageSwitcher = page.locator('[role="combobox"]').first();
    await languageSwitcher.click();
    await page.locator('[role="option"]').filter({ hasText: 'English' }).click();
    await page.waitForTimeout(500);

    // Verify English is active
    await expect(languageSwitcher).toContainText('English');

    // Navigate to pricing page
    await page.goto(`${BASE_URL}/pricing`);
    await page.waitForLoadState('networkidle');

    // Check language is still English
    const pricingSwitcher = page.locator('[role="combobox"]').first();
    await expect(pricingSwitcher).toContainText('English');

    // Navigate to teacher login
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    // Check language is still English
    const loginSwitcher = page.locator('[role="combobox"]').first();
    await expect(loginSwitcher).toContainText('English');

    // Take screenshot
    await page.screenshot({ path: 'language-persist-english.png' });
  });

  test('should restore language preference on page reload', async ({ page }) => {
    // Go to home and switch to English
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const languageSwitcher = page.locator('[role="combobox"]').first();
    await languageSwitcher.click();
    await page.locator('[role="option"]').filter({ hasText: 'English' }).click();
    await page.waitForTimeout(500);

    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check language is still English after reload
    const reloadedSwitcher = page.locator('[role="combobox"]').first();
    await expect(reloadedSwitcher).toContainText('English');
  });

  test('should persist language when switching back to Chinese', async ({ page }) => {
    // Start at teacher login with English
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    // Switch to English
    let switcher = page.locator('[role="combobox"]').first();
    await switcher.click();
    await page.locator('[role="option"]').filter({ hasText: 'English' }).click();
    await page.waitForTimeout(500);

    // Navigate to student login
    await page.goto(`${BASE_URL}/student/login`);
    await page.waitForLoadState('networkidle');

    switcher = page.locator('[role="combobox"]').first();
    await expect(switcher).toContainText('English');

    // Switch back to Chinese
    await switcher.click();
    await page.locator('[role="option"]').filter({ hasText: '繁體中文' }).click();
    await page.waitForTimeout(500);

    // Navigate to home
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check language is Chinese
    switcher = page.locator('[role="combobox"]').first();
    await expect(switcher).toContainText('繁體中文');

    // Take screenshot
    await page.screenshot({ path: 'language-persist-chinese.png' });
  });

  test('should check localStorage contains language preference', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Switch to English
    const languageSwitcher = page.locator('[role="combobox"]').first();
    await languageSwitcher.click();
    await page.locator('[role="option"]').filter({ hasText: 'English' }).click();
    await page.waitForTimeout(500);

    // Check localStorage
    const i18nLanguage = await page.evaluate(() => {
      return localStorage.getItem('i18nextLng');
    });

    console.log('localStorage i18nextLng:', i18nLanguage);
    expect(i18nLanguage).toBe('en');
  });
});
