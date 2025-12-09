# Issue #75: Edge Case Analysis - Recording Deletion & Re-recording

## Edge Case Scenario

**User Story:**
1. User records audio → Automatically uploads to GCS (e.g., `recording_20251208_abc123.webm`)
2. User clicks "Delete" button to remove the recording
3. User re-records audio → Uploads to GCS with new UUID (e.g., `recording_20251208_xyz456.webm`)

**Question:** What happens to the old GCS file?

## Current Implementation Analysis

### ✅ Backend Already Handles This Correctly

**File:** `/Users/young/project/duotopia/backend/routers/students.py` (lines 1349-1367)

```python
# Delete old recording file (if exists and different)
if old_audio_url and old_audio_url != audio_url:
    try:
        audio_manager.delete_old_audio(old_audio_url)
        print(f"Deleted old student recording: {old_audio_url}")

        # Also clear old AI scores (scores belong to old recording)
        if existing_item_progress:
            existing_item_progress.accuracy_score = None
            existing_item_progress.fluency_score = None
            existing_item_progress.pronunciation_score = None
            existing_item_progress.completeness_score = None
            existing_item_progress.ai_feedback = None
            existing_item_progress.ai_assessed_at = None
            print("Cleared AI scores for re-recording")
    except Exception as e:
        print(f"Failed to delete old recording: {e}")
```

**Key Points:**
1. ✅ Old GCS file is **automatically deleted** when new recording is uploaded
2. ✅ AI scores are **cleared** (scores are tied to the old recording)
3. ✅ Uses `audio_manager.delete_old_audio()` for proper cleanup
4. ✅ Error handling ensures upload succeeds even if deletion fails

### Frontend Flow (Current Behavior)

**File:** `/Users/young/project/duotopia/frontend/src/pages/student/StudentActivityPageContent.tsx`

**Current "Delete" Button Behavior:**
- Clears `recording_url` from local state
- Clears `ai_assessment` data
- **Does NOT** call backend to delete GCS file immediately
- Backend handles cleanup when **new recording is uploaded**

## Scenarios Analysis

### Scenario 1: Record → Delete → Re-record (✅ Already Handled)

**Steps:**
1. User records audio → `recorder.onstop` triggers upload → GCS file: `file_v1.webm`
2. User clicks "Delete" → Frontend clears `recording_url` (sets to `""`)
3. User re-records → `recorder.onstop` triggers upload → GCS file: `file_v2.webm`
4. **Backend detects old file** (`file_v1.webm`) → Deletes it → Saves `file_v2.webm`

**Result:** ✅ No orphaned files

### Scenario 2: Record → Upload → Delete → Leave (⚠️ Orphaned File)

**Steps:**
1. User records audio → Uploads to GCS → `file_v1.webm` saved
2. User clicks "Delete" → Frontend clears `recording_url`
3. User **navigates away** or **closes tab** (no re-recording)

**Result:** ⚠️ `file_v1.webm` remains in GCS (orphaned)

**Impact:**
- Storage cost accumulates over time
- No mechanism to clean up abandoned recordings

### Scenario 3: Record → Upload → Delete → Record → Delete → Record (✅ Handled)

**Steps:**
1. Record → Upload → `file_v1.webm`
2. Delete → Frontend clears state
3. Re-record → Upload → `file_v2.webm` (backend deletes `file_v1.webm`)
4. Delete → Frontend clears state
5. Re-record → Upload → `file_v3.webm` (backend deletes `file_v2.webm`)

**Result:** ✅ Only latest file remains (`file_v3.webm`)

## Recommendations

### Option 1: Immediate Deletion (Backend API Call)

**Approach:**
- Frontend calls backend API when user clicks "Delete"
- Backend deletes GCS file immediately

**Pros:**
- ✅ No orphaned files
- ✅ Instant cleanup

**Cons:**
- ❌ Adds network latency to delete action
- ❌ Requires new backend endpoint
- ❌ Fails if network is offline

**Implementation:**
```typescript
// Frontend
const handleDeleteRecording = async () => {
  if (recordingUrl.startsWith("https://storage.googleapis.com/")) {
    await fetch(`/api/students/delete-recording`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audio_url: recordingUrl }),
    });
  }
  // Clear local state
  setRecordingUrl("");
};
```

### Option 2: Lazy Deletion (Keep Current Behavior) ⭐ **Recommended**

**Approach:**
- Keep current behavior (backend deletes old file when new file is uploaded)
- Add periodic cleanup job to remove orphaned files

**Pros:**
- ✅ No frontend changes needed
- ✅ Simple and reliable
- ✅ Works offline (no network required for delete)
- ✅ Batch processing reduces API calls

**Cons:**
- ⚠️ Orphaned files exist temporarily (until cleanup job runs)

**Implementation:**
```python
# Backend cleanup job (run daily via cron)
async def cleanup_orphaned_recordings():
    """
    Delete GCS recordings that are not referenced in StudentItemProgress
    """
    # 1. List all recordings in GCS
    all_gcs_files = storage_client.list_blobs("duotopia-audio", prefix="recordings/")

    # 2. Get all recording_url from StudentItemProgress
    active_urls = db.query(StudentItemProgress.recording_url).filter(
        StudentItemProgress.recording_url.isnot(None)
    ).all()

    # 3. Delete files not in database
    orphaned_files = [f for f in all_gcs_files if f.public_url not in active_urls]
    for file in orphaned_files:
        file.delete()
        print(f"Deleted orphaned recording: {file.name}")
```

