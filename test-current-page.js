const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('Opening courses page...');
  await page.goto('http://localhost:5173/individual/courses');
  
  // Take screenshot
  await page.screenshot({ path: 'current-page-state.png', fullPage: true });
  console.log('Screenshot saved as current-page-state.png');
  
  // Check for errors in console
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Console error:', msg.text());
    }
  });
  
  // Wait for user to see the page
  console.log('Page is open. Check for errors in the browser console.');
  console.log('Press Ctrl+C to close...');
  
  // Keep browser open
  await new Promise(() => {});
})();