#!/usr/bin/env python3
"""
Test script to verify recording playback functionality after refactoring.
Tests that recordings are correctly stored and retrieved from item.recording_url.
"""

import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from models import (
    Student,
    Teacher,
    Classroom,
    Assignment,
    Content,
    ContentItem,
    StudentItemProgress,
    StudentContentProgress,
)


@pytest.fixture
def setup_test_data(test_db: Session):
    """Setup test data for recording playback tests."""
    # Create teacher
    teacher = Teacher(
        google_id="teacher_123", email="teacher@test.com", name="Test Teacher"
    )
    test_db.add(teacher)

    # Create classroom
    classroom = Classroom(name="Test Classroom", teacher=teacher, join_code="TEST123")
    test_db.add(classroom)

    # Create student
    student = Student(
        google_id="student_123",
        email="student@test.com",
        name="Test Student",
        display_name="TestStudent",
    )
    test_db.add(student)
    test_db.flush()

    # Add student to classroom
    classroom.students.append(student)

    # Create content with multiple items (grouped questions)
    content = Content(
        title="Grouped Questions Content",
        type="grouped_questions",
        teacher=teacher,
        is_public=False,
    )
    test_db.add(content)
    test_db.flush()

    # Create content items
    items = []
    for i in range(3):
        item = ContentItem(
            content=content,
            type="question",
            text=f"Question {i+1}",
            translation=f"翻譯 {i+1}",
            order=i,
        )
        test_db.add(item)
        items.append(item)

    test_db.flush()

    # Create assignment
    assignment = Assignment(
        title="Test Assignment", classroom=classroom, teacher=teacher, status="ASSIGNED"
    )
    test_db.add(assignment)
    test_db.flush()

    # Add content to assignment
    assignment.contents.append(content)

    # Create StudentContentProgress
    progress = StudentContentProgress(
        student=student, assignment=assignment, content=content, status="IN_PROGRESS"
    )
    test_db.add(progress)
    test_db.flush()

    # Create StudentItemProgress with recordings for each item
    item_progresses = []
    for i, item in enumerate(items):
        item_progress = StudentItemProgress(
            student_progress=progress,
            content_item=item,
            status="SUBMITTED" if i < 2 else "NOT_STARTED",
            recording_url=f"https://storage.googleapis.com/recording_{i+1}.webm"
            if i < 2
            else None,
            ai_assessment={
                "accuracy_score": 85 + i,
                "fluency_score": 80 + i,
                "pronunciation_score": 88 + i,
            }
            if i < 2
            else None,
        )
        test_db.add(item_progress)
        item_progresses.append(item_progress)

    test_db.commit()

    return {
        "student": student,
        "assignment": assignment,
        "content": content,
        "items": items,
        "progress": progress,
        "item_progresses": item_progresses,
    }


def test_get_activity_with_recording_urls(test_client, test_db, setup_test_data):
    """Test that activities endpoint returns recording URLs in items."""
    data = setup_test_data
    student = data["student"]
    assignment = data["assignment"]

    # Mock authentication
    with patch("routers.auth.verify_student_token") as mock_verify:
        mock_verify.return_value = {"sub": student.google_id, "email": student.email}

        response = test_client.get(
            f"/api/students/assignments/{assignment.id}/activities",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        result = response.json()

        # Check that activities are returned
        assert "activities" in result
        assert len(result["activities"]) > 0

        # Find the grouped questions activity
        activity = result["activities"][0]
        assert activity["type"] == "grouped_questions"

        # Verify items have recording_url field
        assert "items" in activity
        assert len(activity["items"]) == 3

        # Check first two items have recording URLs
        assert (
            activity["items"][0]["recording_url"]
            == "https://storage.googleapis.com/recording_1.webm"
        )
        assert (
            activity["items"][1]["recording_url"]
            == "https://storage.googleapis.com/recording_2.webm"
        )
        assert activity["items"][2]["recording_url"] == ""  # Not recorded yet

        # Verify AI assessments are in items
        assert "ai_assessment" in activity["items"][0]
        assert activity["items"][0]["ai_assessment"]["accuracy_score"] == 85
        assert "ai_assessment" in activity["items"][1]
        assert activity["items"][1]["ai_assessment"]["fluency_score"] == 81


def test_upload_recording_updates_item(test_client, test_db, setup_test_data):
    """Test that uploading a recording updates the correct item's recording_url."""
    data = setup_test_data
    student = data["student"]
    assignment = data["assignment"]
    items = data["items"]

    # Mock authentication and GCS upload
    with patch("routers.auth.verify_student_token") as mock_verify, patch(
        "routers.students.upload_audio_to_gcs"
    ) as mock_upload:
        mock_verify.return_value = {"sub": student.google_id, "email": student.email}
        mock_upload.return_value = "https://storage.googleapis.com/new_recording.webm"

        # Upload recording for the third item (index 2)
        response = test_client.post(
            "/api/students/upload-recording",
            files={"audio_file": ("recording.webm", b"fake_audio_data", "audio/webm")},
            data={
                "assignment_id": str(assignment.id),
                "content_item_id": str(items[2].id),  # Third item
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        result = response.json()
        assert (
            result["audio_url"] == "https://storage.googleapis.com/new_recording.webm"
        )

        # Verify the item progress was updated
        item_progress = (
            test_db.query(StudentItemProgress)
            .filter_by(content_item_id=items[2].id)
            .first()
        )
        assert item_progress is not None
        assert (
            item_progress.recording_url
            == "https://storage.googleapis.com/new_recording.webm"
        )
        assert item_progress.status == "SUBMITTED"


def test_no_recordings_array_in_response(test_client, test_db, setup_test_data):
    """Test that the API no longer returns a recordings array at activity level."""
    data = setup_test_data
    student = data["student"]
    assignment = data["assignment"]

    with patch("routers.auth.verify_student_token") as mock_verify:
        mock_verify.return_value = {"sub": student.google_id, "email": student.email}

        response = test_client.get(
            f"/api/students/assignments/{assignment.id}/activities",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        result = response.json()

        activity = result["activities"][0]

        # Verify no recordings array at activity level
        assert "recordings" not in activity or activity["recordings"] == []

        # All recording data should be in items
        assert all("recording_url" in item for item in activity["items"])


def test_playback_after_refresh(test_client, test_db, setup_test_data):
    """Test that recordings can be played back after page refresh."""
    data = setup_test_data
    student = data["student"]
    assignment = data["assignment"]

    # First request - simulating initial load
    with patch("routers.auth.verify_student_token") as mock_verify:
        mock_verify.return_value = {"sub": student.google_id, "email": student.email}

        response1 = test_client.get(
            f"/api/students/assignments/{assignment.id}/activities",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response1.status_code == 200
        result1 = response1.json()

        # Store recording URLs from first request
        activity1 = result1["activities"][0]
        recording_urls_1 = [item["recording_url"] for item in activity1["items"]]

        # Second request - simulating page refresh
        response2 = test_client.get(
            f"/api/students/assignments/{assignment.id}/activities",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response2.status_code == 200
        result2 = response2.json()

        # Verify same recording URLs are returned
        activity2 = result2["activities"][0]
        recording_urls_2 = [item["recording_url"] for item in activity2["items"]]

        assert recording_urls_1 == recording_urls_2
        assert recording_urls_1[0] == "https://storage.googleapis.com/recording_1.webm"
        assert recording_urls_1[1] == "https://storage.googleapis.com/recording_2.webm"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
