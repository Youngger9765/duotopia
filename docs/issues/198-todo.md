# Issue #198 Implementation TODO

**Branch**: `feat/issue-198-migration`
**Spec**: `docs/issues/198-complete-spec.md`

---

## 📊 Progress Overview

- ✅ Phase 1: Database Schema (100%)
- ⏰ Phase 2: Admin CRUD Frontend (0%)
- ⏰ Phase 3: Points API (0%)
- 🔮 Phase 4: Quota Configuration (Deferred)

---

## ✅ Phase 1: Database Schema (COMPLETED)

### Migration Files
- [x] Create `20260203_0143_add_organization_points_system.py`
  - [x] Add total_points column
  - [x] Add used_points column
  - [x] Add last_points_update column
  - [x] Create organization_points_log table
  - [x] Add foreign keys
  - [x] Add indexes
  - [x] Add check constraint
  - [x] Enable RLS

- [x] Create `20260203_1428_238cc2af0367_add_subscription_dates_to_organization.py`
  - [x] Add subscription_start_date column
  - [x] Add subscription_end_date column

- [x] Create `20260203_1600_add_rls_to_organization_points_log.py`
  - [x] Enable RLS on organization_points_log table

### Schemas
- [x] Update `AdminOrganizationCreate` schema
  - [x] Add total_points field
  - [x] Add subscription_start_date field
  - [x] Add subscription_end_date field

### Deployment
- [x] Merge migrations to staging
- [x] Fix RLS verification issue
- [x] Deploy to staging successfully

---

## ⏰ Phase 2: Admin CRUD Frontend (0% - CURRENT PHASE)

### Backend Verification
- [ ] **Verify List Endpoint** (`GET /api/admin/organizations`)
  - [ ] Test manually with curl/Postman
  - [ ] Check response matches spec
  - [ ] Verify pagination works
  - [ ] Verify search works
  - [ ] Add missing tests if needed

- [ ] **Verify Update Endpoint** (`PUT /api/admin/organizations/{org_id}`)
  - [ ] Test manually with curl/Postman
  - [ ] Check response matches spec
  - [ ] Verify points adjustment works
  - [ ] Verify subscription date update works
  - [ ] Add missing tests if needed

### Frontend Setup
- [ ] **Create Admin Organizations Page**
  - File: `frontend/app/admin/organizations/page.tsx`
  - [ ] Create page component
  - [ ] Add authentication check (admin only)
  - [ ] Add page layout
  - [ ] Add page title and description
  - [ ] Add "Create Organization" button (link to existing `/admin/organizations/create`)

### OrganizationTable Component
- [ ] **Create OrganizationTable Component**
  - File: `frontend/components/admin/OrganizationTable.tsx`

  - [ ] **Table Structure**
    - [ ] Setup shadcn/ui Table component
    - [ ] Define columns:
      - [ ] Organization Name (name + display_name)
      - [ ] Owner (email + name with tooltip)
      - [ ] Teachers (count / limit with progress bar)
      - [ ] Points (used / total with progress bar)
      - [ ] Status (active badge)
      - [ ] Created Date (formatted)
      - [ ] Actions (Edit button)

  - [ ] **Data Fetching**
    - [ ] Create API client function (`getOrganizations`)
    - [ ] Use React Query for data fetching
    - [ ] Handle loading state
    - [ ] Handle error state
    - [ ] Handle empty state

  - [ ] **Search Functionality**
    - [ ] Add search input above table
    - [ ] Debounce search input (300ms)
    - [ ] Update API call with search param
    - [ ] Clear search button

  - [ ] **Pagination**
    - [ ] Add pagination controls below table
    - [ ] Show total count
    - [ ] Show current page / total pages
    - [ ] Previous/Next buttons
    - [ ] Page size selector (10, 20, 50)

  - [ ] **Styling**
    - [ ] Responsive table (scroll on mobile)
    - [ ] Hover effects
    - [ ] Loading skeleton
    - [ ] Empty state illustration

### OrganizationEditDialog Component
- [ ] **Create OrganizationEditDialog Component**
  - File: `frontend/components/admin/OrganizationEditDialog.tsx`

  - [ ] **Dialog Structure**
    - [ ] Use shadcn/ui Dialog component
    - [ ] Add dialog trigger (Edit button)
    - [ ] Add dialog header with title
    - [ ] Add dialog content area
    - [ ] Add dialog footer with actions

  - [ ] **Form Fields**
    - [ ] Display Name (Input)
    - [ ] Description (Textarea)
    - [ ] Teacher Limit (NumberInput)
    - [ ] Total Points (NumberInput with confirmation)
    - [ ] Subscription End Date (DatePicker)

  - [ ] **Read-only Fields** (displayed but not editable)
    - [ ] Organization ID
    - [ ] Name (英文名稱)
    - [ ] Owner Email
    - [ ] Used Points
    - [ ] Created Date

  - [ ] **Form Validation**
    - [ ] Use react-hook-form
    - [ ] Use zod schema validation
    - [ ] Display validation errors
    - [ ] Disable submit if invalid

  - [ ] **Points Adjustment Confirmation**
    - [ ] Detect if total_points changed
    - [ ] Show confirmation dialog before save
    - [ ] Display old value → new value
    - [ ] Require explicit confirmation

  - [ ] **Save Logic**
    - [ ] Create API client function (`updateOrganization`)
    - [ ] Use React Query mutation
    - [ ] Handle success (show toast, close dialog, refetch list)
    - [ ] Handle error (show error message)

  - [ ] **UI Polish**
    - [ ] Loading state during save
    - [ ] Disable form during save
    - [ ] Success toast notification
    - [ ] Error toast notification

