# 🧪 認證系統重構 TDD 流程

**目標**: 安全重構認證系統，修復 Token/LocalStorage 混亂問題
**原則**: 紅燈 → 綠燈 → 重構，絕不改壞現有功能
**參考**: [BUG_REPORT_AUTH_TOKEN.md](./BUG_REPORT_AUTH_TOKEN.md)

---

## 📋 TDD 工作流程

### Phase 0: 準備階段 ✅
- [x] 完成問題分析 ([BUG_REPORT_AUTH_TOKEN.md](./BUG_REPORT_AUTH_TOKEN.md))
- [ ] 建立測試計畫（本文件）
- [ ] 建立測試套件
- [ ] 執行測試確認紅燈

### Phase 1: 紅燈階段 🔴
**目標**: 建立測試，確認現有問題
- [ ] 建立前端測試檔案
- [ ] 建立後端測試檔案
- [ ] 執行測試，確認所有測試失敗（紅燈）

### Phase 2: 綠燈階段 🟢
**目標**: 逐步修復，讓所有測試通過
- [ ] P0-1: 建立 teacherAuthStore.ts
- [ ] P0-2: 統一 Teacher Login 使用新 store
- [ ] P0-3: 修復 API Client token 邏輯
- [ ] 執行測試，確認所有測試通過（綠燈）

### Phase 3: 重構階段 ♻️
**目標**: 清理冗餘代碼
- [ ] P1-4: 移除重複的 lib/auth.ts 或 utils/api.ts
- [ ] P1-5: 統一 logout 邏輯
- [ ] P1-6: 建立 ProtectedRoute component

---

## 🧪 測試案例設計

### 1. 前端測試 (Vitest)

#### Test Suite 1: TeacherAuthStore 測試
**檔案**: `frontend/src/stores/__tests__/teacherAuthStore.test.ts`

```typescript
describe('TeacherAuthStore', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('🔴 RED: 目前缺少 teacherAuthStore', () => {
    it('應該存在 useTeacherAuthStore', () => {
      // 這會失敗，因為目前沒有這個 store
      expect(useTeacherAuthStore).toBeDefined();
    });
  });

  describe('🟢 GREEN: 登入功能', () => {
    it('應該能正確登入並儲存 token', () => {
      const { login } = useTeacherAuthStore.getState();
      const mockToken = 'mock-jwt-token';
      const mockUser = { id: 1, name: 'Teacher', email: 'test@example.com' };

      login(mockToken, mockUser);

      const state = useTeacherAuthStore.getState();
      expect(state.token).toBe(mockToken);
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it('應該將資料持久化到 localStorage', () => {
      const { login } = useTeacherAuthStore.getState();
      login('test-token', { id: 1, name: 'Teacher', email: 'test@example.com' });

      const stored = localStorage.getItem('teacher-auth-storage');
      expect(stored).toBeDefined();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.token).toBe('test-token');
    });
  });

  describe('🟢 GREEN: 登出功能', () => {
    it('應該清除所有認證資料', () => {
      const { login, logout } = useTeacherAuthStore.getState();

      // 先登入
      login('test-token', { id: 1, name: 'Teacher', email: 'test@example.com' });

      // 登出
      logout();

      const state = useTeacherAuthStore.getState();
      expect(state.token).toBe(null);
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
    });
  });
});
```

#### Test Suite 2: Token 儲存一致性測試
**檔案**: `frontend/src/lib/__tests__/auth-consistency.test.ts`

```typescript
describe('認證系統一致性測試', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('🔴 RED: 目前 token 儲存混亂', () => {
    it('不應該同時存在多個 token keys', () => {
      // 模擬當前混亂狀態
      localStorage.setItem('token', 'old-token');
      localStorage.setItem('access_token', 'new-token');
      localStorage.setItem('auth-storage', JSON.stringify({ state: { token: 'auth-token' } }));

      // 應該只有一個有效的 token 來源
      const tokenKeys = ['token', 'access_token', 'auth-storage', 'teacher-auth-storage', 'student-auth-storage'];
      const existingKeys = tokenKeys.filter(key => localStorage.getItem(key));

      // 🔴 這會失敗，因為目前有多個 keys
      expect(existingKeys.length).toBeLessThanOrEqual(2); // 最多 teacher + student
    });
  });

  describe('🟢 GREEN: 統一 token 來源', () => {
    it('Teacher 登入應該只儲存在 teacher-auth-storage', () => {
      const { login } = useTeacherAuthStore.getState();
      login('teacher-token', { id: 1, name: 'Teacher', email: 'test@example.com' });

      // 檢查只有 teacher-auth-storage 存在
      expect(localStorage.getItem('teacher-auth-storage')).toBeDefined();
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('auth-storage')).toBeNull();
    });

    it('Student 登入應該只儲存在 student-auth-storage', () => {
      const { login } = useStudentAuthStore.getState();
      login('student-token', { id: 1, name: 'Student', student_number: 'S001', classroom_id: 1 });

      // 檢查只有 student-auth-storage 存在
      expect(localStorage.getItem('student-auth-storage')).toBeDefined();
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
    });
  });
});
```

