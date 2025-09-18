# Unit Tests for ContentItem Model

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database import Base
from models import Content, ContentItem, Teacher


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_teacher(db_session):
    """Create a sample teacher"""
    teacher = Teacher(
        email="test@example.com", password_hash="hashed_password", name="Test Teacher"
    )
    db_session.add(teacher)
    db_session.commit()
    return teacher


class TestContentItemModel:
    """Test ContentItem model functionality"""

    def test_content_item_creation(self, db_session, sample_teacher):
        """Test basic ContentItem creation"""
        # Create content first
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        # Create content item
        content_item = ContentItem(
            content_id=content.id, order_index=0, text="Hello world", translation="你好世界"
        )
        db_session.add(content_item)
        db_session.commit()

        # Verify
        assert content_item.id is not None
        assert content_item.content_id == content.id
        assert content_item.order_index == 0
        assert content_item.text == "Hello world"
        assert content_item.translation == "你好世界"
        assert content_item.created_at is not None
        assert content_item.updated_at is not None

    def test_content_item_required_fields(self, db_session, sample_teacher):
        """Test that required fields are enforced"""
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        # Missing text should fail
        with pytest.raises(IntegrityError):
            content_item = ContentItem(
                content_id=content.id,
                order_index=0
                # Missing text
            )
            db_session.add(content_item)
            db_session.commit()

        db_session.rollback()

        # Missing content_id should fail
        with pytest.raises(IntegrityError):
            content_item = ContentItem(
                order_index=0,
                text="Hello world"
                # Missing content_id
            )
            db_session.add(content_item)
            db_session.commit()

        db_session.rollback()

        # Missing order_index should fail
        with pytest.raises(IntegrityError):
            content_item = ContentItem(
                content_id=content.id,
                text="Hello world"
                # Missing order_index
            )
            db_session.add(content_item)
            db_session.commit()

    def test_content_item_unique_constraint(self, db_session, sample_teacher):
        """Test unique constraint on (content_id, order_index)"""
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        # Create first item
        item1 = ContentItem(content_id=content.id, order_index=0, text="First item")
        db_session.add(item1)
        db_session.commit()

        # Try to create second item with same order_index
        with pytest.raises(IntegrityError):
            item2 = ContentItem(
                content_id=content.id,
                order_index=0,  # Same order_index
                text="Second item",
            )
            db_session.add(item2)
            db_session.commit()

    def test_content_item_foreign_key_cascade(self, db_session, sample_teacher):
        """Test CASCADE DELETE when content is deleted"""
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        # Create content items
        item1 = ContentItem(content_id=content.id, order_index=0, text="Item 1")
        item2 = ContentItem(content_id=content.id, order_index=1, text="Item 2")
        db_session.add_all([item1, item2])
        db_session.commit()

        # Verify items exist
        items = db_session.query(ContentItem).filter_by(content_id=content.id).all()
        assert len(items) == 2

        # Delete content
        db_session.delete(content)
        db_session.commit()

        # Verify items are also deleted (CASCADE)
        items = db_session.query(ContentItem).filter_by(content_id=content.id).all()
        assert len(items) == 0

    def test_content_item_ordering(self, db_session, sample_teacher):
        """Test content items are properly ordered"""
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        # Create items in random order
        items_data = [(2, "Third item"), (0, "First item"), (1, "Second item")]

        for order_index, text in items_data:
            item = ContentItem(
                content_id=content.id, order_index=order_index, text=text
            )
            db_session.add(item)

        db_session.commit()

        # Query ordered items
        ordered_items = (
            db_session.query(ContentItem)
            .filter_by(content_id=content.id)
            .order_by(ContentItem.order_index)
            .all()
        )

        assert len(ordered_items) == 3
        assert ordered_items[0].text == "First item"
        assert ordered_items[1].text == "Second item"
        assert ordered_items[2].text == "Third item"

    def test_content_item_optional_fields(self, db_session, sample_teacher):
        """Test optional fields work correctly"""
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        # Create item with all optional fields
        item = ContentItem(
            content_id=content.id,
            order_index=0,
            text="Hello world",
            translation="你好世界",
            audio_url="https://example.com/audio.mp3",
            item_metadata={"difficulty": "easy", "theme": "greetings"},
        )
        db_session.add(item)
        db_session.commit()

        # Verify optional fields
        assert item.translation == "你好世界"
        assert item.audio_url == "https://example.com/audio.mp3"
        assert item.item_metadata["difficulty"] == "easy"
        assert item.item_metadata["theme"] == "greetings"

        # Create item without optional fields
        item2 = ContentItem(content_id=content.id, order_index=1, text="Goodbye")
        db_session.add(item2)
        db_session.commit()

        # Verify defaults
        assert item2.translation is None
        assert item2.audio_url is None
        assert item2.item_metadata == {}

    def test_content_item_relationship(self, db_session, sample_teacher):
        """Test relationship with Content model"""
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        item = ContentItem(content_id=content.id, order_index=0, text="Test item")
        db_session.add(item)
        db_session.commit()

        # Test accessing content through relationship
        assert item.content.title == "Test Content"
        assert item.content.teacher_id == sample_teacher.id

        # Test accessing items through content
        assert len(content.content_items) == 1
        assert content.content_items[0].text == "Test item"

    def test_content_item_timestamps(self, db_session, sample_teacher):
        """Test that timestamps are automatically set and updated"""
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=sample_teacher.id
        )
        db_session.add(content)
        db_session.flush()

        item = ContentItem(content_id=content.id, order_index=0, text="Test item")
        db_session.add(item)
        db_session.commit()

        # Check initial timestamps
        created_at = item.created_at
        updated_at = item.updated_at
        assert created_at is not None
        assert updated_at is not None
        assert created_at == updated_at

        # Update the item
        item.text = "Updated text"
        db_session.commit()

        # Check updated timestamp changed
        db_session.refresh(item)
        assert item.updated_at > updated_at
        assert item.created_at == created_at  # Created_at should not change
