# AI Batch Grading Complete Implementation Plan

## Overview
Implement complete AI batch grading workflow with automatic AI assessment, item-level comments, and assignment-level feedback.

## Database Schema
✅ **No migration needed**:
- `StudentItemProgress.teacher_feedback` already exists (can be reused for AI comments)
- `StudentAssignment.feedback` already exists

## Implementation Tasks

### Task 1: Create Comprehensive TDD Tests
**File**: `backend/tests/integration/api/test_batch_grading_complete.py`

Test cases to implement:
1. All items have recordings and AI scores → generate comments and feedback
2. Some items missing AI scores → trigger assessment, then generate comments
3. Some items missing recordings → skip assessment, no comment
4. Item-level comment generation matches score patterns
5. Assignment feedback summarizes performance correctly
6. Batch grade 5 students with various scenarios

### Task 2: Helper Functions
**File**: `backend/routers/assignments.py`

Functions to implement:
- `trigger_ai_assessment_for_item()` - Call Azure Speech API
- `generate_item_comment()` - Generate Chinese comment based on scores
- `generate_assignment_feedback()` - Generate overall feedback

### Task 3: Update batch_grade_assignment()
**File**: `backend/routers/assignments.py`

Integration points:
- Before score calculation, check for missing AI assessments
- Trigger assessment if needed
- Generate item comments
- Generate assignment feedback
- Store in database

### Task 4: Update API Response Schema
**File**: `backend/routers/assignments.py`

Add to `StudentBatchGradingResult`:
- `completed_items: int`
- `feedback: Optional[str]`

### Task 5: Update Frontend
**File**: `frontend/src/components/BatchGradingModal.tsx`

Add:
- Display feedback in tooltip or expandable row
- Show completed_items count

## Success Criteria
- ✅ All tests pass
- ✅ Missing AI scores are automatically generated
- ✅ Each item has an AI comment
- ✅ Assignment has overall feedback
- ✅ No duplicate API calls (efficient)
- ✅ Score calculation remains correct
