# PRD：背景非阻塞分析優化

## 文件資訊
- **建立日期**：2025-12-07
- **版本**：v1.0
- **狀態**：待實作

---

## 1. 問題陳述

### 1.1 現況
- **痛點**：學生提交作業時採用批次分析方式，導致：
  - 等待時間長達 70 秒（10 題 × 7 秒/題）
  - 多位學生同時提交時可能造成伺服器塞車
  - 用戶體驗差，需要長時間等待才能看到結果

### 1.2 目標
- 實作背景非阻塞分析機制，達成零等待體驗
- 學生錄完每題後立即切換到下一題，背景默默執行 AI 分析
- 提交時所有分析已完成，無需等待

---

## 2. 核心功能設計

### 2.1 主流程
```
學生錄完第 N 題
  → 點「下一題」
  → 立即切換到第 N+1 題（不等待）
  → 背景默默執行：上傳音檔 + AI 分析第 N 題
  → 分析完成後，悄悄更新 UI 狀態（顯示分數）
```

### 2.2 技術實作重點
- 使用非同步背景任務處理音檔上傳和 AI 分析
- 透過狀態管理追蹤每題的分析進度
- UI 即時反應分析狀態變化

---

## 3. 邊界情況處理

### 3.1 情況 1：學生不按下一題，直接點「上傳並分析」

**行為**：
- 顯示 loading spinner
- 阻塞式等待分析完成
- 分析完成後顯示結果

**原因**：
- 用戶主動要求分析，應該等待並顯示結果
- 符合用戶預期（點擊分析 → 看到結果）

**實作**：
- 保持原有邏輯（阻塞式分析）
- 顯示明確的 loading 狀態

---

### 3.2 情況 2：最後一題的處理

**場景**：
- 錄完最後一題，沒有「下一題」按鈕
- 需要決定何時觸發分析

**方案比較**：

| 方案 | 觸發時機 | 優點 | 缺點 |
|------|---------|------|------|
| A（推薦）| 錄完自動背景分析 | 用戶體驗最佳，提交時已完成 | 用戶可能未察覺分析進行中 |
| B | 等用戶點「上傳並分析」 | 保持原邏輯，行為一致 | 用戶仍需等待 |

**決策**：採用方案 A
- 錄完最後一題自動觸發背景分析
- 提交按鈕顯示分析進度（若尚未完成）

---

### 3.3 情況 3：切回前一題

**場景**：學生切換回已錄音的前幾題

**行為決策**：

| 該題狀態 | UI 顯示 |
|---------|---------|
| 正在背景分析中 | 顯示「分析中...」spinner |
| 已分析完成 | 顯示分數和分析結果 |
| 分析失敗 | 顯示「重新分析」按鈕 |
| 已錄音未分析 | 顯示「上傳並分析」按鈕 |

**實作**：
- 透過狀態判斷顯示對應 UI
- 允許用戶手動重新分析失敗項目

---

### 3.4 情況 4：提交時的殘餘分析

**場景**：用戶快速錄完所有題目，部分題目仍在背景分析中

**處理流程**：

```
用戶點擊「提交」
  ↓
檢查是否有「analyzing」狀態的項目
  ↓ 是
顯示「還有 X 題正在分析中，請稍候...」
  ↓
等待所有背景分析完成（Promise.all）
  ↓
檢查是否有失敗項目
  ↓ 是
自動重試失敗項目（最多 3 次）
  ↓
全部完成後提交
```

**錯誤處理**：
- 重試 3 次後仍失敗 → 顯示錯誤訊息，允許用戶選擇：
  - 跳過失敗項目繼續提交
  - 取消提交，手動重新分析

---

## 4. 狀態管理設計

### 4.1 項目狀態定義

```typescript
type ItemAnalysisStatus =
  | "not_recorded"     // 未錄音
  | "recorded"         // 已錄音，未分析
  | "analyzing"        // 分析中（背景）
  | "analyzed"         // 分析完成
  | "failed";          // 分析失敗

interface ItemState {
  status: ItemAnalysisStatus;
  recordingUrl?: string;      // 錄音檔 URL
  aiScores?: AiScores;        // AI 分析結果
  error?: string;             // 錯誤訊息
  retryCount?: number;        // 重試次數
}
```

### 4.2 背景任務管理

```typescript
// 用 Map 記錄所有背景分析 Promise
const pendingAnalysis = new Map<number, Promise<void>>();

// 分析失敗的項目列表
const failedItems = new Set<number>();

// 重試次數限制
const MAX_RETRY_COUNT = 3;
```

---

## 5. 實作重點

### 5.1 切題時觸發背景分析

```typescript
const handleNext = () => {
  const currentItem = items[currentIndex];

  // 如果當前題有錄音但未分析
  if (currentItem.recordingUrl && currentItem.status === "recorded") {
    // 🔥 背景分析（不阻塞）
    analyzeInBackground(currentIndex);
  }

  // 立即切到下一題
  setCurrentIndex(currentIndex + 1);
}
```

---

### 5.2 手動點擊「上傳並分析」

