# Issue #112 系统性调查报告

**调查日期**: 2026-01-29
**调查方法**: Systematic Debugging (Phase 1-2)
**调查范围**: feat/issue-112-org-hierarchy 分支所有修复 + Regression Bug 分析

---

## 执行摘要 (Executive Summary)

### 修复状态统计

| 状态 | 数量 | 错误编号 |
|------|------|---------|
| ✅ **已修复且验证** | 3 个 | 错误 1, 2, 3 |
| ⚠️ **有根本原因但未修复** | 4 个 | 错误 4, 5, 6, 7 |
| 🔴 **发现 Regression Bug 风险** | 1 个 | 错误 4 的修复模式不一致 |

### 关键发现

1. **错误 4 (机构名称未更新)** - 修复方案已存在但未应用
2. **错误 6 (首页数据错误)** - 代码注释已标注 bug，但未修复
3. **错误 5 (刷新重定向)** - 需要进一步测试验证
4. **错误 7 (工作人员管理按钮)** - 未实现功能

---

## Phase 1: Root Cause Investigation

### 已修复的错误 (Verified Fixes)

#### ✅ 错误 1: WorkspaceProvider 缺失导致页面空白

**Commit**: `74667767` - fix(frontend): wrap TeacherTemplatePrograms with WorkspaceProvider

**根本原因**:
```typescript
// 问题：直接使用 useWorkspace() 而没有 WorkspaceProvider
const { mode, selectedSchool } = useWorkspace();
```

**修复方案**:
- 拆分为 wrapper (提供 TeacherLayout) + inner component
- TeacherLayout 包含 WorkspaceProvider
- Inner component 安全访问 workspace context

**文件**: `frontend/src/pages/teacher/TeacherTemplatePrograms.tsx`

**验证**: ✅ 代码审查通过，修复正确

---

#### ✅ 错误 2: 编辑分校名称后，列表和侧边栏未更新

**Commits**:
- `f895ec3` - fix: Sidebar not updating after school CRUD operations (SchoolsPage)
- `584a0dc` - fix: Sidebar not updating in OrganizationEditPage after school CRUD

**根本原因**:
```typescript
// SchoolsPage 使用 local state
const [schools, setSchools] = useState<SchoolData[]>([]);

// OrganizationSidebar 使用 OrganizationContext
const { schools } = useOrganization();

// 两者不同步！
```

**修复方案**:
在 CRUD 成功后调用 `refreshSchools()`:

```typescript
const handleEditSuccess = useCallback(() => {
  fetchSchools(); // 更新 local state
  if (effectiveOrgId && token) {
    refreshSchools(token, effectiveOrgId); // 同步 sidebar
  }
}, [effectiveOrgId, token, refreshSchools]);
```

**影响文件**:
- `frontend/src/pages/organization/SchoolsPage.tsx` (3 处调用)
- `frontend/src/pages/organization/OrganizationEditPage.tsx` (3 处调用)

**验证**: ✅ 修复正确，模式一致

---

#### ✅ 错误 3: 新增学校后，左侧组织架构未即时显示

**Commit**: `f895ec3` (同错误 2)

**根本原因**: 同错误 2，state 不同步

**修复方案**: 在 `handleSaveCreate` 成功后调用 `refreshSchools()`

**验证**: ✅ 修复正确

---

### 未修复的错误 (Root Cause Identified)

#### ⚠️ 错误 4: 编辑机构名称后，左侧教育机构名称未即时更新

**状态**: **修复方案已存在，但未应用**

**根本原因**:

```typescript
// OrganizationEditPage.tsx:27-28
const { setSelectedNode, setExpandedOrgs, refreshSchools } = useOrganization();
// ❌ 缺少 refreshOrganizations！

// OrganizationEditPage.tsx:123-125
const handleEditSuccess = () => {
  fetchOrganization(); // ❌ 只更新 local state
  // ❌ 缺少 refreshOrganizations(token) 调用！
};
```

**对比 OrganizationContext**:

