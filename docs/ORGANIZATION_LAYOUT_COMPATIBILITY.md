# 機構層級管理 - Layout 兼容性設計

## 🎯 核心概念：同一個 Layout，動態權限與資料範圍

> **設計目標**: 獨立老師和機構使用相同的 TeacherLayout，透過 Context 動態調整功能與資料範圍

---

## 📐 架構設計

### UserContext 定義

```typescript
interface UserContext {
  // 角色
  role: 'independent_teacher' | 'org_admin' | 'branch_manager' | 'org_teacher' | 'independent_student' | 'org_student'

  // 資料範圍
  scope: {
    organization_id?: string  // 所屬機構
    branch_id?: string        // 所屬分校
    teacher_id?: string       // 老師 ID (role = teacher時)
    student_id?: string       // 學生 ID (role = student時)
  }

  // 權限
  permissions: string[]  // ['view_all_teachers', 'edit_branches', 'assign_homework', ...]
}
```

---

## 🎨 TeacherLayout 動態調整

### 1. Sidebar 動態項目

```tsx
const getSidebarItems = (context: UserContext) => {
  const baseItems = [
    { path: '/teacher/dashboard', label: '首頁', icon: Home, roles: ['all'] },
    { path: '/teacher/classrooms', label: '班級', icon: Users, roles: ['all'] },
    { path: '/teacher/students', label: '所有學生', icon: UserCheck, roles: ['all'] },
    { path: '/teacher/courses', label: '課程', icon: BookOpen, roles: ['all'] },
  ]

  const orgItems = [
    { path: '/org/overview', label: '機構總覽', icon: Building, roles: ['org_admin'] },
    { path: '/org/branches', label: '分校管理', icon: MapPin, roles: ['org_admin'] },
    { path: '/org/teachers', label: '老師管理', icon: Users, roles: ['org_admin', 'branch_manager'] },
    { path: '/org/subscription', label: '訂閱管理', icon: CreditCard, roles: ['org_admin'] },
  ]

  const items = [...baseItems]

  // 機構角色才加入機構專屬項目
  if (context.role === 'org_admin' || context.role === 'branch_manager') {
    items.splice(1, 0, ...orgItems.filter(item => item.roles.includes(context.role)))
  }

  items.push({ path: '/teacher/profile', label: '個人設定', icon: Settings, roles: ['all'] })

  return items
}
```

### 2. TopBar 動態內容

#### 獨立老師
```tsx
<TopBar>
  <Logo />
  <div className="flex items-center gap-2">
    <span className="text-sm text-gray-600">老師</span>
    <span className="font-medium">{teacherName}</span>
  </div>
  <SubscriptionBadge type="personal" />
</TopBar>
```

#### 機構老師 (一般成員)
```tsx
<TopBar>
  <Logo />
  <Breadcrumb>
    <BreadcrumbItem>{orgName}</BreadcrumbItem>
    <BreadcrumbItem>{branchName}</BreadcrumbItem>
  </Breadcrumb>
  <div className="flex items-center gap-2">
    <span className="font-medium">{teacherName}</span>
  </div>
</TopBar>
```

#### 分校主管
```tsx
<TopBar>
  <Logo />
  <Breadcrumb>
    <BreadcrumbItem>{orgName}</BreadcrumbItem>
    <BreadcrumbItem active>{branchName}</BreadcrumbItem>
  </Breadcrumb>
  <TeacherSelector /> {/* 切換查看不同老師 */}
  <Badge variant="secondary">分校主管</Badge>
</TopBar>
```

#### 機構管理員
```tsx
<TopBar>
  <Logo />
  <OrgName>{orgName}</OrgName>
  <BranchSelector /> {/* 切換不同分校 */}
  <TeacherSelector /> {/* 切換查看不同老師 */}
  <Badge variant="primary">機構管理員</Badge>
</TopBar>
```

---

## 📊 資料範圍動態切換

