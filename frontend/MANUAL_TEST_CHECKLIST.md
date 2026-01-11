# Organization UI - Manual Test Checklist
**DO THIS NOW**: Manual browser testing to verify org_owner login flow

---

## 🎯 Quick Start

### Prerequisites
```bash
# Verify services are running
curl http://localhost:8000/health    # Backend health check
curl http://localhost:5173           # Frontend dev server

# Both should respond with 200 OK
```

---

## ✅ Test 1: org_owner Login & Redirect

### Steps
1. Open browser: http://localhost:5173/teacher/login
2. Fill form:
   - Email: `owner@duotopia.com`
   - Password: `owner123`
3. Click "Login" button
4. **OBSERVE**: What happens?

### Expected Result ✅
- Page redirects to `/organization/dashboard`
- URL shows: `http://localhost:5173/organization/dashboard`
- Page title contains: "組織" or "Organization"
- Sidebar shows:
  - 組織架構 (Organization Structure)
  - 學校管理 (Schools)
  - 教師管理 (Teachers)

### If This Happens ❌
**Symptom**: Stays at `/teacher/login` with error "Login failed, please check your credentials"

**Diagnosis**:
- Open Browser DevTools (F12)
- Go to Network tab
- Retry login
- Look for:
  - POST request to `/api/auth/teacher/login`
  - Response status code
  - Response body

**Possible Issues**:
1. `VITE_API_URL` environment variable wrong
2. CORS blocking request
3. Frontend validation rejecting input
4. Backend not receiving correct payload

**Next Step**: Report findings with screenshots

---

## ✅ Test 2: Organization Dashboard Features

### Steps (after successful login)
1. Verify you're at `/organization/dashboard`
2. Look for organization tree structure
3. Try expanding/collapsing nodes
4. Click sidebar links:
   - 學校管理 (Schools)
   - 教師管理 (Teachers)

### Expected Results ✅
- Organization tree displays with org/school/class nodes
- Nodes can expand/collapse
- Clicking "學校管理" → navigates to `/organization/schools`
- Clicking "教師管理" → navigates to `/organization/teachers`
- Pages load without errors

### Screenshots to Take 📸
- Organization Dashboard main view
- Schools page (`/organization/schools`)
- Teachers page (`/organization/teachers`)
- Organization tree expanded state

---

## ✅ Test 3: Pure Teacher Login & Permissions

### Steps
1. Logout from owner account
2. Login with:
   - Email: `orgteacher@duotopia.com`
   - Password: `orgteacher123`
3. **OBSERVE**: Where does it redirect?

### Expected Result ✅
- Redirects to `/teacher/dashboard` (NOT /organization)
- Sidebar does NOT show:
  - 組織架構
  - 學校管理
  - 教師管理
- Shows regular teacher menu instead

### Permission Boundary Test
4. Try navigating to: `http://localhost:5173/organization/dashboard`
5. Try navigating to: `http://localhost:5173/organization/schools`

### Expected Result ✅
- Should be redirected back to `/teacher/dashboard`
- OR shows permission denied error
- Should NOT be able to access organization pages

---

## ✅ Test 4: Cross-Role Switching

### Steps
1. Login as org_owner (owner@duotopia.com)
2. Verify redirect to `/organization/dashboard` ✅
3. Logout
4. Login as teacher (orgteacher@duotopia.com)
5. Verify redirect to `/teacher/dashboard` ✅
6. Logout
7. Login as org_owner again
8. Verify redirect to `/organization/dashboard` ✅

### Expected Result ✅
- Role-based redirects work consistently
- No cross-contamination between sessions
- Sidebar updates correctly for each role

---

## 🐛 Debugging Checklist

If anything fails, check:

### 1. Environment Variables
```bash
# Frontend .env file
cd /Users/young/project/duotopia/frontend
cat .env | grep VITE_API_URL

# Should be:
VITE_API_URL=http://localhost:8000
```

### 2. API Connectivity
```bash
# Test login API directly
curl -X POST http://localhost:8000/api/auth/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@duotopia.com","password":"owner123"}'

# Should return:
# {"access_token":"...","token_type":"bearer","user":{...}}
```

### 3. Browser DevTools
- **Console Tab**: Look for JavaScript errors
- **Network Tab**: Check API calls and responses
- **Application Tab**: Check localStorage for auth tokens

### 4. Backend Logs
```bash
# Check backend terminal for errors
# Look for POST /api/auth/teacher/login requests
```

---

## 📊 Results Template

Copy this template and fill in your results:

```markdown
## Manual Test Results

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Browser**: [Chrome/Firefox/Safari] [Version]

### Test 1: org_owner Login
- [ ] ✅ Redirected to /organization/dashboard
- [ ] ❌ Failed with error: _______________
- Screenshot: [attach if failed]

### Test 2: Organization Dashboard
- [ ] ✅ Organization tree displays
- [ ] ✅ Can navigate to Schools page
- [ ] ✅ Can navigate to Teachers page
- [ ] ❌ Issues: _______________

### Test 3: Pure Teacher Login
- [ ] ✅ Redirected to /teacher/dashboard
- [ ] ✅ Cannot access organization pages
- [ ] ❌ Issues: _______________

### Test 4: Cross-Role Switching
- [ ] ✅ Role-based redirects work consistently
- [ ] ❌ Issues: _______________

### Overall Status
- [ ] ✅ All tests passed - Frontend ready for production
- [ ] ⚠️ Minor issues found (describe): _______________
- [ ] ❌ Critical issues found (describe): _______________
```

---

## 🎯 Success Criteria

**All Green** means:
- ✅ org_owner → /organization/dashboard
- ✅ Pure teacher → /teacher/dashboard
- ✅ Organization features accessible to org_owner
- ✅ Organization features blocked for pure teacher
- ✅ Role switching works correctly

If all criteria met → **E2E test failure is in test setup, not application**

---

## 📞 If You Find Issues

### Report Format
```markdown
**Issue**: [Brief description]
**Steps**: [How to reproduce]
**Expected**: [What should happen]
**Actual**: [What actually happened]
**Screenshot**: [Attach image]
**Browser Console**: [Paste errors]
**Network Tab**: [Show failed requests]
```

### Common Fixes
1. **VITE_API_URL wrong** → Update `.env` file
2. **Backend not running** → Start with `cd backend && uvicorn main:app --reload`
3. **Frontend not running** → Start with `npm run dev`
4. **Cache issues** → Hard refresh (Ctrl+Shift+R)
5. **LocalStorage issues** → Clear and re-login

---

**START TESTING NOW**: http://localhost:5173/teacher/login

**Estimated Time**: 10 minutes

**Priority**: HIGH - Blocking E2E test resolution
