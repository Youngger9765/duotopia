# 單字集 (VOCABULARY_SET) 功能文件

> **文件更新日期**: 2026-01-08
> **分支**: `claude/issue-147`
> **Issue**: #147
> **狀態**: Phase 2 完成（單字朗讀 + 單字選擇）

---

## 1. 功能概覽

### 1.1 內容類型與練習模式

| ContentType | 中文名稱 | 練習模式 | 說明 |
|-------------|---------|---------|------|
| `VOCABULARY_SET` | 單字集 | `word_reading` | 單字朗讀 - 學生朗讀單字，Azure Speech AI 評分 |
| `VOCABULARY_SET` | 單字集 | `word_selection` | 單字選擇 - 看單字/聽音檔選翻譯，艾賓浩斯記憶曲線 |

### 1.2 兩種模式比較

| 項目 | 單字朗讀 (`word_reading`) | 單字選擇 (`word_selection`) |
|------|:------------------------:|:---------------------------:|
| 核心功能 | 學生看單字並朗讀 | 看單字/聽音檔選翻譯 |
| 計分方式 | Azure Speech AI 評分 | 艾賓浩斯熟悉度 |
| 老師批改 | ✅ 需要 | ❌ 不需要（自動完成） |
| 達標條件 | 老師批改通過 | 熟悉度達目標（預設 80%） |
| 作業狀態流程 | 已指派→已開始→已提交→待訂正→已完成 | 已指派→已開始→達標自動完成 |

---

## 2. 單字集內容管理（老師端）

### 2.1 新增/編輯單字集

**入口位置**: 公版課程 或 班級課程列表 → 新增內容 → 選擇「單字集」

**編輯介面欄位**:

| 欄位 | 必填 | 說明 |
|------|:----:|------|
| 英文單字 (`text`) | ✅ | 最多 50 字元 |
| 中文翻譯 (`translation`) | ✅ | 單字的中文翻譯 |
| 詞性 (`part_of_speech`) | 選填 | n., v., adj., adv. 等 |
| 音檔 (`audio_url`) | 選填 | TTS 生成或錄音 |
| 圖片 (`image_url`) | 選填 | 支援上傳/貼上/拖曳 |
| 例句 (`example_sentence`) | 選填 | AI 可生成 |
| 例句翻譯 (`example_sentence_translation`) | 選填 | 支援中/日/韓 |

**批次操作功能**:
- 批次新增單字（每行一個）
- 批次生成語音（TTS）
- 批次單字翻譯（AI）
- 批次 AI 生成例句

**圖片上傳方式**:
- 點擊上傳按鈕
- Ctrl/Cmd + V 貼上截圖
- 拖曳圖片到區域
- 限制：最大 2MB，支援 jpg/png/gif/webp

### 2.2 相關檔案

| 檔案 | 用途 |
|------|------|
| `frontend/src/components/VocabularySetPanel.tsx` | 單字集編輯面板 |
| `backend/routers/teachers.py` | 單字集 CRUD API |

---

## 3. 作業建立流程（老師端）

### 3.1 AssignmentDialog 步驟

1. **Step 1 - 選擇內容**: 從購物車選擇單字集內容
2. **Step 2 - 選擇練習模式**: 根據內容類型顯示對應選項
   - 單字集 → 顯示「單字朗讀」和「單字選擇」
   - 例句集 → 顯示「例句朗讀」和「例句重組」
3. **Step 3 - 選擇學生**: 指派給特定學生或全班
4. **Step 4 - 作業詳情**: 填寫標題、說明、截止日期

### 3.2 單字朗讀作業設定

| 選項 | 欄位名 | 預設值 | 說明 |
|------|-------|--------|------|
| 打亂順序 | `shuffle_questions` | false | 是否隨機排序題目 |
| 顯示翻譯 | `show_translation` | true | 是否顯示中文翻譯 |
| 顯示圖片 | `show_image` | true | 是否顯示單字圖片 |
| 播放音檔 | `play_audio` | false | 是否自動播放音檔 |
| 單題答題時間限制 | `time_limit_per_question` | 0（不限時） | 可設定 20/30/40 秒 |

**錄音限制**:
- 錄音長度上限：10 秒（上傳時檢查）
- 錄音過長會顯示錯誤提示

### 3.3 單字選擇作業設定

