# TODO - Duotopia Project Tasks

**Last Updated**: 2026-02-03
**Current Branch**: `feat/issue-198-migration`
**Focus**: Organization Points System - Admin Organization CRUD (Phase 5 Complete)

---

## 🎨 New Feature - Design Phase

### Teacher Workspace Switcher（個人/機構工作區切換器）

**設計狀態**: ✅ 已完成（見 `docs/plans/2026-01-26-teacher-workspace-switcher-design.md`）

**目標**: 讓老師能清楚切換「個人用途」和「機構用途」兩種工作模式

**核心設計**:
```
Sidebar 頂部
├─ [個人] Tab → 我的班級、我的學生、我的教材
└─ [機構] Tab
   ├─ 階段 1: 機構+學校列表（點擊選擇）
   └─ 階段 2: 學校切換器 + 功能選單
      ├─ [南港分校 ▼] 下拉選單
      ├─ 權限限制橫幅
      └─ 班級（唯讀）、學校公版教材、作業管理
```

**關鍵特性**:
- ✅ Tab-based 切換（個人/機構）
- ✅ 兩階段導航（先選學校 → 再顯示功能）
- ✅ 權限限制視覺化（banner + 唯讀標記）
- ✅ 支援多機構切換（下拉選單）

**Next Steps**:
1. ⏰ Review 設計文檔與 stakeholders
2. ⏰ 使用 `writing-plans` 創建實作計畫
3. ⏰ 使用 `using-git-worktrees` 建立開發分支
4. ⏰ Phase 1-5 實作（見設計文檔 Section 9）

**設計參考**: Agent a6bad49 (ui-design-expert)
**文檔**: `docs/plans/2026-01-26-teacher-workspace-switcher-design.md`

---

## 🚨 Urgent - Awaiting Commit

### Critical Fixes (Staged, Not Committed)

1. **學校教材建立權限修復** 🔴 CRITICAL
   - **問題**: School materials creation 失敗 "Failed to fetch"
   - **Root Cause**: `backend/utils/permissions.py:74` JSONB 查詢錯誤
     ```python
     # ❌ 錯誤：產生 LIKE operator (PostgreSQL JSONB 不支援)
     TeacherSchool.roles.contains(["school_admin"])

     # ✅ 正確：使用 PostgreSQL JSONB ? operator
     TeacherSchool.roles.op('?')('school_admin')
     ```
   - **Error**: `psycopg2.errors.UndefinedFunction: operator does not exist: jsonb ~~ text`
   - **Status**: ✅ 已修復，**⚠️ 待 COMMIT**
   - **影響檔案**: `backend/utils/permissions.py` (line 74-77)
   - **驗證**: ✅ 權限檢查測試通過 (`/tmp/test_permission.py`)
   - **待執行**: `git commit -m "fix(permissions): Use JSONB ? operator for school_admin role check"`

---

## 🚧 In Progress / Next Up

### Issue #198 - Organization Points System ✅ COMPLETE

**狀態**: ✅ Phase 1-5 已實作完成，⏰ 等待案主測試驗收

**完成內容**:

**Phase 1-4 (Points System)**:
- ✅ Backend API (3 endpoints): GET points, POST deduct, GET history
- ✅ Frontend Components: OrganizationPointsBalance, OrganizationPointsHistory
- ✅ Dashboard Integration: Points section in OrganizationDashboard
- ✅ Tests: 13/14 passing (92.9%)
- ✅ Authentication Fix: 修復 401 錯誤 (使用 useTeacherAuthStore)

**Phase 5 (Admin Organization CRUD - 2026-02-03)**:
- ✅ Backend List API: GET /api/admin/organizations (pagination, search, N+1 optimization)
- ✅ Backend Update API: PUT /api/admin/organizations/{id} (points adjustment tracking)
- ✅ Frontend Types: OrganizationListItem, AdminOrganizationUpdate schemas
- ✅ Frontend List Page: AdminOrganizations table (search, pagination, 25/50/100 per page)
- ✅ Frontend Edit Dialog: Comprehensive form with points management
  - Points validation (prevents reducing below used)
  - Large adjustment warnings (>10,000 points)
  - Email and numeric validation
  - Only sends changed fields (efficient updates)
- ✅ Backend Tests: 24/24 passing (test_admin_organizations.py + test_admin_organizations_points.py)
- ✅ Code Review: Applied fixes (sonner toast, type safety, dialog protection)
- ✅ Testing Checklist: 60+ manual test cases documented

