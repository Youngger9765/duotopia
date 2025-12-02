# Complete AI Batch Grading Implementation Specification

## Overview
Implement the complete AI batch grading workflow that automatically triggers AI assessment for missing scores, generates item-level comments, and creates assignment-level feedback.

## Database Schema (No Migration Needed)
- `StudentItemProgress.teacher_feedback` (Text) - Will store AI-generated item comments
- `StudentAssignment.feedback` (Text) - Already exists, will store assignment feedback

## Files to Modify

### 1. `/Users/young/project/duotopia/backend/routers/assignments.py`

#### A. Update Response Schema (Line ~307)
```python
class StudentBatchGradingResult(BaseModel):
    """單個學生的批改結果"""

    student_id: int
    student_name: str
    total_score: float
    missing_items: int
    total_items: int  # NEW: Total items in assignment
    completed_items: int  # NEW: Items with recordings
    avg_pronunciation: float
    avg_accuracy: float
    avg_fluency: float
    avg_completeness: float
    feedback: Optional[str] = None  # NEW: Assignment feedback
    status: str
```

#### B. Add Helper Functions (After imports, around line 100)

```python
def generate_item_comment(
    pronunciation: float,
    accuracy: float,
    fluency: float,
    completeness: float,
) -> str:
    """
    Generate AI comment for a single item based on scores.
    Returns Chinese feedback based on score patterns.
    """
    comments = []

    # Pronunciation feedback
    if pronunciation >= 90:
        comments.append("發音非常標準")
    elif pronunciation >= 80:
        comments.append("發音良好")
    elif pronunciation >= 70:
        comments.append("發音尚可，可以再進步")
    else:
        comments.append("發音需要加強練習")

    # Fluency feedback
    if fluency >= 90:
        comments.append("表達流暢自然")
    elif fluency >= 80:
        comments.append("表達流暢")
    elif fluency < 70:
        comments.append("可以試著說得更流暢")

    # Completeness feedback
    if completeness < 70:
        comments.append("句子完整度需要提升")

    # Accuracy feedback
    if accuracy < 70:
        comments.append("準確度有待加強")

    return "、".join(comments) + "。" if comments else "表現良好。"


def generate_assignment_feedback(
    total_items: int,
    completed_items: int,
    avg_score: float,
    avg_pronunciation: float,
    avg_fluency: float,
    avg_accuracy: float,
    avg_completeness: float,
) -> str:
    """
    Generate overall assignment feedback in Chinese.
    """
    feedback_parts = []

    # Completion status
    completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
    if completion_rate == 100:
        feedback_parts.append(f"完整完成了所有 {total_items} 題")
    else:
        feedback_parts.append(f"完成了 {completed_items}/{total_items} 題")

    # Overall performance
    if avg_score >= 90:
        feedback_parts.append("整體表現優秀")
    elif avg_score >= 80:
        feedback_parts.append("整體表現良好")
    elif avg_score >= 70:
        feedback_parts.append("整體表現尚可")
    else:
        feedback_parts.append("還有進步空間")

    # Detailed breakdown (only if has completed items)
    if completed_items > 0:
        details = []
        if avg_pronunciation >= 85:
            details.append(f"發音標準（{avg_pronunciation:.0f}分）")
        elif avg_pronunciation < 70:
            details.append(f"發音需加強（{avg_pronunciation:.0f}分）")

        if avg_fluency >= 85:
            details.append(f"表達流暢（{avg_fluency:.0f}分）")
        elif avg_fluency < 70:
            details.append(f"流暢度可再提升（{avg_fluency:.0f}分）")

        if avg_accuracy >= 85:
            details.append(f"準確度優秀（{avg_accuracy:.0f}分）")
        elif avg_accuracy < 70:
            details.append(f"準確度需加強（{avg_accuracy:.0f}分）")

        if details:
            feedback_parts.append("、".join(details))

    # Suggestions
    if avg_score >= 85:
        feedback_parts.append("建議：繼續保持，可以挑戰更難的內容")
    elif avg_score >= 70:
        feedback_parts.append("建議：多聽多練，注意發音細節")
    else:
        feedback_parts.append("建議：加強基礎練習，不要急躁")

    return "。".join(feedback_parts) + "。"


async def trigger_ai_assessment_for_item(
    item_progress: StudentItemProgress,
    db: Session,
) -> bool:
    """
    Trigger AI assessment for a single item that has recording but no scores.

    Returns:
        bool: True if assessment succeeded, False otherwise
    """
    if not item_progress.recording_url:
        return False

    if item_progress.ai_assessed_at is not None:
        return False  # Already assessed

    try:
        # Get reference text from content item
        content_item = db.query(ContentItem).filter(
            ContentItem.id == item_progress.content_item_id
        ).first()

        if not content_item:
            logger.error(f"ContentItem not found for item_progress {item_progress.id}")
            return False

        reference_text = content_item.text

        # Download audio from recording_url
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            audio_response = await client.get(item_progress.recording_url)
            audio_data = audio_response.content

        # Convert audio to WAV format
        from routers.speech_assessment import convert_audio_to_wav
        wav_data = convert_audio_to_wav(audio_data, "audio/webm")

        # Call Azure Speech Assessment API
        from routers.speech_assessment import assess_pronunciation
        assessment_result = assess_pronunciation(wav_data, reference_text)

        # Store results
        item_progress.accuracy_score = Decimal(str(assessment_result.get("accuracy_score", 0)))
        item_progress.fluency_score = Decimal(str(assessment_result.get("fluency_score", 0)))
        item_progress.pronunciation_score = Decimal(str(assessment_result.get("pronunciation_score", 0)))
        item_progress.completeness_score = Decimal(str(assessment_result.get("completeness_score", 0)))
        item_progress.transcription = assessment_result.get("recognized_text", "")
        item_progress.ai_feedback = json.dumps(assessment_result)
        item_progress.ai_assessed_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"Successfully assessed item_progress {item_progress.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to assess item_progress {item_progress.id}: {e}")
        db.rollback()
        return False
```