| 選項 | 欄位名 | 預設值 | 說明 |
|------|-------|--------|------|
| 達標熟悉度 | `target_proficiency` | 80% | 50-100%，學生需達此熟悉度才算完成 |
| 打亂順序 | `shuffle_questions` | false | 是否隨機排序題目 |
| 顯示單字 | `show_word` | true | 是否顯示英文單字（關閉時只播音檔） |
| 顯示圖片 | `show_image` | true | 是否顯示單字圖片 |
| 播放音檔 | `play_audio` | false | 是否播放音檔 |
| 每題時間限制 | `time_limit_per_question` | null | 可設定 5/10/15/20/30 秒 |

### 3.4 相關檔案

| 檔案 | 用途 |
|------|------|
| `frontend/src/components/AssignmentDialog.tsx` | 作業建立對話框 |
| `backend/routers/assignments.py` | 作業建立 API |

---

## 4. 單字選擇學生端作答

### 4.1 作答流程

```
開始練習 → 顯示單字/播放音檔 → 選擇翻譯（4選1）→ 顯示結果 → 下一題
    ↓
完成一輪 → 檢查熟悉度 → 達標？
    │           ├─ 是 → 顯示成就對話框 → 關閉/繼續練習
    │           └─ 否 → 開始下一輪
    ↓
每次作答後自動同步作業狀態（GRADED/IN_PROGRESS）
```

### 4.2 UI 元件

**作答畫面包含**:
- Header: [單字選擇] Badge + 第 N/M 題 + 熟悉度顯示
- 題目區域: 圖片（可選）+ 單字文字（可選）+ 播放音檔按鈕（可選）
- 倒數計時器（若有設定時間限制）
- 4 選 1 選項按鈕
- 答題結果反饋（答對/答錯）
- 下一題/完成本輪按鈕

**本輪完成畫面**:
- 熟悉度進度條
- 已達標：顯示成就對話框（繼續練習/關閉）
- 未達標：顯示「開始下一輪」按鈕

### 4.3 艾賓浩斯記憶曲線

**熟悉度計算** (基於 SM-2 演算法):

| 動作 | 效果 |
|------|------|
| 答對 | memory_strength += 0.3（最高 1.0），間隔遞增 |
| 答錯 | memory_strength *= 0.5（最低 0.1），間隔重置 |

**達標判定**:
- 所有單字的平均熟悉度 >= `target_proficiency`
- 達標時自動將作業狀態更新為 `GRADED`

### 4.4 干擾選項生成

- **數量**: 3 個干擾項 + 1 個正確答案 = 4 選 1
- **生成時機**: 老師儲存單字集時預先生成，存入 `content_items.distractors`
- **生成策略**: AI 生成語義相近但不同義的詞彙

### 4.5 相關檔案

| 檔案 | 用途 |
|------|------|
| `frontend/src/components/activities/WordSelectionActivity.tsx` | 單字選擇作答元件 |
| `frontend/src/pages/student/StudentActivityPageContent.tsx` | 學生作業頁面內容 |
| `backend/routers/students.py` | 學生作答 API |

---

## 5. 單字朗讀學生端作答

### 5.1 作答流程

```
進入作業 → 自動播放題目音檔 → 顯示單字（+詞性+翻譯+圖片）
    ↓
學生錄音或上傳音檔（最長 10 秒）
    ↓
點擊「上傳並分析」→ Azure Speech AI 評分
    ↓
顯示 AI 評估結果（準確度/流暢度/完整度/發音）
    ↓
下一題 / 提交作業
    ↓
等待老師批改 → 老師批改通過 → 作業完成
```

### 5.2 UI 元件

**作答畫面佈局**（仿造例句朗讀）:
- 手機版：垂直堆疊佈局
- 桌面版：兩欄式佈局（左：題目/圖片/作答/評語，右：AI 評估）

**左欄包含**:
- 題目區塊：播放音檔按鈕 + 單字文字 + 詞性 Badge + 倍速選擇
- 翻譯區塊（若啟用 `show_translation`）
- 圖片區塊（若啟用 `show_image` 且有圖片）
- 學生作答區塊：錄音按鈕 + 上傳按鈕 / 播放控制 + 刪除按鈕
- 老師評語區塊：顯示老師批改結果

**右欄包含**:
- AI 評估結果：綜合評分 + 四項細項分數
- 「上傳並分析」按鈕（錄音後顯示）
- AI 分析中動畫

### 5.3 錄音功能

