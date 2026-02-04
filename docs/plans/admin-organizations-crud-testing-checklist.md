# Admin Organization CRUD - Testing Checklist

**Feature**: Admin Organization Management (List + Update, Phase 5 of Issue #198)

**Tester**: _________
**Date**: _________
**Environment**: [ ] Local [ ] Staging [ ] Production

---

## Prerequisites

- [ ] Backend server running (`cd backend && uvicorn main:app --reload`)
- [ ] Frontend dev server running (`cd frontend && npm run dev`)
- [ ] Logged in as admin user: `owner@duotopia.com` / `owner123`

---

## Backend API Tests ✅

All backend tests pass:

```bash
cd backend
python -m pytest tests/test_admin_organizations.py -v
# Expected: 20/20 tests PASSED

python -m pytest tests/test_admin_organizations_points.py -v
# Expected: 4/4 tests PASSED
```

**Result**: ✅ All 24 backend tests passing

---

## Manual Frontend Testing

### 1. Navigate to Organization Management

**Steps**:
1. Open browser: `http://localhost:5173`
2. Login as admin: `owner@duotopia.com` / `owner123`
3. Navigate to `/admin`
4. Click "組織管理" tab

**Expected**:
- [ ] Table displays with columns: 名稱, 擁有人, 教師數, 點數, 狀態, 日期, 操作
- [ ] Data loads from API (check Network tab for GET /api/admin/organizations)
- [ ] At least one organization displayed
- [ ] "創建機構" button visible

---

### 2. Organization List Display

**Verify table columns**:
- [ ] **名稱**: Shows organization name (with display_name if exists)
- [ ] **擁有人**: Shows owner email and name
- [ ] **教師數**: Shows "X / Y" (count / limit)
- [ ] **點數**: Shows remaining and total points with proper formatting
- [ ] **狀態**: Shows active badge (green)
- [ ] **日期**: Shows formatted creation date
- [ ] **操作**: Edit button visible for each row

---

### 3. Search Functionality

**Test search by organization name**:
1. Type partial org name in search box (e.g., "Org")
2. Wait 300ms (debounce delay)
3. Verify:
   - [ ] API called with `?search=Org` parameter (check Network tab)
   - [ ] Table shows only matching organizations
   - [ ] Results update in real-time
   - [ ] Clear search → all organizations return

**Test search by owner email**:
1. Type owner email in search box (e.g., "owner@")
2. Verify:
   - [ ] Organizations owned by that email appear
   - [ ] Non-matching organizations filtered out

**Test empty search**:
- [ ] Empty search shows all organizations
- [ ] No errors in console

---

### 4. Pagination

**Test pagination (if > 25 organizations)**:
1. Verify page size selector shows: 25, 50, 100
2. Click "下一頁" (Next)
3. Verify:
   - [ ] URL or state updates
   - [ ] New data loads
   - [ ] "上一頁" (Previous) button enabled
4. Click "上一頁" (Previous)
5. Verify:
   - [ ] Returns to first page
   - [ ] Correct page indicator

**If < 25 organizations**:
- [ ] Pagination controls hidden
- [ ] All organizations visible

---

### 5. Edit Dialog - Basic Display

**Steps**:
1. Click "編輯" (Edit) button on any organization
2. Verify dialog opens:
   - [ ] Dialog title shows organization name
   - [ ] Form fields populated with current data:
     - [ ] Display Name (显示名稱)
     - [ ] Description (描述)
     - [ ] Tax ID (統一編號)
     - [ ] Teacher Limit (教師上限)
     - [ ] Contact Email (聯絡信箱)
     - [ ] Contact Phone (聯絡電話)
     - [ ] Address (地址)
   - [ ] Points management section visible

---

### 6. Points Management Section

**Verify current points display**:
- [ ] Blue card shows:
  - "目前總點數: X"
  - "已使用: Y"
  - "剩餘: Z"
- [ ] Values match table data

**Test points input**:
1. Enter new total points (e.g., current + 5000)
2. Verify:
   - [ ] Delta calculation shows: "+5,000" in green
   - [ ] No error messages
3. Enter points BELOW used_points
4. Verify:
   - [ ] Error message: "總點數不能低於已使用點數"
   - [ ] Save button disabled
   - [ ] Red border on input

**Test large adjustment warning**:
1. Enter points with delta > 10,000
2. Verify:
   - [ ] Yellow warning alert appears
   - [ ] Message: "點數調整較大，請確認是否正確"
   - [ ] Save button still enabled (just warning, not error)

---

### 7. Form Validation

**Email validation**:
1. Enter invalid email in Contact Email (e.g., "invalid")
2. Attempt to save
3. Verify:
   - [ ] Validation error: "請輸入有效的電子郵件"
   - [ ] Save blocked
4. Enter valid email
5. Verify:
   - [ ] Error clears
   - [ ] Save enabled

**Numeric validation**:
1. Enter negative number in Teacher Limit
2. Verify:
   - [ ] Blocked or shows error
3. Enter non-numeric value in Total Points
4. Verify:
   - [ ] Input rejected or converted

---

### 8. Update Organization - Basic Fields

**Steps**:
1. Click Edit on an organization
2. Change display name to: "Updated Test Org"
3. Change teacher limit to: 100
4. Update contact email to valid email
5. Click "儲存" (Save)
6. Verify:
   - [ ] Loading state: Button shows "儲存中..."
   - [ ] Save button disabled during save
   - [ ] Success toast appears: "更新成功"
   - [ ] Dialog closes automatically
   - [ ] Table refreshes with new data
   - [ ] Network tab shows: PUT /api/admin/organizations/{id}
   - [ ] Response: 200 OK

---

### 9. Update Organization - Points Adjustment

**Test points increase**:
1. Edit organization
2. Note current total_points
3. Increase by 10,000
4. Save
5. Verify:
   - [ ] Success toast shows: "組織更新成功 (點數調整 +10,000)"
   - [ ] Table shows updated remaining points
   - [ ] API response has `points_adjusted: true`

**Test points decrease (valid)**:
1. Edit organization with used_points = 0
2. Decrease total_points by 5,000
3. Save
4. Verify:
   - [ ] Success toast shows delta: "-5,000"
   - [ ] Table updates correctly

**Test points reduction blocked**:
1. Edit organization with used_points > 0
2. Try to set total_points below used_points
3. Verify:
   - [ ] Save button disabled
   - [ ] Error message displayed
   - [ ] Cannot submit form

---

### 10. Dialog Interactions

**Test cancel**:
1. Open edit dialog
2. Make changes (don't save)
3. Click "取消" (Cancel)
4. Verify:
   - [ ] Dialog closes
   - [ ] Changes not saved
   - [ ] No API call made

**Test close during save**:
1. Open edit dialog
2. Click Save (with changes)
3. Try to click outside dialog overlay while saving
4. Verify:
   - [ ] Dialog stays open
   - [ ] `onPointerDownOutside` prevents close
   - [ ] Save completes
   - [ ] Dialog closes after success

**Test keyboard navigation**:
- [ ] Tab key moves between fields
- [ ] Enter in text field doesn't submit
- [ ] Escape key closes dialog (when not saving)

---

### 11. Error Handling

**Test API error (simulated)**:
1. Edit organization
2. Make changes
3. (If possible) Disconnect network or use invalid data
4. Click Save
5. Verify:
   - [ ] Error toast appears
   - [ ] Dialog stays open
   - [ ] User can retry
   - [ ] No data corruption

**Test 404 error**:
1. Manually call API with invalid org_id
2. Verify:
   - [ ] 404 response
   - [ ] User-friendly error message

**Test 403 error**:
1. Try to access as non-admin user
2. Verify:
   - [ ] 403 Forbidden
   - [ ] Redirected or error shown

---

### 12. Multiple Updates

**Test sequential updates**:
1. Edit organization A
2. Save
3. Immediately edit organization B
4. Save
5. Verify:
   - [ ] Both updates successful
   - [ ] Table shows both changes
   - [ ] No race conditions

**Test same organization twice**:
1. Edit organization
2. Save
3. Re-open same organization
4. Verify:
   - [ ] Form shows updated values
   - [ ] Can make further changes
   - [ ] Saves correctly again

---

### 13. Data Consistency

**Verify database persistence**:
1. Make changes and save
2. Refresh browser page
3. Verify:
   - [ ] Changes persisted
   - [ ] Table shows updated data
   - [ ] No data loss

**Verify points math**:
1. Note: total_points, used_points, remaining_points
2. Calculate: remaining = total - used
3. Verify:
   - [ ] Math is correct
   - [ ] Display matches calculation

---

### 14. Accessibility

- [ ] All form labels associated with inputs
- [ ] Keyboard navigation works
- [ ] Focus visible on interactive elements
- [ ] Error messages announced (screen reader)
- [ ] Dialog has proper ARIA attributes
- [ ] Color contrast sufficient (WCAG AA)

---

### 15. Responsive Design

**Test on mobile (375px)**:
- [ ] Table responsive or scrollable
- [ ] Dialog fits on screen
- [ ] Form fields usable
- [ ] Buttons accessible

**Test on tablet (768px)**:
- [ ] Two-column form layout maintained
- [ ] Table columns readable

**Test on desktop (1920px)**:
- [ ] Layout not stretched
- [ ] Max width applied
- [ ] Content centered

---

### 16. Performance

**Test with large dataset**:
1. Create 100+ organizations (if possible)
2. Verify:
   - [ ] List loads in < 2 seconds
   - [ ] Search responsive (< 500ms after debounce)
   - [ ] Pagination smooth
   - [ ] No N+1 query issues (check backend logs)

**Test concurrent requests**:
1. Open multiple browser tabs
2. Edit different organizations simultaneously
3. Verify:
   - [ ] No conflicts
   - [ ] Each save successful
   - [ ] Last write wins (or conflict detection)

---

## Known Limitations

As identified in code review:

1. **Missing full organization fetch**: Form fields (description, tax_id, contact info, address) not populated from API on dialog open - they show empty unless edited in this session. Workaround: Add GET /api/admin/organizations/{id} endpoint in future.

2. **No optimistic updates**: Table refresh requires full API call after save. Future enhancement: Update local state immediately.

3. **No undo functionality**: Changes saved are final. User must manually revert.

---

## Test Results Summary

**Date**: _________
**Total Tests**: 60+
**Passed**: _____
**Failed**: _____
**Blocked**: _____

**Critical Issues**: ___________________________

**Non-Critical Issues**: ___________________________

**Notes**: ___________________________

---

## Sign-off

- [ ] All critical functionality tested
- [ ] No blocking bugs found
- [ ] Ready for deployment

**Tester Signature**: _________
**Approver Signature**: _________
**Date**: _________
