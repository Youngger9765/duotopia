# 🚨 認證系統 Bug Report - Token & LocalStorage 混亂問題

**檢查日期**: 2025-10-05
**嚴重程度**: 🔴 HIGH (安全性 + 可維護性問題)

---

## 📊 問題總覽

目前全站的 token 和用戶認證管理**極度混亂**，存在以下核心問題：

1. ❌ **多種 token 儲存方式並存**（5 種不同的 localStorage keys）
2. ❌ **多種用戶資料儲存格式**（4 種不同的結構）
3. ❌ **缺少統一的 Teacher Auth Store**（學生有，教師沒有）
4. ❌ **三個不同的 API Client 各自管理 token**
5. ❌ **logout 邏輯分散且不一致**

---

## 🔍 詳細問題分析

### 1. Token 儲存混亂 (5 種並存)

| localStorage Key | 使用位置 | 格式 | 問題 |
|-----------------|---------|------|------|
| `token` | `lib/auth.ts`, `utils/api.ts` | 純字串 | 舊版遺留 |
| `access_token` | `lib/api.ts` | 純字串 | 新版主要 token |
| `student-auth-storage` | Zustand persist | JSON (含 state.token) | ✅ 正確 |
| `teacher-auth-storage` | 手動寫入 | JSON (含 state.token) | ❌ 沒有對應 store |
| `auth-storage` | 某些地方檢查 | JSON | ❌ 來源不明 |

**位置證據**:
```typescript
// lib/api.ts:41-79 - getToken() 優先順序邏輯
private getToken(): string | null {
  // 1. 優先學生 token
  const studentAuth = localStorage.getItem('student-auth-storage');

  // 2. 檢查老師 token
  const teacherAuth = localStorage.getItem('auth-storage');

  // 3. 最後檢查舊的 access_token
  const oldToken = localStorage.getItem('access_token');
}

// utils/api.ts:21 - 只用 'token'
const token = localStorage.getItem('token');

// lib/auth.ts:99,119,123,127 - 也是用 'token'
localStorage.getItem('token')
localStorage.setItem('token', token)
```

### 2. 用戶資料儲存混亂 (4 種格式)

| localStorage Key | 格式 | 使用位置 | 問題 |
|-----------------|------|---------|------|
| `user` | `JSON.stringify(response.user)` | `lib/api.ts` | 完整用戶物件 |
| `userInfo` | `{id, name, user_type}` | `lib/auth.ts` | 精簡版 |
| `username` | 純字串 | `TeacherLoginModal.tsx` | 只有名字 |
| `role` / `userType` | 純字串 | 多處 | 混用兩個 key |

**位置證據**:
```typescript
// lib/api.ts:144-145
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('user', JSON.stringify(response.user));

// lib/auth.ts:131-135
localStorage.setItem('userInfo', JSON.stringify({
  id: user.user_id,
  name: user.name,
  user_type: user.user_type
}));

// components/TeacherLoginModal.tsx:53-55
localStorage.setItem('token', response.access_token);
localStorage.setItem('role', 'teacher');
localStorage.setItem('username', response.user?.name || email);

// TestRecordingPanel.tsx:377
localStorage.setItem('userType', 'teacher');
```

### 3. 缺少 Teacher Auth Store

**現狀**:
- ✅ 學生: `stores/studentAuthStore.ts` (使用 Zustand + persist)
- ❌ 教師: **沒有對應的 store**，直接手動操作 localStorage

**證據**:
```typescript
// ✅ 學生有正規的 store
// frontend/src/stores/studentAuthStore.ts
export const useStudentAuthStore = create<StudentAuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (token: string, user: StudentUser) => { ... },
      logout: () => { ... }
    }),
    { name: 'student-auth-storage' }
  )
);

// ❌ 教師只有手動寫入 localStorage
// components/TeacherLoginModal.tsx:58-66
const teacherAuthData = {
  state: {
    isAuthenticated: true,
    user: response.user,
    token: response.access_token
  },
  version: 0
};
localStorage.setItem('teacher-auth-storage', JSON.stringify(teacherAuthData));
```

