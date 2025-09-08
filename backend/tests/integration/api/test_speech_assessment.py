"""
Azure Speech Assessment API Tests
測試微軟發音評估 API 整合功能
"""
import pytest
import io
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import base64

from main import app
from database import get_db
from auth import create_access_token
from datetime import timedelta

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """創建測試用的學生認證 headers"""
    token = create_access_token(
        data={
            "sub": "1",
            "email": "test.student@duotopia.com",
            "type": "student",
            "student_id": "TEST001",
        },
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_audio_file():
    """創建模擬的音檔"""
    # 創建一個簡單的 WAV 檔案頭部（44 bytes）
    wav_header = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"fmt " + b"\x00" * 32
    audio_data = wav_header + b"\x00" * 1000  # 模擬音檔資料
    return io.BytesIO(audio_data)


class TestSpeechAssessmentAPI:
    """發音評估 API 測試"""

    def test_assess_pronunciation_success(self, auth_headers, mock_audio_file):
        """測試成功的發音評估請求"""
        # 準備測試資料
        reference_text = "Hello, how are you today?"

        # Mock Azure Speech SDK 回應
        mock_result = {
            "accuracy_score": 95.5,
            "fluency_score": 92.3,
            "completeness_score": 100.0,
            "pronunciation_score": 94.2,
            "words": [
                {
                    "word": "hello",
                    "accuracy_score": 98,
                    "error_type": "None",
                },
                {
                    "word": "how",
                    "accuracy_score": 95,
                    "error_type": "None",
                },
            ],
        }

        with patch("routers.speech_assessment.assess_pronunciation") as mock_assess:
            mock_assess.return_value = mock_result

            # 發送請求
            response = client.post(
                "/api/speech/assess",
                headers=auth_headers,
                files={"audio_file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"reference_text": reference_text, "progress_id": "1"},
            )

            # 驗證回應
            assert response.status_code == 200
            data = response.json()
            assert "accuracy_score" in data
            assert "fluency_score" in data
            assert "pronunciation_score" in data
            assert "words" in data
            assert data["accuracy_score"] == 95.5

    def test_assess_pronunciation_without_auth(self, mock_audio_file):
        """測試未認證的請求應該被拒絕"""
        response = client.post(
            "/api/speech/assess",
            files={"audio_file": ("test.wav", mock_audio_file, "audio/wav")},
            data={"reference_text": "Hello"},
        )

        assert response.status_code == 401

    def test_assess_pronunciation_missing_audio(self, auth_headers):
        """測試缺少音檔的請求"""
        response = client.post(
            "/api/speech/assess",
            headers=auth_headers,
            data={"reference_text": "Hello"},
        )

        assert response.status_code == 422

    def test_assess_pronunciation_missing_text(self, auth_headers, mock_audio_file):
        """測試缺少參考文本的請求"""
        response = client.post(
            "/api/speech/assess",
            headers=auth_headers,
            files={"audio_file": ("test.wav", mock_audio_file, "audio/wav")},
        )

        assert response.status_code == 422

    def test_assess_pronunciation_invalid_audio_format(self, auth_headers):
        """測試不支援的音檔格式"""
        # 創建一個假的文字檔案
        fake_audio = io.BytesIO(b"This is not an audio file")

        response = client.post(
            "/api/speech/assess",
            headers=auth_headers,
            files={"audio_file": ("test.txt", fake_audio, "text/plain")},
            data={"reference_text": "Hello"},
        )

        assert response.status_code == 400
        assert "audio format" in response.json()["detail"].lower()

    def test_assess_pronunciation_file_too_large(self, auth_headers):
        """測試音檔太大的情況（超過 10MB）"""
        # 創建一個超過 10MB 的檔案
        large_audio = io.BytesIO(b"\x00" * (11 * 1024 * 1024))

        response = client.post(
            "/api/speech/assess",
            headers=auth_headers,
            files={"audio_file": ("test.wav", large_audio, "audio/wav")},
            data={"reference_text": "Hello"},
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    def test_assess_pronunciation_azure_api_error(self, auth_headers, mock_audio_file):
        """測試 Azure API 錯誤處理"""
        with patch("routers.speech_assessment.assess_pronunciation") as mock_assess:
            mock_assess.side_effect = Exception("Azure API error")

            response = client.post(
                "/api/speech/assess",
                headers=auth_headers,
                files={"audio_file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"reference_text": "Hello"},
            )

            assert response.status_code == 503
            assert "service unavailable" in response.json()["detail"].lower()

    def test_assess_pronunciation_saves_to_database(
        self, auth_headers, mock_audio_file
    ):
        """測試評估結果是否正確儲存到資料庫"""
        mock_result = {
            "accuracy_score": 95.5,
            "fluency_score": 92.3,
            "completeness_score": 100.0,
            "pronunciation_score": 94.2,
            "words": [],
        }

        with patch("routers.speech_assessment.assess_pronunciation") as mock_assess:
            mock_assess.return_value = mock_result

            with patch("routers.speech_assessment.save_assessment_result") as mock_save:
                response = client.post(
                    "/api/speech/assess",
                    headers=auth_headers,
                    files={"audio_file": ("test.wav", mock_audio_file, "audio/wav")},
                    data={"reference_text": "Hello", "progress_id": "123"},
                )

                assert response.status_code == 200
                # 驗證儲存函數被呼叫
                mock_save.assert_called_once()

    def test_get_assessment_history(self, auth_headers):
        """測試獲取評估歷史記錄"""
        with patch("routers.speech_assessment.get_student_assessments") as mock_get:
            mock_get.return_value = [
                {
                    "id": 1,
                    "reference_text": "Hello",
                    "accuracy_score": 95.5,
                    "created_at": "2024-01-01T00:00:00",
                },
                {
                    "id": 2,
                    "reference_text": "World",
                    "accuracy_score": 88.2,
                    "created_at": "2024-01-02T00:00:00",
                },
            ]

            response = client.get(
                "/api/speech/assessments",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["accuracy_score"] == 95.5

    def test_get_assessment_detail(self, auth_headers):
        """測試獲取單一評估詳細資料"""
        with patch("routers.speech_assessment.get_assessment_by_id") as mock_get:
            mock_get.return_value = {
                "id": 1,
                "reference_text": "Hello, how are you?",
                "accuracy_score": 95.5,
                "fluency_score": 92.3,
                "pronunciation_score": 94.2,
                "words": [
                    {"word": "hello", "accuracy_score": 98},
                    {"word": "how", "accuracy_score": 95},
                ],
                "created_at": "2024-01-01T00:00:00",
            }

            response = client.get(
                "/api/speech/assessments/1",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert len(data["words"]) == 2

    def test_rate_limiting(self, auth_headers, mock_audio_file):
        """測試 API 速率限制（防止濫用）"""
        # 快速發送多個請求
        responses = []
        for _ in range(6):  # 假設限制是 5 次/分鐘
            response = client.post(
                "/api/speech/assess",
                headers=auth_headers,
                files={
                    "audio_file": ("test.wav", mock_audio_file.getvalue(), "audio/wav")
                },
                data={"reference_text": "Hello"},
            )
            responses.append(response)
            mock_audio_file.seek(0)  # 重置檔案指針

        # 最後一個請求應該被限制
        assert responses[-1].status_code == 429
        assert "rate limit" in responses[-1].json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