```typescript
const handleManualAnalyze = async () => {
  // 🔥 阻塞式分析（等待結果）
  setLoading(true);

  try {
    const result = await uploadAndAnalyze(currentItem.audio);
    updateItemScore(currentIndex, result);
    toast.success("分析完成！");
  } catch (error) {
    toast.error("分析失敗，請重試");
    updateItemStatus(currentIndex, "failed", error);
  } finally {
    setLoading(false);
  }
}
```

---

### 5.3 背景分析函數

```typescript
const analyzeInBackground = (itemIndex: number) => {
  // 更新狀態為「分析中」
  updateItemStatus(itemIndex, "analyzing");

  const promise = uploadAndAnalyze(items[itemIndex].audio)
    .then(result => {
      // 分析成功
      updateItemStatus(itemIndex, "analyzed", result);
      pendingAnalysis.delete(itemIndex);
    })
    .catch(error => {
      // 分析失敗
      console.error(`Item ${itemIndex} analysis failed:`, error);
      updateItemStatus(itemIndex, "failed", error);
      failedItems.add(itemIndex);
      pendingAnalysis.delete(itemIndex);
    });

  // 記錄 Promise 以便提交時等待
  pendingAnalysis.set(itemIndex, promise);
}
```

---

### 5.4 提交時處理

```typescript
const handleSubmit = async () => {
  try {
    // 1. 等待所有背景分析完成
    if (pendingAnalysis.size > 0) {
      toast.info(`還有 ${pendingAnalysis.size} 題正在分析中，請稍候...`);
      await Promise.all(Array.from(pendingAnalysis.values()));
    }

    // 2. 重試失敗項目
    if (failedItems.size > 0) {
      toast.info(`重試 ${failedItems.size} 題失敗項目...`);
      await retryFailedItems(Array.from(failedItems));
    }

    // 3. 檢查是否還有未分析項目
    const unanalyzedItems = items.filter(item =>
      item.recordingUrl && item.status !== "analyzed"
    );

    if (unanalyzedItems.length > 0) {
      toast.info(`分析剩餘 ${unanalyzedItems.length} 題...`);
      await batchAnalyze(unanalyzedItems);
    }

    // 4. 最終檢查：確保所有項目都已分析
    const hasUnanalyzed = items.some(item =>
      item.recordingUrl && item.status !== "analyzed"
    );

    if (hasUnanalyzed) {
      throw new Error("仍有項目未完成分析，無法提交");
    }

    // 5. 全部完成，提交作業
    await submitAssignment();
    toast.success("作業提交成功！");

  } catch (error) {
    console.error("Submit failed:", error);
    toast.error("提交失敗，請檢查所有題目是否已完成分析");
  }
}
```

---

### 5.5 失敗重試邏輯

```typescript
const retryFailedItems = async (itemIndices: number[]) => {
  const retryPromises = itemIndices.map(async (index) => {
    const item = items[index];

    // 檢查重試次數
    if ((item.retryCount || 0) >= MAX_RETRY_COUNT) {
      console.warn(`Item ${index} exceeded max retry count`);
      return;
    }

    try {
      const result = await uploadAndAnalyze(item.audio);
      updateItemStatus(index, "analyzed", result);
      failedItems.delete(index);
    } catch (error) {
      // 增加重試次數
      item.retryCount = (item.retryCount || 0) + 1;

      if (item.retryCount >= MAX_RETRY_COUNT) {
        console.error(`Item ${index} failed after ${MAX_RETRY_COUNT} retries`);
      }
    }
  });

  await Promise.allSettled(retryPromises);
}
```

---

## 6. UI/UX 設計

### 6.1 每題的狀態顯示

| 狀態 | 圖示 | 顏色 | 說明 |
|------|------|------|------|
| not_recorded | ○ | 灰色 | 未錄音 |
| recorded | ● | 藍色 | 已錄音未分析 |
| analyzing | ⟳ | 藍色 | 分析中（spinner） |
| analyzed | ✓ | 綠色 | 分析完成 + 分數 |
| failed | ! | 紅色 | 分析失敗 + 重試按鈕 |

### 6.2 提交按鈕邏輯

```typescript
// 提交按鈕狀態
const submitButtonState = useMemo(() => {
  const analyzingCount = items.filter(i => i.status === "analyzing").length;
  const failedCount = failedItems.size;

  if (analyzingCount > 0) {
    return {
      disabled: true,
      text: `分析中 (${analyzingCount} 題)...`,
      showSpinner: true
    };
  }

  if (failedCount > 0) {
    return {
      disabled: false,
      text: `提交作業 (${failedCount} 題失敗)`,
      showSpinner: false
    };
  }

  return {
    disabled: false,
    text: "提交作業",
    showSpinner: false
  };
}, [items, failedItems]);
```

### 6.3 分析進度提示

```typescript
// 頁面頂部顯示分析進度
const AnalysisProgress = () => {
  const analyzingCount = items.filter(i => i.status === "analyzing").length;

  if (analyzingCount === 0) return null;

  return (
    <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
      <div className="flex items-center">
        <Spinner className="mr-2" />
        <p className="text-sm text-blue-700">
          正在背景分析 {analyzingCount} 題，您可以繼續錄音...
        </p>
      </div>
    </div>
  );
}
```

