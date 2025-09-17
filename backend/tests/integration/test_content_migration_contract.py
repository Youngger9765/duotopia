# TDD Contract Tests for Content Migration
# Tests the core contracts defined in TDD_CONTRACT.md

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import app
from database import get_db
from models import (
    User, Content, ContentItem, StudentAssignment, 
    StudentContentProgress, StudentItemProgress, Classroom
)
from tests.fixtures.db_fixtures import test_db, test_client
from tests.fixtures.user_fixtures import test_teacher, test_student, test_classroom
import io
import os
from decimal import Decimal
from datetime import datetime


class TestContentMigrationContract:
    """
    TDD Contract Tests ensuring all Content functionality works with new architecture
    """

    def setup_method(self):
        """Setup test data for each test"""
        self.audio_content = b"fake audio content"
        self.audio_file = ("test_audio.webm", io.BytesIO(self.audio_content), "audio/webm")

    def create_test_assignment_with_3_items(self, db: Session, teacher: User, student: User) -> StudentAssignment:
        """Helper: Create assignment with 3 content items"""
        # Create content with 3 items
        content = Content(
            title="Test Pronunciation",
            type="pronunciation",
            teacher_id=teacher.id
        )
        db.add(content)
        db.flush()

        # Create 3 content items
        items_data = [
            {"text": "Good morning", "translation": "早安"},
            {"text": "Good afternoon", "translation": "午安"},
            {"text": "Good evening", "translation": "晚安"}
        ]
        
        for i, item_data in enumerate(items_data):
            content_item = ContentItem(
                content_id=content.id,
                order_index=i,
                text=item_data["text"],
                translation=item_data["translation"]
            )
            db.add(content_item)

        # Create classroom
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=teacher.id
        )
        db.add(classroom)
        db.flush()

        # Create assignment
        assignment = StudentAssignment(
            student_id=student.id,
            teacher_id=teacher.id,
            classroom_id=classroom.id,
            content_id=content.id,
            title="Test Assignment"
        )
        db.add(assignment)
        db.flush()

        # Create initial progress record
        progress = StudentContentProgress(
            student_assignment_id=assignment.id,
            content_id=content.id,
            order_index=0,
            total_items=3,
            completed_items=0,
            completion_rate=0.0
        )
        db.add(progress)
        
        db.commit()
        return assignment

    @pytest.mark.asyncio
    async def test_student_recording_upload_contract(self, test_client: TestClient, test_db: Session, 
                                                   test_teacher: User, test_student: User):
        """
        Contract 1: 學生上傳錄音後，資料正確儲存到新結構
        """
        # Given: 學生有一個作業，包含3題
        assignment = self.create_test_assignment_with_3_items(test_db, test_teacher, test_student)
        
        # Login as student
        login_response = test_client.post("/api/auth/login", json={
            "email": test_student.email,
            "password": "student123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # When: 學生上傳第2題的錄音 (index=1)
        with open("test_audio.webm", "wb") as f:
            f.write(self.audio_content)
        
        try:
            with open("test_audio.webm", "rb") as f:
                response = test_client.post(
                    f"/api/students/{test_student.id}/assignments/{assignment.id}/upload-recording",
                    headers=headers,
                    data={"content_item_index": "1"},
                    files={"audio_file": ("test_audio.webm", f, "audio/webm")}
                )

            # Then: Response is successful
            assert response.status_code == 200, f"Upload failed: {response.text}"

            # 1. StudentItemProgress 正確更新
            item_progress = test_db.query(StudentItemProgress).filter(
                StudentItemProgress.student_assignment_id == assignment.id
            ).filter_by(content_item_id=test_db.query(ContentItem).filter_by(
                content_id=assignment.content_id, order_index=1
            ).first().id).first()
            
            assert item_progress is not None, "StudentItemProgress record not created"
            assert item_progress.recording_url is not None, "Recording URL not set"
            assert item_progress.status == 'COMPLETED', f"Status should be COMPLETED, got {item_progress.status}"

            # 2. 其他題目不受影響
            item_0_content = test_db.query(ContentItem).filter_by(
                content_id=assignment.content_id, order_index=0
            ).first()
            item_2_content = test_db.query(ContentItem).filter_by(
                content_id=assignment.content_id, order_index=2
            ).first()

            item_0_progress = test_db.query(StudentItemProgress).filter_by(
                student_assignment_id=assignment.id,
                content_item_id=item_0_content.id
            ).first()
            item_2_progress = test_db.query(StudentItemProgress).filter_by(
                student_assignment_id=assignment.id,
                content_item_id=item_2_content.id
            ).first()

            # These should either not exist or have no recording_url
            if item_0_progress:
                assert item_0_progress.recording_url is None, "Item 0 should not have recording"
            if item_2_progress:
                assert item_2_progress.recording_url is None, "Item 2 should not have recording"

            # 3. 摘要統計自動更新
            summary = test_db.query(StudentContentProgress).filter_by(
                student_assignment_id=assignment.id
            ).first()
            assert summary.completed_items == 1, f"Completed items should be 1, got {summary.completed_items}"
            assert abs(summary.completion_rate - 33.33) < 0.1, f"Completion rate should be ~33.33, got {summary.completion_rate}"

        finally:
            # Cleanup
            if os.path.exists("test_audio.webm"):
                os.remove("test_audio.webm")

    @pytest.mark.asyncio 
    async def test_student_activities_view_contract(self, test_client: TestClient, test_db: Session,
                                                  test_teacher: User, test_student: User):
        """
        Contract 2: 學生檢視活動時，看到正確的題目和進度
        """
        # Given: 學生已完成第1題，第2題進行中
        assignment = self.create_test_assignment_with_3_items(test_db, test_teacher, test_student)
        
        # Create progress records
        content_items = test_db.query(ContentItem).filter_by(
            content_id=assignment.content_id
        ).order_by(ContentItem.order_index).all()

        # Item 1 completed
        item1_progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_items[0].id,
            recording_url="https://example.com/recording1.webm",
            status="COMPLETED",
            accuracy_score=Decimal("85.5"),
            fluency_score=Decimal("78.9")
        )
        test_db.add(item1_progress)

        # Item 2 in progress
        item2_progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_items[1].id,
            status="IN_PROGRESS"
        )
        test_db.add(item2_progress)
        test_db.commit()

        # Login as student
        login_response = test_client.post("/api/auth/login", json={
            "email": test_student.email,
            "password": "student123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # When: 學生檢視活動
        response = test_client.get(
            f"/api/students/{test_student.id}/assignments/{assignment.id}/activities",
            headers=headers
        )

        # Then: 
        assert response.status_code == 200, f"Activities view failed: {response.text}"
        activities = response.json()

        # 1. 題目內容正確顯示
        assert len(activities) >= 1, "Should have at least 1 content"
        content1 = activities[0]
        assert len(content1['items']) == 3, f"Content should have 3 items, got {len(content1['items'])}"

        # 2. 進度狀態正確
        item1 = content1['items'][0]
        assert item1['status'] == 'COMPLETED', f"Item 1 should be COMPLETED, got {item1['status']}"
        assert item1['recording_url'] is not None, "Item 1 should have recording URL"

        item2 = content1['items'][1]
        assert item2['status'] == 'IN_PROGRESS', f"Item 2 should be IN_PROGRESS, got {item2['status']}"

        # 3. AI 評分正確對應
        assert float(item1['accuracy_score']) == 85.5, f"Accuracy score should be 85.5, got {item1['accuracy_score']}"
        assert float(item1['fluency_score']) == 78.9, f"Fluency score should be 78.9, got {item1['fluency_score']}"

    @pytest.mark.asyncio
    async def test_ai_assessment_storage_contract(self, test_client: TestClient, test_db: Session,
                                                test_teacher: User, test_student: User):
        """
        Contract 3: AI 評分正確儲存到對應的題目
        """
        # Given: 學生已上傳第3題錄音
        assignment = self.create_test_assignment_with_3_items(test_db, test_teacher, test_student)
        
        content_items = test_db.query(ContentItem).filter_by(
            content_id=assignment.content_id
        ).order_by(ContentItem.order_index).all()

        # Create recorded item progress for item 3 (index 2)
        item_progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_items[2].id,
            recording_url="https://example.com/recording3.webm",
            status="SUBMITTED"
        )
        test_db.add(item_progress)
        test_db.commit()

        # When: AI 評分系統評分
        ai_result = {
            'accuracy_score': 92.5,
            'fluency_score': 88.3,
            'pronunciation_score': 95.1,
            'feedback': 'Excellent pronunciation!'
        }

        # Login as teacher (typically AI service would use service account)
        login_response = test_client.post("/api/auth/login", json={
            "email": test_teacher.email,
            "password": "teacher123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Simulate AI assessment update
        response = test_client.put(
            f"/api/students/{test_student.id}/assignments/{assignment.id}/items/{content_items[2].id}/assessment",
            headers=headers,
            json=ai_result
        )

        # Then:
        assert response.status_code == 200, f"AI assessment storage failed: {response.text}"

        # 1. 評分正確儲存
        updated_progress = test_db.query(StudentItemProgress).filter_by(
            id=item_progress.id
        ).first()
        assert float(updated_progress.accuracy_score) == 92.5
        assert float(updated_progress.fluency_score) == 88.3  
        assert float(updated_progress.pronunciation_score) == 95.1
        assert updated_progress.ai_feedback == 'Excellent pronunciation!'

        # 2. 時間戳記更新
        assert updated_progress.ai_assessed_at is not None

        # 3. 摘要統計更新
        summary = test_db.query(StudentContentProgress).filter_by(
            student_assignment_id=assignment.id
        ).first()
        assert summary.average_accuracy is not None

    @pytest.mark.asyncio
    async def test_teacher_progress_view_contract(self, test_client: TestClient, test_db: Session,
                                                test_teacher: User, test_student: User):
        """
        Contract 4: 老師可以檢視每個學生每題的詳細進度
        """
        # Given: 創建作業，學生有不同進度
        assignment = self.create_test_assignment_with_3_items(test_db, test_teacher, test_student)
        
        # Login as teacher
        login_response = test_client.post("/api/auth/login", json={
            "email": test_teacher.email, 
            "password": "teacher123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # When: 老師檢視作業進度
        response = test_client.get(
            f"/api/teachers/{test_teacher.id}/assignments/{assignment.id}/progress",
            headers=headers
        )

        # Then:
        assert response.status_code == 200, f"Teacher progress view failed: {response.text}"
        progress_data = response.json()

        # 1. 可以看到學生的進度
        assert 'students' in progress_data or 'student_progress' in progress_data
        # Since we only have 1 student in test, adapt accordingly
        
        # 2. 包含必要的統計資料
        if 'statistics' in progress_data:
            stats = progress_data['statistics']
            assert 'completion_rate' in stats or 'average_score' in stats

    @pytest.mark.asyncio
    async def test_teacher_content_creation_contract(self, test_client: TestClient, test_db: Session,
                                                   test_teacher: User):
        """
        Contract 5: 老師創建課程內容時，自動創建 ContentItem
        """
        # Given: 老師要創建包含5題的朗讀練習
        content_data = {
            'title': 'Daily Greetings',
            'type': 'pronunciation',
            'items': [
                {'text': 'Good morning', 'translation': '早安'},
                {'text': 'Good afternoon', 'translation': '午安'},
                {'text': 'Good evening', 'translation': '晚安'},
                {'text': 'Good night', 'translation': '晚安'},
                {'text': 'Have a nice day', 'translation': '祝你有美好的一天'}
            ]
        }

        # Login as teacher
        login_response = test_client.post("/api/auth/login", json={
            "email": test_teacher.email,
            "password": "teacher123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # When: 老師創建內容
        response = test_client.post(
            f"/api/teachers/{test_teacher.id}/contents",
            headers=headers,
            json=content_data
        )

        # Then:
        assert response.status_code == 201, f"Content creation failed: {response.text}"
        content_id = response.json()['id']

        # 1. Content 記錄創建
        content = test_db.query(Content).filter_by(id=content_id).first()
        assert content is not None
        assert content.title == 'Daily Greetings'

        # 2. ContentItem 記錄自動創建
        items = test_db.query(ContentItem).filter_by(content_id=content_id).order_by(ContentItem.order_index).all()
        assert len(items) == 5, f"Should have 5 content items, got {len(items)}"

        # 3. 順序正確
        for i, item in enumerate(items):
            assert item.order_index == i, f"Item {i} should have order_index {i}, got {item.order_index}"
            assert item.text == content_data['items'][i]['text']
            assert item.translation == content_data['items'][i]['translation']