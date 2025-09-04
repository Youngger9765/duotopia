// @ts-check
const { test, expect } = require('@playwright/test');

const BASE_URL = 'https://duotopia-staging-frontend-qchnzlfpda-de.a.run.app';
const TEACHER_EMAIL = 'demo@duotopia.com';
const TEACHER_PASSWORD = 'demo123';

test.describe('Teacher E2E Tests', () => {
  test('Teacher login and view dashboard', async ({ page }) => {
    // 1. 前往登入頁面
    await page.goto(`${BASE_URL}/teacher/login`);
    console.log('✓ 到達登入頁面');

    // 2. 填寫登入表單
    await page.fill('input[type="email"]', TEACHER_EMAIL);
    await page.fill('input[type="password"]', TEACHER_PASSWORD);
    console.log('✓ 填寫登入資料');

    // 3. 點擊登入按鈕
    await page.click('button[type="submit"]');
    console.log('✓ 提交登入');

    // 4. 等待跳轉到 Dashboard
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
    console.log('✓ 成功跳轉到 Dashboard');

    // 5. 驗證 Dashboard 元素
    await expect(page.locator('h1')).toContainText('Dashboard');
    console.log('✓ Dashboard 載入成功');

    // 6. 檢查班級列表
    const classrooms = page.locator('[data-testid="classroom-card"]');
    const classroomCount = await classrooms.count();
    expect(classroomCount).toBeGreaterThan(0);
    console.log(`✓ 找到 ${classroomCount} 個班級`);
  });

  test('View classroom details', async ({ page }) => {
    // 先登入
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.fill('input[type="email"]', TEACHER_EMAIL);
    await page.fill('input[type="password"]', TEACHER_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher/dashboard');

    // 點擊第一個班級
    await page.click('[data-testid="classroom-card"]:first-child');
    await page.waitForURL('**/teacher/classroom/**');
    console.log('✓ 進入班級詳情頁面');

    // 驗證班級資訊顯示
    await expect(page.locator('h1')).toContainText('班');
    console.log('✓ 班級名稱顯示正確');

    // 檢查學生列表
    const students = page.locator('[data-testid="student-item"]');
    const studentCount = await students.count();
    console.log(`✓ 找到 ${studentCount} 位學生`);

    // 檢查課程列表
    const programs = page.locator('[data-testid="program-item"]');
    const programCount = await programs.count();
    console.log(`✓ 找到 ${programCount} 個課程`);
  });

  test('Drag and drop lesson reordering', async ({ page }) => {
    // 先登入並進入班級
    await page.goto(`${BASE_URL}/teacher/login`);
    await page.fill('input[type="email"]', TEACHER_EMAIL);
    await page.fill('input[type="password"]', TEACHER_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/teacher/dashboard');
    await page.click('[data-testid="classroom-card"]:first-child');
    await page.waitForURL('**/teacher/classroom/**');

    // 測試拖拽功能
    const firstLesson = page.locator('[data-testid="lesson-item"]:first-child');
    const secondLesson = page.locator('[data-testid="lesson-item"]:nth-child(2)');

    if (await firstLesson.isVisible() && await secondLesson.isVisible()) {
      // 記錄原始順序
      const originalFirst = await firstLesson.textContent();
      const originalSecond = await secondLesson.textContent();

      // 執行拖拽
      await firstLesson.dragTo(secondLesson);
      console.log('✓ 執行拖拽操作');

      // 等待重新排序
      await page.waitForTimeout(1000);

      // 驗證順序已改變
      const newFirst = await page.locator('[data-testid="lesson-item"]:first-child').textContent();
      const newSecond = await page.locator('[data-testid="lesson-item"]:nth-child(2)').textContent();

      expect(newFirst).toBe(originalSecond);
      expect(newSecond).toBe(originalFirst);
      console.log('✓ 拖拽重新排序成功');
    } else {
      console.log('⚠️ 沒有足夠的課程進行拖拽測試');
    }
  });
});
