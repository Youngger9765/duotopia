# Admin Organization Creation - Extended Features Design

**Date**: 2026-01-30
**Status**: Phase 1 Complete ✅ (2026-01-30)
**Implemented**: Tasks 1-3 (Teacher statistics, Owner lookup, Project staff)
**Branch**: feat/issue-112-org-hierarchy
**Source**: spec/features/organization/機構設定與擁有人註冊.feature

---

## Overview

This document clarifies the implementation approach for extending the Admin Organization Creation feature to match client requirements in the BDD spec.

## Requirements Analysis

### Client Requirements (from 機構設定與擁有人註冊.feature)

Original 7 features requested:
1. 擁有人尚未註冊流程（發送認證信）
2. 設定密碼 Token 流程
3. 專案服務人員指派（org_admin）
4. 總點數欄位（total_points）
5. 擁有人姓名、手機欄位（owner_name, owner_phone）
6. 教師授權數顯示
7. 剩餘點數顯示

---

## Database Schema Analysis

After reviewing existing models, we found that **most required fields already exist**:

### ✅ Existing Fields (No Migration Required)

#### Organization Model
```python
class Organization:
    teacher_limit = Column(Integer)  # 教師授權數上限 ✅
    contact_email = Column(String(200))  # Already exists
    contact_phone = Column(String(50))   # Already exists
    address = Column(Text)               # Already exists
```

#### Teacher Model
```python
class Teacher:
    name = Column(String(100))                    # 擁有人姓名 ✅
    phone = Column(String(20))                    # 擁有人手機 ✅

    # Email verification tokens ✅
    email_verification_token = Column(String(100))
    email_verification_sent_at = Column(DateTime(timezone=True))

    # Password reset tokens ✅
    password_reset_token = Column(String(100))
    password_reset_sent_at = Column(DateTime(timezone=True))
    password_reset_expires_at = Column(DateTime(timezone=True))
```

#### TeacherOrganization Model
```python
class TeacherOrganization:
    role = Column(String)  # Can support multiple org_admin ✅
```

### ❌ Missing Field (Migration Required)

```python
class Organization:
    total_points = Column(Integer)  # NOT EXISTS - Need migration
```

---

## Implementation Categorization

### Category A: No Migration Required (5 features)

#### Feature 1: 專案服務人員指派（org_admin）
**Current State**: TeacherOrganization.role field exists
**Implementation**:
- Frontend: Add "專案服務人員" field to creation form (multi-select)
- Backend: Support assigning multiple org_admin roles during creation
- Casbin: Add org_admin role permissions

**Estimated Effort**: 4-6 hours

---

#### Feature 2: 教師授權數顯示
**Current State**: Organization.teacher_limit field exists
**Implementation**:
- Backend: Add statistics API to count active teachers in organization
  ```python
  GET /api/organizations/{org_id}/statistics
  Response: {
    "teacher_count": 5,
    "teacher_limit": 10,
    "usage_percentage": 50
  }
  ```
- Frontend: Display "已使用 5 / 總數 10"

**Estimated Effort**: 3-4 hours

---

#### Feature 3: 擁有人姓名、手機欄位
**Current State**: Teacher.name and Teacher.phone fields exist
**Implementation**:
- Frontend: When admin enters owner_email, fetch and display owner's name/phone
  ```typescript
  // On owner_email change
  const owner = await fetchTeacherByEmail(email);
  setOwnerInfo({ name: owner.name, phone: owner.phone });
  ```
- Display as read-only info (not editable in org creation form)

**Estimated Effort**: 2-3 hours

---

#### Feature 4: 擁有人尚未註冊流程
**Current State**: Teacher.email_verification_token and password_reset_token exist
**Implementation**:

**Option A: Simple (Recommended)**
- Admin inputs: owner_email, owner_name, owner_phone
- System creates Teacher account with random password
- Display initial password to admin (for offline communication)
- Owner must change password on first login

**Option B: Email Flow (Client Spec)**
- Admin inputs owner info
- System creates Teacher account
- Generates password_reset_token (24hr expiry)
- Sends verification email to owner
- Owner clicks link → sets password → auto-login

**Decision**: Start with Option A (simpler, no email infrastructure)
Can upgrade to Option B later if needed.

**Estimated Effort**:
- Option A: 4-5 hours
- Option B: 12-16 hours (requires email sending infrastructure)

---

#### Feature 5: 設定密碼 Token 流程
**Current State**: Teacher.password_reset_token and password_reset_expires_at exist
**Implementation**:
- Only needed if choosing Option B for Feature 4
- Reuse existing password reset mechanism
- Token expiry: 24 hours (configurable)

