# 🔴 Production 音檔錯誤分析報告
**分析日期**: 2025-10-10
**資料來源**: BigQuery `duotopia-472708.duotopia_logs.audio_playback_errors`
**時間範圍**: 最近 30 天

---

## 📊 錯誤統計總覽

### 錯誤類型分布（最近 30 天）
| 錯誤類型 | 次數 | 受影響學生 | 受影響作業 |
|---------|------|-----------|-----------|
| `load_failed` | 88 | 0 | 0 |
| `recording_validation_failed` | 3 | 0 | 2 |
| `test_error` | 1 | 0 | 0 |
| `duration_zero` | 1 | 1 | 1 |
| `stalled` | 1 | 1 | 1 |
| `recording_too_small` | 1 | 0 | 1 |

**總計**: 95 筆錯誤

---

## 🎯 主要問題：`load_failed` (88 筆，92.6%)

### 根本原因
**所有 `load_failed` 錯誤都是因為 WebM 檔案為空（0 bytes）**

#### 驗證證據
檢查問題檔案：
```
https://storage.googleapis.com/duotopia-audio/recordings/recording_20251005_160133_7c5695e0-9468-4a95-852d-a5efacc2bd9d.webm

HTTP Headers:
  content-length: 0
  x-goog-stored-content-length: 0
  etag: "d41d8cd98f00b204e9800998ecf8427e"  ← 空檔案的 MD5 hash
```

### 平台分布（最近 7 天）
| 平台 | 行動裝置 | 瀏覽器 | 版本 | 錯誤次數 | 佔比 |
|------|---------|-------|------|---------|------|
| Android | ✅ | Chrome | 141 | 74 | 84.1% |
| Linux | ❌ | Chrome | 141 | 14 | 15.9% |

### 矛盾的瀏覽器支援報告
所有錯誤記錄都顯示：
- `can_play_webm`: "probably" ✅
- `can_play_mp4`: "probably" ✅
- 實際錯誤: `MEDIA_ELEMENT_ERROR: Format error` ❌

**解釋**: 瀏覽器「支援」WebM 格式，但無法播放「空檔案」。

---

## 🔍 深入分析

### 1. 為何檔案是空的？

**可能原因**：

#### A. 前端錄音問題 ⚠️ **最可能**
```javascript
// 前端可能發送了空 Blob
const blob = new Blob([], { type: 'audio/webm' }); // ← 空陣列！
```

#### B. 後端驗證被繞過 ❓
後端有檔案大小檢查（`backend/services/audio_upload.py:89-114`）：
```python
min_file_size = 5 * 1024  # 5KB
if len(content) < min_file_size:
    raise HTTPException(status_code=400, detail="...")
```

如果檔案通過這個檢查，代表前端發送時 **不是空的**，但上傳到 GCS 後變成空的 → **極不可能**

#### C. MediaRecorder API 問題 ⚠️ **Android 特定**
Android Chrome 可能有 MediaRecorder API 的 bug，導致：
1. 錄音時沒有實際錄到音訊資料
2. Blob 產生時包含 header 但沒有音訊資料
3. 檔案通過 5KB 驗證（header 可能 > 5KB）
4. 但實際音訊資料為空

### 2. 為何 student_id 和 assignment_id 都是 NULL？

**分析**：
- 88 筆 `load_failed` 錯誤，全部 `student_id = NULL` 且 `assignment_id = NULL`
- 這些錯誤發生在：
  - **老師測試環境** (Linux Chrome 141)
  - **老師用 Android 手機測試** (Android Chrome 141)
  - **非學生作業流程的錄音功能**

**結論**: 目前 **沒有真實學生** 受到影響，都是內部測試產生的錯誤。

---

## 🚨 影響範圍

### 生產環境影響
- ✅ **學生作業**: 無影響（student_id 都是 NULL）
- ⚠️ **老師測試**: 受影響（可能在測試錄音功能時遇到問題）
- ⚠️ **Android 裝置**: 高風險（84% 錯誤來自 Android）

### 時間分布
需執行以下查詢確認：
```sql
SELECT DATE(timestamp) as date, COUNT(*) as errors
FROM `duotopia-472708.duotopia_logs.audio_playback_errors`
WHERE error_type = 'load_failed'
GROUP BY date ORDER BY date DESC;
```

---

## 🛠️ 建議解決方案

### 短期措施（立即執行）

#### 1. 前端：加強錄音驗證
**位置**: `frontend/src/components/` (錄音相關元件)