**基礎驗證結果 (2026-02-03)**:
- ✅ **API 認證**: 修復 localStorage token 問題，改用 Zustand store
- ✅ **元件渲染**: 兩個 Points 元件正確顯示在 Organization Dashboard
- ✅ **API 呼叫**: GET /points (200 OK), GET /points/history (200 OK)
- ✅ **預設狀態**: 正確顯示 0 points 組織狀態 (0/0 total, no history)
- ✅ **CI/CD**: Preview 環境部署成功

**待驗證項目**:
1. ⏰ **Admin 創建組織流程** - 確認 owner email 驗證機制
   - 路徑: `/admin/organizations/create`
   - 測試項目:
     - [ ] 輸入不存在的 email → 應該顯示錯誤
     - [ ] 輸入未驗證的 email → 應該拒絕創建
     - [ ] 輸入已驗證的 email → 成功創建並指派 org_owner 角色
     - [ ] Owner lookup 功能正常顯示姓名、手機
     - [ ] total_points 欄位正確儲存

2. ✅ **Points 功能基礎測試** (Preview 環境) - 確認 Phase 4 實作
   - 路徑: `/organization/dashboard` (選擇組織後)
   - 測試項目:
     - [x] Points balance 正確顯示 (total/used/remaining) ✅ 顯示 0/0 total
     - [x] Progress bar 視覺化正確 ✅ 藍色進度條顯示
     - [ ] Low balance warning 在 remaining < 20% 時顯示 (⏰ 需實際 points 資料測試)
     - [x] History table 顯示使用記錄 ✅ 顯示 "No usage history yet."
     - [ ] Pagination 正常運作 (20 items/page) (⏰ 需實際 history 資料測試)
     - [ ] Feature type badges 顏色正確 (⏰ 需實際 history 資料測試)
     - [ ] 日期格式正確 (toLocaleString) (⏰ 需實際 history 資料測試)

3. ✅ **API Integration 基礎測試** (Preview 環境)
   - [x] GET `/api/organizations/{id}/points` 回傳正確資料 ✅ Status 200
   - [x] GET `/api/organizations/{id}/points/history` 分頁正確 ✅ Status 200 (limit=20&offset=0)
   - [ ] 權限控制: 非 org_owner/org_admin 無法存取 (⏰ 需多帳號測試)
   - [ ] Error handling: 404, 403 等錯誤正確處理 (⏰ 需實際錯誤場景測試)

**Preview URL**: https://duotopia-preview-issue-198-frontend-316409492201.asia-east1.run.app
**Backend URL**: https://duotopia-preview-issue-198-backend-b2ovkkgl6a-de.a.run.app

**測試文檔**:
- `docs/plans/admin-organizations-crud-testing-checklist.md` - 完整測試清單
- `docs/plans/2026-02-03-admin-organization-crud.md` - 實作計畫

**下一步**: 等待案主完整測試驗收，重點項目:
1. ✅ Admin 組織列表頁面 (`/admin` → 組織管理)
2. ✅ 組織資料編輯功能（display_name, teacher_limit, contact info）
3. ✅ Points 管理功能（增減點數、delta 顯示、驗證）
4. Admin 創建組織並分配 points
5. 有實際 points 使用記錄的完整流程測試
3. 權限控制測試 (不同角色存取)

**參考文檔**: `docs/plans/2026-02-03-organization-points-system.md`

---

### 學校學生管理功能（待開始）

**設計狀態**: ✅ 已完成（見 `docs/plans/2026-01-19-school-student-management-complete.md`）  
**核心設計**:
- 學生與學校：多對多關係（`StudentSchool` 關聯表）
- 學生與班級：多對多關係（`ClassroomStudent` 關聯表）
- 流程：先在學校建立學生名冊 → 再分配到班級

**實現計劃**:
1. ⏰ **Phase 1: 數據模型修改**
   - Task 1: 創建 `StudentSchool` 關聯表 Migration
   - 更新 `Student` 和 `School` 模型

2. ⏰ **Phase 2: Backend API (Tasks 2-7)**
   - Task 2: 創建 Schemas
   - Task 3: 實現權限檢查函數
   - Task 4: 實現 GET 端點
   - Task 5: 實現 POST 端點
   - Task 6: 實現 PUT/POST/DELETE 端點
   - Task 7: 實現 DELETE 端點

