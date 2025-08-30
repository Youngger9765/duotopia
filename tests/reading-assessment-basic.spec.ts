import { test, expect } from '@playwright/test';

const DEMO_EMAIL = 'demo@duotopia.com';
const DEMO_PASSWORD = 'demo123';

test.describe('Reading Assessment 基本功能測試', () => {
  test('開發提示已被移除', async ({ page }) => {
    // 登入
    await page.goto('http://localhost:5173/login/teacher');
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');
    
    // 等待登入完成
    await page.waitForURL('**/dashboard/**', { timeout: 10000 });
    
    // 導航到班級詳情頁
    await page.click('.classroom-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊第一個課程
    await page.click('.program-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊第一個課堂
    await page.click('.lesson-item:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊編輯按鈕開啟面板
    const editButton = page.locator('button:has-text("編輯")').first();
    await editButton.click();
    await page.waitForTimeout(1000);
    
    // 確認沒有開發提示文字
    const devNotice1 = page.locator('text=/提示.*OpenAI/');
    const devNotice2 = page.locator('text=/Edge-TTS/');
    const devNotice3 = page.locator('text=/💡 提示/');
    
    // 所有提示都不應該存在
    await expect(devNotice1).not.toBeVisible();
    await expect(devNotice2).not.toBeVisible();
    await expect(devNotice3).not.toBeVisible();
    
    console.log('✅ 開發提示已成功移除');
  });
  
  test('TTS 和錄音功能存在', async ({ page }) => {
    // 登入
    await page.goto('http://localhost:5173/login/teacher');
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');
    
    // 等待登入完成
    await page.waitForURL('**/dashboard/**', { timeout: 10000 });
    
    // 導航到班級詳情頁
    await page.click('.classroom-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊第一個課程
    await page.click('.program-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊第一個課堂
    await page.click('.lesson-item:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊編輯按鈕開啟面板
    const editButton = page.locator('button:has-text("編輯")').first();
    await editButton.click();
    await page.waitForTimeout(1000);
    
    // 檢查音檔按鈕存在
    const speakerIcon = page.locator('button[aria-label*="音檔"]').first();
    await expect(speakerIcon).toBeVisible();
    
    // 點擊音檔按鈕
    await speakerIcon.click();
    await page.waitForTimeout(500);
    
    // 檢查 Generate 和 Record 標籤存在
    const generateTab = page.locator('button[role="tab"]:has-text("Generate")');
    const recordTab = page.locator('button[role="tab"]:has-text("Record")');
    
    await expect(generateTab).toBeVisible();
    await expect(recordTab).toBeVisible();
    
    console.log('✅ TTS 和錄音功能正常');
  });
  
  test('儲存按鈕始終可用', async ({ page }) => {
    // 登入
    await page.goto('http://localhost:5173/login/teacher');
    await page.fill('input[type="email"]', DEMO_EMAIL);
    await page.fill('input[type="password"]', DEMO_PASSWORD);
    await page.click('button[type="submit"]');
    
    // 等待登入完成
    await page.waitForURL('**/dashboard/**', { timeout: 10000 });
    
    // 導航到班級詳情頁
    await page.click('.classroom-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊第一個課程
    await page.click('.program-card:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊第一個課堂
    await page.click('.lesson-item:first-child', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    // 點擊編輯按鈕開啟面板
    const editButton = page.locator('button:has-text("編輯")').first();
    await editButton.click();
    await page.waitForTimeout(1000);
    
    // 檢查儲存按鈕
    const saveButton = page.locator('button:has-text("儲存")');
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled(); // 不應該被禁用
    
    console.log('✅ 儲存按鈕始終可用');
  });
});