### 4. API Client 三頭馬車

**三個不同的 API Client 各自管理 token**:

| 檔案 | 方式 | Token 來源 | 問題 |
|-----|------|----------|------|
| `lib/api.ts` | class ApiClient | 多層優先級檢查 | 複雜邏輯 |
| `utils/api.ts` | axios instance | 只看 `token` | 不完整 |
| `lib/auth.ts` | fetch 函數 | 只看 `token` | 不完整 |

**證據**:
```typescript
// 1. lib/api.ts - 複雜的 getToken() 邏輯
class ApiClient {
  private token: string | null = null;
  private getToken(): string | null {
    // 三層檢查：student-auth-storage -> auth-storage -> access_token
  }
}

// 2. utils/api.ts - 只看 'token'
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
});

// 3. lib/auth.ts - 也只看 'token'
export async function getCurrentUser(): Promise<User> {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('No token found');
  // ...
}
```

### 5. Logout 邏輯不一致

**每個地方的 logout 都刪除不同的 keys**:

```typescript
// lib/api.ts:170-184 (刪 10 個)
logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  localStorage.removeItem('teacher-auth-storage');
  localStorage.removeItem('student-auth-storage');
  localStorage.removeItem('auth-storage');
  localStorage.removeItem('userType');
  localStorage.removeItem('selectedPlan');
}

// services/authService.ts:42-43 (刪 2 個)
logout() {
  localStorage.removeItem('auth-storage');
  localStorage.removeItem('student-auth-storage');
}

// TestRecordingPanel.tsx:404-407 (刪 4 個)
const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('userType');
  localStorage.removeItem('teacher-auth-storage');
  localStorage.removeItem('student-auth-storage');
}

// lib/auth.ts:143-145 (刪 2 個)
export function clearAuthData() {
  removeAuthToken(); // 'token'
  localStorage.removeItem('userInfo');
}
```

---

## ✅ 正確的業界標準做法

### 1. **統一的 Auth Store (Zustand)**
```typescript
// ✅ 教師和學生都應該有各自的 store
stores/
  ├── teacherAuthStore.ts  // ← 目前缺少！
  └── studentAuthStore.ts  // ✅ 已存在
```

### 2. **單一 Token 儲存方式**
```typescript
// ✅ 只用 Zustand persist，不手動操作 localStorage
export const useTeacherAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null })
    }),
    { name: 'teacher-auth-storage' }  // 統一命名
  )
);
```

### 3. **統一的 API Client**
```typescript
// ✅ 只用一個 API Client，從 store 取 token
class ApiClient {
  private getToken(): string | null {
    // 根據當前路由判斷應該用哪個 store
    if (isStudentRoute()) {
      const { token } = useStudentAuthStore.getState();
      return token;
    } else {
      const { token } = useTeacherAuthStore.getState();
      return token;
    }
  }
}
```

### 4. **統一的 Logout**
```typescript
// ✅ 一個函數清除所有認證資料
export function clearAllAuth() {
  useTeacherAuthStore.getState().logout();
  useStudentAuthStore.getState().logout();
  // Zustand persist 會自動清除 localStorage
}
```

---

## 🐛 具體 Bug 清單

### Bug #1: PricingPage 認證檢查混亂
**檔案**: `pages/PricingPage.tsx:66-108`
```typescript
// ❌ 檢查三種不同的認證方式
const teacherAuthStr = localStorage.getItem('teacher-auth-storage');  // 1
const legacyToken = localStorage.getItem('token');                    // 2
const studentAuthStr = localStorage.getItem('student-auth-storage');  // 3
```

### Bug #2: TeacherLoginModal 手動組裝 auth data
**檔案**: `components/TeacherLoginModal.tsx:58-66`
```typescript
// ❌ 手動建立 Zustand 格式但沒有對應的 store
const teacherAuthData = {
  state: { isAuthenticated: true, user: response.user, token: response.access_token },
  version: 0
};
localStorage.setItem('teacher-auth-storage', JSON.stringify(teacherAuthData));
```