3. ⏰ **Phase 3: Frontend (Tasks 8-11)**
   - Task 8: 創建 API Client 方法
   - Task 9: 創建學校學生管理頁面
   - Task 10: 創建對話框組件
   - Task 11: 更新現有頁面

4. ⏰ **Phase 4: Testing (Tasks 12-13)**
   - Task 12: 編寫 Backend 測試
   - Task 13: 前端整合測試

**預估時間**: 9-11 天  
**優先級**: 🔵 MEDIUM  
**參考文檔**: `docs/plans/2026-01-19-school-student-management-complete.md`

---

## ✅ Recently Completed (2026-01-19)

### Bug Fixes - Content Editor & API

1. **內容更新 API 修復** ✅ **已完成**
   - **問題**: ReadingAssessmentPanel 儲存失敗 "Failed to fetch"
   - **Root Causes** (2 個同時發現):
     - Port 不符: Frontend `VITE_API_URL=http://localhost:8000`，Backend 預設 8080
     - Missing import: `content_ops.py` 使用 `text()` 但未 import `from sqlalchemy import text`
   - **解決方案**:
     - ✅ `backend/.env`: 新增 `PORT=8000`
     - ✅ `backend/routers/teachers/content_ops.py`: 新增 `from sqlalchemy import text`
     - ✅ 新增 IntegrityError handling for DELETE operations
   - **完成日期**: 2026-01-19
   - **Commit**: eeb799c1 "fix(api): Fix content update API - port config + missing import + error handling"

2. **編輯器 UX 改善** ✅ **已完成**
   - **需求**: 儲存後不要關閉編輯器，保持開啟以便繼續編輯
   - **實作**:
     - ✅ `ProgramTreeView.tsx`: 移除 `closeReadingEditor()` calls (lines 628, 675)
     - ✅ 保留 toast.success 通知
     - ✅ 本地狀態已由 addContentToLesson/updateProgramContent 更新
   - **完成日期**: 2026-01-19
   - **Commit**: eeb799c1

3. **TypeScript 型別改善** ✅ **已完成**
   - **問題**: Code review warnings (type strictness)
   - **解決方案**:
     - ✅ `api.ts`: 將 `[key: string]: any` 替換為明確的 optional fields
     - ✅ 新增所有可能的 content_items 欄位型別定義
   - **完成日期**: 2026-01-19
   - **Commit**: eeb799c1

---

## Pending ⏰

### High Priority
1. ~~**修復：MaterialsPage/SchoolMaterialsPage Reorder 無法保存**~~ ✅ **已完成**
   - **問題**：拖曳排序後重新整理頁面，順序沒有保存
   - **Root Cause（實際）**：
     - ❌ **ProgramTreeView 使用錯誤的 SWAP 邏輯**（應該用 INSERT splice）
     - ❌ **Backend GET endpoint 沒有排序 programs**（只排序了 lessons/contents）
     - ❌ **使用 onRefresh() 導致不必要的頁面重整**
   - **解決方案**：
     - ✅ Frontend: 修復 SWAP → INSERT 邏輯（三層皆使用 splice）
     - ✅ Backend: 新增 `sorted(programs, key=lambda x: x.order_index)`
     - ✅ UX 優化: 移除 onRefresh()，改用 onProgramsChange 本地更新
   - **測試結果**：
     - ✅ 拖曳排序立即更新 UI（無頁面重整）
     - ✅ 刷新頁面後順序正確保存
     - ✅ orderData 值正確（連續 0,1,2,3...）
   - **完成日期**：2026-01-16
   - **Commit**: da4b519c "fix(reorder): 修復拖曳排序功能 - INSERT邏輯+本地狀態更新"

### Medium Priority