| 項目 | 說明 |
|------|------|
| 錄音長度上限 | 10 秒（上傳時檢查） |
| 支援格式 | webm, mp4, wav, m4a, ogg, aac |
| 錄音按鈕 | 紅色圓形，點擊開始/停止錄音 |
| 上傳按鈕 | 綠色圓形，支援本地音檔上傳 |
| 刪除按鈕 | 垃圾桶圖示，清除錄音和評估結果 |

### 5.4 AI 發音評估

**Azure Speech SDK 評分項目**:

| 項目 | 說明 |
|------|------|
| 準確度 (Accuracy) | 發音的準確程度 |
| 流暢度 (Fluency) | 語句流暢程度 |
| 完整度 (Completeness) | 發音完整性 |
| 發音 (Pronunciation) | 綜合發音評分 |

**評分等級顏色**:
- 80 分以上：綠色
- 60-79 分：黃色
- 60 分以下：紅色

### 5.5 時間限制

| 設定值 | 說明 |
|--------|------|
| 0（預設） | 不限時 |
| 20 | 20 秒倒數 |
| 30 | 30 秒倒數 |
| 40 | 40 秒倒數 |

**時間限制行為**:
- 有設定時間時，右上角顯示倒數計時器
- 倒數到 0 時彈出超時對話框
- 可選擇「重試」或「跳過」

### 5.6 readOnly 模式

提交作業後進入檢視模式：
- 錄音和上傳按鈕禁用
- 刪除按鈕隱藏
- 可播放已錄製的音檔
- 顯示 AI 評估結果和老師評語

### 5.7 相關檔案

| 檔案 | 用途 |
|------|------|
| `frontend/src/components/activities/WordReadingTemplate.tsx` | 單字朗讀作答模板 |
| `frontend/src/components/activities/WordReadingActivity.tsx` | 單字朗讀作答元件 |
| `frontend/src/hooks/useAzurePronunciation.ts` | Azure Speech SDK Hook |

---

## 6. 老師端預覽示範

### 6.1 預覽入口

**位置**: 老師端 → 班級 → 作業管理 → 點擊作業 → 「預覽示範」按鈕

### 6.2 預覽頁面

- 重用 `StudentActivityPageContent` 元件
- 傳入 `isPreviewMode={true}`
- 不儲存任何進度、不呼叫作答 API
- 顯示藍色預覽模式提示 Banner

### 6.3 預覽模式與學生模式差異

| 項目 | 預覽模式 | 學生模式 |
|------|---------|---------|
| 作答 API | ❌ 不呼叫 | ✅ 呼叫 |
| 進度儲存 | ❌ 不儲存 | ✅ 儲存 |
| 熟悉度追蹤 | ❌ 不追蹤 | ✅ 追蹤 |
| Header 顯示 | 外層有返回作業列表按鈕 | 內層有返回按鈕 |

### 6.4 相關檔案

| 檔案 | 用途 |
|------|------|
| `frontend/src/pages/teacher/TeacherAssignmentPreviewPage.tsx` | 老師預覽頁面 |
| `backend/routers/teachers.py` | 預覽 API (`/preview/word-selection-start`) |

---

## 7. 單字選擇相關列表修改

### 7.1 老師端 - 班級作業列表

**檔案**: `frontend/src/pages/teacher/ClassroomDetail.tsx`

| 修改項目 | 說明 |
|---------|------|
| 內容類型標籤 | 依 `practice_mode` 顯示「單字選擇」或「單字朗讀」 |
| AI 批改按鈕 | 單字選擇作業隱藏此按鈕（不需人工批改） |

**標籤顏色**:
- 單字選擇 (`word_selection`) → indigo 色
- 單字朗讀 (`word_reading`) → purple 色

### 7.2 學生端 - 作業列表

**檔案**: `frontend/src/pages/student/StudentAssignmentList.tsx`

| 修改項目 | 說明 |
|---------|------|
| 「查看結果」按鈕 | 單字選擇已完成作業隱藏此按鈕 |
| 分數顯示 | 單字選擇顯示「熟悉度：xx.x%」而非「分數：xxxx」 |
| 進度區塊 | 單字選擇已完成作業隱藏「完成進度」灰色區塊 |

### 7.3 翻譯 Key

**新增的翻譯 Key**:

```json
// zh-TW
{
  "classroomDetail": {
    "contentTypes": {
      "WORD_SELECTION": "單字選擇",
      "WORD_READING": "單字朗讀"
    }
  },
  "studentAssignmentList": {
    "proficiency": {
      "label": "熟悉度：{{proficiency}}%"
    }
  }
}
```

---

## 8. 資料庫結構

