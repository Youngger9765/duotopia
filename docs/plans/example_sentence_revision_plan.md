# 例句功能修正計劃

> **建立日期**: 2025-11-10
> **狀態**: 待確認

---

## 📋 問題分析

### ❌ 原始錯誤實作
- **朗讀錄音（reading_assessment）**：錯誤地加入了例句功能
  - 問題：這裡輸入的本身就是完整句子，不需要再提供例句

### ✅ 正確需求
- **造句練習（sentence_making）**：應該在這裡實作例句功能
  - 原因：這裡輸入的是單字，需要例句來展示單字的用法

---

## 🎯 資料結構分析

### 現有 content_items 表結構

```sql
content_items
├── id (INTEGER, NOT NULL)
├── content_id (INTEGER, NOT NULL)
├── order_index (INTEGER, NOT NULL)
├── text (TEXT, NOT NULL)              -- 單字或句子
├── translation (TEXT, NULL)            -- 翻譯
├── audio_url (TEXT, NULL)              -- 音檔 URL
├── item_metadata (JSON, NULL)          -- 其他資料
├── created_at (TIMESTAMP, NULL)
├── updated_at (TIMESTAMP, NULL)
├── example_sentence (TEXT, NULL)       -- ✅ 已新增
├── example_sentence_translation (TEXT, NULL)  -- ✅ 已新增
└── example_sentence_definition (TEXT, NULL)   -- ✅ 已新增
```

### 📊 資料結構決策

**✅ 建議：沿用現有 content_items 表**

**理由**：
1. ✅ **架構一致性**：content_items 本來就是設計來儲存不同類型內容的 items
2. ✅ **避免重複**：text, translation, audio_url 等欄位可共用
3. ✅ **彈性使用**：不同 content_type 可選擇性使用不同欄位
4. ✅ **已完成 Migration**：例句欄位已經存在，不需要額外建表

**欄位使用規劃**：

| Content Type | text | translation | audio_url | example_sentence | example_sentence_translation | example_sentence_definition |
|--------------|------|-------------|-----------|------------------|------------------------------|------------------------------|
| **reading_assessment** | 完整句子 | 句子翻譯 | ✓ | ❌ 不使用 | ❌ 不使用 | ❌ 不使用 |
| **sentence_making** | 單字 | 單字翻譯 | ✓ | ✅ 例句 | ✅ 例句中文 | ✅ 例句英文 |

---

## 🔄 Phase 1: Revert 朗讀錄音的例句功能

### 1.1 前端 ReadingAssessmentPanel.tsx

**移除內容**：
```typescript
// ❌ 移除：例句輸入區塊（Lines 974-1019）
{/* Example sentence fields - Phase 1 */}
<div className="space-y-2 pt-2 border-t border-gray-200">
  <div className="text-xs font-medium text-gray-500 mb-1">例句（選填）</div>
  <input ... example_sentence ... />
  <input ... example_sentence_translation ... />
  <input ... example_sentence_definition ... />
  <button onClick={handleGenerateExampleTranslation} ... />
</div>
```

**移除函數**：
```typescript
// ❌ 移除：Lines 1632-1663
const handleGenerateExampleTranslation = async (index: number) => { ... }

// ❌ 移除：Lines 1665-1734
const handleBatchGenerateExampleTranslations = async () => { ... }
```

**移除按鈕**：
```typescript
// ❌ 移除：Lines 1925-1934
<Button onClick={handleBatchGenerateExampleTranslations}>
  批次生成例句翻譯
</Button>
```

**移除 Props**：
```typescript
// ❌ 移除：Line 804
handleGenerateExampleTranslation: (index: number) => Promise<void>;

// ❌ 移除：Line 818
handleGenerateExampleTranslation,

// ❌ 移除：Lines 1994-1996
handleGenerateExampleTranslation={handleGenerateExampleTranslation}
```

**保留但調整欄位初始化**：
```typescript
// ✅ 保留初始化，但設為空值（資料庫需要這些欄位）
const [rows, setRows] = useState<ContentRow[]>([
  {
    id: "1",
    text: "",
    definition: "",
    translation: "",
    selectedLanguage: "chinese",
    // 保留但不在 UI 中顯示
    example_sentence: "",
    example_sentence_translation: "",
    example_sentence_definition: "",
  },
  // ...
]);
```

### 1.2 前端 GroupedQuestionsTemplate.tsx

**移除內容**：
```typescript
// ❌ 移除：Lines 778-798
{/* 例句 - Phase 1 */}
{currentQuestion?.example_sentence && (
  <div className="space-y-2 border-t border-gray-200 pt-3 mt-3">
    ...
  </div>
)}
```

**保留 Interface**：
```typescript
// ✅ 保留（因為資料庫有這些欄位）
interface Question {
  // ...
  example_sentence?: string;
  example_sentence_translation?: string;
  example_sentence_definition?: string;
}
```

### 1.3 資料載入/儲存

**✅ 保留**：loadContentData 和儲存邏輯中的例句欄位處理
- 原因：即使 UI 不顯示，資料庫欄位還是存在
- 避免在切換回造句練習時遺失資料

