# Manual UI Testing Checklist
## Organization Portal Separation - Phase 6-7

**Date:** 2026-01-01
**Test Environment:** http://localhost:5173
**Backend:** http://localhost:8000
**Status:** ✅ Backend APIs verified - Ready for UI testing

---

## Test Accounts Reference

| Role | Email | Password | Name | Expected Portal |
|------|-------|----------|------|----------------|
| org_owner | owner@duotopia.com | owner123 | 張機構 | /organization/dashboard |
| org_admin | orgadmin@duotopia.com | orgadmin123 | 李管理 | /organization/dashboard |
| school_admin | schooladmin@duotopia.com | schooladmin123 | 王校長 | /organization/dashboard (limited) |
| teacher | orgteacher@duotopia.com | orgteacher123 | 陳老師 | /teacher/dashboard |

---

## Pre-Testing Setup

- [ ] Backend running on port 8000 (verify: `lsof -i:8000`)
- [ ] Frontend running on port 5173 (verify: `lsof -i:5173`)
- [ ] Chrome browser opened
- [ ] DevTools opened (F12 or Cmd+Option+I)
- [ ] Network tab visible
- [ ] Console tab checked for errors
- [ ] Screenshot tool ready (Cmd+Shift+5 on Mac)

---

## Test Execution Guide

### Session 1: org_owner Role Testing (30 minutes)

#### Step 1: Login and Auto-Redirect
- [ ] Open http://localhost:5173 in incognito window
- [ ] Enter credentials: owner@duotopia.com / owner123
- [ ] Click "Login" button
- [ ] **VERIFY:**
  - [ ] No console errors
  - [ ] Redirects to `/organization/dashboard` (NOT `/teacher/dashboard`)
  - [ ] URL is exactly `http://localhost:5173/organization/dashboard`
- [ ] **SCREENSHOT:** `01_org_owner_login_redirect.png`

#### Step 2: Organization Dashboard Layout
- [ ] **VERIFY Layout:**
  - [ ] OrganizationLayout is loaded
  - [ ] Left sidebar is visible
  - [ ] Organization tree is displayed
  - [ ] Main content area shows dashboard
  - [ ] Top navigation bar present
  - [ ] User profile/logout button visible
- [ ] **VERIFY Organization Tree:**
  - [ ] Shows organization name (e.g., "智慧教育機構")
  - [ ] Shows expand/collapse icons
  - [ ] Shows schools under organization
  - [ ] Tree has proper indentation
- [ ] **SCREENSHOT:** `02_org_owner_dashboard_full.png`

#### Step 3: Organization Tree Interactions
- [ ] Click expand icon on organization node
  - [ ] **VERIFY:** Schools list appears
  - [ ] **VERIFY:** Animation is smooth
- [ ] Click collapse icon
  - [ ] **VERIFY:** Schools list hides
- [ ] Click on organization name
  - [ ] **VERIFY:** Right panel updates (if applicable)
  - [ ] **VERIFY:** Visual selection indicator appears
- [ ] Click on school name
  - [ ] **VERIFY:** Right panel shows school details
  - [ ] **VERIFY:** Selection indicator moves to school
- [ ] **SCREENSHOT:** `03_org_tree_expanded_selected.png`

#### Step 4: Navigate to Schools Management
- [ ] Click "Schools" in left sidebar
  - [ ] **VERIFY:** URL changes to `/organization/schools`
  - [ ] **VERIFY:** Schools list page loads
  - [ ] **VERIFY:** Breadcrumbs update correctly
- [ ] **VERIFY Schools List Page:**
  - [ ] Table/list displays schools correctly
  - [ ] Columns: Name, Display Name, Address, Contact Phone, Actions
  - [ ] "Add School" button is visible
  - [ ] Edit and Delete buttons visible for each school
- [ ] **SCREENSHOT:** `04_schools_management_page.png`

#### Step 5: Create School (CRUD - Create)
- [ ] Click "Add School" button
  - [ ] **VERIFY:** Dialog/modal opens
  - [ ] **VERIFY:** Form fields are present:
    - [ ] Name (required)
    - [ ] Display Name
    - [ ] Address
    - [ ] Contact Phone
  - [ ] **SCREENSHOT:** `05_create_school_dialog.png`
- [ ] Fill in test data:
  - Name: "QA測試分校"
  - Display Name: "QA測試分校 (台北)"
  - Address: "台北市信義區測試路123號"
  - Contact Phone: "02-9999-8888"
- [ ] Click "Submit" or "Create"
  - [ ] **VERIFY:** Loading indicator appears
  - [ ] **VERIFY:** Success toast message appears
  - [ ] **VERIFY:** Dialog closes
  - [ ] **VERIFY:** New school appears in list
  - [ ] **VERIFY:** Network tab shows POST request with 201 status