### Option 3: Hybrid Approach (Best of Both Worlds)

**Approach:**
- Frontend calls backend API (non-blocking)
- If API call fails, rely on lazy deletion
- Periodic cleanup job as fallback

**Pros:**
- ✅ Best user experience (immediate feedback)
- ✅ Fallback mechanism (cleanup job)

**Cons:**
- ❌ More complex implementation

## Decision Matrix

| Scenario | Option 1 (Immediate) | Option 2 (Lazy) | Option 3 (Hybrid) |
|----------|---------------------|-----------------|-------------------|
| No orphaned files | ✅ Yes | ⚠️ Temporary | ✅ Yes |
| Frontend complexity | ❌ High | ✅ Low | ⚠️ Medium |
| Backend complexity | ❌ Medium | ✅ Low | ❌ High |
| Offline support | ❌ No | ✅ Yes | ⚠️ Partial |
| API load | ❌ High | ✅ Low | ⚠️ Medium |
| **Recommendation** | ❌ Not ideal | ✅ **Best** | ⚠️ Overkill |

## Final Recommendation

**Use Option 2: Lazy Deletion + Periodic Cleanup**

**Rationale:**
1. ✅ **Simplicity**: No frontend changes needed
2. ✅ **Reliability**: Current backend logic already handles most cases
3. ✅ **Offline-friendly**: Delete button works instantly (no network wait)
4. ✅ **Cost-effective**: Orphaned files are minimal (only abandoned recordings)
5. ✅ **Scalable**: Cleanup job runs in background (low overhead)

**Implementation Steps:**
1. ✅ Keep current frontend behavior (no changes needed)
2. ✅ Keep current backend logic (already deletes old files on re-upload)
3. ⏳ Add periodic cleanup job (optional, for production)

## Test Coverage

### Existing Tests (Already Passing)
- ✅ Upload recording → Creates GCS file
- ✅ Re-record → Deletes old file, uploads new file
- ✅ AI scores cleared on re-recording

### New Tests to Add

**Test Case 1: Delete Button (Frontend)**
```typescript
test("SHOULD clear recording_url when Delete button is clicked", async () => {
  // Arrange: Render component with recording
  const mockActivities = [
    { items: [{ recording_url: "https://gcs.com/file.webm" }] }
  ];
  render(<StudentActivityPageContent activities={mockActivities} />);

  // Act: Click Delete button
  const deleteButton = screen.getByTitle(/delete|清除/i);
  await userEvent.click(deleteButton);

  // Assert: recording_url is cleared
  expect(screen.queryByTitle(/delete|清除/i)).not.toBeInTheDocument();
});
```

**Test Case 2: Re-record After Delete (Integration)**
```typescript
test("SHOULD upload new file after delete (old file cleaned by backend)", async () => {
  // Arrange: Record → Upload → Delete
  const { recordButton, stopButton, deleteButton } = setup();
  await userEvent.click(recordButton);
  await userEvent.click(stopButton);
  await waitFor(() => expect(uploadSpy).toHaveBeenCalled()); // file_v1.webm uploaded
  await userEvent.click(deleteButton); // Clear frontend state

  // Act: Re-record
  await userEvent.click(recordButton);
  await userEvent.click(stopButton);

  // Assert: New file uploaded, old file deletion logged
  await waitFor(() => {
    expect(uploadSpy).toHaveBeenCalledTimes(2); // file_v2.webm uploaded
    expect(console.log).toHaveBeenCalledWith(expect.stringContaining("Deleted old recording"));
  });
});
```

## Storage Cost Analysis

**Assumption:**
- Average recording: 5 seconds × 16 kbps = ~10 KB
- Abandoned recordings: 5% of all recordings
- Monthly recordings: 10,000

**Cost Calculation:**
- Orphaned files: 10,000 × 5% = 500 files
- Storage: 500 × 10 KB = 5 MB
- GCS cost: 5 MB × $0.020/GB/month = **$0.0001/month** (negligible)

**Conclusion:** Even without cleanup job, cost is minimal.

## Migration Plan

**Phase 1: Documentation (Current)** ✅
- Document current behavior
- Clarify edge case handling
- Update test plan

**Phase 2: Test Coverage (Next)**
- Add test for delete button
- Add test for re-recording after delete
- Verify backend cleanup logic

**Phase 3: Monitoring (Optional)**
- Track orphaned file count (analytics)
- Alert if orphaned files exceed threshold

**Phase 4: Cleanup Job (Production Only)**
- Implement periodic cleanup (weekly)
- Run during off-peak hours
- Log cleanup statistics

## Summary

### Current Status
✅ **Edge case is already handled** by backend (lines 1349-1367 in `students.py`)

### Action Items
1. ✅ Document behavior (this document)
2. ⏳ Add test coverage for delete + re-record scenario
3. ⏳ Update `ISSUE_75_TDD_IMPLEMENTATION_PLAN.md` with edge case tests
4. ⏳ (Optional) Implement cleanup job for production

### No Code Changes Needed
The current implementation already handles this edge case correctly. We only need to:
1. Add test coverage to verify the behavior
2. Document it for future reference
3. Optionally add cleanup job for production safety

---

**Last Updated:** 2025-12-08 02:30:00
**Status:** Edge case analysis complete, no implementation changes needed
**Risk:** Low (current implementation is correct)
