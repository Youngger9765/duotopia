# 作業系統設計風險評估報告

## 🔴 高風險問題

### 1. **JSONB 陣列索引同步問題** ⚠️
**問題描述**：
- 所有 Items 的資料（recordings、answers、ai_assessments）都依賴陣列索引對應
- 如果任何一個陣列長度不一致，會造成資料錯位

**風險場景**：
```json
{
  "items": [item0, item1, item2, item3, item4],  // 5題
  "recordings": [audio0, audio1, audio2],         // 只有3個錄音
  "ai_assessments": [null, score1, score2, score3, score4]  // 5個但錯位
}
```

**影響**：
- AI 評分顯示在錯誤的題目上（已經發生過）
- 錄音和題目對不上
- 難以追蹤和除錯

**建議解決方案**：
```json
// 改為物件結構，使用明確的 key
{
  "responses": {
    "0": {
      "recording": "audio0.webm",
      "answer": "I am a student",
      "ai_assessment": { "score": 85.5 }
    },
    "1": {
      "recording": null,
      "answer": null,
      "ai_assessment": null
    }
  }
}
```

### 2. **Content 變更的連鎖反應** 🔄
**問題描述**：
- 如果老師修改了 Content 的 items（增加/刪除/重排序題目）
- 已經存在的 StudentContentProgress 資料會對不上

**風險場景**：
1. 老師創建作業，5個題目
2. 學生開始答題，錄了3題
3. 老師發現錯誤，刪除第2題
4. 學生的第3題錄音現在對應到新的第2題

**影響**：
- 學生已完成的答案錯位
- AI 評分失效
- 學習進度混亂

**建議解決方案**：
- Content 應該要有版本控制
- 或者一旦有學生開始作答，就不允許修改

### 3. **order_index 維護困難** 📊
**問題描述**：
- 依賴 order_index 來對應 Content
- 手動維護容易出錯

**風險場景**：
```sql
-- 如果刪除中間的 content，order_index 會斷層
DELETE FROM student_content_progress WHERE order_index = 1;
-- 現在有 order_index: 0, 2, 3 (缺少 1)
```

**建議解決方案**：
- 使用資料庫觸發器自動維護
- 或改為直接關聯 content_id + item_index

## 🟡 中風險問題

### 4. **批量操作效能問題** 🐌
**問題描述**：
- 每個學生、每個作業都要創建多個 StudentContentProgress 記錄
- 班級 30 人 × 作業 10 題 = 300 筆記錄

**影響**：
- 資料庫寫入壓力大
- 查詢效能下降
- 備份還原耗時

**建議優化**：
```sql
-- 考慮使用批量插入
INSERT INTO student_content_progress
SELECT ... FROM generate_series(1, 30) -- 批量創建
```

### 5. **狀態管理複雜** 🔄
**問題描述**：
- StudentAssignment 有狀態
- StudentContentProgress 也有狀態
- 兩者可能不同步

**風險場景**：
- StudentAssignment: SUBMITTED
- StudentContentProgress: 部分還是 IN_PROGRESS

**建議解決方案**：
- 使用事務確保狀態同步
- 或只在一處維護狀態

### 6. **資料完整性風險** 🔐
**問題描述**：
- response_data 是 JSONB，沒有 schema 驗證
- 容易存入錯誤格式的資料

**建議解決方案**：
```sql
-- 加入 CHECK 約束
ALTER TABLE student_content_progress
ADD CONSTRAINT check_response_format
CHECK (
  response_data ? 'recordings' AND
  jsonb_typeof(response_data->'recordings') = 'array'
);
```

## 🟢 低風險但需注意

### 7. **擴展性限制** 📈
- 目前設計假設所有題目都是同類型
- 如果要加入不同題型（選擇題、填空題），會很困難

### 8. **備份還原複雜度** 💾
- 資料分散在多個表格
- 部分還原（如只還原某個學生）很困難

### 9. **稽核追蹤不足** 📝
- 沒有記錄誰在何時修改了什麼
- 難以追查問題來源

## 📊 風險矩陣

| 問題 | 發生機率 | 影響程度 | 風險等級 | 優先處理 |
|------|---------|---------|---------|---------|
| JSONB 陣列同步 | 高 | 高 | 🔴 嚴重 | 立即 |
| Content 變更連鎖 | 中 | 高 | 🔴 嚴重 | 立即 |
| order_index 維護 | 中 | 中 | 🟡 中等 | 短期 |
| 批量操作效能 | 低 | 中 | 🟡 中等 | 中期 |
| 狀態管理 | 中 | 低 | 🟢 低 | 長期 |

## 🛠️ 建議改進方案

### 短期（1-2 週）
1. **加入資料驗證**
   - API 層驗證 JSONB 格式
   - 資料庫加入 CHECK 約束
   - 前端加入資料一致性檢查

2. **防止 Content 修改**
   ```python
   if StudentContentProgress.query.filter_by(content_id=content.id).exists():
       raise Exception("Cannot modify content with existing student progress")
   ```

### 中期（1-2 月）
1. **重構 response_data 結構**
   - 從陣列改為物件，使用明確的 key
   - 寫資料遷移腳本
   - 更新前後端邏輯

2. **加入版本控制**
   - Content 增加 version 欄位
   - 學生答題時鎖定版本

### 長期（3-6 月）
1. **重新設計資料模型**
   - 考慮將每個 Item 獨立成表格
   - 使用更正規化的關聯式設計
   - 評估 NoSQL 的可行性

2. **加入事件溯源（Event Sourcing）**
   - 記錄所有操作歷史
   - 可以回溯任何時間點的狀態

## 💡 結論

目前的設計可以運作，但有幾個高風險點需要立即處理：

1. **最緊急**：JSONB 陣列同步問題（已經造成 bug）
2. **次緊急**：防止 Content 修改造成的資料錯亂
3. **重要不緊急**：效能優化和資料模型重構

建議優先處理前兩項，可以大幅降低系統出錯的機率。