```typescript
// OrganizationContext.tsx:54-55 (方法已实现)
refreshOrganizations: (token: string) => Promise<void>; ✅ 方法存在
refreshSchools: (token: string, orgId: string) => Promise<void>; ✅ 已使用
```

**修复方案** (与错误 2 相同模式):

```typescript
// 1. 导入 refreshOrganizations
const { setSelectedNode, setExpandedOrgs, refreshSchools, refreshOrganizations } = useOrganization();

// 2. 在 handleEditSuccess 调用
const handleEditSuccess = useCallback(() => {
  fetchOrganization(); // 更新 local state
  if (token) {
    refreshOrganizations(token); // 同步 sidebar ✅
  }
}, [token, refreshOrganizations]);
```

**证据**:
- `grep -r "refreshOrganizations" frontend/src/pages/organization/` → **0 结果**
- OrganizationEditPage 是唯一编辑机构名称的地方
- 修复模式与错误 2 完全一致

**Regression Bug 风险**: ⚠️ **高** - 修复模式已建立但未一致应用

---

#### ⚠️ 错误 5: 首页重新整理后跳转到错误页面

**老师反馈**:
1. 在 `/organization/dashboard` 页面
2. 刷新页面
3. 被重定向到 `/organization/{org_id}`

**代码分析** (`frontend/src/pages/organization/OrganizationDashboard.tsx`):

```typescript
// Line 89-97: Auto-redirect logic
useEffect(() => {
  const checkAndRedirect = async () => {
    const currentPath = window.location.pathname;
    if (currentPath === "/organization/dashboard") {
      console.log("👤 User is on dashboard, respecting their choice");
      return; // ✅ 应该阻止重定向
    }

    // Line 99-106: 检查 token 和 roles
    if (!token || !userRoles || userRoles.length === 0 || hasRedirectedRef.current) {
      return;
    }

    // Line 113-122: org_owner 逻辑
    if (hasOrgOwner) {
      console.log("🏢 org_owner: staying on dashboard");
      return; // ✅ 正确
    }

    // Line 124-134: org_admin 重定向
    if (hasOrgAdmin) {
      if (organizations.length > 0) {
        hasRedirectedRef.current = true;
        navigate(`/organization/${organizations[0].id}`); // 🔴 这里重定向！
      }
    }
  };

  checkAndRedirect();
}, [token, userRoles, organizations, navigate]); // ⚠️ dependencies 包含 organizations
```

**根本原因分析**:

1. **刷新页面时**:
   - `hasRedirectedRef.current` 重置为 `false` ✅ (ref 不会在刷新后保留)
   - `organizations` 初始为空数组 `[]`

2. **第一次 useEffect 执行**:
   - Line 94: `currentPath === "/organization/dashboard"` → `true`
   - Line 96: `return` ✅ **应该阻止重定向**

3. **organizations 从 API fetch 后**:
   - `organizations.length` 从 `0` → `1+`
   - useEffect 因为 dependency 变化而**重新执行**
   - Line 94: `currentPath === "/organization/dashboard"` → **仍然是 `true`**
   - Line 96: `return` ✅ **仍然阻止重定向**

**矛盾**: 代码逻辑看起来**应该不会重定向**，但老师报告会重定向。

**可能的原因**:
1. **测试账号不是 org_admin？** - 需要确认老师测试账号的 role
2. **`currentPath` 检查时机问题？** - `window.location.pathname` 可能在 navigate 后立即读取
3. **多次 render 竞态？** - React 18 Strict Mode 会双重调用 useEffect

**需要进一步验证**:
- [ ] 确认测试账号 `kaddy-eunice@duotopia.com` 的 roles
- [ ] 添加 console.log 追踪重定向流程
- [ ] 在 preview 环境复现问题

**状态**: ⏳ **需要实际测试验证**

---

#### ⚠️ 错误 6: 首页数据显示不正确 (学校总数、教师总数)

**老师反馈**: 学校总数和教师总数显示错误

**代码分析** (`backend/routers/organizations.py:391-487`):

