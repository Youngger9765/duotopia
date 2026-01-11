# Aggregate-Given-Handler (Behave BDD Version)

## 專案根目錄與預設路徑（chapter04）

**約定**：`{Workspace}` = `chapter04/`（專案根目錄），其下最重要的資料夾是 `app/`, `specs/`, `tests/`。

- **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
- **Step Definitions**：`{Workspace}/tests/features/steps/`
- **Behave Environment**：`{Workspace}/tests/features/environment.py`

## Role

負責實作 `Given` 步驟中建立 Aggregate 初始狀態的邏輯。

**核心任務**：透過 Repository（從 `context.repos.*` 取得）直接在測試環境中建立 Aggregate 初始資料。

---

## ⚠️ 注意事項

- **不透過 Service**：直接使用 `context.repos.*.save()` 建立資料
- **不驗證業務規則**：Given 步驟只是建立前置條件，不需要驗證
- **使用 Fake Repository**：資料儲存在 dict 中
- **從 context 取得 Repository**：所有 Repository 從 `context.repos.*` 取得

---

## Input

1. **Step Definition 樣板**：包含方法簽名、參數、TODO 註解
2. **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
3. **Gherkin 步驟原文**：從 Feature File 中提取

---

## 工作流程

### Step 1: 識別 Aggregate

從 TODO 註解中識別需要建立的 Aggregate：
```python
"""
TODO: [事件風暴部位: Aggregate - LessonProgress]
TODO: 參考 Aggregate-Given-Handler.md 實作
TODO: 參考 Aggregate/Table: LessonProgress
"""
```

→ 需要建立的 Aggregate：`LessonProgress`

### Step 2: 查找 DBML 定義

從 `erm.dbml` 中找到對應的 Table 定義：
```dbml
Table LessonProgress {
  userId varchar [pk]
  lessonId int [pk]
  progress int
  status varchar
}
```

### Step 3: 提取 Gherkin 參數

從 Gherkin 步驟和方法參數中提取需要的值：
```gherkin
Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
```

對應參數：
- `user_name` = "Alice"
- `lesson_id` = 1
- `progress` = 70
- `status` = "進行中"

### Step 4: 實作 Step Definition

```python
from behave import given
from app.models.lesson_progress import LessonProgress

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    # 1. 透過用戶 (Actor) 的 Unique key 取得或建立用戶 ID（from/to context.ids）
    if user_name not in context.ids:
        context.ids[user_name] = user_name
    user_id = context.ids[user_name]
    
    # 2. 狀態映射（如果必要）（中文 → 英文 enum）
    status_map = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    
    # 3. 建立 Aggregate
    lesson_progress = LessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        progress=progress,
        status=status_map.get(status, status)
    )
    
    # 4. 儲存到 Repository（從 context 取得）
    context.repos.lesson_progress.save(lesson_progress)
```

---

## 處理 DataTable

當 Gherkin 使用 DataTable 時：

```gherkin
Given 系統中有以下課程：
  | lessonId | name | type | journeyId | chapterId | rewardExp |
  | 1 | 物件導向基礎 | VIDEO | 1 | 1 | 300 |
  | 2 | 設計模式 | VIDEO | 1 | 1 | 400 |
```

**實作方式**：

```python
from behave import given
from app.models.lesson import Lesson

@given('系統中有以下課程：')
def step_impl(context):
    """建立課程資料"""
    # context.table 由 Behave 自動填充
    for row in context.table:
        lesson = Lesson(
            lesson_id=int(row['lessonId']),
            name=row['name'],
            lesson_type=row['type'],
            journey_id=int(row['journeyId']),
            chapter_id=int(row['chapterId']),
            reward_exp=int(row['rewardExp'])
        )
        context.repos.lesson.save(lesson)
```

---

## 處理 DocString

當 Gherkin 使用 DocString 時：

```gherkin
Given 用戶 "Alice" 的個人簡介為：
  """
  我是一個軟體工程師，
  喜歡學習新技術。
  """
```

