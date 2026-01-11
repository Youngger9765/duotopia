# Aggregate-Then-Handler (Behave BDD Version)

## 專案根目錄與預設路徑（chapter04）

**約定**：`{Workspace}` = `chapter04/`（專案根目錄），其下最重要的資料夾是 `app/`, `specs/`, `tests/`。

- **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
- **Step Definitions**：`{Workspace}/tests/features/steps/`
- **Behave Environment**：`{Workspace}/tests/features/environment.py`

## Role

負責實作 `Then` 步驟中驗證 Aggregate 最終狀態的邏輯。

**核心任務**：透過 Repository（從 `context.repos.*` 取得）查詢 Aggregate 狀態並驗證。

---

## ⚠️ 注意事項

- **透過 Repository 查詢**：使用 `context.repos.*.find()` 查詢資料
- **驗證狀態**：使用 `assert` 驗證 Aggregate 的屬性值
- **不透過 Service**：直接使用 Repository 查詢
- **從 context 取得 Repository**：所有 Repository 從 `context.repos.*` 取得

---

## Input

1. **Step Definition 樣板**：包含方法簽名、參數、TODO 註解
2. **DBML（Aggregate 定義）**：`{Workspace}/specs/erm.dbml`
3. **Gherkin 步驟原文**：從 Feature File 中提取

---

## 工作流程

### Step 1: 識別 Aggregate

從 TODO 註解中識別需要驗證的 Aggregate：
```python
"""
TODO: [事件風暴部位: Aggregate - LessonProgress]
TODO: 參考 Aggregate-Then-Handler.md 實作
TODO: 參考 Aggregate/Table: LessonProgress
"""
```

→ 需要驗證的 Aggregate：`LessonProgress`

### Step 2: 查找 DBML 定義

從 `erm.dbml` 中找到對應的 Table 定義，確認可驗證的屬性。

### Step 3: 提取 Gherkin 參數

從 Gherkin 步驟提取需要驗證的值：
```gherkin
Then 用戶 "Alice" 在課程 1 的進度應為 80%
```

對應參數：
- `user_name` = "Alice"
- `lesson_id` = 1
- `progress` = 80（預期值）

### Step 4: 實作 Step Definition

```python
from behave import then

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # 1. 取得用戶 ID
    user_id = context.ids.get(user_name, user_name)
    
    # 2. 從 Repository 查詢
    lesson_progress = context.repos.lesson_progress.find(
        user_id=user_id,
        lesson_id=lesson_id
    )
    
    # 3. 驗證
    assert lesson_progress is not None, \
        f"找不到用戶 {user_name} 在課程 {lesson_id} 的進度"
    assert lesson_progress.progress == progress, \
        f"預期進度 {progress}%，實際為 {lesson_progress.progress}%"
```

---

## 驗證多個屬性

當 Gherkin 需要驗證多個屬性時：

```gherkin
Then 用戶 "Alice" 在課程 1 的進度應為 80%，狀態為 "進行中"
```

**實作方式**：

```python
@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    user_id = context.ids.get(user_name, user_name)
    
    # 狀態映射
    status_map = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    expected_status = status_map.get(status, status)
    
    # 查詢
    lesson_progress = context.repos.lesson_progress.find(
        user_id=user_id,
        lesson_id=lesson_id
    )
    
    # 驗證
    assert lesson_progress is not None
    assert lesson_progress.progress == progress, \
        f"預期進度 {progress}%，實際為 {lesson_progress.progress}%"
    assert lesson_progress.status == expected_status, \
        f"預期狀態 {expected_status}，實際為 {lesson_progress.status}"
```

---

## 驗證 DataTable

當 Gherkin 使用 DataTable 驗證多筆資料時：

```gherkin
Then 系統中應有以下課程進度：
  | userName | lessonId | progress | status |
  | Alice | 1 | 80 | 進行中 |
  | Bob | 1 | 100 | 已完成 |
```

**實作方式**：

