import { test, expect } from '@playwright/test';

test.describe('Teacher Workspace Switcher', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:5173/teacher/login');
    await page.waitForLoadState('networkidle');

    // Quick login with Demo Teacher
    const demoTeacherButton = page.locator('text=Demo Teacher (300 days prepaid)').first();
    await demoTeacherButton.click();

    // Wait for redirect to dashboard
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Wait for sidebar to load
    await page.waitForTimeout(1000);
  });

  test('should display workspace switcher tabs', async ({ page }) => {
    // Check if Personal and Organization tabs exist
    const personalTab = page.getByRole('tab', { name: '個人' });
    const orgTab = page.getByRole('tab', { name: '機構' });

    await expect(personalTab).toBeVisible();
    await expect(orgTab).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test-results/workspace-tabs.png', fullPage: true });
  });

  test('should show personal mode by default', async ({ page }) => {
    const personalTab = page.getByRole('tab', { name: '個人' });

    // Personal tab should be selected
    await expect(personalTab).toHaveAttribute('data-state', 'active');

    // Should show personal mode text
    await expect(page.getByText('個人教學模式 - 完整權限')).toBeVisible();

    await page.screenshot({ path: 'test-results/personal-mode.png', fullPage: true });
  });

  test('should switch to organization mode', async ({ page }) => {
    const orgTab = page.getByRole('tab', { name: '機構' });

    // Click organization tab
    await orgTab.click();
    await page.waitForTimeout(500); // Wait for transition

    // Organization tab should be active
    await expect(orgTab).toHaveAttribute('data-state', 'active');

    await page.screenshot({ path: 'test-results/organization-mode.png', fullPage: true });
  });

  test('should show read-only indicators in organization mode', async ({ page }) => {
    // Switch to organization mode
    await page.getByRole('tab', { name: '機構' }).click();
    await page.waitForTimeout(500);

    // Check if Eye icons are present (read-only indicators)
    const eyeIcons = page.locator('svg.lucide-eye');
    const count = await eyeIcons.count();

    console.log(`Found ${count} read-only indicators`);

    // Should have at least some read-only items (classrooms, students)
    expect(count).toBeGreaterThan(0);

    await page.screenshot({ path: 'test-results/readonly-indicators.png', fullPage: true });
  });

  test('should persist workspace selection in localStorage', async ({ page }) => {
    // Switch to organization mode
    await page.getByRole('tab', { name: '機構' }).click();
    await page.waitForTimeout(500);

    // Check localStorage
    const mode = await page.evaluate(() => localStorage.getItem('workspace:mode'));
    expect(mode).toBe('organization');

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Should still be in organization mode
    const orgTab = page.getByRole('tab', { name: '機構' });
    await expect(orgTab).toHaveAttribute('data-state', 'active');

    await page.screenshot({ path: 'test-results/localStorage-persistence.png', fullPage: true });
  });

  test('sidebar should show workspace switcher', async ({ page }) => {
    // Check if workspace switcher is visible in sidebar
    const sidebar = page.locator('.bg-white.dark\\:bg-gray-800.shadow-lg');
    await expect(sidebar).toBeVisible();

    // Workspace tabs should be in sidebar
    const tabsInSidebar = sidebar.locator('[role="tablist"]');
    await expect(tabsInSidebar).toBeVisible();

    await page.screenshot({ path: 'test-results/sidebar-integration.png', fullPage: true });
  });
});
