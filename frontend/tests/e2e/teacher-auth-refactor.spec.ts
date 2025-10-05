import { test, expect } from '@playwright/test';

/**
 * E2E 測試：Teacher Auth 重構驗證
 *
 * 對應 docs/MANUAL_TESTING_STEPS.md 的自動化測試
 * 驗證 teacherAuthStore 重構後功能正常
 */
test.describe('Teacher Auth Refactor Verification', () => {

  test.beforeEach(async ({ page }) => {
    // 清除所有 localStorage (對應手動測試步驟)
    await page.goto('http://localhost:5173');
    await page.evaluate(() => localStorage.clear());
  });

  test('測試案例 1：教師登入功能 - localStorage 正確性', async ({ page }) => {
    // 1. 打開登入頁面
    await page.goto('http://localhost:5173/teacher/login');

    // 2. 使用測試帳號登入 (Demo 教師)
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');

    // 3. 等待跳轉到 dashboard
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });

    // 4. 等待 localStorage 寫入 (Zustand persist 需要時間)
    await page.waitForFunction(
      () => localStorage.getItem('teacher-auth-storage') !== null,
      { timeout: 5000 }
    );

    // 5. 驗證 URL
    await expect(page).toHaveURL(/.*\/teacher\/dashboard/);

    // 6. 檢查 localStorage
    const localStorageKeys = await page.evaluate(() => Object.keys(localStorage));
    const teacherAuthStorage = await page.evaluate(() =>
      localStorage.getItem('teacher-auth-storage')
    );

    // ✅ 應該存在的 key
    expect(localStorageKeys).toContain('teacher-auth-storage');
    expect(teacherAuthStorage).toBeTruthy();

    // ❌ 不應該存在的舊 keys
    const oldKeys = ['token', 'access_token', 'user', 'userInfo', 'role', 'username', 'userType', 'auth-storage'];
    oldKeys.forEach(key => {
      expect(localStorageKeys).not.toContain(key);
    });

    // 6. 驗證 teacher-auth-storage 格式
    const authData = await page.evaluate(() => {
      const data = localStorage.getItem('teacher-auth-storage');
      return data ? JSON.parse(data) : null;
    });

    expect(authData).toHaveProperty('state');
    expect(authData.state).toHaveProperty('token');
    expect(authData.state).toHaveProperty('user');
    expect(authData.state).toHaveProperty('isAuthenticated');
    expect(authData.state.isAuthenticated).toBe(true);
    expect(authData.state.user.email).toBe('demo@duotopia.com');

    console.log('✅ 測試案例 1 通過：localStorage 只有 teacher-auth-storage');
  });

  test('測試案例 1-B：快速登入按鈕 (Demo 教師)', async ({ page }) => {
    await page.goto('http://localhost:5173/teacher/login');

    // 點擊 Demo 教師快速登入按鈕
    await page.click('button:has-text("Demo 教師")');

    // 等待跳轉
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });

    // 等待 localStorage 寫入
    await page.waitForFunction(
      () => localStorage.getItem('teacher-auth-storage') !== null,
      { timeout: 5000 }
    );

    await expect(page).toHaveURL(/.*\/teacher\/dashboard/);

    // 驗證 localStorage
    const authData = await page.evaluate(() => {
      const data = localStorage.getItem('teacher-auth-storage');
      return data ? JSON.parse(data) : null;
    });

    expect(authData.state.isAuthenticated).toBe(true);
    expect(authData.state.user.is_demo).toBe(true);

    console.log('✅ 快速登入功能正常');
  });

  test('測試案例 2：PricingPage 登入流程', async ({ page }) => {
    // 1. 清除 localStorage
    await page.goto('http://localhost:5173');
    await page.evaluate(() => localStorage.clear());

    // 2. 打開 PricingPage
    await page.goto('http://localhost:5173/pricing');

    // 3. 點擊任一訂閱方案 (應該彈出登入 Modal)
    await page.click('button:has-text("選擇方案")').catch(() => {
      // 可能按鈕文字不同，試試其他方案按鈕
      return page.click('button:has-text("立即訂閱")');
    });

    // 4. 等待登入 Modal 出現
    await page.waitForSelector('input[type="email"]', { timeout: 5000 });

    // 5. 在 Modal 中登入
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button:has-text("登入")');

    // 6. 等待登入完成 + localStorage 寫入
    await page.waitForFunction(
      () => localStorage.getItem('teacher-auth-storage') !== null,
      { timeout: 5000 }
    );

    // 7. 檢查結果
    const authData = await page.evaluate(() => {
      const teacherAuth = localStorage.getItem('teacher-auth-storage');
      const selectedPlan = localStorage.getItem('selectedPlan');
      return {
        teacherAuth: teacherAuth ? JSON.parse(teacherAuth) : null,
        selectedPlan: selectedPlan ? JSON.parse(selectedPlan) : null,
        allKeys: Object.keys(localStorage)
      };
    });

    // localStorage 有 teacher-auth-storage
    expect(authData.teacherAuth).toBeTruthy();
    expect(authData.teacherAuth.state.isAuthenticated).toBe(true);

    // 沒有舊的 token keys
    const oldKeys = ['token', 'access_token', 'user', 'auth-storage'];
    oldKeys.forEach(key => {
      expect(authData.allKeys).not.toContain(key);
    });

    console.log('✅ 測試案例 2 通過：PricingPage 登入流程正常');
  });

  test('測試案例 3：Logout 功能', async ({ page }) => {
    // 1. 先登入
    await page.goto('http://localhost:5173/teacher/login');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });

    // 等待 localStorage 寫入
    await page.waitForFunction(
      () => localStorage.getItem('teacher-auth-storage') !== null,
      { timeout: 5000 }
    );

    // 2. 檢查登入狀態
    const beforeLogout = await page.evaluate(() => {
      const data = localStorage.getItem('teacher-auth-storage');
      return data ? JSON.parse(data) : null;
    });
    expect(beforeLogout.state.isAuthenticated).toBe(true);

    // 3. 執行 Logout (點擊登出按鈕)
    await page.click('button:has-text("登出")');

    // 等待狀態更新
    await page.waitForTimeout(500);

    // 4. 檢查結果
    const afterLogout = await page.evaluate(() => {
      const data = localStorage.getItem('teacher-auth-storage');
      return data ? JSON.parse(data) : null;
    });

    // 驗收標準
    expect(afterLogout.state.token).toBeNull();
    expect(afterLogout.state.user).toBeNull();
    expect(afterLogout.state.isAuthenticated).toBe(false);

    // 5. 重新整理頁面後仍然是登出狀態
    await page.reload();
    const afterReload = await page.evaluate(() => {
      const data = localStorage.getItem('teacher-auth-storage');
      return data ? JSON.parse(data) : null;
    });
    expect(afterReload.state.isAuthenticated).toBe(false);

    console.log('✅ 測試案例 3 通過：Logout 功能正常');
  });

  test('測試案例 4：跨角色隔離測試', async ({ page, context }) => {
    // 注意：這個測試需要學生登入 API 可用

    // 1. Teacher 登入
    await page.goto('http://localhost:5173/teacher/login');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });

    // 等待 localStorage 寫入
    await page.waitForFunction(
      () => localStorage.getItem('teacher-auth-storage') !== null,
      { timeout: 5000 }
    );

    // 2. 檢查 localStorage (應該有 teacher-auth-storage)
    let storageData = await page.evaluate(() => ({
      keys: Object.keys(localStorage),
      teacherAuth: localStorage.getItem('teacher-auth-storage')
    }));
    expect(storageData.keys).toContain('teacher-auth-storage');

    // 3. 開新分頁 Student 登入
    const studentPage = await context.newPage();
    await studentPage.goto('http://localhost:5173/student/login');

    // 學生登入流程 (使用完整 4 步驟)
    await studentPage.fill('input[type="email"]', 'demo@duotopia.com');
    await studentPage.click('button:has-text("下一步")');

    await studentPage.waitForSelector('button:has-text("五年級A班")', { timeout: 5000 });
    await studentPage.click('button:has-text("五年級A班")');

    await studentPage.waitForSelector('button:has-text("王小明")', { timeout: 5000 });
    await studentPage.click('button:has-text("王小明")');

    await studentPage.fill('input[type="password"]', '20120101');
    await studentPage.click('button:has-text("登入")');
    await studentPage.waitForURL('**/student/dashboard', { timeout: 10000 });

    // 4. 檢查 localStorage (應該同時有兩個 auth)
    storageData = await studentPage.evaluate(() => ({
      keys: Object.keys(localStorage),
      teacherAuth: localStorage.getItem('teacher-auth-storage'),
      studentAuth: localStorage.getItem('student-auth-storage')
    }));

    expect(storageData.keys).toContain('teacher-auth-storage');
    expect(storageData.keys).toContain('student-auth-storage');

    // 5. Teacher Logout (在原頁面 - 點擊登出按鈕)
    await page.click('button:has-text("登出")');
    await page.waitForTimeout(500);

    // 6. 檢查結果
    const finalTeacherAuth = await page.evaluate(() => {
      const data = localStorage.getItem('teacher-auth-storage');
      return data ? JSON.parse(data) : null;
    });

    const finalStudentAuth = await studentPage.evaluate(() => {
      const data = localStorage.getItem('student-auth-storage');
      return data ? JSON.parse(data) : null;
    });

    // Teacher token 被清除
    expect(finalTeacherAuth.state.isAuthenticated).toBe(false);

    // Student token 不受影響
    expect(finalStudentAuth.state.isAuthenticated).toBe(true);

    await studentPage.close();

    console.log('✅ 測試案例 4 通過：跨角色隔離正常');
  });

  test('完整性檢查：無 Console 錯誤', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // 執行完整登入流程
    await page.goto('http://localhost:5173/teacher/login');
    await page.fill('input[type="email"]', 'demo@duotopia.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });

    // 等待 localStorage 寫入 + 頁面完全載入
    await page.waitForFunction(
      () => localStorage.getItem('teacher-auth-storage') !== null,
      { timeout: 5000 }
    );
    await page.waitForTimeout(1000);

    // 檢查是否有 Console 錯誤
    expect(consoleErrors.length).toBe(0);

    if (consoleErrors.length > 0) {
      console.log('❌ Console Errors:', consoleErrors);
    } else {
      console.log('✅ 無 Console 錯誤');
    }
  });
});
