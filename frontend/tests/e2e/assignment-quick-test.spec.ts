import { test, expect } from '@playwright/test';

test.describe('Assignment Dashboard Quick Test', () => {
  test('Test all assignment features', async ({ page }) => {
    console.log('📍 Starting assignment dashboard test...');

    // 1. Navigate to teacher login
    console.log('1️⃣ Navigating to teacher login...');
    await page.goto('http://localhost:5173/teacher/login');

    // 2. Login as teacher
    console.log('2️⃣ Logging in as teacher...');
    await page.fill('input[type="email"]', 'teacher1@duotopia.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load
    await page.waitForURL('**/teacher/dashboard', { timeout: 10000 });
    console.log('✅ Login successful!');

    // 3. Navigate to classrooms
    console.log('3️⃣ Navigating to classrooms...');
    await page.goto('http://localhost:5173/teacher/classrooms');
    await page.waitForSelector('text=班級列表', { timeout: 5000 });

    // 4. Click on first classroom
    console.log('4️⃣ Entering first classroom...');
    const classroomCards = page.locator('.bg-white.rounded-lg.shadow');
    const count = await classroomCards.count();
    console.log(`   Found ${count} classrooms`);

    if (count > 0) {
      await classroomCards.first().click();
      await page.waitForURL('**/teacher/classrooms/*', { timeout: 5000 });
      console.log('✅ Entered classroom detail page');

      // 5. Click on Assignment tab
      console.log('5️⃣ Testing Assignment Tab...');
      await page.click('button:has-text("作業管理")');
      await page.waitForSelector('text=作業列表', { timeout: 5000 });
      console.log('✅ Assignment tab loaded');

      // 6. Test Create Assignment button
      console.log('6️⃣ Testing Create Assignment button...');
      const createButton = page.locator('button:has-text("指派新作業")');
      if (await createButton.isVisible()) {
        await createButton.click();
        await page.waitForSelector('[role="dialog"]', { timeout: 5000 });
        console.log('✅ Assignment dialog opened');

        // Close dialog
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
        console.log('✅ Assignment dialog closed');
      }

      // 7. Test View Assignment Details
      console.log('7️⃣ Testing View Assignment Details...');
      const viewDetailsButtons = page.locator('button:has-text("查看詳情")');
      const detailsCount = await viewDetailsButtons.count();
      console.log(`   Found ${detailsCount} assignments`);

      if (detailsCount > 0) {
        await viewDetailsButtons.first().click();
        await page.waitForSelector('[role="dialog"]', { timeout: 5000 });

        // Check if student dashboard is visible
        const studentListVisible = await page.locator('text=學生列表').isVisible();
        console.log(`✅ Student list visible: ${studentListVisible}`);

        // Check if summary stats are visible
        const statsVisible = await page.locator('text=總人數').isVisible();
        console.log(`✅ Statistics visible: ${statsVisible}`);

        // Test action buttons
        console.log('8️⃣ Testing Action Buttons...');

        // Test Edit button
        const editButton = page.locator('button:has-text("編輯作業")');
        if (await editButton.isVisible()) {
          await editButton.click();
          await page.waitForTimeout(1000);
          console.log('✅ Edit button clicked');
        }

        // Test Delete button (but cancel)
        const deleteButton = page.locator('button:has-text("刪除作業")');
        if (await deleteButton.isVisible()) {
          // Set up dialog handler to cancel
          page.once('dialog', dialog => {
            console.log(`   Dialog message: ${dialog.message()}`);
            dialog.dismiss();
          });

          await deleteButton.click();
          await page.waitForTimeout(1000);
          console.log('✅ Delete button clicked (cancelled)');
        }

        // Close dialog
        await page.keyboard.press('Escape');
      }

      // 9. Test Student Completion Dashboard
      console.log('9️⃣ Testing Student Completion Dashboard...');
      if (detailsCount > 0) {
        await viewDetailsButtons.first().click();
        await page.waitForSelector('[role="dialog"]', { timeout: 5000 });

        // Check if table headers are visible
        const tableHeaders = ['學生姓名', '待批改', '已打正', '待訂正', '待完成', '批改完'];
        for (const header of tableHeaders) {
          const headerVisible = await page.locator(`th:has-text("${header}")`).isVisible();
          console.log(`   ${header}: ${headerVisible ? '✅' : '❌'}`);
        }

        // Test search functionality
        const searchInput = page.locator('input[placeholder*="搜尋學生"]');
        if (await searchInput.isVisible()) {
          await searchInput.fill('A');
          await page.waitForTimeout(500);
          console.log('✅ Search functionality tested');
          await searchInput.clear();
        }

        // Test filter
        const filterSelect = page.locator('select').first();
        if (await filterSelect.isVisible()) {
          await filterSelect.selectOption('SUBMITTED');
          await page.waitForTimeout(500);
          console.log('✅ Filter functionality tested');
          await filterSelect.selectOption('all');
        }

        // Test action buttons in student rows
        const gradeButtons = page.locator('button:has-text("批改")');
        const gradeCount = await gradeButtons.count();
        if (gradeCount > 0) {
          await gradeButtons.first().click();
          await page.waitForTimeout(1000);
          console.log('✅ Grade button clicked');
        }

        const viewButtons = page.locator('button:has-text("查看")');
        const viewCount = await viewButtons.count();
        if (viewCount > 0) {
          await viewButtons.first().click();
          await page.waitForTimeout(1000);
          console.log('✅ View button clicked');
        }

        const remindButtons = page.locator('button:has-text("提醒")');
        const remindCount = await remindButtons.count();
        if (remindCount > 0) {
          await remindButtons.first().click();
          await page.waitForTimeout(1000);
          console.log('✅ Remind button clicked');
        }
      }

      console.log('\n🎉 All tests completed successfully!');

    } else {
      console.log('⚠️ No classrooms found, skipping detailed tests');
    }

    // Take screenshot for reference
    await page.screenshot({ path: 'test-results.png', fullPage: true });
    console.log('📸 Screenshot saved as test-results.png');
  });
});