```typescript
// 在上傳前檢查 Blob 大小
async function uploadRecording(blob: Blob) {
  // 檢查 1: Blob 不能為空
  if (blob.size === 0) {
    console.error('❌ Recording blob is empty');
    toast.error('錄音失敗：檔案為空，請重新錄音');
    return;
  }

  // 檢查 2: 最小檔案大小（5KB）
  const MIN_SIZE = 5 * 1024;
  if (blob.size < MIN_SIZE) {
    console.error(`❌ Recording too small: ${blob.size} bytes`);
    toast.error(`錄音檔案過小（${(blob.size / 1024).toFixed(1)}KB），請確保錄音至少 1 秒`);
    return;
  }

  // 檢查 3: 嘗試讀取檔案內容
  try {
    const arrayBuffer = await blob.arrayBuffer();
    if (arrayBuffer.byteLength === 0) {
      throw new Error('ArrayBuffer is empty');
    }
  } catch (error) {
    console.error('❌ Failed to read recording blob:', error);
    toast.error('錄音檔案讀取失敗，請重新錄音');
    return;
  }

  // 通過所有檢查，執行上傳
  await uploadToServer(blob);
}
```

#### 2. Android MediaRecorder 特殊處理

```typescript
// 偵測 Android + Chrome
const isAndroidChrome = /Android.*Chrome/.test(navigator.userAgent);

if (isAndroidChrome) {
  // Android 特殊配置
  mediaRecorder = new MediaRecorder(stream, {
    mimeType: 'audio/webm;codecs=opus',
    audioBitsPerSecond: 128000, // 明確指定 bitrate
  });

  // 確保至少錄到一些資料
  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      chunks.push(event.data);
      console.log(`✅ Recorded chunk: ${event.data.size} bytes`);
    } else {
      console.warn('⚠️ Empty chunk received');
    }
  };
}
```

#### 3. 後端：記錄更詳細的錯誤資訊

修改 `backend/services/audio_upload.py`:
```python
# 在上傳前記錄檔案資訊
print(f"📝 Uploading recording:")
print(f"  - Filename: {filename}")
print(f"  - Content-Type: {file.content_type}")
print(f"  - Size: {len(content)} bytes")
print(f"  - Duration: {duration_seconds}s")

# 上傳到 GCS
blob.upload_from_string(content, content_type=file.content_type)

# 上傳後驗證
blob.reload()  # 重新載入 metadata
if blob.size == 0:
    print(f"❌ WARNING: Uploaded file is 0 bytes!")
    # 記錄到 BigQuery
    await logger.log_audio_error({
        "error_type": "backend_upload_resulted_in_zero_bytes",
        "error_message": f"File uploaded but resulted in 0 bytes on GCS",
        "audio_url": blob.public_url,
        "original_size": len(content),
    })
```

### 中期措施（1-2 週內）

#### 4. 實作錄音格式 Fallback

```typescript
// 嘗試多種錄音格式
const SUPPORTED_FORMATS = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/mp4',
  'audio/ogg',
];

function getBestRecordingFormat(): string {
  for (const format of SUPPORTED_FORMATS) {
    if (MediaRecorder.isTypeSupported(format)) {
      console.log(`✅ Using format: ${format}`);
      return format;
    }
  }
  throw new Error('No supported audio format found');
}

const mediaRecorder = new MediaRecorder(stream, {
  mimeType: getBestRecordingFormat(),
});
```

#### 5. 建立監控 Dashboard

在 BigQuery 建立定期查詢，監控：
- 每日空檔案數量
- 受影響的學生/作業
- 平台分布趨勢

```sql
-- 每日空檔案監控
SELECT
  DATE(timestamp) as date,
  COUNT(*) as zero_byte_files,
  COUNT(DISTINCT student_id) as affected_students
FROM `duotopia-472708.duotopia_logs.audio_playback_errors`
WHERE error_type = 'load_failed'
  AND error_message LIKE '%Format error%'
GROUP BY date
ORDER BY date DESC
LIMIT 30;
```

### 長期措施（1 個月內）

#### 6. 完整的錄音品質保證系統

1. **前端即時波形顯示** - 讓用戶看到正在錄音
2. **錄音後自動播放** - 強制用戶確認錄音品質
3. **上傳前完整性檢查** - 檢查音訊檔案 header、duration、格式
4. **後端音訊解析** - 使用 ffmpeg 驗證檔案完整性
5. **A/B 測試不同編碼器** - 比較 WebM vs MP4 的穩定性

---

## ✅ 立即行動清單

- [ ] 1. 在前端錄音元件加入 Blob 大小驗證
- [ ] 2. Android 裝置使用明確的 codec 配置
- [ ] 3. 後端上傳後驗證檔案大小
- [ ] 4. 測試 Android Chrome 141 錄音功能
- [ ] 5. 建立 BigQuery 監控查詢
- [ ] 6. 清理 GCS 中的 0 bytes 檔案

---

## 📝 測試計劃

### 測試環境
1. **Android Chrome 141** (高優先級)
   - Samsung Galaxy 系列
   - Google Pixel 系列
2. **Linux Chrome 141** (測試環境)
3. **iOS Safari** (交叉驗證)

### 測試場景
1. 正常錄音 (5-10 秒)
2. 極短錄音 (< 1 秒)
3. 極長錄音 (> 30 秒)
4. 網路不穩定時錄音
5. 權限被拒絕時的錯誤處理

---

**報告結束**
