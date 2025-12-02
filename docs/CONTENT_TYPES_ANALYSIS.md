# 課程內容類型系統分析

> 文件建立日期：2025-12-02
> 目的：整理目前系統中課程內容的類型、作答方式、計分方式，作為後續修改的基準

---

## 1. 內容類型總覽

### 1.1 ContentType Enum 定義

**位置**: `backend/models.py` (第 133-140 行)

```python
class ContentType(str, enum.Enum):
    READING_ASSESSMENT = "READING_ASSESSMENT"
    SENTENCE_MAKING = "SENTENCE_MAKING"
    # Phase 2 擴展（目前已註釋禁用）
    # SPEAKING_PRACTICE = "SPEAKING_PRACTICE"
    # SPEAKING_SCENARIO = "SPEAKING_SCENARIO"
    # LISTENING_CLOZE = "LISTENING_CLOZE"
    # SPEAKING_QUIZ = "SPEAKING_QUIZ"
```

### 1.2 目前啟用狀態

| 類型 | 中文名稱 | 狀態 | 說明 |
|------|---------|------|------|
| `READING_ASSESSMENT` | 朗讀評測 | ✅ 啟用 | Phase 1 完成 |
| `SENTENCE_MAKING` | 句子模組 | ✅ 啟用 | Phase 1 完成 |
| `SPEAKING_PRACTICE` | 口說練習 | ❌ 禁用 | Phase 2 計畫中 |
| `SPEAKING_SCENARIO` | 情境對話 | ❌ 禁用 | Phase 2 計畫中 |
| `LISTENING_CLOZE` | 聽力填空 | ❌ 禁用 | Phase 2 計畫中 |
| `SPEAKING_QUIZ` | 口說測驗 | ❌ 禁用 | Phase 2 計畫中 |

---

## 2. READING_ASSESSMENT（朗讀評測）

### 2.1 功能描述

學生朗讀指定的英文文本，系統錄音並透過 Azure Speech API 進行 AI 評分。

### 2.2 資料結構

#### ContentItem 欄位使用

| 欄位 | 用途 | 必填 |
|------|------|------|
| `text` | 朗讀文本（英文） | ✅ |
| `translation` | 中文翻譯（輔助理解） | 選填 |
| `audio_url` | 示範錄音（老師/TTS） | 選填 |
| `example_sentence` | ❌ 不使用 | - |
| `example_sentence_translation` | ❌ 不使用 | - |

#### Content 設定欄位

| 欄位 | 用途 | 預設值 |
|------|------|--------|
| `target_wpm` | 目標語速（字/分鐘） | 100 |
| `target_accuracy` | 目標準確率 | 80% |
| `time_limit_seconds` | 時間限制 | 無 |

### 2.3 作答流程

```
1. 學生進入作業頁面
   ↓
2. 載入題目列表（多個 ContentItem）
   ↓
3. 對每個題目：
   ├─ 顯示朗讀文本
   ├─ 可播放示範錄音（如有）
   ├─ 學生按「開始錄音」
   ├─ 錄音中...（顯示計時）
   ├─ 學生按「停止錄音」
   ├─ 上傳錄音至 GCS
   ├─ 調用 Azure Speech API 評分
   └─ 顯示評分結果
   ↓
4. 全部題目完成後，學生按「提交作業」
   ↓
5. 狀態變更為 SUBMITTED
```

### 2.4 計分方式

#### AI 評分維度

| 維度 | 英文欄位 | 分數範圍 | 說明 |
|------|---------|---------|------|
| 準確率 | `accuracy_score` | 0-100 | 單字發音正確程度 |
| 流暢度 | `fluency_score` | 0-100 | 語句連貫程度 |
| 發音 | `pronunciation_score` | 0-100 | 發音標準程度 |

#### 總分計算

```python
overall_score = (accuracy_score + fluency_score + pronunciation_score) / 3
```

#### 儲存位置

- **StudentItemProgress** 表
  - `accuracy_score`, `fluency_score`, `pronunciation_score`
  - `ai_feedback` (JSON 格式完整評分資料)
  - `recording_url` (學生錄音檔案)

### 2.5 熟練度/完成度判定

**目前無記憶曲線追蹤**

- 完成標準：所有題目都有錄音並評分
- 不使用 `UserWordProgress` 表
- 不使用 `memory_strength` 計算

### 2.6 老師批改

| 欄位 | 用途 |
|------|------|
| `teacher_review_score` | 老師評分 (0-100) |
| `teacher_feedback` | 老師文字回饋 |
| `teacher_passed` | 是否通過 (T/F/NULL) |
| `review_status` | PENDING / REVIEWED |

---

## 3. SENTENCE_MAKING（句子模組）

### 3.1 功能描述

學生透過反覆練習掌握指定單字，系統使用艾賓浩斯記憶曲線追蹤記憶強度。

### 3.2 資料結構

#### ContentItem 欄位使用

