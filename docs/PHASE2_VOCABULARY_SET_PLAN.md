# Phase 2: VOCABULARY_SET (單字集) 實作規格

> **文件版本**：v1.0
> **建立日期**：2025-12-17
> **狀態**：Draft - 待討論

---

## 1. 功能概述

### 1.1 什麼是 VOCABULARY_SET？

**單字集** 是一種以「單字記憶」為核心的練習類型。教師建立一組單字（含中文翻譯和例句），學生透過「看單字 → 用單字造句」的方式進行練習，系統根據艾賓浩斯記憶曲線安排複習順序。

### 1.2 與 EXAMPLE_SENTENCES（例句集）的差異

| 面向 | EXAMPLE_SENTENCES (例句集) | VOCABULARY_SET (單字集) |
|------|---------------------------|------------------------|
| **核心目標** | 練習整句的朗讀或聽力重組 | 記憶單字並學會應用造句 |
| **內容結構** | 以「例句」為主體 | 以「單字」為主體，例句為輔助 |
| **作答模式** | 朗讀 (reading) / 重組 (rearrangement) | 聽力造句 (listening) / 寫作造句 (writing) |
| **題目來源** | 固定題序或隨機打亂 | 根據記憶曲線動態選題 |
| **完成條件** | 完成所有題目 | 達到目標熟悉度 (如 80%) |
| **計分邏輯** | 每題獨立計分 | 累積記憶強度 |
| **適用場景** | 口說練習、聽力訓練 | 單字背誦、詞彙擴充 |

### 1.3 核心特色

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOCABULARY_SET 核心特色                       │
├─────────────────────────────────────────────────────────────────┤
│  1. 艾賓浩斯記憶曲線                                              │
│     - 根據遺忘曲線安排複習時機                                     │
│     - 答對的單字間隔拉長，答錯的縮短                                │
│                                                                  │
│  2. 智慧選題                                                     │
│     - 優先練習即將遺忘的單字                                       │
│     - 新單字逐步引入                                              │
│                                                                  │
│  3. 目標熟悉度                                                   │
│     - 不是「做完」而是「學會」                                      │
│     - 達到 80% 熟悉度才算完成                                      │
│                                                                  │
│  4. 雙模式作答                                                   │
│     - 聽力模式：聽音檔 → 選字造句                                  │
│     - 寫作模式：看翻譯 → 選字造句                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 資料結構設計

### 2.1 Content 層級（教師建立的單字集）

```
┌─────────────────────────────────────────────────────────────────┐
│                      Content (單字集)                            │
├─────────────────────────────────────────────────────────────────┤
│  id: 1                                                          │
│  type: VOCABULARY_SET                                           │
│  title: "Unit 1 單字練習"                                        │
│  lesson_id: 101                                                 │
│  level: "A1"                                                    │
│  target_mastery: 0.8  ← 目標熟悉度 (80%)                         │
│  words_per_session: 10 ← 每次練習的單字數量                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:M
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ContentItem (單字)                            │
├─────────────────────────────────────────────────────────────────┤
│  id: 1                                                          │
│  content_id: 1                                                  │
│  order_index: 0                                                 │
│  text: "apple"              ← 單字                               │
│  translation: "蘋果"        ← 中文翻譯                            │
│  audio_url: "..."           ← 單字發音（選填）                     │
│  example_sentence: "I eat an apple every day."  ← 例句           │
│  example_sentence_translation: "我每天吃一顆蘋果。"                 │
│  example_sentence_audio_url: "..."  ← 例句音檔（聽力模式用）        │
│  word_count: 6              ← 例句單字數                          │
│  max_errors: 3              ← 允許錯誤次數                        │
│  difficulty_level: 1        ← 難度等級 (1-5)                      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Assignment 層級（作業設定）

```
┌─────────────────────────────────────────────────────────────────┐
│                      Assignment (作業)                           │
├─────────────────────────────────────────────────────────────────┤
│  新增欄位（VOCABULARY_SET 專用）:                                 │
│                                                                  │
│  answer_mode: "listening" | "writing"                           │
│    └─ 作答模式                                                   │
│                                                                  │
│  target_mastery: 0.8                                            │
│    └─ 目標熟悉度 (預設 80%)                                       │
│                                                                  │
│  words_per_session: 10                                          │
│    └─ 每次練習的單字數量                                          │
│                                                                  │
│  allow_mode_switch: false                                       │
│    └─ 是否允許學生切換模式                                        │
│                                                                  │
│  show_hint_after_errors: 2                                      │
│    └─ 錯幾次後顯示提示                                            │
│                                                                  │
│  score_category: "writing" | "listening"                        │
│    └─ 分數記錄分類                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 學生進度追蹤

