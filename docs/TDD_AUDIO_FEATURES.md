# TDD - Audio Features Test Specification
# 音檔功能測試規範文檔

## 測試環境配置

### 前置條件
```bash
# 1. 確保環境變數設定
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export OPENAI_API_KEY=your-openai-key
export GCS_BUCKET_NAME=duotopia-audio

# 2. 啟動本地開發環境
docker-compose up -d  # PostgreSQL
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

## 功能測試清單

### 1. TTS (Text-to-Speech) 功能測試

#### 1.1 生成 TTS 音檔
**測試步驟：**
1. 登入教師帳號
2. 進入班級詳情頁面
3. 選擇朗讀評測內容
4. 點擊「音效設定」
5. 輸入文字或使用現有文字
6. 選擇口音、性別、語速
7. 點擊「Generate」按鈕

**預期結果：**
- ✅ 顯示「Generating...」載入狀態
- ✅ 生成成功後顯示播放按鈕
- ✅ 點擊播放可聽到生成的語音
- ✅ 音檔儲存至 GCS

**驗證點：**
```javascript
// 檢查 API 回應
expect(response.audio_url).toContain('https://storage.googleapis.com/');
expect(response.audio_url).toContain('.mp3');
```

#### 1.2 批次生成 TTS
**測試步驟：**
1. 在內容編輯面板中
2. 點擊「批次生成TTS」
3. 選擇設定（口音、性別、語速）
4. 確認批次生成

**預期結果：**
- ✅ 所有項目顯示生成中狀態
- ✅ 逐一完成生成
- ✅ 每個項目都有獨立音檔
- ✅ Panel 不會自動關閉

### 2. 錄音功能測試

#### 2.1 錄製音檔
**測試步驟：**
1. 點擊「音效設定」
2. 切換到「Recording」標籤
3. 點擊「開始錄音」
4. 說話 3-5 秒
5. 點擊「停止錄音」

**預期結果：**
- ✅ 顯示錄音計時器
- ✅ 錄音完成顯示播放按鈕
- ✅ 顯示錄音長度
- ✅ 可以試聽錄音
- ✅ 不會立即上傳（等待確認）

**驗證點：**
```javascript
// 檢查錄音 Blob
expect(audioBlob.size).toBeGreaterThan(0);
expect(audioBlob.size).toBeLessThan(2 * 1024 * 1024); // < 2MB
expect(audioBlob.type).toBe('audio/webm');
```

#### 2.2 錄音上傳
**測試步驟：**
1. 完成錄音後
2. 試聽確認無誤
3. 點擊「Confirm」按鈕

**預期結果：**
- ✅ 顯示上傳中狀態
- ✅ 上傳成功返回 GCS URL
- ✅ 更新內容的音檔 URL
- ✅ Panel 關閉

**驗證點：**
```python
# 後端驗證
assert file.content_type in ['audio/webm', 'video/webm']
assert len(content) <= 2 * 1024 * 1024  # 2MB 限制
assert duration <= 30  # 30秒限制
```

#### 2.3 錄音限制測試
**測試場景：**
- 錄音超過 30 秒自動停止
- 檔案大於 2MB 拒絕上傳
- 無麥克風權限顯示錯誤

### 3. 音源切換測試

#### 3.1 雙音源選擇
**測試步驟：**
1. 先生成 TTS
2. 再錄製音檔
3. 應顯示音源選擇界面
4. 選擇其中一個音源
5. 點擊 Confirm

**預期結果：**
- ✅ 顯示兩個音源選項（TTS/Recording）
- ✅ 選中的音源有視覺提示
- ✅ 未選擇時 Confirm 顯示警告
- ✅ 選擇後正確保存對應音源

### 4. 音檔持久化測試

#### 4.1 重新整理測試
**測試步驟：**
1. 生成或上傳音檔
2. Confirm 保存
3. 重新整理頁面
4. 重新進入相同內容

**預期結果：**
- ✅ 音檔 URL 正確保存
- ✅ 可以播放之前的音檔
- ✅ GCS URL 持續有效

### 5. 錯誤處理測試

#### 5.1 網路錯誤
- TTS 生成失敗顯示錯誤提示
- 上傳失敗顯示重試選項
- GCS 不可用時 fallback 到本地

#### 5.2 權限錯誤
- 無麥克風權限顯示提示
- Token 過期自動重新登入

## API 端點測試

### TTS API
```bash
POST /api/teachers/content/{content_id}/tts
{
  "text": "Hello World",
  "voice": "en-US-JennyNeural",
  "rate": "+0%",
  "volume": "+0%"
}

# 預期回應
{
  "audio_url": "https://storage.googleapis.com/duotopia-audio/tts/..."
}
```

### Upload API
```bash
POST /api/teachers/upload/audio
Content-Type: multipart/form-data
- file: audio.webm
- duration: 5
- content_id: 123
- item_index: 0

# 預期回應
{
  "audio_url": "https://storage.googleapis.com/duotopia-audio/recordings/..."
}
```

## 效能基準

| 操作 | 預期時間 | 最大時間 |
|-----|---------|---------|
| TTS 生成（單句） | < 2s | 5s |
| TTS 批次生成（5句） | < 5s | 10s |
| 錄音上傳（30秒） | < 3s | 8s |
| 音檔播放載入 | < 500ms | 2s |

## 瀏覽器相容性

### 支援的瀏覽器
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### MediaRecorder 支援
```javascript
// 支援的 MIME types（按優先順序）
const supportedTypes = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/ogg',
  'audio/mp4'
];
```

## 資料驗證

### Content 資料結構
```typescript
interface ContentItem {
  text: string;
  translation?: string;
  audioUrl?: string;
  audioSettings?: {
    accent: string;
    gender: string;
    speed: string;
    source: 'tts' | 'recording';
  };
}
```

### 檔案命名規則
- TTS: `tts_YYYYMMDD_HHMMSS_[uuid].mp3`
- Recording: `recording_c[content_id]_i[item_index]_YYYYMMDD_HHMMSS_[uuid].webm`

## 安全性檢查

- [x] 檔案大小限制（2MB）
- [x] 錄音時長限制（30秒）
- [x] MIME type 白名單
- [x] JWT token 驗證
- [x] Content-ID 權限檢查
- [x] GCS 公開讀取設定

## 測試執行命令

```bash
# 前端單元測試
npm run test

# 後端單元測試
cd backend && python -m pytest tests/

# E2E 測試
npx playwright test tests/audio-e2e.spec.ts

# 手動測試腳本
python backend/scripts/test/test_audio_all.py
```

## 已知問題與解決方案

### 問題 1: MIME type 不匹配
**問題：** `audio/webm;codecs=opus` vs `audio/webm`
**解決：** 前端移除 codec 信息，只傳送基本 MIME type

### 問題 2: 錄音無聲
**問題：** MediaRecorder 未正確捕獲音頻
**解決：** 使用 `timeslice` 參數定期收集數據

### 問題 3: Duration 顯示 Infinity
**問題：** WebM 格式的 duration metadata 問題
**解決：** 手動追蹤錄音時長

## 測試覆蓋率目標

- 單元測試覆蓋率: > 80%
- E2E 關鍵路徑: 100%
- API 端點測試: 100%

---

最後更新：2024-08-30
測試負責人：@Claude