### API 查詢邏輯

```python
# backend/routers/teachers.py

@router.get("/classrooms")
def get_classrooms(current_user: User = Depends(get_current_user)):
    """
    動態範圍查詢班級
    - 獨立老師: WHERE teacher_id = current_user.id
    - 機構老師: WHERE teacher_id = current_user.id (相同)
    - 分校主管: WHERE teacher_id IN (SELECT id FROM teachers WHERE branch_id = current_user.branch_id)
    - 機構管理員: WHERE teacher_id IN (SELECT id FROM teachers WHERE organization_id = current_user.organization_id)
    """

    if current_user.role == 'org_admin':
        # 可查看整個機構的所有班級
        query = select(Classroom).join(Teacher).where(
            Teacher.organization_id == current_user.organization_id
        )
    elif current_user.role == 'branch_manager':
        # 可查看該分校的所有班級
        query = select(Classroom).join(Teacher).where(
            Teacher.branch_id == current_user.branch_id
        )
    else:
        # 獨立老師或機構老師：只看自己的班級
        query = select(Classroom).where(
            Classroom.teacher_id == current_user.id
        )

    return db.execute(query).scalars().all()
```

### Dashboard 數據顯示

#### 獨立老師 Dashboard
```
┌─────────────────────────────────┐
│ 歡迎回來，王老師！               │
├─────────────────────────────────┤
│ 📊 我的統計                     │
│   • 班級數: 3                   │
│   • 學生數: 87                  │
│   • 課程數: 12                  │
└─────────────────────────────────┘
```

#### 機構老師 Dashboard (相同介面)
```
┌─────────────────────────────────┐
│ 歡迎回來，王老師！               │
│ 均一教育平台 / 台北校區          │
├─────────────────────────────────┤
│ 📊 我的統計                     │
│   • 班級數: 3                   │
│   • 學生數: 87                  │
│   • 課程數: 12 (含機構共用 5)    │
└─────────────────────────────────┘
```

#### 分校主管 Dashboard
```
┌─────────────────────────────────┐
│ 台北校區管理                     │
│ 均一教育平台                     │
├─────────────────────────────────┤
│ 📊 分校統計                     │
│   • 老師數: 15                  │
│   • 班級數: 42                  │
│   • 學生數: 1,234               │
├─────────────────────────────────┤
│ 👥 老師列表                     │
│ [切換查看] ▼                    │
│   • 王老師 (3 班, 87 學生)       │
│   • 李老師 (5 班, 123 學生)      │
│   • ...                         │
└─────────────────────────────────┘
```

#### 機構管理員 Dashboard
```
┌─────────────────────────────────┐
│ 均一教育平台                     │
│ [選擇分校: 台北校區 ▼]           │
├─────────────────────────────────┤
│ 📊 機構統計                     │
│   • 分校數: 8                   │
│   • 老師數: 120                 │
│   • 班級數: 356                 │
│   • 學生數: 10,245              │
├─────────────────────────────────┤
│ 🏢 分校概覽                     │
│   • 台北校區: 15 師, 42 班       │
│   • 新竹校區: 12 師, 35 班       │
│   • ...                         │
└─────────────────────────────────┘
```

---

## 🎓 學生介面區隔

### 登入方式差異

#### 獨立學生登入
```
┌─────────────────────────┐
│ 學生登入                 │
├─────────────────────────┤
│ Email 或 學號:          │
│ [________________]      │
│                         │
│ 密碼:                   │
│ [________________]      │
│                         │
│ [登入]                  │
└─────────────────────────┘
```

#### 機構學生登入
```
┌─────────────────────────┐
│ 學生登入                 │
├─────────────────────────┤
│ 機構代碼:               │
│ [均一] (auto-fill)      │
│                         │
│ 分校:                   │
│ [台北校區 ▼]            │
│                         │
│ 學號:                   │
│ [________________]      │
│                         │
│ 密碼:                   │
│ [________________]      │
│                         │
│ [登入]                  │
└─────────────────────────┘
```

