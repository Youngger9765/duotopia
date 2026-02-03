# Issue #198: 機構點數系統 + Admin Organization CRUD

**優先級**: 🟡 Medium
**負責人**: Young
**狀態**: In Progress
**分支**: `feat/issue-198-migration`

---

## 📋 Overview

建立完整的機構點數管理系統，包含：
1. 點數資料庫架構（已完成）
2. Admin Organization CRUD 功能
3. Points 使用 API
4. Admin 前端管理介面

**與 #201 的關係**:
- 本 issue 提供點數系統基礎
- #201 (Quota 配置) 已合併到本 issue，作為 Phase 4 實作

---

## 🎯 Goals

### 核心目標
1. ✅ Admin 可以創建機構並設定初始點數
2. ⏰ Admin 可以查看所有機構列表
3. ⏰ Admin 可以編輯機構資訊和調整點數
4. ⏰ 系統可以記錄點數使用歷史
5. ⏰ API 可以查詢和扣除點數

### 延伸目標 (Phase 4)
- Quota 自動配置
- Quota 警告機制
- 月度/年度 quota 重置

---

## 🗄️ Database Schema

### ✅ Phase 1: 已完成

**organizations 表新增欄位**:
```sql
ALTER TABLE organizations ADD COLUMN total_points INT DEFAULT 0 NOT NULL;
ALTER TABLE organizations ADD COLUMN used_points INT DEFAULT 0 NOT NULL;
ALTER TABLE organizations ADD COLUMN last_points_update TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN subscription_start_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN subscription_end_date TIMESTAMP WITH TIME ZONE;
```

**organization_points_log 表** (點數使用記錄):
```sql
CREATE TABLE organization_points_log (
    id SERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    teacher_id INT REFERENCES teachers(id) ON DELETE SET NULL,
    points_used INT NOT NULL,
    feature_type VARCHAR(50),  -- 'ai_generation', 'translation', etc.
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_organization_points_log_organization_id ON organization_points_log(organization_id);
CREATE INDEX ix_organization_points_log_teacher_id ON organization_points_log(teacher_id);
CREATE INDEX ix_organization_points_log_created_at ON organization_points_log(created_at DESC);
```

**Constraints**:
```sql
ALTER TABLE organizations
ADD CONSTRAINT chk_organizations_points_valid
CHECK (used_points <= total_points AND used_points >= 0 AND total_points >= 0);
```

**Migration Files**:
- ✅ `20260203_0143_add_organization_points_system.py`
- ✅ `20260203_1428_238cc2af0367_add_subscription_dates_to_organization.py`
- ✅ `20260203_1600_add_rls_to_organization_points_log.py`

---

## 🔌 API Endpoints

### Phase 1: Admin Organization Create ✅

**Endpoint**: `POST /api/admin/organizations`

**Request**:
```json
{
  "name": "ABC Education",
  "display_name": "ABC 教育集團",
  "description": "Professional English education organization",
  "tax_id": "12345678",
  "teacher_limit": 10,
  "owner_email": "wang@abc.edu.tw",
  "project_staff_emails": ["staff@duotopia.com"],
  "total_points": 10000,
  "subscription_start_date": "2026-01-01T00:00:00Z",
  "subscription_end_date": "2026-12-31T23:59:59Z"
}
```

**Response**: `201 Created`
```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_name": "ABC Education",
  "owner_email": "wang@abc.edu.tw",
  "owner_id": 42,
  "project_staff_assigned": ["staff@duotopia.com"],
  "message": "Organization created successfully"
}
```

**Status**: ✅ Implemented (backend/routers/admin.py:714)

---

### Phase 2: Admin Organization CRUD ⏰

#### List Organizations ✅ (Backend Only)

**Endpoint**: `GET /api/admin/organizations`

**Query Parameters**:
- `search` (optional): Search by name/display_name
- `limit` (optional, default=20): Items per page
- `offset` (optional, default=0): Pagination offset

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "ABC Education",
      "display_name": "ABC 教育集團",
      "owner_email": "wang@abc.edu.tw",
      "owner_name": "王小明",
      "teacher_count": 5,
      "teacher_limit": 10,
      "total_points": 10000,
      "used_points": 2500,
      "remaining_points": 7500,
      "is_active": true,
      "created_at": "2026-01-15T10:30:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**Status**: ✅ Backend implemented (backend/routers/admin.py:952)
**TODO**: ❌ Frontend UI not implemented

---

#### Update Organization ✅ (Backend Only)