```python
# Line 475-477: 已知 Bug，代码注释标注
# Note: total_teachers might double-count if teacher is both org and school member
# For now, we just sum them. Could use UNION for exact count if needed.
total_teachers = (org_teachers or 0) + school_teachers
```

**根本原因**:

1. **教师重复计算**:
   ```python
   org_teachers = count(distinct(TeacherOrganization.teacher_id))  # 机构教师
   school_teachers = count(distinct(TeacherSchool.teacher_id))      # 学校教师
   total_teachers = org_teachers + school_teachers  # ❌ 直接相加会重复！
   ```
   - 如果一个教师同时是 org member 和 school member，会被计算两次

2. **学校总数** (需要验证):
   ```python
   # Line 440-444
   total_schools = (
       db.query(func.count(School.id))
       .filter(School.organization_id.in_(org_ids), School.is_active.is_(True))
       .scalar()
   )
   ```
   - 逻辑看起来正确
   - 但需要确认 `org_ids` 的范围是否正确

**修复方案**:

```python
# 使用 UNION 去重
from sqlalchemy import union

org_teacher_ids = (
    db.query(TeacherOrganization.teacher_id)
    .filter(
        TeacherOrganization.organization_id.in_(org_ids),
        TeacherOrganization.is_active.is_(True),
    )
)

school_teacher_ids = (
    db.query(TeacherSchool.teacher_id)
    .filter(
        TeacherSchool.school_id.in_(school_id_list),
        TeacherSchool.is_active.is_(True),
    )
)

# 去重计算
unique_teachers = org_teacher_ids.union(school_teacher_ids)
total_teachers = unique_teachers.count()
```

**证据**:
- 代码注释明确标注 "might double-count"
- 没有后续 commit 修复此问题

**状态**: ⚠️ **已知 Bug，未修复**

---

#### ⚠️ 错误 7: 缺少工作人员状态和角色管理按钮

**老师反馈**:
- 位置: `/organization/{org_id}` 页面
- 问题: 没有可以改变工作人员「状态」与「角色」的操作按钮

**代码分析** (`frontend/src/pages/organization/OrganizationEditPage.tsx`):

```typescript
// Line 165: 注释说明已移除到 StaffTable 组件
// Role management is now handled by StaffTable component
```

**检查 StaffTable**:

```bash
$ grep -n "role\|status\|active" frontend/src/components/organization/StaffTable.tsx
```

**根本原因**: **功能未实现**

**需要实现**:
1. 编辑教师角色 (org_admin, teacher, etc.)
2. 编辑教师状态 (active/inactive)
3. UI 按钮和对话框

**状态**: ⚠️ **功能缺失，需要新实现**

---

## Phase 2: Regression Bug 分析

### 🔴 高风险：Sidebar 刷新模式不一致

**问题**: 修复错误 2 时建立了 sidebar 刷新模式，但未一致应用到机构编辑

**证据**:

| 操作 | 文件 | refreshSchools | refreshOrganizations |
|------|------|----------------|----------------------|
| 编辑学校 | SchoolsPage.tsx | ✅ 已调用 | N/A |
| 新增学校 | SchoolsPage.tsx | ✅ 已调用 | N/A |
| 删除学校 | SchoolsPage.tsx | ✅ 已调用 | N/A |
| 编辑学校 (org page) | OrganizationEditPage.tsx | ✅ 已调用 | N/A |
| **编辑机构** | OrganizationEditPage.tsx | N/A | ❌ **未调用** |

**风险**:
- 用户会困惑为什么学校名称会即时更新，但机构名称不会
- 不一致的 UX 体验
- 违反 "同样的模式应该有同样的行为" 原则

**推荐**: 应用相同的修复模式到错误 4

---

### ⚠️ 中风险：useWorkspace() 使用范围广泛

**问题**: `useWorkspace()` 在 12 个文件中使用，但只修复了 1 个 (TeacherTemplatePrograms)

