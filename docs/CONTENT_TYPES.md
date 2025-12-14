# Content Type 系統架構

> **文件更新日期**：2025-12-09
> **目的**：描述目前系統中課程內容類型的架構

---

## 1. ContentType 總覽

### 1.1 Enum 定義

**位置**: `backend/models.py`

```python
class ContentType(str, enum.Enum):
    # Phase 1 - 啟用
    EXAMPLE_SENTENCES = "EXAMPLE_SENTENCES"  # 例句集

    # Phase 2 - 暫時禁用（UI 中不顯示）
    VOCABULARY_SET = "VOCABULARY_SET"        # 單字集
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"      # 單選題庫
    SCENARIO_DIALOGUE = "SCENARIO_DIALOGUE"  # 情境對話

    # Legacy values - 保留向後相容性（deprecated）
    READING_ASSESSMENT = "READING_ASSESSMENT"  # @deprecated: use EXAMPLE_SENTENCES
    SENTENCE_MAKING = "SENTENCE_MAKING"        # @deprecated: use VOCABULARY_SET
```

### 1.2 目前啟用狀態

| 類型 | 中文名稱 | 狀態 | 說明 |
|------|---------|------|------|
| `EXAMPLE_SENTENCES` | 例句集 | ✅ 啟用 | 聽音檔重組句子練習 |
| `VOCABULARY_SET` | 單字集 | ⏸️ Phase 2 | 看單字造句練習 |
| `MULTIPLE_CHOICE` | 單選題庫 | ⏸️ Phase 2 | 單選題庫 |
| `SCENARIO_DIALOGUE` | 情境對話 | ⏸️ Phase 2 | 情境對話練習 |

### 1.3 Legacy 值對應

| 舊值 (Deprecated) | 新值 |
|------------------|------|
| `READING_ASSESSMENT` | `EXAMPLE_SENTENCES` |
| `SENTENCE_MAKING` | `VOCABULARY_SET` |

> **注意**：新程式碼應使用新值，後端的 `normalize_content_type()` 會自動轉換舊值。

---

## 2. 作答模式 (PracticeMode)

### 2.1 Enum 定義

```python
class PracticeMode(str, enum.Enum):
    """作答模式（例句集專用）"""
    READING = "reading"           # 例句朗讀 -> 口說分類
    REARRANGEMENT = "rearrangement"  # 例句重組 -> 聽力/寫作分類
```

### 2.2 分數分類對應

```python
class ScoreCategory(str, enum.Enum):
    """分數記錄分類"""
    SPEAKING = "speaking"   # 口說
    LISTENING = "listening" # 聽力
    WRITING = "writing"     # 寫作
```

| 作答模式 | 播放音檔 | 記錄至分類 |
|---------|---------|----------|
| 例句朗讀 (`reading`) | N/A | 口說 (speaking) |
| 例句重組 (`rearrangement`) | ✅ 是 | 聽力 (listening) |
| 例句重組 (`rearrangement`) | ❌ 否 | 寫作 (writing) |

---

## 3. EXAMPLE_SENTENCES（例句集）

### 3.1 功能描述

教師建立例句集，學生可透過「例句朗讀」或「例句重組」兩種模式練習。

### 3.2 ContentItem 欄位使用

| 欄位 | 用途 | 必填 |
|------|------|------|
| `text` | 例句文本（英文） | ✅ |
| `translation` | 中文翻譯（輔助理解） | 選填 |
| `audio_url` | 例句音檔（TTS 生成） | ✅ 例句重組必要 |

### 3.3 內容建立規則

- **字數限制**: 2-25 個英文單字
- **計算方式**: 以空格分隔的 token 數量

### 3.4 作業設定選項

| 選項 | 欄位名 | 類型 | 預設值 |
|-----|-------|------|--------|
| 作答模式 | `practice_mode` | string | `reading` |
| 每題時間限制 | `time_limit_per_question` | int | 40 |
| 打亂題目順序 | `shuffle_questions` | bool | false |
| 播放音檔 | `play_audio` | bool | false |

### 3.5 例句朗讀計分

使用 Azure Speech API 進行 AI 評分：

| 維度 | 欄位 | 分數範圍 |
|------|------|---------|
| 準確率 | `accuracy_score` | 0-100 |
| 流暢度 | `fluency_score` | 0-100 |
| 發音 | `pronunciation_score` | 0-100 |

### 3.6 例句重組計分

```
每題總分 = 100 分
每個單字分數 = floor(100 / 句子單字數量)

錯誤次數限制：
- 2-10 個單字: 3 次
- 11-25 個單字: 5 次
```

---

## 4. 資料庫關聯圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Assignment                                │
├─────────────────────────────────────────────────────────────────┤
│ practice_mode: VARCHAR(20)        -- 'reading'/'rearrangement'  │
│ time_limit_per_question: INTEGER  -- 10/20/30/40 秒             │
│ shuffle_questions: BOOLEAN        -- 是否打亂順序                │
│ play_audio: BOOLEAN               -- 是否播放音檔                │
│ score_category: VARCHAR(20)       -- 分數記錄分類                │
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
│  type: EXAMPLE_SENTENCES / VOCABULARY_SET / ...                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ 1:M
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ContentItem (題目)                            │
│  text: 例句文本                                                  │
│  translation: 中文翻譯                                           │
│  audio_url: 音檔 URL                                            │
│  word_count: 單字數量                                            │
│  max_errors: 允許錯誤次數                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  StudentItemProgress (學生進度)                   │
├─────────────────────────────────────────────────────────────────┤
│ 【朗讀專用】                                                     │
│ - recording_url: 錄音檔案                                        │
│ - accuracy_score, fluency_score, pronunciation_score            │
│ - ai_feedback (JSON)                                            │
│                                                                  │
│ 【重組專用】                                                     │
│ - error_count: 錯誤次數                                          │
│ - correct_word_count: 已正確選擇的單字數                          │
│ - expected_score: 預期分數                                       │
│                                                                  │
│ 【老師批改】                                                     │
│ - teacher_review_score, teacher_feedback, teacher_passed        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 前端組件對應

| 內容類型 | 作答模式 | 主要組件 |
|---------|---------|---------|
| EXAMPLE_SENTENCES | reading | `ReadingAssessmentTemplate` |
| EXAMPLE_SENTENCES | rearrangement | `RearrangementActivity` |

---

## 6. API 端點一覽

### 例句朗讀相關

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/students/assignments/{id}/activities` | GET | 取得作業活動列表 |
| `/api/students/upload-recording` | POST | 上傳錄音檔 |
| `/api/speech/assess` | POST | AI 語音評分 |
| `/api/students/assignments/{id}/submit` | POST | 提交作業 |

### 例句重組相關

| 端點 | 方法 | 用途 |
|------|------|------|
| `/api/students/assignments/{id}/rearrangement/start` | POST | 開始重組練習 |
| `/api/students/assignments/{id}/submit-rearrangement` | POST | 提交重組答案 |
| `/api/students/assignments/{id}/items/{item_id}/retry` | POST | 重新挑戰 |