### Navigation Integration
- [ ] **Update Admin Sidebar**
  - File: `frontend/components/admin/AdminSidebar.tsx` (or equivalent)
  - [ ] Add "Organizations" menu item
  - [ ] Add icon (Building2 or similar)
  - [ ] Set active state when on `/admin/organizations`
  - [ ] Position after Dashboard, before Teachers

### Testing
- [ ] **Unit Tests**
  - File: `frontend/components/admin/__tests__/OrganizationTable.test.tsx`
  - [ ] Test table renders correctly
  - [ ] Test search functionality
  - [ ] Test pagination
  - [ ] Test empty state
  - [ ] Test error state

- [ ] **Unit Tests**
  - File: `frontend/components/admin/__tests__/OrganizationEditDialog.test.tsx`
  - [ ] Test dialog opens/closes
  - [ ] Test form validation
  - [ ] Test points confirmation
  - [ ] Test save success
  - [ ] Test save error

- [ ] **E2E Tests**
  - File: `frontend/tests/e2e/admin-organizations.spec.ts`
  - [ ] Test admin can view organizations list
  - [ ] Test admin can search organizations
  - [ ] Test admin can edit organization
  - [ ] Test admin can adjust points with confirmation
  - [ ] Test non-admin cannot access page

### Manual Testing Checklist
- [ ] Login as admin user
- [ ] Navigate to `/admin/organizations`
- [ ] Verify organizations list displays correctly
- [ ] Test search functionality
- [ ] Test pagination (if > 20 orgs)
- [ ] Click "Edit" on an organization
- [ ] Update display name → Save → Verify update
- [ ] Adjust total_points → Confirm → Verify update
- [ ] Update subscription_end_date → Save → Verify update
- [ ] Test validation errors
- [ ] Logout and login as non-admin → Verify 403/redirect

---

## ⏰ Phase 3: Points API (0% - NEXT PHASE)

### Backend Setup
- [ ] **Create Points Router**
  - File: `backend/routers/organization_points.py`
  - [ ] Create router with prefix `/api/organizations/{org_id}/points`
  - [ ] Add admin/owner authorization checks

### Schemas
- [ ] **Create Points Schemas**
  - File: `backend/routers/schemas/organization_points.py`
  - [ ] `PointsBalanceResponse`
  - [ ] `DeductPointsRequest`
  - [ ] `DeductPointsResponse`
  - [ ] `PointsHistoryItem`
  - [ ] `PointsHistoryResponse`

### Query Points Endpoint
- [ ] **Implement GET `/api/organizations/{org_id}/points`**
  - [ ] Create endpoint function
  - [ ] Query organization by ID
  - [ ] Return total_points, used_points, remaining_points
  - [ ] Return last_points_update timestamp
  - [ ] Handle organization not found (404)
  - [ ] Add authorization check (owner/admin only)

### Deduct Points Endpoint
- [ ] **Implement POST `/api/organizations/{org_id}/points/deduct`**
  - [ ] Create endpoint function
  - [ ] Validate request (points > 0, feature_type not empty)
  - [ ] Start database transaction
  - [ ] Check sufficient points available
  - [ ] Update organization.used_points
  - [ ] Update organization.last_points_update
  - [ ] Insert record to organization_points_log
  - [ ] Commit transaction
  - [ ] Return new balance
  - [ ] Handle insufficient points error (400)
  - [ ] Handle database errors (rollback transaction)
  - [ ] Add internal API authentication (not exposed publicly)

### Points History Endpoint
- [ ] **Implement GET `/api/organizations/{org_id}/points/history`**
  - [ ] Create endpoint function
  - [ ] Query organization_points_log with JOIN to teachers
  - [ ] Support pagination (limit, offset)
  - [ ] Support filtering by feature_type
  - [ ] Order by created_at DESC
  - [ ] Return paginated results
  - [ ] Include teacher email/name in response
  - [ ] Add authorization check (owner/admin only)