| 欄位 | 用途 | 必填 |
|------|------|------|
| `text` | 單字（英文） | ✅ |
| `translation` | 單字中文翻譯 | ✅ |
| `audio_url` | 單字/例句發音 | 建議（聽力模式必要） |
| `example_sentence` | 英文例句 | ✅ |
| `example_sentence_translation` | 例句中文翻譯 | 選填 |

#### Assignment 專屬欄位

| 欄位 | 用途 | 可選值 |
|------|------|--------|
| `answer_mode` | 答題模式 | `listening` / `writing` |

### 3.3 作答流程

```
1. 學生進入作業頁面
   ↓
2. 呼叫 get_words_for_practice() 取得 10 個練習題
   ├─ 智能選擇邏輯（見 3.5）
   └─ 建立 PracticeSession 記錄
   ↓
3. 根據 answer_mode 選擇模式：
   │
   ├─【聽力模式 (listening)】
   │   ├─ 播放例句音檔
   │   ├─ 顯示打亂的單字選項
   │   ├─ 學生依序點選組成句子
   │   └─ 即時判斷對錯
   │
   └─【寫作模式 (writing)】
       ├─ 顯示例句（挖空目標單字）
       ├─ 顯示單字的中文定義
       ├─ 學生輸入英文單字
       └─ 即時判斷對錯
   ↓
4. 每次作答後：
   ├─ 呼叫 update_memory_strength() 更新記憶強度
   ├─ 記錄至 PracticeAnswer
   └─ 顯示對錯回饋
   ↓
5. 一輪 10 題完成後：
   ├─ 呼叫 calculate_assignment_mastery() 檢查完成度
   │
   ├─ 如達成目標（>= 90%）
   │   └─ 完成作業，狀態變更為 SUBMITTED
   │
   └─ 如未達成
       └─ 重新載入新的 10 題，返回第 2 步
```

### 3.4 計分方式

#### 單題計分

| 結果 | 處理 |
|------|------|
| 答對 | `is_correct = true`，記憶強度增加 |
| 答錯 | `is_correct = false`，記憶強度減少 |

**無 AI 評分**，純粹比對答案正確性。

### 3.5 熟練度計算（艾賓浩斯記憶曲線）

#### 核心演算法：SM-2 (SuperMemo 2)

**儲存位置**: `UserWordProgress` 表

| 欄位 | 用途 | 初始值 |
|------|------|--------|
| `memory_strength` | 記憶強度 (0-1) | 0 |
| `easiness_factor` | 難易度因子 | 2.5 |
| `repetition_count` | 連續答對次數 | 0 |
| `interval_days` | 複習間隔天數 | 1 |
| `next_review_at` | 下次建議複習時間 | NULL |

#### 記憶強度更新邏輯

```sql
-- update_memory_strength() 函數

【初次嘗試】
IF 答對:
    memory_strength = 0.5
    next_review_at = NOW() + 1 day
    repetition_count = 1
ELSE:
    memory_strength = 0.2
    next_review_at = NOW() + 1 day
    repetition_count = 0

【後續嘗試】
-- 1. 計算時間衰減（遺忘曲線）
elapsed_seconds = NOW() - last_review_at
decay = EXP(-elapsed_seconds / (86400 * easiness_factor))
new_strength = memory_strength * decay

-- 2. 根據對錯調整
IF 答對:
    new_strength = MIN(1.0, new_strength + 0.3)
    new_easiness = MAX(1.3, easiness_factor + 0.1)

    -- 複習間隔（SM-2）
    IF repetition_count == 0: interval = 1 day
    ELSIF repetition_count == 1: interval = 6 days
    ELSE: interval = interval_days * easiness_factor

    repetition_count += 1
ELSE:
    new_strength = MAX(0.1, memory_strength * 0.5)
    new_easiness = MAX(1.3, easiness_factor - 0.2)
    interval = 1 day
    repetition_count = 0  -- 重置
```

#### 練習題目選擇邏輯

```sql
-- get_words_for_practice() 函數

優先級計算：
1. 從未練習過 → priority = 100
2. 已逾期複習（next_review_at <= NOW()）
   → priority = 50 + (1 - memory_strength) * 50
3. 未逾期但記憶弱
   → priority = (1 - memory_strength) * 30

選擇方式：
- 按優先級降序排列
- 同優先級內隨機
- 取前 10 個
```

#### 作業完成度判定

```sql
-- calculate_assignment_mastery() 函數

計算：
1. total_words = 作業總單字數
2. practiced_words = 已練習的單字數
3. avg_strength = 已練習單字的平均 memory_strength

-- 未練習的單字視為 0
IF practiced_words < total_words:
    avg_strength = (avg_strength * practiced_words) / total_words

完成標準：
- achieved = (avg_strength >= 0.90)  -- 90% 熟練度
- words_mastered = COUNT(*) WHERE memory_strength >= 0.8
```

### 3.6 相關資料表

| 表名 | 用途 |
|------|------|
| `UserWordProgress` | 單字記憶強度追蹤 |
| `PracticeSession` | 練習場次記錄 |
| `PracticeAnswer` | 個別答題記錄 |

---

## 4. 兩種類型的比較

