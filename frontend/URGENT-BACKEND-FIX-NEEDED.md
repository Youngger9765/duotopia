# 🚨 URGENT: Backend Login Endpoint Missing Role Information

## Issue Summary

**Status:** 🔴 CRITICAL BUG - Login flow broken for org_owner users
**Affected:** All organization/school hierarchy features (Issue #112)
**Impact:** Frontend cannot redirect users to correct dashboard

---

## Problem

The `/api/auth/teacher/login` endpoint **DOES NOT** return the user's role information, making it impossible for the frontend to:
1. Redirect users to the correct dashboard
2. Show appropriate navigation menus
3. Enforce role-based access control

---

## Evidence

### Database Contains Correct Data ✅

```
Teacher ID: 6
Teacher Name: 張機構
Teacher Email: owner@duotopia.com

TeacherOrganization:
  Role: org_owner
  Organization ID: 22f0f71f-c858-4892-b5ec-07720c5b5561
  Organization Name: 智慧教育機構
```

### Login API Returns Incomplete Data ❌

**Current Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 6,
    "email": "owner@duotopia.com",
    "name": "張機構",
    "phone": null,
    "is_demo": false,
    "is_admin": false
    // ❌ MISSING: role
    // ❌ MISSING: organization_id
    // ❌ MISSING: school_id
  }
}
```

**Required Response:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 6,
    "email": "owner@duotopia.com",
    "name": "張機構",
    "phone": null,
    "is_demo": false,
    "is_admin": false,
    "role": "org_owner",  // ← ADD THIS
    "organization_id": "22f0f71f-c858-4892-b5ec-07720c5b5561",  // ← ADD THIS
    "school_id": null  // ← ADD THIS
  }
}
```

---

## Required Fix

### File: `/Users/young/project/duotopia/backend/routers/auth.py`
### Function: `teacher_login()` (lines 62-115)

**Current Code (lines 104-115):**
```python
return {
    "access_token": access_token,
    "token_type": "bearer",
    "user": {
        "id": teacher.id,
        "email": teacher.email,
        "name": teacher.name,
        "phone": teacher.phone,
        "is_demo": teacher.is_demo,
        "is_admin": teacher.is_admin,
    },
}
```

**Fixed Code:**
```python
# Query role information
from models import TeacherOrganization, TeacherSchool, School

teacher_org = db.query(TeacherOrganization).filter(
    TeacherOrganization.teacher_id == teacher.id
).first()

teacher_school = db.query(TeacherSchool).filter(
    TeacherSchool.teacher_id == teacher.id
).first()

# Determine role (priority: org_owner > org_admin > school_admin > teacher)
role = "teacher"  # default
organization_id = None
school_id = None

if teacher_org:
    role = teacher_org.role  # "org_owner" or "org_admin"
    organization_id = str(teacher_org.organization_id)
elif teacher_school:
    role = teacher_school.role  # "school_admin" or "teacher"
    school_id = teacher_school.school_id
    # Get school's organization_id
    school = db.query(School).filter(School.id == teacher_school.school_id).first()
    if school:
        organization_id = str(school.organization_id)

return {
    "access_token": access_token,
    "token_type": "bearer",
    "user": {
        "id": teacher.id,
        "email": teacher.email,
        "name": teacher.name,
        "phone": teacher.phone,
        "is_demo": teacher.is_demo,
        "is_admin": teacher.is_admin,
        "role": role,  # ← NEW
        "organization_id": organization_id,  # ← NEW
        "school_id": school_id,  # ← NEW
    },
}
```

---

## Verification Steps

After applying the fix, verify with:

```bash
# Test login API
curl -X POST 'http://localhost:8000/api/auth/teacher/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@duotopia.com","password":"owner123"}' \
  | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```

**Expected Output:**
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": 6,
    "email": "owner@duotopia.com",
    "name": "張機構",
    "phone": null,
    "is_demo": false,
    "is_admin": false,
    "role": "org_owner",  // ✅ MUST BE PRESENT
    "organization_id": "22f0f71f-c858-4892-b5ec-07720c5b5561",  // ✅ MUST BE PRESENT
    "school_id": null  // ✅ MUST BE PRESENT
  }
}
```

---

## Frontend Impact

Once backend is fixed, frontend needs to:

1. **Update TypeScript types:**
```typescript
// src/types/auth.ts
export interface User {
  id: number;
  email: string;
  name: string;
  phone: string | null;
  is_demo: boolean;
  is_admin: boolean;
  role: 'org_owner' | 'org_admin' | 'school_admin' | 'teacher';
  organization_id: string | null;
  school_id: string | null;
}
```

2. **Add role-based routing:**
```typescript
// After login success
if (user.role === 'org_owner' || user.role === 'org_admin') {
  navigate('/organization/dashboard');
} else if (user.role === 'school_admin') {
  navigate('/school/dashboard');
} else {
  navigate('/teacher/dashboard');
}
```

---

## Priority

**CRITICAL** - This blocks all org hierarchy features from working.

Without this fix:
- ❌ org_owner cannot access organization dashboard
- ❌ Frontend cannot show correct navigation
- ❌ Role-based access control doesn't work
- ❌ QA testing cannot proceed

---

## Related Files

- Backend: `/Users/young/project/duotopia/backend/routers/auth.py` (lines 62-115)
- Models: `/Users/young/project/duotopia/backend/models/organization.py` (TeacherOrganization)
- Models: `/Users/young/project/duotopia/backend/models/organization.py` (TeacherSchool)
- Test Report: `/Users/young/project/duotopia/frontend/org-owner-login-test-report.md`

---

## Test Account

**Email:** owner@duotopia.com
**Password:** owner123
**Expected Role:** org_owner
**Expected Organization:** 智慧教育機構 (22f0f71f-c858-4892-b5ec-07720c5b5561)