```
┌─────────────────────────────────────────────────────────────────┐
│                  UserWordProgress (單字記憶進度)                   │
├─────────────────────────────────────────────────────────────────┤
│  這個 Model 已存在，欄位包括：                                     │
│                                                                  │
│  student_id: 學生 ID                                             │
│  student_assignment_id: 作業實例 ID                               │
│  content_item_id: 單字 ID                                        │
│                                                                  │
│  memory_strength: 0.75     ← 記憶強度 (0-1)                       │
│  repetition_count: 3       ← 連續答對次數                         │
│  correct_count: 5          ← 累計答對次數                         │
│  incorrect_count: 2        ← 累計答錯次數                         │
│  last_review_at: DateTime  ← 最後複習時間                         │
│  next_review_at: DateTime  ← 下次建議複習時間                      │
│  easiness_factor: 2.5      ← SM-2 難易度因子                      │
│  interval_days: 4          ← 複習間隔天數                         │
│  accuracy_rate: 0.71       ← 正確率                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  PracticeSession (練習記錄)                       │
├─────────────────────────────────────────────────────────────────┤
│  這個 Model 已存在，欄位包括：                                     │
│                                                                  │
│  student_id: 學生 ID                                             │
│  student_assignment_id: 作業實例 ID                               │
│  practice_mode: "listening" | "writing"                         │
│  words_practiced: 10       ← 本次練習單字數                        │
│  correct_count: 8          ← 本次答對題數                         │
│  total_time_seconds: 300   ← 總花費時間                           │
│  started_at: DateTime                                           │
│  completed_at: DateTime                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  PracticeAnswer (答題記錄)                        │
├─────────────────────────────────────────────────────────────────┤
│  practice_session_id: Session ID                                │
│  content_item_id: 單字 ID                                        │
│  is_correct: true/false                                         │
│  time_spent_seconds: 25                                         │
│  answer_data: {                                                 │
│    selected_words: ["I", "eat", "an", "apple", ...],            │
│    attempts: 3,                                                 │
│    hint_used: false                                             │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 新增欄位 (Database Migration)

```python
# Migration: 為 VOCABULARY_SET 新增必要欄位

# 1. Content 表新增欄位
op.execute("""
    ALTER TABLE contents
    ADD COLUMN IF NOT EXISTS target_mastery DECIMAL(3,2) DEFAULT 0.8,
    ADD COLUMN IF NOT EXISTS words_per_session INTEGER DEFAULT 10
""")

# 2. ContentItem 表新增欄位
op.execute("""
    ALTER TABLE content_items
    ADD COLUMN IF NOT EXISTS example_sentence_audio_url TEXT,
    ADD COLUMN IF NOT EXISTS difficulty_level INTEGER DEFAULT 1
""")

# 3. Assignment 表新增欄位
op.execute("""
    ALTER TABLE assignments
    ADD COLUMN IF NOT EXISTS target_mastery DECIMAL(3,2) DEFAULT 0.8,
    ADD COLUMN IF NOT EXISTS words_per_session INTEGER DEFAULT 10,
    ADD COLUMN IF NOT EXISTS allow_mode_switch BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS show_hint_after_errors INTEGER DEFAULT 2
""")
```

---

## 3. UI 流程設計

### 3.1 教師端：建立單字集

```
┌─────────────────────────────────────────────────────────────────┐
│  教師端 - 建立 VOCABULARY_SET 流程                                │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  選擇內容類型  │
    │  (對話框)     │
    └──────┬───────┘
           │ 選擇 "單字集"
           ▼
    ┌──────────────┐
    │  輸入基本資訊  │
    │  - 標題       │
    │  - 等級       │
    │  - 目標熟悉度  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  新增單字     │◄─────────────────┐
    │  - 英文單字   │                  │
    │  - 中文翻譯   │                  │
    │  - 例句      │                  │
    │  - 例句翻譯   │                  │
    └──────┬───────┘                  │
           │                          │
           ├─────── [繼續新增] ────────┘
           │
           │ [完成]
           ▼
    ┌──────────────┐
    │  生成音檔     │
    │  (批次 TTS)   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  單字集建立   │
    │    完成!     │
    └──────────────┘
