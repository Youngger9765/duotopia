# Success-Failure-Handler (Behave BDD Version)

## 專案根目錄與預設路徑（chapter04）

**約定**：`{Workspace}` = `chapter04/`（專案根目錄），其下最重要的資料夾是 `app/`, `specs/`, `tests/`。

- **Step Definitions**：`{Workspace}/tests/features/steps/`
- **Behave Environment**：`{Workspace}/tests/features/environment.py`

## Role

負責實作 `Then` 步驟中驗證操作成功或失敗的邏輯。

**核心任務**：檢查 `context.last_error` 是否為 None 來判斷操作結果。

---

## 已實作步驟

這些步驟應該在 `tests/features/steps/common_then.py` 中預先實作，不需要每次生成：

```python
# tests/features/steps/common_then.py

from behave import then

@then("操作成功")
def step_impl(context):
    """驗證操作成功（沒有錯誤）"""
    assert context.last_error is None, \
        f"預期操作成功，但發生錯誤：{context.last_error}"

@then("操作失敗")
def step_impl(context):
    """驗證操作失敗（有錯誤）"""
    assert context.last_error is not None, \
        "預期操作失敗，但沒有發生錯誤"
```

---

## 擴展：驗證特定錯誤類型

如果需要驗證特定的錯誤類型：

```gherkin
Then 操作失敗，錯誤類型為 "InvalidStateError"
```

```python
@then('操作失敗，錯誤類型為 "{error_type}"')
def step_impl(context, error_type):
    """驗證操作失敗，並檢查錯誤類型"""
    error = context.last_error
    
    assert error is not None, "預期操作失敗，但沒有發生錯誤"
    assert type(error).__name__ == error_type, \
        f"預期錯誤類型 {error_type}，實際為 {type(error).__name__}"
```

---

## 擴展：驗證錯誤訊息

如果需要驗證錯誤訊息內容：

```gherkin
Then 操作失敗，錯誤訊息包含 "進度不可倒退"
```

```python
@then('操作失敗，錯誤訊息包含 "{message}"')
def step_impl(context, message):
    """驗證操作失敗，並檢查錯誤訊息"""
    error = context.last_error
    
    assert error is not None, "預期操作失敗，但沒有發生錯誤"
    assert message in str(error), \
        f"預期錯誤訊息包含 '{message}'，實際為 '{str(error)}'"
```

---

## 擴展：驗證錯誤代碼

如果錯誤物件有 code 屬性：

```gherkin
Then 操作失敗，錯誤代碼為 "INVALID_STATE"
```

```python
@then('操作失敗，錯誤代碼為 "{error_code}"')
def step_impl(context, error_code):
    """驗證操作失敗，並檢查錯誤代碼"""
    error = context.last_error
    
    assert error is not None, "預期操作失敗，但沒有發生錯誤"
    assert hasattr(error, 'code'), "錯誤物件沒有 code 屬性"
    assert error.code == error_code, \
        f"預期錯誤代碼 {error_code}，實際為 {error.code}"
```

---

## environment.py 設定

```python
# tests/features/environment.py

def before_scenario(context, scenario):
    """每個 scenario 執行前初始化"""
    # 初始化狀態（包含 last_error）
    context.last_error = None
    context.query_result = None
    context.ids = {}
    context.memo = {}
    
    # 初始化依賴
    # ...

def after_scenario(context, scenario):
    """每個 scenario 執行後清理"""
    context.last_error = None
    # ...
```

---

## 使用範例

### Scenario：成功案例

```gherkin
Feature: 增加影片進度

Scenario: 成功增加影片進度
  Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
  When 用戶 "Alice" 更新課程 1 的影片進度為 80%
  Then 操作成功
```

### Scenario：失敗案例

```gherkin
Scenario: 進度不可倒退
  Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
  When 用戶 "Alice" 更新課程 1 的影片進度為 60%
  Then 操作失敗
```

---

## 完整的 common_then.py

```python
# tests/features/steps/common_then.py

from behave import then

# ============================================================
# 基本操作成功/失敗驗證
# ============================================================

@then("操作成功")
def step_impl(context):
    """驗證操作成功（沒有錯誤）"""
    assert context.last_error is None, \
        f"預期操作成功，但發生錯誤：{context.last_error}"

@then("操作失敗")
def step_impl(context):
    """驗證操作失敗（有錯誤）"""
    assert context.last_error is not None, \
        "預期操作失敗，但沒有發生錯誤"

# ============================================================
# 擴展：驗證特定錯誤類型
# ============================================================

@then('操作失敗，錯誤類型為 "{error_type}"')
def step_impl(context, error_type):
    """驗證操作失敗，並檢查錯誤類型"""
    error = context.last_error
    
    assert error is not None, "預期操作失敗，但沒有發生錯誤"
    assert type(error).__name__ == error_type, \
        f"預期錯誤類型 {error_type}，實際為 {type(error).__name__}"

# ============================================================
# 擴展：驗證錯誤訊息
# ============================================================

@then('操作失敗，錯誤訊息包含 "{message}"')
def step_impl(context, message):
    """驗證操作失敗，並檢查錯誤訊息"""
    error = context.last_error
    
    assert error is not None, "預期操作失敗，但沒有發生錯誤"
    assert message in str(error), \
        f"預期錯誤訊息包含 '{message}'，實際為 '{str(error)}'"
```

---

## Critical Rules

### R1: 使用 context.last_error
從 `context.last_error` 取得錯誤物件（直接屬性，不是 dict）。

### R2: 成功時 last_error 為 None
當操作成功時，`context.last_error` 應為 `None`。

### R3: 失敗時 last_error 不為 None
當操作失敗時，`context.last_error` 應包含例外物件。

### R4: 這是預設已實作的步驟
`操作成功` 和 `操作失敗` 應該在 `common_then.py` 中預先實作。

### R5: 擴展時保持一致
擴展驗證（如錯誤類型、錯誤訊息）時，保持相同的 context 使用模式。

### R6: 函數簽名規則
第一個參數必須是 `context`，後接從 pattern 解析的參數。

---

**文件建立日期**：2025-12-28
**文件版本**：Behave BDD Unit Test Version 2.0
**適用框架**：Python + Behave
