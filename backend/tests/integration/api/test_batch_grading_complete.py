"""
Comprehensive TDD Tests for Complete AI Batch Grading Workflow

This test suite covers the complete AI batch grading feature including:
1. Recording check and statistics
2. Automatic AI assessment for missing scores
3. Item-level comment generation
4. Assignment-level feedback generation
5. Score calculation and storage

Backend API endpoint: POST /api/teachers/assignments/{assignment_id}/batch-grade
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Assignment,
    Content,
    ContentItem,
    AssignmentContent,
    StudentAssignment,
    StudentItemProgress,
    AssignmentStatus,
)
from auth import get_password_hash, create_access_token
from unittest.mock import AsyncMock


def setup_async_httpx_mock(mock_httpx: MagicMock):
    """Helper to setup async httpx client mock correctly"""
    mock_response = MagicMock()
    mock_response.content = b"fake_audio_data"
    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_httpx.return_value = mock_client_instance


@pytest.fixture
def auth_teacher(shared_test_session: Session):
    """Create authenticated teacher for all tests"""
    teacher = Teacher(
        email="teacher_complete@test.com",
        name="Test Teacher Complete",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def auth_headers(auth_teacher: Teacher):
    """Create auth headers for API requests"""
    access_token = create_access_token(
        data={"sub": str(auth_teacher.id), "type": "teacher"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def setup_complete_grading_env(shared_test_session: Session, auth_teacher: Teacher):
    """Setup complete test environment for AI grading"""
    # Create classroom
    classroom = Classroom(
        name="Complete Grading Classroom",
        teacher_id=auth_teacher.id,
    )
    shared_test_session.add(classroom)
    shared_test_session.commit()
    shared_test_session.refresh(classroom)

    # Create assignment
    assignment = Assignment(
        title="Complete AI Grading Test",
        classroom_id=classroom.id,
        teacher_id=auth_teacher.id,
        due_date=datetime.now(timezone.utc),
    )
    shared_test_session.add(assignment)
    shared_test_session.commit()
    shared_test_session.refresh(assignment)

    # Create Program and Lesson
    from models import Program, Lesson

    program = Program(
        name="Complete Test Program",
        teacher_id=auth_teacher.id,
        classroom_id=classroom.id,
    )
    shared_test_session.add(program)
    shared_test_session.commit()
    shared_test_session.refresh(program)

    lesson = Lesson(
        program_id=program.id,
        name="Complete Test Lesson",
    )
    shared_test_session.add(lesson)
    shared_test_session.commit()
    shared_test_session.refresh(lesson)

    # Create content with 5 items
    content = Content(
        lesson_id=lesson.id,
        title="Complete Test Content",
        type="reading_assessment",
    )
    shared_test_session.add(content)
    shared_test_session.commit()
    shared_test_session.refresh(content)

    # Link assignment to content
    ac = AssignmentContent(
        assignment_id=assignment.id,
        content_id=content.id,
        order_index=1,
    )
    shared_test_session.add(ac)
    shared_test_session.commit()

    # Create 5 content items
    items = []
    for i in range(5):
        item = ContentItem(
            content_id=content.id,
            order_index=i,
            text=f"Test sentence {i+1}",
            translation=f"測試句子 {i+1}",
        )
        shared_test_session.add(item)
        items.append(item)
    shared_test_session.commit()

    for item in items:
        shared_test_session.refresh(item)

    return {
        "teacher": auth_teacher,
        "classroom": classroom,
        "assignment": assignment,
        "content": content,
        "items": items,
    }


def create_student_with_items(
    db: Session,
    classroom: Classroom,
    assignment: Assignment,
    items: list[ContentItem],
    student_name: str,
    student_number: str,
) -> tuple[Student, StudentAssignment]:
    """Helper: Create student with assignment"""
    from datetime import date

    student = Student(
        email=f"{student_number}@complete.test",
        name=student_name,
        student_number=student_number,
        password_hash=get_password_hash("password123"),
        birthdate=date(2010, 1, 1),
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # Add to classroom
    cs = ClassroomStudent(
        classroom_id=classroom.id,
        student_id=student.id,
    )
    db.add(cs)
    db.commit()

    # Create student assignment
    sa = StudentAssignment(
        student_id=student.id,
        assignment_id=assignment.id,
        classroom_id=classroom.id,
        title=assignment.title,
        status=AssignmentStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)

    return student, sa


# ============================================================================
# TEST 1: All Items Have AI Scores - Generate Comments and Feedback
# ============================================================================
def test_complete_grading_all_items_have_scores(
    test_client: TestClient,
    shared_test_session: Session,
    setup_complete_grading_env,
    auth_headers,
):
    """
    Test Requirement 1, 3, 4, 5:
    - Check recordings (all 5 have recordings)
    - All items already have AI scores (no new assessment needed)
    - Generate item-level comments
    - Calculate average score
    - Generate assignment feedback
    """
    data = setup_complete_grading_env

    student, sa = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Complete Student",
        "CS001",
    )

    # Add all items with recordings and AI scores
    for item in data["items"]:
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=item.id,
            recording_url=f"https://example.com/recording_{item.id}.mp3",
            pronunciation_score=Decimal("85.0"),
            accuracy_score=Decimal("88.0"),
            fluency_score=Decimal("90.0"),
            completeness_score=Decimal("87.0"),
            ai_assessed_at=datetime.now(timezone.utc),
            status="SUBMITTED",
        )
        shared_test_session.add(progress)
    shared_test_session.commit()

    # Call batch grading API
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "return_for_correction": {},
        },
    )

    # Assert response
    assert response.status_code == 200, f"API failed: {response.text}"
    result = response.json()

    student_result = result["results"][0]
    assert student_result["student_name"] == "Complete Student"
    assert student_result["missing_items"] == 0
    assert student_result["completed_items"] == 5  # NEW: Completed items count

    # Expected score: (85 + 88 + 90 + 87) / 4 = 87.5
    expected_score = (85 + 88 + 90 + 87) / 4
    assert abs(student_result["total_score"] - expected_score) < 0.5

    # NEW: Check feedback exists
    assert "feedback" in student_result
    assert student_result["feedback"] is not None
    assert len(student_result["feedback"]) > 0
    assert "完成" in student_result["feedback"]  # Should mention completion

    # Verify database
    shared_test_session.refresh(sa)
    assert sa.score is not None
    assert sa.feedback is not None  # NEW: Assignment feedback stored
    assert len(sa.feedback) > 0

    # Verify item comments generated
    item_progress_list = (
        shared_test_session.query(StudentItemProgress)
        .filter(StudentItemProgress.student_assignment_id == sa.id)
        .all()
    )

    for item_progress in item_progress_list:
        # NEW: Each item should have a comment
        assert item_progress.teacher_feedback is not None
        assert len(item_progress.teacher_feedback) > 0
        # Comment should be in Chinese
        assert any(
            word in item_progress.teacher_feedback for word in ["發音", "流暢", "準確", "完整"]
        )


# ============================================================================
# TEST 2: Some Items Missing AI Scores - Trigger Assessment
# ============================================================================
@patch("routers.speech_assessment.convert_audio_to_wav")
@patch("routers.speech_assessment.assess_pronunciation")
@patch("httpx.AsyncClient")
def test_complete_grading_trigger_missing_assessments(
    mock_httpx: MagicMock,
    mock_assess: MagicMock,
    mock_convert: MagicMock,
    test_client: TestClient,
    shared_test_session: Session,
    setup_complete_grading_env,
    auth_headers,
):
    """
    Test Requirement 2:
    - 3 items have recordings but NO AI assessment
    - Should automatically trigger AI assessment
    - Then generate comments and feedback
    """
    data = setup_complete_grading_env

    student, sa = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Missing Assessment Student",
        "CS002",
    )

    # Setup async httpx mock
    setup_async_httpx_mock(mock_httpx)
    mock_convert.return_value = b"fake_wav_data"

    # Mock Azure Speech API response
    mock_assess.return_value = {
        "accuracy_score": 85.0,
        "fluency_score": 88.0,
        "pronunciation_score": 90.0,
        "completeness_score": 87.0,
        "recognized_text": "Test recognized text",
        "words": [],
    }

    # Add 2 items with AI scores
    for i in range(2):
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=data["items"][i].id,
            recording_url=f"https://example.com/recording_{i}.mp3",
            pronunciation_score=Decimal("85.0"),
            accuracy_score=Decimal("88.0"),
            fluency_score=Decimal("90.0"),
            completeness_score=Decimal("87.0"),
            ai_assessed_at=datetime.now(timezone.utc),
            status="SUBMITTED",
        )
        shared_test_session.add(progress)

    # Add 3 items with recordings but NO AI scores
    for i in range(2, 5):
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=data["items"][i].id,
            recording_url=f"https://example.com/recording_{i}.mp3",
            pronunciation_score=None,  # NO AI SCORE
            accuracy_score=None,
            fluency_score=None,
            completeness_score=None,
            ai_assessed_at=None,
            status="SUBMITTED",
        )
        shared_test_session.add(progress)

    shared_test_session.commit()

    # Call batch grading API
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "return_for_correction": {},
        },
    )

    # Assert response
    assert response.status_code == 200
    result = response.json()

    # NEW: AI assessment should have been triggered 3 times
    assert mock_assess.call_count == 3

    student_result = result["results"][0]
    assert student_result["completed_items"] == 5
    assert student_result["missing_items"] == 0  # All have recordings now

    # Verify database - all items should now have AI scores
    item_progress_list = (
        shared_test_session.query(StudentItemProgress)
        .filter(StudentItemProgress.student_assignment_id == sa.id)
        .all()
    )

    for item_progress in item_progress_list:
        # All should have scores now
        assert item_progress.pronunciation_score is not None
        assert item_progress.accuracy_score is not None
        # All should have comments
        assert item_progress.teacher_feedback is not None


# ============================================================================
# TEST 3: Mixed Scenario - Some Missing Recordings, Some Missing Scores
# ============================================================================
@patch("routers.speech_assessment.convert_audio_to_wav")
@patch("routers.speech_assessment.assess_pronunciation")
@patch("httpx.AsyncClient")
def test_complete_grading_mixed_scenario(
    mock_httpx: MagicMock,
    mock_assess: MagicMock,
    mock_convert: MagicMock,
    test_client: TestClient,
    shared_test_session: Session,
    setup_complete_grading_env,
    auth_headers,
):
    """
    Test Requirements 1-5 Combined:
    - Item 1-2: Have recordings + AI scores (generate comments)
    - Item 3: Has recording but NO AI score (trigger assessment + generate comment)
    - Item 4-5: NO recordings (skip, count as missing)
    """
    data = setup_complete_grading_env

    student, sa = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Mixed Scenario Student",
        "CS003",
    )

    # Setup async httpx mock
    setup_async_httpx_mock(mock_httpx)
    mock_convert.return_value = b"fake_wav_data"

    mock_assess.return_value = {
        "accuracy_score": 82.0,
        "fluency_score": 85.0,
        "pronunciation_score": 87.0,
        "completeness_score": 84.0,
        "recognized_text": "Test",
        "words": [],
    }

    # Item 1-2: Complete with scores
    for i in range(2):
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=data["items"][i].id,
            recording_url=f"https://example.com/recording_{i}.mp3",
            pronunciation_score=Decimal("90.0"),
            accuracy_score=Decimal("92.0"),
            fluency_score=Decimal("88.0"),
            completeness_score=Decimal("91.0"),
            ai_assessed_at=datetime.now(timezone.utc),
            status="SUBMITTED",
        )
        shared_test_session.add(progress)

    # Item 3: Has recording but no AI score
    progress = StudentItemProgress(
        student_assignment_id=sa.id,
        content_item_id=data["items"][2].id,
        recording_url="https://example.com/recording_2.mp3",
        pronunciation_score=None,
        accuracy_score=None,
        fluency_score=None,
        completeness_score=None,
        ai_assessed_at=None,
        status="SUBMITTED",
    )
    shared_test_session.add(progress)

    # Item 4-5: No recordings
    for i in range(3, 5):
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=data["items"][i].id,
            recording_url=None,
            status="NOT_STARTED",
        )
        shared_test_session.add(progress)

    shared_test_session.commit()

    # Call API
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "return_for_correction": {},
        },
    )

    # Assert
    assert response.status_code == 200
    result = response.json()

    # AI assessment triggered once for item 3
    assert mock_assess.call_count == 1

    student_result = result["results"][0]
    assert student_result["completed_items"] == 3  # Items 1-3
    assert student_result["missing_items"] == 2  # Items 4-5

    # Check feedback mentions partial completion
    assert "feedback" in student_result
    assert "3/5" in student_result["feedback"] or "3" in student_result["feedback"]

    # Verify item comments
    item_progress_list = (
        shared_test_session.query(StudentItemProgress)
        .filter(StudentItemProgress.student_assignment_id == sa.id)
        .all()
    )

    for item_progress in item_progress_list:
        if item_progress.recording_url:
            # Items with recordings should have comments
            assert item_progress.teacher_feedback is not None
        else:
            # Items without recordings should have no comment
            assert item_progress.teacher_feedback is None


# ============================================================================
# TEST 4: Item Comment Generation Accuracy
# ============================================================================
def test_item_comment_generation_patterns(
    test_client: TestClient,
    shared_test_session: Session,
    setup_complete_grading_env,
    auth_headers,
):
    """
    Test Requirement 3: Item-level comment generation
    - High scores (90+) → positive comments
    - Low pronunciation (<70) → pronunciation feedback
    - Low fluency (<70) → fluency feedback
    - Low completeness (<70) → completeness feedback
    """
    data = setup_complete_grading_env

    student, sa = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Comment Test Student",
        "CS004",
    )

    # Different score patterns for testing comment generation
    test_cases = [
        # (pronunciation, accuracy, fluency, completeness, expected_keywords)
        (95, 96, 97, 98, ["標準", "流暢", "優秀"]),  # High scores
        (65, 85, 85, 85, ["加強", "練習"]),  # Low pronunciation
        (85, 85, 65, 85, ["流暢"]),  # Low fluency
        (85, 85, 85, 65, ["完整"]),  # Low completeness
        (60, 65, 60, 62, ["加強", "練習", "提升"]),  # Low all
    ]

    for i, (pron, acc, flu, comp, keywords) in enumerate(test_cases):
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=data["items"][i].id,
            recording_url=f"https://example.com/recording_{i}.mp3",
            pronunciation_score=Decimal(str(pron)),
            accuracy_score=Decimal(str(acc)),
            fluency_score=Decimal(str(flu)),
            completeness_score=Decimal(str(comp)),
            ai_assessed_at=datetime.now(timezone.utc),
            status="SUBMITTED",
        )
        shared_test_session.add(progress)

    shared_test_session.commit()

    # Call API
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "return_for_correction": {},
        },
    )

    assert response.status_code == 200

    # Verify comments match score patterns
    item_progress_list = (
        shared_test_session.query(StudentItemProgress)
        .filter(StudentItemProgress.student_assignment_id == sa.id)
        .order_by(StudentItemProgress.content_item_id)
        .all()
    )

    for i, item_progress in enumerate(item_progress_list):
        comment = item_progress.teacher_feedback
        assert comment is not None
        _, _, _, _, expected_keywords = test_cases[i]

        # Check if comment contains expected keywords
        assert any(
            keyword in comment for keyword in expected_keywords
        ), f"Item {i}: Expected keywords {expected_keywords} in comment: {comment}"


# ============================================================================
# TEST 5: Assignment Feedback Generation
# ============================================================================
def test_assignment_feedback_generation(
    test_client: TestClient,
    shared_test_session: Session,
    setup_complete_grading_env,
    auth_headers,
):
    """
    Test Requirement 5: Assignment-level feedback generation
    - Completion rate (5/5 vs 3/5)
    - Overall performance (high vs low scores)
    - Suggestions based on performance
    """
    data = setup_complete_grading_env

    # Test Case 1: Perfect completion, high scores
    student1, sa1 = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Perfect Student",
        "CS005",
    )

    for item in data["items"]:
        progress = StudentItemProgress(
            student_assignment_id=sa1.id,
            content_item_id=item.id,
            recording_url=f"https://example.com/recording_{item.id}.mp3",
            pronunciation_score=Decimal("95.0"),
            accuracy_score=Decimal("96.0"),
            fluency_score=Decimal("97.0"),
            completeness_score=Decimal("98.0"),
            ai_assessed_at=datetime.now(timezone.utc),
            status="SUBMITTED",
        )
        shared_test_session.add(progress)

    shared_test_session.commit()

    # Call API
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "return_for_correction": {},
        },
    )

    assert response.status_code == 200
    result = response.json()

    student_result = result["results"][0]
    feedback = student_result["feedback"]

    # Perfect student feedback should be positive
    assert "優秀" in feedback or "良好" in feedback or "保持" in feedback
    assert "5" in feedback  # Should mention total items
    assert "完成" in feedback

    # Verify database
    shared_test_session.refresh(sa1)
    assert sa1.feedback == feedback
    assert len(sa1.feedback) > 20  # Substantial feedback


# ============================================================================
# TEST 6: Batch Processing with Multiple Students
# ============================================================================
@patch("routers.speech_assessment.convert_audio_to_wav")
@patch("routers.speech_assessment.assess_pronunciation")
@patch("httpx.AsyncClient")
def test_batch_grading_multiple_students_complete_workflow(
    mock_httpx: MagicMock,
    mock_assess: MagicMock,
    mock_convert: MagicMock,
    test_client: TestClient,
    shared_test_session: Session,
    setup_complete_grading_env,
    auth_headers,
):
    """
    Integration Test: Batch process 3 students with different scenarios
    - Student 1: All complete with scores
    - Student 2: Some missing AI scores
    - Student 3: Some missing recordings
    """
    data = setup_complete_grading_env

    # Setup async httpx mock
    setup_async_httpx_mock(mock_httpx)
    mock_convert.return_value = b"fake_wav_data"

    mock_assess.return_value = {
        "accuracy_score": 85.0,
        "fluency_score": 88.0,
        "pronunciation_score": 90.0,
        "completeness_score": 87.0,
        "recognized_text": "Test",
        "words": [],
    }

    # Student 1: Complete
    student1, sa1 = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Student Complete",
        "CS006",
    )

    for item in data["items"]:
        progress = StudentItemProgress(
            student_assignment_id=sa1.id,
            content_item_id=item.id,
            recording_url=f"https://example.com/recording_{item.id}.mp3",
            pronunciation_score=Decimal("90.0"),
            accuracy_score=Decimal("92.0"),
            fluency_score=Decimal("88.0"),
            completeness_score=Decimal("91.0"),
            ai_assessed_at=datetime.now(timezone.utc),
            status="SUBMITTED",
        )
        shared_test_session.add(progress)

    # Student 2: Missing AI scores on 2 items
    student2, sa2 = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Student Missing Scores",
        "CS007",
    )

    for i, item in enumerate(data["items"]):
        if i < 3:
            # Has scores
            progress = StudentItemProgress(
                student_assignment_id=sa2.id,
                content_item_id=item.id,
                recording_url=f"https://example.com/recording_{item.id}.mp3",
                pronunciation_score=Decimal("85.0"),
                accuracy_score=Decimal("87.0"),
                fluency_score=Decimal("84.0"),
                completeness_score=Decimal("86.0"),
                ai_assessed_at=datetime.now(timezone.utc),
                status="SUBMITTED",
            )
        else:
            # Missing scores
            progress = StudentItemProgress(
                student_assignment_id=sa2.id,
                content_item_id=item.id,
                recording_url=f"https://example.com/recording_{item.id}.mp3",
                status="SUBMITTED",
            )
        shared_test_session.add(progress)

    # Student 3: Missing recordings on 2 items
    student3, sa3 = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Student Missing Recordings",
        "CS008",
    )

    for i, item in enumerate(data["items"]):
        if i < 3:
            progress = StudentItemProgress(
                student_assignment_id=sa3.id,
                content_item_id=item.id,
                recording_url=f"https://example.com/recording_{item.id}.mp3",
                pronunciation_score=Decimal("88.0"),
                accuracy_score=Decimal("90.0"),
                fluency_score=Decimal("86.0"),
                completeness_score=Decimal("89.0"),
                ai_assessed_at=datetime.now(timezone.utc),
                status="SUBMITTED",
            )
        else:
            progress = StudentItemProgress(
                student_assignment_id=sa3.id,
                content_item_id=item.id,
                recording_url=None,
                status="NOT_STARTED",
            )
        shared_test_session.add(progress)

    shared_test_session.commit()

    # Call API
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "return_for_correction": {},
        },
    )

    # Assert
    assert response.status_code == 200
    result = response.json()

    assert result["total_students"] == 3
    assert result["processed"] == 3

    # AI assessment should have been called for student 2 (2 items)
    assert mock_assess.call_count == 2

    # Verify each student
    results_by_name = {r["student_name"]: r for r in result["results"]}

    # Student 1: Complete
    s1 = results_by_name["Student Complete"]
    assert s1["completed_items"] == 5
    assert s1["missing_items"] == 0
    assert s1["feedback"] is not None
    assert "5" in s1["feedback"]

    # Student 2: Missing scores (now assessed)
    s2 = results_by_name["Student Missing Scores"]
    assert s2["completed_items"] == 5
    assert s2["missing_items"] == 0

    # Student 3: Missing recordings
    s3 = results_by_name["Student Missing Recordings"]
    assert s3["completed_items"] == 3
    assert s3["missing_items"] == 2
    assert "3/5" in s3["feedback"] or "3" in s3["feedback"]

    # Verify all students have feedback
    for student_result in result["results"]:
        assert "feedback" in student_result
        assert student_result["feedback"] is not None
        assert len(student_result["feedback"]) > 0


# ============================================================================
# TEST 7: Error Handling - AI Assessment Failure
# ============================================================================
@patch("routers.speech_assessment.convert_audio_to_wav")
@patch("routers.speech_assessment.assess_pronunciation")
@patch("httpx.AsyncClient")
def test_batch_grading_ai_assessment_failure_graceful(
    mock_httpx: MagicMock,
    mock_assess: MagicMock,
    mock_convert: MagicMock,
    test_client: TestClient,
    shared_test_session: Session,
    setup_complete_grading_env,
    auth_headers,
):
    """
    Test error handling when AI assessment fails
    - Should continue with other items
    - Should not crash the entire batch grading
    - Failed items should be logged but not break the process
    """
    data = setup_complete_grading_env

    # Setup async httpx mock
    setup_async_httpx_mock(mock_httpx)
    mock_convert.return_value = b"fake_wav_data"

    # Mock AI assessment to raise exception
    mock_assess.side_effect = Exception("Azure API Error")

    student, sa = create_student_with_items(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Error Test Student",
        "CS009",
    )

    # Add items with missing AI scores
    for item in data["items"]:
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=item.id,
            recording_url=f"https://example.com/recording_{item.id}.mp3",
            status="SUBMITTED",
        )
        shared_test_session.add(progress)

    shared_test_session.commit()

    # Call API - should not crash
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "return_for_correction": {},
        },
    )

    # Should return 200 even if AI assessment fails
    assert response.status_code == 200
    result = response.json()

    # Student should be processed (with 0 scores for failed assessments)
    assert result["total_students"] == 1
    assert result["processed"] == 1

    student_result = result["results"][0]
    # Should count items without successful assessment as missing
    assert student_result["missing_items"] > 0