**Endpoint**: `PUT /api/admin/organizations/{org_id}`

**Request**:
```json
{
  "display_name": "ABC 教育集團（更新）",
  "description": "Updated description",
  "teacher_limit": 15,
  "total_points": 15000,
  "subscription_end_date": "2027-12-31T23:59:59Z"
}
```

**Response**: `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Organization updated successfully"
}
```

**Status**: ✅ Backend implemented (backend/routers/admin.py:1069)
**TODO**: ❌ Frontend UI not implemented

---

### Phase 3: Points API ❌

#### Query Points Balance

**Endpoint**: `GET /api/organizations/{org_id}/points`

**Response**: `200 OK`
```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_points": 10000,
  "used_points": 2500,
  "remaining_points": 7500,
  "last_updated": "2026-02-03T14:30:00Z"
}
```

**Status**: ❌ Not implemented

---

#### Deduct Points (Internal API)

**Endpoint**: `POST /api/organizations/{org_id}/points/deduct`

**Request**:
```json
{
  "points": 100,
  "feature_type": "ai_generation",
  "description": "Generated 5 AI responses",
  "teacher_id": 42
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "remaining_points": 7400,
  "log_id": 123
}
```

**Error**: `400 Bad Request` (Insufficient points)
```json
{
  "error": "Insufficient points",
  "required": 100,
  "available": 50
}
```

**Status**: ❌ Not implemented

---

#### Points Usage History

**Endpoint**: `GET /api/organizations/{org_id}/points/history`

