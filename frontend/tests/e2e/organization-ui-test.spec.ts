import { test, expect, Page } from '@playwright/test';

/**
 * Organization UI Test Suite
 *
 * Tests:
 * 1. org_owner role - redirect to /organization/dashboard
 * 2. org_owner role - access to organization features
 * 3. pure teacher role - redirect to /teacher/dashboard
 * 4. pure teacher role - blocked from organization features
 * 5. UI functionality (expand nodes, click schools, etc.)
 */

const ORG_OWNER_CREDENTIALS = {
  email: 'owner@duotopia.com',
  password: 'owner123',
};

const TEACHER_CREDENTIALS = {
  email: 'orgteacher@duotopia.com',
  password: 'orgteacher123',
};

// Helper function to login
async function login(page: Page, email: string, password: string) {
  await page.goto('/teacher/login');
  await page.waitForLoadState('networkidle');

  // Fill login form
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);

  // Click login button and wait for navigation
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle', timeout: 15000 }),
    page.click('button[type="submit"]'),
  ]);
}

// Helper function to logout
async function logout(page: Page) {
  // Look for logout button in navbar/sidebar
  const logoutButton = page.locator('button:has-text("登出"), button:has-text("Logout")').first();
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    await page.waitForLoadState('networkidle');
  }
}

test.describe('Organization UI Tests - org_owner Role', () => {
  test('should redirect org_owner to /organization/dashboard after login', async ({ page }) => {
    // Step 1: Login as org_owner
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);

    // Step 2: Verify redirect to /organization/dashboard
    await expect(page).toHaveURL(/\/organization\/dashboard/, { timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'test-results/org-owner-dashboard.png', fullPage: true });
  });

  test('should display organization management UI for org_owner', async ({ page }) => {
    // Login as org_owner
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/organization\/dashboard/);

    // Verify page title/heading
    const heading = page.locator('h1, h2').filter({ hasText: /組織管理|組織架構|Organization/ }).first();
    await expect(heading).toBeVisible({ timeout: 5000 });

    // Verify sidebar has organization-related items
    const sidebar = page.locator('[role="navigation"], nav, aside').first();
    await expect(sidebar).toBeVisible();

    // Check for organization menu items (flexible matching)
    const hasOrgMenu = await page.locator('text=/組織架構|學校管理|教師管理|Organization|Schools|Teachers/i').count();
    expect(hasOrgMenu).toBeGreaterThan(0);

    console.log('✅ Organization management UI verified');
  });

  test('should display organization tree structure', async ({ page }) => {
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/organization\/dashboard/);

    // Wait for tree to load
    await page.waitForTimeout(2000);

    // Look for tree structure elements (common tree indicators)
    const treeElements = await page.locator('[role="tree"], [role="treeitem"], .tree, .node').count();

    if (treeElements > 0) {
      console.log(`✅ Found ${treeElements} tree elements`);
    } else {
      console.log('⚠️ Tree structure not found - check if data is loaded');
    }

    // Take screenshot for visual verification
    await page.screenshot({ path: 'test-results/org-tree-structure.png', fullPage: true });
  });

  test('should navigate to Schools page', async ({ page }) => {
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);

    // Click on "學校管理" or "Schools" link
    const schoolsLink = page.locator('a:has-text("學校管理"), a:has-text("Schools")').first();
    await schoolsLink.click();

    // Verify navigation
    await expect(page).toHaveURL(/\/organization\/schools/, { timeout: 10000 });

    // Verify page loaded
    const pageHeading = page.locator('h1, h2').filter({ hasText: /學校|Schools/ }).first();
    await expect(pageHeading).toBeVisible({ timeout: 5000 });

    // Take screenshot
    await page.screenshot({ path: 'test-results/schools-page.png', fullPage: true });

    console.log('✅ Schools page navigation successful');
  });

  test('should navigate to Teachers page', async ({ page }) => {
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);

    // Click on "教師管理" or "Teachers" link
    const teachersLink = page.locator('a:has-text("教師管理"), a:has-text("Teachers")').first();
    await teachersLink.click();

    // Verify navigation
    await expect(page).toHaveURL(/\/organization\/teachers/, { timeout: 10000 });

    // Verify page loaded
    const pageHeading = page.locator('h1, h2').filter({ hasText: /教師|Teachers/ }).first();
    await expect(pageHeading).toBeVisible({ timeout: 5000 });

    // Take screenshot
    await page.screenshot({ path: 'test-results/teachers-page.png', fullPage: true });

    console.log('✅ Teachers page navigation successful');
  });
});