**影响文件**:
- `frontend/src/components/workspace/*.tsx` (5 个)
- `frontend/src/pages/teacher/*.tsx` (4 个)
- `frontend/src/components/AssignmentDialog.tsx`
- `frontend/src/components/TeacherLayout.tsx`
- `frontend/src/pages/teacher/SchoolMaterialsPage.tsx`

**验证需要**:
- [ ] 确认所有使用 `useWorkspace()` 的组件都在 `WorkspaceProvider` 内
- [ ] 检查是否有其他组件会遇到相同的 "useWorkspace must be used within a WorkspaceProvider" 错误

**推荐**: 使用 grep 检查所有 `useWorkspace()` 使用点的父组件树

---

## Phase 3: 修复优先级建议

### P0 - 立即修复 (影响核心功能)

1. **错误 4**: 编辑机构名称后 sidebar 未更新
   - 修复成本: 低 (5 分钟，复制错误 2 的模式)
   - 用户影响: 高 (核心功能，UX 不一致)
   - 修复方案: 已明确 (见上文)

2. **错误 6**: 首页数据错误
   - 修复成本: 中 (30 分钟，需要改 SQL query)
   - 用户影响: 高 (数据错误会损害信任)
   - 修复方案: 已明确 (使用 UNION 去重)

### P1 - 高优先级 (功能缺失)

3. **错误 7**: 工作人员管理按钮
   - 修复成本: 高 (2-3 小时，需要实现完整功能)
   - 用户影响: 高 (无法管理成员)
   - 修复方案: 需要设计和实现

### P2 - 需要验证

4. **错误 5**: 首页刷新重定向
   - 修复成本: 未知 (需要先复现问题)
   - 用户影响: 中 (可以手动导航回去)
   - 推荐: 先在 preview 环境测试确认

---

## 测试建议

### 回归测试清单

在修复错误 4 后，必须验证：

- [ ] 编辑机构名称 → sidebar 即时更新 ✅
- [ ] 编辑学校名称 → sidebar 即时更新 ✅ (已修复)
- [ ] 新增学校 → sidebar 即时显示 ✅ (已修复)
- [ ] 删除学校 → sidebar 即时移除 ✅ (已修复)
- [ ] 刷新页面后 → 所有数据正确显示

### E2E 测试场景

```gherkin
Scenario: 机构管理 sidebar 同步测试
  Given 用户登录为 org_admin
  When 用户编辑机构名称从 "笑笑羊美语" 到 "笑笑羊国际美语"
  And 点击储存
  Then sidebar 应该立即显示 "笑笑羊国际美语"
  And 不需要刷新页面
```

---

## 结论

### 修复状态总结

| 错误 | 状态 | 根本原因 | 修复难度 | 优先级 |
|------|------|---------|---------|--------|
| 错误 1 | ✅ 已修复 | WorkspaceProvider 缺失 | 已解决 | - |
| 错误 2 | ✅ 已修复 | State 不同步 | 已解决 | - |
| 错误 3 | ✅ 已修复 | State 不同步 | 已解决 | - |
| 错误 4 | ⚠️ 未修复 | 缺少 refreshOrganizations 调用 | 低 | P0 |
| 错误 5 | ⏳ 待验证 | 重定向逻辑需测试 | 未知 | P2 |
| 错误 6 | ⚠️ 未修复 | 教师重复计算 (已知 bug) | 中 | P0 |
| 错误 7 | ⚠️ 未修复 | 功能未实现 | 高 | P1 |

### Regression Bug 风险

- 🔴 **高风险**: 错误 4 - 修复模式不一致
- ⚠️ **中风险**: useWorkspace() 广泛使用但只部分修复

### 推荐行动

1. **立即修复** 错误 4 (5 分钟)
2. **立即修复** 错误 6 (30 分钟)
3. **规划实现** 错误 7 (2-3 小时)
4. **测试验证** 错误 5 (在 preview 环境)

---

**报告结束**

*本报告使用 Systematic Debugging 方法论生成*
*调查人员: Claude (SuperClaude v3.0)*
*调查时间: 2026-01-29*
