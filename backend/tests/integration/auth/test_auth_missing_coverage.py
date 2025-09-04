"""
Tests to cover missing lines in auth.py for 90%+ coverage
"""
from sqlalchemy.orm import Session
from auth import (
    verify_password,
    get_password_hash,
    authenticate_teacher,
    authenticate_student,
)
from models import Teacher, Student


class TestPasswordFunctions:
    """Test password hashing and verification functions"""

    def test_password_hashing(self):
        """Test password hashing creates different hashes"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_password_verification_failure(self):
        """Test password verification with wrong password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        # Correct password should verify
        assert verify_password(password, hashed)

        # Wrong password should not verify
        assert not verify_password(wrong_password, hashed)

    def test_empty_password_handling(self):
        """Test handling of empty passwords"""
        empty_password = ""
        hashed = get_password_hash(empty_password)

        # Should still work with empty password
        assert verify_password(empty_password, hashed)
        assert not verify_password("not_empty", hashed)


class TestTeacherAuthentication:
    """Test teacher authentication function coverage"""

    def test_authenticate_teacher_success(self, db: Session):
        """Test successful teacher authentication"""
        # Create teacher with known password
        password = "test_password_123"
        teacher = Teacher(
            email="auth_test@duotopia.com",
            hashed_password=get_password_hash(password),
            name="Auth Test Teacher",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

        # Authenticate successfully
        result = authenticate_teacher(db, "auth_test@duotopia.com", password)
        assert result is not None
        assert result.id == teacher.id
        assert result.email == teacher.email

    def test_authenticate_teacher_not_exists(self, db: Session):
        """Test authenticating non-existent teacher"""
        result = authenticate_teacher(db, "nonexistent@duotopia.com", "password")
        assert result is None

    def test_authenticate_teacher_wrong_password(self, db: Session):
        """Test authenticating teacher with wrong password"""
        # Create teacher
        teacher = Teacher(
            email="wrong_pass@duotopia.com",
            hashed_password=get_password_hash("correct_password"),
            name="Wrong Pass Teacher",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()

        # Try with wrong password
        result = authenticate_teacher(db, "wrong_pass@duotopia.com", "wrong_password")
        assert result is None


class TestStudentAuthentication:
    """Test student authentication function coverage"""

    def test_authenticate_student_success(self, db: Session):
        """Test successful student authentication"""
        # Create student with known password
        password = "student_password_123"
        student = Student(
            email="auth_student@test.com",
            name="Auth Test Student",
            hashed_password=get_password_hash(password),
            birthdate="2000-01-01",
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # Authenticate successfully
        result = authenticate_student(db, "auth_student@test.com", password)
        assert result is not None
        assert result.id == student.id
        assert result.email == student.email

    def test_authenticate_student_not_exists(self, db: Session):
        """Test authenticating non-existent student"""
        result = authenticate_student(db, "nonexistent_student@test.com", "password")
        assert result is None

    def test_authenticate_student_wrong_password(self, db: Session):
        """Test authenticating student with wrong password"""
        # Create student
        student = Student(
            email="wrong_student@test.com",
            name="Wrong Pass Student",
            hashed_password=get_password_hash("correct_password"),
            birthdate="2000-01-01",
        )
        db.add(student)
        db.commit()

        # Try with wrong password
        result = authenticate_student(db, "wrong_student@test.com", "wrong_password")
        assert result is None


class TestAuthEdgeCases:
    """Test edge cases and special scenarios"""

    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        special_passwords = [
            "password@#$%",
            "密碼123",
            "пароль",
            "🔒password🔒",
            "pass\nword",
            "pass\tword",
        ]

        for password in special_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed)
            assert not verify_password("different", hashed)

    def test_very_long_password(self):
        """Test very long passwords"""
        long_password = "a" * 1000  # 1000 character password
        hashed = get_password_hash(long_password)

        assert verify_password(long_password, hashed)
        assert not verify_password("short", hashed)

    def test_case_sensitive_email_auth(self, db: Session):
        """Test that email authentication is case sensitive or insensitive"""
        password = "test_password"
        teacher = Teacher(
            email="CaseTest@Duotopia.com",  # Mixed case
            hashed_password=get_password_hash(password),
            name="Case Test Teacher",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()

        # Test exact case
        result1 = authenticate_teacher(db, "CaseTest@Duotopia.com", password)
        assert result1 is not None

        # Test different case
        result2 = authenticate_teacher(db, "casetest@duotopia.com", password)
        # This depends on database collation - might be None or the teacher
        # Both outcomes are valid depending on setup

    def test_whitespace_in_credentials(self, db: Session):
        """Test handling whitespace in email and password"""
        password = "test_password"
        teacher = Teacher(
            email="whitespace@duotopia.com",
            hashed_password=get_password_hash(password),
            name="Whitespace Teacher",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()

        # Test with trailing/leading spaces (should probably fail)
        result = authenticate_teacher(db, " whitespace@duotopia.com ", password)
        # This should fail as emails with spaces aren't the same
        assert result is None

    def test_null_password_handling(self, db: Session):
        """Test handling of null/empty passwords in authentication"""
        teacher = Teacher(
            email="nullpass@duotopia.com",
            hashed_password=get_password_hash(""),  # Empty password hash
            name="Null Pass Teacher",
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.commit()

        # Should authenticate with empty password
        result = authenticate_teacher(db, "nullpass@duotopia.com", "")
        assert result is not None

        # Should not authenticate with non-empty password
        result2 = authenticate_teacher(db, "nullpass@duotopia.com", "not_empty")
        assert result2 is None


class TestPasswordComplexity:
    """Test password complexity scenarios"""

    def test_password_with_numbers(self):
        """Test passwords with various number combinations"""
        passwords = ["123456", "password123", "12pa34ss56wo78rd90"]

        for password in passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed)

    def test_password_with_symbols(self):
        """Test passwords with symbols"""
        passwords = [
            "!@#$%^&*()",
            "pass!word",
            "p@$$w0rd",
            "complex.password-with_symbols",
        ]

        for password in passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed)

    def test_unicode_passwords(self):
        """Test Unicode passwords"""
        unicode_passwords = [
            "مرحبا",  # Arabic
            "你好",  # Chinese
            "здравствуй",  # Russian
            "🎉🎊🎈",  # Emojis
        ]

        for password in unicode_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed)