1. **Admin Organization Creation - 擴展功能** ✅ **PHASE 1 COMPLETED (2026-01-30)**
   - **來源**: `spec/features/organization/機構設定與擁有人註冊.feature`（案主需求）
   - **設計文檔**: `docs/plans/2026-01-30-admin-org-creation-extended-features-design.md` ✅

   **Phase 1: 不需要 Migration（優先實作）** ✅ COMPLETED
   - ✅ **教師授權數顯示**（3-4h） - DONE 2026-01-30
     - ✅ 使用現有 `Organization.teacher_limit` 欄位
     - ✅ Backend: GET /api/admin/organizations/{id}/statistics
     - ✅ Frontend: TeacherUsageCard component

   - ✅ **擁有人姓名、手機欄位**（2-3h） - DONE 2026-01-30
     - ✅ 使用現有 `Teacher.name` 和 `Teacher.phone` 欄位
     - ✅ Backend: GET /api/admin/teachers/lookup?email=xxx
     - ✅ Frontend: Auto-fetch on owner_email change

   - ✅ **專案服務人員指派（org_admin）**（4-6h） - DONE 2026-01-30
     - ✅ 使用現有 `TeacherOrganization.role` 欄位
     - ✅ Frontend: Multi-select input with validation
     - ✅ Backend: project_staff_emails field support
     - ✅ Casbin: org_admin role permissions

   **Phase 2: 未註冊擁有人流程（簡化版）**
   - ⏰ **擁有人尚未註冊流程 - Option A**（4-5h）
     - ✅ 使用現有 `Teacher` 表和 token 欄位
     - Admin 輸入：owner_email, owner_name, owner_phone
     - 系統自動建立 Teacher 帳號（隨機密碼）
     - 顯示初始密碼給 Admin（線下告知擁有人）
     - 擁有人首次登入強制改密碼

   **Phase 3: 點數系統（需 Migration，暫緩）**
   - ⏸️ **總點數欄位**（5h）- **需要 Migration**
     - ❌ 需要新增 `Organization.total_points` 欄位
     - 採用方案 B（機構層級點數池）
     - 等待 Migration 批准

   - ⏸️ **剩餘點數顯示**（3-4h）- **依賴 Phase 3.1**
     - 計算：total_points - sum(point_usage_logs)
     - 顯示在機構後台

   - ⏸️ **Email 認證流程 - Option B**（12-16h）- **未來擴展**
     - 發送認證信機制
     - Token 驗證頁面
     - 自動登入流程
     - 需要 Email 基礎建設

   - **預估時間**:
     - Phase 1-2（不需 Migration）: 13-18 小時
     - Phase 3（需 Migration）: 8-9 小時
     - 總計: 21-27 小時

   - **優先級**: 🔴 HIGH（案主明確需求）
   - **狀態**: Phase 1-2 可立即開始，Phase 3 等待批准
   - **參考文檔**: `spec/features/organization/機構設定與擁有人註冊.feature`

2. ~~**重構：ProgramTreeView 取代所有 RecursiveTreeAccordion 直接使用**~~ ✅ **已完成**
   - **完成日期**：2026-01-16
   - **實作內容**：
     - ✅ ProgramTreeView 內建完整 Program/Lesson/Content CRUD
     - ✅ 移除不必要的 props（onEdit/onDelete/onCreate/onReorder 改為可選）
     - ✅ MaterialsPage 簡化（60% 代碼減少：404行 → 163行）
     - ✅ SchoolMaterialsPage 簡化（63% 代碼減少：404行 → 151行）
     - ✅ TeacherTemplatePrograms 遷移（93% 代碼減少：882行 → 64行）
   - **架構改進**：
     - RecursiveTreeAccordion 現在只負責純 UI 層（拖曳、展開/收合）
     - ProgramTreeView 是完整的自包含元件（CRUD + Reorder + Content Editor）
     - 統一三個 scope 的實作（不再有重複邏輯）
   - **Commits**: ba1cdeed, f189d519, 7f236f1a, 2a5080dc, 093a19e3, 7607df2b, 1deee214, 67d9bd3c, a6d4c780, 27e3b3e4, 11e29466
   - **文檔**: `docs/architecture/program-tree-refactor.md`
   - **測試狀態**：
     - ✅ Unit tests: Program/Lesson/Content CRUD handlers
     - ⏰ Integration tests: 待手動驗證（需要瀏覽器測試）
     - ⏰ E2E tests: 待手動驗證（跨頁面流程）

2. **進行中：教材共用模組** 🔄
   - 現況：Copy 流程分散在多個元件
   - `CreateProgramDialog` 使用 `/api/programs/copy-from-template` 與 `/api/programs/copy-from-classroom`
   - `CopyProgramDialog` 使用 `/api/teachers/classrooms/{id}/programs/copy`
   - `SchoolProgramCreateDialog` 才使用 `useProgramCopy`（統一 copy API）
   - 待做：抽成 shared copy modal + 統一 hook 規則

