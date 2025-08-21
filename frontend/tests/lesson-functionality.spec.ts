import { test, expect } from '@playwright/test';

test.describe('課程單元功能測試', () => {
  test('三折頁設計應該正常顯示', async ({ page }) => {
    // 1. 登入
    await page.goto('http://localhost:5173/login');
    await page.fill('#email', 'teacher@individual.com');
    await page.fill('#password', 'test123');
    await page.click('button[type="submit"]');
    
    // 2. 等待登入完成並導航到課程頁面
    await page.waitForLoadState('networkidle');
    await page.goto('http://localhost:5173/individual/courses');
    
    // 3. 檢查頁面是否正常載入
    await expect(page.locator('h2:has-text("課程管理")')).toBeVisible();
    
    // 4. 檢查三折頁的三個面板
    // 第一面板 - 課程列表
    await expect(page.locator('h3:has-text("課程列表")')).toBeVisible();
    
    // 選擇第一個課程
    const firstCourse = page.locator('.bg-white.rounded-lg.shadow').nth(0).locator('.p-3.border-b').first();
    await firstCourse.click();
    
    // 第二面板 - 單元列表應該顯示
    await expect(page.locator('text=/單元/')).toBeVisible();
    
    // 選擇第一個單元
    const firstLesson = page.locator('.divide-y').first().locator('.p-3').first();
    await firstLesson.click();
    
    // 第三面板 - 單元內容應該顯示
    await expect(page.locator('h4:has-text("單元說明")')).toBeVisible();
    await expect(page.locator('h4:has-text("單元內容")')).toBeVisible();
    
    // 檢查編輯和預覽按鈕
    await expect(page.locator('button:has-text("編輯內容")')).toBeVisible();
    await expect(page.locator('button:has-text("預覽")')).toBeVisible();
    
    // 截圖保存
    await page.screenshot({ path: 'lesson-functionality-test.png', fullPage: true });
  });
  
  test('面板收合功能應該正常', async ({ page }) => {
    // 前置：登入並進入課程頁面
    await page.goto('http://localhost:5173/login');
    await page.fill('#email', 'teacher@individual.com');
    await page.fill('#password', 'test123');
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.goto('http://localhost:5173/individual/courses');
    
    // 選擇課程和單元
    await page.locator('.p-3.border-b').first().click();
    
    // 測試收合按鈕
    const collapseButton = page.locator('button[title="收合面板"]');
    await collapseButton.click();
    
    // 檢查面板是否收合
    await expect(page.locator('.w-12')).toBeVisible();
    
    // 展開面板
    const expandButton = page.locator('button[title="展開單元列表"]');
    await expandButton.click();
    
    // 檢查面板是否展開
    await expect(page.locator('.w-96')).toBeVisible();
  });
});