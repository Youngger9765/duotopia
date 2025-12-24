"""
Comprehensive tests for Pronunciation Upload Analysis Endpoint
Testing background upload of audio files and analysis results from frontend
"""
import json
from unittest.mock import patch


class TestPronunciationUploadAPI:
    """Test pronunciation upload analysis endpoint"""

    def test_upload_analysis_requires_authentication(self, test_client):
        """Test 1: 未登录用户无法上传"""
        audio_file = ("test.wav", b"fake audio data", "audio/wav")
        analysis_json = json.dumps({"pronunciation_score": 85})

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={"analysis_json": analysis_json, "latency_ms": 1500},
        )

        assert response.status_code == 401

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_success_student(
        self,
        mock_upload,
        test_client,
        demo_student,
        auth_headers_student,
        test_student_assignment,
        test_classroom,
    ):
        """Test 2: 学生成功上传音档和分析结果"""
        mock_upload.return_value = (
            "https://storage.googleapis.com/duotopia-audio/recordings/test.wav"
        )

        # 准备测试数据
        audio_file = ("test.wav", b"fake audio data" * 100, "audio/wav")  # 足够大
        analysis_result = {
            "pronunciation_score": 85,
            "accuracy_score": 88,
            "fluency_score": 82,
            "completeness_score": 90,
            "words": [
                {"word": "hello", "accuracy_score": 90},
                {"word": "world", "accuracy_score": 80},
            ],
        }

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={
                "analysis_json": json.dumps(analysis_result),
                "latency_ms": 1500,
                "progress_id": test_student_assignment["id"],
            },
            headers=auth_headers_student,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "progress_id" in data
        assert data["audio_url"] == mock_upload.return_value

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_stores_metadata(
        self,
        mock_upload,
        test_client,
        demo_student,
        auth_headers_student,
        test_student_assignment,
        shared_test_session,
    ):
        """Test 3: 验证 metadata 正确存储到 JSONB（方案 A）"""
        from models import StudentItemProgress

        mock_upload.return_value = "https://storage.googleapis.com/test.wav"

        audio_file = ("test.wav", b"x" * 10000, "audio/wav")
        analysis_result = {
            "pronunciation_score": 85,
            "words": [{"word": "test", "accuracy_score": 85}],
        }

        # Get first item progress for this assignment
        progress = (
            shared_test_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=test_student_assignment["id"])
            .first()
        )

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={
                "analysis_json": json.dumps(analysis_result),
                "latency_ms": 1500,
                "progress_id": progress.id,
            },
            headers=auth_headers_student,
        )

        assert response.status_code == 200

        # 验证数据库存储
        shared_test_session.refresh(progress)

        # 检查 ai_feedback 包含 metadata
        feedback = json.loads(progress.ai_feedback)
        assert "_metadata" in feedback
        assert feedback["_metadata"]["source"] == "frontend_direct"
        assert feedback["_metadata"]["latency_ms"] == 1500
        assert feedback["_metadata"]["azure_token_used"] is True
        assert "uploaded_at" in feedback["_metadata"]

        # 检查分数正确存储
        assert float(progress.pronunciation_score) == 85

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_invalid_json(
        self,
        mock_upload,
        test_client,
        demo_student,
        auth_headers_student,
        test_student_assignment,
    ):
        """Test 4: 无效的 JSON 格式返回 400"""
        mock_upload.return_value = "https://storage.googleapis.com/test.wav"

        audio_file = ("test.wav", b"x" * 10000, "audio/wav")

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={
                "analysis_json": "invalid json{]",
                "latency_ms": 1500,
                "progress_id": test_student_assignment["id"],
            },
            headers=auth_headers_student,
        )

        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_missing_required_fields(
        self, mock_upload, test_client, demo_student, auth_headers_student
    ):
        """Test 5: 缺少必需字段返回 422"""
        mock_upload.return_value = "https://storage.googleapis.com/test.wav"

        audio_file = ("test.wav", b"x" * 10000, "audio/wav")

        # 缺少 progress_id
        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={"analysis_json": json.dumps({"pronunciation_score": 85})},
            headers=auth_headers_student,
        )

        assert response.status_code == 422

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_gcs_upload_failure(
        self,
        mock_upload,
        test_client,
        demo_student,
        auth_headers_student,
        test_student_assignment,
    ):
        """Test 6: GCS 上传失败时返回 500"""
        from fastapi import HTTPException

        mock_upload.side_effect = HTTPException(
            status_code=500, detail="GCS upload failed"
        )

        audio_file = ("test.wav", b"x" * 10000, "audio/wav")
        analysis_result = {"pronunciation_score": 85}

        # Mock progress_id (since shared_test_session not in scope)
        progress_id = 99998  # Different from 99999 used in previous test

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={
                "analysis_json": json.dumps(analysis_result),
                "progress_id": progress_id,
            },
            headers=auth_headers_student,
        )

        assert response.status_code == 500

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_invalid_progress_id(
        self, mock_upload, test_client, demo_student, auth_headers_student
    ):
        """Test 7: 无效的 progress_id 返回 404"""
        mock_upload.return_value = "https://storage.googleapis.com/test.wav"

        audio_file = ("test.wav", b"x" * 10000, "audio/wav")
        analysis_result = {"pronunciation_score": 85}

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={
                "analysis_json": json.dumps(analysis_result),
                "progress_id": 99999,  # Non-existent ID
            },
            headers=auth_headers_student,
        )

        assert response.status_code == 404
        assert "Progress not found" in response.json()["detail"]

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_permission_check(
        self,
        mock_upload,
        test_client,
        demo_student,
        demo_teacher,
        auth_headers_student,
        auth_headers_teacher,
        test_student_assignment,
        shared_test_session,
    ):
        """Test 8: 学生不能上传其他学生的作业"""
        from models import Student, StudentItemProgress
        from auth import get_password_hash
        from datetime import date

        # Create another student
        other_student = Student(
            email="other@duotopia.com",
            password_hash=get_password_hash("test123"),
            name="Other Student",
            birthdate=date(2010, 1, 1),
            email_verified=True,
        )
        shared_test_session.add(other_student)
        shared_test_session.commit()

        # Get progress belonging to demo_student
        progress = (
            shared_test_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=test_student_assignment["id"])
            .first()
        )

        mock_upload.return_value = "https://storage.googleapis.com/test.wav"

        audio_file = ("test.wav", b"x" * 10000, "audio/wav")
        analysis_result = {"pronunciation_score": 85}

        # Try to upload with other_student's auth
        from auth import create_access_token

        other_headers = {
            "Authorization": f"Bearer {create_access_token(data={'sub': str(other_student.id), 'type': 'student'})}"
        }

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={
                "analysis_json": json.dumps(analysis_result),
                "progress_id": progress.id,
            },
            headers=other_headers,
        )

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    @patch("services.audio_upload.AudioUploadService.upload_audio")
    def test_upload_analysis_preserves_existing_data(
        self,
        mock_upload,
        test_client,
        demo_student,
        auth_headers_student,
        test_student_assignment,
        shared_test_session,
    ):
        """Test 9: 上传不会覆盖现有的 ai_feedback 数据"""
        from models import StudentItemProgress

        mock_upload.return_value = "https://storage.googleapis.com/test.wav"

        # Get first progress
        progress = (
            shared_test_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=test_student_assignment["id"])
            .first()
        )

        # Set existing ai_feedback
        existing_feedback = {
            "some_field": "existing_value",
            "timestamp": "2025-01-01T00:00:00",
        }
        progress.ai_feedback = json.dumps(existing_feedback)
        shared_test_session.commit()

        audio_file = ("test.wav", b"x" * 10000, "audio/wav")
        analysis_result = {
            "pronunciation_score": 90,
            "words": [{"word": "new", "accuracy_score": 90}],
        }

        response = test_client.post(
            "/api/speech/upload-analysis",
            files={"audio_file": audio_file},
            data={
                "analysis_json": json.dumps(analysis_result),
                "latency_ms": 2000,
                "progress_id": progress.id,
            },
            headers=auth_headers_student,
        )

        assert response.status_code == 200

        # 验证数据合并
        shared_test_session.refresh(progress)
        feedback = json.loads(progress.ai_feedback)

        # 新的分析结果应该存在
        assert feedback["pronunciation_score"] == 90
        # Metadata 应该存在
        assert "_metadata" in feedback
        assert feedback["_metadata"]["source"] == "frontend_direct"