```python
@then('系統中應有以下課程進度：')
def step_impl(context):
    # context.table 由 Behave 自動填充
    status_map = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    
    for row in context.table:
        user_name = row['userName']
        lesson_id = int(row['lessonId'])
        expected_progress = int(row['progress'])
        expected_status = status_map.get(row['status'], row['status'])
        
        user_id = context.ids.get(user_name, user_name)
        actual = context.repos.lesson_progress.find(user_id, lesson_id)
        
        assert actual is not None, \
            f"找不到用戶 {user_name} 在課程 {lesson_id} 的進度"
        assert actual.progress == expected_progress, \
            f"用戶 {user_name} 課程 {lesson_id}：預期進度 {expected_progress}%，實際為 {actual.progress}%"
        assert actual.status == expected_status, \
            f"用戶 {user_name} 課程 {lesson_id}：預期狀態 {expected_status}，實際為 {actual.status}"
```

---

## 驗證不存在

當 Gherkin 需要驗證資料不存在時：

```gherkin
Then 用戶 "Alice" 在課程 1 的進度記錄不存在
```

**實作方式**：

```python
@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度記錄不存在')
def step_impl(context, user_name, lesson_id):
    user_id = context.ids.get(user_name, user_name)
    
    lesson_progress = context.repos.lesson_progress.find(
        user_id=user_id,
        lesson_id=lesson_id
    )
    
    assert lesson_progress is None, \
        f"預期不存在，但找到了用戶 {user_name} 在課程 {lesson_id} 的進度"
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
# tests/features/steps/aggregate_then.py

from behave import then

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """驗證用戶的課程進度"""
    # 1. 取得用戶 ID
    user_id = context.ids.get(user_name, user_name)
    
    # 2. 從 Repository 查詢
    lesson_progress = context.repos.lesson_progress.find(
        user_id=user_id,
        lesson_id=lesson_id
    )
    
    # 3. 驗證
    assert lesson_progress is not None, \
        f"找不到用戶 {user_name} 在課程 {lesson_id} 的進度"
    assert lesson_progress.progress == progress, \
        f"預期進度 {progress}%，實際為 {lesson_progress.progress}%"
```

---

## 使用 helpers 簡化

當多個 Then steps 都有驗證邏輯時，可以抽取為 helper：

```python
# tests/features/steps/helpers.py

def assert_lesson_progress(
    context,
    user_name,
    lesson_id,
    expected_progress=None,
    expected_status=None,
):
    """驗證課程進度"""
    user_id = context.ids.get(user_name, user_name)
    actual = context.repos.lesson_progress.find(user_id, lesson_id)
    
    assert actual is not None, f"找不到用戶 {user_name} 在課程 {lesson_id} 的進度"
    
    if expected_progress is not None:
        assert actual.progress == expected_progress, \
            f"預期進度 {expected_progress}%，實際為 {actual.progress}%"
    
    if expected_status is not None:
        assert actual.status == expected_status, \
            f"預期狀態 {expected_status}，實際為 {actual.status}"
```

使用 helper 後：

```python
# tests/features/steps/aggregate_then.py

from behave import then
from steps.helpers import assert_lesson_progress, translate_status

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """驗證用戶的課程進度"""
    assert_lesson_progress(context, user_name, lesson_id, expected_progress=progress)

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的狀態應為 "{status}"')
def step_impl(context, user_name, lesson_id, status):
    """驗證用戶的課程狀態"""
    status_en = translate_status(status)
    assert_lesson_progress(context, user_name, lesson_id, expected_status=status_en)

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """驗證用戶的課程進度和狀態"""
    status_en = translate_status(status)
    assert_lesson_progress(context, user_name, lesson_id, expected_progress=progress, expected_status=status_en)
```

---

## Critical Rules

### R1: 透過 Repository 查詢
使用 `context.repos.*.find()` 查詢資料。

### R2: 從 context 取得 Repository
所有 Repository 從 `context.repos.*` 取得。

### R3: user_name → user_id 轉換
使用 `context.ids.get(user_name, user_name)` 取得用戶 ID。

### R4: 狀態映射
中文狀態需要轉換為英文 enum。

### R5: 驗證前檢查不為空
先確認查詢結果不為 None。

### R6: DataTable 從 context.table 取得
Behave 自動將 DataTable 填充到 `context.table`。

### R7: 函數簽名規則
第一個參數必須是 `context`，後接從 pattern 解析的參數。

---

**文件建立日期**：2025-12-28
**文件版本**：Behave BDD Unit Test Version 2.0
**適用框架**：Python + Behave