#### Test Suite 3: API Client Token 測試
**檔案**: `frontend/src/lib/__tests__/api-token.test.ts`

```typescript
describe('API Client Token 管理', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('🔴 RED: getToken() 邏輯過於複雜', () => {
    it('應該從正確的 store 獲取 token', () => {
      // 設定 teacher token
      useTeacherAuthStore.getState().login('teacher-token', mockTeacherUser);

      const apiClient = new ApiClient();
      const token = (apiClient as any).getToken();

      // 🔴 目前會失敗，因為邏輯太複雜
      expect(token).toBe('teacher-token');
    });
  });

  describe('🟢 GREEN: 簡化 token 獲取邏輯', () => {
    it('Teacher 路由應該使用 teacherAuthStore', () => {
      useTeacherAuthStore.getState().login('teacher-token', mockTeacherUser);

      const apiClient = new ApiClient();
      const token = (apiClient as any).getToken();

      expect(token).toBe('teacher-token');
    });

    it('Student 路由應該使用 studentAuthStore', () => {
      useStudentAuthStore.getState().login('student-token', mockStudentUser);

      const apiClient = new ApiClient();
      const token = (apiClient as any).getToken();

      expect(token).toBe('student-token');
    });

    it('沒有登入時應該返回 null', () => {
      const apiClient = new ApiClient();
      const token = (apiClient as any).getToken();

      expect(token).toBeNull();
    });
  });
});
```

#### Test Suite 4: Logout 一致性測試
**檔案**: `frontend/src/lib/__tests__/logout-consistency.test.ts`

```typescript
describe('Logout 一致性測試', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('🔴 RED: 多處 logout 邏輯不一致', () => {
    it('所有 logout 應該清除相同的 keys', () => {
      // 設定初始狀態
      useTeacherAuthStore.getState().login('teacher-token', mockTeacherUser);
      localStorage.setItem('selectedPlan', JSON.stringify({ id: 1 }));

      // 測試 lib/api.ts 的 logout
      apiClient.logout();

      // 🔴 可能會失敗，因為清理不完整
      expect(localStorage.getItem('teacher-auth-storage')).toBeNull();
      expect(localStorage.getItem('student-auth-storage')).toBeNull();
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('selectedPlan')).toBeNull();
    });
  });

  describe('🟢 GREEN: 統一 logout 函數', () => {
    it('clearAllAuth() 應該清除所有認證資料', () => {
      // 設定 teacher 和 student 都登入
      useTeacherAuthStore.getState().login('teacher-token', mockTeacherUser);
      useStudentAuthStore.getState().login('student-token', mockStudentUser);
      localStorage.setItem('selectedPlan', JSON.stringify({ id: 1 }));

      // 執行統一 logout
      clearAllAuth();

      // 檢查所有都被清除
      expect(useTeacherAuthStore.getState().token).toBeNull();
      expect(useStudentAuthStore.getState().token).toBeNull();
      expect(localStorage.getItem('selectedPlan')).toBeNull();
    });
  });
});
```

---

### 2. 後端測試 (Pytest)

#### Test Suite 5: Token 驗證測試
**檔案**: `backend/tests/integration/auth/test_token_validation.py`

```python
import pytest
from fastapi.testclient import TestClient

class TestTokenValidation:
    """測試 JWT Token 驗證邏輯"""

    def test_valid_teacher_token(self, client: TestClient, teacher_token: str):
        """✅ 有效的 teacher token 應該能訪問 teacher API"""
        response = client.get(
            "/api/teachers/dashboard",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200

    def test_valid_student_token(self, client: TestClient, student_token: str):
        """✅ 有效的 student token 應該能訪問 student API"""
        response = client.get(
            "/api/students/dashboard",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200

    def test_teacher_token_cannot_access_student_api(self, client: TestClient, teacher_token: str):
        """❌ Teacher token 不能訪問 student API"""
        response = client.get(
            "/api/students/dashboard",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 403

    def test_student_token_cannot_access_teacher_api(self, client: TestClient, student_token: str):
        """❌ Student token 不能訪問 teacher API"""
        response = client.get(
            "/api/teachers/dashboard",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403

    def test_expired_token_rejected(self, client: TestClient, expired_token: str):
        """❌ 過期的 token 應該被拒絕"""
        response = client.get(
            "/api/teachers/dashboard",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_invalid_token_format_rejected(self, client: TestClient):
        """❌ 無效格式的 token 應該被拒絕"""
        response = client.get(
            "/api/teachers/dashboard",
            headers={"Authorization": "Bearer invalid-token-format"}
        )
        assert response.status_code == 401
```

