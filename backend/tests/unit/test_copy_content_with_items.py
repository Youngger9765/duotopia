"""
_copy_content_with_items 單元測試

確保深拷貝 Content + ContentItem 時所有欄位都被正確複製，
包含例句、單字集、例句重組等 Phase 2 欄位。
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from unittest.mock import Mock, MagicMock, patch, call
from copy import deepcopy

from services.program_service import _copy_content_with_items
from models.base import ContentType


def _make_mock_item(**overrides):
    """建立一個 mock ContentItem，所有欄位都有值。"""
    defaults = {
        "order_index": 1,
        "text": "apple",
        "translation": "蘋果",
        "audio_url": "https://example.com/apple.mp3",
        "example_sentence": "I eat an apple every day.",
        "example_sentence_translation": "我每天吃一顆蘋果。",
        "example_sentence_definition": "A round fruit with red skin.",
        "word_count": 6,
        "max_errors": 3,
        "image_url": "https://example.com/apple.jpg",
        "part_of_speech": "n.",
        "distractors": ["banana", "orange", "grape"],
        "item_metadata": {"source": "test"},
    }
    defaults.update(overrides)
    item = Mock()
    for key, value in defaults.items():
        setattr(item, key, value)
    return item


def _make_mock_content(content_items, **overrides):
    """建立一個 mock Content。"""
    defaults = {
        "title": "Test Vocabulary",
        "type": ContentType.VOCABULARY_SET,
        "level": "A1",
        "tags": ["fruit"],
        "is_public": False,
        "target_wpm": None,
        "target_accuracy": None,
        "time_limit_seconds": None,
        "order_index": 0,
        "is_active": True,
        "content_items": content_items,
    }
    defaults.update(overrides)
    content = Mock()
    for key, value in defaults.items():
        setattr(content, key, value)
    return content


class TestCopyContentWithItems:
    """_copy_content_with_items 函式測試"""

    def _setup_db(self):
        """建立 mock db session，追蹤 db.add() 的呼叫。"""
        db = Mock()
        db.flush = Mock()
        # 追蹤所有 db.add 呼叫的物件
        self.added_objects = []

        def track_add(obj):
            self.added_objects.append(obj)

        db.add = Mock(side_effect=track_add)
        return db

    def test_copies_all_content_item_fields_for_vocabulary_set(self):
        """單字集的所有欄位都被正確複製"""
        item = _make_mock_item(
            order_index=0,
            text="apple",
            translation="蘋果",
            audio_url="https://example.com/apple.mp3",
            example_sentence="I eat an apple.",
            example_sentence_translation="我吃一顆蘋果。",
            example_sentence_definition="A round fruit.",
            word_count=4,
            max_errors=3,
            image_url="https://example.com/apple.jpg",
            part_of_speech="n.",
            distractors=["banana", "orange", "grape"],
            item_metadata={"level": "basic"},
        )
        content = _make_mock_content([item])
        db = self._setup_db()

        with patch("services.program_service.Content") as MockContent, patch(
            "services.program_service.ContentItem"
        ) as MockContentItem:
            mock_new_content = Mock()
            mock_new_content.id = 99
            MockContent.return_value = mock_new_content

            _copy_content_with_items(content, new_lesson_id=10, db=db)

            # 驗證 ContentItem 被呼叫時帶了所有欄位
            MockContentItem.assert_called_once()
            kwargs = MockContentItem.call_args[1]

            assert kwargs["content_id"] == 99
            assert kwargs["order_index"] == 0
            assert kwargs["text"] == "apple"
            assert kwargs["translation"] == "蘋果"
            assert kwargs["audio_url"] == "https://example.com/apple.mp3"
            # 例句欄位
            assert kwargs["example_sentence"] == "I eat an apple."
            assert kwargs["example_sentence_translation"] == "我吃一顆蘋果。"
            assert kwargs["example_sentence_definition"] == "A round fruit."
            # 例句重組欄位
            assert kwargs["word_count"] == 4
            assert kwargs["max_errors"] == 3
            # 單字集欄位
            assert kwargs["image_url"] == "https://example.com/apple.jpg"
            assert kwargs["part_of_speech"] == "n."
            assert kwargs["distractors"] == ["banana", "orange", "grape"]
            # metadata
            assert kwargs["item_metadata"] == {"level": "basic"}

    def test_copies_multiple_items(self):
        """多個 ContentItem 都會被複製"""
        items = [
            _make_mock_item(order_index=0, text="apple"),
            _make_mock_item(order_index=1, text="banana"),
            _make_mock_item(order_index=2, text="cherry"),
        ]
        content = _make_mock_content(items)
        db = self._setup_db()

        with patch("services.program_service.Content") as MockContent, patch(
            "services.program_service.ContentItem"
        ) as MockContentItem:
            mock_new_content = Mock()
            mock_new_content.id = 99
            MockContent.return_value = mock_new_content

            _copy_content_with_items(content, new_lesson_id=10, db=db)

            assert MockContentItem.call_count == 3
            texts = [c[1]["text"] for c in MockContentItem.call_args_list]
            assert texts == ["apple", "banana", "cherry"]

    def test_handles_none_optional_fields(self):
        """可選欄位為 None 時不會出錯"""
        item = _make_mock_item(
            translation=None,
            audio_url=None,
            example_sentence=None,
            example_sentence_translation=None,
            example_sentence_definition=None,
            word_count=None,
            max_errors=None,
            image_url=None,
            part_of_speech=None,
            distractors=None,
            item_metadata=None,
        )
        content = _make_mock_content([item])
        db = self._setup_db()

        with patch("services.program_service.Content") as MockContent, patch(
            "services.program_service.ContentItem"
        ) as MockContentItem:
            mock_new_content = Mock()
            mock_new_content.id = 99
            MockContent.return_value = mock_new_content

            _copy_content_with_items(content, new_lesson_id=10, db=db)

            kwargs = MockContentItem.call_args[1]
            assert kwargs["translation"] is None
            assert kwargs["audio_url"] is None
            assert kwargs["example_sentence"] is None
            assert kwargs["example_sentence_translation"] is None
            assert kwargs["example_sentence_definition"] is None
            assert kwargs["word_count"] is None
            assert kwargs["max_errors"] is None
            assert kwargs["image_url"] is None
            assert kwargs["part_of_speech"] is None
            assert kwargs["distractors"] is None
            assert kwargs["item_metadata"] == {}

    def test_content_fields_are_copied(self):
        """Content 層級的欄位都被正確複製"""
        content = _make_mock_content(
            [],
            title="My Vocab",
            type=ContentType.VOCABULARY_SET,
            level="B1",
            tags=["animals"],
            is_public=True,
            target_wpm=120,
            target_accuracy=0.85,
            time_limit_seconds=60,
            order_index=3,
            is_active=True,
        )
        db = self._setup_db()

        with patch("services.program_service.Content") as MockContent, patch(
            "services.program_service.ContentItem"
        ):
            mock_new_content = Mock()
            mock_new_content.id = 99
            MockContent.return_value = mock_new_content

            _copy_content_with_items(content, new_lesson_id=10, db=db)

            kwargs = MockContent.call_args[1]
            assert kwargs["lesson_id"] == 10
            assert kwargs["title"] == "My Vocab"
            assert kwargs["type"] == ContentType.VOCABULARY_SET
            assert kwargs["level"] == "B1"
            assert kwargs["tags"] == ["animals"]
            assert kwargs["is_public"] is True
            assert kwargs["target_wpm"] == 120
            assert kwargs["target_accuracy"] == 0.85
            assert kwargs["time_limit_seconds"] == 60
            assert kwargs["order_index"] == 3
            assert kwargs["is_active"] is True

    def test_distractors_are_deep_copied(self):
        """distractors JSON 欄位是深拷貝，修改副本不影響原始"""
        original_distractors = ["banana", "orange", "grape"]
        item = _make_mock_item(distractors=original_distractors)
        content = _make_mock_content([item])
        db = self._setup_db()

        with patch("services.program_service.Content") as MockContent, patch(
            "services.program_service.ContentItem"
        ) as MockContentItem:
            mock_new_content = Mock()
            mock_new_content.id = 99
            MockContent.return_value = mock_new_content

            _copy_content_with_items(content, new_lesson_id=10, db=db)

            kwargs = MockContentItem.call_args[1]
            copied_distractors = kwargs["distractors"]
            assert copied_distractors == original_distractors
            # 確保是不同的物件（深拷貝）
            assert copied_distractors is not original_distractors
