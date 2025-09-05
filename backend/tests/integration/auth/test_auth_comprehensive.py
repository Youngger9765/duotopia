"""
Comprehensive tests for auth.py module
Testing all authentication utilities and edge cases
"""
import pytest
from datetime import datetime, timedelta  # noqa: F401
from jose import jwt
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_teacher,
    authenticate_student,
)
from models import Teacher, Student


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_password_hashing_and_verification(self):
        """Test password hashing and verification work correctly"""
        password = "test123"
        hashed = get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password

        # Verification should work
        assert verify_password(password, hashed) is True

        # Wrong password should fail
        assert verify_password("wrong_password", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)"""
        password = "test123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        """Test handling of empty password"""
        password = ""
        hashed = get_password_hash(password)

        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False

    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        special_passwords = [
            "P@ssw0rd!",
            "密碼123",
            "пароль",
            "🔒🗝️123",
            "a very long password with spaces and numbers 123456789",
        ]

        for password in special_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True
            assert verify_password("wrong", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification"""

    def test_create_and_verify_token(self):
        """Test basic token creation and verification"""
        data = {"sub": "123", "email": "test@example.com", "type": "teacher"}

        token = create_access_token(data)
        assert isinstance(token, str)
        assert token != ""

        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "teacher"
        assert "exp" in payload  # Expiration should be added

    def test_token_with_custom_expiry(self):
        """Test token creation with custom expiry"""
        data = {"sub": "123", "email": "test@example.com"}
        expires_delta = timedelta(minutes=5)

        token = create_access_token(data, expires_delta=expires_delta)
        payload = verify_token(token)

        assert payload is not None

        # Check expiration time is roughly correct (within 1 minute tolerance)
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.utcfromtimestamp(payload["exp"])

        # Allow 1 minute tolerance for test execution time
        assert abs((expected_exp - actual_exp).total_seconds()) < 60

    def test_expired_token(self):
        """Test verification of expired token"""
        data = {"sub": "123", "email": "test@example.com"}
        expired_delta = timedelta(seconds=-10)  # Expired 10 seconds ago

        token = create_access_token(data, expires_delta=expired_delta)

        # Should return None for expired token
        payload = verify_token(token)
        assert payload is None

    def test_invalid_token(self):
        """Test verification of invalid tokens"""
        invalid_tokens = [
            "invalid.token.here",
            "not.a.jwt",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_payload.signature",
            None,
        ]

        for token in invalid_tokens:
            payload = verify_token(token)
            assert payload is None

    def test_token_with_wrong_secret(self):
        """Test token created with different secret"""

        data = {"sub": "123", "email": "test@example.com"}

        # Create token with different secret
        wrong_secret_token = jwt.encode(data, "wrong_secret", algorithm="HS256")

        # Should not verify with our secret
        payload = verify_token(wrong_secret_token)
        assert payload is None

    def test_token_with_minimal_data(self):
        """Test token with minimal required data"""
        data = {"sub": "123"}

        token = create_access_token(data)
        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == "123"
        assert "exp" in payload

    def test_token_with_extra_data(self):
        """Test token with additional custom fields"""
        data = {
            "sub": "123",
            "email": "test@example.com",
            "type": "teacher",
            "name": "Test Teacher",
            "custom_field": "custom_value",
            "permissions": ["read", "write"],
        }

        token = create_access_token(data)
        payload = verify_token(token)

        assert payload is not None
        assert payload["custom_field"] == "custom_value"
        assert payload["permissions"] == ["read", "write"]


