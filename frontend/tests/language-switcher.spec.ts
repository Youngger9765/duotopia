import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('Language Switcher Tests', () => {
  test('should have language switcher on home page', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check for language switcher
    const languageSwitcher = page.locator('[role="combobox"]').first();
    await expect(languageSwitcher).toBeVisible();
  });

  test('should have language switcher on teacher login page', async ({ page }) => {
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    // Take screenshot before
    await page.screenshot({ path: 'teacher-login-before-switch.png' });

    // Check for language switcher
    const languageSwitcher = page.locator('[role="combobox"]').first();
    await expect(languageSwitcher).toBeVisible();

    // Click to switch language
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    // Take screenshot after opening
    await page.screenshot({ path: 'teacher-login-language-options.png' });
  });

  test('should have language switcher on student login page', async ({ page }) => {
    await page.goto(`${BASE_URL}/student/login`);
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'student-login-with-switcher.png' });

    // Check for language switcher
    const languageSwitcher = page.locator('[role="combobox"]').first();
    await expect(languageSwitcher).toBeVisible();
  });

  test('should switch language on teacher login page', async ({ page }) => {
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    // Get initial text
    const initialTitle = await page.locator('h1').first().textContent();
    console.log('Initial title:', initialTitle);

    // Click language switcher
    const languageSwitcher = page.locator('[role="combobox"]').first();
    await languageSwitcher.click();

    // Select English
    await page.locator('[role="option"]').filter({ hasText: 'English' }).click();
    await page.waitForTimeout(500);

    // Get new text
    const newTitle = await page.locator('h1').first().textContent();
    console.log('New title:', newTitle);

    // Titles should be different
    expect(initialTitle).not.toBe(newTitle);

    // Take screenshot in English
    await page.screenshot({ path: 'teacher-login-english.png' });
  });
});