### 8.1 ContentItem 擴充欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `image_url` | TEXT | 單字圖片 URL |
| `part_of_speech` | VARCHAR(20) | 詞性 (n., v., adj., etc.) |
| `distractors` | JSONB | 預生成的干擾選項 `["選項1", "選項2", "選項3"]` |

### 8.2 Assignment 擴充欄位

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `target_proficiency` | INTEGER | 80 | 達標熟悉度 (50-100) |
| `show_translation` | BOOLEAN | true | 是否顯示翻譯（單字朗讀） |
| `show_word` | BOOLEAN | true | 是否顯示單字（單字選擇） |
| `show_image` | BOOLEAN | true | 是否顯示圖片 |

### 8.3 UserWordProgress（記憶強度追蹤）

```sql
CREATE TABLE user_word_progress (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    student_assignment_id INTEGER NOT NULL,
    content_item_id INTEGER NOT NULL,
    memory_strength NUMERIC(5, 4) DEFAULT 0,      -- 記憶強度 (0-1)
    repetition_count INTEGER DEFAULT 0,            -- 連續答對次數
    correct_count INTEGER DEFAULT 0,               -- 累計答對
    incorrect_count INTEGER DEFAULT 0,             -- 累計答錯
    last_review_at TIMESTAMPTZ,                    -- 最後複習時間
    next_review_at TIMESTAMPTZ,                    -- 下次複習時間
    UNIQUE(student_assignment_id, content_item_id)
);
```

---

## 9. API 端點

### 9.1 學生端 API

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/students/assignments/{id}/vocabulary/selection/start` | GET | 開始單字選擇練習 |
| `/api/students/assignments/{id}/vocabulary/selection/answer` | POST | 提交選擇答案 |
| `/api/students/assignments/{id}/vocabulary/selection/proficiency` | GET | 取得熟悉度狀態 |

### 9.2 老師端 API

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/teachers/assignments/{id}/preview` | GET | 取得預覽資料 |
| `/api/teachers/assignments/{id}/preview/word-selection-start` | GET | 開始預覽模式練習 |

---

## 10. claude/issue-147 分支修改記錄

### 10.1 主要功能提交

| Commit | 說明 |
|--------|------|
| `7262385` | 實作 VOCABULARY_SET Phase 2 基礎功能 |
| `866a77f` | 預先生成干擾選項 & 老師詳情頁優化 |
| `6921381` | 支援老師端預覽模式 |
| `2c8100b` | 圖片上傳與作業設定改進 |

### 10.2 修復提交

| Commit | 說明 |
|--------|------|
| `3fe9808` | 作業副本複製時包含 distractors, image_url, part_of_speech |
| `726e97c` | 修復熟悉度分數更新與顯示（後端每次都更新 score） |
| `23bbefc` | 改進干擾選項 prompt 避免生成近義詞 |
| `0d9d401` | 修正單字選擇模式的三個問題 |

### 10.3 UI 優化提交

| Commit | 說明 |
|--------|------|
| `c8c1bdc` | 單字集作業列表依 practice_mode 顯示不同標籤 |
| `04463bf` | 隱藏單字選擇作業的 AI 批改按鈕 |
| `eb05cac` | 隱藏單字選擇已完成作業的進度區塊 |
| `939790c` | 隱藏單字選擇已完成作業的「查看結果」按鈕 |
| `31b2e43` | 修正學生端返回按鈕，隱藏提交按鈕 |

---

## 11. 待開發功能

### 11.1 單字朗讀（Phase 2-2）✅ 已完成

- [x] WordReadingTemplate 元件
- [x] 錄音功能（max 10s）
- [x] Azure Speech AI 評分整合
- [x] 老師批改介面
- [x] 時間限制設定（不限時/20/30/40 秒）
- [x] 自動播放音檔功能
- [x] readOnly 模式（提交後不可刪除錄音和評估）

### 11.2 未來考量

- 跨班級單字熟悉度（需考慮帳號合併問題）
- 更多干擾選項生成策略
- 學習曲線數據分析

---

## 12. 參考文件

- [CONTENT_TYPES.md](./CONTENT_TYPES.md) - 內容類型系統架構
- [VOCABULARY_SET_UI_PLAN.md](./VOCABULARY_SET_UI_PLAN.md) - UI 規劃文件
- [vocabulary_set_phase2_plan.md](./plans/vocabulary_set_phase2_plan.md) - Phase 2 實作計劃

---

**文件版本**: v1.0
**建立日期**: 2026-01-08
**作者**: Claude Code
