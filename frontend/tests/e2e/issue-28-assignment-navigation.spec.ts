/**
 * E2E Test for Issue #28: Remove assignment confirmation screen navigation
 *
 * Test Requirements:
 * 1. Return button in assignment work page → Navigate to assignment list
 * 2. Submit button in assignment work page → Navigate to assignment list
 * 3. No navigation to assignment detail/confirmation page
 *
 * @see https://github.com/Youngger9765/duotopia/issues/28
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.VITE_API_URL || 'https://duotopia-staging-backend-316409492201.asia-east1.run.app';
const FRONTEND_URL = 'http://localhost:5173';

// Test data
const TEST_STUDENT = {
  username: 'student001',
  password: 'password123',
};

test.describe('Issue #28: Assignment Navigation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as student
    await page.goto(`${FRONTEND_URL}/student/login`);

    // Fill login form
    await page.fill('input[name="username"]', TEST_STUDENT.username);
    await page.fill('input[name="password"]', TEST_STUDENT.password);

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for navigation to assignments page
    await page.waitForURL('**/student/assignments', { timeout: 10000 });
  });

  test('Return button should navigate to assignment list', async ({ page }) => {
    // Arrange: Find and click on an assignment
    const assignmentCard = page.locator('[data-testid="assignment-card"]').first();
    await assignmentCard.waitFor({ state: 'visible', timeout: 10000 });

    const startButton = assignmentCard.locator('[data-testid="assignment-action-button"]');
    await startButton.click();

    // Wait for navigation to activity page
    await page.waitForURL('**/assignment/*/activity', { timeout: 10000 });

    // Act: Click return button
    const returnButton = page.locator('button', { hasText: /返回|back/i }).first();
    await returnButton.waitFor({ state: 'visible', timeout: 5000 });
    await returnButton.click();

    // Assert: Should navigate to assignment list, not detail page
    await expect(page).toHaveURL(/\/student\/assignments$/, { timeout: 5000 });

    // Verify we are NOT on detail page
    await expect(page).not.toHaveURL(/\/student\/assignment\/\d+\/detail/);

    // Verify assignment list is visible
    const assignmentListHeader = page.locator('h3', { hasText: /作業狀態|Assignment Flow/i });
    await expect(assignmentListHeader).toBeVisible({ timeout: 5000 });
  });

  test('Submit button should navigate to assignment list', async ({ page, context }) => {
    // Enable API mocking for submit endpoint
    await context.route(`${API_URL}/api/students/assignments/*/submit`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Assignment submitted successfully' }),
      });
    });

    // Arrange: Find and click on an assignment
    const assignmentCard = page.locator('[data-testid="assignment-card"]').first();
    await assignmentCard.waitFor({ state: 'visible', timeout: 10000 });

    const startButton = assignmentCard.locator('[data-testid="assignment-action-button"]');
    await startButton.click();

    // Wait for navigation to activity page
    await page.waitForURL('**/assignment/*/activity', { timeout: 10000 });

    // Act: Find and click submit button
    const submitButton = page.locator('button', { hasText: /提交|submit/i }).first();

    // Check if submit button exists and is enabled
    const isSubmitVisible = await submitButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (isSubmitVisible) {
      await submitButton.click();

      // Assert: Should navigate to assignment list after submit
      await expect(page).toHaveURL(/\/student\/assignments$/, { timeout: 5000 });

      // Verify we are NOT on detail page
      await expect(page).not.toHaveURL(/\/student\/assignment\/\d+\/detail/);

      // Verify assignment list is visible
      const assignmentListHeader = page.locator('h3', { hasText: /作業狀態|Assignment Flow/i });
      await expect(assignmentListHeader).toBeVisible({ timeout: 5000 });
    } else {
      test.skip('Submit button not available for this assignment');
    }
  });

  test('Verify no navigation to confirmation/detail page during workflow', async ({ page }) => {
    // Arrange: Start an assignment
    const assignmentCard = page.locator('[data-testid="assignment-card"]').first();
    await assignmentCard.waitFor({ state: 'visible', timeout: 10000 });

    const startButton = assignmentCard.locator('[data-testid="assignment-action-button"]');
    await startButton.click();

    // Wait for navigation to activity page
    await page.waitForURL('**/assignment/*/activity', { timeout: 10000 });

    // Listen for navigation events
    const navigationPromise = page.waitForURL('**/student/assignment/*/detail', {
      timeout: 2000
    }).catch(() => null);

    // Act: Click return button
    const returnButton = page.locator('button', { hasText: /返回|back/i }).first();
    await returnButton.waitFor({ state: 'visible', timeout: 5000 });
    await returnButton.click();

    // Assert: Should NOT navigate to detail page
    const didNavigateToDetail = await navigationPromise;
    expect(didNavigateToDetail).toBeNull();

    // Should be on assignment list
    await expect(page).toHaveURL(/\/student\/assignments$/, { timeout: 3000 });
  });
});
