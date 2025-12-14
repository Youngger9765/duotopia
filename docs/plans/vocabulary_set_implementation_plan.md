# 單字集 (VOCABULARY_SET) 實作計劃

> ⚠️ **注意**：此功能目前為 **Phase 2**，尚未實作。
>
> 此文件保留完整實作計劃供未來開發參考。

---

## 概述

| 項目 | 說明 |
|------|------|
| ContentType | `VOCABULARY_SET` |
| 中文名稱 | 單字集 |
| 舊名稱 | SENTENCE_MAKING（已棄用） |
| 目前狀態 | ⏸️ Phase 2 - 尚未實作 |

---

## 📋 目錄

1. [功能概述](#功能概述)
2. [⚠️ 向後兼容性考量](#向後兼容性考量)
3. [資料庫架構設計](#資料庫架構設計)
4. [後端 API 設計](#後端-api-設計)
5. [前端組件設計](#前端組件設計)
6. [艾賓浩斯記憶曲線演算法](#艾賓浩斯記憶曲線演算法)
7. [實作優先順序](#實作優先順序)
8. [測試計劃](#測試計劃)

---

## 功能概述

### 🎯 核心功能

**造句練習**是一個結合艾賓浩斯記憶曲線的英文學習系統，支援兩種答題模式：

1. **聽力模式作答**
   - 播放單字音檔
   - 學生聽音檔後選擇單字組成句子
   - 適合聽力訓練和語音記憶

2. **寫作模式作答**
   - 不播放音檔
   - 學生純粹看題目選擇單字組成句子
   - 適合閱讀理解和文字記憶

### 🧠 艾賓浩斯記憶曲線整合

- 系統根據學生的記憶強度智能選擇練習單字
- 每次答題後更新記憶強度和下次複習時間
- 優先練習即將遺忘的單字
- 達到目標熟悉度後完成作業

---

## ⚠️ 向後兼容性考量

### 🎯 核心原則

**絕對不能影響現有的朗讀評測功能！**

造句練習是一個**新增功能**，而非修改功能。所有新增的代碼、資料庫欄位、API 都必須確保：
1. 不破壞現有朗讀評測作業的創建
2. 不破壞現有朗讀評測作業的顯示
3. 不破壞現有朗讀評測作業的答題流程
4. 不破壞現有學生作業數據

---

### 🔒 關鍵檢查點

#### 1. 資料庫層面

**✅ 正確做法**：
```sql
-- ✅ 添加欄位時必須設置預設值，確保現有資料不受影響
ALTER TABLE assignments ADD COLUMN IF NOT EXISTS
  answer_mode VARCHAR(20) DEFAULT 'writing' CHECK (answer_mode IN ('listening', 'writing'));
```

**❌ 錯誤做法**：
```sql
-- ❌ 不設置預設值會導致現有記錄出現 NULL
ALTER TABLE assignments ADD COLUMN answer_mode VARCHAR(20) NOT NULL;
```

**檢查清單**：
- [ ] `answer_mode` 欄位有預設值 `'writing'`
- [ ] 現有的朗讀評測作業自動設為 `'writing'` 模式（雖然不使用）
- [ ] 新增的表 (`user_word_progress`, `practice_sessions`, `practice_answers`) 不影響現有表
- [ ] 所有 Foreign Key 使用 `ON DELETE CASCADE` 避免孤兒記錄

#### 2. 後端 API 層面

**✅ 正確做法**：
```python
class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    classroom_id: int
    content_ids: List[int]
    student_ids: List[int] = []
    due_date: Optional[datetime] = None
    answer_mode: str = "writing"  # ✅ 有預設值，舊版前端不傳此參數也能正常運作
```

**❌ 錯誤做法**：
```python
class AssignmentCreate(BaseModel):
    title: str
    answer_mode: str  # ❌ 必填欄位會導致舊版前端無法創建作業
```

**檢查清單**：
- [ ] `answer_mode` 參數為選填，有預設值
- [ ] 創建作業 API 在沒有 `answer_mode` 時預設為 `'writing'`
- [ ] 回傳的作業資料包含 `answer_mode`，但舊版前端可忽略此欄位
- [ ] 不修改任何現有 API 的必填參數

#### 3. 前端路由層面

**✅ 正確做法**：
```typescript
// StudentActivityPageContent.tsx
const renderActivity = () => {
  const contentType = assignment.content?.type;

  if (contentType === "reading_assessment") {
    // ✅ 朗讀評測走原本的 ReadingAssessmentTemplate
    return <ReadingAssessmentTemplate {...props} />;
  }

  if (contentType === "sentence_making") {
    // ✅ 造句練習走新的 SentenceMakingActivity
    return <SentenceMakingActivity {...props} />;
  }

  // ✅ 未來的新類型...
  return <DefaultTemplate />;
};
```

**❌ 錯誤做法**：
```typescript
// ❌ 不要根據 answer_mode 路由，這會影響朗讀評測
if (assignment.answer_mode === "listening") {
  return <ListeningModeTemplate />;  // ❌ 錯誤！朗讀評測也可能有 answer_mode
}
```

**檢查清單**：
- [ ] 路由邏輯只根據 `content.type` 判斷，不看 `answer_mode`
- [ ] `answer_mode` 只在 `sentence_making` 類型內部使用
- [ ] 朗讀評測的組件完全不受 `answer_mode` 影響
- [ ] 預設情況下回退到朗讀評測（向後兼容）

#### 4. 學生作業實例層面

**✅ 正確做法**：
```python
# 創建學生作業時，根據 content.type 決定處理方式
if content.type == ContentType.READING_ASSESSMENT:
    # ✅ 朗讀評測使用原本的邏輯
    student_content_progress = StudentContentProgress(
        student_assignment_id=student_assignment.id,
        content_id=content.id,
        status=AssignmentStatusEnum.NOT_STARTED
        # 不創建 user_word_progress，不影響現有流程
    )
elif content.type == ContentType.SENTENCE_MAKING:
    # ✅ 造句練習才使用新的記憶曲線系統
    student_content_progress = StudentContentProgress(
        student_assignment_id=student_assignment.id,
        content_id=content.id,
        status=AssignmentStatusEnum.NOT_STARTED
    )
    # 只有造句練習才初始化 user_word_progress
```

**❌ 錯誤做法**：
```python
# ❌ 不要對所有作業都創建 user_word_progress
for content in contents:
    # 為所有內容創建記憶進度（包括朗讀評測）❌
    user_word_progress = UserWordProgress(...)
```

**檢查清單**：
- [ ] `user_word_progress` 只為 `sentence_making` 類型創建
- [ ] 朗讀評測作業完全不使用記憶曲線系統
- [ ] 學生作業狀態更新邏輯根據類型分流
- [ ] 分數計算邏輯根據類型分流

#### 5. 前端組件層面

**✅ 正確做法**：
```typescript
// AssignmentDialog.tsx
{getSelectedContentType() === "sentence_making" && (
  <div className="mt-2 pt-2 border-t border-blue-200">
    {/* ✅ 只在造句練習時顯示答題模式選擇器 */}
    <div className="text-xs font-medium text-blue-900 mb-2">
      答題模式：
    </div>
    <RadioGroup value={formData.answer_mode} ...>
      {/* Radio 選項 */}
    </RadioGroup>
  </div>
)}
```

**❌ 錯誤做法**：
```typescript
// ❌ 不要對所有作業類型都顯示答題模式
<RadioGroup value={formData.answer_mode}>
  {/* 這會在朗讀評測時也顯示，造成困惑 */}
</RadioGroup>
```

**檢查清單**：
- [ ] 答題模式選擇器只在 `sentence_making` 類型顯示
- [ ] 朗讀評測的表單不包含 `answer_mode` 選項
- [ ] UI 文案明確區分朗讀評測和造句練習
- [ ] 作業卡片顯示正確的類型標籤

---

### 🧪 向後兼容性測試場景

#### Scenario 1: 現有朗讀評測作業不受影響

**測試步驟**：
1. 使用新版代碼啟動系統
2. 查詢資料庫中現有的朗讀評測作業
3. 確認 `answer_mode` 欄位自動填充為 `'writing'`
4. 學生打開現有的朗讀評測作業
5. 確認顯示原本的朗讀評測介面（不是造句練習介面）
6. 學生完成作業並提交
7. 確認評分和記錄正常

**預期結果**：
- ✅ 所有現有作業正常運作
- ✅ 學生看不到任何變化
- ✅ 老師看不到任何變化
- ✅ 資料庫記錄正常

#### Scenario 2: 創建新的朗讀評測作業

**測試步驟**：
1. 老師創建新的朗讀評測作業
2. 選擇 `content.type = "reading_assessment"`
3. 確認作業摘要中**不顯示**答題模式選擇器
4. 提交作業
5. 學生打開作業
6. 確認顯示朗讀評測介面

**預期結果**：
- ✅ 朗讀評測作業創建流程不變
- ✅ 不會出現答題模式選擇器
- ✅ 學生端正常顯示朗讀評測

#### Scenario 3: 創建新的造句練習作業

**測試步驟**：
1. 老師創建新的造句練習作業
2. 選擇 `content.type = "sentence_making"`
3. 確認作業摘要中**顯示**答題模式選擇器
4. 選擇「寫作模式」或「聽力模式」
5. 提交作業
6. 學生打開作業
7. 確認顯示對應的造句練習介面

**預期結果**：
- ✅ 新功能正常運作
- ✅ 不影響朗讀評測

#### Scenario 4: 混合作業（包含朗讀評測和造句練習）

**測試步驟**：
1. 老師在同一個作業中選擇：
   - 2 個朗讀評測內容
   - 2 個造句練習內容
2. 由於類型限制，應該**無法同時選擇**
3. 確認 UI 正確禁用不同類型的內容

**預期結果**：
- ✅ 類型限制機制正常運作
- ✅ 不會創建混合類型作業
- ✅ 避免了複雜的相容性問題

#### Scenario 5: API 向後兼容性

**測試步驟**：
1. 使用舊版前端（沒有 `answer_mode` 參數）
2. 調用 `/api/teachers/assignments/create` API
3. Request Body 不包含 `answer_mode`
4. 確認作業成功創建
5. 確認 `answer_mode` 自動設為 `'writing'`

**預期結果**：
- ✅ 舊版前端繼續正常運作
- ✅ 不會出現驗證錯誤
- ✅ 預設值正確

---

### 📝 Migration 安全性檢查

在執行資料庫 Migration 前，必須確認：

```bash
# 1. 備份資料庫
pg_dump duotopia_production > backup_before_sentence_making_$(date +%Y%m%d).sql

# 2. 在測試環境先執行
alembic upgrade head --sql > migration.sql
# 檢查 SQL 是否包含 DROP、TRUNCATE 等危險指令

# 3. 確認預設值
grep "DEFAULT" migration.sql
# 應該看到：answer_mode VARCHAR(20) DEFAULT 'writing'

# 4. 在測試環境執行並驗證
alembic upgrade head
# 檢查現有資料是否正常

# 5. 執行向後兼容性測試（上述 5 個 Scenarios）

# 6. 正式環境執行（維護窗口）
alembic upgrade head
```

---

### 🚨 紅線規則（絕對禁止）

1. ❌ **絕對不要**修改現有的 `reading_assessment` 相關代碼邏輯
2. ❌ **絕對不要**在朗讀評測流程中調用記憶曲線相關函數
3. ❌ **絕對不要**讓 `answer_mode` 成為必填欄位
4. ❌ **絕對不要**根據 `answer_mode` 路由所有作業類型
5. ❌ **絕對不要**在沒有備份的情況下執行 Migration
6. ❌ **絕對不要**刪除或重命名現有的資料庫欄位
7. ❌ **絕對不要**修改現有 API 的回傳格式（只能新增欄位）

---

### ✅ 安全實作檢查清單

**在開始 Phase 1 之前**：
- [ ] 已閱讀並理解所有向後兼容性要求
- [ ] 已規劃 Migration 回滾策略
- [ ] 已準備測試環境和資料

**Phase 1 完成後**：
- [ ] 資料庫欄位有正確的預設值
- [ ] 現有資料的 `answer_mode` 已自動填充
- [ ] Migration 可以安全回滾

**Phase 2 完成後**：
- [ ] API 參數都是選填
- [ ] 舊版前端測試通過
- [ ] 朗讀評測作業創建測試通過

**Phase 3 完成後**：
- [ ] 路由邏輯只根據 `content.type`
- [ ] 朗讀評測介面完全不變
- [ ] UI 條件渲染正確

**上線前**：
- [ ] 所有 5 個向後兼容性測試場景通過
- [ ] 資料庫已備份
- [ ] 回滾計劃已準備
- [ ] 監控告警已設置

---

## 資料庫架構設計

### 📊 Schema 概覽

```
┌─────────────────┐
│   assignments   │  作業主表
└────────┬────────┘
         │
         ├──────────┐
         │          │
┌────────▼────────┐ │
│ student_        │ │
│ assignments     │ │  學生作業實例
└────────┬────────┘ │
         │          │
┌────────▼──────────▼──────┐
│ user_word_progress       │  記憶強度追蹤（核心）
└──────────────────────────┘
         │
┌────────▼────────┐
│ practice_       │  練習記錄
│ sessions        │
└────────┬────────┘
         │
┌────────▼────────┐
│ practice_       │  答題詳細記錄
│ answers         │
└─────────────────┘
```

### 1. assignments 表（作業主表）- 需要新增欄位

```sql
ALTER TABLE assignments ADD COLUMN IF NOT EXISTS
  answer_mode VARCHAR(20) DEFAULT 'writing' CHECK (answer_mode IN ('listening', 'writing'));

-- 答題模式：'listening' 聽力模式，'writing' 寫作模式
-- 預設為 'writing'
```

**說明**：
- 作業創建時由老師選擇答題模式
- 同一個作業的所有學生使用相同的答題模式

### 2. user_word_progress 表（學生單字記憶進度）- 新增

```sql
CREATE TABLE IF NOT EXISTS user_word_progress (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  student_assignment_id INTEGER NOT NULL REFERENCES student_assignments(id) ON DELETE CASCADE,
  content_item_id INTEGER NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,

  -- 艾賓浩斯記憶曲線相關欄位
  memory_strength DECIMAL(5,4) DEFAULT 0 CHECK (memory_strength >= 0 AND memory_strength <= 1),
  -- 記憶強度 (0-1)，0 表示完全不記得，1 表示完全記住

  repetition_count INTEGER DEFAULT 0,
  -- 連續答對次數（SuperMemo-2 演算法用）

  correct_count INTEGER DEFAULT 0,
  -- 累計答對次數

  incorrect_count INTEGER DEFAULT 0,
  -- 累計答錯次數

  last_review_at TIMESTAMPTZ,
  -- 最後複習時間

  next_review_at TIMESTAMPTZ,
  -- 下次建議複習時間（根據遺忘曲線計算）

  easiness_factor DECIMAL(3,2) DEFAULT 2.5 CHECK (easiness_factor >= 1.3),
  -- 難易度因子（SM-2 演算法），1.3-2.5，數字越大表示越容易記住

  interval_days DECIMAL(10,2) DEFAULT 1,
  -- 目前複習間隔天數

  -- 統計資料
  total_attempts INTEGER DEFAULT 0,
  -- 總嘗試次數

  accuracy_rate DECIMAL(5,4) DEFAULT 0,
  -- 正確率 = correct_count / total_attempts

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(student_assignment_id, content_item_id)
  -- 確保每個學生作業中的每個 content_item 只有一條記錄
);

-- 索引優化
CREATE INDEX idx_user_word_progress_student ON user_word_progress(student_id, student_assignment_id);
CREATE INDEX idx_user_word_progress_next_review ON user_word_progress(student_assignment_id, next_review_at);
CREATE INDEX idx_user_word_progress_memory ON user_word_progress(memory_strength);
```

### 3. practice_sessions 表（練習記錄）- 新增

```sql
CREATE TABLE IF NOT EXISTS practice_sessions (
  id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  student_assignment_id INTEGER NOT NULL REFERENCES student_assignments(id) ON DELETE CASCADE,

  -- 練習模式
  practice_mode VARCHAR(20) NOT NULL CHECK (practice_mode IN ('listening', 'writing')),

  -- 本次練習統計
  words_practiced INTEGER NOT NULL DEFAULT 0,
  -- 本次練習的單字數（通常是 10 個）

  correct_count INTEGER DEFAULT 0,
  -- 本次練習答對題數

  total_time_seconds INTEGER DEFAULT 0,
  -- 總花費時間（秒）

  -- 時間戳記
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_practice_sessions_student ON practice_sessions(student_id, student_assignment_id);
CREATE INDEX idx_practice_sessions_started ON practice_sessions(started_at);
```

### 4. practice_answers 表（答題詳細記錄）- 新增

```sql
CREATE TABLE IF NOT EXISTS practice_answers (
  id SERIAL PRIMARY KEY,
  practice_session_id INTEGER NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
  content_item_id INTEGER NOT NULL REFERENCES content_items(id),

  -- 答題結果
  is_correct BOOLEAN NOT NULL,
  time_spent_seconds INTEGER DEFAULT 0,

  -- 學生答案（JSON 格式儲存）
  answer_data JSONB,
  -- 例如: {"selected_words": ["How", "are", "you"], "attempts": 3}

  -- 時間戳記
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_practice_answers_session ON practice_answers(practice_session_id);
CREATE INDEX idx_practice_answers_item ON practice_answers(content_item_id);
```

### 5. content_items 表（內容項目）- 已存在，需確認欄位

```sql
-- 確認 content_items 表有以下欄位：
-- - id
-- - content_id
-- - text (單字)
-- - translation (中文翻譯)
-- - example_sentence (例句)
-- - example_sentence_translation (例句中文翻譯)
-- - audio_url (音檔 URL)
-- - order_index (排序)
```

---

## 後端 API 設計

### 🔌 API 端點列表

#### 1. 創建作業（已存在，需修改）

**端點**: `POST /api/teachers/assignments/create`

**Request Body**:
```json
{
  "title": "Week 1 Vocabulary",
  "description": "Practice common words",
  "classroom_id": 1,
  "content_ids": [1, 2, 3],
  "student_ids": [10, 11, 12],
  "due_date": "2025-12-01T00:00:00Z",
  "answer_mode": "listening"  // ✨ 新增欄位
}
```

**修改位置**: `/backend/routers/teachers.py`

```python
class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    classroom_id: int
    content_ids: List[int]
    student_ids: List[int] = []
    due_date: Optional[datetime] = None
    answer_mode: str = "writing"  # ✨ 新增：答題模式，預設寫作模式
```

#### 2. 獲取練習題目（新增）

**端點**: `GET /api/students/assignments/{assignment_id}/practice-words`

**功能**: 根據艾賓浩斯曲線選擇 10 個需要練習的單字

**Response**:
```json
{
  "session_id": 123,
  "answer_mode": "listening",
  "words": [
    {
      "content_item_id": 45,
      "text": "apple",
      "translation": "蘋果",
      "example_sentence": "I eat an apple every day.",
      "example_sentence_translation": "我每天吃一個蘋果。",
      "audio_url": "https://storage.../apple.mp3",
      "memory_strength": 0.3,
      "priority_score": 75
    }
    // ... 9 more words
  ]
}
```

**實作邏輯**:
```python
@router.get("/assignments/{assignment_id}/practice-words")
async def get_practice_words(
    assignment_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    # 1. 取得學生作業實例
    student_assignment = db.query(StudentAssignment).filter(
        StudentAssignment.assignment_id == assignment_id,
        StudentAssignment.student_number == current_student.student_number
    ).first()

    if not student_assignment:
        raise HTTPException(404, "作業不存在")

    # 2. 創建新的練習 session
    practice_session = PracticeSession(
        student_id=current_student.id,
        student_assignment_id=student_assignment.id,
        practice_mode=student_assignment.assignment.answer_mode
    )
    db.add(practice_session)
    db.commit()

    # 3. 使用 SQL function 選擇 10 個單字
    words = db.execute(
        text("""
            SELECT * FROM get_words_for_practice(
                :student_assignment_id,
                :limit_count
            )
        """),
        {
            "student_assignment_id": student_assignment.id,
            "limit_count": 10
        }
    ).fetchall()

    return {
        "session_id": practice_session.id,
        "answer_mode": practice_session.practice_mode,
        "words": [dict(word) for word in words]
    }
```

#### 3. 提交答案（新增）

**端點**: `POST /api/students/practice-sessions/{session_id}/submit-answer`

**Request Body**:
```json
{
  "content_item_id": 45,
  "is_correct": true,
  "time_spent_seconds": 12,
  "answer_data": {
    "selected_words": ["I", "eat", "an", "apple", "every", "day"],
    "attempts": 2
  }
}
```

**Response**:
```json
{
  "success": true,
  "new_memory_strength": 0.65,
  "next_review_at": "2025-12-03T10:30:00Z"
}
```

**實作邏輯**:
```python
@router.post("/practice-sessions/{session_id}/submit-answer")
async def submit_answer(
    session_id: int,
    answer: PracticeAnswerSubmit,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    # 1. 驗證 session 屬於當前學生
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.student_id == current_student.id
    ).first()

    if not session:
        raise HTTPException(404, "練習 session 不存在")

    # 2. 記錄答案
    practice_answer = PracticeAnswer(
        practice_session_id=session_id,
        content_item_id=answer.content_item_id,
        is_correct=answer.is_correct,
        time_spent_seconds=answer.time_spent_seconds,
        answer_data=answer.answer_data
    )
    db.add(practice_answer)

    # 3. 更新記憶強度（使用 PostgreSQL function）
    result = db.execute(
        text("""
            SELECT * FROM update_memory_strength(
                :student_assignment_id,
                :content_item_id,
                :is_correct
            )
        """),
        {
            "student_assignment_id": session.student_assignment_id,
            "content_item_id": answer.content_item_id,
            "is_correct": answer.is_correct
        }
    ).fetchone()

    db.commit()

    return {
        "success": True,
        "new_memory_strength": result.memory_strength,
        "next_review_at": result.next_review_at
    }
```

#### 4. 檢查作業完成度（新增）

**端點**: `GET /api/students/assignments/{assignment_id}/mastery-status`

**Response**:
```json
{
  "current_mastery": 0.87,
  "target_mastery": 0.90,
  "achieved": false,
  "words_mastered": 23,
  "total_words": 30,
  "weak_words": [
    {
      "text": "difficult",
      "memory_strength": 0.45,
      "last_review_at": "2025-11-20T10:00:00Z"
    }
  ]
}
```

---

## 前端組件設計

### 🎨 組件結構

```
StudentActivityPageContent (已存在)
  └─ SentenceMakingActivity (新增)
       ├─ ListeningModeTemplate (新增)
       │    ├─ AudioPlayer
       │    ├─ WordChoicePanel
       │    └─ ProgressIndicator
       │
       └─ WritingModeTemplate (新增)
            ├─ QuestionDisplay
            ├─ WordChoicePanel
            └─ ProgressIndicator
```

### 📦 組件詳細設計

#### 1. SentenceMakingActivity (主組件)

**位置**: `/frontend/src/components/activities/SentenceMakingActivity.tsx`

**功能**:
- 獲取練習題目
- 根據 answer_mode 決定使用 ListeningModeTemplate 或 WritingModeTemplate
- 管理答題狀態和進度

**State 管理**:
```typescript
interface SentenceMakingState {
  sessionId: number | null;
  answerMode: "listening" | "writing";
  words: PracticeWord[];
  currentIndex: number;
  answers: AnswerRecord[];
  loading: boolean;
  masteryStatus: MasteryStatus | null;
}

interface PracticeWord {
  content_item_id: number;
  text: string;
  translation: string;
  example_sentence: string;
  example_sentence_translation: string;
  audio_url?: string;
  memory_strength: number;
  priority_score: number;
}

interface AnswerRecord {
  content_item_id: number;
  is_correct: boolean;
  time_spent_seconds: number;
  answer_data: {
    selected_words: string[];
    attempts: number;
  };
}
```

**核心邏輯**:
```typescript
const SentenceMakingActivity: React.FC<Props> = ({ assignmentId }) => {
  const [state, setState] = useState<SentenceMakingState>({
    sessionId: null,
    answerMode: "writing",
    words: [],
    currentIndex: 0,
    answers: [],
    loading: true,
    masteryStatus: null,
  });

  // 初始化：獲取練習題目
  useEffect(() => {
    loadPracticeWords();
  }, [assignmentId]);

  const loadPracticeWords = async () => {
    try {
      const response = await apiClient.get(
        `/api/students/assignments/${assignmentId}/practice-words`
      );

      setState((prev) => ({
        ...prev,
        sessionId: response.session_id,
        answerMode: response.answer_mode,
        words: response.words,
        loading: false,
      }));
    } catch (error) {
      console.error("Failed to load practice words:", error);
      toast.error("無法載入練習題目");
    }
  };

  // 提交答案
  const submitAnswer = async (answer: AnswerRecord) => {
    try {
      await apiClient.post(
        `/api/students/practice-sessions/${state.sessionId}/submit-answer`,
        answer
      );

      // 記錄答案
      setState((prev) => ({
        ...prev,
        answers: [...prev.answers, answer],
      }));

      // 移動到下一題
      if (state.currentIndex < state.words.length - 1) {
        setState((prev) => ({ ...prev, currentIndex: prev.currentIndex + 1 }));
      } else {
        // 完成本輪練習，檢查達標狀態
        checkMasteryStatus();
      }
    } catch (error) {
      console.error("Failed to submit answer:", error);
      toast.error("提交答案失敗");
    }
  };

  // 檢查達標狀態
  const checkMasteryStatus = async () => {
    const status = await apiClient.get(
      `/api/students/assignments/${assignmentId}/mastery-status`
    );

    setState((prev) => ({ ...prev, masteryStatus: status }));

    if (status.achieved) {
      toast.success("恭喜！您已達成目標熟悉度！");
      // 跳轉到完成頁面或返回作業列表
    } else {
      toast.info(
        `當前熟悉度：${(status.current_mastery * 100).toFixed(0)}%，繼續練習！`
      );
      // 重新載入下一輪題目
      loadPracticeWords();
    }
  };

  if (state.loading) {
    return <LoadingSpinner />;
  }

  const currentWord = state.words[state.currentIndex];

  return (
    <div className="sentence-making-activity">
      {state.answerMode === "listening" ? (
        <ListeningModeTemplate
          word={currentWord}
          onSubmit={submitAnswer}
          progress={{
            current: state.currentIndex + 1,
            total: state.words.length,
          }}
        />
      ) : (
        <WritingModeTemplate
          word={currentWord}
          onSubmit={submitAnswer}
          progress={{
            current: state.currentIndex + 1,
            total: state.words.length,
          }}
        />
      )}
    </div>
  );
};
```

#### 2. ListeningModeTemplate (聽力模式組件)

**位置**: `/frontend/src/components/activities/ListeningModeTemplate.tsx`

**功能**:
- 自動播放音檔
- 顯示例句的打亂單字選項
- 處理單字點擊和答題邏輯

**UI 設計**:
```
┌─────────────────────────────────────────────┐
│ 進度：第 3 題 / 共 10 題              [80%] │
├─────────────────────────────────────────────┤
│                                             │
│   🔊 [Playing Audio...]                     │
│                                             │
│   正在播放例句音檔，請仔細聆聽...            │
│                                             │
│   [▶ 重播音檔]                              │
│                                             │
├─────────────────────────────────────────────┤
│ 答案區：                                     │
│ ┌───┬───┬───┬───┬───┬───┬───┐              │
│ │ I │   │   │   │   │   │   │              │
│ └───┴───┴───┴───┴───┴───┴───┘              │
├─────────────────────────────────────────────┤
│ 選擇單字：                                   │
│ ┌───────┬───────┬───────┬───────┐          │
│ │ apple │ every │  eat  │  an   │          │
│ └───────┴───────┴───────┴───────┘          │
│ ┌───────┬───────┐                          │
│ │  day  │   .   │                          │
│ └───────┴───────┘                          │
└─────────────────────────────────────────────┘
```

**核心邏輯**:
```typescript
interface Props {
  word: PracticeWord;
  onSubmit: (answer: AnswerRecord) => void;
  progress: { current: number; total: number };
}

const ListeningModeTemplate: React.FC<Props> = ({ word, onSubmit, progress }) => {
  const [selectedWords, setSelectedWords] = useState<string[]>([]);
  const [availableWords, setAvailableWords] = useState<string[]>([]);
  const [attempts, setAttempts] = useState(0);
  const [startTime, setStartTime] = useState(Date.now());
  const [audioPlayed, setAudioPlayed] = useState(false);

  // 初始化：打亂例句單字
  useEffect(() => {
    const words = word.example_sentence
      .replace(/[,!?]/g, "") // 移除標點
      .split(" ")
      .filter((w) => w.length > 0);

    // 隨機打亂
    const shuffled = [...words].sort(() => Math.random() - 0.5);
    setAvailableWords(shuffled);
    setSelectedWords([]);
    setAttempts(0);
    setStartTime(Date.now());
  }, [word]);

  // 自動播放音檔
  useEffect(() => {
    if (word.audio_url && !audioPlayed) {
      playAudio();
    }
  }, [word.audio_url]);

  const playAudio = () => {
    const audio = new Audio(word.audio_url);
    audio.play();
    setAudioPlayed(true);
  };

  const handleWordClick = (word: string) => {
    setAttempts((prev) => prev + 1);

    // 正確答案是原始例句的單字序列
    const correctWords = word.example_sentence
      .replace(/[,!?]/g, "")
      .split(" ")
      .filter((w) => w.length > 0);

    const nextIndex = selectedWords.length;
    const isCorrect = word === correctWords[nextIndex];

    if (isCorrect) {
      // 正確：添加到答案區
      setSelectedWords((prev) => [...prev, word]);
      setAvailableWords((prev) => prev.filter((w) => w !== word));

      // 檢查是否完成
      if (nextIndex + 1 === correctWords.length) {
        // 全部答對，提交答案
        const timeSpent = Math.floor((Date.now() - startTime) / 1000);
        onSubmit({
          content_item_id: word.content_item_id,
          is_correct: true,
          time_spent_seconds: timeSpent,
          answer_data: {
            selected_words: [...selectedWords, word],
            attempts,
          },
        });
      }
    } else {
      // 錯誤：播放錯誤音效
      playErrorSound();
      toast.error("選錯了，再試試看！");
    }
  };

  return (
    <div className="listening-mode p-6">
      {/* 進度條 */}
      <ProgressBar current={progress.current} total={progress.total} />

      {/* 音檔播放區 */}
      <div className="audio-section mt-6 mb-8 text-center">
        {!audioPlayed && (
          <div className="text-gray-600 mb-4">
            <Loader2 className="animate-spin inline-block mr-2" />
            正在播放例句音檔...
          </div>
        )}
        <Button onClick={playAudio} variant="outline">
          <Volume2 className="mr-2" />
          重播音檔
        </Button>
      </div>

      {/* 答案區 */}
      <div className="answer-area mb-6">
        <div className="text-sm font-medium mb-2">答案區：</div>
        <div className="flex gap-2">
          {selectedWords.map((w, idx) => (
            <div key={idx} className="px-4 py-2 bg-blue-100 border border-blue-300 rounded">
              {w}
            </div>
          ))}
          {/* 空白框 */}
          {Array.from({ length: correctWords.length - selectedWords.length }).map((_, idx) => (
            <div key={`empty-${idx}`} className="px-4 py-2 border-2 border-dashed border-gray-300 rounded w-20" />
          ))}
        </div>
      </div>

      {/* 單字選擇區 */}
      <div className="word-choices">
        <div className="text-sm font-medium mb-2">選擇單字：</div>
        <div className="grid grid-cols-4 gap-3">
          {availableWords.map((w, idx) => (
            <button
              key={idx}
              onClick={() => handleWordClick(w)}
              className="px-4 py-3 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 hover:border-blue-400 transition-colors"
            >
              {w}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
```

#### 3. WritingModeTemplate (寫作模式組件)

**位置**: `/frontend/src/components/activities/WritingModeTemplate.tsx`

**功能**: 與 ListeningModeTemplate 幾乎相同，但：
- 不自動播放音檔
- 顯示例句原文和中文翻譯作為提示
- 其他邏輯完全相同

**UI 設計**:
```
┌─────────────────────────────────────────────┐
│ 進度：第 3 題 / 共 10 題              [80%] │
├─────────────────────────────────────────────┤
│ 題目：                                       │
│   I eat an apple every day.                 │
│   我每天吃一個蘋果。                         │
├─────────────────────────────────────────────┤
│ 答案區：（同上）                             │
│ 選擇單字：（同上）                           │
└─────────────────────────────────────────────┘
```

---

## 艾賓浩斯記憶曲線演算法

### 🧮 核心演算法：SuperMemo-2 (SM-2)

**PostgreSQL Function 實作**:

```sql
-- 更新記憶強度的核心函數
CREATE OR REPLACE FUNCTION update_memory_strength(
  p_student_assignment_id INTEGER,
  p_content_item_id INTEGER,
  p_is_correct BOOLEAN
) RETURNS TABLE (
  memory_strength DECIMAL,
  next_review_at TIMESTAMPTZ,
  easiness_factor DECIMAL
) AS $
DECLARE
  v_progress user_word_progress%ROWTYPE;
  v_time_since_last_review INTERVAL;
  v_new_strength DECIMAL;
  v_new_easiness DECIMAL;
  v_new_interval DECIMAL;
BEGIN
  -- 取得或創建進度記錄
  SELECT * INTO v_progress
  FROM user_word_progress
  WHERE student_assignment_id = p_student_assignment_id
    AND content_item_id = p_content_item_id;

  -- 如果不存在，創建新記錄
  IF NOT FOUND THEN
    INSERT INTO user_word_progress (
      student_assignment_id,
      content_item_id,
      memory_strength,
      last_review_at,
      next_review_at,
      total_attempts
    ) VALUES (
      p_student_assignment_id,
      p_content_item_id,
      CASE WHEN p_is_correct THEN 0.5 ELSE 0.2 END,
      NOW(),
      NOW() + INTERVAL '1 day',
      1
    )
    RETURNING * INTO v_progress;

    RETURN QUERY SELECT
      v_progress.memory_strength,
      v_progress.next_review_at,
      v_progress.easiness_factor;
    RETURN;
  END IF;

  -- 計算距離上次複習的時間
  v_time_since_last_review := NOW() - v_progress.last_review_at;

  -- 艾賓浩斯遺忘公式：R = e^(-t/S)
  -- R: 記憶保持率, t: 經過時間（秒）, S: 記憶強度常數（與難易度成正比）
  v_new_strength := v_progress.memory_strength *
    EXP(
      -EXTRACT(EPOCH FROM v_time_since_last_review) /
      (86400.0 * v_progress.easiness_factor)
    );

  IF p_is_correct THEN
    -- ===== 答對處理 =====

    -- 提升記憶強度（最高 1.0）
    v_new_strength := LEAST(1.0, v_new_strength + 0.3);

    -- 更新難易度因子（SM-2 演算法）
    -- EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    -- 其中 q = 4 (答對的品質評分)
    v_new_easiness := v_progress.easiness_factor +
      (0.1 - (5 - 4) * (0.08 + (5 - 4) * 0.02));
    v_new_easiness := GREATEST(1.3, v_new_easiness); -- 最小值 1.3

    -- 計算下次複習間隔（SM-2 演算法）
    IF v_progress.repetition_count = 0 THEN
      v_new_interval := 1;  -- 第一次答對：1 天後複習
    ELSIF v_progress.repetition_count = 1 THEN
      v_new_interval := 6;  -- 第二次答對：6 天後複習
    ELSE
      v_new_interval := v_progress.interval_days * v_new_easiness;
    END IF;

    -- 更新記錄
    UPDATE user_word_progress SET
      memory_strength = v_new_strength,
      repetition_count = repetition_count + 1,
      correct_count = correct_count + 1,
      total_attempts = total_attempts + 1,
      easiness_factor = v_new_easiness,
      interval_days = v_new_interval,
      last_review_at = NOW(),
      next_review_at = NOW() + (v_new_interval || ' days')::INTERVAL,
      accuracy_rate = (correct_count + 1)::DECIMAL / (total_attempts + 1),
      updated_at = NOW()
    WHERE id = v_progress.id
    RETURNING * INTO v_progress;

  ELSE
    -- ===== 答錯處理 =====

    -- 降低記憶強度
    v_new_strength := GREATEST(0.1, v_new_strength * 0.5);

    -- 降低難易度因子（變難記）
    v_new_easiness := GREATEST(1.3, v_progress.easiness_factor - 0.2);

    -- 重置間隔為 1 天
    v_new_interval := 1;

    UPDATE user_word_progress SET
      memory_strength = v_new_strength,
      repetition_count = 0,  -- 重置連續答對次數
      incorrect_count = incorrect_count + 1,
      total_attempts = total_attempts + 1,
      easiness_factor = v_new_easiness,
      interval_days = v_new_interval,
      last_review_at = NOW(),
      next_review_at = NOW() + INTERVAL '1 day',
      accuracy_rate = correct_count::DECIMAL / (total_attempts + 1),
      updated_at = NOW()
    WHERE id = v_progress.id
    RETURNING * INTO v_progress;
  END IF;

  RETURN QUERY SELECT
    v_progress.memory_strength,
    v_progress.next_review_at,
    v_progress.easiness_factor;
END;
$ LANGUAGE plpgsql;
```

### 📊 選題演算法

```sql
-- 選擇需要複習的單字
CREATE OR REPLACE FUNCTION get_words_for_practice(
  p_student_assignment_id INTEGER,
  p_limit_count INTEGER DEFAULT 10
) RETURNS TABLE (
  content_item_id INTEGER,
  text VARCHAR,
  translation VARCHAR,
  example_sentence TEXT,
  example_sentence_translation TEXT,
  audio_url TEXT,
  memory_strength DECIMAL,
  priority_score DECIMAL
) AS $
BEGIN
  RETURN QUERY
  WITH assignment_contents AS (
    -- 取得此作業包含的所有 content_items
    SELECT DISTINCT ci.id as content_item_id
    FROM student_assignments sa
    JOIN student_content_progress scp ON scp.student_assignment_id = sa.id
    JOIN content_items ci ON ci.content_id = scp.content_id
    WHERE sa.id = p_student_assignment_id
  )
  SELECT
    ci.id,
    ci.text,
    ci.translation,
    ci.example_sentence,
    ci.example_sentence_translation,
    ci.audio_url,
    COALESCE(uwp.memory_strength, 0) as memory_strength,
    -- 優先順序計算：
    -- 1. 從未練習過的單字（priority = 100）
    -- 2. 該複習時間到了 + 記憶強度低（priority = 50-100）
    -- 3. 時間未到但記憶強度低（priority = 0-30）
    CASE
      WHEN uwp.id IS NULL THEN 100  -- 從未練習過
      WHEN uwp.next_review_at IS NULL THEN 100
      WHEN uwp.next_review_at <= NOW() THEN
        50 + (1 - uwp.memory_strength) * 50
      ELSE
        (1 - uwp.memory_strength) * 30
    END as priority_score
  FROM assignment_contents ac
  JOIN content_items ci ON ci.id = ac.content_item_id
  LEFT JOIN user_word_progress uwp ON
    uwp.student_assignment_id = p_student_assignment_id AND
    uwp.content_item_id = ci.id
  ORDER BY priority_score DESC, RANDOM()
  LIMIT p_limit_count;
END;
$ LANGUAGE plpgsql;
```

### 🎯 達標檢查

```sql
-- 計算作業整體熟悉度
CREATE OR REPLACE FUNCTION calculate_assignment_mastery(
  p_student_assignment_id INTEGER
) RETURNS TABLE (
  current_mastery DECIMAL,
  target_mastery DECIMAL,
  achieved BOOLEAN,
  words_mastered INTEGER,
  total_words INTEGER
) AS $
DECLARE
  v_total_words INTEGER;
  v_avg_strength DECIMAL;
  v_target DECIMAL := 0.90;  -- 目標 90% 熟悉度
BEGIN
  -- 取得作業總單字數
  SELECT COUNT(DISTINCT ci.id) INTO v_total_words
  FROM student_assignments sa
  JOIN student_content_progress scp ON scp.student_assignment_id = sa.id
  JOIN content_items ci ON ci.content_id = scp.content_id
  WHERE sa.id = p_student_assignment_id;

  -- 計算平均記憶強度
  SELECT
    COALESCE(AVG(uwp.memory_strength), 0)
  INTO v_avg_strength
  FROM user_word_progress uwp
  WHERE uwp.student_assignment_id = p_student_assignment_id;

  -- 如果有未練習的單字，將其視為 0 強度
  IF v_total_words > 0 THEN
    SELECT COUNT(*) INTO v_practiced_words
    FROM user_word_progress
    WHERE student_assignment_id = p_student_assignment_id;

    v_avg_strength := (v_avg_strength * v_practiced_words) / v_total_words;
  END IF;

  -- 計算已掌握的單字數（記憶強度 >= 0.8）
  SELECT COUNT(*) INTO v_words_mastered
  FROM user_word_progress
  WHERE student_assignment_id = p_student_assignment_id
    AND memory_strength >= 0.8;

  RETURN QUERY SELECT
    v_avg_strength,
    v_target,
    v_avg_strength >= v_target,
    v_words_mastered,
    v_total_words;
END;
$ LANGUAGE plpgsql;
```

---

## 實作優先順序

### Phase 1: 基礎設施（必須先完成）

**優先級**: ⭐⭐⭐⭐⭐

1. **資料庫 Schema 建立**
   - [ ] 修改 `assignments` 表，添加 `answer_mode` 欄位
   - [ ] 創建 `user_word_progress` 表
   - [ ] 創建 `practice_sessions` 表
   - [ ] 創建 `practice_answers` 表
   - [ ] 創建所有索引

2. **PostgreSQL Functions**
   - [ ] `update_memory_strength()`
   - [ ] `get_words_for_practice()`
   - [ ] `calculate_assignment_mastery()`

3. **Alembic Migration**
   - [ ] 創建 migration 檔案
   - [ ] 執行 migration

**預估時間**: 4-6 小時

---

### Phase 2: 後端 API 開發

**優先級**: ⭐⭐⭐⭐

4. **修改現有 API**
   - [ ] 更新 `/api/teachers/assignments/create` 接收 `answer_mode`
   - [ ] 更新 Assignment model 和 schema

5. **新增 API 端點**
   - [ ] `GET /api/students/assignments/{id}/practice-words`
   - [ ] `POST /api/students/practice-sessions/{id}/submit-answer`
   - [ ] `GET /api/students/assignments/{id}/mastery-status`

6. **測試 API**
   - [ ] 單元測試
   - [ ] 整合測試

**預估時間**: 6-8 小時

---

### Phase 3: 前端組件開發

**優先級**: ⭐⭐⭐⭐

7. **核心組件**
   - [ ] `SentenceMakingActivity.tsx`（主組件）
   - [ ] `ListeningModeTemplate.tsx`
   - [ ] `WritingModeTemplate.tsx`
   - [ ] `WordChoicePanel.tsx`（共用組件）
   - [ ] `ProgressIndicator.tsx`（共用組件）

8. **路由整合**
   - [ ] 在 `StudentActivityPageContent.tsx` 中整合新組件
   - [ ] 根據 content type 路由到正確的組件

**預估時間**: 8-10 小時

---

### Phase 4: 音檔檢查與驗證

**優先級**: ⭐⭐⭐

9. **音檔檢查邏輯**
   - [ ] 實作前端音檔檢查（選擇聽力模式時）
   - [ ] API 端點檢查內容是否有音檔
   - [ ] 提示訊息 UI

10. **錯誤處理**
    - [ ] 音檔載入失敗處理
    - [ ] 網路錯誤處理
    - [ ] 用戶體驗優化

**預估時間**: 3-4 小時

---

### Phase 5: 測試與優化

**優先級**: ⭐⭐⭐

11. **E2E 測試**
    - [ ] 老師創建造句練習作業
    - [ ] 學生完成聽力模式作業
    - [ ] 學生完成寫作模式作業
    - [ ] 艾賓浩斯曲線驗證

12. **性能優化**
    - [ ] SQL 查詢優化
    - [ ] 前端加載優化
    - [ ] 快取策略

**預估時間**: 4-6 小時

---

## 測試計劃

### 🧪 單元測試

#### 後端測試

```python
# tests/test_memory_strength.py

def test_update_memory_strength_first_time_correct():
    """第一次答對應該設置記憶強度為 0.5"""
    result = update_memory_strength(
        student_assignment_id=1,
        content_item_id=10,
        is_correct=True
    )
    assert result.memory_strength == 0.5
    assert result.easiness_factor == 2.5

def test_update_memory_strength_consecutive_correct():
    """連續答對應該提升記憶強度和間隔"""
    # 第一次
    update_memory_strength(1, 10, True)
    # 第二次
    result = update_memory_strength(1, 10, True)
    assert result.memory_strength > 0.5
    assert result.interval_days == 6

def test_update_memory_strength_incorrect():
    """答錯應該降低記憶強度並重置間隔"""
    # 先答對兩次
    update_memory_strength(1, 10, True)
    update_memory_strength(1, 10, True)
    # 答錯
    result = update_memory_strength(1, 10, False)
    assert result.repetition_count == 0
    assert result.interval_days == 1

def test_get_words_for_practice_prioritizes_weak_words():
    """選題應該優先選擇記憶強度低的單字"""
    words = get_words_for_practice(
        student_assignment_id=1,
        limit_count=10
    )
    # 檢查前幾個單字的優先級較高
    assert words[0].priority_score > words[-1].priority_score
```

#### 前端測試

```typescript
// tests/components/SentenceMakingActivity.test.tsx

describe('SentenceMakingActivity', () => {
  it('should load practice words on mount', async () => {
    const mockWords = [
      { content_item_id: 1, text: 'apple', example_sentence: 'I eat an apple.' }
    ];

    apiClient.get = jest.fn().mockResolvedValue({
      session_id: 123,
      answer_mode: 'writing',
      words: mockWords
    });

    render(<SentenceMakingActivity assignmentId={1} />);

    await waitFor(() => {
      expect(screen.getByText('apple')).toBeInTheDocument();
    });
  });

  it('should switch to listening mode when answer_mode is listening', async () => {
    apiClient.get = jest.fn().mockResolvedValue({
      answer_mode: 'listening',
      words: []
    });

    render(<SentenceMakingActivity assignmentId={1} />);

    await waitFor(() => {
      expect(screen.getByText('重播音檔')).toBeInTheDocument();
    });
  });
});
```

### 🔬 整合測試

```python
# tests/integration/test_sentence_making_flow.py

def test_complete_practice_flow():
    """測試完整的練習流程"""
    # 1. 創建作業
    assignment = create_assignment(
        title="Vocabulary Practice",
        content_ids=[1],
        answer_mode="writing"
    )

    # 2. 學生獲取練習題目
    response = client.get(
        f"/api/students/assignments/{assignment.id}/practice-words"
    )
    assert response.status_code == 200
    assert len(response.json()['words']) == 10

    # 3. 提交答案
    session_id = response.json()['session_id']
    word = response.json()['words'][0]

    submit_response = client.post(
        f"/api/students/practice-sessions/{session_id}/submit-answer",
        json={
            "content_item_id": word['content_item_id'],
            "is_correct": True,
            "time_spent_seconds": 10,
            "answer_data": {"selected_words": ["I", "eat"], "attempts": 1}
        }
    )
    assert submit_response.status_code == 200

    # 4. 檢查記憶強度有更新
    progress = db.query(UserWordProgress).filter_by(
        content_item_id=word['content_item_id']
    ).first()
    assert progress.memory_strength > 0
```

---

## 總結

### 📈 預估開發時間

| Phase | 內容 | 時間 |
|-------|------|------|
| Phase 1 | 資料庫 Schema + Functions | 4-6 小時 |
| Phase 2 | 後端 API 開發 | 6-8 小時 |
| Phase 3 | 前端組件開發 | 8-10 小時 |
| Phase 4 | 音檔檢查與驗證 | 3-4 小時 |
| Phase 5 | 測試與優化 | 4-6 小時 |
| **總計** | | **25-34 小時** |

### ✅ 成功標準

1. ✅ 老師可以創建造句練習作業並選擇答題模式
2. ✅ 學生進入作業時根據模式看到不同的 UI
3. ✅ 聽力模式會自動播放音檔
4. ✅ 寫作模式不播放音檔但顯示例句文字
5. ✅ 答題正確性判斷準確
6. ✅ 記憶強度正確更新
7. ✅ 達到 90% 熟悉度後作業完成
8. ✅ 所有測試通過

### 🚀 後續擴展

1. **統計分析**
   - 學生學習曲線圖表
   - 弱項單字分析
   - 學習時間統計

2. **進階功能**
   - 自定義目標熟悉度
   - 不同難度級別
   - 多輪複習機制

3. **遊戲化**
   - 連續答對獎勵
   - 成就系統
   - 排行榜

---

## 附錄

### A. 資料庫 Migration 檔案範本

```python
# alembic/versions/xxx_add_sentence_making_features.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxx'
down_revision = 'yyy'

def upgrade():
    # 1. 修改 assignments 表
    op.add_column('assignments',
        sa.Column('answer_mode', sa.String(20), server_default='writing'))
    op.create_check_constraint(
        'assignments_answer_mode_check',
        'assignments',
        "answer_mode IN ('listening', 'writing')"
    )

    # 2. 創建 user_word_progress 表
    op.create_table(
        'user_word_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE')),
        sa.Column('student_assignment_id', sa.Integer(), sa.ForeignKey('student_assignments.id', ondelete='CASCADE')),
        sa.Column('content_item_id', sa.Integer(), sa.ForeignKey('content_items.id', ondelete='CASCADE')),
        sa.Column('memory_strength', sa.Numeric(5, 4), server_default='0'),
        sa.Column('repetition_count', sa.Integer(), server_default='0'),
        sa.Column('correct_count', sa.Integer(), server_default='0'),
        sa.Column('incorrect_count', sa.Integer(), server_default='0'),
        sa.Column('last_review_at', sa.DateTime(timezone=True)),
        sa.Column('next_review_at', sa.DateTime(timezone=True)),
        sa.Column('easiness_factor', sa.Numeric(3, 2), server_default='2.5'),
        sa.Column('interval_days', sa.Numeric(10, 2), server_default='1'),
        sa.Column('total_attempts', sa.Integer(), server_default='0'),
        sa.Column('accuracy_rate', sa.Numeric(5, 4), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('student_assignment_id', 'content_item_id')
    )

    # 索引
    op.create_index('idx_uwp_student', 'user_word_progress', ['student_id', 'student_assignment_id'])
    op.create_index('idx_uwp_next_review', 'user_word_progress', ['student_assignment_id', 'next_review_at'])

    # 3-4. 其他表類似...

    # 5. 創建 PostgreSQL functions
    op.execute("""
        CREATE OR REPLACE FUNCTION update_memory_strength(...)
        -- 完整函數定義
    """)

def downgrade():
    op.drop_table('practice_answers')
    op.drop_table('practice_sessions')
    op.drop_table('user_word_progress')
    op.drop_column('assignments', 'answer_mode')
    op.execute("DROP FUNCTION IF EXISTS update_memory_strength")
```

---

**文件版本**: v1.0
**創建日期**: 2025-11-11
**最後更新**: 2025-11-11
**作者**: Claude Code
**審核狀態**: 待審核