---

## 7. 測試場景

### 7.1 測試案例清單

| # | 場景 | 預期行為 | 驗證重點 |
|---|------|---------|---------|
| 1 | 正常流程 | 錄 10 題 → 每題錄完切下一題 → 背景分析 → 提交 | 零等待，所有題目已分析 |
| 2 | 手動分析 | 錄完第 3 題 → 點「上傳並分析」→ 等待結果 → 切下一題 | 顯示 spinner，分析完成後顯示分數 |
| 3 | 最後一題 | 錄完第 10 題 → 自動背景分析 → 點提交 | 自動觸發分析，提交時已完成 |
| 4 | 切回前題 | 第 5 題 → 第 3 題（分析中）→ 顯示 spinner → 切回第 5 題 | 正確顯示分析中狀態 |
| 5 | 網路失敗 | 分析失敗 3 次 → 標記失敗 → 提交時重試 | 重試邏輯正確，最終成功或顯示錯誤 |
| 6 | 提交等待 | 還有 2 題分析中 → 顯示等待 → 完成後提交 | 等待所有分析完成，不阻塞提交 |
| 7 | 快速切題 | 快速錄完並切換 10 題 → 提交 | 所有背景任務正確執行 |
| 8 | 中途離開 | 錄完 5 題離開頁面 → 返回 | 狀態正確保存（若實作） |

---

## 8. 技術架構

### 8.1 狀態管理架構

```
Component State (useState)
  ├── items: ItemState[]          // 所有題目狀態
  ├── currentIndex: number        // 當前題目索引
  └── pendingAnalysis: Map        // 背景分析任務

Helper Functions
  ├── analyzeInBackground()       // 背景分析
  ├── handleManualAnalyze()       // 手動分析
  ├── retryFailedItems()          // 重試失敗項目
  └── handleSubmit()              // 提交處理
```

### 8.2 資料流

```
用戶錄音
  ↓
recordingUrl 存入 state
  ↓
status: "recorded"
  ↓
點擊「下一題」
  ↓
觸發 analyzeInBackground()
  ↓
status: "analyzing"
  ↓
API 呼叫 (非同步)
  ↓
成功 → status: "analyzed" + aiScores
失敗 → status: "failed" + error
```

---

## 9. 風險與限制

### 9.1 潛在風險

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| 網路不穩定導致分析失敗 | 用戶無法提交 | 自動重試 3 次 + 手動重試選項 |
| 用戶快速切題導致大量 API 請求 | 伺服器負載增加 | 實作請求節流（throttle） |
| 背景分析時用戶關閉頁面 | 分析結果遺失 | 考慮本地儲存狀態（未來優化） |
| 分析時間過長 | 提交時仍需等待 | 顯示進度條，提升用戶體驗 |

### 9.2 限制

- 不支援離線模式（需要網路連線）
- 背景分析不保證即時完成（取決於 API 速度）
- 最大重試次數為 3 次（避免無限重試）

---

## 10. 成功指標

### 10.1 量化指標

| 指標 | 現況 | 目標 | 測量方式 |
|------|------|------|---------|
| 提交等待時間 | 70 秒 | < 5 秒 | 計時器測量 |
| 用戶感知等待 | 70 秒 | 0 秒 | 錄完即可切題 |
| 分析成功率 | 95% | 98% | 錯誤日誌統計 |
| API 請求分散度 | 集中提交時 | 均勻分散 | 伺服器日誌分析 |

### 10.2 質化指標

- 用戶反饋：「提交速度變快」
- 伺服器負載：「高峰期不再塞車」
- 開發維護：「程式碼邏輯清晰，易於維護」

---

## 11. 實作計畫

### 11.1 開發階段

| 階段 | 任務 | 預估時間 |
|------|------|---------|
| Phase 1 | 建立狀態管理架構 | 2 小時 |
| Phase 2 | 實作背景分析邏輯 | 3 小時 |
| Phase 3 | 實作 UI 狀態顯示 | 2 小時 |
| Phase 4 | 實作提交處理邏輯 | 2 小時 |
| Phase 5 | 錯誤處理與重試 | 2 小時 |
| Phase 6 | 測試與除錯 | 3 小時 |

**總計**：14 小時

### 11.2 測試階段

- 單元測試：各函數邏輯正確性
- 整合測試：完整流程測試
- 壓力測試：多用戶同時使用
- 用戶驗收測試：真實用戶體驗

---

## 12. 附錄

### 12.1 相關檔案

- `frontend/src/pages/student/StudentActivityPageContent.tsx`
- `frontend/src/components/activities/ReadingAssessmentTemplate.tsx`
- `frontend/src/components/activities/GroupedQuestionsTemplate.tsx`

### 12.2 參考資料

- React 非同步狀態管理最佳實踐
- Promise.all / Promise.allSettled 使用指南
- 用戶體驗設計：非阻塞式操作

---

**文件結束**
