# 測試文件組織結構

## 📁 測試目錄結構

```
tests/
├── README.md                     # 測試說明文件（本文件）
├── conftest.py                   # pytest 共用配置
│
├── unit/                         # 單元測試
│   ├── test_auth.py             # 認證功能測試
│   ├── test_models.py           # 資料模型測試
│   ├── test_schemas.py          # Pydantic schemas 測試
│   └── test_utils.py            # 工具函數測試
│
├── integration/                  # 整合測試（API測試）
│   ├── test_auth_api.py         # 認證 API 測試
│   ├── test_student_api.py      # 學生相關 API 測試
│   ├── test_teacher_api.py      # 教師相關 API 測試
│   ├── test_classroom_api.py    # 教室相關 API 測試
│   └── test_student_password_change.py  # 學生密碼修改 API 測試
│
├── e2e/                         # 端到端測試
│   ├── conftest.py              # E2E 測試配置
│   ├── run_tests.sh             # E2E 測試執行腳本
│   ├── test_complete_flows.py   # 完整業務流程測試
│   └── [其他現有的 E2E 測試]
│
└── fixtures/                    # 測試數據和夾具
    ├── sample_data.py           # 測試用的示例數據
    └── test_db.py               # 測試數據庫設置
```

## 🎯 測試分類原則

### 單元測試 (unit/)
- 測試單個函數或類別
- 不依賴外部系統（資料庫、API）
- 執行快速，覆蓋率高
- 檔名格式：`test_[模組名].py`

### 整合測試 (integration/)
- 測試 API 端點
- 涉及資料庫操作
- 測試不同模組間的協作
- 檔名格式：`test_[功能名]_api.py`

### 端到端測試 (e2e/)
- 測試完整的用戶流程
- 涉及前後端交互
- 執行較慢，但最接近真實使用
- 檔名格式：`test_[流程名].py`

## 🔧 執行測試

```bash
# 執行所有測試
pytest

# 執行特定分類的測試
pytest tests/unit/              # 僅執行單元測試
pytest tests/integration/      # 僅執行整合測試
pytest tests/e2e/              # 僅執行端到端測試

# 執行特定測試文件
pytest tests/integration/test_student_password_change.py

# 顯示覆蓋率報告
pytest --cov=. tests/
```

## 📋 測試命名規範

### 測試文件命名
- `test_[功能模組].py`
- 例如：`test_student_password_change.py`

### 測試函數命名
- `test_[測試場景]_[預期結果]()`
- 例如：`test_change_password_with_valid_data_should_success()`

### 測試類別命名
- `Test[功能名]`
- 例如：`TestStudentPasswordChange`

## 🚀 最佳實踐

1. **每個測試應該獨立運行**，不依賴其他測試的結果
2. **使用有意義的測試名稱**，清楚描述測試內容
3. **遵循 AAA 模式**：Arrange（準備）、Act（執行）、Assert（驗證）
4. **適當使用 fixtures**，避免重複的設置代碼
5. **測試覆蓋正常和異常情況**
6. **保持測試簡潔**，一個測試只驗證一個概念

## 📝 清理計畫

目前 backend 根目錄下散落的測試文件將按照以下原則重新組織：

- `test_*.py` → 移動到對應的分類目錄
- 重複或過時的測試文件 → 刪除或合併
- 建立統一的測試配置和工具函數