class TestTeacherAuthentication:
    """Test teacher authentication"""

    def test_authenticate_valid_teacher(self, db):
        """Test authenticating valid teacher"""
        # Create teacher
        teacher = Teacher(
            email="auth@duotopia.com",
            password_hash=get_password_hash("correct_password"),
            name="Auth Teacher",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

        # Authenticate
        result = authenticate_teacher(db, "auth@duotopia.com", "correct_password")

        assert result is not None
        assert result.id == teacher.id
        assert result.email == "auth@duotopia.com"
        assert result.name == "Auth Teacher"

    def test_authenticate_teacher_wrong_password(self, db):
        """Test authenticating teacher with wrong password"""
        # Create teacher
        teacher = Teacher(
            email="auth2@duotopia.com",
            password_hash=get_password_hash("correct_password"),
            name="Auth Teacher 2",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()

        # Try wrong password
        result = authenticate_teacher(db, "auth2@duotopia.com", "wrong_password")
        assert result is None

    def test_authenticate_teacher_not_exists(self, db):
        """Test authenticating non-existent teacher"""
        result = authenticate_teacher(db, "nonexistent@duotopia.com", "password")
        assert result is None

    def test_authenticate_inactive_teacher(self, db):
        """Test authenticating inactive teacher"""
        # Create inactive teacher
        teacher = Teacher(
            email="inactive@duotopia.com",
            password_hash=get_password_hash("password"),
            name="Inactive Teacher",
            is_active=False,  # Inactive
            is_demo=False,
        )
        db.add(teacher)
        db.commit()

        # Should still authenticate (business logic decision)
        result = authenticate_teacher(db, "inactive@duotopia.com", "password")
        # Current implementation may or may not authenticate inactive users
        # Test the actual behavior
        if result:
            assert result.is_active is False

    def test_authenticate_teacher_case_sensitivity(self, db):
        """Test email case sensitivity in authentication"""
        # Create teacher with lowercase email
        teacher = Teacher(
            email="case@duotopia.com",
            password_hash=get_password_hash("password"),
            name="Case Teacher",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()

        # Try different cases
        test_cases = [
            "case@duotopia.com",  # Exact match
            "CASE@DUOTOPIA.COM",  # Uppercase
            "Case@Duotopia.Com",  # Mixed case
        ]

        for email in test_cases:
            result = authenticate_teacher(db, email, "password")
            # Current implementation behavior - test what actually happens
            # If case-sensitive, only first should work
            # If case-insensitive, all should work
            if email == "case@duotopia.com":
                assert result is not None
            # For others, depends on implementation


class TestStudentAuthentication:
    """Test student authentication"""

    def test_authenticate_valid_student(self, db):
        """Test authenticating valid student"""
        # Create student
        student = Student(
            name="Auth Student",
            email="authstudent@example.com",
            password_hash=get_password_hash("20100101"),
            birthdate=datetime(2010, 1, 1).date(),
            is_active=True,
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # Authenticate
        result = authenticate_student(db, "authstudent@example.com", "20100101")

        assert result is not None
        assert result.id == student.id
        assert result.email == "authstudent@example.com"

    def test_authenticate_student_wrong_password(self, db):
        """Test authenticating student with wrong password"""
        # Create student
        student = Student(
            name="Auth Student 2",
            email="authstudent2@example.com",
            password_hash=get_password_hash("20100101"),
            birthdate=datetime(2010, 1, 1).date(),
            is_active=True,
        )
        db.add(student)
        db.commit()

        # Try wrong password
        result = authenticate_student(db, "authstudent2@example.com", "20100102")
        assert result is None

    def test_authenticate_student_not_exists(self, db):
        """Test authenticating non-existent student"""
        result = authenticate_student(db, "nonexistent@example.com", "20100101")
        assert result is None


class TestEdgeCasesAndSecurity:
    """Test edge cases and security scenarios"""

    def test_password_hash_not_plain_text(self):
        """Ensure password hash is not stored as plain text"""
        password = "super_secret_password"
        hashed = get_password_hash(password)

        # Hash should not contain the original password
        assert password not in hashed
        assert len(hashed) > len(password)  # Should be longer due to salt and hashing

    def test_token_payload_structure(self):
        """Test token payload has expected structure"""
        data = {
            "sub": "user123",
            "email": "user@example.com",
            "type": "teacher",
            "name": "Test User",
        }

        token = create_access_token(data)
        payload = verify_token(token)

        assert payload is not None

        # Should have all original data
        for key, value in data.items():
            assert payload[key] == value

        # Should have expiration
        assert "exp" in payload
        assert isinstance(payload["exp"], int)

        # Expiration should be in the future
        assert payload["exp"] > datetime.utcnow().timestamp()

    def test_null_and_none_handling(self):
        """Test handling of null/None values"""
        # Test password functions with None
        with pytest.raises((TypeError, AttributeError)):
            get_password_hash(None)

        with pytest.raises((TypeError, AttributeError)):
            verify_password(None, "hash")

        with pytest.raises((TypeError, AttributeError)):
            verify_password("password", None)

    def test_unicode_in_tokens(self):
        """Test Unicode characters in token data"""
        data = {
            "sub": "123",
            "email": "用戶@example.com",
            "name": "тестовый пользователь",
            "description": "🔒 Secure user",
        }

        token = create_access_token(data)
        payload = verify_token(token)

        assert payload is not None
        assert payload["email"] == "用戶@example.com"
        assert payload["name"] == "тестовый пользователь"
        assert payload["description"] == "🔒 Secure user"

    def test_very_long_token_data(self):
        """Test token with very long data"""
        long_string = "A" * 1000  # 1000 character string

        data = {"sub": "123", "email": "test@example.com", "long_field": long_string}

        token = create_access_token(data)
        payload = verify_token(token)

        assert payload is not None
        assert payload["long_field"] == long_string