- [ ] **SCREENSHOT:** `06_school_created_success.png`

#### Step 6: Edit School (CRUD - Update)
- [ ] Click "Edit" button on the newly created school
  - [ ] **VERIFY:** Edit dialog opens
  - [ ] **VERIFY:** Form is pre-filled with existing data
  - [ ] **SCREENSHOT:** `07_edit_school_dialog.png`
- [ ] Modify display name: "QA測試分校 (台北) - Updated"
- [ ] Click "Save" or "Update"
  - [ ] **VERIFY:** Success toast appears
  - [ ] **VERIFY:** Dialog closes
  - [ ] **VERIFY:** Changes reflected in list
- [ ] **SCREENSHOT:** `08_school_updated_success.png`

#### Step 7: Delete School (CRUD - Delete) [OPTIONAL - Use with caution]
- [ ] Click "Delete" button on a test school
  - [ ] **VERIFY:** Confirmation dialog appears
  - [ ] **VERIFY:** Warning message is clear
  - [ ] **SCREENSHOT:** `09_delete_school_confirmation.png`
- [ ] Click "Cancel"
  - [ ] **VERIFY:** Dialog closes, no deletion occurs
- [ ] Click "Delete" again, then "Confirm"
  - [ ] **VERIFY:** Success toast appears
  - [ ] **VERIFY:** School removed from list
  - [ ] **SCREENSHOT:** `10_school_deleted_success.png`

#### Step 8: Navigate to Teachers Management
- [ ] Click "Teachers" in left sidebar
  - [ ] **VERIFY:** URL changes to `/organization/teachers`
  - [ ] **VERIFY:** Teachers list page loads
- [ ] **VERIFY Teachers Page:**
  - [ ] Teachers list displayed
  - [ ] Shows columns: Name, Email, Roles, Organization, School
  - [ ] Role badges are color-coded and clear
  - [ ] Statistics section shows correct counts
  - [ ] **VERIFY Statistics:**
    - [ ] Total teachers count
    - [ ] org_owner count
    - [ ] org_admin count
    - [ ] school_admin count
    - [ ] teacher count
- [ ] **SCREENSHOT:** `11_teachers_management_page.png`

#### Step 9: Navigation and Breadcrumbs
- [ ] Navigate between pages: Dashboard → Schools → Teachers → Dashboard
  - [ ] **VERIFY:** Each navigation is smooth
  - [ ] **VERIFY:** Breadcrumbs update correctly
  - [ ] **VERIFY:** Sidebar highlights active page
  - [ ] **VERIFY:** No console errors during navigation
- [ ] **SCREENSHOT:** `12_navigation_breadcrumbs.png`

#### Step 10: Access Teacher Portal (Dual Role Test)
- [ ] Manually navigate to `/teacher/dashboard`
  - [ ] **VERIFY:** Page loads (org_owner may also be a teacher)
  - [ ] **VERIFY:** OR shows option to "Switch to Organization Portal"
  - [ ] **VERIFY:** No errors
- [ ] Check sidebar
  - [ ] **VERIFY:** If has teaching role: shows teacher menu items
  - [ ] **VERIFY:** Shows link/button to switch back to organization portal
- [ ] **SCREENSHOT:** `13_org_owner_teacher_portal.png`

---

### Session 2: org_admin Role Testing (20 minutes)

#### Step 1: Logout and Login
- [ ] Logout from org_owner account
- [ ] Login as orgadmin@duotopia.com / orgadmin123
- [ ] **VERIFY:** Redirects to `/organization/dashboard`
- [ ] **SCREENSHOT:** `14_org_admin_dashboard.png`

#### Step 2: Verify Permissions
- [ ] **VERIFY Can Access:**
  - [ ] Organization dashboard
  - [ ] Schools list
  - [ ] Teachers list
- [ ] **VERIFY Limitations:**
  - [ ] Can only see/edit organizations they admin
  - [ ] Cannot delete organizations they don't own
- [ ] Try to edit an organization they manage
  - [ ] **VERIFY:** Edit works
- [ ] Try to edit an organization they don't manage (if multiple exist)
  - [ ] **VERIFY:** Either hidden OR edit button disabled OR 403 error
- [ ] **SCREENSHOT:** `15_org_admin_permissions.png`

---

### Session 3: school_admin Role Testing (15 minutes)

#### Step 1: Logout and Login
- [ ] Logout from org_admin account
- [ ] Login as schooladmin@duotopia.com / schooladmin123
- [ ] **VERIFY:** Redirects to `/organization/dashboard` OR `/teacher/dashboard`
  - Note: Behavior depends on implementation
- [ ] **SCREENSHOT:** `16_school_admin_dashboard.png`

#### Step 2: Verify Limited Access
- [ ] **VERIFY Can See:**
  - [ ] Only their assigned school(s)
  - [ ] Teachers in their school