---

## 🚀 Phase 2: 啟用並實作造句練習功能

### 2.1 啟用造句練習選項

**前端：ContentTypeDialog.tsx** (Line 53-58)
```typescript
{
  type: "sentence_making",
  name: "造句練習",
  description: "使用指定單字或句型造句",
  icon: "✍️",
  disabled: false,  // ✅ 改為 false
},
```

**後端：models.py** (Line 114)
```python
class ContentType(str, enum.Enum):
    READING_ASSESSMENT = "reading_assessment"
    SENTENCE_MAKING = "sentence_making"  # ✅ 啟用
```

### 2.2 建立 SentenceMakingPanel 組件

**檔案位置**：`frontend/src/components/SentenceMakingPanel.tsx`

**設計規劃**：
- 參考 ReadingAssessmentPanel 的架構
- **主要差異**：
  - text 欄位：提示文字改為「輸入單字」（而非「輸入文本」）
  - **顯示例句區塊**：展開顯示，不是折疊的
  - **單字發音**：可以點擊單字發音（使用 Web Speech API）
  - **沒有「朗讀模式」**：學生是用單字來造句，不是朗讀

**UI 結構**：
```
┌─────────────────────────────────────────────────┐
│ 造句練習內容編輯                                 │
├─────────────────────────────────────────────────┤
│ 標題: [___________________________________]      │
│                                                  │
│ [+ 新增單字] [批次貼上] [批次生成TTS]           │
│ [批次生成翻譯] [批次生成例句翻譯]              │
│                                                  │
│ ┌──────────────────────────────────────────┐   │
│ │ 1. 單字: [apple                ]  [🔊][🎤]│   │
│ │    翻譯: [蘋果                  ]  [中▼][🌐]│   │
│ │                                           │   │
│ │    ───────────── 例句 ─────────────      │   │
│ │    例句(英文): [I eat an apple    ]      │   │
│ │    中文翻譯:   [我吃一顆蘋果      ]      │   │
│ │    英文釋義:   [A common fruit    ]      │   │
│ │    [🌐 生成例句翻譯]                     │   │
│ │                                           │   │
│ │                                  [複製][刪除] │
│ └──────────────────────────────────────────┘   │
│                                                  │
│ ┌──────────────────────────────────────────┐   │
│ │ 2. ...                                    │   │
│ └──────────────────────────────────────────┘   │
│                                                  │
│                           [取消]  [儲存]        │
└─────────────────────────────────────────────────┘
```

### 2.3 學生端造句練習顯示

**新建組件**：`frontend/src/components/activities/SentenceMakingTemplate.tsx`

**功能需求**：
1. **顯示單字**：
   - 單字文字
   - 單字翻譯
   - 單字發音按鈕（播放音檔或 TTS）

2. **顯示例句**：
   - 例句（英文）
   - 例句中文翻譯
   - 例句英文釋義

3. **學生作答區**：
   - 文字輸入框（造句）
   - 錄音功能（學生朗讀造的句子）
   - 提交按鈕

**UI 結構**：
```
┌─────────────────────────────────────────────────┐
│ 📝 造句練習 - 題目 1/10                          │
├─────────────────────────────────────────────────┤
│                                                  │
│ 🎯 單字: apple                        [🔊 播放]  │
│ 📖 翻譯: 蘋果                                    │
│                                                  │
│ ───────────── 參考例句 ─────────────            │
│ 💡 I eat an apple every day.                    │
│ 🇹🇼 我每天吃一顆蘋果                             │
│ 🇬🇧 A common fruit that grows on trees          │
│ ────────────────────────────────────            │
│                                                  │
│ ✍️ 你的造句:                                     │
│ ┌───────────────────────────────────────────┐  │
│ │                                            │  │
│ │  [輸入你用 "apple" 造的句子...]            │  │
│ │                                            │  │
│ └───────────────────────────────────────────┘  │
│                                                  │
│ 🎙️ 朗讀你的句子:                                │
│ [⏺️ 開始錄音]  [⏹️ 停止]  [▶️ 播放]            │
│                                                  │
│               [⬅️ 上一題]  [下一題 ➡️]           │
│                       [提交作業]                 │
└─────────────────────────────────────────────────┘
```

### 2.4 後端 API 調整

**無需修改**：
- ContentType enum 已支援 SENTENCE_MAKING
- content_items 表已有例句欄位
- 現有的 CRUD API 都支援例句欄位

**需要測試**：
- 確認 type="sentence_making" 的內容可以正常建立、讀取、更新

### 2.5 前端路由調整

**ClassroomDetail.tsx** 需要處理 sentence_making 類型：

```typescript
// 在內容編輯區塊判斷
{selectedContent.type === "reading_assessment" && (
  <ReadingAssessmentPanel ... />
)}

{selectedContent.type === "sentence_making" && (
  <SentenceMakingPanel ... />  // ✅ 新增
)}
```

**StudentActivityPageContent.tsx** 需要渲染對應模板：

