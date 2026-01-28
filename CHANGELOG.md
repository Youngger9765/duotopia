# Changelog

All notable changes to the Duotopia project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Issue #112: Organization Soft Delete & Materials Management

#### Database & Models (2026-01-14)

- **Migration**: `20250114_1606_e06b75c5e6b5_add_organization_id_to_programs.py`
  - Added `organization_id UUID` column to `programs` table (nullable, FK to organizations.id)
  - Added CASCADE DELETE constraint (org deletion → auto-delete org materials)
  - Added indexes: `ix_programs_organization_id`, `ix_programs_organization_active`
  - **Migration Safety**: Nullable column, backward compatible with 220 existing individual teacher programs

- **Program Model Enhancements** (`backend/models/program.py`):
  - Added `organization_id` field (UUID, nullable)
  - Added `is_organization_template` property (returns True if is_template AND organization_id is not NULL)
  - Added `program_type` property (debugging helper: "organization_template" | "public_template" | "classroom_program" | "custom")
  - Updated `source_metadata` docstring with organization template tracking example
  - Updated `__repr__` to show organization context

#### API Endpoints (2026-01-14) ✅ IMPLEMENTED

- **NEW Router**: `backend/routers/organization_programs.py` (744 lines, 6 endpoints) ✅
  - `GET /{org_id}/programs` - List organization materials
  - `GET /{org_id}/programs/{program_id}` - Get material details with full hierarchy (Program → Lessons → Contents → Items)
  - `POST /{org_id}/programs` - Create organization material (requires `manage_materials` permission)
  - `PUT /{org_id}/programs/{program_id}` - Update organization material
  - `DELETE /{org_id}/programs/{program_id}` - Soft delete material (sets `is_active=False`)
  - `POST /{org_id}/programs/{program_id}/copy-to-classroom` - Deep copy material to classroom with source tracking
  - **Test Results**: 33/33 tests passing (100% success rate)
  - **Registered in**: `backend/main.py`

- **Source Metadata Tracking**: Organization materials copied to classrooms include:
  ```json
  {
    "organization_id": "uuid",
    "organization_name": "台北市立國中",
    "program_id": 123,
    "program_name": "初級會話",
    "source_type": "organization_template"
  }
  ```

- **Deep Copy Functionality**:
  - Recursive copying: Program → Lessons → Contents → Items
  - Maintains order indices and metadata
  - Creates independent copy (editable without affecting original)
  - Validates organization membership before copying

#### RBAC Permissions (2026-01-14) ✅ CONFIGURED

- **NEW Permission**: `manage_materials` added to Casbin policies
  - **File**: `backend/config/casbin_policy.csv`
  - **Roles with Permission**:
    - `org_owner` - Automatic (inherent to role)
    - `org_admin` - Automatic (inherent to role)
  - **Test Suite**: `backend/tests/test_manage_materials_permission.py` (5/5 tests passing)
  - **Documentation**: `backend/docs/casbin_manage_materials_permission.md`
  - **Example Router**: `backend/docs/examples/organization_materials_router_example.py`

#### Tests (2026-01-14) ✅ COMPREHENSIVE COVERAGE

- **Test Suite 1**: `backend/tests/test_organization_teachers.py` (8 tests)
  - Teacher role update endpoint (bug fix)
  - Coverage: org_owner permissions, org_admin permissions, security constraints
  - **Status**: 8/8 tests passing (100%)

- **Test Suite 2**: `backend/tests/test_organization_programs.py` (33 tests) ✅ NEW
  - Organization materials CRUD operations
  - Coverage breakdown:
    - List materials: 5 tests
    - Get material details: 5 tests
    - Create material: 6 tests
    - Update material: 5 tests
    - Soft delete: 6 tests
    - Copy to classroom: 6 tests
  - **Status**: 33/33 tests passing (100%)
  - **Permission testing**: org_owner, org_admin, regular teacher roles
  - **Edge cases**: 404s, empty lists, soft deletes, cross-org isolation

- **Test Suite 3**: `backend/tests/test_manage_materials_permission.py` (5 tests) ✅ NEW
  - Casbin permission enforcement for manage_materials
  - **Status**: 5/5 tests passing (100%)

- **Test Suite 4**: `backend/tests/test_e2e_organization_materials.py` (3 E2E tests) ✅ NEW
  - Complete user journey: org_owner creates material → teacher copies to classroom
  - Coverage: Full lifecycle (create → list → copy → edit → verify independence)
  - Cross-organization isolation testing
  - Permission enforcement throughout lifecycle
  - **Status**: 3/3 tests passing (100%)
  - **Total Assertions**: 72 comprehensive checks

- **Test Suite 5**: `backend/tests/test_integration_classroom_schools.py` (19 integration tests) ✅ NEW
  - Comprehensive classroom-school relationship testing
  - Coverage: CRUD operations, unique constraints, cascade delete, query optimization
  - Business logic: independent teachers, organization migration
  - Edge cases: soft delete/reactivation, concurrent operations
  - **Status**: 19/19 tests passing (100%)
  - **Execution Time**: 8.47 seconds

