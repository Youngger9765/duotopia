# Org Owner Login Test Report

**Test Date:** 2026-01-01
**Environment:** Local Development (localhost)
**Branch:** `feat/issue-112-org-hierarchy`

---

## ✅ Test Results Summary

### Backend API Test

**Endpoint:** `POST /api/auth/teacher/login`
**Test Account:** owner@duotopia.com / owner123

#### ✅ Login API Works
```bash
curl -X POST 'http://localhost:8000/api/auth/teacher/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@duotopia.com","password":"owner123"}'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 6,
    "email": "owner@duotopia.com",
    "name": "張機構",
    "phone": null,
    "is_demo": false,
    "is_admin": false
  }
}
```

---

## 🔴 CRITICAL ISSUES FOUND

### Issue #1: Missing Role Information in Login Response

**Problem:**
The login response **does NOT include** the following required fields:
- ❌ `role` (e.g., "org_owner", "school_admin", "teacher")
- ❌ `organization_id`
- ❌ `school_id`

**Impact:**
Frontend **CANNOT** determine:
1. Where to redirect user after login
2. What permissions the user has
3. What navigation items to show

**Current Code Location:**
`/Users/young/project/duotopia/backend/routers/auth.py` (lines 104-115)

**Current Implementation:**
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

**Required Implementation:**
```python
# Query teacher_organizations table to get role
teacher_org = db.query(TeacherOrganization).filter(
    TeacherOrganization.teacher_id == teacher.id
).first()

# Query teacher_schools table to get school role
teacher_school = db.query(TeacherSchool).filter(
    TeacherSchool.teacher_id == teacher.id
).first()

# Determine role priority: org_owner > org_admin > school_admin > teacher
role = "teacher"  # default
organization_id = None
school_id = None

if teacher_org:
    role = teacher_org.role  # "org_owner" or "org_admin"
    organization_id = str(teacher_org.organization_id)
elif teacher_school:
    role = teacher_school.role  # "school_admin" or "teacher"
    school_id = str(teacher_school.school_id)
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
        "role": role,  # ← ADD THIS
        "organization_id": organization_id,  # ← ADD THIS
        "school_id": school_id,  # ← ADD THIS
    },
}
```

---

### Issue #2: Frontend Routing Logic Missing

**Problem:**
Even if backend returns `role`, frontend needs logic to redirect based on role:

```typescript
// src/pages/TeacherLoginPage.tsx or similar
const handleLoginSuccess = (response: LoginResponse) => {
  const { user } = response;

  // Store token
  localStorage.setItem('token', response.access_token);
  localStorage.setItem('user', JSON.stringify(user));

  // Redirect based on role
  if (user.role === 'org_owner' || user.role === 'org_admin') {
    navigate('/organization/dashboard');
  } else if (user.role === 'school_admin') {
    navigate('/school/dashboard');
  } else {
    navigate('/teacher/dashboard'); // regular teacher
  }
};
```

**Current Frontend State:**
❓ Unknown - needs investigation

---

## 📋 Required Changes

### Backend Changes

1. **Update `/api/auth/teacher/login` endpoint** (`routers/auth.py`)
   - Query `teacher_organizations` table
   - Query `teacher_schools` table
   - Determine user's role
   - Include `role`, `organization_id`, `school_id` in response

2. **Update `TokenResponse` model** (if using Pydantic)
   ```python
   class TokenResponse(BaseModel):
       access_token: str
       token_type: str
       user: dict  # Should be a proper UserResponse model
   ```

3. **Create proper response model:**
   ```python
   class UserResponse(BaseModel):
       id: int
       email: str
       name: str
       phone: Optional[str]
       is_demo: bool
       is_admin: bool
       role: str  # "org_owner", "org_admin", "school_admin", "teacher"
       organization_id: Optional[str]
       school_id: Optional[str]
   ```

### Frontend Changes

1. **Update TypeScript types** (`src/types/auth.ts` or similar)
   ```typescript
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

2. **Add role-based routing** in login page
3. **Add role-based navigation** in main layout
4. **Create organization dashboard** (`/organization/dashboard`)
5. **Create school dashboard** (`/school/dashboard`)

---

## 🧪 Manual Browser Testing (BLOCKED)

**Status:** ❌ Cannot proceed until backend issue is fixed

**Reason:**
Without `role` in the login response, frontend cannot determine where to redirect the user.

**Next Steps:**
1. Fix backend login endpoint to include role information
2. Fix frontend routing logic
3. Re-run browser test

---

## 🔧 Recommended Fix Priority

### Priority 1: Backend Login Response (CRITICAL)
- [ ] Add role query to login endpoint
- [ ] Return `role`, `organization_id`, `school_id` in user object
- [ ] Test with curl/Postman

### Priority 2: Frontend Routing
- [ ] Update TypeScript types
- [ ] Add role-based redirect logic
- [ ] Create organization/school dashboards

### Priority 3: Manual Browser Test
- [ ] Test org_owner login → should redirect to `/organization/dashboard`
- [ ] Test school_admin login → should redirect to `/school/dashboard`
- [ ] Test regular teacher login → should redirect to `/teacher/dashboard`

---

## 📊 Test Data

### Test Accounts Needed

| Email | Password | Role | Organization | School |
|-------|----------|------|--------------|--------|
| owner@duotopia.com | owner123 | org_owner | 測試機構 | - |
| admin@school1.com | admin123 | school_admin | 測試機構 | 學校A |
| teacher@school1.com | teacher123 | teacher | 測試機構 | 學校A |

**Verification Query:**
```sql
-- Check teacher's role in organization
SELECT t.email, t.name, to2.role, o.name as org_name
FROM teachers t
JOIN teacher_organizations to2 ON t.id = to2.teacher_id
JOIN organizations o ON to2.organization_id = o.id
WHERE t.email = 'owner@duotopia.com';

-- Check teacher's role in school
SELECT t.email, t.name, ts.role, s.name as school_name
FROM teachers t
JOIN teacher_schools ts ON t.id = ts.teacher_id
JOIN schools s ON ts.school_id = s.id
WHERE t.email = 'owner@duotopia.com';
```

---

## 🎯 Success Criteria (Not Yet Met)

When all issues are fixed, the following must be TRUE:

### Backend API
- [x] Login returns 200 OK ✅
- [ ] Login response includes `role` field ❌
- [ ] Login response includes `organization_id` (if applicable) ❌
- [ ] Login response includes `school_id` (if applicable) ❌

### Frontend Browser Test
- [ ] org_owner login redirects to `/organization/dashboard` ❌ (blocked)
- [ ] Organization navigation is visible ❌ (blocked)
- [ ] Can navigate to Schools page ❌ (blocked)
- [ ] Can navigate to Teachers page ❌ (blocked)
- [ ] No console errors ❓ (not tested)

---

## 📝 Notes

1. **Backend is running:** ✅ Port 8000 (2 processes)
2. **Frontend is running:** ✅ Port 5173 (2 processes)
3. **Login API works:** ✅ Returns 200 with token
4. **Role detection:** ❌ MISSING - This is the blocker

**Next Action Required:**
Fix the backend login endpoint to include role information before proceeding with frontend tests.