```typescript
// 根據 content type 渲染不同模板
{activity.type === "reading_assessment" && (
  <ReadingAssessmentTemplate ... />
)}

{activity.type === "sentence_making" && (
  <SentenceMakingTemplate ... />  // ✅ 新增
)}
```

---

## 📝 實作任務清單

### Phase 1: Revert (預計 30 分鐘)

- [ ] 1.1 Revert ReadingAssessmentPanel UI 的例句區塊
- [ ] 1.2 移除 handleGenerateExampleTranslation 函數
- [ ] 1.3 移除批次生成例句翻譯按鈕
- [ ] 1.4 移除 SortableRowInnerProps 中的相關 prop
- [ ] 1.5 Revert GroupedQuestionsTemplate 的例句顯示
- [ ] 1.6 保留資料載入/儲存邏輯中的例句欄位（因為資料庫有）
- [ ] 1.7 測試朗讀錄音功能是否正常

### Phase 2: 啟用造句練習 (預計 3-4 小時)

#### 2.1 基礎設定 (15 分鐘)
- [ ] 啟用 ContentTypeDialog 的 sentence_making 選項
- [ ] 啟用後端 ContentType enum 的 SENTENCE_MAKING
- [ ] 測試能否選擇造句練習類型

#### 2.2 教師端編輯 (90 分鐘)
- [ ] 建立 SentenceMakingPanel 組件
- [ ] 實作單字輸入 UI
- [ ] 實作例句輸入 UI（3個欄位）
- [ ] 實作單一「生成例句翻譯」功能
- [ ] 實作「批次生成例句翻譯」功能
- [ ] 整合音檔上傳/TTS 功能
- [ ] 實作儲存功能
- [ ] 在 ClassroomDetail 中整合 SentenceMakingPanel

#### 2.3 學生端顯示 (60 分鐘)
- [ ] 建立 SentenceMakingTemplate 組件
- [ ] 實作單字顯示區塊
- [ ] 實作例句顯示區塊
- [ ] 實作學生造句輸入
- [ ] 實作錄音功能
- [ ] 實作題目導航
- [ ] 在 StudentActivityPageContent 中整合 SentenceMakingTemplate

#### 2.4 測試 (30 分鐘)
- [ ] 測試建立造句練習內容
- [ ] 測試編輯造句練習內容
- [ ] 測試 AI 生成例句翻譯（單一 + 批次）
- [ ] 測試學生端顯示
- [ ] 測試學生作答功能

---

## 🔄 Migration 需求

**✅ 無需新的 Migration**
- 例句欄位已經存在於 content_items 表
- 只需要更新程式碼邏輯

---

## ⚠️ 注意事項

1. **資料相容性**：
   - 已經建立的朗讀錄音內容可能有例句資料
   - Revert UI 後，這些資料還在資料庫中，只是不顯示
   - 不影響功能，但可能佔用少量儲存空間

2. **API 相容性**：
   - 所有 API 端點都已支援例句欄位
   - 朗讀錄音不使用例句欄位，但 API 還是會返回（為 null）

3. **測試重點**：
   - 確保朗讀錄音功能完全恢復原狀
   - 確保造句練習的例句功能完整可用

---

## 📊 預估時間

| Phase | 任務 | 預估時間 |
|-------|------|----------|
| Phase 1 | Revert 朗讀錄音例句功能 | 30 分鐘 |
| Phase 2.1 | 啟用造句練習選項 | 15 分鐘 |
| Phase 2.2 | 教師端編輯介面 | 90 分鐘 |
| Phase 2.3 | 學生端顯示介面 | 60 分鐘 |
| Phase 2.4 | 測試 | 30 分鐘 |
| **總計** | | **3.5-4 小時** |

---

## ✅ 驗收標準

### Phase 1: Revert
- [ ] 朗讀錄音編輯介面沒有例句相關 UI
- [ ] 朗讀錄音學生端沒有顯示例句
- [ ] 朗讀錄音功能完全正常運作
- [ ] 資料庫欄位保持不變（未刪除）

### Phase 2: 造句練習
- [ ] 可以選擇「造句練習」類型
- [ ] 可以建立造句練習內容（單字 + 例句）
- [ ] AI 生成例句翻譯功能正常
- [ ] 學生端正確顯示單字、例句
- [ ] 學生可以造句並錄音
- [ ] 儲存和讀取功能正常

---

## 🤔 待確認問題

請確認以下設計：

1. ✅ **資料結構**：沿用現有 content_items 表？
   - [ ] 同意
   - [ ] 需要調整（請說明）

2. ✅ **欄位使用**：朗讀錄音不使用例句欄位，造句練習使用？
   - [ ] 同意
   - [ ] 需要調整（請說明）

3. ✅ **UI 設計**：造句練習的例句區塊展開顯示？
   - [ ] 同意
   - [ ] 需要調整（請說明）

4. ✅ **功能範圍**：造句練習的學生端需要文字輸入 + 錄音功能？
   - [ ] 同意
   - [ ] 只需要文字輸入
   - [ ] 只需要錄音
   - [ ] 其他（請說明）

---

**請確認以上計劃後，我將開始實作 Phase 1 (Revert) 的工作。**