```

### 3.2 教師端：指派作業

```
┌─────────────────────────────────────────────────────────────────┐
│  指派 VOCABULARY_SET 作業 - 設定選項                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  基本設定                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  作業標題: [Unit 1 單字練習          ]                    │    │
│  │  截止日期: [2025-01-15 ▼]                                │    │
│  │  班級:    [五年級 A 班 ▼]                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  作答模式                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ○ 聽力模式 - 聽例句音檔後選字造句                         │    │
│  │  ● 寫作模式 - 看中文翻譯後選字造句                         │    │
│  │                                                          │    │
│  │  □ 允許學生切換模式                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  進階設定                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  目標熟悉度: [80%  ▼]  (達到此熟悉度才算完成)              │    │
│  │  每次練習數: [10   ▼]  單字                               │    │
│  │  錯誤提示:   [2    ▼]  次錯誤後顯示提示                   │    │
│  │  分數分類:   [寫作 ▼]                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│                              [取消]  [指派作業]                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 學生端：練習流程

```
┌─────────────────────────────────────────────────────────────────┐
│  學生端 - VOCABULARY_SET 練習流程                                │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  作業列表    │
                    └──────┬───────┘
                           │ 點擊進入
                           ▼
                    ┌──────────────┐
                    │  作業概覽    │
                    │  - 總單字數   │
                    │  - 目前熟悉度 │
                    │  - 目標熟悉度 │
                    └──────┬───────┘
                           │ 開始練習
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │                    練習介面                           │
    │  ┌────────────────────────────────────────────────┐  │
    │  │  進度: ████████░░░░░░░░░░░░  4/10              │  │
    │  └────────────────────────────────────────────────┘  │
    │                                                      │
    │  【聽力模式】           或          【寫作模式】       │
    │  ┌────────────────┐         ┌────────────────┐      │
    │  │  🔊 播放音檔    │         │  請翻譯：       │      │
    │  │                │         │  "我每天吃一顆   │      │
    │  │  [重播]        │         │   蘋果。"       │      │
    │  └────────────────┘         └────────────────┘      │
    │                                                      │
    │  單字提示：apple (蘋果)                               │
    │                                                      │
    │  答案區：                                            │
    │  ┌─────────────────────────────────────────────┐    │
    │  │ [I] [eat] [an] [ ] [ ] [ ] [ ]              │    │
    │  └─────────────────────────────────────────────┘    │
    │                                                      │
    │  選字區：                                            │
    │  ┌─────────────────────────────────────────────┐    │
    │  │ [apple] [every] [day] [an] [eat]            │    │
    │  └─────────────────────────────────────────────┘    │
    └──────────────────────────────────────────────────────┘
                           │
                           │ 完成一題
                           ▼
                    ┌──────────────┐
                    │  即時反饋    │
                    │  ✓ 正確!    │
                    │  或          │
                    │  ✗ 再試一次  │
                    └──────┬───────┘
                           │
               ┌───────────┴───────────┐
               │                       │
               ▼                       ▼
        ┌────────────┐          ┌────────────┐
        │  繼續下一題  │          │  本輪完成   │
        │  (未達10題)  │          │  (達10題)   │
        └────────────┘          └─────┬──────┘
                                      │
                                      ▼
                               ┌────────────┐
                               │  檢查熟悉度 │
                               └─────┬──────┘
                           ┌─────────┴─────────┐
                           │                   │
                           ▼                   ▼
                    ┌────────────┐      ┌────────────┐
                    │  未達標    │      │  已達標!   │
                    │  熟悉度:60%│      │  熟悉度:82%│
                    │  [繼續練習]│      │  🎉 完成!  │
                    └────────────┘      └────────────┘
```

### 3.4 答題畫面狀態

