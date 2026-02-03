# Task 5: Edit Organization Dialog - Test Checklist

**Feature**: Admin organization update functionality with comprehensive points management.

## Implementation Summary

### Files Modified
- `/frontend/src/pages/admin/AdminOrganizations.tsx` (+406 lines)

### Key Features Implemented

1. **Edit Dialog Component**
   - Opens when Edit button clicked in organization list
   - Shows organization name in header
   - Responsive 2-column layout for form fields
   - Maximum height with scrollable content

2. **Form Fields**
   - Display Name
   - Description (textarea)
   - Tax ID (8 character limit)
   - Teacher Limit (numeric, optional)
   - Contact Email (with validation)
   - Contact Phone
   - Address
   - Total Points (with special handling)

3. **Points Management Section**
   - Current points display (Total/Used/Remaining)
   - New total points input
   - Real-time delta calculation (+/- change)
   - Warning for reducing below used points
   - Alert for large adjustments (>10,000 points)
   - Validation to prevent invalid reductions

4. **Form Validation**
   - Email format validation (regex)
   - Numeric validation for limits and points
   - Negative number prevention
   - Inline error messages
   - Prevention of total points < used points

5. **Save Logic**
   - Only sends changed fields to API
   - Properly typed API response
   - Loading state on save button
   - Success toast with points change info
   - Error handling with toast notifications
   - Automatic list refresh on success
   - Dialog closes on success

6. **UI/UX Features**
   - Two-column grid layout
   - Highlighted points section (blue background)
   - Cancel button
   - Disabled save button while loading
   - Disabled save when validation fails
   - Clear error messages
   - Responsive design

## Manual Test Checklist

### Test Case 1: Basic Edit Flow
- [ ] Click Edit button on any organization
- [ ] Dialog opens with correct organization name
- [ ] All fields pre-populated with current values
- [ ] Can modify display name
- [ ] Can modify description
- [ ] Can modify tax ID
- [ ] Can modify contact fields
- [ ] Click Save
- [ ] Success toast appears
- [ ] Dialog closes
- [ ] List refreshes with updated data

### Test Case 2: Points Increase
- [ ] Open edit dialog
- [ ] Change total points to higher value (e.g., +5000)
- [ ] See green positive delta (+5,000)
- [ ] No warnings shown
- [ ] Click Save
- [ ] Success toast shows: "組織更新成功 (點數調整: +5,000)"
- [ ] List shows updated points

### Test Case 3: Points Decrease (Valid)
- [ ] Open edit dialog for org with unused points
- [ ] Reduce total points (but stay above used points)
- [ ] See red negative delta
- [ ] No error warnings
- [ ] Click Save
- [ ] Success toast shows negative adjustment
- [ ] Points updated correctly

### Test Case 4: Points Decrease (Invalid)
- [ ] Open edit dialog for org with some used points
- [ ] Try to set total points below used points
- [ ] Red error alert appears: "總點數不能低於已使用點數"
- [ ] Save button disabled
- [ ] Cannot submit form
- [ ] Error toast if attempted: "總點數不能低於已使用點數"

### Test Case 5: Large Points Adjustment Warning
- [ ] Open edit dialog
- [ ] Change points by more than 10,000
- [ ] Yellow warning alert appears
- [ ] Message: "注意：您正在進行大幅度點數調整..."
- [ ] Can still save (warning, not error)
- [ ] Save succeeds

### Test Case 6: Email Validation
- [ ] Enter invalid email (e.g., "not-an-email")
- [ ] Inline error appears: "請輸入有效的 Email 格式"
- [ ] Try to save
- [ ] Error toast: "請修正表單錯誤"
- [ ] Form not submitted
- [ ] Fix email format
- [ ] Error disappears
- [ ] Can save successfully

### Test Case 7: Numeric Validation
- [ ] Enter non-numeric value in teacher_limit
- [ ] Error: "教師限制必須是數字"
- [ ] Enter negative number
- [ ] Error: "教師限制不能為負數"
- [ ] Enter non-numeric in total_points
- [ ] Error: "總點數必須是數字"
- [ ] Fix all errors
- [ ] Can save

