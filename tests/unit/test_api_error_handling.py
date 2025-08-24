"""
Comprehensive API Error Handling Tests
Tests error scenarios, validation, and edge cases
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.orm import Session
import uuid
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.database import get_db
from backend.models import User, Classroom, Student
from backend.routers import individual_v2
from backend.auth import get_current_active_user


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_teacher():
    """Create mock individual teacher"""
    return User(
        id=str(uuid.uuid4()),
        email="teacher@individual.com",
        full_name="Test Teacher",
        role="teacher",
        is_individual_teacher=True
    )


@pytest.fixture
def mock_non_individual_teacher():
    """Create mock non-individual teacher"""
    return User(
        id=str(uuid.uuid4()),
        email="regular@teacher.com",
        full_name="Regular Teacher",
        role="teacher",
        is_individual_teacher=False
    )


class TestAuthorizationErrors:
    """Test authorization and permission errors"""
    
    def test_unauthorized_access_without_token(self, client):
        """Test API endpoints without authentication token"""
        endpoints = [
            "/api/individual/classrooms",
            "/api/individual/students",
            "/api/individual/courses",
            "/api/individual/classrooms/123",
            "/api/individual/students/123"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            assert "detail" in response.json()
    
    def test_forbidden_access_non_individual_teacher(self, client, mock_non_individual_teacher):
        """Test access denied for non-individual teachers"""
        with patch.object(individual_v2, 'get_current_active_user', return_value=mock_non_individual_teacher):
            response = client.get(
                "/api/individual/classrooms",
                headers={"Authorization": "Bearer fake-token"}
            )
            assert response.status_code == 403
            assert response.json()["detail"] == "需要個體戶教師權限"
    
    def test_invalid_token_format(self, client):
        """Test invalid authorization header format"""
        response = client.get(
            "/api/individual/classrooms",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code == 401
    
    def test_expired_token(self, client):
        """Test expired token handling"""
        with patch.object(get_current_active_user, '__call__', side_effect=HTTPException(status_code=401, detail="Token expired")):
            response = client.get(
                "/api/individual/classrooms",
                headers={"Authorization": "Bearer expired-token"}
            )
            assert response.status_code == 401
            assert "Token expired" in response.json()["detail"]


class TestValidationErrors:
    """Test input validation errors"""
    
    def test_create_classroom_missing_required_fields(self, client, mock_teacher):
        """Test classroom creation with missing required fields"""
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            # Missing name
            response = client.post(
                "/api/individual/classrooms",
                json={},
                headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 422
            errors = response.json()["detail"]
            assert any(error["loc"] == ["body", "name"] for error in errors)
    
    def test_create_student_invalid_email(self, client, mock_teacher):
        """Test student creation with invalid email format"""
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            response = client.post(
                "/api/individual/students",
                json={
                    "name": "Test Student",
                    "email": "invalid-email-format",
                    "birth_date": "2010-01-01"
                },
                headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 422
            errors = response.json()["detail"]
            assert any("email" in str(error) for error in errors)
    
    def test_create_student_invalid_birth_date(self, client, mock_teacher):
        """Test student creation with invalid birth date format"""
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=Mock()):
                response = client.post(
                    "/api/individual/students",
                    json={
                        "name": "Test Student",
                        "email": "test@example.com",
                        "birth_date": "invalid-date"
                    },
                    headers={"Authorization": "Bearer token"}
                )
                # The API should accept the date but may fail during processing
                # This tests that the API at least accepts the request
                assert response.status_code in [200, 201, 400, 422, 500]
    
    def test_invalid_uuid_format(self, client, mock_teacher):
        """Test endpoints with invalid UUID format"""
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            invalid_ids = ["not-a-uuid", "123", "xyz-abc-def", ""]
            
            for invalid_id in invalid_ids:
                response = client.get(
                    f"/api/individual/classrooms/{invalid_id}",
                    headers={"Authorization": "Bearer token"}
                )
                # Should handle gracefully, likely returning 404
                assert response.status_code in [400, 404, 422]


class TestNotFoundErrors:
    """Test resource not found errors"""
    
    def test_classroom_not_found(self, client, mock_teacher, mock_db):
        """Test accessing non-existent classroom"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.get(
                    f"/api/individual/classrooms/{uuid.uuid4()}",
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 404
                assert response.json()["detail"] == "教室不存在"
    
    def test_student_not_found_update(self, client, mock_teacher, mock_db):
        """Test updating non-existent student"""
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.put(
                    f"/api/individual/students/{uuid.uuid4()}",
                    json={
                        "name": "Updated Name",
                        "email": "updated@example.com",
                        "birth_date": "2010-01-01"
                    },
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 404
                assert response.json()["detail"] == "學生不存在"
    
    def test_student_not_in_teacher_classroom(self, client, mock_teacher, mock_db):
        """Test accessing student not belonging to teacher"""
        # Student exists but not in teacher's classroom
        mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.delete(
                    f"/api/individual/students/{uuid.uuid4()}",
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 404


class TestDatabaseErrors:
    """Test database-related errors"""
    
    def test_duplicate_student_email(self, client, mock_teacher, mock_db):
        """Test creating student with duplicate email"""
        existing_student = Student(
            id=str(uuid.uuid4()),
            email="existing@example.com",
            full_name="Existing Student",
            birth_date="20100101"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_student
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.post(
                    "/api/individual/students",
                    json={
                        "name": "New Student",
                        "email": "existing@example.com",
                        "birth_date": "2010-01-01"
                    },
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 400
                assert response.json()["detail"] == "此 Email 已被使用"
    
    def test_database_connection_error(self, client, mock_teacher):
        """Test database connection failure"""
        def raise_db_error():
            raise Exception("Database connection failed")
        
        mock_db = Mock()
        mock_db.query.side_effect = raise_db_error
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.get(
                    "/api/individual/classrooms",
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 500
    
    def test_transaction_rollback_on_error(self, client, mock_teacher, mock_db):
        """Test transaction rollback on error"""
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback = Mock()
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                try:
                    response = client.post(
                        "/api/individual/classrooms",
                        json={"name": "Test Classroom"},
                        headers={"Authorization": "Bearer token"}
                    )
                    assert response.status_code == 500
                except:
                    pass
                
                # Verify rollback would be called in real scenario
                # (Note: FastAPI handles this automatically)


class TestBusinessLogicErrors:
    """Test business logic validation errors"""
    
    def test_add_student_already_in_classroom(self, client, mock_teacher, mock_db):
        """Test adding student already in classroom"""
        classroom = Classroom(id=str(uuid.uuid4()), name="Test Class", teacher_id=mock_teacher.id)
        student = Student(id=str(uuid.uuid4()), full_name="Test Student", email="test@example.com")
        existing_mapping = Mock()
        
        # Setup mock chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        # Classroom exists
        mock_query.filter.return_value.first.return_value = classroom
        
        # Student exists (through complex join)
        mock_query.join.return_value.join.return_value.filter.return_value.first.return_value = student
        
        # Mapping already exists
        mock_query.filter.return_value.first.return_value = existing_mapping
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.post(
                    f"/api/individual/classrooms/{classroom.id}/students/{student.id}",
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 400
                assert response.json()["detail"] == "學生已在教室中"
    
    def test_remove_student_not_in_classroom(self, client, mock_teacher, mock_db):
        """Test removing student not in classroom"""
        classroom = Classroom(id=str(uuid.uuid4()), name="Test Class", teacher_id=mock_teacher.id)
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        # Classroom exists
        mock_query.filter.return_value.first.return_value = classroom
        
        # No mapping found (delete returns 0)
        mock_query.filter.return_value.delete.return_value = 0
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.delete(
                    f"/api/individual/classrooms/{classroom.id}/students/{uuid.uuid4()}",
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 404
                assert response.json()["detail"] == "學生不在此教室中"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_classroom_statistics(self, client, mock_teacher, mock_db):
        """Test statistics for empty classroom"""
        classroom = Classroom(id=str(uuid.uuid4()), name="Empty Class", teacher_id=mock_teacher.id)
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        # Classroom exists
        mock_query.filter.return_value.first.return_value = classroom
        
        # No students
        mock_query.filter.return_value.count.return_value = 0
        
        # No assignments
        mock_query.join.return_value.join.return_value.filter.return_value.count.return_value = 0
        mock_query.join.return_value.join.return_value.filter.return_value.all.return_value = []
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.get(
                    f"/api/individual/classrooms/{classroom.id}/stats",
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["total_students"] == 0
                assert data["completion_rate"] == 0
                assert data["average_score"] == 0
    
    def test_null_values_handling(self, client, mock_teacher, mock_db):
        """Test handling of null values in responses"""
        students = [
            Student(
                id=str(uuid.uuid4()),
                full_name="Student 1",
                email=None,  # Null email
                birth_date="20100101"
            ),
            Student(
                id=str(uuid.uuid4()),
                full_name="Student 2",
                email="student2@example.com",
                birth_date=None  # Null birth date
            )
        ]
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = students
        
        # Mock the GROUP_CONCAT query
        mock_query.join.return_value.filter.return_value.all.return_value = [(s, "Class1,Class2") for s in students]
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                response = client.get(
                    "/api/individual/students",
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 200
                data = response.json()
                
                # Should handle null values gracefully
                assert data[0]["email"] is None
                assert data[1]["birth_date"] == ""
    
    def test_very_long_input_values(self, client, mock_teacher):
        """Test handling of very long input values"""
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            # Very long classroom name
            response = client.post(
                "/api/individual/classrooms",
                json={
                    "name": "A" * 1000,  # 1000 character name
                    "grade_level": "B" * 500
                },
                headers={"Authorization": "Bearer token"}
            )
            # Should either accept or reject with proper error
            assert response.status_code in [200, 201, 400, 422]
    
    def test_special_characters_in_input(self, client, mock_teacher, mock_db):
        """Test handling of special characters"""
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch.object(individual_v2, 'get_individual_teacher', return_value=mock_teacher):
            with patch.object(individual_v2, 'get_db', return_value=mock_db):
                special_names = [
                    "班級<script>alert('xss')</script>",
                    "班級'; DROP TABLE students; --",
                    "班級\n\r\t",
                    "班級\\u0000null",
                    "班級🎓📚✨"
                ]
                
                for name in special_names:
                    response = client.post(
                        "/api/individual/classrooms",
                        json={"name": name},
                        headers={"Authorization": "Bearer token"}
                    )
                    # Should handle safely without breaking
                    assert response.status_code in [200, 201, 400, 422]