2. **~~Org Dashboard 教材入口/UI~~** ✅ 已完成 (Issue #112)
   - ✅ 組織詳情頁已有「組織教材」卡片入口
   - ✅ 可新增/編輯/刪除組織教材
   - ✅ 可複製組織教材到分校（權限已修復）

3. **機構內學校的班級建立** ⏰
   - 現況：老師建立班級 `POST /api/teachers/classrooms`
   - 現況：班級連結學校 `POST /api/classrooms/{classroom_id}/school`
   - 缺口：沒有 `POST /api/schools/{school_id}/classrooms`（school admin 直接建立）

4. **機構內、學校班級學生建立或匯入** ⏰
   - 現況：`teachers/student_ops.py` 皆為 teacher-only
   - 缺口：school_admin/school_director 對同校班級操作的權限入口

5. **老師個人頁面切換身分** ⏰
   - 現況：無 `activeContext`（store 只有 userRoles）
   - OrganizationContext 僅供組織後台頁使用
   - 待補：個人/機構/學校身分切換 + scope 影響

6. **Teacher 端複製流程驗證** ⏰
   - 現況：使用 `CopyProgramDialog` + legacy copy API
   - 待補：驗證 unified copy API 的教師端流程

7. **驗證紀錄（待補）** ⏰
   - 組織後台入口：未驗證
   - 教師端 copy 流程：未驗證

8. **Copy 規則（現行）** ✅
   - Organization → School ✅
   - School → Teacher / Classroom ✅
   - Teacher → Teacher / Classroom ✅
   - Classroom → Teacher / Classroom ✅

9. **Integration Tests** ⏰
   - Classroom ↔ School 關係測試（CRUD + cascade + unique）
   - Full hierarchy E2E（Organization → School → Classroom → Students）

10. **機構 ↔ 個人教材規劃（待補規格）** ⏰
   - 角色/身分切換：Teacher 可選「個人 / 機構 / 學校」並影響 scope
   - Copy 來源可見性：個人頁是否顯示機構/學校來源清單
   - 權限矩陣：前端可用規則與後端檢查對齊
   - 來源標示：Program list/tree 顯示 source_metadata
   - 複製後歸屬：copy 後是否允許再向上/跨層

11. **共用模組化方向（草案）** ⏰
   - **1) 規則單一來源**
     - 新增：`frontend/src/utils/copyRules.ts`
     - 介面：
       ```ts
       export type CopyScope = "organization" | "school" | "teacher" | "classroom";
       export type CopyTargetScope = "school" | "teacher" | "classroom";
       export interface CopyContext {
         activeContext: "personal" | "organization" | "school";
         organizationId?: string | null;
         schoolId?: string | null;
         teacherId?: number | null;
         classroomId?: number | null;
       }
       export function getAllowedCopyTargets(
         sourceScope: CopyScope,
         ctx: CopyContext,
       ): CopyTargetScope[];
       ```
   - **2) 共用 Copy Modal**
     - 新增：`frontend/src/components/shared/ProgramCopyDialog.tsx`
     - Props：
       ```ts
       interface ProgramCopyDialogProps {
         open: boolean;
         onClose: () => void;
         sourceScope: CopyScope;
         targetScopes: CopyTargetScope[];
         programs: Program[];
         onCopy: (programId: number, targetScope: CopyTargetScope, targetId: string | number) => Promise<void>;
       }
       ```
   - **3) 共用 Hook**
     - 既有：`frontend/src/hooks/useProgramCopy.ts`
     - 新增：`useCopyRules(ctx)` 回傳 targetScopes + 顯示條件
   - **4) 統一 Tree 資料介面**
     - 調整：`frontend/src/hooks/useProgramTree.ts`
     - 確保所有 scope 回傳 `ProgramTreeProgram` 型別（含 `Content.items_count`）
   - **5) 統一入口控制**
     - 新增狀態：`frontend/src/stores/teacherAuthStore.ts` → `activeContext`
     - 在 `TeacherLayout`/`OrganizationLayout` 放切換 UI
     - 影響 `CreateProgramDialog` 與 `SchoolProgramCreateDialog`
   - **6) 逐步替換舊流程**
     - `frontend/src/components/CreateProgramDialog.tsx` 改用 `ProgramCopyDialog`
     - `frontend/src/components/CopyProgramDialog.tsx` 退場或改成 wrapper

