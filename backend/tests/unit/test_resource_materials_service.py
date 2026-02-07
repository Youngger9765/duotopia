"""
Resource Materials Service 單元測試

測試資源教材包的核心商業邏輯：
- 每日複製上限 (DAILY_COPY_LIMIT = 10)
- check_copy_limit 判斷邏輯
- list_resource_materials 回傳的 copy 相關欄位
- update_program_visibility 權限驗證
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from unittest.mock import Mock, MagicMock, patch
from datetime import date

from services.resource_materials_service import (
    DAILY_COPY_LIMIT,
    check_copy_limit,
    update_program_visibility,
)


class TestDailyCopyLimit:
    """每日複製上限常數測試"""

    def test_daily_copy_limit_is_10(self):
        """DAILY_COPY_LIMIT 應該是 10"""
        assert DAILY_COPY_LIMIT == 10

    def test_daily_copy_limit_is_positive(self):
        """DAILY_COPY_LIMIT 應該是正整數"""
        assert isinstance(DAILY_COPY_LIMIT, int)
        assert DAILY_COPY_LIMIT > 0


class TestCheckCopyLimit:
    """check_copy_limit 函式測試"""

    def _mock_db(self, count: int):
        """建立 mock db session，回傳指定的 count"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = count
        db = Mock()
        db.query.return_value = mock_query
        return db

    def test_allows_copy_when_count_is_zero(self):
        """沒有複製記錄時允許複製"""
        db = self._mock_db(0)
        assert check_copy_limit(db, 1, "individual", "123") is True

    def test_allows_copy_when_under_limit(self):
        """未達上限時允許複製"""
        db = self._mock_db(DAILY_COPY_LIMIT - 1)
        assert check_copy_limit(db, 1, "individual", "123") is True

    def test_blocks_copy_at_limit(self):
        """達到上限時禁止複製"""
        db = self._mock_db(DAILY_COPY_LIMIT)
        assert check_copy_limit(db, 1, "individual", "123") is False

    def test_blocks_copy_over_limit(self):
        """超過上限時禁止複製"""
        db = self._mock_db(DAILY_COPY_LIMIT + 5)
        assert check_copy_limit(db, 1, "individual", "123") is False

    def test_works_for_organization_type(self):
        """組織類型也正確檢查"""
        db = self._mock_db(3)
        assert check_copy_limit(db, 1, "organization", "org-uuid") is True


class TestUpdateProgramVisibility:
    """update_program_visibility 權限測試"""

    @patch("services.resource_materials_service.get_resource_account")
    def test_rejects_non_resource_account(self, mock_get_account):
        """非 resource account 無法更新 visibility"""
        mock_account = Mock()
        mock_account.id = 999
        mock_get_account.return_value = mock_account

        db = Mock()
        try:
            update_program_visibility(db, 1, teacher_id=123, visibility="public")
            assert False, "Should have raised PermissionError"
        except PermissionError as e:
            assert "resource account" in str(e).lower()

    @patch("services.resource_materials_service.get_resource_account")
    def test_rejects_invalid_visibility(self, mock_get_account):
        """無效的 visibility 值被拒絕"""
        mock_account = Mock()
        mock_account.id = 1
        mock_get_account.return_value = mock_account

        db = Mock()
        try:
            update_program_visibility(db, 1, teacher_id=1, visibility="invalid_value")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "invalid" in str(e).lower()

    @patch("services.resource_materials_service.get_resource_account")
    def test_accepts_valid_visibility_values(self, mock_get_account):
        """所有有效的 visibility 值都被接受"""
        valid_values = ["private", "public", "organization_only", "individual_only"]
        mock_account = Mock()
        mock_account.id = 1
        mock_get_account.return_value = mock_account

        for value in valid_values:
            mock_program = Mock()
            mock_program.visibility = "private"

            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_program

            db = Mock()
            db.query.return_value = mock_query

            result = update_program_visibility(db, 1, teacher_id=1, visibility=value)
            assert result["visibility"] == value
            assert mock_program.visibility == value

    @patch("services.resource_materials_service.get_resource_account")
    def test_rejects_when_no_resource_account(self, mock_get_account):
        """resource account 不存在時拒絕"""
        mock_get_account.return_value = None
        db = Mock()
        try:
            update_program_visibility(db, 1, teacher_id=1, visibility="public")
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass
