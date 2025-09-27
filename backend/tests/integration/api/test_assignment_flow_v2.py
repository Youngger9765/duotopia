"""
測試完整作業流程 V2 - 使用新的 StudentItemProgress 架構
這是核心的 E2E 測試，確保整個作業流程正常運作
"""

from sqlalchemy.orm import Session
from models import StudentItemProgress
from tests.factories import TestDataFactory
import json


class TestAssignmentFlowV2:
    """測試新架構下的完整作業流程"""

    def test_create_assignment_with_content_items(self, db_session: Session):
        """測試創建作業並正確建立 ContentItem 關聯"""
        # 建立基礎資料
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            content_items=[
                {"text": "Hello, how are you?", "translation": "你好嗎？"},
                {"text": "Nice to meet you", "translation": "很高興認識你"},
                {"text": "What's your name?", "translation": "你叫什麼名字？"},
            ],
        )

        # 驗證 ContentItem 被正確創建
        content = data["content"]
        assert len(content.content_items) == 3
        assert content.content_items[0].text == "Hello, how are you?"
        assert content.content_items[1].text == "Nice to meet you"
        assert content.content_items[2].text == "What's your name?"

        # 驗證每個 ContentItem 都有正確的 order_index
        for idx, item in enumerate(content.content_items):
            assert item.order_index == idx

    def test_student_progress_per_content_item(self, db_session: Session):
        """測試每個 ContentItem 都有獨立的進度記錄"""
        # 建立資料
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            content_items=[
                {"text": "Question 1", "translation": "問題1"},
                {"text": "Question 2", "translation": "問題2"},
            ],
        )

        student_assignment = data["student_assignment"]
        content_items = data["content"].content_items

        # 為每個 ContentItem 創建進度記錄
        for item in content_items:
            progress = StudentItemProgress(
                student_assignment_id=student_assignment.id,
                content_item_id=item.id,
                status="NOT_STARTED",
            )
            db_session.add(progress)
        db_session.commit()

        # 驗證進度記錄
        progress_records = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == student_assignment.id)
            .all()
        )

        assert len(progress_records) == 2
        for progress in progress_records:
            assert progress.status == "NOT_STARTED"
            assert progress.content_item_id in [item.id for item in content_items]

    def test_upload_recording_to_content_item(self, db_session: Session):
        """測試上傳錄音到特定的 ContentItem"""
        # 建立資料
        data = TestDataFactory.create_full_assignment_chain(
            db_session, content_items=[{"text": "Test question", "translation": "測試題目"}]
        )

        student_assignment = data["student_assignment"]
        content_item = data["content"].content_items[0]

        # 創建或更新進度記錄
        progress = StudentItemProgress(
            student_assignment_id=student_assignment.id,
            content_item_id=content_item.id,
            recording_url="https://storage.example.com/recording1.webm",
            status="SUBMITTED",
        )
        db_session.add(progress)
        db_session.commit()

        # 驗證錄音被正確儲存
        saved_progress = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.content_item_id == content_item.id)
            .first()
        )

        assert saved_progress is not None
        assert (
            saved_progress.recording_url
            == "https://storage.example.com/recording1.webm"
        )
        assert saved_progress.status == "SUBMITTED"

    def test_ai_feedback_per_content_item(self, db_session: Session):
        """測試每個 ContentItem 的 AI 評分"""
        # 建立資料
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            content_items=[{"text": "Practice sentence", "translation": "練習句子"}],
        )

        student_assignment = data["student_assignment"]
        content_item = data["content"].content_items[0]

        # AI 評分資料
        ai_scores = {
            "accuracy_score": 92.5,
            "fluency_score": 88.0,
            "pronunciation_score": 90.0,
            "completeness_score": 95.0,
            "overall_score": 91.4,
            "detailed_words": [
                {
                    "word": "Practice",
                    "accuracy_score": 95.0,
                    "index": 0,
                    "syllables": [
                        {"syllable": "Prac", "accuracy_score": 96.0, "index": 0},
                        {"syllable": "tice", "accuracy_score": 94.0, "index": 1},
                    ],
                    "phonemes": [
                        {"phoneme": "p", "accuracy_score": 98.0, "index": 0},
                        {"phoneme": "r", "accuracy_score": 92.0, "index": 1},
                        {"phoneme": "æ", "accuracy_score": 95.0, "index": 2},
                    ],
                }
            ],
        }

        # 儲存 AI 評分
        progress = StudentItemProgress(
            student_assignment_id=student_assignment.id,
            content_item_id=content_item.id,
            recording_url="https://storage.example.com/recording.webm",
            ai_feedback=json.dumps(ai_scores),
            accuracy_score=ai_scores["accuracy_score"],
            fluency_score=ai_scores["fluency_score"],
            pronunciation_score=ai_scores["pronunciation_score"],
            status="ASSESSED",
            ai_assessed_at=db_session.execute("SELECT CURRENT_TIMESTAMP").scalar(),
        )
        db_session.add(progress)
        db_session.commit()

        # 驗證 AI 評分
        saved_progress = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.content_item_id == content_item.id)
            .first()
        )

        assert saved_progress.accuracy_score == 92.5
        assert saved_progress.fluency_score == 88.0
        assert saved_progress.pronunciation_score == 90.0
        assert saved_progress.status == "ASSESSED"

        # 驗證詳細評分資料
        saved_ai_feedback = json.loads(saved_progress.ai_feedback)
        assert "detailed_words" in saved_ai_feedback
        assert len(saved_ai_feedback["detailed_words"]) == 1
        assert saved_ai_feedback["detailed_words"][0]["word"] == "Practice"

    def test_teacher_feedback_per_content_item(self, db_session: Session):
        """測試教師對每個 ContentItem 的批改"""
        # 建立資料
        data = TestDataFactory.create_full_assignment_chain(db_session)

        student_assignment = data["student_assignment"]
        content_item = data["content"].content_items[0]

        # 先創建學生提交
        progress = StudentItemProgress(
            student_assignment_id=student_assignment.id,
            content_item_id=content_item.id,
            recording_url="https://storage.example.com/recording.webm",
            status="SUBMITTED",
        )
        db_session.add(progress)
        db_session.commit()

        # 教師批改
        progress.teacher_feedback = "Great pronunciation! Keep practicing."
        progress.teacher_review_score = 85
        progress.teacher_passed = True
        progress.review_status = "REVIEWED"
        progress.teacher_id = data["teacher"].id
        db_session.commit()

        # 驗證教師批改
        saved_progress = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.content_item_id == content_item.id)
            .first()
        )

        assert (
            saved_progress.teacher_feedback == "Great pronunciation! Keep practicing."
        )
        assert saved_progress.teacher_review_score == 85
        assert saved_progress.teacher_passed is True
        assert saved_progress.review_status == "REVIEWED"
        assert saved_progress.teacher_id == data["teacher"].id

    def test_complete_assignment_workflow(self, db_session: Session):
        """測試完整的作業工作流程：創建 -> 錄音 -> AI評分 -> 教師批改"""
        # 1. 創建作業
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            content_items=[
                {"text": "Question 1", "translation": "題目1"},
                {"text": "Question 2", "translation": "題目2"},
            ],
        )

        student_assignment = data["student_assignment"]
        content_items = data["content"].content_items

        # 2. 學生完成錄音
        for idx, item in enumerate(content_items):
            progress = StudentItemProgress(
                student_assignment_id=student_assignment.id,
                content_item_id=item.id,
                recording_url=f"https://storage.example.com/recording{idx+1}.webm",
                status="SUBMITTED",
            )
            db_session.add(progress)
        db_session.commit()

        # 3. AI 評分
        for progress in (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == student_assignment.id)
            .all()
        ):
            ai_scores = {
                "accuracy_score": 85 + (progress.content_item_id % 10),
                "fluency_score": 80 + (progress.content_item_id % 10),
                "pronunciation_score": 82 + (progress.content_item_id % 10),
                "overall_score": 82.3,
            }
            progress.ai_feedback = json.dumps(ai_scores)
            progress.accuracy_score = ai_scores["accuracy_score"]
            progress.fluency_score = ai_scores["fluency_score"]
            progress.pronunciation_score = ai_scores["pronunciation_score"]
            progress.status = "ASSESSED"
        db_session.commit()

        # 4. 教師批改
        for progress in (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == student_assignment.id)
            .all()
        ):
            progress.teacher_feedback = f"Feedback for item {progress.content_item_id}"
            progress.teacher_review_score = 90
            progress.teacher_passed = True
            progress.review_status = "REVIEWED"
            progress.teacher_id = data["teacher"].id
        db_session.commit()

        # 5. 驗證完整流程
        all_progress = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == student_assignment.id)
            .all()
        )

        assert len(all_progress) == 2
        for progress in all_progress:
            # 驗證每個階段的資料都存在
            assert progress.recording_url is not None
            assert progress.ai_feedback is not None
            assert progress.teacher_feedback is not None
            assert progress.status == "ASSESSED"
            assert progress.review_status == "REVIEWED"
            assert progress.teacher_passed is True

    def test_progress_independence_between_items(self, db_session: Session):
        """測試不同 ContentItem 的進度是獨立的"""
        # 建立資料
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            content_items=[
                {"text": "Item 1", "translation": "項目1"},
                {"text": "Item 2", "translation": "項目2"},
                {"text": "Item 3", "translation": "項目3"},
            ],
        )

        student_assignment = data["student_assignment"]
        items = data["content"].content_items

        # 不同項目設置不同狀態
        statuses = ["NOT_STARTED", "SUBMITTED", "ASSESSED"]
        for idx, item in enumerate(items):
            progress = StudentItemProgress(
                student_assignment_id=student_assignment.id,
                content_item_id=item.id,
                status=statuses[idx],
            )
            if idx >= 1:  # 第二個項目有錄音
                progress.recording_url = f"recording{idx}.webm"
            if idx == 2:  # 第三個項目有 AI 評分
                progress.ai_feedback = json.dumps({"accuracy_score": 90})
            db_session.add(progress)
        db_session.commit()

        # 驗證每個項目的進度是獨立的
        all_progress = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == student_assignment.id)
            .order_by(StudentItemProgress.content_item_id)
            .all()
        )

        assert all_progress[0].status == "NOT_STARTED"
        assert all_progress[0].recording_url is None

        assert all_progress[1].status == "SUBMITTED"
        assert all_progress[1].recording_url == "recording1.webm"

        assert all_progress[2].status == "ASSESSED"
        assert all_progress[2].recording_url == "recording2.webm"
        assert all_progress[2].ai_feedback is not None


# 執行測試時可以使用：
# pytest tests/integration/api/test_assignment_flow_v2.py -v