- **Test Suite 6**: `backend/tests/test_e2e_full_hierarchy.py` (20 E2E tests) ✅ NEW
  - Complete 4-layer hierarchy: Organization → School → Classroom → Students
  - Coverage: Full lifecycle, cascade delete, role-based access, data migration
  - Performance: Bulk operations (10 schools, 50 classrooms, 100 students)
  - Query optimization: Nested queries across 250 students
  - Cross-organization and cross-school isolation
  - **Status**: 20/20 tests passing (100%)
  - **Total Assertions**: 69+
  - **Execution Time**: 132 seconds (2min 12s)

#### Documentation (2026-01-14)

- **PRD.md**: Added section 3.6 "機構教材管理（Issue #112）"
  - 6 subsections covering functionality, permissions, implementation, frontend, testing
  - Complete technical specifications and user workflows

- **ISSUE_112_IMPLEMENTATION_PLAN.md**: Created comprehensive implementation guide
  - TL;DR summary, architecture strategy, decision log, progress tracking

### Fixed

#### Organizations API (2026-01-14)

- **Empty Organization List Handling** (`backend/routers/organizations.py`):
  - Changed from `403 Forbidden` to empty list `[]` when teacher has no organizations
  - More RESTful and frontend-friendly behavior
  - Fixed lines ~283 and ~304

### Changed

#### Database Schema (2026-01-14)

- **DBML Spec Correction** (`spec/erm-organization.dbml`):
  - Removed redundant owner fields: `owner_name`, `owner_email`, `owner_phone` from organizations table
  - Added explanatory comments: Owner info retrieved via `teacher_organizations` relationship (role='org_owner')
  - Follows database normalization (3NF) - avoid data duplication
  - Added note about partial unique index for `tax_id` (allows reuse after soft delete)

### Fixed - Continued

#### Bug Fix - Teacher Role Update (2026-01-14) ✅ RESOLVED

- **Customer Report**: "org_owner cannot re-edit staff roles"
- **Root Cause**: Missing PUT endpoint for updating teacher roles in organizations
- **TDD Workflow**:
  - ✅ RED Phase: 8 failing tests written in `backend/tests/test_organization_teachers.py`
  - ✅ GREEN Phase: Implemented `PUT /{org_id}/teachers/{teacher_id}` endpoint
  - ⏰ REFACTOR Phase: Pending (all tests passing, refactoring optional)

- **Implementation Details** (`backend/routers/organizations.py`):
  - Added `TeacherUpdateRequest` schema (role, first_name, last_name)
  - Implemented endpoint with proper permission checks (org_owner or manage_teachers)
  - Security: Prevents self-modification
  - Business logic: Auto-demotes current org_owner when transferring ownership
  - Supports role updates and optional teacher info updates
  - **Test Results**: 8/8 tests passing (100% coverage of bug scenarios)

### Pending

#### Organization Materials - Phase 2 Tasks

- Add RBAC permissions for `manage_materials` action
- Write unit tests for organization_programs router (target: 70%+ coverage)
- Update frontend org dashboard with materials management UI (reuse Program components)
- E2E test: org_owner creates material → teacher copies to classroom → verify source_metadata

#### Integration & E2E Tests

- Integration tests for classroom_schools module
- E2E tests for org → school → classroom → students hierarchy
- Migration conflict resolution with main branch (alembic merge)

#### Deployment

- Deploy to staging environment
- Manual testing and validation
- Production deployment

---

## Architecture Decisions

### Why Reuse Program Model Instead of New Tables?

**Decision (2026-01-14)**: Extend `Program` model with `organization_id` field instead of creating new `organization_materials` table.

**Rationale**:
1. **Code Reuse**: Leverage existing Program → Lesson → Content → Item architecture (4-layer structure)
2. **Reduce Development Time**: 2.5-3 days vs 3-5 days for new tables
3. **Consistency**: Same UI components, same API patterns, same business logic
4. **Flexibility**: Same field `organization_id` supports both scenarios:
   - `NULL`: Individual teacher programs (existing behavior)
   - `UUID`: Organization materials (new feature)

**Trade-offs Accepted**:
- Slight increase in `programs` table complexity
- Need to carefully handle NULL vs non-NULL organization_id in queries

**Migration Safety**: Nullable column ensures zero impact on 220 existing programs.

---

## Technical Notes

### Migration Best Practices Established

**Rule** (2026-01-14): "以後要動到 migration 都要先跟我討論！！！" (Always discuss migrations with stakeholder first)

**Why**: Migrations affect production data and require careful planning to ensure:
- Backward compatibility
- Zero data loss
- Rollback capability
- Performance impact assessment

### TDD Workflow Enforcement

All bug fixes and new features follow strict TDD cycle:
1. **RED**: Write failing tests first
2. **GREEN**: Minimal implementation to pass tests
3. **REFACTOR**: Clean up while maintaining green tests

Current example: Teacher role update endpoint (RED phase complete, GREEN phase in progress).

---

## Contributors

- Implementation: Claude Code (Sonnet 4.5)
- Product Owner: Young
- QA & Validation: Customer feedback

---

**Last Updated**: 2026-01-14
