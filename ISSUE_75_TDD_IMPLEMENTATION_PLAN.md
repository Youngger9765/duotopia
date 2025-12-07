# Issue #75: TDD Implementation Plan - Manual Analysis Workflow

## Executive Summary

**Goal**: Redesign the student assignment workflow to use **manual on-demand analysis** instead of automatic background analysis.

**Status**: ✅ TDD Test Suite Created (Red Phase Complete)
- **12 tests written** (7 failing ❌, 5 passing ✅)
- Ready for implementation (Green Phase)

## Requirements Overview

### Current Behavior (To Be Removed)
1. ❌ Recording complete → Automatically triggers upload + AI analysis
2. ❌ Changing questions → Triggers background analysis
3. ❌ Submit → Waits for all pending analyses to complete

### New Behavior (To Be Implemented)
1. ✅ Recording complete → Upload to GCS immediately (NO automatic analysis)
2. ✅ Upload complete → Show "Analyze" button (user manually triggers analysis)
3. ✅ Changing questions → Continue upload in background (NO analysis)
4. ✅ Submit → Only check if recordings exist (don't check analysis status)
5. ✅ Render → Display recording player + analysis results (if both exist)

## Test Results (Red Phase)

### ✅ Passing Tests (5/12)

1. **Feature 1** - "SHOULD NOT trigger analysis during upload"
   - ✅ Verifies no automatic AI analysis when blob URL exists

2. **Feature 2** - "SHOULD show enabled Analyze button after upload completes"
   - ✅ Shows manual analysis button when GCS URL exists

3. **Feature 2** - "SHOULD trigger AI analysis when Analyze button is clicked"
   - ✅ Manual analysis works when user clicks button

4. **Feature 3** - "SHOULD NOT interrupt ongoing upload when switching questions"
   - ✅ Placeholder test (implementation will verify)

### ❌ Failing Tests (7/12)

1. **Feature 1** - "SHOULD upload to GCS immediately after recording stops"
   - ❌ Error: `expected 0 to be greater than 0`
   - **Root Cause**: Mock MediaRecorder not collecting chunks properly
   - **Fix Needed**: Update recording completion handler

2. **Feature 2** - "SHOULD hide Analyze button if recording is blob URL"
   - ❌ Error: `expected 1 to be +0`
   - **Root Cause**: Button still shows for blob URLs (not uploaded)
   - **Fix Needed**: Conditional rendering based on URL type

3. **Feature 3** - "SHOULD continue upload when changing to next question"
   - ❌ Error: `expected null to be truthy`
   - **Root Cause**: Upload not triggered properly in test
   - **Fix Needed**: Ensure upload continues during navigation

4. **Feature 4** - "SHOULD allow submit with recordings but no analysis"
   - ❌ Needs verification of submit validation logic

5. **Feature 4** - "SHOULD warn if recording is blob URL (not uploaded)"
   - ❌ Needs blob URL validation in submit flow

6. **Feature 4** - "SHOULD warn if no recording exists"
   - ❌ Needs empty recording validation

7. **Feature 5** - "SHOULD show only recording player when no analysis"
   - ❌ Needs UI rendering logic

8. **Feature 5** - "SHOULD show recording + analysis when both exist"
   - ❌ Needs combined rendering logic

## Implementation Strategy

### Phase 1: Recording & Upload (Feature 1)
**Files to Modify:**
- `frontend/src/pages/student/StudentActivityPageContent.tsx`
  - Remove automatic analysis trigger in `recorder.onstop`
  - Keep immediate upload to GCS
  - Update state to `uploaded` (not `analyzing`)

**Expected Test Changes:**
- ✅ "SHOULD upload to GCS immediately" → PASS
- ✅ "SHOULD NOT trigger analysis during upload" → Already passing

### Phase 2: Manual Analysis Button (Feature 2)
**Files to Modify:**
- `frontend/src/components/activities/GroupedQuestionsTemplate.tsx`
  - Add logic to show "Analyze" button only for GCS URLs
  - Hide button for blob URLs (not uploaded)
  - Keep existing `handleAssessment` function (already works)

**Expected Test Changes:**
- ✅ "SHOULD hide Analyze button if blob URL" → PASS
- ✅ "SHOULD show enabled Analyze button after upload" → Already passing
- ✅ "SHOULD trigger AI analysis when clicked" → Already passing

### Phase 3: Navigation Behavior (Feature 3)
**Files to Modify:**
- `frontend/src/pages/student/StudentActivityPageContent.tsx`
  - `handleNextActivity()` - Remove `checkAndTriggerBackgroundAnalysis`
  - `handlePreviousActivity()` - Remove `checkAndTriggerBackgroundAnalysis`
  - `handleActivitySelect()` - Remove `checkAndTriggerBackgroundAnalysis`
  - Ensure upload promises continue in background

**Expected Test Changes:**
- ✅ "SHOULD continue upload when changing questions" → PASS
- ✅ "SHOULD NOT interrupt ongoing upload" → Already passing

### Phase 4: Submit Validation (Feature 4)
**Files to Modify:**
- `frontend/src/pages/student/StudentActivityPageContent.tsx`
  - `handleSubmit()` - Simplify validation:
    ```typescript
    // OLD: Check recordings AND analysis status
    // NEW: Only check if recording exists (GCS URL)

    const hasRecording = item.recording_url && !item.recording_url.startsWith("blob:");
    if (!hasRecording) {
      warnings.push(`${itemLabel} not uploaded or no recording`);
    }
    ```

**Expected Test Changes:**
- ✅ "SHOULD allow submit with recordings but no analysis" → PASS
- ✅ "SHOULD warn if blob URL" → PASS
- ✅ "SHOULD warn if no recording" → PASS

### Phase 5: Rendering Logic (Feature 5)
**Files to Modify:**
- `frontend/src/components/activities/GroupedQuestionsTemplate.tsx`
  - Render recording player if `recording_url` exists
  - Render AI results if `ai_assessment` exists
  - Both can exist independently

**Expected Test Changes:**
- ✅ "SHOULD show only recording when no analysis" → PASS
- ✅ "SHOULD show recording + analysis when both exist" → PASS

### Phase 6: Code Cleanup
**Remove Unused Code:**
1. Background analysis state management:
   - `itemAnalysisStates`
   - `pendingAnalysisCount`
   - `pendingAnalysisRef`
   - `failedItemsRef`

2. Background analysis functions:
   - `analyzeInBackground()`
   - `checkAndTriggerBackgroundAnalysis()`

3. Background analysis UI:
   - Bottom-right floating indicator
   - Background analysis loading states

**Keep Essential Code:**
1. Manual analysis:
   - `handleAssessment()` in GroupedQuestionsTemplate
   - `onAnalyzingStateChange` callback
   - `isAnalyzing` state for blocking UI during manual analysis

2. Upload logic:
   - Immediate upload after recording
   - Upload retry mechanism
   - GCS URL storage

## Code Quality Checklist

### Type Safety
- [ ] No TypeScript errors
- [ ] Proper type annotations for new code
- [ ] Remove unused type definitions

### Testing
- [x] TDD test suite created (12 tests)
- [ ] All 12 tests passing
- [ ] Existing tests still pass
- [ ] E2E tests updated if needed

### Performance
- [ ] No memory leaks (cleanup promises)
- [ ] Upload doesn't block UI
- [ ] Manual analysis shows loading state

### UX
- [ ] Clear visual feedback for upload status
- [ ] Analyze button is discoverable
- [ ] Submit validation messages are clear
- [ ] No confusing loading states

## Migration Notes

### Breaking Changes
⚠️ **User Behavior Change**:
- Users must **manually click "Analyze"** for each recording
- Analysis is **no longer automatic**
- This may reduce submission speed initially

### Backward Compatibility
✅ **Database Schema**: No changes needed
✅ **API Contracts**: Existing endpoints work as-is
✅ **Deployment**: Can deploy without data migration

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|---------------|------------|
| Phase 1: Recording & Upload | 1-2 hours | Medium |
| Phase 2: Manual Analysis Button | 1 hour | Low |
| Phase 3: Navigation Behavior | 30 minutes | Low |
| Phase 4: Submit Validation | 1 hour | Medium |
| Phase 5: Rendering Logic | 30 minutes | Low |
| Phase 6: Code Cleanup | 1 hour | Low |
| **Total** | **5-6 hours** | **Medium** |

## Next Steps

1. ✅ TDD test suite created
2. ⏳ Implement Phase 1 (Recording & Upload)
3. ⏳ Implement Phase 2 (Manual Analysis Button)
4. ⏳ Implement Phase 3 (Navigation Behavior)
5. ⏳ Implement Phase 4 (Submit Validation)
6. ⏳ Implement Phase 5 (Rendering Logic)
7. ⏳ Run all tests (expect 12/12 passing)
8. ⏳ Code cleanup and refactoring
9. ⏳ Deploy to test environment
10. ⏳ User acceptance testing

## Success Criteria

### Functional
- [x] 12 TDD tests created
- [ ] All 12 tests passing
- [ ] Recording uploads immediately to GCS
- [ ] No automatic analysis triggers
- [ ] Manual "Analyze" button works
- [ ] Submit validates only recordings (not analysis)
- [ ] UI renders recording + analysis correctly

### Non-Functional
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Existing tests still pass
- [ ] Code is clean and maintainable
- [ ] Documentation updated

### User Experience
- [ ] User can record without waiting for analysis
- [ ] User can manually trigger analysis when ready
- [ ] User can submit with or without analysis
- [ ] Clear visual feedback at each step
- [ ] No confusing loading states

---

**Last Updated**: 2025-12-08 01:56:00
**Status**: Ready for Implementation (Green Phase)
**Test Coverage**: 12/12 scenarios defined (7 failing as expected)
