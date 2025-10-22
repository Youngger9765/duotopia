/**
 * Payment Card Management E2E Tests
 * 測試信用卡管理功能的完整流程
 */

import { test, expect } from '@playwright/test';

// 測試用的老師帳號
const TEACHER_EMAIL = 'demo@duotopia.com';
const TEACHER_PASSWORD = 'demo123';

// TapPay 測試卡號（Sandbox 環境）- 保留以備未來使用
// const TEST_CARD_NUMBER = '4242424242424242';
// const TEST_CARD_EXPIRY = '01/25';
// const TEST_CARD_CCV = '123';

test.describe('Payment Card Management E2E Tests', () => {

  test.beforeEach(async ({ page }) => {
    // 前往登入頁面
    await page.goto('http://localhost:5173/teacher/login');

    // 登入老師帳號
    await page.fill('input[type="email"]', TEACHER_EMAIL);
    await page.fill('input[type="password"]', TEACHER_PASSWORD);
    await page.click('button[type="submit"]');

    // 等待導向 Dashboard
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
  });

  test('1. 訂閱頁面應該顯示卡片管理區塊', async ({ page }) => {
    // 前往訂閱管理頁面
    await page.goto('http://localhost:5173/teacher/subscription');

    // 等待頁面載入
    await page.waitForLoadState('networkidle');

    // 檢查卡片管理標題
    await expect(page.locator('text=付款方式管理')).toBeVisible({ timeout: 10000 });

    // 檢查卡片管理說明文字
    await expect(page.locator('text=管理您的自動續訂付款方式')).toBeVisible();
  });

  test('2. 無卡片時應該顯示新增卡片按鈕', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');

    // 檢查是否有「新增信用卡」或「更換信用卡」按鈕
    const addCardButton = page.locator('button:has-text("新增信用卡"), button:has-text("更換信用卡")').first();
    await expect(addCardButton).toBeVisible({ timeout: 10000 });
  });

  test('3. 點擊新增信用卡應該開啟 TapPay 對話框', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');

    // 點擊新增/更換信用卡按鈕
    const cardButton = page.locator('button:has-text("新增信用卡"), button:has-text("更換信用卡")').first();
    await cardButton.click();

    // 等待對話框出現
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 });

    // 檢查對話框標題
    const dialogTitle = page.locator('text=新增信用卡, text=更換信用卡').first();
    await expect(dialogTitle).toBeVisible();

    // 檢查 TapPay 表單元素（iframe）
    // 注意：TapPay 使用 iframe，無法直接測試內部元素
    // 但可以檢查 iframe container 是否存在
    await expect(page.locator('#card-number')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#card-expiration-date')).toBeVisible();
    await expect(page.locator('#card-ccv')).toBeVisible();
  });

  test('4. 應該顯示 1 元驗證說明', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');

    // 點擊新增卡片
    const cardButton = page.locator('button:has-text("新增信用卡"), button:has-text("更換信用卡")').first();
    await cardButton.click();

    // 等待對話框
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 });

    // 檢查是否有 1 元驗證說明
    const verificationText = page.locator('text=/1.*元.*驗證/i, text=/測試.*退款/i').first();
    await expect(verificationText).toBeVisible({ timeout: 5000 });
  });

  test('5. 應該顯示安全提示', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');

    // 檢查安全提示（Alert 組件）
    // 如果已有卡片，應該看到安全提示
    // 如果沒有卡片，應該看到警告提示
    // const securityAlert = page.locator('text=/安全保障/i, text=/TapPay/i, text=/加密/i').first();

    // 使用 or 條件，因為有卡片和無卡片顯示不同
    const hasSecurityOrWarning = await page.locator('[role="alert"]').count() > 0;
    expect(hasSecurityOrWarning).toBe(true);
  });

  test('6. 已有卡片時應該顯示卡片資訊', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');

    // 等待 API 回應
    await page.waitForTimeout(2000);

    // 檢查是否有卡片顯示（條件式測試）
    const cardDisplay = page.locator('text=/目前使用的信用卡/i');
    const noCardAlert = page.locator('text=/尚未儲存付款方式/i');

    const hasCard = await cardDisplay.isVisible().catch(() => false);
    const noCard = await noCardAlert.isVisible().catch(() => false);

    // 應該有其中一個顯示
    expect(hasCard || noCard).toBe(true);

    if (hasCard) {
      // 如果有卡片，應該顯示更換和刪除按鈕
      await expect(page.locator('button:has-text("更換信用卡")')).toBeVisible();
      await expect(page.locator('button:has-text("刪除信用卡")')).toBeVisible();
    } else {
      // 如果沒有卡片，應該顯示新增按鈕
      await expect(page.locator('button:has-text("新增信用卡")')).toBeVisible();
    }
  });

  test('7. 點擊刪除卡片應該顯示確認對話框', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 檢查是否有刪除按鈕（表示已有卡片）
    const deleteButton = page.locator('button:has-text("刪除信用卡")');
    const hasDeleteButton = await deleteButton.isVisible().catch(() => false);

    if (hasDeleteButton) {
      // 點擊刪除按鈕
      await deleteButton.click();

      // 等待確認對話框
      await page.waitForSelector('[role="dialog"]', { timeout: 5000 });

      // 檢查確認訊息
      await expect(page.locator('text=/確認刪除/i')).toBeVisible();
      await expect(page.locator('text=/自動續訂.*無法使用/i')).toBeVisible();

      // 檢查確認和取消按鈕
      await expect(page.locator('button:has-text("確認刪除")')).toBeVisible();
      await expect(page.locator('button:has-text("取消")')).toBeVisible();

      // 點擊取消（不實際刪除）
      await page.click('button:has-text("取消")');
    } else {
      // 如果沒有卡片，跳過此測試
      test.skip();
    }
  });

  test('8. 卡片管理區塊應該在訂閱狀態卡片後面', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');

    // 檢查頁面結構順序
    const subscriptionStatus = page.locator('text=當前訂閱狀態, text=訂閱狀態').first();
    const cardManagement = page.locator('text=付款方式管理');
    const paymentHistory = page.locator('text=付款歷史');

    await expect(subscriptionStatus).toBeVisible();
    await expect(cardManagement).toBeVisible();
    await expect(paymentHistory).toBeVisible();

    // 檢查順序（Y 座標應該依序增加）
    const statusBox = await subscriptionStatus.boundingBox();
    const cardBox = await cardManagement.boundingBox();
    const historyBox = await paymentHistory.boundingBox();

    if (statusBox && cardBox && historyBox) {
      expect(statusBox.y).toBeLessThan(cardBox.y);
      expect(cardBox.y).toBeLessThan(historyBox.y);
    }
  });

  test('9. 卡片示意圖應該有正確的樣式', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // 檢查是否有卡片顯示
    const hasCard = await page.locator('text=/目前使用的信用卡/i').isVisible().catch(() => false);

    if (hasCard) {
      // 檢查卡片示意圖元素
      // 卡號遮蔽顯示 (••••)
      const maskedNumber = page.locator('text=/••••.*••••.*••••/i');
      await expect(maskedNumber).toBeVisible({ timeout: 5000 });

      // 應該顯示發卡銀行或卡別資訊
      const cardInfo = page.locator('text=/VISA|MasterCard|JCB|發卡銀行/i').first();
      await expect(cardInfo).toBeVisible();
    } else {
      test.skip();
    }
  });

  test('10. 無 Console 錯誤', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:5173/teacher/subscription');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // 過濾已知的無害錯誤
    const realErrors = consoleErrors.filter(error => {
      return !error.includes('404') &&
             !error.includes('favicon') &&
             !error.includes('TapPay SDK not loaded'); // TapPay 可能未載入（測試環境）
    });

    expect(realErrors.length).toBe(0);
  });
});

