import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('LanguageSwitcher RWD Tests', () => {
  test('should display correctly on mobile (375px)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    // Check LanguageSwitcher is visible
    const languageSwitcher = page.locator('[role="combobox"]').first();
    await expect(languageSwitcher).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'language-switcher-mobile-375.png', fullPage: true });

    // Count how many LanguageSwitchers are visible
    const switcherCount = await page.locator('[role="combobox"]').count();
    console.log(`Mobile (375px): Found ${switcherCount} LanguageSwitchers`);
  });

  test('should display correctly on tablet (768px)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    const languageSwitcher = page.locator('[role="combobox"]').first();
    await expect(languageSwitcher).toBeVisible();

    await page.screenshot({ path: 'language-switcher-tablet-768.png', fullPage: true });

    const switcherCount = await page.locator('[role="combobox"]').count();
    console.log(`Tablet (768px): Found ${switcherCount} LanguageSwitchers`);
  });

  test('should display correctly on desktop (1920px)', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 }); // Full HD
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    const languageSwitcher = page.locator('[role="combobox"]').first();
    await expect(languageSwitcher).toBeVisible();

    await page.screenshot({ path: 'language-switcher-desktop-1920.png' });

    const switcherCount = await page.locator('[role="combobox"]').count();
    console.log(`Desktop (1920px): Found ${switcherCount} LanguageSwitchers`);
  });

  test('StudentLayout mobile RWD', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    // Need to login first for student pages - skip for now
    await page.goto(`${BASE_URL}/student/login`);
    await page.waitForLoadState('networkidle');

    const switcherCount = await page.locator('[role="combobox"]').count();
    console.log(`StudentLogin Mobile (375px): Found ${switcherCount} LanguageSwitchers`);

    await page.screenshot({ path: 'student-login-mobile-375.png', fullPage: true });
  });

  test('should not show duplicate LanguageSwitchers', async ({ page }) => {
    // Test desktop size
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.waitForLoadState('networkidle');

    const switcherCount = await page.locator('[role="combobox"]').count();

    // Should only have ONE LanguageSwitcher visible
    expect(switcherCount).toBeLessThanOrEqual(1);

    console.log(`Desktop LanguageSwitcher count: ${switcherCount} (should be 1)`);
  });
});
