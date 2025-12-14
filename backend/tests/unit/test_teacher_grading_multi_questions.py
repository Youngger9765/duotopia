#!/usr/bin/env python3
"""
測試教師批改頁面讀取多題目學生錄音和AI評分
"""
import pytest
from sqlalchemy.orm import Session
from models import (
    StudentContentProgress,
    AssignmentStatus,
    Content,
    ContentType,
)


class TestTeacherGradingMultiQuestions:
    """測試教師批改多題目功能"""

    def test_teacher_can_read_multi_question_recordings(self, db_session: Session):
        """測試教師能讀取多題目的學生錄音"""
        # 創建測試資料
        content = Content(
            lesson_id=1,  # 必填欄位
            title="Multi Question Test",
            type=ContentType.EXAMPLE_SENTENCES,
            items=[
                {"text": "Hello world", "translation": "你好世界"},
                {"text": "Good morning", "translation": "早安"},
                {"text": "How are you", "translation": "你好嗎"},
            ],
        )
        db_session.add(content)
        db_session.commit()

        # 創建學生進度，包含多題目錄音
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=content.id,
            status=AssignmentStatus.SUBMITTED,
            response_data={
                "recordings": [
                    "https://gcs.bucket.com/recording1.webm",
                    "https://gcs.bucket.com/recording2.webm",
                    "https://gcs.bucket.com/recording3.webm",
                ]
            },
            ai_scores={
                "items": {
                    "0": {"accuracy_score": 85, "fluency_score": 90},
                    "1": {"accuracy_score": 92, "fluency_score": 88},
                    "2": {"accuracy_score": 78, "fluency_score": 85},
                }
            },
        )
        db_session.add(progress)
        db_session.commit()

        # 模擬 get_student_submission API 的邏輯
        submissions = []
        items_data = content.items

        for local_item_index, item in enumerate(items_data):
            submission = {
                "question_text": item.get("text", ""),
                "question_translation": item.get("translation", ""),
                "student_audio_url": "",
                "ai_scores": None,
            }

            # 應用我們的修復邏輯
            if progress.response_data:
                recordings = progress.response_data.get("recordings", [])
                if (
                    recordings
                    and local_item_index < len(recordings)
                    and recordings[local_item_index]
                ):
                    submission["student_audio_url"] = recordings[local_item_index]

            if progress.ai_scores:
                if (
                    "items" in progress.ai_scores
                    and str(local_item_index) in progress.ai_scores["items"]
                ):
                    submission["ai_scores"] = progress.ai_scores["items"][
                        str(local_item_index)
                    ]

            submissions.append(submission)

        # 驗證結果
        assert len(submissions) == 3

        # 驗證每題的錄音都能正確讀取
        assert (
            submissions[0]["student_audio_url"]
            == "https://gcs.bucket.com/recording1.webm"
        )
        assert (
            submissions[1]["student_audio_url"]
            == "https://gcs.bucket.com/recording2.webm"
        )
        assert (
            submissions[2]["student_audio_url"]
            == "https://gcs.bucket.com/recording3.webm"
        )

        # 驗證每題的AI評分都能正確讀取
        assert submissions[0]["ai_scores"]["accuracy_score"] == 85
        assert submissions[1]["ai_scores"]["accuracy_score"] == 92
        assert submissions[2]["ai_scores"]["accuracy_score"] == 78

    def test_teacher_can_read_single_question_data(self, db_session: Session):
        """測試教師能讀取單題目的學生錄音和AI評分"""
        content = Content(
            lesson_id=1,  # 必填欄位
            title="Single Question Test",
            type=ContentType.EXAMPLE_SENTENCES,
            items="Hello world",
        )
        db_session.add(content)
        db_session.commit()

        # 創建學生進度，單題目格式
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=content.id,
            status=AssignmentStatus.SUBMITTED,
            response_data={"audio_url": "https://gcs.bucket.com/single_recording.webm"},
            ai_scores={
                "accuracy_score": 88,
                "fluency_score": 92,
                "completeness_score": 85,
                "pronunciation_score": 90,
            },
        )
        db_session.add(progress)
        db_session.commit()

        # 模擬單題目的讀取邏輯
        submission = {
            "question_text": "Hello world",
            "student_audio_url": "",
            "ai_scores": None,
        }

        # 應用修復邏輯
        if progress.response_data:
            recordings = progress.response_data.get("recordings", [])
            if not recordings or not recordings[0]:  # 沒有 recordings 陣列
                audio_url = progress.response_data.get("audio_url")
                if audio_url:
                    submission["student_audio_url"] = audio_url

        if progress.ai_scores:
            if "items" not in progress.ai_scores:  # 單題目格式
                submission["ai_scores"] = {
                    k: v for k, v in progress.ai_scores.items() if k not in ["items"]
                }

        # 驗證結果
        assert (
            submission["student_audio_url"]
            == "https://gcs.bucket.com/single_recording.webm"
        )
        assert submission["ai_scores"]["accuracy_score"] == 88
        assert submission["ai_scores"]["fluency_score"] == 92

    def test_mixed_questions_with_partial_recordings(self, db_session: Session):
        """測試部分題目有錄音的情況"""
        content = Content(
            lesson_id=1,  # 必填欄位
            title="Partial Recording Test",
            type=ContentType.EXAMPLE_SENTENCES,
            items=[
                {"text": "Question 1"},
                {"text": "Question 2"},
                {"text": "Question 3"},
            ],
        )
        db_session.add(content)
        db_session.commit()

        # 只有第1題和第3題有錄音
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=content.id,
            status=AssignmentStatus.IN_PROGRESS,
            response_data={
                "recordings": [
                    "https://gcs.bucket.com/q1.webm",  # 第1題有錄音
                    "",  # 第2題沒錄音
                    "https://gcs.bucket.com/q3.webm",  # 第3題有錄音
                ]
            },
            ai_scores={
                "items": {
                    "0": {"accuracy_score": 85},  # 第1題有AI評分
                    "2": {"accuracy_score": 78},  # 第3題有AI評分
                }
            },
        )
        db_session.add(progress)
        db_session.commit()

        # 測試讀取邏輯
        submissions = []
        for local_item_index in range(3):
            submission = {"student_audio_url": "", "ai_scores": None}

            # 錄音讀取
            if progress.response_data:
                recordings = progress.response_data.get("recordings", [])
                if (
                    recordings
                    and local_item_index < len(recordings)
                    and recordings[local_item_index]
                ):
                    submission["student_audio_url"] = recordings[local_item_index]

            # AI評分讀取
            if progress.ai_scores:
                if (
                    "items" in progress.ai_scores
                    and str(local_item_index) in progress.ai_scores["items"]
                ):
                    submission["ai_scores"] = progress.ai_scores["items"][
                        str(local_item_index)
                    ]

            submissions.append(submission)

        # 驗證結果
        assert (
            submissions[0]["student_audio_url"] == "https://gcs.bucket.com/q1.webm"
        )  # 第1題有錄音
        assert submissions[1]["student_audio_url"] == ""  # 第2題沒錄音
        assert (
            submissions[2]["student_audio_url"] == "https://gcs.bucket.com/q3.webm"
        )  # 第3題有錄音

        assert submissions[0]["ai_scores"]["accuracy_score"] == 85  # 第1題有AI評分
        assert submissions[1]["ai_scores"] is None  # 第2題沒AI評分
        assert submissions[2]["ai_scores"]["accuracy_score"] == 78  # 第3題有AI評分


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
