#!/usr/bin/env python3
"""
測試多題目AI評估功能
驗證錄音和AI評分的正確存取
"""
import pytest
from sqlalchemy.orm import Session
from routers.speech_assessment import save_assessment_result
from models import StudentContentProgress, AssignmentStatus


class TestMultiQuestionAIAssessment:
    """測試多題目AI評估功能"""

    def test_single_question_ai_scores_storage(self, db_session: Session):
        """測試單題目的AI評分存取"""
        # 創建測試資料
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=1,
            status=AssignmentStatus.IN_PROGRESS,
            ai_scores={},
            response_data={},
        )
        db_session.add(progress)
        db_session.commit()

        # 模擬AI評估結果
        assessment_result = {
            "accuracy_score": 85.5,
            "fluency_score": 90.0,
            "completeness_score": 88.0,
            "pronunciation_score": 87.5,
            "words": [{"word": "hello", "accuracy_score": 95}],
        }

        # 執行保存（單題目，不傳 item_index）
        updated_progress = save_assessment_result(
            db=db_session,
            progress_id=progress.id,
            assessment_result=assessment_result,
            item_index=None,  # 單題目
        )

        # 驗證結果
        assert updated_progress.ai_scores["accuracy_score"] == 85.5
        assert updated_progress.ai_scores["fluency_score"] == 90.0
        assert "items" not in updated_progress.ai_scores  # 單題目不應該有 items 結構

    def test_multi_question_ai_scores_storage(self, db_session: Session):
        """測試多題目的AI評分存取"""
        # 創建測試資料
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=1,
            status=AssignmentStatus.IN_PROGRESS,
            ai_scores={},
            response_data={},
        )
        db_session.add(progress)
        db_session.commit()

        # 第1題的AI評估
        assessment_result_1 = {
            "accuracy_score": 85.5,
            "fluency_score": 90.0,
            "completeness_score": 88.0,
            "pronunciation_score": 87.5,
            "words": [{"word": "hello", "accuracy_score": 95}],
        }

        updated_progress = save_assessment_result(
            db=db_session,
            progress_id=progress.id,
            assessment_result=assessment_result_1,
            item_index=0,  # 第1題
        )

        # 驗證第1題的結果
        assert "items" in updated_progress.ai_scores
        assert "0" in updated_progress.ai_scores["items"]
        assert updated_progress.ai_scores["items"]["0"]["accuracy_score"] == 85.5

        # 第2題的AI評估
        assessment_result_2 = {
            "accuracy_score": 92.0,
            "fluency_score": 88.5,
            "completeness_score": 90.0,
            "pronunciation_score": 89.0,
            "words": [{"word": "world", "accuracy_score": 98}],
        }

        updated_progress = save_assessment_result(
            db=db_session,
            progress_id=progress.id,
            assessment_result=assessment_result_2,
            item_index=1,  # 第2題
        )

        # 驗證兩題的結果都存在
        assert "0" in updated_progress.ai_scores["items"]  # 第1題還在
        assert "1" in updated_progress.ai_scores["items"]  # 第2題也在
        assert (
            updated_progress.ai_scores["items"]["0"]["accuracy_score"] == 85.5
        )  # 第1題沒被覆蓋
        assert (
            updated_progress.ai_scores["items"]["1"]["accuracy_score"] == 92.0
        )  # 第2題正確

    def test_multi_question_recordings_storage(self, db_session: Session):
        """測試多題目的錄音存取"""
        # 創建測試資料
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=1,
            status=AssignmentStatus.IN_PROGRESS,
            response_data={"recordings": []},
        )
        db_session.add(progress)
        db_session.commit()

        # 模擬前端保存錄音陣列
        recordings = ["", "audio_url_2", "", "audio_url_4"]  # 第2題和第4題有錄音

        # 正確更新 response_data - 需要重新賦值整個字典
        new_response_data = progress.response_data.copy()
        new_response_data["recordings"] = recordings
        progress.response_data = new_response_data

        # 標記 JSON 欄位已修改
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(progress, "response_data")

        db_session.commit()
        db_session.refresh(progress)

        # 驗證錄音陣列正確保存
        saved_recordings = progress.response_data["recordings"]
        assert len(saved_recordings) == 4
        assert saved_recordings[1] == "audio_url_2"  # 第2題的錄音
        assert saved_recordings[3] == "audio_url_4"  # 第4題的錄音
        assert saved_recordings[0] == ""  # 第1題沒錄音
        assert saved_recordings[2] == ""  # 第3題沒錄音

    def test_ai_assessment_api_with_item_index(self, db_session: Session):
        """測試AI評估API是否正確處理item_index"""
        # 這個測試需要mock speech_assessment API
        # 驗證API呼叫時是否正確傳遞item_index

        # 創建測試資料
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=1,
            status=AssignmentStatus.IN_PROGRESS,
            ai_scores={},
            response_data={},
        )
        db_session.add(progress)
        db_session.commit()

        # Mock評估結果
        mock_result = {
            "accuracy_score": 85.0,
            "fluency_score": 90.0,
            "completeness_score": 88.0,
            "pronunciation_score": 87.0,
            "words": [],
        }

        # 測試不同題目索引
        for item_index in [0, 1, 2]:
            updated_progress = save_assessment_result(
                db=db_session,
                progress_id=progress.id,
                assessment_result=mock_result,
                item_index=item_index,
            )

            # 驗證每個題目的評分都獨立存在
            assert str(item_index) in updated_progress.ai_scores["items"]
            assert (
                updated_progress.ai_scores["items"][str(item_index)]["accuracy_score"]
                == 85.0
            )

    def test_page_reload_data_persistence(self, db_session: Session):
        """測試頁面重新載入後資料持久性"""
        # 創建完整的測試場景
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=1,
            status=AssignmentStatus.IN_PROGRESS,
            ai_scores={
                "items": {
                    "0": {"accuracy_score": 85, "fluency_score": 90},
                    "1": {"accuracy_score": 92, "fluency_score": 88},
                    "2": {"accuracy_score": 78, "fluency_score": 85},
                }
            },
            response_data={"recordings": ["url1", "url2", "url3"]},
        )
        db_session.add(progress)
        db_session.commit()

        # 模擬頁面重新載入，重新查詢資料
        progress_id = progress.id  # 保存 ID
        db_session.expunge_all()  # 清除session快取
        reloaded_progress = (
            db_session.query(StudentContentProgress).filter_by(id=progress_id).first()
        )

        # 驗證所有資料都正確載入
        assert reloaded_progress is not None
        assert "items" in reloaded_progress.ai_scores
        assert len(reloaded_progress.ai_scores["items"]) == 3
        assert reloaded_progress.ai_scores["items"]["0"]["accuracy_score"] == 85
        assert reloaded_progress.ai_scores["items"]["1"]["accuracy_score"] == 92
        assert reloaded_progress.ai_scores["items"]["2"]["accuracy_score"] == 78

        assert len(reloaded_progress.response_data["recordings"]) == 3
        assert reloaded_progress.response_data["recordings"][0] == "url1"
        assert reloaded_progress.response_data["recordings"][1] == "url2"
        assert reloaded_progress.response_data["recordings"][2] == "url3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
