# Command-Handler (Behave BDD Version)

## 專案根目錄與預設路徑（chapter04）

**約定**：`{Workspace}` = `chapter04/`（專案根目錄），其下最重要的資料夾是 `app/`, `specs/`, `tests/`。

- **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
- **Step Definitions**：`{Workspace}/tests/features/steps/`
- **Behave Environment**：`{Workspace}/tests/features/environment.py`

## Role

負責實作 `Given`（已完成的動作）和 `When`（執行中的動作）步驟中的 Command 操作。

**核心任務**：直接呼叫 Service 方法執行寫入操作。

---

## ⚠️ 與 E2E 版本的關鍵差異

| 項目 | E2E 版本 | Unit Test 版本 |
|------|---------|---------------|
| 執行方式 | MockMvc HTTP POST | **直接呼叫 Service 方法** |
| 認證 | JWT Token | **不需認證** |
| 結果處理 | 儲存 MvcResult | **捕獲 Exception** |
| 依賴注入 | Spring Context | **context.services.*** |

---

## Input

1. **Step Definition 樣板**：包含方法簽名、參數、TODO 註解
2. **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
3. **Gherkin 步驟原文**：從 Feature File 中提取

---

## 工作流程

### Step 1: 識別 Command

從 TODO 註解中識別需要執行的 Command：
```python
"""
TODO: [事件風暴部位: Command - update_video_progress]
TODO: 參考 Command-Handler.md 實作
"""
```

→ 需要呼叫的 Service 方法：`update_video_progress`

### Step 2: 分析 Gherkin 參數

從 Gherkin 步驟提取參數：
```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
```

對應參數：
- `user_name` = "Alice" → 需要轉換為 `user_id`（從 `context.ids` 取得）
- `lesson_id` = 1
- `progress` = 80

### Step 3: 實作 Step Definition

```python
from behave import when

@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # 1. 取得用戶 ID（從 context.ids）
    user_id = context.ids.get(user_name, user_name)
    
    # 2. 執行 Command（包裹在 try-except 中）
    try:
        context.services.lesson.update_video_progress(
            user_id=user_id,
            lesson_id=lesson_id,
            progress=progress
        )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

---

## Given vs When 的處理

### Given（已完成的動作 - 過去式）

用於建立前置條件，通常不需要驗證結果。

```gherkin
Given 用戶 "Alice" 已訂閱旅程 1
```

```python
@given('用戶 "{user_name}" 已訂閱旅程 {journey_id:d}')
def step_impl(context, user_name, journey_id):
    user_id = context.ids.get(user_name, user_name)
    
    # Given 通常假設成功，不需要 try-except
    context.services.journey.subscribe(
        user_id=user_id,
        journey_id=journey_id
    )
```

### When（執行中的動作 - 現在式）

用於執行待測試的操作，需要捕獲可能的錯誤。

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
```

```python
@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    user_id = context.ids.get(user_name, user_name)
    
    try:
        context.services.lesson.update_video_progress(
            user_id=user_id,
            lesson_id=lesson_id,
            progress=progress
        )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

---

## 處理 DataTable

當 Command 需要處理多筆資料時：

```gherkin
When 管理員批次建立以下用戶：
  | name | email |
  | Alice | alice@example.com |
  | Bob | bob@example.com |
```

```python
@when('管理員批次建立以下用戶：')
def step_impl(context):
    # context.table 由 Behave 自動填充
    try:
        for row in context.table:
            context.services.user.register(
                name=row['name'],
                email=row['email']
            )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

---

## 處理 DocString

當 Command 需要處理長文本時：

```gherkin
When 用戶 "Alice" 提交作業，內容為：
  """
  這是我的作業內容，
  包含多行文字。
  """
```

```python
@when('用戶 "{user_name}" 提交作業，內容為：')
def step_impl(context, user_name):
    user_id = context.ids.get(user_name, user_name)
    content = context.text  # DocString 內容（Behave 自動填充）
    
    try:
        context.services.assignment.submit(
            user_id=user_id,
            content=content
        )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

---

## 錯誤捕獲

**重要**：所有 When 步驟都需要捕獲錯誤，供後續 Then 步驟驗證。

```python
@when('...')
def step_impl(context, ...):
    try:
        # 執行 Command
        context.services.some_service.some_method(...)
        context.last_error = None  # 成功時清除錯誤
    except Exception as e:
        context.last_error = e  # 失敗時儲存錯誤