- [ ] **VERIFY CANNOT:**
  - [ ] Create/edit organizations
  - [ ] Create/edit schools
  - [ ] Access other schools' data
- [ ] Try to navigate to `/organization/schools`
  - [ ] **VERIFY:** Either shows only their school OR access denied
- [ ] **SCREENSHOT:** `17_school_admin_limited_view.png`

---

### Session 4: Pure Teacher Role Testing (20 minutes)

#### Step 1: Logout and Login
- [ ] Logout from school_admin account
- [ ] Login as orgteacher@duotopia.com / orgteacher123
- [ ] **VERIFY:** Redirects to `/teacher/dashboard` (NOT organization portal)
- [ ] **SCREENSHOT:** `18_teacher_dashboard.png`

#### Step 2: Verify Clean Teacher Dashboard
- [ ] **VERIFY Dashboard:**
  - [ ] Shows ONLY teaching-related content
  - [ ] Statistics are about classes, students, assignments
  - [ ] NO organization management sections
  - [ ] NO "Organizations" statistics
- [ ] **SCREENSHOT:** `19_teacher_dashboard_clean.png`

#### Step 3: Verify Sidebar Has No Org Management
- [ ] Check left sidebar
  - [ ] **VERIFY:** Shows only:
    - [ ] Dashboard
    - [ ] My Classes
    - [ ] Students
    - [ ] Programs (if applicable)
    - [ ] Profile
    - [ ] Subscription
  - [ ] **VERIFY:** Does NOT show:
    - [ ] Organizations
    - [ ] Schools (management)
    - [ ] Teachers (management)
- [ ] **SCREENSHOT:** `20_teacher_sidebar_no_org.png`

#### Step 4: Verify Access Denied to Organization Portal
- [ ] Manually navigate to `/organization/dashboard`
  - [ ] **VERIFY:** Redirected to `/teacher/dashboard`
  - [ ] **VERIFY:** OR shows 403 Forbidden message
  - [ ] **VERIFY:** Cannot access organization features
- [ ] **SCREENSHOT:** `21_teacher_blocked_from_org_portal.png`
- [ ] Try `/organization/schools`
  - [ ] **VERIFY:** Blocked or redirected
- [ ] Try `/organization/teachers`
  - [ ] **VERIFY:** Blocked or redirected

---

### Session 5: Permission Boundary Testing (15 minutes)

#### Test 1: Unauthenticated Access
- [ ] Open new incognito window
- [ ] Navigate to `/organization/dashboard`
  - [ ] **VERIFY:** Redirects to `/teacher/login`
- [ ] Navigate to `/teacher/dashboard`
  - [ ] **VERIFY:** Redirects to `/teacher/login`
- [ ] **SCREENSHOT:** `22_unauthenticated_redirect.png`

#### Test 2: Cross-Portal Access
- [ ] Login as teacher (orgteacher@duotopia.com)
- [ ] Try accessing organization routes directly:
  - `/organization/dashboard`
  - `/organization/schools`
  - `/organization/teachers`
- [ ] **VERIFY:** All blocked or redirected
- [ ] **SCREENSHOT:** `23_teacher_cross_portal_blocked.png`

---

### Session 6: UI/UX Quality Checks (20 minutes)

#### Visual Design
- [ ] **Colors and Theming:**
  - [ ] Consistent color scheme
  - [ ] Proper contrast (text readable)
  - [ ] Brand colors used correctly
- [ ] **Typography:**
  - [ ] Fonts are consistent
  - [ ] Text sizes appropriate
  - [ ] Headers clearly distinguishable
- [ ] **Spacing:**
  - [ ] Proper padding and margins
  - [ ] Elements not cramped
  - [ ] White space used effectively
- [ ] **SCREENSHOT:** `24_ui_design_quality.png`

#### Interactive Elements
- [ ] **Buttons:**
  - [ ] Hover states work
  - [ ] Active states visible
  - [ ] Disabled states clear
  - [ ] Icons aligned properly
- [ ] **Forms:**
  - [ ] Input fields have proper focus states
  - [ ] Validation messages are clear
  - [ ] Error states are visible
  - [ ] Success states are visible
- [ ] **SCREENSHOT:** `25_interactive_elements.png`

#### Loading and Error States
- [ ] **Loading States:**
  - [ ] Spinners/skeletons appear during data load
  - [ ] Loading text is clear
  - [ ] No layout shift during load
- [ ] **Error States:**
  - [ ] Error messages are user-friendly
  - [ ] Error icons/colors are clear
  - [ ] Retry options available (if applicable)
- [ ] **Empty States:**
  - [ ] Empty list shows helpful message
  - [ ] Call-to-action button present (e.g., "Add School")
  - [ ] Icon/illustration present
