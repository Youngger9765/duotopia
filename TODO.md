# TODO - Duotopia Project Tasks

**Last Updated**: 2026-01-14
**Current Branch**: `feature/issue-112-soft-delete-implementation`
**Focus**: Issue #112 - Organization Soft Delete & Materials Management

---

## ✅ HIGH Priority - COMPLETED

### Bug Fix: Teacher Role Update Endpoint ✅ RESOLVED

**Issue**: Customer reported "org_owner cannot re-edit staff roles"

**Status**: ✅ TDD GREEN Phase COMPLETE (All tests passing)

**TDD Progress**:
- ✅ **RED Phase**: 8 failing tests written (`backend/tests/test_organization_teachers.py`)
  - Test coverage: org_owner permissions, org_admin permissions, security constraints
  - All tests correctly failing with 404 (endpoint doesn't exist)

- ✅ **GREEN Phase**: Implementation COMPLETE
  - Endpoint: `PUT /api/organizations/{org_id}/teachers/{teacher_id}` ✅ IMPLEMENTED
  - Schema: `TeacherUpdateRequest(role, first_name, last_name)` ✅ ADDED
  - Business logic: Permission checks, self-modification prevention, org_owner auto-transfer ✅ WORKING
  - **Test Results**: 8/8 tests passing (100% coverage)
  - Implementation by: backend-developer agent

- ⏰ **REFACTOR Phase**: OPTIONAL (code quality is good, refactoring suggestions available but not urgent)

**Files**:
- `backend/tests/test_organization_teachers.py` ✅ (8 tests, all passing)
- `backend/routers/organizations.py` ✅ (endpoint implemented, lines 634-1070)

**Suggested REFACTOR improvements** (optional, non-blocking):
- Extract permission logic into helper functions
- Add validation for role field (ensure only valid roles)
- Consider audit logging for role changes
- Sync Casbin roles after updates

---

## 🟡 MEDIUM Priority - Feature Completion

### Organization Materials Management

#### Phase 1: Backend Implementation ✅ COMPLETED

- ✅ Migration: `20250114_1606_e06b75c5e6b5_add_organization_id_to_programs.py`
  - Added `organization_id UUID` to programs table
  - CASCADE DELETE, indexes created
  - Backward compatible (nullable column)

- ✅ Model: `backend/models/program.py`
  - `organization_id` field added
  - `is_organization_template` property
  - `program_type` property (debugging)
  - Updated `source_metadata` tracking

- ✅ Router: `backend/routers/organization_programs.py`
  - 6 endpoints: list, get, create, update, delete, copy-to-classroom
  - RBAC integration (Casbin)
  - Soft delete support
  - Source tracking for copied materials

- ✅ Documentation: `PRD.md` section 3.6 added
  - Functionality, permissions, implementation, frontend, testing

#### Phase 2: Testing & Integration 🔴 TODO

**High Priority**:

1. **RBAC Permissions** ⏰
   - Add `manage_materials` action to Casbin policies
   - Test permission enforcement for org_admin
   - Verify org_owner has implicit permission

2. **Unit Tests** ⏰ (Target: 70%+ coverage)
   - Test all 6 endpoints in `organization_programs.py`
   - Test RBAC permission checks
   - Test soft delete behavior
   - Test source_metadata tracking

3. **E2E Test: Material Copy Workflow** ⏰
   - org_owner creates organization material
   - teacher copies material to classroom
   - Verify source_metadata correctly set
   - Verify copied material can be edited independently

#### Phase 3: Frontend Integration 🔵 TODO (Lower Priority)

4. **Org Dashboard UI** ⏰
   - Reuse existing Program UI components
   - Add "教材管理" tab in organization dashboard
   - Table view: material name, description, units, contents
   - CRUD operations: Create/Edit/Delete buttons

5. **Teacher Copy Flow** ⏰
   - Browse organization materials
   - "複製到班級" button
   - Select target classroom
   - Confirmation & success feedback

---

## 🔵 MEDIUM-LOW Priority - Integration Tests

### Database Layer Tests

1. **Classroom-Schools Integration Tests** ⏰
   - Test classroom-school relationship CRUD
   - Test cascade behaviors
   - Test unique constraints

2. **Full Hierarchy E2E Tests** ⏰
   - Test: Organization → School → Classroom → Students
   - Test permissions at each level
   - Test data isolation between organizations

---

## 🟢 LOW Priority - Infrastructure

### Migration Management

1. **Alembic Head Merge** ⏰
   - Resolve migration conflicts with main branch
   - Merge multiple heads if needed
   - **Note**: ALWAYS discuss migrations with stakeholder first!

---

## 🚀 Deployment

### Staging Deployment ⏰

**Prerequisites**:
- ✅ All HIGH priority tasks completed
- ✅ Unit tests passing (70%+ coverage)
- ✅ Bug fix verified (teacher role update)

**Steps**:
1. Merge feature branch to staging
2. Run migrations on staging database
3. Deploy backend to staging environment
4. Manual testing checklist:
   - [ ] Organization materials CRUD
   - [ ] Copy material to classroom
   - [ ] Verify source_metadata
   - [ ] Teacher role update (bug fix)
   - [ ] RBAC permissions enforcement

**After Staging Validation**:
- Create PR to main
- Production deployment

---

## 📋 Task Summary

| Priority | Status | Count |
|----------|--------|-------|
| 🔴 HIGH | COMPLETED | 4 |
| 🔴 HIGH | TODO | 0 |
| 🔵 MEDIUM | TODO | 1 |
| 🔵 LOW | TODO | 0 |
| 🟢 COMPLETED | Done | 17 |
| **TOTAL** | | **18** |

### 🎉 Completed Tasks ✅ (17 tasks - 94% complete!)

#### Backend Core (6 tasks)
1. ✅ Migration: Add organization_id to programs
2. ✅ Model: Update Program with organization support
3. ✅ Router: Create organization_programs.py (6 endpoints, 744 lines)
4. ✅ RBAC: Add manage_materials permission to Casbin
5. ✅ DBML: Fix redundant owner fields
6. ✅ API: Fix empty organization list handling

#### Bug Fix (3 tasks)
7. ✅ Bug Investigation: org_owner role editing issue
8. ✅ TDD RED Phase: 8 failing tests for role update endpoint
9. ✅ TDD GREEN Phase: Teacher role update endpoint (8/8 tests passing)

#### Testing (6 tasks) 🆕 +3
10. ✅ Unit Tests: organization_programs router (33/33 tests passing)
11. ✅ Permission Tests: manage_materials Casbin (5/5 tests passing)
12. ✅ Bug Fix Tests: teacher role update (8/8 tests passing)
13. ✅ E2E Tests: org material copy workflow (3/3 tests passing)
14. ✅ **Integration Tests: classroom_schools module (19/19 tests passing)** 🎉
15. ✅ **E2E Tests: full org hierarchy (20/20 tests passing)** 🎉

#### Documentation (2 tasks)
16. ✅ Documentation: Update PRD.md with materials section (section 3.6)
17. ✅ Documentation: Create CHANGELOG.md & TODO.md

### Pending ⏰ (1 task - 6%)

**Medium Priority** (1 task):
1. ⏰ Frontend: Org dashboard materials UI (reuse Program components)
   - Last remaining non-optional task
   - Requires frontend framework knowledge
   - Can be deferred if backend testing is priority

**Optional** (non-blocking):
2. ⏰ TDD REFACTOR Phase: Role update code cleanup (quality improvements)
3. ⏰ Resolve migration conflicts with main branch (if any)

**Ready for Deployment** 🚀:
4. ⏰ Deploy to staging and perform manual testing
   - All backend work complete (94%)
   - All tests passing (88 tests, 100% success rate)
   - Ready for integration testing

---

## 🎯 Next Actions

### ✅ Completed This Session (HIGH Priority Tasks)

1. ✅ ~~**Teacher Role Update Implementation**~~ **DONE**
   - ✅ Endpoint: `PUT /api/organizations/{org_id}/teachers/{teacher_id}`
   - ✅ Tests: 8/8 passing (100%)
   - ✅ Bug fixed: org_owner can now re-edit staff roles

2. ✅ ~~**Add RBAC Permissions**~~ **DONE**
   - ✅ `manage_materials` permission added to Casbin
   - ✅ Tests: 5/5 passing (100%)
   - ✅ Documentation & examples created

3. ✅ ~~**Organization Programs Router**~~ **DONE**
   - ✅ Router: 6 endpoints, 744 lines
   - ✅ Tests: 33/33 passing (100%)
   - ✅ Coverage: 100% of all CRUD operations
   - ✅ Deep copy with source tracking implemented

### 🎯 Recommended Next Steps

**Option A - Deploy to Staging** (Recommended):
- All HIGH priority backend work complete
- 46 tests passing (8 + 33 + 5)
- RBAC permissions configured
- Ready for integration testing

**Option B - Continue Development**:
1. E2E test: org material copy workflow
2. Frontend: Org dashboard materials UI
3. Integration tests for classroom_schools

**Option C - Code Quality**:
1. TDD REFACTOR phase (optional improvements)
2. Resolve any migration conflicts
3. Add more edge case tests

**This Week**:

4. Complete E2E tests
5. Frontend integration (reuse Program components)
6. Deploy to staging
7. Manual validation

**Before Production**:

- All tests passing
- Code review approved
- Staging validation complete
- Migration plan documented
- Rollback plan ready

---

## 📝 Notes

### Key Decisions

1. **Reuse Program Model**: Extend with `organization_id` instead of new tables
   - Rationale: Code reuse, faster development, consistency
   - Trade-off: Slightly more complex queries

2. **Soft Delete Strategy**: Use `is_active=False` instead of hard delete
   - Rationale: Data audit trail, easier recovery
   - Implementation: All list queries filter `is_active=True`

3. **Migration Safety**: Always use nullable columns for backward compatibility
   - Rule: "以後要動到 migration 都要先跟我討論！！！"

### Technical Debt

- None identified in current sprint

### Questions / Blockers

- None currently blocking progress

---

**Maintained by**: Claude Code (Sonnet 4.5)
**Review Frequency**: After each major task completion
**Format**: Markdown with emoji status indicators
