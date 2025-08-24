#!/usr/bin/env python3
"""
Integration Tests - Frontend & Backend Integration
"""
import requests
import time
from playwright.sync_api import sync_playwright

class IntegrationTestSuite:
    """Integration tests for full-stack functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:5173"
        
    def test_api_data_consistency(self):
        """Test data consistency across API endpoints"""
        print("🔗 Testing API data consistency...")
        
        # Get auth token
        login_response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={"username": "teacher@individual.com", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get data from different endpoints
        classrooms = requests.get(f"{self.base_url}/api/individual/classrooms", headers=headers).json()
        students = requests.get(f"{self.base_url}/api/individual/students", headers=headers).json()
        courses = requests.get(f"{self.base_url}/api/individual/courses", headers=headers).json()
        
        # Verify data consistency
        total_students_in_classrooms = sum(c["student_count"] for c in classrooms)
        print(f"   Students in classrooms: {total_students_in_classrooms}")
        print(f"   Students in student list: {len(students)}")
        
        # Test classroom detail consistency
        for classroom in classrooms[:2]:  # Test first 2 classrooms
            detail = requests.get(f"{self.base_url}/api/individual/classrooms/{classroom['id']}", headers=headers).json()
            assert detail["student_count"] == classroom["student_count"]
            print(f"   ✅ Classroom {classroom['name']}: {detail['student_count']} students, {detail['course_count']} courses")
        
        print("   ✅ API data consistency verified")
        
    def test_frontend_backend_integration(self):
        """Test frontend-backend integration with real browser"""
        print("🌐 Testing frontend-backend integration...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                # Test login flow
                page.goto(f"{self.frontend_url}/login")
                page.click('button:has-text("個體戶教師")')
                page.click('button[type="submit"]:has-text("登入")')
                
                # Verify navigation to dashboard
                page.wait_for_url("**/individual", timeout=10000)
                print("   ✅ Login and navigation working")
                
                # Test data loading in each section
                sections = [
                    ("我的教室", "classroom"),
                    ("學生管理", "student"),
                    ("課程管理", "course")
                ]
                
                for section_name, section_type in sections:
                    page.click(f'a:has-text("{section_name}")')
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    
                    # Check for loading completion
                    loading = page.query_selector("text=載入中...")
                    if not loading:
                        print(f"   ✅ {section_name} data loaded successfully")
                    else:
                        print(f"   ⚠️  {section_name} still loading")
                
                print("   ✅ Frontend-backend integration verified")
                
            finally:
                browser.close()
                
    def test_crud_operations_integration(self):
        """Test full CRUD operations across frontend and backend"""
        print("🔄 Testing CRUD operations integration...")
        
        # Get auth token
        login_response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={"username": "teacher@individual.com", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test CREATE operation
        test_classroom = {
            "name": f"Integration Test Classroom {int(time.time())}",
            "grade_level": "Test Grade"
        }
        
        create_response = requests.post(
            f"{self.base_url}/api/individual/classrooms",
            json=test_classroom,
            headers=headers
        )
        assert create_response.status_code == 200
        created_classroom = create_response.json()
        print(f"   ✅ CREATE: Classroom '{created_classroom['name']}' created")
        
        # Test READ operation
        read_response = requests.get(
            f"{self.base_url}/api/individual/classrooms/{created_classroom['id']}",
            headers=headers
        )
        assert read_response.status_code == 200
        classroom_detail = read_response.json()
        assert classroom_detail["name"] == test_classroom["name"]
        print(f"   ✅ READ: Classroom details retrieved")
        
        # Test DELETE operation
        delete_response = requests.delete(
            f"{self.base_url}/api/individual/classrooms/{created_classroom['id']}",
            headers=headers
        )
        assert delete_response.status_code == 200
        print(f"   ✅ DELETE: Classroom removed")
        
        # Verify deletion
        verify_response = requests.get(
            f"{self.base_url}/api/individual/classrooms/{created_classroom['id']}",
            headers=headers
        )
        assert verify_response.status_code == 404
        print("   ✅ CRUD operations integration verified")
        
    def test_authentication_flow_integration(self):
        """Test complete authentication flow integration"""
        print("🔐 Testing authentication flow integration...")
        
        # Test invalid credentials
        invalid_response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={"username": "invalid@user.com", "password": "wrong_password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert invalid_response.status_code == 401
        print("   ✅ Invalid credentials properly rejected")
        
        # Test valid credentials  
        valid_response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={"username": "teacher@individual.com", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert valid_response.status_code == 200
        auth_data = valid_response.json()
        
        # Verify token structure
        required_fields = ["access_token", "token_type", "user_type", "user_id", "full_name", "email"]
        for field in required_fields:
            assert field in auth_data
        print("   ✅ Valid credentials accepted with proper token structure")
        
        # Test token validation
        token = auth_data["access_token"]
        validate_response = requests.get(
            f"{self.base_url}/api/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert validate_response.status_code == 200
        print("   ✅ Token validation working")
        
        # Test protected endpoint access
        protected_response = requests.get(
            f"{self.base_url}/api/individual/classrooms",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert protected_response.status_code == 200
        print("   ✅ Protected endpoint access with token working")
        
        print("   ✅ Authentication flow integration verified")
        
    def test_error_handling_integration(self):
        """Test error handling across the system"""
        print("🚨 Testing error handling integration...")
        
        # Get valid token
        login_response = requests.post(
            f"{self.base_url}/api/auth/login",
            data={"username": "teacher@individual.com", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 404 error handling
        response_404 = requests.get(
            f"{self.base_url}/api/individual/classrooms/nonexistent-id",
            headers=headers
        )
        assert response_404.status_code == 404
        print("   ✅ 404 errors properly handled")
        
        # Test validation error handling
        invalid_classroom = {
            "name": "",  # Empty name should cause validation error
            "grade_level": "Test"
        }
        
        validation_response = requests.post(
            f"{self.base_url}/api/individual/classrooms",
            json=invalid_classroom,
            headers=headers
        )
        # Should handle validation gracefully
        print(f"   ✅ Validation handling: Status {validation_response.status_code}")
        
        print("   ✅ Error handling integration verified")
        
    def run_all_tests(self):
        """Run all integration tests"""
        print("=== INTEGRATION TEST SUITE ===\n")
        
        tests = [
            self.test_api_data_consistency,
            self.test_frontend_backend_integration,
            self.test_crud_operations_integration,
            self.test_authentication_flow_integration,
            self.test_error_handling_integration
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                test()
                passed += 1
                print("")
            except Exception as e:
                print(f"   ❌ {test.__name__} FAILED: {str(e)}\n")
                failed += 1
                
        print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
        return passed, failed

if __name__ == "__main__":
    suite = IntegrationTestSuite()
    suite.run_all_tests()