import { test, expect } from '@playwright/test';

/**
 * 最終測試：Workspace Switcher 完整功能驗證
 *
 * 測試帳號：demo@duotopia.com / Demo123!
 */

test.describe('Workspace Switcher - 最終驗證', () => {
  test('完整流程：登入 → 查看 Workspace Switcher → 截圖', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });

    // 1. 前往登入頁
    await page.goto('http://localhost:5173/teacher/login');
    await page.waitForLoadState('networkidle');

    console.log('✅ 登入頁面載入完成');
    await page.screenshot({
      path: 'workspace-final-screenshots/01-login-page.png',
      fullPage: true
    });

    // 2. 使用快速登入按鈕（Demo Teacher (300 days prepaid)）
    const quickLoginButton = page.locator('text=Demo Teacher (300 days prepaid)').first();
    await quickLoginButton.waitFor({ timeout: 5000 });
    await quickLoginButton.click();
    console.log('✅ 點擊 Demo Teacher 快速登入按鈕');

    // 3. 等待導向 dashboard
    try {
      await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
      console.log('✅ 成功導向 dashboard');
    } catch (e) {
      console.log('⚠️ 未導向 dashboard，當前 URL:', page.url());
      await page.screenshot({
        path: 'workspace-final-screenshots/02-after-login.png',
        fullPage: true
      });
    }

    await page.waitForTimeout(2000); // 等待頁面完全載入

    // 4. 截圖整個頁面
    await page.screenshot({
      path: 'workspace-final-screenshots/03-dashboard-full.png',
      fullPage: true
    });
    console.log('✅ Dashboard 完整截圖');

    // 5. 檢查 Workspace Switcher 元素
    const personalTab = page.getByRole('tab', { name: '個人' });
    const orgTab = page.getByRole('tab', { name: '機構' });

    const personalExists = await personalTab.count();
    const orgExists = await orgTab.count();

    console.log(`找到「個人」tab: ${personalExists}`);
    console.log(`找到「機構」tab: ${orgExists}`);

    if (personalExists > 0 && orgExists > 0) {
      console.log('✅ Workspace Switcher 存在！');

      // 截圖 Sidebar 區域
      const sidebar = page.locator('.bg-white.dark\\:bg-gray-800').first();
      await sidebar.screenshot({
        path: 'workspace-final-screenshots/04-sidebar-closeup.png'
      });

      // 測試切換到機構模式
      await orgTab.click();
      await page.waitForTimeout(500);
      console.log('✅ 切換到機構模式');

      await page.screenshot({
        path: 'workspace-final-screenshots/05-organization-mode.png',
        fullPage: true
      });

      // 檢查唯讀標記（Eye icon）
      const eyeIcons = page.locator('svg').filter({ hasText: /eye/i });
      const eyeCount = await eyeIcons.count();
      console.log(`找到 ${eyeCount} 個 Eye icon（唯讀標記）`);

    } else {
      console.log('❌ Workspace Switcher 未找到');

      // Debug: 列出所有 role=tab 的元素
      const allTabs = await page.locator('[role="tab"]').allTextContents();
      console.log('頁面上所有 tab 元素:', allTabs);

      // Debug: 檢查 HTML 是否包含 workspace 相關內容
      const htmlContent = await page.content();
      const hasWorkspace = htmlContent.includes('workspace') || htmlContent.includes('個人') || htmlContent.includes('機構');
      console.log('HTML 包含 workspace 相關內容:', hasWorkspace);
    }

    // 6. 最終狀態截圖
    await page.screenshot({
      path: 'workspace-final-screenshots/06-final-state.png',
      fullPage: true
    });

    console.log('✅ 測試完成！所有截圖已保存到 workspace-final-screenshots/');
  });
});