### URL 路由設計

#### 選項 A: Path-based (推薦)
```
獨立學生:
  https://duotopia.com/student/login
  https://duotopia.com/student/dashboard

機構學生:
  https://duotopia.com/org/{org-slug}/student/login
  https://duotopia.com/org/{org-slug}/student/dashboard

  例如: https://duotopia.com/org/junyiacademy/student/login
```

#### 選項 B: Subdomain (未來可考慮)
```
獨立學生:
  https://app.duotopia.com/student/login

機構學生:
  https://junyiacademy.duotopia.com/student/login
```

### Student Dashboard 差異

#### 獨立學生
```tsx
<StudentLayout>
  <Header>
    <Logo />
    <StudentName>{name}</StudentName>
  </Header>

  <Dashboard>
    <MyAssignments />
    <MyProgress />
    <RecentCourses />
  </Dashboard>
</StudentLayout>
```

#### 機構學生
```tsx
<StudentLayout>
  <Header>
    <Logo />
    <OrgBreadcrumb>{orgName} / {branchName}</OrgBreadcrumb>
    <StudentName>{name}</StudentName>
  </Header>

  <Dashboard>
    {/* 額外的機構功能 */}
    <OrgAnnouncements />
    <BranchActivities />

    {/* 原有功能 */}
    <MyAssignments />
    <MyProgress />
    <RecentCourses />
  </Dashboard>
</StudentLayout>
```

---

## 📚 課程共享機制

### 課程資料表設計

```sql
ALTER TABLE courses ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE courses ADD COLUMN is_organization_shared BOOLEAN DEFAULT false;
ALTER TABLE courses ADD COLUMN visibility VARCHAR(20) DEFAULT 'private';
  -- 'public' (系統公版), 'organization' (機構共用), 'private' (個人)
```

### 課程選擇器 UI

```tsx
<CourseSelector>
  {/* 系統公版課程 - 所有人可見 */}
  <CourseGroup label="📚 系統公版課程">
    <CourseItem>國小數學一年級</CourseItem>
    <CourseItem>國小國語一年級</CourseItem>
  </CourseGroup>

  {/* 機構共用課程 - 僅機構成員可見 */}
  {context.organization_id && (
    <CourseGroup label="🏢 機構共用課程">
      <CourseItem>均一專用補充教材</CourseItem>
      <CourseItem>台北校區特色課程</CourseItem>
      <Badge>可編輯</Badge> {/* 僅 org_admin 可編輯 */}
    </CourseGroup>
  )}

  {/* 個人課程 - 僅建立者可見 */}
  <CourseGroup label="👤 我的個人課程">
    <CourseItem>王老師客製化課程</CourseItem>
    <Button>+ 新增課程</Button>
  </CourseGroup>
</CourseSelector>
```

### 課程存取權限邏輯

```python
# backend/routers/courses.py

def get_available_courses(user: User):
    """
    根據使用者身份回傳可用課程
    """
    courses = []

    # 1. 系統公版課程 (所有人)
    public_courses = db.query(Course).filter(
        Course.visibility == 'public'
    ).all()
    courses.extend(public_courses)

    # 2. 機構共用課程 (僅機構成員)
    if user.organization_id:
        org_courses = db.query(Course).filter(
            Course.organization_id == user.organization_id,
            Course.visibility == 'organization'
        ).all()
        courses.extend(org_courses)

    # 3. 個人課程 (僅建立者)
    personal_courses = db.query(Course).filter(
        Course.teacher_id == user.id,
        Course.visibility == 'private'
    ).all()
    courses.extend(personal_courses)

    return courses
```

---

## 🔐 權限檢查中介層

### Middleware 設計

