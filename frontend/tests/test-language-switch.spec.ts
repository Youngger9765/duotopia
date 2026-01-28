import { test } from '@playwright/test';

test('測試語言切換', async ({ page }) => {
  // 登入
  await page.goto('http://localhost:5173/teacher/login');
  await page.locator('text=Demo Teacher (300 days prepaid)').first().click();
  await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
  
  console.log('✅ 登入成功（預設英文）');
  
  // 點擊語言選擇器切換到中文
  await page.locator('[class*="w-\\[140px\\]"]').first().click();
  await page.waitForTimeout(500);
  await page.locator('text=繁體中文').click();
  await page.waitForTimeout(1000);
  
  console.log('✅ 切換到繁體中文');
  
  // 檢查語言選擇器
  const languageSelect = page.locator('[class*="w-\\[140px\\]"]').first();
  const selectValue = await languageSelect.textContent();
  console.log(`語言選擇器顯示：${selectValue}`);
  
  // 檢查 Workspace Switcher
  const personalTab = page.getByRole('tab', { name: '個人' });
  const orgTab = page.getByRole('tab', { name: '機構' });
  
  const personalText = await personalTab.textContent();
  const orgText = await orgTab.textContent();
  
  console.log(`個人 tab: ${personalText}`);
  console.log(`機構 tab: ${orgText}`);
  
  // 截圖
  await page.screenshot({ path: 'workspace-i18n-zh-TW.png', fullPage: true });
  console.log('✅ 中文截圖已儲存');
});
