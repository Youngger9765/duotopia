"""
TDD測試：驗證 upload-recording API 不會創建錯誤的 content_id=1 記錄
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import io
from datetime import date
from models import (
    Teacher,
    Student,
    Assignment,
    StudentAssignment,
    StudentContentProgress,
    Content,
    Lesson,
    Program,
)


@pytest.fixture
def setup_test_data(db_session: Session):
    """設置測試資料"""
    # 創建老師
    teacher = Teacher(
        name="Test Teacher", email="teacher@test.com", password_hash="hashed"
    )
    db_session.add(teacher)
    db_session.commit()

    # 創建學生
    student = Student(
        name="Test Student",
        email="student@test.com",
        password_hash="hashed",
        birthdate=date(2010, 1, 1),
    )
    db_session.add(student)
    db_session.commit()

    # 創建 Program 和 Lesson
    program = Program(
        title="Test Program",
        description="Test",
        teacher_id=teacher.id,
        level="beginner",
    )
    db_session.add(program)
    db_session.commit()

    lesson = Lesson(
        title="Test Lesson", description="Test", program_id=program.id, order_index=1
    )
    db_session.add(lesson)
    db_session.commit()

    # 創建正確的 Content (不是 id=1)
    content1 = Content(
        lesson_id=lesson.id,
        type="pronunciation",
        title="Real Content 1",
        items=[
            {"text": "Hello World", "translation": "你好世界"},
            {"text": "Good Morning", "translation": "早安"},
        ],
        order_index=1,
    )
    content2 = Content(
        lesson_id=lesson.id,
        type="pronunciation",
        title="Real Content 2",
        items=[
            {"text": "Thank you", "translation": "謝謝"},
            {"text": "Goodbye", "translation": "再見"},
        ],
        order_index=2,
    )
    db_session.add_all([content1, content2])
    db_session.commit()

    # 創建作業
    assignment = Assignment(
        title="Test Assignment",
        description="Test",
        teacher_id=teacher.id,
        classroom_id=1,  # 假設的
    )
    db_session.add(assignment)
    db_session.commit()

    # 創建學生作業
    student_assignment = StudentAssignment(
        student_id=student.id, assignment_id=assignment.id, status="in_progress"
    )
    db_session.add(student_assignment)
    db_session.commit()

    # 創建正確的 StudentContentProgress 記錄
    progress1 = StudentContentProgress(
        student_assignment_id=student_assignment.id,
        content_id=content1.id,  # 正確的 content_id
        order_index=0,
        status="not_started",
    )
    progress2 = StudentContentProgress(
        student_assignment_id=student_assignment.id,
        content_id=content2.id,  # 正確的 content_id
        order_index=1,
        status="not_started",
    )
    db_session.add_all([progress1, progress2])
    db_session.commit()

    return {
        "student": student,
        "student_assignment": student_assignment,
        "content1": content1,
        "content2": content2,
        "progress1": progress1,
        "progress2": progress2,
    }


def test_upload_recording_uses_correct_content_id(
    client: TestClient, db_session: Session, setup_test_data
):
    """測試上傳錄音時使用正確的 content_id，而不是硬編碼的 1"""

    test_data = setup_test_data
    student = test_data["student"]
    student_assignment = test_data["student_assignment"]
    content1 = test_data["content1"]
    content2 = test_data["content2"]

    # 模擬學生登入
    with patch("routers.students.get_current_user") as mock_user:
        mock_user.return_value = {
            "type": "student",
            "sub": str(student.id),
            "username": student.name,
        }

        # 模擬音頻上傳服務
        with patch("routers.students.get_audio_upload_service") as mock_audio_service:
            mock_service = MagicMock()
            mock_service.upload_audio.return_value = (
                "https://gcs.example.com/audio123.webm"
            )
            mock_audio_service.return_value = mock_service

            with patch("routers.students.get_audio_manager"):
                # 準備測試音頻檔案
                audio_file = io.BytesIO(b"fake audio data")
                audio_file.name = "test.webm"

                # 測試1：為第一個 content (order_index=0) 上傳錄音
                response = client.post(
                    "/api/students/upload-recording",
                    files={"audio_file": ("test.webm", audio_file, "audio/webm")},
                    data={
                        "assignment_id": student_assignment.id,
                        "content_item_index": 0,  # 對應 content1
                    },
                )

                assert response.status_code == 200

                # 驗證：檢查 StudentContentProgress 的 content_id 沒有被改成 1
                progress = (
                    db_session.query(StudentContentProgress)
                    .filter(
                        StudentContentProgress.student_assignment_id
                        == student_assignment.id,
                        StudentContentProgress.order_index == 0,
                    )
                    .first()
                )

                assert progress is not None
                assert progress.content_id == content1.id  # 應該保持原本的 content_id
                assert progress.content_id != 1  # 絕對不應該是 1
                assert (
                    progress.response_data["audio_url"]
                    == "https://gcs.example.com/audio123.webm"
                )

                # 測試2：為第二個 content (order_index=1) 上傳錄音
                audio_file.seek(0)  # 重置檔案指標
                response2 = client.post(
                    "/api/students/upload-recording",
                    files={"audio_file": ("test.webm", audio_file, "audio/webm")},
                    data={
                        "assignment_id": student_assignment.id,
                        "content_item_index": 1,  # 對應 content2
                    },
                )

                assert response2.status_code == 200

                # 驗證第二個記錄
                progress2 = (
                    db_session.query(StudentContentProgress)
                    .filter(
                        StudentContentProgress.student_assignment_id
                        == student_assignment.id,
                        StudentContentProgress.order_index == 1,
                    )
                    .first()
                )

                assert progress2 is not None
                assert progress2.content_id == content2.id  # 應該保持原本的 content_id
                assert progress2.content_id != 1  # 絕對不應該是 1


def test_upload_recording_without_existing_progress_returns_error(
    client: TestClient, db_session: Session, setup_test_data
):
    """測試：當沒有對應的 StudentContentProgress 記錄時，應該報錯而不是創建錯誤記錄"""

    test_data = setup_test_data
    student = test_data["student"]
    student_assignment = test_data["student_assignment"]

    # 模擬學生登入
    with patch("routers.students.get_current_user") as mock_user:
        mock_user.return_value = {
            "type": "student",
            "sub": str(student.id),
            "username": student.name,
        }

        with patch("routers.students.get_audio_upload_service") as mock_audio_service:
            mock_service = MagicMock()
            mock_service.upload_audio.return_value = (
                "https://gcs.example.com/audio456.webm"
            )
            mock_audio_service.return_value = mock_service

            with patch("routers.students.get_audio_manager"):
                audio_file = io.BytesIO(b"fake audio data")
                audio_file.name = "test.webm"

                # 嘗試為不存在的 order_index 上傳錄音
                response = client.post(
                    "/api/students/upload-recording",
                    files={"audio_file": ("test.webm", audio_file, "audio/webm")},
                    data={
                        "assignment_id": student_assignment.id,
                        "content_item_index": 999,  # 不存在的 index
                    },
                )

                # 應該返回錯誤
                assert response.status_code == 400
                assert "No content found for order_index" in response.json()["detail"]

                # 驗證：確保沒有創建任何新的 content_id=1 記錄
                wrong_progress = (
                    db_session.query(StudentContentProgress)
                    .filter(
                        StudentContentProgress.student_assignment_id
                        == student_assignment.id,
                        StudentContentProgress.content_id == 1,
                    )
                    .first()
                )

                assert wrong_progress is None  # 不應該存在


def test_no_hardcoded_content_id_one(client: TestClient, db_session: Session):
    """測試：確保系統中沒有任何地方硬編碼使用 content_id=1"""

    # 創建測試資料，但故意不創建 content_id=1
    teacher = Teacher(name="Teacher", email="teacher2@test.com", password_hash="hashed")
    db_session.add(teacher)
    db_session.commit()

    student = Student(
        name="Student",
        email="student2@test.com",
        password_hash="hashed",
        birthdate=date(2010, 1, 1),
    )
    db_session.add(student)
    db_session.commit()

    # 創建作業，使用直接 content 模式
    student_assignment = StudentAssignment(
        student_id=student.id,
        content_id=50,  # 使用一個不是 1 的 content_id
        status="in_progress",
    )
    db_session.add(student_assignment)
    db_session.commit()

    with patch("routers.students.get_current_user") as mock_user:
        mock_user.return_value = {
            "type": "student",
            "sub": str(student.id),
            "username": student.name,
        }

        with patch("routers.students.get_audio_upload_service") as mock_audio_service:
            mock_service = MagicMock()
            mock_service.upload_audio.return_value = (
                "https://gcs.example.com/audio789.webm"
            )
            mock_audio_service.return_value = mock_service

            with patch("routers.students.get_audio_manager"):
                audio_file = io.BytesIO(b"fake audio data")
                audio_file.name = "test.webm"

                # 上傳錄音
                response = client.post(
                    "/api/students/upload-recording",
                    files={"audio_file": ("test.webm", audio_file, "audio/webm")},
                    data={
                        "assignment_id": student_assignment.id,
                        "content_item_index": 0,
                    },
                )

                assert response.status_code == 200

                # 驗證：確保使用的是正確的 content_id=50，而不是 1
                progress = (
                    db_session.query(StudentContentProgress)
                    .filter(
                        StudentContentProgress.student_assignment_id
                        == student_assignment.id
                    )
                    .first()
                )

                assert progress is not None
                assert progress.content_id == 50  # 應該使用正確的 content_id
                assert progress.content_id != 1  # 絕對不應該是硬編碼的 1