```

這樣後續的 `Then 操作成功` 或 `Then 操作失敗` 可以驗證結果。

---

## context.last_error

**重要**：`context.last_error` 直接作為屬性使用（不是 dict）。

```python
# tests/features/environment.py

def before_scenario(context, scenario):
    """每個 scenario 執行前初始化"""
    context.last_error = None  # 直接屬性
    # ...
```

**為什麼這樣設計？**

Behave 的 `context` 物件在同一個 scenario 中共享，可以直接修改屬性：
```python
# ✅ 正確：Behave 版本
def step_impl(context):
    context.last_error = some_error  # 直接賦值，其他 step 可以讀到

# ❌ 錯誤：pytest-bdd 的做法（不適用於 Behave）
# last_error["error"] = some_error
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
# tests/features/steps/commands.py

from behave import when

@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """更新用戶的影片觀看進度"""
    # 1. 取得用戶 ID
    user_id = context.ids.get(user_name, user_name)
    
    # 2. 執行 Command
    try:
        context.services.lesson.update_video_progress(
            user_id=user_id,
            lesson_id=lesson_id,
            progress=progress
        )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

---

## 其他範例

### 範例 1：不需要參數的 Command

```gherkin
When 用戶 "Alice" 交付課程 1
```

```python
@when('用戶 "{user_name}" 交付課程 {lesson_id:d}')
def step_impl(context, user_name, lesson_id):
    user_id = context.ids.get(user_name, user_name)
    
    try:
        context.services.lesson.deliver(
            user_id=user_id,
            lesson_id=lesson_id
        )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

### 範例 2：需要多個參數的 Command

```gherkin
When 用戶 "Alice" 提交課程 1 的挑戰題作業
```

```python
@when('用戶 "{user_name}" 提交課程 {lesson_id:d} 的挑戰題作業')
def step_impl(context, user_name, lesson_id):
    user_id = context.ids.get(user_name, user_name)
    
    try:
        context.services.challenge.submit(
            user_id=user_id,
            lesson_id=lesson_id
        )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

---

## 使用 helpers 簡化

當多個 Command steps 都有 try-except 模式時，可以抽取為 helper：

```python
# tests/features/steps/helpers.py

def execute_command(context, command_func):
    """執行 Command 並捕獲錯誤"""
    try:
        command_func()
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

使用 helper 後：

```python
# tests/features/steps/commands.py

from behave import when
from steps.helpers import get_user_id, execute_command

@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """更新用戶的影片觀看進度"""
    user_id = get_user_id(context, user_name)
    
    execute_command(
        context,
        lambda: context.services.lesson.update_video_progress(
            user_id=user_id,
            lesson_id=lesson_id,
            progress=progress
        )
    )
```

---

## Critical Rules

### R1: 所有 When 步驟必須捕獲錯誤
使用 try-except 包裹 Service 呼叫，將錯誤儲存到 `context.last_error`。

### R2: Given 通常不需要捕獲錯誤
Given 用於建立前置條件，通常假設成功。

### R3: 從 context 取得依賴
所有 Service 從 `context.services.*` 取得。

### R4: user_name → user_id 轉換
使用 `context.ids.get(user_name, user_name)` 取得用戶 ID。

### R5: DataTable 從 context.table 取得
Behave 自動將 DataTable 填充到 `context.table`。

### R6: DocString 從 context.text 取得
Behave 自動將 DocString 填充到 `context.text`。

### R7: context.last_error 是直接屬性
不使用 dict，直接賦值：`context.last_error = e`。

### R8: 函數簽名規則
第一個參數必須是 `context`，後接從 pattern 解析的參數。

---

**文件建立日期**：2025-12-28
**文件版本**：Behave BDD Unit Test Version 2.0
**適用框架**：Python + Behave
