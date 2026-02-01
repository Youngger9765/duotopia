import { test, expect } from '@playwright/test';

test('語言選擇器和國際化測試', async ({ page }) => {
  // 登入
  await page.goto('http://localhost:5173/teacher/login');
  await page.locator('text=Demo Teacher (300 days prepaid)').first().click();
  await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
  
  console.log('✅ 登入成功');
  
  // 檢查語言選擇器是否有值
  const languageSelect = page.locator('[class*="w-\\[140px\\]"]').first();
  const selectValue = await languageSelect.textContent();
  console.log(`語言選擇器顯示：${selectValue}`);
  
  // 檢查 Workspace Switcher 的 tab
  const personalTab = page.getByRole('tab', { name: /個人|Personal/ });
  const orgTab = page.getByRole('tab', { name: /機構|Organization/ });
  
  const personalText = await personalTab.textContent();
  const orgText = await orgTab.textContent();
  
  console.log(`個人 tab: ${personalText}`);
  console.log(`機構 tab: ${orgText}`);
  
  // 截圖
  await page.screenshot({ path: 'workspace-i18n-test.png', fullPage: true });
  console.log('✅ 截圖已儲存');
});