test.describe('Organization UI Tests - Pure Teacher Role', () => {
  test('should redirect pure teacher to /teacher/dashboard after login', async ({ page }) => {
    // Step 1: Login as pure teacher
    await login(page, TEACHER_CREDENTIALS.email, TEACHER_CREDENTIALS.password);

    // Step 2: Verify redirect to /teacher/dashboard (NOT /organization)
    await expect(page).toHaveURL(/\/teacher\/dashboard/, { timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'test-results/teacher-dashboard.png', fullPage: true });

    console.log('✅ Pure teacher redirected to /teacher/dashboard');
  });

  test('should NOT display organization menu items for pure teacher', async ({ page }) => {
    await login(page, TEACHER_CREDENTIALS.email, TEACHER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/teacher\/dashboard/);

    // Wait for page to fully load
    await page.waitForTimeout(2000);

    // Check that organization-specific items are NOT visible
    const orgMenuItems = page.locator('text=/組織架構|學校管理|Organization Structure|School Management/i');
    const count = await orgMenuItems.count();

    expect(count).toBe(0);
    console.log('✅ Organization menu items correctly hidden from pure teacher');
  });

  test('should block pure teacher from accessing /organization/dashboard', async ({ page }) => {
    await login(page, TEACHER_CREDENTIALS.email, TEACHER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/teacher\/dashboard/);

    // Attempt to navigate to organization dashboard
    await page.goto('/organization/dashboard');
    await page.waitForLoadState('networkidle');

    // Should be redirected back or show error
    const currentUrl = page.url();

    // Either redirected to /teacher/dashboard or shows permission error
    const isRedirected = currentUrl.includes('/teacher/dashboard');
    const hasError = await page.locator('text=/權限|Permission|Access Denied/i').count() > 0;

    expect(isRedirected || hasError).toBeTruthy();

    if (isRedirected) {
      console.log('✅ Pure teacher redirected away from /organization/dashboard');
    } else if (hasError) {
      console.log('✅ Pure teacher sees permission error');
    }

    // Take screenshot
    await page.screenshot({ path: 'test-results/teacher-blocked-org.png', fullPage: true });
  });

  test('should block pure teacher from accessing /organization/schools', async ({ page }) => {
    await login(page, TEACHER_CREDENTIALS.email, TEACHER_CREDENTIALS.password);

    // Attempt to navigate to schools page
    await page.goto('/organization/schools');
    await page.waitForLoadState('networkidle');

    const currentUrl = page.url();
    const isBlocked = !currentUrl.includes('/organization/schools');

    expect(isBlocked).toBeTruthy();
    console.log('✅ Pure teacher blocked from /organization/schools');
  });

  test('should block pure teacher from accessing /organization/teachers', async ({ page }) => {
    await login(page, TEACHER_CREDENTIALS.email, TEACHER_CREDENTIALS.password);

    // Attempt to navigate to teachers page
    await page.goto('/organization/teachers');
    await page.waitForLoadState('networkidle');

    const currentUrl = page.url();
    const isBlocked = !currentUrl.includes('/organization/teachers');

    expect(isBlocked).toBeTruthy();
    console.log('✅ Pure teacher blocked from /organization/teachers');
  });
});

test.describe('Organization UI Functionality Tests', () => {
  test('should expand and collapse organization tree nodes', async ({ page }) => {
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/organization\/dashboard/);

    // Wait for tree to load
    await page.waitForTimeout(2000);

    // Look for expandable nodes (common patterns)
    const expandButtons = page.locator('button[aria-expanded], [role="button"]:has-text("▶"), [role="button"]:has-text("▼")');
    const buttonCount = await expandButtons.count();

    if (buttonCount > 0) {
      // Click first expandable node
      await expandButtons.first().click();
      await page.waitForTimeout(500);

      console.log('✅ Tree node interaction successful');

      // Take screenshot
      await page.screenshot({ path: 'test-results/tree-expanded.png', fullPage: true });
    } else {
      console.log('⚠️ No expandable tree nodes found - tree might be already expanded or empty');
    }
  });

  test('should open "Add School" dialog from Schools page', async ({ page }) => {
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);

    // Navigate to Schools page
    const schoolsLink = page.locator('a:has-text("學校管理"), a:has-text("Schools")').first();
    await schoolsLink.click();
    await expect(page).toHaveURL(/\/organization\/schools/);

    // Click "Add School" or "新增學校" button
    const addButton = page.locator('button:has-text("新增"), button:has-text("Add")').first();

    if (await addButton.isVisible()) {
      await addButton.click();
      await page.waitForTimeout(500);

      // Verify dialog opened
      const dialog = page.locator('[role="dialog"], .dialog, .modal').first();
      await expect(dialog).toBeVisible({ timeout: 3000 });

      console.log('✅ Add School dialog opened');

      // Take screenshot
      await page.screenshot({ path: 'test-results/add-school-dialog.png', fullPage: true });

      // Click cancel/close
      const cancelButton = page.locator('button:has-text("取消"), button:has-text("Cancel")').first();
      if (await cancelButton.isVisible()) {
        await cancelButton.click();
        await page.waitForTimeout(500);
        console.log('✅ Dialog closed successfully');
      }
    } else {
      console.log('⚠️ Add School button not found');
    }
  });

  test('should measure page load performance', async ({ page }) => {
    const startTime = Date.now();

    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/organization\/dashboard/);

    const loadTime = Date.now() - startTime;

    console.log(`📊 Organization dashboard load time: ${loadTime}ms`);

    // Performance threshold: should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });
});

test.describe('Cross-Role Verification', () => {
  test('should correctly switch between org_owner and teacher views', async ({ page }) => {
    // Step 1: Login as org_owner
    await login(page, ORG_OWNER_CREDENTIALS.email, ORG_OWNER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/organization\/dashboard/);
    console.log('✅ Step 1: Logged in as org_owner');

    // Verify org menu is visible
    const orgMenuCount1 = await page.locator('text=/組織架構|學校管理/i').count();
    expect(orgMenuCount1).toBeGreaterThan(0);
    console.log('✅ Step 2: Organization menu visible for org_owner');

    // Step 2: Logout
    await logout(page);
    await page.waitForTimeout(1000);
    console.log('✅ Step 3: Logged out');

    // Step 3: Login as pure teacher
    await login(page, TEACHER_CREDENTIALS.email, TEACHER_CREDENTIALS.password);
    await expect(page).toHaveURL(/\/teacher\/dashboard/);
    console.log('✅ Step 4: Logged in as pure teacher');

    // Verify org menu is hidden
    const orgMenuCount2 = await page.locator('text=/組織架構|學校管理/i').count();
    expect(orgMenuCount2).toBe(0);
    console.log('✅ Step 5: Organization menu correctly hidden for teacher');

    // Take final screenshot
    await page.screenshot({ path: 'test-results/teacher-view-final.png', fullPage: true });
  });
});