### Testing
- [ ] **Backend Tests**
  - File: `backend/tests/test_organization_points.py`

  - [ ] **Query Points Tests**
    - [ ] test_query_points_success
    - [ ] test_query_points_organization_not_found
    - [ ] test_query_points_requires_auth

  - [ ] **Deduct Points Tests**
    - [ ] test_deduct_points_success
    - [ ] test_deduct_points_insufficient
    - [ ] test_deduct_points_creates_log
    - [ ] test_deduct_points_updates_timestamp
    - [ ] test_deduct_points_invalid_amount (negative, zero)
    - [ ] test_deduct_points_transaction_rollback_on_error

  - [ ] **Points History Tests**
    - [ ] test_points_history_success
    - [ ] test_points_history_pagination
    - [ ] test_points_history_filter_by_feature
    - [ ] test_points_history_requires_auth
    - [ ] test_points_history_empty

### Integration
- [ ] **Add Points API to main router**
  - File: `backend/main.py`
  - [ ] Import organization_points router
  - [ ] Include router in app

### Manual Testing Checklist
- [ ] Test GET /api/organizations/{org_id}/points
  - [ ] As owner → 200 OK
  - [ ] As admin → 200 OK
  - [ ] As non-owner → 403 Forbidden
  - [ ] Invalid org_id → 404 Not Found

- [ ] Test POST /api/organizations/{org_id}/points/deduct
  - [ ] Sufficient points → 200 OK, points deducted
  - [ ] Insufficient points → 400 Bad Request
  - [ ] Invalid points (0, negative) → 400 Bad Request
  - [ ] Verify log entry created
  - [ ] Verify last_points_update updated

- [ ] Test GET /api/organizations/{org_id}/points/history
  - [ ] Returns paginated results
  - [ ] Pagination works (limit, offset)
  - [ ] Filter by feature_type works
  - [ ] Ordered by created_at DESC

---

## 🔮 Phase 4: Quota Configuration (DEFERRED)

**Status**: Not implementing in this sprint

**Reason**:
- Initial phase can use manual total_points adjustment
- Quota automation is optimization, not core functionality
- Will implement when customer base grows

**Future Tasks** (for reference):
- [ ] Design quota allocation strategy
- [ ] Create quota settings UI
- [ ] Implement quota auto-allocation
- [ ] Add quota warning system
- [ ] Implement monthly/yearly quota reset
- [ ] Add quota usage analytics

---

## 🚀 Deployment Steps

### Pre-deployment Checklist
- [ ] All Phase 2 tasks completed
- [ ] All Phase 3 tasks completed
- [ ] Backend tests passing (pytest -v)
- [ ] Frontend tests passing (npm test)
- [ ] Manual testing completed
- [ ] Code review requested and approved
- [ ] No merge conflicts with staging

### Staging Deployment
- [ ] Merge feat/issue-198-migration to staging
- [ ] Monitor CI/CD pipeline
  - [ ] Build succeeds
  - [ ] Tests pass
  - [ ] Migrations run successfully
  - [ ] RLS verification passes
  - [ ] Deployment completes
- [ ] Manual verification on staging
  - [ ] Admin can access /admin/organizations
  - [ ] List displays correctly
  - [ ] Edit functionality works
  - [ ] Points API responds correctly
- [ ] Monitor staging for 24-48 hours
- [ ] Check error logs (no new errors)

### Production Deployment
- [ ] Get approval from stakeholders
- [ ] Create PR from staging to main
- [ ] Final code review
- [ ] Merge to main
- [ ] Monitor production deployment
  - [ ] Build succeeds
  - [ ] Tests pass
  - [ ] Migrations run successfully
  - [ ] Deployment completes
- [ ] Smoke test on production
  - [ ] Admin dashboard accessible
  - [ ] Organizations list works
  - [ ] No errors in console
- [ ] Monitor for 1 week
- [ ] Document any issues

### Post-deployment
- [ ] Update issue status
- [ ] Close Issue #201 (merged into #198)
- [ ] Notify stakeholders
- [ ] Update documentation if needed
- [ ] Archive Phase 4 tasks for future sprint

---

## 📝 Notes

### Design Decisions
- **Why separate frontend and backend phases?**
  - Backend already implemented, just needs verification
  - Frontend is new work, needs careful design
  - Can test backend independently via API

- **Why defer Quota (Phase 4)?**
  - Manual adjustment sufficient for initial customers
  - Quota automation adds complexity
  - Better to validate core functionality first
  - Can implement when scale requires it

### Dependencies
- Phase 2 (Frontend) depends on Phase 1 (Database) ✅
- Phase 3 (Points API) independent of Phase 2
- Can work on Phase 2 and 3 in parallel if needed

### Estimated Timeline
- Phase 2: 6-8 hours (1-2 days)
- Phase 3: 4-6 hours (1 day)
- Testing & Review: 2-3 hours
- **Total: 12-17 hours (3-4 days)**

### Team Notes
- Frontend developer: Focus on Phase 2
- Backend developer: Can start Phase 3 in parallel
- QA: Review test coverage, prepare test plan

---

**Last Updated**: 2026-02-03
**Created By**: Claude (requirements-clarification skill)
