# TODO - Duotopia Project Tasks

**Last Updated**: 2026-01-16
**Current Branch**: `feat/issue-112-org-hierarchy`
**Focus**: Organization Materials Management - Reorder Functionality

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
1. ~~**重構：ProgramTreeView 取代所有 RecursiveTreeAccordion 直接使用**~~ ✅ **已完成**
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

2. **Org Dashboard 教材入口/UI** ⏰
   - `organizationRoutes.tsx` 已有 `/organization/:orgId/materials`
   - `OrganizationLayout`/`OrganizationDashboard` 無明確入口
   - `SchoolDetailPage` 已有學校教材入口
   - 待補：機構教材入口的 UI 連結與導覽

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
