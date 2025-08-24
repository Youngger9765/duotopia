#!/usr/bin/env python3
"""
Unit Tests - Individual Teacher API Endpoints
"""
import pytest
import requests
import json
from datetime import datetime

class TestIndividualTeacherAPI:
    """Comprehensive unit tests for individual teacher API endpoints"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.base_url = "http://localhost:8000"
        cls.token = cls._get_auth_token()
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        
    @classmethod
    def _get_auth_token(cls):
        """Get authentication token for tests"""
        response = requests.post(
            f"{cls.base_url}/api/auth/login",
            data={
                "username": "teacher@individual.com",
                "password": "password123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]
    
    def test_login_authentication(self):
        """Test login endpoint"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={
                "username": "teacher@individual.com",
                "password": "password123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_type"] == "teacher"
        assert data["is_individual_teacher"] == True
        
    def test_token_validation(self):
        """Test token validation endpoint"""
        response = requests.get(
            f"{self.base_url}/api/auth/validate",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "teacher@individual.com"
        assert data["is_individual_teacher"] == True
        
    def test_get_classrooms(self):
        """Test classroom listing endpoint"""
        response = requests.get(
            f"{self.base_url}/api/individual/classrooms",
            headers=self.headers
        )
        
        assert response.status_code == 200
        classrooms = response.json()
        assert isinstance(classrooms, list)
        assert len(classrooms) > 0
        
        # Verify classroom structure
        first_classroom = classrooms[0]
        required_fields = ["id", "name", "grade_level", "student_count", "created_at"]
        for field in required_fields:
            assert field in first_classroom
            
    def test_get_students(self):
        """Test student listing endpoint"""
        response = requests.get(
            f"{self.base_url}/api/individual/students",
            headers=self.headers
        )
        
        assert response.status_code == 200
        students = response.json()
        assert isinstance(students, list)
        assert len(students) > 0
        
        # Verify student structure
        first_student = students[0]
        required_fields = ["id", "full_name", "email", "birth_date", "classroom_names"]
        for field in required_fields:
            assert field in first_student
            
    def test_get_courses(self):
        """Test course listing endpoint"""
        response = requests.get(
            f"{self.base_url}/api/individual/courses",
            headers=self.headers
        )
        
        assert response.status_code == 200
        courses = response.json()
        assert isinstance(courses, list)
        assert len(courses) > 0
        
        # Verify course structure
        first_course = courses[0]
        required_fields = ["id", "title", "description", "difficulty_level", "lesson_count"]
        for field in required_fields:
            assert field in first_course
            
    def test_create_classroom(self):
        """Test classroom creation endpoint"""
        new_classroom_data = {
            "name": f"Test Classroom {datetime.now().strftime('%H%M%S')}",
            "grade_level": "Test Grade"
        }
        
        response = requests.post(
            f"{self.base_url}/api/individual/classrooms",
            json=new_classroom_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        classroom = response.json()
        assert classroom["name"] == new_classroom_data["name"]
        assert classroom["grade_level"] == new_classroom_data["grade_level"]
        assert classroom["student_count"] == 0
        
        # Cleanup - delete test classroom
        cleanup_response = requests.delete(
            f"{self.base_url}/api/individual/classrooms/{classroom['id']}",
            headers=self.headers
        )
        assert cleanup_response.status_code == 200
        
    def test_create_course(self):
        """Test course creation endpoint"""
        new_course_data = {
            "title": f"Test Course {datetime.now().strftime('%H%M%S')}",
            "description": "Test course description",
            "difficulty_level": "A1"
        }
        
        response = requests.post(
            f"{self.base_url}/api/individual/courses",
            json=new_course_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        course = response.json()
        assert course["title"] == new_course_data["title"]
        assert course["description"] == new_course_data["description"]
        assert course["difficulty_level"] == new_course_data["difficulty_level"]
        assert course["lesson_count"] == 0
        
    def test_classroom_detail(self):
        """Test classroom detail endpoint"""
        # Get first classroom
        classrooms_response = requests.get(
            f"{self.base_url}/api/individual/classrooms",
            headers=self.headers
        )
        classrooms = classrooms_response.json()
        classroom_id = classrooms[0]["id"]
        
        # Get classroom detail
        response = requests.get(
            f"{self.base_url}/api/individual/classrooms/{classroom_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        detail = response.json()
        required_fields = ["id", "name", "students", "courses", "student_count", "course_count"]
        for field in required_fields:
            assert field in detail
            
    def test_unauthorized_access(self):
        """Test unauthorized access is properly rejected"""
        response = requests.get(
            f"{self.base_url}/api/individual/classrooms"
        )
        
        assert response.status_code == 401
        
    def test_invalid_token_access(self):
        """Test invalid token is properly rejected"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(
            f"{self.base_url}/api/individual/classrooms",
            headers=invalid_headers
        )
        
        assert response.status_code == 401

if __name__ == "__main__":
    # Run unit tests
    import subprocess
    import sys
    
    try:
        # Try to run with pytest if available
        result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], 
                              capture_output=True, text=True)
        print("=== UNIT TEST RESULTS ===")
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"Exit code: {result.returncode}")
    except FileNotFoundError:
        # Fallback to manual test execution
        print("=== MANUAL UNIT TEST EXECUTION ===")
        test_instance = TestIndividualTeacherAPI()
        test_instance.setup_class()
        
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                print(f"Running {test_method}...")
                getattr(test_instance, test_method)()
                print(f"✅ {test_method} PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ {test_method} FAILED: {str(e)}")
                failed += 1
                
        print(f"\n📊 Results: {passed} passed, {failed} failed")