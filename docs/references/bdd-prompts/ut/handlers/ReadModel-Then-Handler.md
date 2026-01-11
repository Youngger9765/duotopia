# ReadModel-Then-Handler (Behave BDD Version)

## 專案根目錄與預設路徑（chapter04）

**約定**：`{Workspace}` = `chapter04/`（專案根目錄），其下最重要的資料夾是 `app/`, `specs/`, `tests/`。

- **Step Definitions**：`{Workspace}/tests/features/steps/`
- **Behave Environment**：`{Workspace}/tests/features/environment.py`

## Role

負責實作 `Then` 步驟中驗證 Query 查詢結果的邏輯。

**核心任務**：從 `context.query_result` 取得查詢結果並驗證內容。

---

## ⚠️ 與 Aggregate-Then 的差異

| 項目 | Aggregate Then | ReadModel Then |
|------|---------------|---------------|
| 資料來源 | Repository 查詢 | **context.query_result** |
| 操作 | 執行 Repository 查詢 | **只讀取 context.query_result** |
| 前置步驟 | Command | **Query** |

**關鍵規則**：
- **ReadModel Then 不能重新執行 Query**
- **只能讀取 When 步驟儲存的 `context.query_result`**

---

## Input

1. **Step Definition 樣板**：包含方法簽名、參數、TODO 註解
2. **Gherkin 步驟原文**：從 Feature File 中提取
3. **Query 結果型別**：從對應的 Service 方法了解回傳型別

---

## 工作流程

### Step 1: 確認前置條件

檢查前一個 When 步驟是否為 Query：
```gherkin
When 用戶 "Alice" 查詢課程 1 的進度
Then 查詢結果應包含進度 80，狀態為 "進行中"
```

→ 前置步驟是 Query，因此使用 ReadModel-Then-Handler

### Step 2: 分析 Gherkin 參數

從 Gherkin 步驟提取驗證參數：
```gherkin
Then 查詢結果應包含進度 80，狀態為 "進行中"
```

對應參數：
- `progress` = 80
- `status` = "進行中" → 需要轉換為 "IN_PROGRESS"

### Step 3: 實作 Step Definition

```python
from behave import then

@then('查詢結果應包含進度 {progress:d}，狀態為 "{status}"')
def step_impl(context, progress, status):
    # 1. 從 context.query_result 取得結果（不重新查詢）
    result = context.query_result
    
    # 2. 驗證結果不為空
    assert result is not None, "查詢結果為空"
    
    # 3. 狀態映射
    status_map = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    expected_status = status_map.get(status, status)
    
    # 4. 驗證結果內容
    assert result.progress == progress, \
        f"預期進度 {progress}，實際為 {result.progress}"
    assert result.status == expected_status, \
        f"預期狀態 {expected_status}，實際為 {result.status}"
```

---

## 驗證列表結果

當 Query 回傳列表時：

```gherkin
Then 查詢結果應包含 2 筆課程進度
```

```python
@then('查詢結果應包含 {count:d} 筆課程進度')
def step_impl(context, count):
    result = context.query_result
    
    assert result is not None, "查詢結果為空"
    assert len(result) == count, \
        f"預期 {count} 筆資料，實際為 {len(result)} 筆"
```

---

## 驗證列表內容（使用 DataTable）

當需要驗證列表中的每個項目時：

```gherkin
Then 查詢結果應包含以下課程進度：
  | lessonId | progress | status |
  | 1        | 80       | 進行中  |
  | 2        | 100      | 已完成  |
```

```python
@then('查詢結果應包含以下課程進度：')
def step_impl(context):
    result = context.query_result
    
    assert result is not None, "查詢結果為空"
    assert len(result) == len(context.table), \
        f"預期 {len(context.table)} 筆資料，實際為 {len(result)} 筆"
    
    # 驗證每一筆資料
    for i, row in enumerate(context.table):
        expected_lesson_id = int(row['lessonId'])
        expected_progress = int(row['progress'])
        expected_status_cn = row['status']
        
        actual = result[i]
        
        assert actual.lesson_id == expected_lesson_id
        assert actual.progress == expected_progress
        # 狀態映射...
```

---

## 驗證單一欄位

當只需要驗證某個欄位時：

```gherkin
Then 查詢結果應包含：
  | progress | 80 |
```

```python
@then('查詢結果應包含：')
def step_impl(context):
    result = context.query_result
    
    assert result is not None, "查詢結果為空"
    
    # context.table 只有一行資料
    row = context.table[0]
    
    for key, value in row.items():
        actual_value = getattr(result, key)
        if value.isdigit():
            assert actual_value == int(value), \
                f"欄位 {key}：預期 {value}，實際為 {actual_value}"
        else:
            assert actual_value == value, \
                f"欄位 {key}：預期 {value}，實際為 {actual_value}"
```

---

## 驗證空結果

當預期查詢結果為空時：

```gherkin
Then 查詢結果應為空
```

```python
@then('查詢結果應為空')
def step_impl(context):
    result = context.query_result
    
    # 根據回傳型別判斷是否為空
    if result is None:
        return  # 空的
    elif isinstance(result, list):
        assert len(result) == 0, f"預期空列表，但包含 {len(result)} 筆資料"
    else:
        assert False, f"預期空結果，但回傳 {result}"
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
# tests/features/steps/queries.py (When Query)

from behave import when

@when('用戶 "{user_name}" 查詢課程 {lesson_id:d} 的進度')
def step_impl(context, user_name, lesson_id):
    user_id = context.ids.get(user_name, user_name)
    
    try:
        result = context.services.lesson.get_lesson_progress(
            user_id=user_id,
            lesson_id=lesson_id
        )
        context.query_result = result  # 儲存結果
        context.last_error = None
    except Exception as e:
        context.query_result = None
        context.last_error = e
```

```python
# tests/features/steps/readmodel.py (Then ReadModel)

from behave import then

@then('查詢結果應包含進度 {progress:d}，狀態為 "{status}"')
def step_impl(context, progress, status):
    """驗證查詢結果的進度和狀態"""
    # 1. 從 context.query_result 取得結果
    result = context.query_result
    
    # 2. 驗證結果不為空
    assert result is not None, "查詢結果為空"
    
    # 3. 狀態映射
    status_map = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    expected_status = status_map.get(status, status)
    
    # 4. 驗證結果內容
    assert result.progress == progress, \
        f"預期進度 {progress}，實際為 {result.progress}"
    assert result.status == expected_status, \
        f"預期狀態 {expected_status}，實際為 {result.status}"
```

---

## Critical Rules

### R1: 使用 context.query_result
從 `context.query_result` 取得查詢結果（不是重新查詢）。

### R2: Then 不得重新執行 Query
ReadModel Then 只負責驗證，不執行任何 Service 呼叫。

### R3: 驗證前檢查結果不為空
先確認 `context.query_result is not None`。

### R4: 狀態映射
中文狀態需要轉換為英文 enum（如 "進行中" → "IN_PROGRESS"）。

### R5: 使用 helpers 簡化
狀態映射等重複邏輯可以抽取到 `tests/features/steps/helpers.py`。

### R6: 函數簽名規則
第一個參數必須是 `context`，後接從 pattern 解析的參數。

---

**文件建立日期**：2025-12-28
**文件版本**：Behave BDD Unit Test Version 2.0
**適用框架**：Python + Behave