### Bug #3: utils/api.ts 只看舊 token
**檔案**: `utils/api.ts:21`
```typescript
// ❌ 只檢查舊的 'token'，不管新的認證系統
const token = localStorage.getItem('token');
```

### Bug #4: lib/auth.ts 與 lib/api.ts 重複功能
```typescript
// ❌ 兩個檔案都有登入、token 管理功能
// lib/auth.ts: loginTeacher(), setAuthToken(), removeAuthToken()
// lib/api.ts: teacherLogin(), logout()
```

### Bug #5: 沒有統一的路由守衛
- 沒有統一的 `ProtectedRoute` component
- 每個頁面自己檢查認證狀態
- 檢查方式不一致（有的看 token，有的看 auth-storage）

---

## 📝 修復建議優先級

### 🔴 P0 (立即修復)
1. **建立 `teacherAuthStore.ts`** - 與 studentAuthStore 對稱
2. **統一所有 Teacher Login 使用新 store** - 移除手動 localStorage 操作
3. **修復 API Client token 獲取邏輯** - 只從 store 取

### 🟡 P1 (短期修復)
4. **移除重複的 auth 檔案** - `lib/auth.ts` 或 `utils/api.ts` 二選一
5. **統一 logout 邏輯** - 一個函數處理所有清理
6. **建立 ProtectedRoute component**

### 🟢 P2 (長期優化)
7. **Token 刷新機制** - JWT refresh token
8. **Session 管理** - 處理多分頁同步
9. **安全性增強** - httpOnly cookies 考慮

---

## 🎯 建議的新架構

```
frontend/src/
├── stores/
│   ├── teacherAuthStore.ts    # ✅ 新增：教師認證 store
│   └── studentAuthStore.ts    # ✅ 已存在
│
├── lib/
│   ├── api.ts                 # ✅ 保留：統一 API Client
│   ├── auth.ts                # ❌ 移除：功能合併到 stores
│   └── protectedRoute.tsx     # ✅ 新增：路由守衛
│
├── utils/
│   └── api.ts                 # ❌ 移除：使用 lib/api.ts
│
└── services/
    └── authService.ts         # ❌ 移除或重構
```

---

## 📚 相關檔案清單

### 需要修改的檔案 (18 個)
1. `frontend/src/lib/api.ts` - 簡化 getToken()
2. `frontend/src/components/TeacherLoginModal.tsx` - 使用 store
3. `frontend/src/pages/TeacherLogin.tsx` - 使用 store
4. `frontend/src/pages/PricingPage.tsx` - 簡化認證檢查
5. `frontend/src/components/admin/TestRecordingPanel.tsx` - 使用 store
6. `frontend/src/utils/api.ts` - 移除或重構
7. `frontend/src/lib/auth.ts` - 移除或重構
8. `frontend/src/services/authService.ts` - 移除或重構
9. `frontend/src/services/api.ts` - 檢查是否還需要
10. 所有使用 `localStorage.getItem('token')` 的頁面

### 需要新增的檔案 (2 個)
1. `frontend/src/stores/teacherAuthStore.ts`
2. `frontend/src/lib/protectedRoute.tsx`

---

## ⚠️ 風險評估

### 安全性風險
- 🔴 **Token 暴露**: 多個地方儲存 token，增加洩漏風險
- 🔴 **認證繞過**: 檢查邏輯不一致，可能被繞過
- 🟡 **XSS 攻擊**: localStorage 容易被 XSS 攻擊讀取

### 可維護性風險
- 🔴 **新人無法理解**: 認證邏輯分散在 10+ 個檔案
- 🔴 **Bug 難以追蹤**: 不知道該相信哪個 token
- 🟡 **重構困難**: 牽一髮動全身

### 業務風險
- 🟡 **登入失敗**: 用戶可能因為 token 混亂無法登入
- 🟡 **資料遺失**: logout 不完整導致殘留資料
- 🟢 **效能問題**: 重複檢查多個 localStorage keys

---

**報告結束** 🏁
