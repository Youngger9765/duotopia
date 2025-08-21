# 📋 Duotopia 測試指南

本文件說明如何執行 Duotopia 專案的各種測試。

## 🏗️ 測試架構總覽

```
測試分層：
├── 單元測試 (Unit Tests) - 測試單一功能模組
├── 整合測試 (Integration Tests) - 測試模組間互動
└── E2E 測試 (End-to-End Tests) - 測試完整使用流程
```

## 🔧 環境設置

### 後端測試環境
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### 前端測試環境
```bash
npm install
# Jest 和 React Testing Library 已包含在 package.json 中
```

## 🧪 後端測試

### 執行所有測試
```bash
cd backend
python -m pytest
```

### 執行特定類型測試
```bash
# 單元測試
python run_tests.py --type unit

# 整合測試
python run_tests.py --type integration

# E2E 測試
python run_tests.py --type e2e

# 所有測試（預設）
python run_tests.py --type all
```

### 執行特定測試檔案
```bash
python run_tests.py -f tests/unit/test_auth_unit.py
```

### 產生測試覆蓋率報告
```bash
python run_tests.py --coverage
# 報告會產生在 htmlcov/index.html
```

### 顯示詳細輸出
```bash
python run_tests.py -v
```

## 🎨 前端測試

### 執行所有測試
```bash
npm test
```

### 監聽模式（開發時使用）
```bash
npm run test:watch
```

### 產生覆蓋率報告
```bash
npm run test:coverage
```

### 執行特定測試檔案
```bash
npm test -- src/components/__tests__/StudentForm.test.tsx
```

## 📁 測試檔案結構

### 後端測試結構
```
backend/tests/
├── conftest.py              # Pytest fixtures
├── unit/                    # 單元測試
│   ├── test_auth_unit.py
│   ├── test_classroom_management_unit.py
│   ├── test_student_management_unit.py
│   └── test_course_management_unit.py
├── integration/             # 整合測試
│   └── test_dual_system_api.py
└── e2e/                     # 端對端測試
    ├── test_classroom_detail.py
    └── test_student_management.py
```

### 前端測試結構
```
frontend/src/
├── setupTests.ts                    # 測試設定
├── components/__tests__/            # 元件測試
│   ├── StudentForm.test.tsx
│   └── ClassroomCard.test.tsx
├── contexts/__tests__/              # Context 測試
│   └── AuthContext.test.tsx
└── hooks/__tests__/                 # Hook 測試
    └── useStudents.test.tsx
```

## 🎯 測試重點

### 認證系統測試
- ✅ 教師登入/登出
- ✅ 學生四步驟登入
- ✅ JWT token 管理
- ✅ 密碼雜湊與驗證
- ✅ 角色切換功能

### 班級管理測試
- ✅ 建立/編輯/刪除班級
- ✅ 班級容量限制
- ✅ 學生分配到班級
- ✅ 批量操作功能

### 學生管理測試
- ✅ 新增/編輯/刪除學生
- ✅ 預設密碼生成（生日）
- ✅ 密碼狀態追蹤
- ✅ 批量匯入功能
- ✅ 搜尋與篩選

### 課程管理測試
- ✅ 建立/編輯課程
- ✅ 從模板複製課程
- ✅ 單元管理（CRUD）
- ✅ 活動類型配置
- ✅ 課程分配到班級

## 🚀 CI/CD 測試

GitHub Actions 會自動執行測試：

```yaml
# .github/workflows/test.yml
- 每次 Push 執行測試
- Pull Request 時執行測試
- 測試失敗會阻擋合併
```

## 📊 測試標準

### 單元測試
- 每個函數/方法都應有對應測試
- 測試覆蓋率目標：80%
- Mock 外部依賴

### 整合測試
- 測試 API 端點
- 測試資料庫互動
- 使用測試資料庫

### E2E 測試
- 測試完整使用者流程
- 使用 Playwright（前端）
- 模擬真實使用情境

## 🐛 常見問題

### 後端測試失敗
1. 確認虛擬環境已啟動
2. 確認測試資料庫設定正確
3. 清除 pytest cache：`pytest --cache-clear`

### 前端測試失敗
1. 確認 node_modules 已安裝
2. 清除 Jest cache：`npm test -- --clearCache`
3. 確認 TypeScript 類型正確

### 測試資料庫
後端測試使用 SQLite in-memory 資料庫，不會影響開發資料庫。

## 📝 撰寫新測試

### 後端測試範例
```python
import pytest
from models import Student

class TestStudentModel:
    def test_create_student(self, db):
        student = Student(name="測試學生", ...)
        db.add(student)
        db.commit()
        
        assert student.id is not None
```

### 前端測試範例
```typescript
import { render, screen } from '@testing-library/react';
import { StudentForm } from '../StudentForm';

test('renders student form', () => {
  render(<StudentForm />);
  expect(screen.getByLabelText(/姓名/)).toBeInTheDocument();
});
```

## 🔍 測試除錯

### 執行單一測試
```bash
# 後端
pytest -k "test_create_student" -v

# 前端
npm test -- -t "renders student form"
```

### 顯示 print 輸出
```bash
# 後端
pytest -s

# 前端（使用 console.log）
npm test -- --verbose
```

---

記住：**寫測試是為了提高程式碼品質，而不是為了通過測試！**