**Query Parameters**:
- `limit` (optional, default=50): Items per page
- `offset` (optional, default=0): Pagination offset
- `feature_type` (optional): Filter by feature type

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": 123,
      "points_used": 100,
      "feature_type": "ai_generation",
      "description": "Generated 5 AI responses",
      "teacher_email": "teacher@abc.edu.tw",
      "created_at": "2026-02-03T14:30:00Z"
    }
  ],
  "total": 250,
  "limit": 50,
  "offset": 0
}
```

**Status**: ❌ Not implemented

---

## 🎨 Frontend Requirements

### Phase 2: Admin Organization Management UI ❌

#### Organization List Page

**Route**: `/admin/organizations`

**Features**:
- 📊 Table view with columns:
  - Organization Name (name + display_name)
  - Owner (email + name)
  - Teachers (count / limit)
  - Points (used / total)
  - Status (active/inactive)
  - Created Date
  - Actions (Edit button)

- 🔍 Search bar (search by name/display_name/owner email)
- 📄 Pagination (20 items per page)
- ➕ "Create Organization" button (links to existing create page)

**Status**: ❌ Not implemented

---

#### Organization Edit Dialog

**Component**: `OrganizationEditDialog`

**Features**:
- Modal dialog triggered by "Edit" button
- Form fields:
  - Display Name (editable)
  - Description (editable)
  - Teacher Limit (editable)
  - **Total Points** (editable, with confirmation)
  - Subscription End Date (editable)

- 💾 Save button
- ❌ Cancel button
- ✅ Success notification
- ⚠️ Confirmation for points adjustment:
  - "Adjusting points from 10,000 to 15,000. Continue?"

**Status**: ❌ Not implemented

---

### Phase 3: Points Display (Optional) ❌

**Location**: Organization Dashboard (for org owners/admins)

**Features**:
- 💰 Points balance card:
  - Total Points
  - Used Points
  - Remaining Points
  - Progress bar

- ⚠️ Low balance warning (< 10%)
- 📊 Usage history link

**Status**: ❌ Not implemented (low priority)

---

## 🧪 Testing Requirements

### Backend Tests ⏰

**File**: `backend/tests/test_admin_organizations.py`

**Test Cases**:
- ✅ `test_create_organization_success` (已存在)
- ✅ `test_create_organization_requires_admin` (已存在)
- ⏰ `test_list_organizations_success`
- ⏰ `test_list_organizations_pagination`
- ⏰ `test_list_organizations_search`
- ⏰ `test_update_organization_success`
- ⏰ `test_update_organization_points_adjustment`
- ⏰ `test_update_organization_requires_admin`

**File**: `backend/tests/test_organization_points.py` (new)

**Test Cases**:
- ⏰ `test_query_points_success`
- ⏰ `test_deduct_points_success`
- ⏰ `test_deduct_points_insufficient`
- ⏰ `test_deduct_points_creates_log`
- ⏰ `test_points_history_success`
- ⏰ `test_points_history_filter_by_feature`

---

### Frontend Tests ❌

**File**: `frontend/tests/e2e/admin-organizations.spec.ts`

**Test Cases**:
- ❌ `test_admin_can_view_organizations_list`
- ❌ `test_admin_can_search_organizations`
- ❌ `test_admin_can_edit_organization`
- ❌ `test_admin_can_adjust_points`
- ❌ `test_non_admin_cannot_access`

---

## 📅 Implementation Phases

### ✅ Phase 1: Database Schema (Completed)
- Migration files created
- Points fields added to organizations table
- organization_points_log table created
- RLS enabled
- Constraints added

**Estimated**: 3-4 hours
**Actual**: Completed

---

### ⏰ Phase 2: Admin CRUD Frontend (Current)

**Backend**: ✅ Already implemented
- List organizations endpoint exists
- Update organization endpoint exists

**Frontend**: ❌ To implement
1. Create `/admin/organizations` page
2. Build OrganizationTable component
3. Build OrganizationEditDialog component
4. Add search functionality
5. Add pagination
6. Write tests

**Estimated**: 6-8 hours

**Files to Create**:
- `frontend/app/admin/organizations/page.tsx`
- `frontend/components/admin/OrganizationTable.tsx`
- `frontend/components/admin/OrganizationEditDialog.tsx`

**Files to Modify**:
- `frontend/components/admin/AdminSidebar.tsx` (add menu item)

---

### ⏰ Phase 3: Points API (Next)

1. Create `backend/routers/organization_points.py`
2. Implement query points endpoint
3. Implement deduct points endpoint (with transaction)
4. Implement usage history endpoint
5. Write backend tests

**Estimated**: 4-6 hours

**Files to Create**:
- `backend/routers/organization_points.py`
- `backend/routers/schemas/organization_points.py`
- `backend/tests/test_organization_points.py`

---

### 🔮 Phase 4: Quota Configuration (Future - 原 #201)

**Scope**:
- Quota 設定 UI
- Quota 自動分配
- Quota 檢查 middleware
- Quota 警告機制
- 月度/年度 quota 重置

**Status**: Deferred to future sprint

**Reason**:
- 初期可用手動調整 total_points 替代
- Quota 需要更複雜的 UI 和邏輯
- 待客戶數增加後再實作自動化

**Estimated**: 8-12 hours

---

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] All migrations tested on staging
- [ ] Backend tests passing (coverage > 80%)
- [ ] Frontend tests passing
- [ ] Manual testing completed
- [ ] Code review approved

### Deployment
- [ ] Merge to staging branch
- [ ] Verify staging deployment
- [ ] Monitor staging for 24 hours
- [ ] Merge to main
- [ ] Deploy to production

### Post-deployment
- [ ] Verify production deployment
- [ ] Check RLS configuration
- [ ] Monitor error logs
- [ ] Notify stakeholders

---

## 📚 Related Documentation

- Implementation Plan: `docs/plans/2026-02-03-admin-organization-crud.md`
- Organization Spec: `ORG_IMPLEMENTATION_SPEC.md`
- Database Schema: `backend/alembic/versions/20260203_0143_*.py`
- Testing Guide: `docs/TESTING_GUIDE.md`

---

## 🔗 Related Issues

- ~~#201 (Quota 配置系統)~~ → Merged into this issue as Phase 4
- #112 (Organization Hierarchy) - Separate feature, not blocking

---

## ✅ Acceptance Criteria

### Phase 2 (Admin CRUD Frontend)
- [ ] Admin can view paginated list of all organizations
- [ ] Admin can search organizations by name/owner
- [ ] Admin can edit organization details
- [ ] Admin can adjust total_points with confirmation
- [ ] Non-admin users cannot access admin organization pages
- [ ] All changes are logged and auditable

### Phase 3 (Points API)
- [ ] System can query organization points balance
- [ ] System can deduct points with proper validation
- [ ] Points deduction creates audit log entry
- [ ] System prevents negative points (constraint enforced)
- [ ] Points history is queryable with pagination
- [ ] All API endpoints have proper error handling

---

## 🐛 Known Issues

- None currently

---

## 💡 Future Enhancements (Not in Scope)

- Points充值功能 (需串接金流)
- Points到期機制
- Points轉移功能
- Points使用統計報表
- Email notifications for low balance
- Automated quota alerts

---

**Last Updated**: 2026-02-03
**Updated By**: Claude (via requirements-clarification skill)
