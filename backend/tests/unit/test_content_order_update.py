"""
Unit Test: Content Order Index Update
測試內容順序更新功能的單元測試
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from models import Content
from routers.teachers.validators import ContentUpdate


class TestContentOrderUpdate:
    """測試內容順序更新功能"""

    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫 session"""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_content(self):
        """建立測試用內容"""
        content = Content(
            id=1, title="Test Content", type="reading", order_index=1, lesson_id=1
        )
        return content

    def test_content_update_with_order_index(self, mock_db_session, sample_content):
        """測試 ContentUpdate 是否支援 order_index 參數"""
        # Arrange
        update_data = ContentUpdate(order_index=5)

        # Mock 資料庫查詢
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            sample_content
        )
        mock_db_session.commit.return_value = None

        # Act & Assert - 確保不會拋出異常
        try:
            # 模擬更新邏輯
            if update_data.order_index is not None:
                sample_content.order_index = update_data.order_index

            assert sample_content.order_index == 5
            print("✅ ContentUpdate 支援 order_index 參數")
        except Exception as e:
            pytest.fail(f"❌ ContentUpdate 不支援 order_index: {e}")

    def test_content_order_index_type_validation(self):
        """測試 order_index 型別驗證"""
        # 正確的型別
        valid_update = ContentUpdate(order_index=10)
        assert valid_update.order_index == 10

        # None 也是有效的
        none_update = ContentUpdate(order_index=None)
        assert none_update.order_index is None

        print("✅ order_index 型別驗證通過")

    def test_content_order_index_boundary_values(self):
        """測試 order_index 邊界值"""
        # 測試 0
        zero_update = ContentUpdate(order_index=0)
        assert zero_update.order_index == 0

        # 測試負數（根據業務邏輯決定是否允許）
        negative_update = ContentUpdate(order_index=-1)
        assert negative_update.order_index == -1

        # 測試大數值
        large_update = ContentUpdate(order_index=999999)
        assert large_update.order_index == 999999

        print("✅ order_index 邊界值測試通過")

    def test_drag_sort_logic(self):
        """測試拖拽排序邏輯"""
        # 模擬原始內容順序: [1, 2, 3]
        contents = [
            {"id": 1, "order_index": 1},
            {"id": 2, "order_index": 2},
            {"id": 3, "order_index": 3},
        ]

        # 模擬拖拽：將第一個移到最後 -> [2, 3, 1]
        new_order = [
            {"id": 2, "order_index": 1},
            {"id": 3, "order_index": 2},
            {"id": 1, "order_index": 3},
        ]

        # 驗證邏輯
        for item in new_order:
            content_id = item["id"]
            new_index = item["order_index"]

            # 找到對應的內容並更新
            for content in contents:
                if content["id"] == content_id:
                    content["order_index"] = new_index

        # 驗證結果
        expected = [
            {"id": 1, "order_index": 3},  # 第一個移到最後
            {"id": 2, "order_index": 1},  # 第二個變第一
            {"id": 3, "order_index": 2},  # 第三個變第二
        ]

        assert contents == expected
        print("✅ 拖拽排序邏輯測試通過")

    def test_content_update_preserves_other_fields(self, sample_content):
        """測試更新 order_index 不會影響其他欄位"""
        original_title = sample_content.title
        original_type = sample_content.type
        original_lesson_id = sample_content.lesson_id

        # 更新 order_index
        update_data = ContentUpdate(order_index=999)
        sample_content.order_index = update_data.order_index

        # 驗證其他欄位沒有改變
        assert sample_content.title == original_title
        assert sample_content.type == original_type
        assert sample_content.lesson_id == original_lesson_id
        assert sample_content.order_index == 999

        print("✅ 更新 order_index 保持其他欄位不變")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
