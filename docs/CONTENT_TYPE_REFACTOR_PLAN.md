# Content Type 重構計劃

> **目標**：將 Phase 1 的兩個 ContentType 改名並重新定義，增加 Phase 2 內容類型，並實現「例句集」的多種作答模式。

---

## 📋 目錄

1. [概述](#1-概述)
2. [命名方案](#2-命名方案)
3. [Phase 1 開放狀態](#3-phase-1-開放狀態)
4. [例句集功能規格](#4-例句集功能規格)
5. [計分系統規格](#5-計分系統規格)
6. [資料庫變更](#6-資料庫變更)
7. [API 變更](#7-api-變更)
8. [前端變更](#8-前端變更)
9. [Migration 計劃](#9-migration-計劃)
10. [開發階段](#10-開發階段)
11. [待釐清問題](#11-待釐清問題)

---

## 1. 概述

### 1.1 現有架構

| 現有 ContentType | 中文名稱 | 狀態 |
|-----------------|---------|------|
| `READING_ASSESSMENT` | 朗讀評測 | ✅ Phase 1 啟用 |
| `SENTENCE_MAKING` | 句子模組 | ✅ Phase 1 啟用 |

### 1.2 目標架構

| 新 ContentType | 中文名稱 | Phase | 狀態 |
|---------------|---------|-------|------|
| `EXAMPLE_SENTENCES` | 例句集 | Phase 1 | ✅ 啟用 |
| `VOCABULARY_SET` | 單字集 | Phase 2 | ⏸️ 禁用 |
| `MULTIPLE_CHOICE` | 單選題庫 | Phase 2 | ⏸️ 禁用 |
| `SCENARIO_DIALOGUE` | 情境對話 | Phase 2 | ⏸️ 禁用 |

### 1.3 對應關係

```
舊類型                    →    新類型
──────────────────────────────────────────
READING_ASSESSMENT        →    EXAMPLE_SENTENCES（例句集）
SENTENCE_MAKING           →    VOCABULARY_SET（單字集，Phase 2）
SPEAKING_PRACTICE (舊)    →    刪除
SPEAKING_SCENARIO (舊)    →    SCENARIO_DIALOGUE（情境對話）
LISTENING_CLOZE (舊)      →    刪除
SPEAKING_QUIZ (舊)        →    MULTIPLE_CHOICE（單選題庫）
```

---

## 2. 命名方案

### 2.1 英文命名建議

| 中文名稱 | 英文 Enum 值 | 英文描述 |
|---------|-------------|---------|
| 例句集 | `EXAMPLE_SENTENCES` | Example Sentences Collection |
| 單字集 | `VOCABULARY_SET` | Vocabulary Set |
| 單選題庫 | `MULTIPLE_CHOICE` | Multiple Choice Questions |
| 情境對話 | `SCENARIO_DIALOGUE` | Scenario Dialogue |

### 2.2 資料庫 Enum 定義

```python
class ContentType(str, enum.Enum):
    # Phase 1 - 啟用
    EXAMPLE_SENTENCES = "EXAMPLE_SENTENCES"  # 例句集（原 READING_ASSESSMENT）

    # Phase 2 - 暫時禁用
    VOCABULARY_SET = "VOCABULARY_SET"        # 單字集（原 SENTENCE_MAKING）
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"      # 單選題庫
    SCENARIO_DIALOGUE = "SCENARIO_DIALOGUE"  # 情境對話
```

---

## 3. Phase 1 開放狀態

### 3.1 Phase 1（目前）

| ContentType | 狀態 | 說明 |
|------------|------|------|
| `EXAMPLE_SENTENCES` | ✅ 啟用 | 例句集（含多種作答模式） |
| `VOCABULARY_SET` | ⏸️ 禁用 | 單字集（保留程式碼，UI 禁用） |
| `MULTIPLE_CHOICE` | ⏸️ 禁用 | 單選題庫（Phase 2） |
| `SCENARIO_DIALOGUE` | ⏸️ 禁用 | 情境對話（Phase 2） |

### 3.2 Phase 2（未來）

開放 `VOCABULARY_SET`、`MULTIPLE_CHOICE`、`SCENARIO_DIALOGUE`

---

## 4. 例句集功能規格

### 4.1 內容建立規則

#### 輸入字數限制

- **最少**: 2 個英文單字
- **最多**: 25 個英文單字
- **計算方式**: 以空格分隔的 token 數量

#### 字數計算範例

```
句子：One of the two members of the National Guard that were shot in Washington DC on Wednesday has died, US President Donald Trump said.

計算方式：
- "One" → 前面沒空格，後面有空格 → 1 個單字
- "members" → 前後都有空格 → 1 個單字
- "died," → 前後都有空格 → 1 個單字（逗號視為單字的一部分）

總計：24 個單字 ✅ 符合限制
```

#### 驗證邏輯（前後端一致）

```python
def count_words(text: str) -> int:
    """計算英文單字數量（以空格分隔）"""
    return len(text.strip().split())

def validate_sentence_length(text: str) -> tuple[bool, str]:
    """驗證句子長度是否符合規則"""
    word_count = count_words(text)
    if word_count < 2:
        return False, f"句子至少需要 2 個單字，目前 {word_count} 個"
    if word_count > 25:
        return False, f"句子最多 25 個單字，目前 {word_count} 個"
    return True, f"符合規則（{word_count} 個單字）"
```

### 4.2 作答模式

當指派「例句集」類型的作業時，需要選擇作答模式：

| 作答模式 | 英文代碼 | 說明 | 記錄至分類 |
|---------|---------|------|----------|
| 例句朗讀 | `reading` | 學生朗讀句子，AI 評分 | 口說 |
| 例句重組 | `rearrangement` | 學生排列打亂的單字 | 視聽力設定 |

### 4.3 作業設定選項

#### 共通選項（兩種模式都有）

| 選項 | 欄位名 | 類型 | 預設值 | 選項 |
|-----|-------|------|--------|------|
| 限制每題答題時間 | `time_limit_seconds` | int | 40 | 10/20/30/40 秒 |
| 是否打亂順序 | `shuffle_questions` | bool | false | true/false |

#### 例句重組專用選項

| 選項 | 欄位名 | 類型 | 預設值 | 說明 |
|-----|-------|------|--------|------|
| 是否播放音檔 | `play_audio` | bool | false | true = 聽力模式，false = 寫作模式 |

### 4.4 分類對應

| 作答模式 | 播放音檔 | 記錄至分類 |
|---------|---------|----------|
| 例句朗讀 (`reading`) | N/A | 口說 (speaking) |
| 例句重組 (`rearrangement`) | ✅ 是 | 聽力 (listening) |
| 例句重組 (`rearrangement`) | ❌ 否 | 寫作 (writing) |

---

## 5. 計分系統規格

### 5.1 例句重組計分

#### 基本公式

```
每題總分 = 100 分
每個單字分數 = floor(100 / 句子單字數量)

範例：24 個單字的句子
- 每個單字分數 = floor(100/24) = floor(4.166...) = 4 分
```

#### 錯誤次數限制

| 句子長度 | 允許錯誤次數 |
|---------|------------|
| 2-10 個單字 | 3 次 |
| 11-25 個單字 | 5 次 |

#### 計分流程

```
開始作答
├── 學生選擇單字
│   ├── 正確 → 不扣分，繼續
│   └── 錯誤 → 扣 (100/單字數) 分，錯誤次數 +1
│       ├── 未達錯誤上限 → 繼續作答
│       └── 達到錯誤上限 → 顯示「挑戰失敗」
│           ├── 學生選「重新挑戰」→ 分數歸零重來
│           └── 學生選「繼續完成」→ 繼續作答
│
└── 完成所有單字
    └── 紀錄「預期分數」為「實際分數」
```

#### 最低基本分

- 只要學生**完成作答**（不管錯多少），最低保留 `floor(100/題數)` 分
- 若學生**跳題未完成**，該題為 **0 分**

#### 時間到期處理

- 若老師設定時間限制，時間到時：
  - 不管學生是否完成
  - 以「當下預期分數」作為「實際分數」
  - 未作答的視為 0 分

### 5.2 例句朗讀計分

沿用現有 Azure Speech API 評分：
- Accuracy Score（準確率）
- Fluency Score（流暢度）
- Pronunciation Score（發音）

### 5.3 整份作業總分計算

```
作業總分 = Σ(所有小題分數) / 題目數量

範例：10 題作業
- 題 1: 80 分
- 題 2: 60 分
- ...
- 題 10: 90 分

總分 = (80 + 60 + ... + 90) / 10
```

**保留老師人工調整權利**：老師可覆蓋系統計算的分數

---

## 6. 資料庫變更

### 6.1 Enum 變更

#### 新增 Enum 值

```sql
-- 使用 IF NOT EXISTS 模式（遵循 Additive Migration 原則）
DO $$
BEGIN
    -- 新增 EXAMPLE_SENTENCES
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'EXAMPLE_SENTENCES'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
    ) THEN
        ALTER TYPE contenttype ADD VALUE 'EXAMPLE_SENTENCES';
    END IF;

    -- 新增 VOCABULARY_SET
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'VOCABULARY_SET'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
    ) THEN
        ALTER TYPE contenttype ADD VALUE 'VOCABULARY_SET';
    END IF;

    -- 新增 MULTIPLE_CHOICE
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'MULTIPLE_CHOICE'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
    ) THEN
        ALTER TYPE contenttype ADD VALUE 'MULTIPLE_CHOICE';
    END IF;

    -- 新增 SCENARIO_DIALOGUE
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'SCENARIO_DIALOGUE'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
    ) THEN
        ALTER TYPE contenttype ADD VALUE 'SCENARIO_DIALOGUE';
    END IF;
END
$$;
```

#### 資料遷移

```sql
-- 將舊類型資料遷移到新類型
UPDATE contents
SET type = 'EXAMPLE_SENTENCES'
WHERE type = 'READING_ASSESSMENT';

UPDATE contents
SET type = 'VOCABULARY_SET'
WHERE type = 'SENTENCE_MAKING';
```

### 6.2 Assignment 表變更

#### 新增欄位

```sql
-- 作答模式（例句集專用）
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS practice_mode VARCHAR(20) DEFAULT 'reading';
-- 值：'reading' (例句朗讀) / 'rearrangement' (例句重組)

-- 每題時間限制（秒）
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS time_limit_per_question INTEGER DEFAULT 40;
-- 值：10 / 20 / 30 / 40

-- 是否打亂題目順序
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS shuffle_questions BOOLEAN DEFAULT FALSE;

-- 是否播放音檔（例句重組專用）
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS play_audio BOOLEAN DEFAULT FALSE;

-- 分數記錄分類
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS score_category VARCHAR(20) DEFAULT NULL;
-- 值：'speaking' / 'listening' / 'writing'
-- 根據 practice_mode 和 play_audio 自動設定
```

### 6.3 ContentItem 表變更

#### 新增驗證欄位

```sql
-- 單字數量（建立時自動計算）
ALTER TABLE content_items
ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT NULL;

-- 允許錯誤次數（根據 word_count 自動計算）
ALTER TABLE content_items
ADD COLUMN IF NOT EXISTS max_errors INTEGER DEFAULT NULL;
```

### 6.4 StudentItemProgress 表變更

#### 新增例句重組專用欄位

```sql
-- 錯誤次數
ALTER TABLE student_item_progress
ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0;

-- 已正確選擇的單字數量
ALTER TABLE student_item_progress
ADD COLUMN IF NOT EXISTS correct_word_count INTEGER DEFAULT 0;

-- 是否選擇重新挑戰
ALTER TABLE student_item_progress
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- 預期分數（作答過程中持續更新）
ALTER TABLE student_item_progress
ADD COLUMN IF NOT EXISTS expected_score DECIMAL(5,2) DEFAULT 0;

-- 是否因時間到期結束
ALTER TABLE student_item_progress
ADD COLUMN IF NOT EXISTS timeout_ended BOOLEAN DEFAULT FALSE;
```

### 6.5 完整 Schema 圖示

```
┌─────────────────────────────────────────────────────────────────┐
│                        Assignment                                │
├─────────────────────────────────────────────────────────────────┤
│ + practice_mode: VARCHAR(20)        -- 'reading'/'rearrangement'│
│ + time_limit_per_question: INTEGER  -- 10/20/30/40 秒           │
│ + shuffle_questions: BOOLEAN        -- 是否打亂順序              │
│ + play_audio: BOOLEAN               -- 是否播放音檔（重組專用）   │
│ + score_category: VARCHAR(20)       -- 分數記錄分類              │
│ - answer_mode: VARCHAR(20)          -- [保留相容] 舊欄位         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ContentItem                                  │
├─────────────────────────────────────────────────────────────────┤
│ + word_count: INTEGER               -- 單字數量                  │
│ + max_errors: INTEGER               -- 允許錯誤次數              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  StudentItemProgress                             │
├─────────────────────────────────────────────────────────────────┤
│ + error_count: INTEGER              -- 錯誤次數                  │
│ + correct_word_count: INTEGER       -- 已正確選擇的單字數         │
│ + retry_count: INTEGER              -- 重新挑戰次數              │
│ + expected_score: DECIMAL(5,2)      -- 預期分數                  │
│ + timeout_ended: BOOLEAN            -- 是否超時結束              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. API 變更

### 7.1 Content 建立 API

#### 請求格式更新

```python
class ContentCreate(BaseModel):
    type: str  # "example_sentences" / "vocabulary_set" / etc.
    title: str
    items: List[ContentItemCreate]
    # ... 其他欄位

class ContentItemCreate(BaseModel):
    text: str  # 句子內容
    translation: Optional[str] = None
    audio_url: Optional[str] = None
    # word_count 和 max_errors 由後端自動計算
```

#### 驗證邏輯

```python
@router.post("/lessons/{lesson_id}/contents")
async def create_content(lesson_id: int, content: ContentCreate):
    # 驗證句子長度
    for item in content.items:
        word_count = len(item.text.strip().split())
        if word_count < 2 or word_count > 25:
            raise HTTPException(
                status_code=400,
                detail=f"句子須為 2-25 個單字，目前 {word_count} 個"
            )
```

### 7.2 Assignment 建立 API

#### 請求格式更新

```python
class CreateAssignmentRequest(BaseModel):
    title: str
    description: Optional[str] = None
    classroom_id: int
    content_ids: List[int]
    student_ids: List[int] = []
    due_date: Optional[datetime] = None

    # 新增欄位（例句集專用）
    practice_mode: str = "reading"  # 'reading' / 'rearrangement'
    time_limit_per_question: int = 40  # 10/20/30/40
    shuffle_questions: bool = False
    play_audio: bool = False  # 僅 rearrangement 有效
```

#### 分數分類自動設定

```python
def determine_score_category(practice_mode: str, play_audio: bool) -> str:
    if practice_mode == "reading":
        return "speaking"
    elif practice_mode == "rearrangement":
        return "listening" if play_audio else "writing"
    return None
```

### 7.3 答題提交 API

#### 例句重組答題

```python
class RearrangementAnswerRequest(BaseModel):
    content_item_id: int
    selected_word_index: int  # 學生選擇的單字索引

class RearrangementAnswerResponse(BaseModel):
    is_correct: bool
    error_count: int
    max_errors: int
    expected_score: float
    challenge_failed: bool  # 達到錯誤上限
    completed: bool  # 是否完成所有單字
```

```python
@router.post("/assignments/{assignment_id}/submit-rearrangement")
async def submit_rearrangement_answer(
    assignment_id: int,
    answer: RearrangementAnswerRequest
):
    # 1. 驗證答案正確性
    # 2. 更新 error_count 和 expected_score
    # 3. 檢查是否達到錯誤上限
    # 4. 返回結果
```

#### 重新挑戰 API

```python
@router.post("/assignments/{assignment_id}/items/{item_id}/retry")
async def retry_item(assignment_id: int, item_id: int):
    """重置該題目的作答狀態"""
    # 重置 error_count, correct_word_count, expected_score
    # retry_count + 1
```

---

## 8. 前端變更

### 8.1 ContentTypeDialog 更新

```typescript
const contentTypes: ContentType[] = [
  {
    type: "example_sentences",
    name: "例句集",
    icon: "📝",
    description: "建立例句供學生練習朗讀或重組",
    recommended: true,
    disabled: false,
  },
  {
    type: "vocabulary_set",
    name: "單字集",
    icon: "📚",
    description: "建立單字集供學生記憶練習",
    disabled: true,  // Phase 2
    comingSoon: true,
  },
  {
    type: "multiple_choice",
    name: "單選題庫",
    icon: "✅",
    description: "建立單選題目供學生測驗",
    disabled: true,  // Phase 2
    comingSoon: true,
  },
  {
    type: "scenario_dialogue",
    name: "情境對話",
    icon: "💬",
    description: "建立情境對話供學生練習",
    disabled: true,  // Phase 2
    comingSoon: true,
  },
];
```

### 8.2 AssignmentDialog 更新

#### 新增作答模式選擇步驟

```
步驟 1: 選擇內容（現有）
    ↓
步驟 2: 選擇作答模式（新增 - 僅例句集）
    ├── 例句朗讀
    └── 例句重組
    ↓
步驟 3: 設定細節（新增）
    ├── 共通選項
    │   ├── 每題答題時間：[10秒 ▼] [20秒] [30秒] [40秒]
    │   └── 打亂順序：[是] [否 ▼]
    │
    └── 例句重組專用
        └── 播放音檔：[是（聽力模式）] [否（寫作模式）▼]
    ↓
步驟 4: 選擇學生、設定截止日期（現有）
```

#### 組件結構

```typescript
// 新增作答模式選擇組件
const PracticeModeSelector: React.FC<{
  mode: PracticeMode;
  onChange: (mode: PracticeMode) => void;
}> = ({ mode, onChange }) => {
  return (
    <div className="practice-mode-selector">
      <h4>選擇作答模式</h4>
      <RadioGroup value={mode} onChange={onChange}>
        <RadioButton value="reading">
          <Icon name="microphone" /> 例句朗讀
          <span className="description">學生朗讀句子，AI 評分</span>
        </RadioButton>
        <RadioButton value="rearrangement">
          <Icon name="shuffle" /> 例句重組
          <span className="description">學生排列打亂的單字</span>
        </RadioButton>
      </RadioGroup>
    </div>
  );
};

// 新增設定細節組件
const AssignmentSettings: React.FC<{
  practiceMode: PracticeMode;
  settings: AssignmentSettings;
  onChange: (settings: AssignmentSettings) => void;
}> = ({ practiceMode, settings, onChange }) => {
  return (
    <div className="assignment-settings">
      <h4>作業設定</h4>

      {/* 共通選項 */}
      <FormField label="每題答題時間">
        <Select
          value={settings.timeLimitPerQuestion}
          onChange={(v) => onChange({ ...settings, timeLimitPerQuestion: v })}
        >
          <Option value={10}>10 秒</Option>
          <Option value={20}>20 秒</Option>
          <Option value={30}>30 秒</Option>
          <Option value={40}>40 秒（預設）</Option>
        </Select>
      </FormField>

      <FormField label="打亂題目順序">
        <Switch
          checked={settings.shuffleQuestions}
          onChange={(v) => onChange({ ...settings, shuffleQuestions: v })}
        />
      </FormField>

      {/* 例句重組專用選項 */}
      {practiceMode === 'rearrangement' && (
        <FormField label="播放音檔">
          <RadioGroup
            value={settings.playAudio}
            onChange={(v) => onChange({ ...settings, playAudio: v })}
          >
            <RadioButton value={true}>
              是（聽力模式）
              <span className="hint">分數記錄至【聽力】</span>
            </RadioButton>
            <RadioButton value={false}>
              否（寫作模式）
              <span className="hint">分數記錄至【寫作】</span>
            </RadioButton>
          </RadioGroup>
        </FormField>
      )}

      {practiceMode === 'reading' && (
        <div className="info-box">
          ℹ️ 例句朗讀模式的分數將記錄至【口說】分類
        </div>
      )}
    </div>
  );
};
```

### 8.3 學生活動組件

#### 例句重組活動

```typescript
// 新增例句重組活動組件
const RearrangementActivity: React.FC<{
  assignmentId: number;
  contentItemId: number;
  sentence: string;
  playAudio: boolean;
  timeLimit: number;
  onComplete: (result: RearrangementResult) => void;
}> = ({ assignmentId, contentItemId, sentence, playAudio, timeLimit, onComplete }) => {
  const [shuffledWords, setShuffledWords] = useState<string[]>([]);
  const [selectedWords, setSelectedWords] = useState<string[]>([]);
  const [errorCount, setErrorCount] = useState(0);
  const [expectedScore, setExpectedScore] = useState(100);
  const [timeRemaining, setTimeRemaining] = useState(timeLimit);
  const [challengeFailed, setChallengeFailed] = useState(false);

  // 計算相關數值
  const wordCount = sentence.split(' ').length;
  const maxErrors = wordCount <= 10 ? 3 : 5;
  const pointsPerWord = Math.floor(100 / wordCount);

  // ... 實作選字、計分、時間倒數邏輯

  return (
    <div className="rearrangement-activity">
      {/* 進度指示 */}
      <ProgressBar current={selectedWords.length} total={wordCount} />

      {/* 時間倒數 */}
      <Timer remaining={timeRemaining} />

      {/* 音檔播放（若啟用） */}
      {playAudio && <AudioPlayer src={audioUrl} />}

      {/* 已選擇的單字 */}
      <div className="selected-words">
        {selectedWords.map((word, i) => (
          <WordChip key={i} word={word} correct />
        ))}
      </div>

      {/* 可選擇的單字池 */}
      <div className="word-pool">
        {shuffledWords.map((word, i) => (
          <WordChip
            key={i}
            word={word}
            onClick={() => handleWordSelect(i)}
            disabled={selectedWords.includes(word)}
          />
        ))}
      </div>

      {/* 分數顯示 */}
      <div className="score-display">
        預期分數: {expectedScore} / 錯誤: {errorCount}/{maxErrors}
      </div>

      {/* 挑戰失敗對話框 */}
      {challengeFailed && (
        <ChallengeFailedDialog
          onRetry={() => handleRetry()}
          onContinue={() => handleContinue()}
        />
      )}
    </div>
  );
};
```

### 8.4 Type 定義更新

```typescript
// frontend/src/types/index.ts

export type ContentType =
  | 'example_sentences'
  | 'vocabulary_set'
  | 'multiple_choice'
  | 'scenario_dialogue';

export type PracticeMode = 'reading' | 'rearrangement';

export type ScoreCategory = 'speaking' | 'listening' | 'writing';

export interface AssignmentSettings {
  practiceMode: PracticeMode;
  timeLimitPerQuestion: 10 | 20 | 30 | 40;
  shuffleQuestions: boolean;
  playAudio: boolean;  // 僅 rearrangement 有效
  scoreCategory: ScoreCategory;  // 自動計算
}

export interface RearrangementResult {
  contentItemId: number;
  isCorrect: boolean;
  errorCount: number;
  expectedScore: number;
  completed: boolean;
  timeoutEnded: boolean;
}
```

---

## 9. Migration 計劃

### 9.1 Migration 檔案列表

```
backend/alembic/versions/
├── 202512XX_XXXX_add_new_content_types.py          # 1. 新增 Enum 值
├── 202512XX_XXXX_add_assignment_settings_columns.py # 2. Assignment 新欄位
├── 202512XX_XXXX_add_content_item_word_count.py    # 3. ContentItem 新欄位
├── 202512XX_XXXX_add_student_progress_columns.py   # 4. StudentItemProgress 新欄位
└── 202512XX_XXXX_migrate_content_types.py          # 5. 資料遷移
```

### 9.2 Migration 1: 新增 Enum 值

```python
# 202512XX_XXXX_add_new_content_types.py
def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'EXAMPLE_SENTENCES'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'EXAMPLE_SENTENCES';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'VOCABULARY_SET'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'VOCABULARY_SET';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'MULTIPLE_CHOICE'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'MULTIPLE_CHOICE';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'SCENARIO_DIALOGUE'
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'contenttype')
            ) THEN
                ALTER TYPE contenttype ADD VALUE 'SCENARIO_DIALOGUE';
            END IF;
        END
        $$;
    """)

def downgrade() -> None:
    pass  # Enum 值無法刪除，保持現狀
```

### 9.3 Migration 2: Assignment 新欄位

```python
# 202512XX_XXXX_add_assignment_settings_columns.py
def upgrade() -> None:
    op.execute("""
        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS practice_mode VARCHAR(20) DEFAULT 'reading';

        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS time_limit_per_question INTEGER DEFAULT 40;

        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS shuffle_questions BOOLEAN DEFAULT FALSE;

        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS play_audio BOOLEAN DEFAULT FALSE;

        ALTER TABLE assignments
        ADD COLUMN IF NOT EXISTS score_category VARCHAR(20) DEFAULT NULL;
    """)

def downgrade() -> None:
    pass  # 遵循 Additive 原則，不刪除
```

### 9.4 Migration 3: ContentItem 新欄位

```python
# 202512XX_XXXX_add_content_item_word_count.py
def upgrade() -> None:
    op.execute("""
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT NULL;

        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS max_errors INTEGER DEFAULT NULL;
    """)

    # 更新現有資料的 word_count
    op.execute("""
        UPDATE content_items
        SET word_count = array_length(string_to_array(trim(text), ' '), 1)
        WHERE word_count IS NULL;
    """)

    # 根據 word_count 計算 max_errors
    op.execute("""
        UPDATE content_items
        SET max_errors = CASE
            WHEN word_count <= 10 THEN 3
            ELSE 5
        END
        WHERE max_errors IS NULL;
    """)

def downgrade() -> None:
    pass
```

### 9.5 Migration 4: StudentItemProgress 新欄位

```python
# 202512XX_XXXX_add_student_progress_columns.py
def upgrade() -> None:
    op.execute("""
        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0;

        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS correct_word_count INTEGER DEFAULT 0;

        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS expected_score DECIMAL(5,2) DEFAULT 0;

        ALTER TABLE student_item_progress
        ADD COLUMN IF NOT EXISTS timeout_ended BOOLEAN DEFAULT FALSE;
    """)

def downgrade() -> None:
    pass
```

### 9.6 Migration 5: 資料遷移

```python
# 202512XX_XXXX_migrate_content_types.py
def upgrade() -> None:
    # 將 READING_ASSESSMENT 遷移到 EXAMPLE_SENTENCES
    op.execute("""
        UPDATE contents
        SET type = 'EXAMPLE_SENTENCES'
        WHERE type = 'READING_ASSESSMENT';
    """)

    # 將 SENTENCE_MAKING 遷移到 VOCABULARY_SET
    op.execute("""
        UPDATE contents
        SET type = 'VOCABULARY_SET'
        WHERE type = 'SENTENCE_MAKING';
    """)

    # 更新現有 Assignment 的設定
    # 原本的 answer_mode 對應到新的 practice_mode 和 play_audio
    op.execute("""
        UPDATE assignments
        SET
            practice_mode = 'reading',
            score_category = 'speaking'
        WHERE answer_mode IS NULL OR answer_mode = 'writing';
    """)

def downgrade() -> None:
    pass  # 不可逆遷移
```

---

## 10. 開發階段

### Phase 1: 資料庫準備

- [ ] 建立所有 Migration 檔案
- [ ] 在 develop 環境測試 Migration
- [ ] 更新 Python Models（ContentType Enum）
- [ ] 更新相關 Pydantic Schemas

### Phase 2: 後端 API

- [ ] 更新 Content 建立 API（驗證句子長度）
- [ ] 更新 Assignment 建立 API（新增設定欄位）
- [ ] 實作例句重組答題 API
- [ ] 實作重新挑戰 API
- [ ] 實作計分邏輯

### Phase 3: 前端組件

- [ ] 更新 ContentTypeDialog
- [ ] 實作 PracticeModeSelector 組件
- [ ] 實作 AssignmentSettings 組件
- [ ] 更新 AssignmentDialog 流程
- [ ] 實作 RearrangementActivity 組件

### Phase 4: 測試與驗證

- [ ] 單元測試：計分邏輯
- [ ] 整合測試：完整作答流程
- [ ] E2E 測試：學生作答體驗
- [ ] 效能測試：大量題目情境

### Phase 5: 資料遷移

- [ ] 備份現有資料
- [ ] 執行資料遷移 Migration
- [ ] 驗證遷移結果
- [ ] 更新 Seed Data

---

## 11. 決策記錄（已確認）

> **更新日期**: 2025-12-02

### ✅ 決策 1: 舊類型 Enum 值處理

**問題描述**：
PostgreSQL 的 Enum 類型無法刪除舊值（`READING_ASSESSMENT`、`SENTENCE_MAKING`）。

**決策**：選項 1 - **保留舊值**
- 在程式碼中標記為 deprecated
- 資料庫 Enum 仍保留這些值
- 最簡單且向下相容

---

### ✅ 決策 2: 現有資料遷移策略

**問題描述**：
現有的 `READING_ASSESSMENT` 內容遷移到 `EXAMPLE_SENTENCES` 後，相關的作業 (Assignment) 如何處理？

**決策**：
- 原本的 `READING_ASSESSMENT`（朗讀評測）必須保持正常顯示和作答
- `SENTENCE_MAKING`（句子模組）尚未正式上線，有影響沒關係
- 現有作業預設 `practice_mode = 'reading'`
- 學生進度記錄不需變更

---

### ✅ 決策 3: 打亂順序的定義

**問題釐清**：
「是否打亂順序」指的是**例句的出現順序**，而非例句重組時單字的打亂。

**定義**：
- `shuffle_questions = true`：假設內容有 20 個例句，這 20 個例句的**出題順序**是隨機的
- `shuffle_questions = false`：例句按照建立時的 `order_index` 順序出現

**例句重組的單字打亂**：
- 這是例句重組模式的固有行為，**永遠會打亂**單字順序
- 使用純隨機打亂演算法

---

### ✅ 決策 4: 音檔播放時機

**問題描述**：
例句重組的「播放音檔」選項，音檔何時播放？

**決策**：選項 3 - **限時內無限次播放**
- 在設定的答題時間內，學生可無限次播放音檔
- 降低聽力障礙，讓學生專注於理解內容
- 時間到期後自動結束作答

---

### ✅ 決策 5: 繼續完成後的計分邏輯

**問題描述**：
學生選擇「繼續完成」後，最終分數如何計算？

**決策**：**扣分不回復 + 保底分機制**

規則：
1. 選擇「繼續完成」：扣分不回復，繼續累計扣分
2. 選擇「重新挑戰」：分數歸零重新開始計分
3. 保底分：只要學生**完成作答**，最低保留 `floor(100/題數)` 分
4. 未完成（跳題或超時未作答完）：該題 0 分

**範例**：
- 5 個單字的句子（每字 20 分）
- 錯了 4 次，扣 80 分，預期分數 = 20 分
- 選「繼續完成」→ 完成後最終分數 = max(20, floor(100/作業題數)) 分
- 選「重新挑戰」→ 分數歸零，重新計分

---

### ✅ 決策 6: 合併步驟的 UI 設計

**問題描述**：
「選擇作答模式」和「設定細節」兩個步驟是否可以合併成一個畫面？

**決策**：**先分開實作**
- 保持步驟清晰
- 後續根據用戶反饋評估是否合併
- 可在未來迭代中優化

---

### ✅ 決策 7: 向後相容性

**問題描述**：
現有前端/後端如何處理新舊 ContentType 值的混合情況？

**決策**：
1. 資料庫遷移完成後，統一使用新值
2. API 層加入相容性轉換邏輯（雙向映射）
3. 前端必須支援新舊兩種值，確認所有相關程式碼都有 cover

**API 相容性轉換範例**：
```python
def normalize_content_type(content_type: str) -> str:
    """將舊的 ContentType 值轉換為新值"""
    mapping = {
        "READING_ASSESSMENT": "EXAMPLE_SENTENCES",
        "reading_assessment": "example_sentences",
        "SENTENCE_MAKING": "VOCABULARY_SET",
        "sentence_making": "vocabulary_set",
    }
    return mapping.get(content_type, content_type)
```

---

## 12. 原始問題參考（已關閉）

<details>
<summary>點擊展開原始問題記錄</summary>

（原始問題內容已移至決策記錄區）

</details>

---

## 📝 變更記錄

| 日期 | 版本 | 變更內容 |
|-----|------|---------|
| 2025-12-02 | v1.0 | 初版規劃文件 |
| 2025-12-02 | v1.1 | 確認所有待釐清問題的決策，更新第 11 節為決策記錄 |
