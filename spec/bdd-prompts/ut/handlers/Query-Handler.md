# Query-Handler (Behave BDD Version)

## 專案根目錄與預設路徑（chapter04）

**約定**：`{Workspace}` = `chapter04/`（專案根目錄），其下最重要的資料夾是 `app/`, `specs/`, `tests/`。

- **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
- **Step Definitions**：`{Workspace}/tests/features/steps/`
- **Behave Environment**：`{Workspace}/tests/features/environment.py`

## Role

負責實作 `When` 步驟中的 Query（查詢）操作。

**核心任務**：直接呼叫 Service 方法執行讀取操作，將結果儲存到 `context.query_result` 供後續 Then 步驟驗證。

---

## ⚠️ 與 Command 的差異

| 項目 | Command | Query |
|------|---------|-------|
| 目的 | 修改系統狀態 | 讀取資料 |
| 回傳值 | 通常無回傳 | **有回傳值** |
| 結果處理 | 捕獲錯誤 | **儲存查詢結果** |

---

## Input

1. **Step Definition 樣板**：包含方法簽名、參數、TODO 註解
2. **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
3. **Gherkin 步驟原文**：從 Feature File 中提取

---

## 工作流程

### Step 1: 識別 Query

從 TODO 註解中識別需要執行的 Query：
```python
"""
TODO: [事件風暴部位: Query - get_lesson_progress]
TODO: 參考 Query-Handler.md 實作
"""
```

→ 需要呼叫的 Service 方法：`get_lesson_progress`

### Step 2: 分析 Gherkin 參數

從 Gherkin 步驟提取參數：
```gherkin
When 用戶 "Alice" 查詢課程 1 的進度
```

對應參數：
- `user_name` = "Alice" → 需要轉換為 `user_id`（從 `context.ids` 取得）
- `lesson_id` = 1

### Step 3: 實作 Step Definition

```python
from behave import when

@when('用戶 "{user_name}" 查詢課程 {lesson_id:d} 的進度')
def step_impl(context, user_name, lesson_id):
    # 1. 取得用戶 ID
    user_id = context.ids.get(user_name, user_name)
    
    # 2. 執行 Query
    try:
        result = context.services.lesson.get_lesson_progress(
            user_id=user_id,
            lesson_id=lesson_id
        )
        context.query_result = result  # 儲存查詢結果
        context.last_error = None
    except Exception as e:
        context.query_result = None
        context.last_error = e
```

---

## context.query_result

**重要**：`context.query_result` 直接作為屬性使用（不是 dict）。

```python
# tests/features/environment.py

def before_scenario(context, scenario):
    """每個 scenario 執行前初始化"""
    context.last_error = None
    context.query_result = None  # 直接屬性
    # ...
```

這樣後續的 Then 步驟可以透過 `context.query_result` 取得查詢結果。

---

## 查詢列表

當 Query 回傳多筆資料時：

```gherkin
When 用戶 "Alice" 查詢所有課程進度
```

```python
@when('用戶 "{user_name}" 查詢所有課程進度')
def step_impl(context, user_name):
    user_id = context.ids.get(user_name, user_name)
    
    try:
        results = context.services.lesson.get_all_progress(user_id=user_id)
        context.query_result = results  # 列表
        context.last_error = None
    except Exception as e:
        context.query_result = None
        context.last_error = e
```

---

## 查詢統計

當 Query 回傳統計資料時：

```gherkin
When 用戶 "Alice" 查詢課程完成統計
```

```python
@when('用戶 "{user_name}" 查詢課程完成統計')
def step_impl(context, user_name):
    user_id = context.ids.get(user_name, user_name)
    
    try:
        stats = context.services.lesson.get_statistics(user_id=user_id)
        context.query_result = stats  # dict 或其他型別
        context.last_error = None
    except Exception as e:
        context.query_result = None
        context.last_error = e
```

---

## 完整範例

### Input (Feature File)

```gherkin
Feature: 課程平台 - 查詢課程進度

Scenario: 查詢課程進度
  Given 用戶 "Alice" 在課程 1 的進度為 80%，狀態為 "進行中"
  When 用戶 "Alice" 查詢課程 1 的進度
  Then 查詢結果應包含進度 80，狀態為 "進行中"
```

### Output (Step Definition)

```python
# tests/features/steps/queries.py

from behave import when

@when('用戶 "{user_name}" 查詢課程 {lesson_id:d} 的進度')
def step_impl(context, user_name, lesson_id):
    """查詢用戶的課程進度"""
    # 1. 取得用戶 ID
    user_id = context.ids.get(user_name, user_name)
    
    # 2. 執行 Query
    try:
        result = context.services.lesson.get_lesson_progress(
            user_id=user_id,
            lesson_id=lesson_id
        )
        context.query_result = result
        context.last_error = None
    except Exception as e:
        context.query_result = None
        context.last_error = e
```

---

## 使用 helpers 簡化

當多個 Query steps 都有 try-except 模式時，可以抽取為 helper：

```python
# tests/features/steps/helpers.py

def execute_query(context, query_func):
    """執行 Query 並儲存結果"""
    try:
        context.query_result = query_func()
        context.last_error = None
    except Exception as e:
        context.query_result = None
        context.last_error = e
```

使用 helper 後：

```python
# tests/features/steps/queries.py

from behave import when
from steps.helpers import get_user_id, execute_query

@when('用戶 "{user_name}" 查詢課程 {lesson_id:d} 的進度')
def step_impl(context, user_name, lesson_id):
    """查詢用戶的課程進度"""
    user_id = get_user_id(context, user_name)
    
    execute_query(
        context,
        lambda: context.services.lesson.get_lesson_progress(
            user_id=user_id,
            lesson_id=lesson_id
        )
    )
```

---

## Critical Rules

### R1: Query 必須儲存結果
將查詢結果儲存到 `context.query_result`。

### R2: Query 也需要捕獲錯誤
使用 try-except 包裹 Service 呼叫。

### R3: 從 context 取得依賴
所有 Service 從 `context.services.*` 取得。

### R4: user_name → user_id 轉換
使用 `context.ids.get(user_name, user_name)` 取得用戶 ID。

### R5: context.query_result 是直接屬性
不使用 dict，直接賦值：`context.query_result = result`。

### R6: 函數簽名規則
第一個參數必須是 `context`，後接從 pattern 解析的參數。

---

**文件建立日期**：2025-12-28
**文件版本**：Behave BDD Unit Test Version 2.0
**適用框架**：Python + Behave
