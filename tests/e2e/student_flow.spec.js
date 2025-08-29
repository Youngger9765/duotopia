// @ts-check
const { test, expect } = require('@playwright/test');

const BASE_URL = 'https://duotopia-staging-frontend-qchnzlfpda-de.a.run.app';
const TEACHER_EMAIL = 'demo@duotopia.com';

test.describe('Student E2E Tests', () => {
  test('Student multi-step login', async ({ page }) => {
    // 1. 前往學生登入頁面
    await page.goto(`${BASE_URL}/student/login`);
    console.log('✓ 到達學生登入頁面');
    
    // Step 1: 選擇教師
    await page.fill('input[placeholder*="教師"]', TEACHER_EMAIL);
    await page.click('button:has-text("下一步")');
    console.log('✓ Step 1: 選擇教師完成');
    
    // Step 2: 選擇班級
    await page.waitForSelector('select, [data-testid="classroom-select"]');
    await page.selectOption('select', { index: 1 }); // 選擇第一個班級
    await page.click('button:has-text("下一步")');
    console.log('✓ Step 2: 選擇班級完成');
    
    // Step 3: 選擇學生
    await page.waitForSelector('select, [data-testid="student-select"]');
    await page.selectOption('select', { index: 1 }); // 選擇第一個學生
    await page.click('button:has-text("下一步")');
    console.log('✓ Step 3: 選擇學生完成');
    
    // Step 4: 輸入密碼
    await page.fill('input[type="password"]', '20120101'); // 使用預設密碼
    await page.click('button[type="submit"]');
    console.log('✓ Step 4: 輸入密碼完成');
    
    // 等待跳轉到學生首頁
    await page.waitForURL('**/student/**', { timeout: 10000 });
    console.log('✓ 成功登入學生帳號');
  });
  
  test('View student assignments', async ({ page }) => {
    // 快速登入（使用李小美的帳號）
    await page.goto(`${BASE_URL}/student/login`);
    
    // Step 1: 教師
    await page.fill('input[placeholder*="教師"]', TEACHER_EMAIL);
    await page.click('button:has-text("下一步")');
    
    // Step 2: 選擇五年級A班
    await page.waitForSelector('select');
    await page.selectOption('select', { value: '1' });
    await page.click('button:has-text("下一步")');
    
    // Step 3: 選擇李小美
    await page.waitForSelector('select');
    await page.selectOption('select', { label: '李小美' });
    await page.click('button:has-text("下一步")');
    
    // Step 4: 密碼
    await page.fill('input[type="password"]', '20120101');
    await page.click('button[type="submit"]');
    
    // 等待進入學生首頁
    await page.waitForURL('**/student/**');
    console.log('✓ 學生登入成功');
    
    // 檢查作業列表
    const assignments = page.locator('[data-testid="assignment-card"]');
    const assignmentCount = await assignments.count();
    console.log(`✓ 找到 ${assignmentCount} 個作業`);
    
    if (assignmentCount > 0) {
      // 點擊第一個作業
      await assignments.first().click();
      await page.waitForURL('**/student/assignment/**');
      console.log('✓ 進入作業詳情頁面');
      
      // 檢查作業內容
      await expect(page.locator('h1')).toBeVisible();
      console.log('✓ 作業內容載入成功');
    }
  });
  
  test('Complete practice activity', async ({ page }) => {
    // 登入學生帳號
    await page.goto(`${BASE_URL}/student/login`);
    await page.fill('input[placeholder*="教師"]', TEACHER_EMAIL);
    await page.click('button:has-text("下一步")');
    await page.selectOption('select', { value: '1' });
    await page.click('button:has-text("下一步")');
    await page.selectOption('select', { label: '王小明' });
    await page.click('button:has-text("下一步")');
    await page.fill('input[type="password"]', 'mynewpassword123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/student/**');
    
    // 找到練習活動
    const practiceButton = page.locator('button:has-text("開始練習")').first();
    if (await practiceButton.isVisible()) {
      await practiceButton.click();
      console.log('✓ 開始練習活動');
      
      // 等待活動載入
      await page.waitForTimeout(2000);
      
      // 檢查活動頁面元素
      const activityTitle = page.locator('h1, h2').first();
      await expect(activityTitle).toBeVisible();
      console.log('✓ 活動頁面載入成功');
      
      // 模擬完成活動
      const submitButton = page.locator('button:has-text("提交"), button:has-text("完成")');
      if (await submitButton.isVisible()) {
        await submitButton.click();
        console.log('✓ 提交練習結果');
      }
    } else {
      console.log('⚠️ 沒有可用的練習活動');
    }
  });
});