---

## 📝 執行計畫

### Step 1: 建立測試檔案（紅燈階段）

```bash
# 1. 建立前端測試目錄
mkdir -p frontend/src/stores/__tests__
mkdir -p frontend/src/lib/__tests__

# 2. 建立測試檔案
touch frontend/src/stores/__tests__/teacherAuthStore.test.ts
touch frontend/src/lib/__tests__/auth-consistency.test.ts
touch frontend/src/lib/__tests__/api-token.test.ts
touch frontend/src/lib/__tests__/logout-consistency.test.ts

# 3. 建立後端測試檔案
touch backend/tests/integration/auth/test_token_validation.py
```

### Step 2: 執行測試，確認紅燈

```bash
# 前端測試（應該全部失敗）
npm run test -- frontend/src/stores/__tests__/teacherAuthStore.test.ts
npm run test -- frontend/src/lib/__tests__/auth-consistency.test.ts

# 後端測試
cd backend
pytest tests/integration/auth/test_token_validation.py -v

# 預期結果：🔴 所有測試都應該失敗
```

### Step 3: 逐步修復（綠燈階段）

#### P0-1: 建立 teacherAuthStore.ts
```bash
# 1. 建立檔案
touch frontend/src/stores/teacherAuthStore.ts

# 2. 實作 store（參考 studentAuthStore.ts）

# 3. 執行測試
npm run test -- teacherAuthStore.test.ts

# 預期：🟢 teacherAuthStore 測試通過
```

#### P0-2: 統一 Teacher Login
```bash
# 1. 修改 TeacherLoginModal.tsx
# 2. 修改 TeacherLogin.tsx
# 3. 修改 PricingPage.tsx

# 4. 執行測試
npm run test -- auth-consistency.test.ts

# 預期：🟢 Token 一致性測試通過
```

#### P0-3: 修復 API Client
```bash
# 1. 簡化 lib/api.ts 的 getToken() 方法

# 2. 執行測試
npm run test -- api-token.test.ts

# 預期：🟢 API Token 測試通過
```

### Step 4: 完整測試（全綠燈）

```bash
# 執行所有測試
npm run test
npm run test:api

# 預期：🟢 所有測試通過
```

---

## ✅ 驗收標準

### 功能驗收
- [ ] Teacher 可以正常登入
- [ ] Student 可以正常登入
- [ ] 登出後所有資料被清除
- [ ] API 請求正確帶上 token
- [ ] 不同角色不能互相訪問對方 API

### 技術驗收
- [ ] 只有 2 個 localStorage keys: `teacher-auth-storage`, `student-auth-storage`
- [ ] 移除所有舊的 token keys (`token`, `access_token`, `auth-storage`)
- [ ] 移除所有舊的用戶資料 keys (`user`, `userInfo`, `username`, `role`, `userType`)
- [ ] 只有一個 API Client 負責 token 管理
- [ ] 所有測試通過（綠燈）

### 程式碼品質
- [ ] 測試覆蓋率 > 80%
- [ ] 沒有 TypeScript 錯誤
- [ ] 沒有 ESLint 錯誤
- [ ] 所有 pre-commit hooks 通過

---

## 🚨 注意事項

### 測試過程中的紀律
1. **絕對不要跳過紅燈階段** - 必須先確認測試失敗
2. **一次只修一個問題** - 不要同時改多個檔案
3. **每次修改後都要跑測試** - 確保沒有改壞其他功能
4. **測試必須是可重複的** - 每次執行結果都一樣

### 回滾計畫
如果修改後測試失敗：
```bash
# 1. 檢查修改了什麼
git diff

# 2. 如果改壞了，立即回滾
git checkout -- <檔案名稱>

# 3. 重新思考修改策略
# 4. 再次嘗試
```

### 階段性 Commit
每完成一個 P0 任務就 commit：
```bash
git add -A
git commit -m "test: 🟢 P0-1 建立 teacherAuthStore 並通過測試"
```

---

## 📊 進度追蹤

### Phase 1: 紅燈階段 🔴
- [ ] 建立所有測試檔案
- [ ] 執行測試，確認全部失敗
- [ ] 記錄失敗原因

### Phase 2: 綠燈階段 🟢
- [ ] P0-1: teacherAuthStore ✅
- [ ] P0-2: 統一 Teacher Login ✅
- [ ] P0-3: 修復 API Client ✅
- [ ] 所有測試通過 ✅

### Phase 3: 重構階段 ♻️
- [ ] P1-4: 移除重複檔案
- [ ] P1-5: 統一 logout
- [ ] P1-6: ProtectedRoute
- [ ] 最終測試通過 ✅

---

**TDD 原則**：紅 → 綠 → 重構，永遠不要跳過任何步驟！