```python
# backend/middleware/auth.py

def check_scope_access(
    required_scope: str,  # 'self' | 'branch' | 'organization'
    target_id: str,       # 要存取的資源 ID
    current_user: User
) -> bool:
    """
    檢查使用者是否有權限存取目標資源
    """

    if required_scope == 'self':
        # 只能存取自己的資源
        return str(current_user.id) == target_id

    elif required_scope == 'branch':
        # 分校主管可存取該分校所有資源
        if current_user.role == 'branch_manager':
            target = db.query(Teacher).get(target_id)
            return target.branch_id == current_user.branch_id
        return False

    elif required_scope == 'organization':
        # 機構管理員可存取該機構所有資源
        if current_user.role == 'org_admin':
            target = db.query(Teacher).get(target_id)
            return target.organization_id == current_user.organization_id
        return False

    return False
```

### API 權限裝飾器

```python
from functools import wraps

def require_scope(scope: str):
    """
    API endpoint 權限檢查裝飾器
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            target_id = kwargs.get('teacher_id') or kwargs.get('classroom_id')

            if not check_scope_access(scope, target_id, current_user):
                raise HTTPException(403, "沒有權限存取此資源")

            return func(*args, **kwargs)
        return wrapper
    return decorator

# 使用範例
@router.get("/teachers/{teacher_id}/classrooms")
@require_scope('branch')  # 需要 branch 層級權限
def get_teacher_classrooms(
    teacher_id: str,
    current_user: User = Depends(get_current_user)
):
    # 只有該老師本人、分校主管、機構管理員可存取
    ...
```

---

## 🎯 實作優先順序（修訂版）

### Phase 1: 資料模型與權限基礎 (1.5 weeks)
- [ ] 建立 `organizations`, `branches` 資料表
- [ ] 修改 `teachers`, `students`, `courses` 加入 org/branch 欄位
- [ ] 建立 UserContext 與 role 定義
- [ ] 實作權限檢查中介層 `check_scope_access`
- [ ] 更新所有 API 加入範圍檢查

### Phase 2: TeacherLayout 動態化 (1 week)
- [ ] 修改 TeacherLayout 支援動態 Sidebar
- [ ] 實作 TopBar 動態內容（Breadcrumb, Selector）
- [ ] 建立 `getSidebarItems()` 邏輯
- [ ] 測試獨立老師模式（確保向下相容）

### Phase 3: 機構管理功能 (1.5 weeks)
- [ ] 機構管理員 Dashboard
- [ ] 分校管理 CRUD
- [ ] 老師邀請與管理
- [ ] BranchSelector, TeacherSelector 元件

### Phase 4: 課程共享機制 (1 week)
- [ ] 課程資料表加入 visibility, organization_id
- [ ] CourseSelector 動態顯示
- [ ] 課程存取權限 API
- [ ] 機構共用課程管理介面

### Phase 5: 學生介面區隔 (1 week)
- [ ] 機構學生登入流程（org-slug 路由）
- [ ] StudentLayout 動態內容
- [ ] 機構公告、分校活動模組

### Phase 6: 訂閱與金流 (2 weeks)
- [ ] 機構層級訂閱管理
- [ ] TapPay 整合（機構計費）
- [ ] 超量計費邏輯
- [ ] 發票與帳單

---

## ✅ 兼容性保證

### 向下相容原則

1. **資料庫**: 所有新欄位為 nullable，現有資料不受影響
2. **API**: 現有 endpoint 行為不變，新增 org 相關 endpoint
3. **UI**: 獨立老師看到的介面與現在完全一致
4. **登入**: 現有老師/學生登入流程不變

### 測試檢查清單

- [ ] 現有獨立老師可正常登入與操作
- [ ] 現有學生可正常登入與操作
- [ ] 班級、作業、課程功能完全正常
- [ ] 訂閱與付款功能不受影響

---

**文件版本**: v0.2
**最後更新**: 2025-11-26
**狀態**: Draft - Layout 兼容性設計
