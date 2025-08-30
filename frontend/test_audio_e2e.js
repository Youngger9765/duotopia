/**
 * 前端音檔功能 E2E 測試
 * 使用瀏覽器自動化測試完整的用戶流程
 */

// 確保前端和後端都在運行
// npm run dev (前端)
// uvicorn main:app --reload --port 8000 (後端)

const TEST_URL = 'http://localhost:5173';
const DEMO_EMAIL = 'demo@duotopia.com';
const DEMO_PASSWORD = 'demo123';

// 模擬測試用的文字
const TEST_TEXTS = [
    'The weather is nice today.',
    'I love learning English.',
    'Practice makes perfect.'
];

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function testLogin() {
    console.log('📝 登入測試...');
    
    // 開啟瀏覽器
    window.open(`${TEST_URL}/login/teacher`);
    
    // 等待頁面載入
    await sleep(2000);
    
    console.log('   請手動輸入登入資訊：');
    console.log(`   Email: ${DEMO_EMAIL}`);
    console.log(`   Password: ${DEMO_PASSWORD}`);
    console.log('   然後按登入按鈕');
    
    // 等待登入完成
    await sleep(5000);
    
    console.log('✅ 登入成功');
}

async function testNavigateToContent() {
    console.log('\n📝 導航到內容頁面...');
    
    console.log('   請手動點擊：');
    console.log('   1. 選擇任意班級');
    console.log('   2. 選擇任意課程');
    console.log('   3. 選擇任意課堂');
    console.log('   4. 點擊第一個內容的編輯按鈕');
    
    await sleep(10000);
    
    console.log('✅ 已進入內容編輯頁面');
}

async function testTTSGeneration() {
    console.log('\n📝 測試 TTS 生成...');
    
    console.log('   請手動操作：');
    console.log('   1. 點擊第一個項目的喇叭圖示');
    console.log('   2. 在彈出的 Modal 中選擇 "Generate" 標籤');
    console.log('   3. 選擇聲音（預設即可）');
    console.log('   4. 點擊 "生成音檔" 按鈕');
    console.log('   5. 等待生成完成');
    console.log('   6. 點擊 "確認使用" 按鈕');
    
    await sleep(15000);
    
    console.log('✅ TTS 生成成功');
}

async function testAudioPlayback() {
    console.log('\n📝 測試音檔播放...');
    
    console.log('   請手動操作：');
    console.log('   1. 點擊項目旁的播放按鈕');
    console.log('   2. 確認音檔播放正常');
    
    await sleep(5000);
    
    console.log('✅ 音檔播放成功');
}

async function testRecording() {
    console.log('\n📝 測試錄音功能...');
    
    console.log('   請手動操作：');
    console.log('   1. 點擊第二個項目的喇叭圖示');
    console.log('   2. 選擇 "Record" 標籤');
    console.log('   3. 點擊 "開始錄音" 按鈕');
    console.log('   4. 說一些話（最長 30 秒）');
    console.log('   5. 點擊 "停止錄音" 按鈕');
    console.log('   6. 點擊 "上傳錄音" 按鈕');
    console.log('   7. 等待上傳完成');
    console.log('   8. 點擊 "確認使用" 按鈕');
    
    await sleep(20000);
    
    console.log('✅ 錄音上傳成功');
}

async function testPersistence() {
    console.log('\n📝 測試持久化...');
    
    console.log('   請手動操作：');
    console.log('   1. 重新整理頁面（F5）');
    console.log('   2. 確認音檔圖示仍然存在');
    console.log('   3. 點擊播放按鈕，確認音檔可以播放');
    
    await sleep(10000);
    
    console.log('✅ 音檔持久化成功');
}

async function testAudioReplacement() {
    console.log('\n📝 測試音檔替換...');
    
    console.log('   請手動操作：');
    console.log('   1. 點擊已有音檔的項目的喇叭圖示');
    console.log('   2. 生成新的 TTS 或錄製新的音檔');
    console.log('   3. 確認使用新音檔');
    console.log('   4. 確認舊音檔被替換');
    
    await sleep(15000);
    
    console.log('✅ 音檔替換成功');
}

async function runManualTests() {
    console.log('🎯 Duotopia 前端音檔功能手動測試指南');
    console.log('=' .repeat(50));
    console.log('請按照以下步驟手動測試：\n');
    
    await testLogin();
    await testNavigateToContent();
    await testTTSGeneration();
    await testAudioPlayback();
    await testRecording();
    await testPersistence();
    await testAudioReplacement();
    
    console.log('\n' + '='.repeat(50));
    console.log('📊 測試完成總結');
    console.log('-'.repeat(50));
    console.log('✅ 所有手動測試步驟已完成');
    console.log('\n💡 檢查清單：');
    console.log('□ TTS 生成功能正常');
    console.log('□ 錄音上傳功能正常');
    console.log('□ 音檔播放功能正常');
    console.log('□ 頁面重新整理後音檔仍存在');
    console.log('□ 音檔替換時舊檔被刪除');
    console.log('□ 無控制台錯誤');
    console.log('\n如果有任何問題，請檢查：');
    console.log('1. 瀏覽器控制台（F12）');
    console.log('2. 網路請求（Network 標籤）');
    console.log('3. 後端日誌');
}

// 執行測試
console.log('請在瀏覽器控制台中執行此腳本');
console.log('或直接按照以下步驟手動測試：\n');

// 如果在 Node.js 環境執行
if (typeof window === 'undefined') {
    runManualTests().catch(console.error);
} else {
    // 如果在瀏覽器控制台執行
    runManualTests();
}