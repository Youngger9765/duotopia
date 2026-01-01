# Org Owner Login Test Script

## Test Environment
- **Frontend URL**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Test User**: owner@duotopia.com / owner123

## Manual Test Steps

### Step 1: Navigate to Login Page
1. Open browser to: `http://localhost:5173/teacher/login`
2. **Expected**: Login form displays with email and password fields

### Step 2: Fill Login Form
1. Enter email: `owner@duotopia.com`
2. Enter password: `owner123`
3. Click "登入" button

### Step 3: Verify Login Success
**Expected Behavior**:
- ✅ HTTP POST to `/api/teacher/login` returns 200
- ✅ Response contains `access_token`
- ✅ Response contains user data with `role: "org_owner"`
- ✅ Browser redirects to `/organization/dashboard`
- ✅ Navigation bar shows organization management options

### Step 4: Verify Organization Dashboard
**Expected URL**: `http://localhost:5173/organization/dashboard`

**Expected Content**:
- Page title: "機構管理後台"
- Navigation items:
  - 學校管理 (Schools)
  - 教師管理 (Teachers)
  - 學生管理 (Students)
  - 課程管理 (Courses)
- Welcome message with organization name

### Step 5: Test Navigation - Schools
1. Click "學校管理" link
2. **Expected URL**: `http://localhost:5173/organization/schools`
3. **Expected Content**: List of schools under the organization

### Step 6: Test Navigation - Teachers
1. Click "教師管理" link
2. **Expected URL**: `http://localhost:5173/organization/teachers`
3. **Expected Content**: List of teachers in the organization

### Step 7: Verify Access Control
**What org_owner SHOULD see**:
- ✅ Organization dashboard
- ✅ School management
- ✅ Teacher management across all schools
- ✅ Student management across all schools

**What org_owner SHOULD NOT see**:
- ❌ Individual classroom management (that's for teachers)
- ❌ Teacher's personal class lists

## Automated Test (Playwright)

Run the automated test:
```bash
cd frontend
npm run test:e2e -- --grep "org_owner login"
```

## Backend API Verification

Check the user's permissions:
```bash
curl -X POST http://localhost:8000/api/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@duotopia.com","password":"owner123"}' \
  | jq '.'
```

Expected response structure:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "owner@duotopia.com",
    "name": "Organization Owner",
    "role": "org_owner",
    "organization_id": 1,
    "school_id": null
  }
}
```

## Troubleshooting

### Issue: Login fails with 401
**Check**:
1. Is the backend running? `lsof -ti:8000`
2. Does the user exist? Check database
3. Is the password correct?

### Issue: Redirects to wrong page
**Check**:
1. Frontend routing configuration in `src/App.tsx`
2. `ProtectedRoute` logic for role-based routing
3. Browser console for errors

### Issue: Navigation doesn't work
**Check**:
1. React Router configuration
2. Navigation component permissions
3. Browser console for JavaScript errors

## Success Criteria

All of these must be TRUE:
- [x] Login succeeds with 200 response
- [x] Token is stored in localStorage
- [x] User is redirected to `/organization/dashboard`
- [x] Organization navigation is visible
- [x] Can navigate to Schools page
- [x] Can navigate to Teachers page
- [x] No console errors
- [x] No network errors in DevTools

## Current Status (Manual Test Required)

**Please execute the manual test steps above and report results.**

Use browser DevTools to capture:
1. Network tab - Login request/response
2. Console tab - Any errors
3. Application tab - localStorage content
4. Screenshots of each page
