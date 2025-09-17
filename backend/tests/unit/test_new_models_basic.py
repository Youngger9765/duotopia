# Basic Tests for New Models - using existing test patterns

import pytest
from decimal import Decimal
from models import ContentItem, StudentItemProgress


class TestNewModelsBasic:
    """Basic tests to verify new models are properly defined"""

    def test_content_item_model_exists(self):
        """Test that ContentItem model is properly defined"""
        # Test that the model can be imported and has expected attributes
        assert hasattr(ContentItem, "id")
        assert hasattr(ContentItem, "content_id")
        assert hasattr(ContentItem, "order_index")
        assert hasattr(ContentItem, "text")
        assert hasattr(ContentItem, "translation")
        assert hasattr(ContentItem, "audio_url")
        assert hasattr(ContentItem, "item_metadata")
        assert hasattr(ContentItem, "created_at")
        assert hasattr(ContentItem, "updated_at")

    def test_student_item_progress_model_exists(self):
        """Test that StudentItemProgress model is properly defined"""
        # Test that the model can be imported and has expected attributes
        assert hasattr(StudentItemProgress, "id")
        assert hasattr(StudentItemProgress, "student_assignment_id")
        assert hasattr(StudentItemProgress, "content_item_id")
        assert hasattr(StudentItemProgress, "recording_url")
        assert hasattr(StudentItemProgress, "answer_text")
        assert hasattr(StudentItemProgress, "submitted_at")
        assert hasattr(StudentItemProgress, "accuracy_score")
        assert hasattr(StudentItemProgress, "fluency_score")
        assert hasattr(StudentItemProgress, "pronunciation_score")
        assert hasattr(StudentItemProgress, "ai_feedback")
        assert hasattr(StudentItemProgress, "ai_assessed_at")
        assert hasattr(StudentItemProgress, "status")
        assert hasattr(StudentItemProgress, "attempts")
        assert hasattr(StudentItemProgress, "created_at")
        assert hasattr(StudentItemProgress, "updated_at")

    def test_model_table_names(self):
        """Test that models have correct table names"""
        assert ContentItem.__tablename__ == "content_items"
        assert StudentItemProgress.__tablename__ == "student_item_progress"

    def test_model_relationships_defined(self):
        """Test that relationships are properly defined"""
        # Check ContentItem relationships
        assert hasattr(ContentItem, "content")
        assert hasattr(ContentItem, "student_progress")

        # Check StudentItemProgress relationships
        assert hasattr(StudentItemProgress, "student_assignment")
        assert hasattr(StudentItemProgress, "content_item")
