"""
完整的 auth.py 單元測試，提升覆蓋率
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest  # noqa: E402
from unittest.mock import Mock, patch, MagicMock  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402
from jose import jwt, JWTError  # noqa: E402
from fastapi import HTTPException  # noqa: E402
import asyncio  # noqa: E402
from auth import (  # noqa: E402
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_teacher,
    authenticate_student,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
)


class TestPasswordFunctions:
    """密碼相關函數測試"""

    def test_get_password_hash_creates_different_hashes(self):
        """測試密碼雜湊產生不同結果"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # 每次產生的 hash 應該不同
        assert hash1.startswith("$2b$")  # bcrypt hash 格式
        assert len(hash1) > 50

    def test_verify_password_with_correct_password(self):
        """測試驗證正確密碼"""
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_wrong_password(self):
        """測試驗證錯誤密碼"""
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_with_empty_string(self):
        """測試空字串密碼"""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False


class TestTokenFunctions:
    """Token 相關函數測試"""

    def test_create_access_token_without_expiry(self):
        """測試建立沒有指定過期時間的 token"""
        data = {"sub": "user123", "type": "teacher"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # 解碼 token 檢查內容
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "teacher"
        assert "exp" in decoded

    def test_create_access_token_with_custom_expiry(self):
        """測試建立有自訂過期時間的 token"""
        data = {"sub": "user456", "type": "student"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "user456"
        assert decoded["type"] == "student"

        # 檢查過期時間大約是 60 分鐘後
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        diff = exp_time - now
        assert 59 <= diff.total_seconds() / 60 <= 61

    def test_verify_token_with_valid_token(self):
        """測試驗證有效的 token"""
        data = {"sub": "user789", "type": "teacher"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user789"
        assert payload["type"] == "teacher"

    def test_verify_token_with_none(self):
        """測試驗證 None token"""
        payload = verify_token(None)
        assert payload is None

    def test_verify_token_with_invalid_token(self):
        """測試驗證無效的 token"""
        invalid_token = "this.is.not.a.valid.token"
        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_token_with_expired_token(self):
        """測試驗證過期的 token"""
        data = {"sub": "user", "type": "teacher"}
        # 建立一個已經過期的 token
        expired_token = create_access_token(data, timedelta(seconds=-1))

        payload = verify_token(expired_token)
        assert payload is None

    def test_verify_token_with_wrong_secret(self):
        """測試用錯誤密鑰驗證 token"""
        data = {"sub": "user", "type": "teacher"}
        # 用不同的密鑰建立 token
        wrong_secret_token = jwt.encode(data, "wrong_secret", algorithm=ALGORITHM)

        payload = verify_token(wrong_secret_token)
        assert payload is None


class TestAuthentication:
    """認證相關函數測試"""

    def test_authenticate_teacher_success(self):
        """測試成功認證教師"""
        mock_db = Mock()
        mock_teacher = Mock()
        mock_teacher.password_hash = get_password_hash("correct_password")
        mock_teacher.email = "teacher@test.com"

        mock_db.query().filter().first.return_value = mock_teacher

        result = authenticate_teacher(mock_db, "teacher@test.com", "correct_password")
        assert result == mock_teacher

    def test_authenticate_teacher_user_not_found(self):
        """測試教師不存在"""
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None

        result = authenticate_teacher(mock_db, "notfound@test.com", "password")
        assert result is None

    def test_authenticate_teacher_wrong_password(self):
        """測試教師密碼錯誤"""
        mock_db = Mock()
        mock_teacher = Mock()
        mock_teacher.password_hash = get_password_hash("correct_password")

        mock_db.query().filter().first.return_value = mock_teacher

        result = authenticate_teacher(mock_db, "teacher@test.com", "wrong_password")
        assert result is None

    def test_authenticate_student_success(self):
        """測試成功認證學生"""
        mock_db = Mock()
        mock_student = Mock()
        mock_student.password_hash = get_password_hash("student_pass")
        mock_student.email = "student@test.com"

        mock_db.query().filter().first.return_value = mock_student

        result = authenticate_student(mock_db, "student@test.com", "student_pass")
        assert result == mock_student

    def test_authenticate_student_not_found(self):
        """測試學生不存在"""
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None

        result = authenticate_student(mock_db, "notfound@test.com", "password")
        assert result is None

    def test_authenticate_student_wrong_password(self):
        """測試學生密碼錯誤"""
        mock_db = Mock()
        mock_student = Mock()
        mock_student.password_hash = get_password_hash("correct_password")

        mock_db.query().filter().first.return_value = mock_student

        result = authenticate_student(mock_db, "student@test.com", "wrong_password")
        assert result is None


class TestGetCurrentUser:
    """測試 get_current_user 函數"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """測試有效 token 取得使用者"""
        data = {"sub": "123", "type": "teacher", "email": "test@test.com"}
        token = create_access_token(data)

        result = await get_current_user(token)
        assert result["sub"] == "123"
        assert result["type"] == "teacher"
        assert result["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """測試無效 token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(invalid_token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self):
        """測試 token 缺少 sub 欄位"""
        data = {"type": "teacher"}  # 缺少 sub
        token = create_access_token(data)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_missing_type(self):
        """測試 token 缺少 type 欄位"""
        data = {"sub": "123"}  # 缺少 type
        token = create_access_token(data)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """測試過期的 token"""
        data = {"sub": "123", "type": "teacher"}
        expired_token = create_access_token(data, timedelta(seconds=-1))

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(expired_token)

        assert exc_info.value.status_code == 401


class TestEdgeCases:
    """邊界情況測試"""

    def test_password_with_special_chars(self):
        """測試特殊字元密碼"""
        password = "P@$$w0rd!#$%^&*()"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_with_unicode(self):
        """測試 Unicode 密碼"""
        password = "密碼測試🔒"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_very_long_password(self):
        """測試超長密碼"""
        password = "a" * 1000
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_token_with_extra_claims(self):
        """測試有額外宣告的 token"""
        data = {
            "sub": "123",
            "type": "teacher",
            "extra": "data",
            "role": "admin",
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)
        payload = verify_token(token)

        assert payload["extra"] == "data"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