| 項目 | READING_ASSESSMENT | SENTENCE_MAKING |
|------|-------------------|-----------------|
| **核心功能** | 朗讀錄音評分 | 單字記憶練習 |
| **作答方式** | 錄音 | 選擇/輸入 |
| **評分方式** | Azure AI 評分 | 答案比對 |
| **評分維度** | 準確率/流暢度/發音 | 對/錯 |
| **熟練度追蹤** | 無 | 艾賓浩斯記憶曲線 |
| **完成標準** | 全部錄音完成 | 平均記憶強度 >= 90% |
| **老師批改** | 支援 | 不支援 |
| **答題模式** | 單一（錄音） | 聽力/寫作 兩種 |

---

## 5. 資料庫關聯圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Assignment (作業)                         │
│  - answer_mode: 'listening' / 'writing' (SENTENCE_MAKING 專用)  │
└────────────────────────────┬────────────────────────────────────┘
                             │ 1:M
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AssignmentContent (作業-內容映射)              │
└────────────────────────────┬────────────────────────────────────┘
                             │ M:1
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Content (內容)                              │
│  - type: READING_ASSESSMENT / SENTENCE_MAKING                   │
│  - target_wpm, target_accuracy (朗讀專用)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ 1:M
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ContentItem (題目)                            │
│  - text: 朗讀文本 / 單字                                         │
│  - translation: 中文翻譯                                         │
│  - audio_url: 示範錄音                                           │
│  - example_sentence: 例句 (SENTENCE_MAKING)                      │
│  - example_sentence_translation: 例句翻譯 (SENTENCE_MAKING)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────────┐               ┌───────────────────────┐
│ StudentItemProgress   │               │  UserWordProgress     │
│ (題目進度)            │               │  (記憶強度)           │
│                       │               │                       │
│ 【朗讀專用】          │               │ 【造句專用】          │
│ - recording_url       │               │ - memory_strength     │
│ - accuracy_score      │               │ - easiness_factor     │
│ - fluency_score       │               │ - repetition_count    │
│ - pronunciation_score │               │ - next_review_at      │
│ - ai_feedback         │               │ - interval_days       │
│                       │               │                       │
│ 【老師批改】          │               └───────────────────────┘
│ - teacher_review_score│
│ - teacher_feedback    │
│ - teacher_passed      │
└───────────────────────┘

                             │
                             ▼
              ┌─────────────────────────────────┐
              │      PracticeSession            │
              │      (練習記錄)                  │
              │  【SENTENCE_MAKING 專用】        │
              │  - practice_mode                │
              │  - words_practiced              │
              │  - correct_count                │
              └──────────────┬──────────────────┘
                             │ 1:M
                             ▼
              ┌─────────────────────────────────┐
              │      PracticeAnswer             │
              │      (答題記錄)                  │
              │  - is_correct                   │
              │  - time_spent_seconds           │
              │  - answer_data (JSON)           │
              └─────────────────────────────────┘
```

---

## 6. 前端組件對應

| 內容類型 | 主要組件 | 子組件 |
|---------|---------|--------|
| READING_ASSESSMENT | `GroupedQuestionsTemplate` | `ReadingAssessmentTemplate` |
| SENTENCE_MAKING | `SentenceMakingActivity` | `ListeningModeTemplate`, `WritingModeTemplate` |

### 活動類型判定邏輯

**位置**: `frontend/src/pages/student/StudentActivityPageContent.tsx`

```typescript
switch (activity.type) {
    case "READING_ASSESSMENT":
    case "reading_assessment":
        // → GroupedQuestionsTemplate 或 ReadingAssessmentTemplate

    case "SENTENCE_MAKING":
    case "sentence_making":
        // → SentenceMakingActivity

    default:
        // → ReadingAssessmentTemplate (fallback)
}
```

---

## 7. API 端點一覽

### READING_ASSESSMENT 相關

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/students/assignments/{id}/activities` | GET | 取得作業活動列表 |
| `/api/students/upload-recording` | POST | 上傳錄音檔 |
| `/api/speech/assess` | POST | AI 語音評分 |
| `/api/students/assignments/{id}/submit` | POST | 提交作業 |

### SENTENCE_MAKING 相關

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/students/assignments/{id}/practice-words` | GET | 取得練習題目（智能選擇） |
| `/api/students/practice-sessions/{id}/submit-answer` | POST | 提交單題答案 |
| `/api/students/assignments/{id}/mastery-status` | GET | 查詢完成度 |

---

## 8. 待確認/潛在修改點

### 8.1 可能的改進方向

1. **統一計分體系**：READING_ASSESSMENT 是否也要引入熟練度追蹤？
2. **答題模式擴展**：是否增加更多作答方式？
3. **AI 評分整合**：SENTENCE_MAKING 是否需要語音評分？
4. **完成度標準**：90% 熟練度是否需要調整？

### 8.2 目前的設計限制

1. READING_ASSESSMENT 無法追蹤「是否真正掌握」
2. SENTENCE_MAKING 無法評估「發音正確性」
3. 兩種類型的完成標準不統一
4. 老師批改功能僅限於 READING_ASSESSMENT

---

*此文件將作為後續修改的基準參考*
