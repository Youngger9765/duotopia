# Login Flow Diagnosis

## Current Broken Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User enters credentials                                  │
│    Email: owner@duotopia.com                                │
│    Password: owner123                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. POST /api/auth/teacher/login                             │
│    ✅ Verifies password                                     │
│    ✅ Generates JWT token                                   │
│    ❌ DOES NOT query teacher_organizations table            │
│    ❌ DOES NOT include role in response                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Backend Response (INCOMPLETE)                            │
│    {                                                         │
│      "access_token": "...",                                 │
│      "user": {                                              │
│        "id": 6,                                             │
│        "email": "owner@duotopia.com",                       │
│        "name": "張機構",                                     │
│        ❌ MISSING: "role": "org_owner"                      │
│        ❌ MISSING: "organization_id": "22f0f71f-..."        │
│      }                                                       │
│    }                                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Frontend receives response                               │
│    ❓ Where should I redirect this user?                   │
│    ❓ Is this an org_owner or regular teacher?             │
│    ❓ Which dashboard to show?                             │
│                                                              │
│    ❌ CANNOT PROCEED - Missing role information            │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Has The Data! ✅

```
┌──────────────────────────────────────────────────────────────┐
│ teachers table                                               │
├──────────────────────────────────────────────────────────────┤
│ id: 6                                                        │
│ email: owner@duotopia.com                                    │
│ name: 張機構                                                  │
│ password_hash: $2b$12$...                                    │
└──────────────────────────────────────────────────────────────┘
                           │
                           │ (1:1 relationship)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ teacher_organizations table                                  │
├──────────────────────────────────────────────────────────────┤
│ teacher_id: 6                                                │
│ organization_id: 22f0f71f-c858-4892-b5ec-07720c5b5561        │
│ role: "org_owner"  ← THIS DATA EXISTS BUT NOT RETURNED!     │
└──────────────────────────────────────────────────────────────┘
                           │
                           │ (many:1 relationship)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ organizations table                                          │
├──────────────────────────────────────────────────────────────┤
│ id: 22f0f71f-c858-4892-b5ec-07720c5b5561                     │
│ name: 智慧教育機構                                            │
│ owner_id: 6                                                  │
└──────────────────────────────────────────────────────────────┘
```

**The role data EXISTS in the database, but the login endpoint DOES NOT query it!**

---

## Fixed Flow (What It Should Be)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User enters credentials                                  │
│    Email: owner@duotopia.com                                │
│    Password: owner123                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. POST /api/auth/teacher/login                             │
│    ✅ Verifies password                                     │
│    ✅ Generates JWT token                                   │
│    ✅ Queries teacher_organizations table  ← FIX THIS       │
│    ✅ Queries teacher_schools table (if needed)             │
│    ✅ Determines role priority                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Backend Response (COMPLETE)                              │
│    {                                                         │
│      "access_token": "...",                                 │
│      "user": {                                              │
│        "id": 6,                                             │
│        "email": "owner@duotopia.com",                       │
│        "name": "張機構",                                     │
│        ✅ "role": "org_owner",                              │
│        ✅ "organization_id": "22f0f71f-c858-...",           │
│        ✅ "school_id": null                                 │
│      }                                                       │
│    }                                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Frontend receives complete data                          │
│    ✅ user.role === "org_owner"                             │
│    ✅ Redirect to /organization/dashboard                   │
│    ✅ Show organization navigation menu                     │
│    ✅ Apply correct permissions                             │
└─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Organization Dashboard Loads                             │
│    URL: /organization/dashboard                             │
│    Nav: 學校管理 | 教師管理 | 學生管理 | 課程管理            │
│    ✅ User can manage their organization                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Role Priority Logic

```python
# Role priority (highest to lowest):
# 1. org_owner (owns an organization)
# 2. org_admin (admin in an organization)
# 3. school_admin (admin in a school)
# 4. teacher (regular teacher in a school)

if teacher_organizations record exists:
    role = teacher_org.role  # "org_owner" or "org_admin"
    organization_id = teacher_org.organization_id
    school_id = null

elif teacher_schools record exists:
    role = teacher_school.role  # "school_admin" or "teacher"
    school_id = teacher_school.school_id
    organization_id = school.organization_id  # from school record

else:
    role = "teacher"  # independent teacher (no org/school)
    organization_id = null
    school_id = null
```

---

## Impact Analysis

### What Works ✅
- Password authentication
- JWT token generation
- Basic user data retrieval

### What Doesn't Work ❌
- Role-based dashboard routing
- Organization management features
- School management features
- Role-based navigation menus
- Permission enforcement on frontend
- QA testing for Issue #112

### Blocking Issues
- Frontend cannot determine user role
- Cannot redirect to correct dashboard
- Cannot show appropriate navigation
- Organization hierarchy features are unusable

---

## Fix Required

**File:** `/Users/young/project/duotopia/backend/routers/auth.py`
**Lines:** 104-115 (teacher_login function return statement)
**Action:** Add role query and include role/organization_id/school_id in response

**See:** `/Users/young/project/duotopia/frontend/URGENT-BACKEND-FIX-NEEDED.md` for detailed implementation
