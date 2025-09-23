"""
測試學生查看老師評語功能
"""
import pytest
from datetime import datetime

from models import (
    Student,
    Teacher,
    Assignment,
    StudentAssignment,
    Content,
    ContentItem,
    StudentContentProgress,
    StudentItemProgress,
    AssignmentStatus,
    ContentType,
    AssignmentContent,
)
from auth import create_access_token


@pytest.fixture
def test_data(test_session):
    """Create test data with teacher feedback"""
    # Create student and teacher
    student = Student(
        id=1, name="Test Student", email="student@test.com", is_active=True
    )
    teacher = Teacher(
        id=1, name="Test Teacher", email="teacher@test.com", is_active=True
    )
    test_session.add_all([student, teacher])
    test_session.commit()

    # Create assignment
    assignment = Assignment(
        id=1, title="Test Assignment", teacher_id=teacher.id, is_active=True
    )
    test_session.add(assignment)
    test_session.commit()

    # Create student assignment
    student_assignment = StudentAssignment(
        id=1,
        student_id=student.id,
        assignment_id=assignment.id,
        title="Test Assignment",
        status=AssignmentStatus.IN_PROGRESS,
        is_active=True,
    )
    test_session.add(student_assignment)
    test_session.commit()

    # Create content with items
    content = Content(
        id=1,
        type=ContentType.READING_ASSESSMENT,
        title="Reading Test",
        content="Test content",
        is_active=True,
    )
    test_session.add(content)
    test_session.commit()

    # Create assignment content link
    assignment_content = AssignmentContent(
        assignment_id=assignment.id,
        content_id=content.id,
        order_index=0,
        is_active=True,
    )
    test_session.add(assignment_content)
    test_session.commit()

    # Create content items
    items = []
    for i in range(3):
        item = ContentItem(
            content_id=content.id,
            text=f"Question {i+1}",
            translation=f"題目 {i+1}",
            order_index=i,
        )
        test_session.add(item)
        items.append(item)

    test_session.commit()
    for item in items:
        test_session.refresh(item)

    # Create student content progress
    progress = StudentContentProgress(
        student_assignment_id=student_assignment.id,
        content_id=content.id,
        order_index=0,
        status=AssignmentStatus.IN_PROGRESS,
    )
    test_session.add(progress)
    test_session.commit()

    # Create student item progress with teacher feedback
    item_progress_list = []
    teacher_feedback_data = [
        {"feedback": "Great pronunciation! Keep it up.", "passed": True, "score": 95},
        {"feedback": "注意 'the' 的發音，應該是 /ðə/。", "passed": True, "score": 85},
        {"feedback": "需要更多練習。請注意語速。", "passed": False, "score": 65},
    ]

    for i, item in enumerate(items):
        feedback = teacher_feedback_data[i]
        item_progress = StudentItemProgress(
            student_assignment_id=student_assignment.id,
            content_item_id=item.id,
            status="COMPLETED",
            teacher_feedback=feedback["feedback"],
            teacher_passed=feedback["passed"],
            teacher_review_score=feedback["score"],
            teacher_reviewed_at=datetime.utcnow(),
            teacher_id=teacher.id,
            review_status="REVIEWED",
        )
        test_session.add(item_progress)
        item_progress_list.append(item_progress)

    test_session.commit()

    # Create access token
    token = create_access_token(data={"sub": str(student.id), "type": "student"})

    return {
        "student": student,
        "teacher": teacher,
        "assignment": assignment,
        "student_assignment": student_assignment,
        "content": content,
        "items": items,
        "item_progress": item_progress_list,
        "token": token,
    }


class TestStudentTeacherFeedback:
    """Test student viewing teacher feedback"""

    def test_get_activities_with_teacher_feedback(self, test_client, test_data):
        """Test that activities API returns teacher feedback"""
        response = test_client.get(
            f"/api/students/assignments/{test_data['student_assignment'].id}/activities",
            headers={"Authorization": f"Bearer {test_data['token']}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check basic structure
        assert "activities" in data
        assert len(data["activities"]) > 0

        activity = data["activities"][0]
        assert "items" in activity
        assert len(activity["items"]) == 3

        # Check teacher feedback in items
        for i, item in enumerate(activity["items"]):
            assert "teacher_feedback" in item
            assert "teacher_passed" in item
            assert "teacher_review_score" in item
            assert "teacher_reviewed_at" in item
            assert "review_status" in item

            # Verify specific feedback content
            if i == 0:
                assert item["teacher_feedback"] == "Great pronunciation! Keep it up."
                assert item["teacher_passed"] is True
                assert item["teacher_review_score"] == 95.0
                assert item["review_status"] == "REVIEWED"
            elif i == 1:
                assert item["teacher_feedback"] == "注意 'the' 的發音，應該是 /ðə/。"
                assert item["teacher_passed"] is True
                assert item["teacher_review_score"] == 85.0
            elif i == 2:
                assert item["teacher_feedback"] == "需要更多練習。請注意語速。"
                assert item["teacher_passed"] is False
                assert item["teacher_review_score"] == 65.0

    def test_teacher_feedback_null_handling(self, test_client, test_data, test_session):
        """Test handling of items without teacher feedback"""
        # Create an item without teacher feedback
        new_item = ContentItem(
            content_id=test_data["content"].id,
            text="Question 4",
            translation="題目 4",
            order_index=3,
        )
        test_session.add(new_item)
        test_session.commit()
        test_session.refresh(new_item)

        # Create progress without teacher feedback
        item_progress = StudentItemProgress(
            student_assignment_id=test_data["student_assignment"].id,
            content_item_id=new_item.id,
            status="NOT_STARTED",
        )
        test_session.add(item_progress)
        test_session.commit()

        # Get activities
        response = test_client.get(
            f"/api/students/assignments/{test_data['student_assignment'].id}/activities",
            headers={"Authorization": f"Bearer {test_data['token']}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Find the new item (should be the 4th one)
        activity = data["activities"][0]
        assert len(activity["items"]) == 4

        new_item_data = activity["items"][3]
        assert new_item_data["teacher_feedback"] is None
        assert new_item_data["teacher_passed"] is None
        assert new_item_data["teacher_review_score"] is None
        assert new_item_data["review_status"] == "PENDING"

    def test_unauthorized_access(self, test_client, test_data):
        """Test that unauthorized users cannot access teacher feedback"""
        # Try without token
        response = test_client.get(
            f"/api/students/assignments/{test_data['student_assignment'].id}/activities"
        )
        assert response.status_code == 401

        # Try with invalid token
        response = test_client.get(
            f"/api/students/assignments/{test_data['student_assignment'].id}/activities",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_different_student_cannot_access(
        self, test_client, test_data, test_session
    ):
        """Test that different students cannot access each other's feedback"""
        # Create another student
        other_student = Student(
            id=2, name="Other Student", email="other@test.com", is_active=True
        )
        test_session.add(other_student)
        test_session.commit()

        # Create token for other student
        other_token = create_access_token(
            data={"sub": str(other_student.id), "type": "student"}
        )

        # Try to access first student's assignment
        response = test_client.get(
            f"/api/students/assignments/{test_data['student_assignment'].id}/activities",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 404
        assert "not found or not assigned to you" in response.json()["detail"]
