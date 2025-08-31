# 測試組織結構

## 目錄結構
```
tests/
├── unit/                      # 單元測試 (快速、無依賴)
│   ├── test_models.py        # 資料模型測試
│   ├── test_schemas.py       # Pydantic schema 測試
│   └── test_utils.py         # 工具函數測試
│
├── integration/               # 整合測試 (需要資料庫)
│   ├── auth/
│   │   ├── test_teacher_auth.py
│   │   └── test_student_auth.py
│   ├── api/
│   │   ├── test_classrooms_api.py
│   │   ├── test_students_api.py
│   │   └── test_assignments_api.py
│   └── test_database.py
│
├── e2e/                       # 端到端測試 (完整流程)
│   ├── test_teacher_workflow.py
│   ├── test_student_workflow.py
│   └── test_assignment_lifecycle.py
│
├── fixtures/                  # 測試資料
│   ├── users.json
│   ├── classrooms.json
│   └── factory.py           # 測試資料工廠
│
├── performance/              # 效能測試 (選用)
│   └── test_load.py
│
└── conftest.py              # pytest 全域設定
```

## 測試命名規範

### 檔案命名
- `test_*.py` - pytest 自動發現
- 按功能分組，不要太大的檔案

### 函數命名
```python
def test_should_create_user_when_valid_data():
    """測試：當提供有效資料時應該建立使用者"""
    pass

def test_should_raise_error_when_email_exists():
    """測試：當 email 已存在時應該拋出錯誤"""
    pass
```

## 執行測試

```bash
# 執行所有測試
pytest

# 只執行單元測試 (快速)
pytest tests/unit/

# 只執行整合測試
pytest tests/integration/

# 執行特定模組
pytest tests/integration/api/test_classrooms_api.py

# 執行並顯示覆蓋率
pytest --cov=backend tests/

# 執行時顯示輸出
pytest -v -s
```

## 測試標記 (Markers)

```python
# 在 conftest.py 定義
pytest.ini:
[pytest]
markers =
    unit: Unit tests (fast, no dependencies)
    integration: Integration tests (needs database)
    e2e: End-to-end tests (full flow)
    slow: Slow tests
    auth: Authentication tests
```

使用方式：
```python
@pytest.mark.unit
def test_password_hash():
    pass

@pytest.mark.integration
@pytest.mark.auth
def test_login_with_database():
    pass
```

執行特定標記：
```bash
pytest -m unit           # 只執行單元測試
pytest -m "not slow"     # 跳過慢測試
pytest -m "auth and integration"  # 組合條件
```

## CI/CD 整合

```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - name: Run unit tests
        run: pytest tests/unit/ --maxfail=1
        
      - name: Run integration tests
        run: pytest tests/integration/
        
      - name: Run e2e tests
        if: github.ref == 'refs/heads/main'
        run: pytest tests/e2e/
```