12. **重構：MaterialsPage 命名混淆** ⏰
   - **問題**：MaterialsPage 實際是組織層級教材，命名容易混淆
   - **現況**：
     - `MaterialsPage.tsx` - 組織教材（❌ 命名不清楚）
     - `SchoolMaterialsPage.tsx` - 學校教材（✅ 命名清楚）
   - **建議方案**：
     - **選項 A（推薦）**：重構命名
       - `MaterialsPage.tsx` → `OrgMaterialsPage.tsx`
       - 更新所有 import 和路由配置
       - 預估工作量：30 分鐘
     - **選項 B**：合併成單一頁面（scope 參數區分）
     - **選項 C**：保持現狀 + 加註解說明
   - **影響範圍**：
     - 檔案：`src/pages/organization/MaterialsPage.tsx`
     - 路由：`src/App.tsx` 或路由配置檔
     - Import：所有引用此頁面的地方
   - **決策**：待討論（功能優先，命名稍後處理）

 

### Low Priority / Optional
4. **TDD REFACTOR Phase** ⏰
   - 角色更新 endpoint 代碼清理

5. **Alembic Head Merge** ⏰
   - 與主線合併前先確認 migration 狀態
   - 變更前先討論

### Deployment
6. **Staging 部署與驗證** ⏰
   - Organization/School 教材 CRUD
   - Copy 流程驗證
   - RBAC 權限檢查

---

## 📝 Notes

### Technical Debt

#### 🔴 HIGH - Program Table Refactoring

**問題**: `programs` table 設計混亂，用多個 nullable FK + `is_template` 組合判斷類型

**現狀**:
| 類型 | is_template | classroom_id | organization_id | teacher_id |
|------|-------------|--------------|-----------------|------------|
| Organization 教材 | True | NULL | 有值 | 有值 |
| Teacher 模板 | True | NULL | NULL | 有值 |
| Classroom 教材 | False | 有值 | NULL | 有值 |

**問題**:
1. 欄位語意混淆 - 靠 NULL/非 NULL 組合判斷類型
2. 擴展性差 - 每加一個層級就要加 `xxx_id` 欄位
3. 查詢複雜 - 需要多條件判斷

**重構方案**:
```python
class ProgramScope(str, Enum):
    ORGANIZATION = "organization"  # 機構教材
    SCHOOL = "school"              # 學校教材
    TEACHER = "teacher"            # 教師模板
    CLASSROOM = "classroom"        # 班級教材

class Program:
    # 新增欄位
    scope = Column(Enum(ProgramScope), nullable=False)  # 明確類型
    owner_id = Column(String(36), nullable=False)       # 統一擁有者 ID (UUID or int as string)
    
    # 保留欄位 (向下相容，逐步廢棄)
    is_template = Column(Boolean)      # deprecated
    classroom_id = Column(Integer)     # deprecated  
    organization_id = Column(UUID)     # deprecated
    school_id = Column(UUID)           # 新增 (如果不重構)
```

**重構步驟**:
1. ⏰ **Phase 1: 新增欄位** (向下相容)
   - 新增 `scope` 和 `owner_id` 欄位 (nullable)
   - 寫 migration 填充現有資料
   - 更新 Model 加入新屬性

2. ⏰ **Phase 2: 更新 API**
   - 更新所有 router 使用新欄位
   - 新增 `/api/schools/{school_id}/programs` router
   - 更新查詢邏輯用 `scope` 過濾

3. ⏰ **Phase 3: 廢棄舊欄位**
   - 移除 `is_template` 依賴
   - 移除 `classroom_id`/`organization_id` 依賴
   - 最終 migration 刪除舊欄位

**預估工作量**: 2-3 天
**風險**: 中 (需要 migration + 多處 API 修改)
**優先級**: 🔵 LOW - 延後處理

> ⚠️ **決策 (2026-01-15)**: 先求有，後續再重構
> - 先用快速方案：只加 `school_id` 欄位
> - 重構計畫保留，等功能穩定後再執行
4. ✅ 後端 Lesson CRUD endpoints (POST/PUT/DELETE)
5. ✅ 後端 Content delete endpoint
6. ✅ 前端 SchoolMaterialsPage (三層 CRUD: Program/Lesson/Content)
7. ✅ 前端即時更新 tree (onProgramsChange/onRefresh)
8. ✅ 權限測試: org_owner/org_admin/school_admin 存取控制
9. ✅ 前端測試: 所有三層 CRUD 功能測試通過

**完成日期**: 2026-01-15

### Questions / Blockers

- None currently blocking progress

---

**Maintained by**: Claude Code (Sonnet 4.5)
**Review Frequency**: After each major task completion
**Format**: Markdown with emoji status indicators