```
┌─────────────────────────────────────────────────────────────────┐
│  答題畫面狀態機                                                  │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   IDLE      │ ◄─── 初始狀態
    │   等待作答   │
    └──────┬──────┘
           │ 點擊單字
           ▼
    ┌─────────────┐
    │  CHECKING   │
    │  檢查答案   │
    └──────┬──────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌─────────┐
│ CORRECT │ │ WRONG   │
│ 答對    │ │ 答錯    │
└────┬────┘ └────┬────┘
     │           │
     │           ├─── 錯誤次數 < max_errors
     │           │         │
     │           │         ▼
     │           │    ┌─────────┐
     │           │    │ RETRY   │
     │           │    │ 重試    │
     │           │    └────┬────┘
     │           │         │
     │           │         └──────► IDLE
     │           │
     │           └─── 錯誤次數 >= max_errors
     │                     │
     │                     ▼
     │               ┌─────────┐
     │               │ FAILED  │
     │               │ 本題失敗 │
     │               └────┬────┘
     │                    │
     └────────┬───────────┘
              │
              ▼
       ┌─────────────┐
       │ NEXT / DONE │
       │ 下一題/完成  │
       └─────────────┘
```

---

## 4. 計分方式

### 4.1 單題計分

```
┌─────────────────────────────────────────────────────────────────┐
│  單題計分邏輯                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  基礎分數 = 100 分                                               │
│                                                                  │
│  錯誤扣分：                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  每次選錯扣分 = floor(100 / 句子單字數 / 2)              │    │
│  │                                                          │    │
│  │  例：6 個單字的句子                                       │    │
│  │      每選錯一次扣 floor(100 / 6 / 2) = 8 分              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  時間加成（可選）：                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  在時限內完成：額外 +10 分                                │    │
│  │  超時完成：不扣分，但無加成                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  提示扣分：                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  使用提示：扣 20 分                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  最終分數 = max(0, 基礎分數 - 錯誤扣分 - 提示扣分 + 時間加成)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 記憶強度更新（艾賓浩斯 SM-2 演算法）

```python
def update_memory_strength(progress: UserWordProgress, is_correct: bool, quality: int):
    """
    更新記憶強度

    quality: 答題品質 (0-5)
        5: 完美，無錯誤
        4: 正確，但有 1 次錯誤
        3: 正確，但有多次錯誤
        2: 錯誤，但記得部分
        1: 完全錯誤
        0: 放棄
    """

    if quality >= 3:  # 答對
        # 更新 easiness factor
        progress.easiness_factor = max(1.3,
            progress.easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

        # 更新間隔天數
        if progress.repetition_count == 0:
            progress.interval_days = 1
        elif progress.repetition_count == 1:
            progress.interval_days = 6
        else:
            progress.interval_days = progress.interval_days * progress.easiness_factor

        progress.repetition_count += 1
        progress.correct_count += 1

    else:  # 答錯
        progress.repetition_count = 0
        progress.interval_days = 1
        progress.incorrect_count += 1

    # 更新記憶強度 (0-1)
    progress.memory_strength = calculate_memory_strength(progress)

    # 設定下次複習時間
    progress.last_review_at = datetime.now()
    progress.next_review_at = datetime.now() + timedelta(days=progress.interval_days)

    # 更新正確率
    total = progress.correct_count + progress.incorrect_count
    progress.accuracy_rate = progress.correct_count / total if total > 0 else 0
```

### 4.3 熟悉度計算

```python
def calculate_mastery(student_assignment_id: int) -> MasteryStatus:
    """
    計算整體熟悉度
    """

    # 取得所有單字進度
    word_progress_list = get_word_progress(student_assignment_id)

    if not word_progress_list:
        return MasteryStatus(current_mastery=0, achieved=False)

    # 計算平均記憶強度
    total_strength = sum(wp.memory_strength for wp in word_progress_list)
    current_mastery = total_strength / len(word_progress_list)

    # 計算已掌握單字數（記憶強度 >= 0.8 的視為已掌握）
    words_mastered = sum(1 for wp in word_progress_list if wp.memory_strength >= 0.8)

    # 取得目標熟悉度
    target_mastery = get_assignment_target_mastery(student_assignment_id)  # 預設 0.8

    return MasteryStatus(
        current_mastery=current_mastery,
        target_mastery=target_mastery,
        achieved=current_mastery >= target_mastery,
        words_mastered=words_mastered,
        total_words=len(word_progress_list)
    )
```

### 4.4 智慧選題演算法

```python
def get_practice_words(student_assignment_id: int, count: int = 10) -> List[PracticeWord]:
    """
    根據記憶曲線選擇練習單字

    優先順序：
    1. 需要複習的單字（next_review_at <= now）
    2. 記憶強度最低的單字
    3. 從未練習過的新單字
    """

    now = datetime.now()

    # 1. 需要複習的單字（按緊急程度排序）
    due_words = (
        UserWordProgress.query
        .filter(
            student_assignment_id == student_assignment_id,
            next_review_at <= now
        )
        .order_by(next_review_at.asc())
        .all()
    )

    # 2. 記憶強度最低的單字
    weak_words = (
        UserWordProgress.query
        .filter(
            student_assignment_id == student_assignment_id,
            next_review_at > now
        )
        .order_by(memory_strength.asc())
        .all()
    )

    # 3. 從未練習過的新單字
    practiced_item_ids = [wp.content_item_id for wp in all_progress]
    new_words = (
        ContentItem.query
        .filter(content_id == content_id)
        .filter(~ContentItem.id.in_(practiced_item_ids))
        .all()
    )

    # 組合選題（優先複習 > 弱項 > 新字）
    selected = []

    # 50% 需要複習的
    selected.extend(due_words[:count // 2])

    # 30% 記憶弱的
    remaining = count - len(selected)
    selected.extend(weak_words[:remaining * 3 // 5])

    # 20% 新單字
    remaining = count - len(selected)
    selected.extend(new_words[:remaining])

    # 補足數量
    if len(selected) < count:
        # 從所有單字中補足
        ...

    return selected[:count]
```

---

## 5. API 設計

### 5.1 教師端 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/contents` | POST | 建立單字集 |
| `/api/contents/{id}` | GET | 取得單字集詳情 |
| `/api/contents/{id}` | PUT | 更新單字集 |
| `/api/contents/{id}/items` | POST | 新增單字 |
| `/api/contents/{id}/items/{item_id}` | PUT | 更新單字 |
| `/api/contents/{id}/items/{item_id}` | DELETE | 刪除單字 |
| `/api/contents/{id}/generate-audio` | POST | 批次生成音檔 |
| `/api/assignments` | POST | 建立作業（含 VOCABULARY_SET 設定）|

### 5.2 學生端 API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/students/assignments/{id}/practice-words` | GET | 取得練習單字（智慧選題）|
| `/api/students/practice-sessions` | POST | 開始練習 session |
| `/api/students/practice-sessions/{id}/submit-answer` | POST | 提交單題答案 |
| `/api/students/practice-sessions/{id}/complete` | POST | 完成本輪練習 |
| `/api/students/assignments/{id}/mastery-status` | GET | 取得熟悉度狀態 |
| `/api/students/assignments/{id}/word-progress` | GET | 取得單字進度列表 |

### 5.3 API Response 範例

```typescript
// GET /api/students/assignments/{id}/practice-words
{
  "session_id": 123,
  "answer_mode": "writing",
  "words": [
    {
      "content_item_id": 1,
      "text": "apple",
      "translation": "蘋果",
      "example_sentence": "I eat an apple every day.",
      "example_sentence_translation": "我每天吃一顆蘋果。",
      "audio_url": "https://...",
      "memory_strength": 0.45,
      "priority_score": 0.85  // 練習優先度
    },
    // ... more words
  ],
  "mastery_status": {
    "current_mastery": 0.62,
    "target_mastery": 0.80,
    "words_mastered": 12,
    "total_words": 20
  }
}
```

---

## 6. 前端組件設計

### 6.1 組件架構

```
┌─────────────────────────────────────────────────────────────────┐
│  前端組件架構                                                    │
└─────────────────────────────────────────────────────────────────┘

src/components/
├── activities/
│   ├── SentenceMakingActivity.tsx    [既有] 主控制組件
│   ├── WritingModeTemplate.tsx       [既有] 寫作模式
│   ├── ListeningModeTemplate.tsx     [既有] 聽力模式
│   └── shared/
│       ├── ProgressIndicator.tsx     [既有] 進度指示器
│       └── WordChoicePanel.tsx       [既有] 單字選擇面板
│
├── teacher/
│   ├── VocabularySetPanel.tsx        [新增] 教師端單字集管理
│   ├── VocabularySetEditor.tsx       [新增] 單字編輯器
│   └── VocabularySetAssignDialog.tsx [新增] 作業指派對話框
│
└── student/
    └── MasteryProgressCard.tsx       [新增] 熟悉度進度卡片
```

### 6.2 新增組件說明

#### VocabularySetPanel.tsx（教師端）
```typescript
interface VocabularySetPanelProps {
  contentId: number;
  onSave: () => void;
}

// 功能：
// - 顯示單字列表（表格形式）
// - 新增/編輯/刪除單字
// - 批次匯入 (CSV)
// - 批次生成音檔
// - 預覽單字集
```

#### VocabularySetEditor.tsx（單字編輯）
```typescript
interface VocabularyItem {
  id?: number;
  text: string;           // 英文單字
  translation: string;    // 中文翻譯
  example_sentence: string;
  example_sentence_translation: string;
  audio_url?: string;
  example_sentence_audio_url?: string;
}

interface VocabularySetEditorProps {
  item?: VocabularyItem;  // 編輯模式時傳入
  onSave: (item: VocabularyItem) => void;
  onCancel: () => void;
}
```

#### MasteryProgressCard.tsx（學生端）
```typescript
interface MasteryProgressCardProps {
  currentMastery: number;   // 0-1
  targetMastery: number;    // 0-1
  wordsMastered: number;
  totalWords: number;
}

// 顯示：
// - 圓形進度條（熟悉度）
// - 已掌握/總單字數
// - 達標狀態提示
```

### 6.3 修改既有組件

#### ContentTypeDialog.tsx
```typescript
// 啟用 VOCABULARY_SET 選項
{
  type: "vocabulary_set",
  name: "單字集",
  description: "建立單字集，學生透過記憶曲線練習單字造句",
  icon: "📚",
  disabled: false,  // 改為 false
}
```

#### AssignmentDialog.tsx
```typescript
// 新增 VOCABULARY_SET 專用設定欄位
{content.type === 'VOCABULARY_SET' && (
  <>
    <Select name="answer_mode" label="作答模式">
      <Option value="writing">寫作模式</Option>
      <Option value="listening">聽力模式</Option>
    </Select>

    <Slider
      name="target_mastery"
      label="目標熟悉度"
      min={50} max={100} step={5}
      format={(v) => `${v}%`}
    />

    <NumberInput
      name="words_per_session"
      label="每次練習單字數"
      min={5} max={20}
    />

    <Checkbox
      name="allow_mode_switch"
      label="允許學生切換作答模式"
    />
  </>
)}
```

---

## 7. 實作優先順序

### Phase 2.1：基礎架構（Week 1-2）

```
□ 1. Database Migration
   □ 新增 Content 欄位 (target_mastery, words_per_session)
   □ 新增 ContentItem 欄位 (example_sentence_audio_url, difficulty_level)
   □ 新增 Assignment 欄位 (target_mastery, words_per_session, allow_mode_switch)

□ 2. Backend API
   □ 啟用 VOCABULARY_SET ContentType
   □ 實作 VOCABULARY_SET 專用 CRUD
   □ 實作智慧選題 API
   □ 實作熟悉度計算 API

□ 3. 前端基礎
   □ 啟用 ContentTypeDialog 的 VOCABULARY_SET 選項
   □ 建立 VocabularySetPanel 組件
   □ 建立 VocabularySetEditor 組件
```

### Phase 2.2：教師端功能（Week 3-4）

```
□ 4. 教師端 - 建立單字集
   □ 單字新增/編輯/刪除介面
   □ 批次匯入功能 (CSV)
   □ 音檔生成功能 (TTS)
   □ 預覽功能

□ 5. 教師端 - 指派作業
   □ AssignmentDialog 新增 VOCABULARY_SET 設定
   □ 作答模式選擇
   □ 目標熟悉度設定
   □ 進階選項
```

### Phase 2.3：學生端功能（Week 5-6）

```
□ 6. 學生端 - 練習介面
   □ 整合既有 SentenceMakingActivity
   □ 整合 WritingModeTemplate
   □ 整合 ListeningModeTemplate
   □ 新增 MasteryProgressCard

□ 7. 學生端 - 進度追蹤
   □ 單字記憶進度顯示
   □ 熟悉度達標判定
   □ 作業完成流程
```

### Phase 2.4：優化與測試（Week 7-8）

```
□ 8. 測試
   □ 單元測試
   □ 整合測試
   □ E2E 測試

□ 9. 優化
   □ 效能優化
   □ UX 優化
   □ 錯誤處理

□ 10. 文件
    □ 更新 API 文件
    □ 更新使用手冊
```

---

## 8. 風險與注意事項

### 8.1 技術風險

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| 記憶曲線演算法效能 | 選題 API 響應慢 | 使用 Redis 快取、預計算 |
| 音檔生成成本 | Azure TTS 費用增加 | 批次生成、音檔重用 |
| 資料庫 Migration | 影響現有資料 | 使用 Additive Migration |

### 8.2 相容性注意

```
⚠️ 重要：Migration 必須使用 IF NOT EXISTS
⚠️ 重要：新欄位必須有 DEFAULT 值或 nullable=True
⚠️ 重要：不要破壞既有 EXAMPLE_SENTENCES 功能
```

### 8.3 與既有系統的整合

```
┌─────────────────────────────────────────────────────────────────┐
│  整合點                                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ContentType 系統                                             │
│     - 共用 Content, ContentItem 模型                             │
│     - 共用 normalize_content_type() 函數                         │
│                                                                  │
│  2. 作業系統                                                     │
│     - 共用 Assignment, StudentAssignment 模型                    │
│     - 共用作業狀態流程                                            │
│                                                                  │
│  3. 前端路由                                                     │
│     - 根據 content.type 路由到對應組件                            │
│     - EXAMPLE_SENTENCES → ReadingAssessment / Rearrangement     │
│     - VOCABULARY_SET → SentenceMakingActivity                   │
│                                                                  │
│  4. 點數系統                                                     │
│     - TTS 生成計費                                               │
│     - 與 PointUsageLog 整合                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. 討論事項

以下是需要與團隊討論的問題：

### 9.1 設計決策

1. **目標熟悉度預設值**：80% 是否合適？是否需要讓教師自訂？
2. **每次練習單字數**：預設 10 個是否合適？範圍 5-20 是否足夠？
3. **記憶曲線參數**：SM-2 演算法的 easiness factor 初始值 2.5 是否需要調整？

### 9.2 功能範圍

1. **批次匯入格式**：CSV 還是 Excel？需要提供範本嗎？
2. **音檔生成**：單字音檔和例句音檔都要生成嗎？
3. **提示功能**：錯誤後是否顯示正確答案？還是只顯示提示？

### 9.3 UX 問題

1. **模式切換**：允許學生中途切換作答模式嗎？
2. **進度儲存**：學生中途離開，進度如何處理？
3. **達標後**：達標後是否還能繼續練習？

---

## 附錄 A：資料範例

### A.1 單字集範例

```json
{
  "title": "Unit 1 水果單字",
  "type": "VOCABULARY_SET",
  "level": "A1",
  "target_mastery": 0.8,
  "items": [
    {
      "text": "apple",
      "translation": "蘋果",
      "example_sentence": "I eat an apple every day.",
      "example_sentence_translation": "我每天吃一顆蘋果。"
    },
    {
      "text": "banana",
      "translation": "香蕉",
      "example_sentence": "The banana is yellow.",
      "example_sentence_translation": "香蕉是黃色的。"
    },
    {
      "text": "orange",
      "translation": "橘子",
      "example_sentence": "She likes orange juice.",
      "example_sentence_translation": "她喜歡柳橙汁。"
    }
  ]
}
```

### A.2 作業設定範例

```json
{
  "title": "Unit 1 單字練習作業",
  "classroom_id": 1,
  "content_ids": [101],
  "due_date": "2025-01-15T23:59:59Z",
  "settings": {
    "answer_mode": "writing",
    "target_mastery": 0.8,
    "words_per_session": 10,
    "allow_mode_switch": false,
    "show_hint_after_errors": 2,
    "score_category": "writing"
  }
}
```

---

> **下一步**：請團隊審閱此規格，提出修改建議後進入實作階段。