### Test Case 8: Cancel Functionality
- [ ] Open edit dialog
- [ ] Make several changes
- [ ] Click Cancel
- [ ] Dialog closes
- [ ] No changes saved
- [ ] List unchanged
- [ ] Reopen dialog
- [ ] Original values shown

### Test Case 9: Save Loading State
- [ ] Open edit dialog
- [ ] Make changes
- [ ] Click Save
- [ ] Button text changes to "儲存中..."
- [ ] Button disabled during save
- [ ] Cancel button disabled during save
- [ ] Cannot close dialog during save
- [ ] After save completes, dialog closes

### Test Case 10: Error Handling
- [ ] Simulate API error (disconnect network or use invalid data)
- [ ] Try to save
- [ ] Error toast appears with message
- [ ] Dialog stays open
- [ ] Can retry or cancel
- [ ] Changes preserved in form

### Test Case 11: Teacher Limit Display
- [ ] Open edit for org with teachers
- [ ] See current teacher count below teacher_limit field
- [ ] Text: "目前有 X 位教師"
- [ ] Useful context for setting limits

### Test Case 12: Empty/Optional Fields
- [ ] Leave optional fields empty
- [ ] Can save successfully
- [ ] No errors for empty optional fields
- [ ] Required field handling correct

### Test Case 13: Responsive Design
- [ ] Open on wide screen
- [ ] Two-column layout displayed
- [ ] Open on narrow screen
- [ ] Layout adjusts appropriately
- [ ] Dialog scrollable if content overflows
- [ ] Max height 90vh respected

### Test Case 14: Multiple Edits in Session
- [ ] Edit organization A
- [ ] Save changes
- [ ] Edit organization B
- [ ] Previous changes not mixed in
- [ ] Each edit independent
- [ ] No state pollution

## API Integration Tests

### Verify API Call
```javascript
// Expected payload when only changing display_name and total_points:
{
  display_name: "New Name",
  total_points: 50000
}
// Should NOT include unchanged fields
```

### Verify Response Handling
```javascript
// Expected response:
{
  organization_id: "uuid",
  message: "Organization updated successfully",
  points_adjusted: true,
  points_change: 10000
}
```

## Edge Cases

- [ ] Edit org with null teacher_limit
- [ ] Edit org with 0 used points
- [ ] Edit org with 0 remaining points
- [ ] Edit org with exactly used_points = total_points
- [ ] Very large point numbers (>1,000,000)
- [ ] Very long description text
- [ ] Special characters in fields
- [ ] Unicode characters in fields

## Performance

- [ ] Dialog opens quickly (<200ms)
- [ ] Form updates smoothly (no lag)
- [ ] Save completes in reasonable time (<2s)
- [ ] List refresh doesn't cause flicker
- [ ] No memory leaks on repeated opens

## Accessibility

- [ ] Can navigate form with keyboard
- [ ] Tab order is logical
- [ ] Can submit with Enter key
- [ ] Can cancel with Escape key
- [ ] Labels properly associated with inputs
- [ ] Error messages announced by screen readers

## Success Criteria

- ✅ Dialog opens and closes smoothly
- ✅ All form fields functional
- ✅ Validation works correctly
- ✅ Points management features work
- ✅ API integration successful
- ✅ Error handling robust
- ✅ UX is intuitive and clear
- ✅ No TypeScript errors
- ✅ Build successful
- ✅ No console errors

## Known Limitations

1. **Partial Field Population**: Currently only populating fields available in `OrganizationListItem`. Some fields (description, tax_id, etc.) start empty even if they exist in the database. This is because the list API doesn't return these fields. Future enhancement: fetch full organization details on edit.

2. **No Optimistic Updates**: List refresh requires full API call. Could be optimized with optimistic updates.

3. **No Undo**: After save, changes are permanent. Consider adding undo functionality.

## Future Enhancements

1. Fetch full organization details when opening edit dialog
2. Add confirmation dialog for large point adjustments
3. Add audit log display (who changed what when)
4. Add bulk edit capability
5. Add organization status toggle (active/inactive)
6. Add organization deletion
7. Add owner change functionality
8. Add project staff management in dialog