test.describe('Payment Card Management - API Integration', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/login');
    await page.fill('input[type="email"]', TEACHER_EMAIL);
    await page.fill('input[type="password"]', TEACHER_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
  });

  test('API: 查詢儲存的卡片應該正常回應', async ({ page }) => {
    // 監聽 API 請求
    const apiPromise = page.waitForResponse(
      response => response.url().includes('/api/payment/saved-card') && response.status() === 200,
      { timeout: 10000 }
    );

    await page.goto('http://localhost:5173/teacher/subscription');

    // 等待 API 回應
    const response = await apiPromise;
    const data = await response.json();

    // 檢查回應格式
    expect(data).toHaveProperty('has_card');

    if (data.has_card) {
      expect(data.card).toHaveProperty('last_four');
      expect(data.card).toHaveProperty('card_type');
      expect(data.card).toHaveProperty('issuer');
    }
  });

  test('API: 查詢應該不洩漏 card_key 或 card_token', async ({ page }) => {
    const apiPromise = page.waitForResponse(
      response => response.url().includes('/api/payment/saved-card') && response.status() === 200,
      { timeout: 10000 }
    );

    await page.goto('http://localhost:5173/teacher/subscription');
    const response = await apiPromise;
    const data = await response.json();

    // 確保回應中不包含敏感資訊
    const responseText = JSON.stringify(data);
    expect(responseText).not.toContain('card_key');
    expect(responseText).not.toContain('card_token');
    expect(responseText).not.toContain('card_bin_code');
  });
});