**實作方式**：

```python
from behave import given

@given('用戶 "{user_name}" 的個人簡介為：')
def step_impl(context, user_name):
    """設定用戶簡介"""
    user_id = context.ids.get(user_name, user_name)
    
    # context.text 是 DocString 內容（Behave 自動填充）
    bio = context.text
    
    # 更新用戶資料
    user = context.repos.user.find(user_id)
    user.bio = bio
    context.repos.user.save(user)
```

---

## 處理複合主鍵

當 Aggregate 有複合主鍵時：

```gherkin
Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
```

**Repository 實作**：
```python
# app/repositories/lesson_progress_repository.py

class LessonProgressRepository:
    def __init__(self):
        # Key: (user_id, lesson_id)
        self._data = {}
    
    def save(self, lesson_progress):
        key = (lesson_progress.user_id, lesson_progress.lesson_id)
        self._data[key] = lesson_progress
    
    def find(self, user_id, lesson_id):
        key = (user_id, lesson_id)
        return self._data.get(key)
```

---

## 完整範例

### Input (Feature File)

```gherkin
Feature: 課程平台 - 增加影片進度

Rule: 影片進度必須單調遞增
  
  Example: 成功增加影片進度
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
    When 用戶 "Alice" 更新課程 1 的影片進度為 80%
    Then 操作成功
    And 用戶 "Alice" 在課程 1 的進度應為 80%
```

### Output (Step Definition)

```python
# tests/features/steps/aggregate_given.py

from behave import given
from app.models.lesson_progress import LessonProgress

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """建立用戶的課程進度初始狀態"""
    # 1. 取得或建立用戶 ID
    if user_name not in context.ids:
        context.ids[user_name] = user_name
    user_id = context.ids[user_name]
    
    # 2. 狀態映射
    status_map = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    
    # 3. 建立 Aggregate
    lesson_progress = LessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        progress=progress,
        status=status_map.get(status, status)
    )
    
    # 4. 儲存到 Repository
    context.repos.lesson_progress.save(lesson_progress)
```

---

## 使用 helpers 簡化

當多個 Given steps 都有狀態映射時，可以抽取為 helper：

```python
# tests/features/steps/helpers.py

STATUS_MAP = {
    "進行中": "IN_PROGRESS",
    "已完成": "COMPLETED",
    "未開始": "NOT_STARTED",
}

def translate_status(chinese_status):
    """中文狀態轉英文 enum"""
    return STATUS_MAP.get(chinese_status, chinese_status)

def get_user_id(context, user_name):
    """從 context.ids 取得或建立用戶 ID"""
    if user_name not in context.ids:
        context.ids[user_name] = user_name
    return context.ids[user_name]
```

使用 helper 後：

```python
# tests/features/steps/aggregate_given.py

from behave import given
from app.models.lesson_progress import LessonProgress
from steps.helpers import get_user_id, translate_status

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """建立用戶的課程進度初始狀態"""
    user_id = get_user_id(context, user_name)
    status_en = translate_status(status)
    
    lesson_progress = LessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        progress=progress,
        status=status_en
    )
    
    context.repos.lesson_progress.save(lesson_progress)
```

---

## Critical Rules

### R1: 不透過 Service
Given 步驟直接使用 Repository，不呼叫 Service。

### R2: 從 context 取得 Repository
所有 Repository 從 `context.repos.*` 取得。

### R3: user_name → user_id 映射
將 user_name 儲存到 `context.ids`，供後續步驟使用。

### R4: 狀態映射
中文狀態需要轉換為英文 enum。

### R5: DataTable 從 context.table 取得
Behave 自動將 DataTable 填充到 `context.table`。

### R6: DocString 從 context.text 取得
Behave 自動將 DocString 填充到 `context.text`。

### R7: 函數簽名規則
第一個參數必須是 `context`，後接從 pattern 解析的參數。

---

**文件建立日期**：2025-12-28
**文件版本**：Behave BDD Unit Test Version 2.0
**適用框架**：Python + Behave
