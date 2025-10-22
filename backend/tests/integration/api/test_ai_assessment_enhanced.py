"""
測試增強的 Azure Speech AI 評估功能
包括韻律評估、詳細音素分析等新功能
"""

import json
from sqlalchemy.orm import Session
from models import StudentItemProgress
from tests.factories import TestDataFactory


class TestAIAssessmentEnhanced:
    """測試增強的 AI 評估功能"""

    def test_ai_assessment_response_structure(self, db_session: Session):
        """測試 AI 評估回應的資料結構"""
        # 每個測試使用獨立的 email 避免資料衝突
        # 模擬 Azure Speech API 回應
        mock_assessment_result = {
            "accuracy_score": 92.5,
            "fluency_score": 88.0,
            "pronunciation_score": 90.0,
            "completeness_score": 95.0,
            "prosody_score": 87.5,  # 新增的韻律評分
            "reference_text": "Hello, how are you today?",
            "recognized_text": "Hello how are you today",
            "detailed_words": [
                {
                    "word": "Hello",
                    "accuracy_score": 95.0,
                    "error_type": None,
                    "index": 0,
                    "syllables": [
                        {"syllable": "Hel", "accuracy_score": 96.0, "index": 0},
                        {"syllable": "lo", "accuracy_score": 94.0, "index": 1},
                    ],
                    "phonemes": [
                        {"phoneme": "h", "accuracy_score": 98.0, "index": 0},
                        {"phoneme": "ɛ", "accuracy_score": 95.0, "index": 1},
                        {"phoneme": "l", "accuracy_score": 93.0, "index": 2},
                        {"phoneme": "oʊ", "accuracy_score": 94.0, "index": 3},
                    ],
                }
            ],
            "word_details": [{"word": "Hello", "accuracy_score": 95.0}],  # 保留舊版相容性
            "analysis_summary": {
                "total_words": 5,
                "problematic_words": ["are"],
                "low_score_phonemes": [
                    {"phoneme": "r", "score": 72.0, "in_word": "are"}
                ],
                "assessment_time": "2024-12-28T10:30:00Z",
            },
        }

        # 建立測試資料（使用唯一 email）
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            teacher_email="teacher_ai_response@test.com",
            student_email="student_ai_response@test.com",
            student_number="S_AI_RESP",
            content_items=[
                {"text": "Hello, how are you today?", "translation": "你好嗎？"}
            ],
        )

        # 更新已存在的 StudentItemProgress 記錄（Factory 已創建）
        progress = (
            db_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id
                == data["student_assignment"].id,
                StudentItemProgress.content_item_id
                == data["content"].content_items[0].id,
            )
            .first()
        )

        # 更新 AI 評估結果
        progress.recording_url = "test.webm"
        progress.ai_feedback = json.dumps(mock_assessment_result)
        progress.accuracy_score = mock_assessment_result["accuracy_score"]
        progress.fluency_score = mock_assessment_result["fluency_score"]
        progress.pronunciation_score = mock_assessment_result["pronunciation_score"]
        progress.status = "ASSESSED"
        db_session.commit()

        # 驗證資料結構
        saved = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.id == progress.id)
            .first()
        )

        ai_data = json.loads(saved.ai_feedback)

        # 驗證新增的欄位
        assert "prosody_score" in ai_data
        assert "detailed_words" in ai_data
        assert "analysis_summary" in ai_data
        assert "reference_text" in ai_data
        assert "recognized_text" in ai_data

    def test_detailed_phoneme_analysis(self, db_session: Session):
        """測試詳細的音素分析"""
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            teacher_email="teacher_phoneme@test.com",
            student_email="student_phoneme@test.com",
            student_number="S_PHONEME",
        )

        # 詳細的音素分析資料
        ai_feedback = {
            "accuracy_score": 85.0,
            "detailed_words": [
                {
                    "word": "difficult",
                    "accuracy_score": 75.0,
                    "error_type": "mispronunciation",
                    "index": 0,
                    "syllables": [
                        {"syllable": "dif", "accuracy_score": 80.0, "index": 0},
                        {"syllable": "fi", "accuracy_score": 70.0, "index": 1},
                        {"syllable": "cult", "accuracy_score": 75.0, "index": 2},
                    ],
                    "phonemes": [
                        {"phoneme": "d", "accuracy_score": 90.0, "index": 0},
                        {"phoneme": "ɪ", "accuracy_score": 85.0, "index": 1},
                        {"phoneme": "f", "accuracy_score": 88.0, "index": 2},
                        {"phoneme": "ɪ", "accuracy_score": 60.0, "index": 3},  # 低分音素
                        {"phoneme": "k", "accuracy_score": 82.0, "index": 4},
                        {"phoneme": "ʌ", "accuracy_score": 65.0, "index": 5},  # 低分音素
                        {"phoneme": "l", "accuracy_score": 78.0, "index": 6},
                        {"phoneme": "t", "accuracy_score": 85.0, "index": 7},
                    ],
                }
            ],
        }

        # 更新已存在的記錄
        progress = (
            db_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id
                == data["student_assignment"].id,
                StudentItemProgress.content_item_id
                == data["content"].content_items[0].id,
            )
            .first()
        )
        progress.ai_feedback = json.dumps(ai_feedback)
        progress.status = "ASSESSED"
        db_session.commit()

        # 驗證音素分析
        saved = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.id == progress.id)
            .first()
        )

        ai_data = json.loads(saved.ai_feedback)
        word = ai_data["detailed_words"][0]

        assert len(word["phonemes"]) == 8
        assert len(word["syllables"]) == 3

        # 找出低分音素（< 70）
        low_score_phonemes = [p for p in word["phonemes"] if p["accuracy_score"] < 70]
        assert len(low_score_phonemes) == 2
        assert low_score_phonemes[0]["phoneme"] == "ɪ"
        assert low_score_phonemes[1]["phoneme"] == "ʌ"

    def test_prosody_assessment(self, db_session: Session):
        """測試韻律評估功能"""
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            teacher_email="teacher_prosody@test.com",
            student_email="student_prosody@test.com",
            student_number="S_PROSODY",
        )

        # 包含韻律評估的資料
        ai_feedback = {
            "accuracy_score": 88.0,
            "fluency_score": 85.0,
            "pronunciation_score": 87.0,
            "prosody_score": 82.0,  # 韻律分數
            "prosody_details": {
                "intonation": 85.0,  # 語調
                "stress": 80.0,  # 重音
                "rhythm": 81.0,  # 節奏
            },
        }

        # 更新已存在的記錄
        progress = (
            db_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id
                == data["student_assignment"].id,
                StudentItemProgress.content_item_id
                == data["content"].content_items[0].id,
            )
            .first()
        )
        progress.ai_feedback = json.dumps(ai_feedback)
        progress.status = "ASSESSED"
        db_session.commit()

        # 驗證韻律評估
        saved = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.id == progress.id)
            .first()
        )

        ai_data = json.loads(saved.ai_feedback)
        assert "prosody_score" in ai_data
        assert ai_data["prosody_score"] == 82.0

        if "prosody_details" in ai_data:
            assert ai_data["prosody_details"]["intonation"] == 85.0
            assert ai_data["prosody_details"]["stress"] == 80.0
            assert ai_data["prosody_details"]["rhythm"] == 81.0

    def test_analysis_summary_generation(self, db_session: Session):
        """測試分析摘要生成"""
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            teacher_email="teacher_summary@test.com",
            student_email="student_summary@test.com",
            student_number="S_SUMMARY",
        )

        # 包含分析摘要的資料
        ai_feedback = {
            "accuracy_score": 75.0,
            "detailed_words": [
                {"word": "Hello", "accuracy_score": 95.0, "phonemes": []},
                {"word": "difficult", "accuracy_score": 65.0, "phonemes": []},
                {"word": "pronunciation", "accuracy_score": 60.0, "phonemes": []},
            ],
            "analysis_summary": {
                "total_words": 3,
                "problematic_words": ["difficult", "pronunciation"],
                "low_score_phonemes": [
                    {"phoneme": "ʃ", "score": 55.0, "in_word": "pronunciation"},
                    {"phoneme": "eɪ", "score": 58.0, "in_word": "pronunciation"},
                ],
                "suggestions": [
                    "Focus on the 'sh' sound in 'pronunciation'",
                    "Practice the word 'difficult' more slowly",
                ],
                "overall_feedback": "Good effort! Focus on problematic sounds.",
                "assessment_time": "2024-12-28T10:30:00Z",
            },
        }

        # 更新已存在的記錄
        progress = (
            db_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id
                == data["student_assignment"].id,
                StudentItemProgress.content_item_id
                == data["content"].content_items[0].id,
            )
            .first()
        )
        progress.ai_feedback = json.dumps(ai_feedback)
        progress.status = "ASSESSED"
        db_session.commit()

        # 驗證分析摘要
        saved = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.id == progress.id)
            .first()
        )

        ai_data = json.loads(saved.ai_feedback)
        summary = ai_data["analysis_summary"]

        assert summary["total_words"] == 3
        assert len(summary["problematic_words"]) == 2
        assert "difficult" in summary["problematic_words"]
        assert len(summary["low_score_phonemes"]) == 2
        assert summary["low_score_phonemes"][0]["phoneme"] == "ʃ"

    def test_backward_compatibility(self, db_session: Session):
        """測試向後相容性 - 舊版資料結構仍可使用"""
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            teacher_email="teacher_compat@test.com",
            student_email="student_compat@test.com",
            student_number="S_COMPAT",
        )

        # 舊版資料結構（只有 word_details）
        old_format = {
            "accuracy_score": 85.0,
            "fluency_score": 82.0,
            "pronunciation_score": 84.0,
            "completeness_score": 90.0,
            "word_details": [
                {"word": "Hello", "accuracy_score": 90.0},
                {"word": "world", "accuracy_score": 85.0},
            ],
        }

        # 更新已存在的記錄
        progress = (
            db_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id
                == data["student_assignment"].id,
                StudentItemProgress.content_item_id
                == data["content"].content_items[0].id,
            )
            .first()
        )
        progress.ai_feedback = json.dumps(old_format)
        progress.accuracy_score = old_format["accuracy_score"]
        progress.fluency_score = old_format["fluency_score"]
        progress.pronunciation_score = old_format["pronunciation_score"]
        progress.status = "ASSESSED"
        db_session.commit()

        # 驗證舊格式仍可讀取
        saved = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.id == progress.id)
            .first()
        )

        ai_data = json.loads(saved.ai_feedback)
        assert "word_details" in ai_data
        assert len(ai_data["word_details"]) == 2
        assert ai_data["accuracy_score"] == 85.0

    def test_multiple_items_independent_assessment(self, db_session: Session):
        """測試多個項目的獨立評估"""
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            teacher_email="teacher_multi@test.com",
            student_email="student_multi@test.com",
            student_number="S_MULTI",
            content_items=[
                {"text": "Item 1", "translation": "項目1"},
                {"text": "Item 2", "translation": "項目2"},
            ],
        )

        items = data["content"].content_items

        # 為第一個項目更新評估（Factory 已創建）
        ai_feedback_1 = {
            "accuracy_score": 80.0,
            "detailed_words": [
                {
                    "word": "Word1",
                    "accuracy_score": 75.0,
                    "phonemes": [{"phoneme": "w", "accuracy_score": 80.0}],
                }
            ],
        }

        progress_1 = (
            db_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id
                == data["student_assignment"].id,
                StudentItemProgress.content_item_id == items[0].id,
            )
            .first()
        )
        progress_1.ai_feedback = json.dumps(ai_feedback_1)
        progress_1.accuracy_score = ai_feedback_1["accuracy_score"]
        progress_1.status = "ASSESSED"

        # 為第二個項目創建新評估
        ai_feedback_2 = {
            "accuracy_score": 85.0,
            "detailed_words": [
                {
                    "word": "Word2",
                    "accuracy_score": 85.0,
                    "phonemes": [{"phoneme": "w", "accuracy_score": 85.0}],
                }
            ],
        }

        progress_2 = StudentItemProgress(
            student_assignment_id=data["student_assignment"].id,
            content_item_id=items[1].id,
            ai_feedback=json.dumps(ai_feedback_2),
            accuracy_score=ai_feedback_2["accuracy_score"],
            status="ASSESSED",
        )
        db_session.add(progress_2)
        db_session.commit()

        # 驗證每個項目的評估是獨立的
        all_progress = (
            db_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id
                == data["student_assignment"].id
            )
            .order_by(StudentItemProgress.content_item_id)
            .all()
        )

        assert len(all_progress) == 2
        assert all_progress[0].accuracy_score == 80.0
        assert all_progress[1].accuracy_score == 85.0

        # 驗證詳細資料也是獨立的
        ai_data_1 = json.loads(all_progress[0].ai_feedback)
        ai_data_2 = json.loads(all_progress[1].ai_feedback)

        assert ai_data_1["detailed_words"][0]["word"] == "Word1"
        assert ai_data_2["detailed_words"][0]["word"] == "Word2"


# 執行測試：
# pytest tests/integration/api/test_ai_assessment_enhanced.py -v