- [ ] **SCREENSHOT:** `26_loading_error_empty_states.png`

#### Responsive Design (Optional)
- [ ] Resize browser to tablet size (768px)
  - [ ] **VERIFY:** Sidebar collapses to hamburger menu
  - [ ] **VERIFY:** Tables scroll horizontally or adapt
  - [ ] **VERIFY:** No overflow issues
- [ ] **SCREENSHOT:** `27_responsive_tablet.png`

---

### Session 7: Performance Testing (15 minutes)

#### Page Load Speed
- [ ] Clear browser cache (Cmd+Shift+Delete)
- [ ] Open DevTools → Network tab
- [ ] Navigate to `/organization/dashboard`
- [ ] **RECORD:**
  - [ ] Time to First Byte (TTFB): __________ ms
  - [ ] First Contentful Paint (FCP): __________ ms
  - [ ] Time to Interactive (TTI): __________ ms
  - [ ] **TARGET:** TTI < 2000ms
- [ ] **SCREENSHOT:** `28_network_performance.png`

#### API Response Times
- [ ] Check Network tab for API calls:
  - [ ] GET /api/organizations - Response time: __________ ms (Target: <500ms)
  - [ ] GET /api/schools - Response time: __________ ms (Target: <500ms)
  - [ ] GET /api/organizations/{id}/teachers - Response time: __________ ms (Target: <500ms)
- [ ] **SCREENSHOT:** `29_api_response_times.png`

#### Organization Tree Rendering
- [ ] Expand organization tree
- [ ] **OBSERVE:** Rendering speed
  - [ ] **TARGET:** < 500ms
  - [ ] Should be instantaneous or near-instantaneous
- [ ] Collapse and expand multiple times
  - [ ] **VERIFY:** No lag or janky animations

#### Memory Usage
- [ ] Open DevTools → Performance tab
- [ ] Take heap snapshot
- [ ] Navigate through all organization pages
- [ ] Take another heap snapshot
- [ ] **VERIFY:**
  - [ ] No significant memory increase (< 10MB growth is OK)
  - [ ] No memory leaks detected
- [ ] **SCREENSHOT:** `30_memory_usage.png`

---

## Checklist Summary

### Total Checkpoints: ~120+

**Estimated Time:** 2.5 - 3 hours for complete manual testing

### Priority Levels

**P0 (Critical - Must Pass):**
- [ ] Authentication works for all roles
- [ ] Role-based redirection works correctly
- [ ] Pure teacher CANNOT access organization portal
- [ ] org_owner CAN access all organization features
- [ ] No console errors on any page
- [ ] CRUD operations work (Create, Read, Update, Delete)

**P1 (High - Should Pass):**
- [ ] Organization tree renders correctly
- [ ] Navigation and breadcrumbs work
- [ ] All forms validate properly
- [ ] Success/error toasts appear
- [ ] Page load < 2 seconds
- [ ] API responses < 500ms

**P2 (Medium - Nice to Have):**
- [ ] Responsive design works
- [ ] Animations are smooth
- [ ] Empty states are helpful
- [ ] Loading states are clear

**P3 (Low - Enhancements):**
- [ ] Keyboard navigation works
- [ ] Accessibility features present
- [ ] Dark mode (if applicable)

---

## Issue Reporting Template

When you find an issue, document it using this format:

```markdown
### Issue #N: [Brief Description]

**Severity:** Critical / High / Medium / Low
**Component:** [Page/Component Name]
**Role:** [Which role encountered this]

**Steps to Reproduce:**
1. Login as [role]
2. Navigate to [page]
3. Click [element]
4. Observe [problem]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Screenshot:** [filename.png]

**Console Errors:** [Copy any errors from console]

**Network Errors:** [Copy any failed requests]

**Browser:** Chrome [version]
**OS:** macOS [version]
```

---

## Post-Testing Actions

After completing all tests:

1. **Collect all screenshots** into a folder: `screenshots/phase6-7-testing/`
2. **Compile issues list** with severity levels
3. **Generate test report** (see INTEGRATION_TEST_EXECUTION.md)
4. **Update PRD** - Mark completed acceptance criteria
5. **Share results** with team

---

## Quick Reference Commands

```bash
# Check if servers are running
lsof -i:5173  # Frontend
lsof -i:8000  # Backend

# View backend logs
tail -f backend/logs/app.log  # If logging to file

# Clear browser data
# Chrome: Cmd+Shift+Delete → Select "Cached images and files"

# Take screenshot
# macOS: Cmd+Shift+5 → Select area or window
```

---

**Testing Status:** Ready to Execute
**Backend API Status:** ✅ All tests passed (12/12)
**UI Testing Status:** ⏳ Awaiting manual execution
**Last Updated:** 2026-01-01