**Estimated Effort**: Included in Feature 4 Option B

---

### Category B: Migration Required (2 features)

#### Feature 6: 總點數欄位（total_points）

**Analysis**: Two approaches considered

**Approach A: Use Existing Teacher-Level Points** (Rejected)
- No migration needed
- Organization points = sum of all teachers' SubscriptionPeriod.quota_total
- Problem: Conceptually incorrect (org should have own point pool)

**Approach B: Organization-Level Points** (✅ Chosen)
- Add Organization.total_points field
- Clear concept: Organization purchases points, teachers share from pool
- Matches client requirement in BDD spec

**Migration**:
```python
# alembic revision
def upgrade():
    op.add_column('organizations',
        sa.Column('total_points', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('organizations', 'total_points')
```

**Estimated Effort**:
- Migration: 1 hour
- Backend API update: 2 hours
- Frontend display: 2 hours
**Total**: 5 hours

---

#### Feature 7: 剩餘點數顯示
**Current State**: Depends on Feature 6
**Implementation**:
- Calculate: remaining = total_points - sum(point_usage_logs.points_used)
- Display in organization dashboard
- API:
  ```python
  GET /api/organizations/{org_id}/points
  Response: {
    "total_points": 117000,
    "used_points": 12000,
    "remaining_points": 105000
  }
  ```

**Estimated Effort**: 3-4 hours (assuming Feature 6 is done)

---

## Recommended Implementation Order

### Phase 1: No Migration Features (Priority 1) ✅ COMPLETED (2026-01-30)
1. ✅ Feature 2: 教師授權數顯示 (3-4h) - DONE
   - Backend: GET /api/admin/organizations/{id}/statistics
   - Frontend: TeacherUsageCard component
2. ✅ Feature 3: 擁有人姓名、手機欄位 (2-3h) - DONE
   - Backend: GET /api/admin/teachers/lookup?email=xxx
   - Frontend: Auto-fetch on owner_email change
3. ✅ Feature 1: 專案服務人員指派 (4-6h) - DONE
   - Backend: project_staff_emails field support
   - Frontend: Multi-select input with validation
   - Casbin: org_admin role permissions

**Phase 1 Total**: 9-13 hours
**Implementation**: 14 backend tests, 2 new API endpoints, frontend form enhancements
**Commits**: 9 commits (2b7b12df to 967294d7)
**Test Coverage**: 100% for new features

### Phase 2: Unregistered Owner Flow (Priority 2)
4. ✅ Feature 4: 擁有人尚未註冊流程 - Option A (4-5h)

**Phase 2 Total**: 4-5 hours

### Phase 3: Points System (Priority 3) - **ON HOLD**
5. ⏸️ Feature 6: 總點數欄位 (5h) - Requires migration approval
6. ⏸️ Feature 7: 剩餘點數顯示 (3-4h)

**Phase 3 Total**: 8-9 hours

---

## Total Effort Estimate

- **Without Migration** (Phase 1-2): 13-18 hours
- **With Migration** (Phase 1-3): 21-27 hours

---

## Decision Log

### 2026-01-30: Migration Strategy
- **Decision**: Prioritize no-migration features first
- **Reason**: Faster delivery, lower risk
- **Next Steps**: Implement Phase 1-2, defer Phase 3 pending client confirmation

### 2026-01-30: Unregistered Owner Flow
- **Decision**: Start with Option A (admin-created password)
- **Reason**: Simpler, no email infrastructure required
- **Future**: Can upgrade to Option B (email flow) if client requires

### 2026-01-30: Organization Points
- **Decision**: Use Approach B (organization-level points pool)
- **Reason**: Matches client spec, clearer concept
- **Status**: ON HOLD - waiting for migration approval

---

## Next Steps

1. ✅ Document design (this file)
2. ⏰ Update TODO.md with categorized tasks
3. ⏰ Update ORG_PRD.md Missing Features section
4. ⏰ Create implementation plan using writing-plans skill
5. ⏰ Implement Phase 1 features
6. ⏰ User testing
7. ⏰ Implement Phase 2
8. ⏰ User testing
9. ⏰ Client approval for migration
10. ⏰ Implement Phase 3

---

## References

- Client BDD Spec: `spec/features/organization/機構設定與擁有人註冊.feature`
- Current Implementation: `backend/routers/admin.py` (lines 702-800)
- Organization Model: `backend/models/organization.py`
- Teacher Model: `backend/models/user.py`
- Subscription Model: `backend/models/subscription.py`