#### C. Modify batch_grade_assignment() function (Around line 2720)

**Insert BEFORE the score calculation loop (after line 2793):**

```python
# 4.5. Trigger AI assessment for items with recordings but no scores
with start_span("Trigger Missing AI Assessments"):
    for item in item_progress_list:
        # Check if has recording but no AI assessment
        if item.recording_url and not item.ai_assessed_at:
            logger.info(f"Triggering AI assessment for item_progress {item.id}")
            await trigger_ai_assessment_for_item(item, db)
            # Refresh to get updated scores
            db.refresh(item)

    perf.checkpoint("AI Assessments Triggered")
```

**After score calculation (around line 2895), add comment and feedback generation:**

```python
# 6.5. Generate item-level comments
with start_span("Generate Item Comments"):
    for item in item_progress_list:
        # Only generate comments for items with recordings
        if item.recording_url and item.ai_assessed_at:
            # Get scores (use get_score_with_fallback for safety)
            pron = float(get_score_with_fallback(
                item, "pronunciation_score", "pronunciation_score", db, ai_feedback_data={}
            ))
            acc = float(get_score_with_fallback(
                item, "accuracy_score", "accuracy_score", db, ai_feedback_data={}
            ))
            flu = float(get_score_with_fallback(
                item, "fluency_score", "fluency_score", db, ai_feedback_data={}
            ))
            comp = float(get_score_with_fallback(
                item, "completeness_score", "completeness_score", db, ai_feedback_data={}
            ))

            # Generate and store comment
            comment = generate_item_comment(pron, acc, flu, comp)
            item.teacher_feedback = comment

    perf.checkpoint("Item Comments Generated")

# 6.6. Generate assignment feedback
with start_span("Generate Assignment Feedback"):
    completed_items_count = len([i for i in item_progress_list if i.recording_url])

    assignment_feedback = generate_assignment_feedback(
        total_items=len(item_progress_list),
        completed_items=completed_items_count,
        avg_score=total_score,
        avg_pronunciation=avg_pronunciation,
        avg_fluency=avg_fluency,
        avg_accuracy=avg_accuracy,
        avg_completeness=avg_completeness,
    )

    student_assignment.feedback = assignment_feedback
    perf.checkpoint("Assignment Feedback Generated")
```

**Update the results.append() call (around line 2910) to include new fields:**

```python
results.append(
    StudentBatchGradingResult(
        student_id=student.id,
        student_name=student.name,
        total_score=round(total_score, 1),
        missing_items=missing_count,
        total_items=len(item_progress_list),  # NEW
        completed_items=len([i for i in item_progress_list if i.recording_url]),  # NEW
        avg_pronunciation=round(avg_pronunciation, 1),
        avg_accuracy=round(avg_accuracy, 1),
        avg_fluency=round(avg_fluency, 1),
        avg_completeness=round(avg_completeness, 1),
        feedback=student_assignment.feedback,  # NEW
        status=student_assignment.status.value,
    )
)
```

### 2. Add Required Imports

At the top of assignments.py (around line 10), ensure these imports exist:

```python
import httpx
from decimal import Decimal
import json
from datetime import datetime, timezone
```

## Testing Strategy

1. **Run new test file first (TDD)**:
   ```bash
   pytest backend/tests/integration/api/test_batch_grading_complete.py -v
   ```

2. **Ensure existing tests still pass**:
   ```bash
   pytest backend/tests/integration/api/test_batch_ai_grading.py -v
   ```

3. **Check all assignment tests**:
   ```bash
   pytest backend/tests/integration/api/ -k batch -v
   ```

## Success Criteria

✅ All new tests in `test_batch_grading_complete.py` pass
✅ All existing tests in `test_batch_ai_grading.py` still pass
✅ API response includes `completed_items` and `feedback` fields
✅ Database stores:
  - Item comments in `StudentItemProgress.teacher_feedback`
  - Assignment feedback in `StudentAssignment.feedback`
✅ Missing AI assessments are automatically triggered
✅ No crashes when AI assessment fails (graceful error handling)

## Edge Cases to Handle

1. **AI Assessment Failure**: Catch exceptions, log error, continue with 0 scores
2. **No Recording URL**: Skip assessment, no comment generated
3. **All Items Missing**: Feedback should mention 0 completion
4. **Partial Dimensions**: Use available scores only (already handled by existing code)

## Performance Considerations

- Use `await trigger_ai_assessment_for_item()` for async execution
- Batch AI assessments can be done sequentially (already inside student loop)
- Keep existing performance monitoring with `start_span()` and `perf.checkpoint()`

## Rollback Plan

If implementation fails:
1. Revert `assignments.py` changes
2. Keep test file for future reference
3. No database migration to rollback (using existing fields)
