#!/usr/bin/env python3
"""
Comprehensive test script for Duotopia system
Tests teacher login, student login, dashboards, course creation, and class management
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test credentials
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"
STUDENT_PHONE = "+1234567890"
STUDENT_OTP = "123456"  # Fixed OTP for testing

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test_header(test_name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing: {test_name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

def test_teacher_login():
    """Test teacher login flow"""
    print_test_header("Teacher Login")
    
    try:
        # Login request
        login_data = {
            "username": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            print_success(f"Teacher login successful")
            print_info(f"Access token: {token_data['access_token'][:20]}...")
            print_info(f"Token type: {token_data['token_type']}")
            print_info(f"User type: {token_data['user_type']}")
            print_info(f"User ID: {token_data['user_id']}")
            return token_data['access_token']
        else:
            print_error(f"Teacher login failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Exception during teacher login: {str(e)}")
        return None

def test_teacher_dashboard(token):
    """Test teacher dashboard access"""
    print_test_header("Teacher Dashboard")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get teacher profile
        response = requests.get(f"{BASE_URL}/api/teachers/profile", headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            print_success("Teacher profile retrieved successfully")
            print_info(f"Teacher name: {profile.get('name', 'N/A')}")
            print_info(f"Teacher email: {profile.get('email', 'N/A')}")
            print_info(f"Teacher ID: {profile.get('id', 'N/A')}")
            
            # Get teacher's courses
            courses_response = requests.get(f"{BASE_URL}/api/teachers/courses", headers=headers)
            
            if courses_response.status_code == 200:
                courses = courses_response.json()
                print_success(f"Retrieved {len(courses)} courses")
                for course in courses[:3]:  # Show first 3 courses
                    print_info(f"  - Course: {course.get('title', 'N/A')} (ID: {course.get('id', 'N/A')})")
            else:
                print_error(f"Failed to get courses: {courses_response.status_code}")
                
            return True
        else:
            print_error(f"Failed to get teacher profile: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Exception accessing teacher dashboard: {str(e)}")
        return False

def test_create_course(token):
    """Test course creation"""
    print_test_header("Course Creation")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Create a new course
        course_data = {
            "title": f"Test Course {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "This is a test course created by the automated test script",
            "grade_level": 10,
            "subject": "Mathematics",
            "max_students": 30
        }
        
        response = requests.post(
            f"{BASE_URL}/api/teachers/courses", 
            headers=headers,
            json=course_data
        )
        
        if response.status_code == 200 or response.status_code == 201:
            course = response.json()
            print_success("Course created successfully")
            print_info(f"Course ID: {course.get('id', 'N/A')}")
            print_info(f"Course title: {course.get('title', 'N/A')}")
            print_info(f"Course code: {course.get('course_code', 'N/A')}")
            return course.get('id')
        else:
            print_error(f"Failed to create course: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Exception creating course: {str(e)}")
        return None

def test_student_login():
    """Test student 4-step login flow"""
    print_test_header("Student Login (4-step flow)")
    
    try:
        # Step 1: Send OTP
        otp_data = {"phone_number": STUDENT_PHONE}
        
        response = requests.post(f"{BASE_URL}/api/auth/student/send-otp", json=otp_data)
        
        if response.status_code == 200:
            print_success("Step 1: OTP sent successfully")
        else:
            print_error(f"Step 1 failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
        # Step 2: Verify OTP
        verify_data = {
            "phone_number": STUDENT_PHONE,
            "otp": STUDENT_OTP
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/student/verify-otp", json=verify_data)
        
        if response.status_code == 200:
            result = response.json()
            print_success("Step 2: OTP verified successfully")
            print_info(f"Temporary token: {result['temp_token'][:20]}...")
            temp_token = result['temp_token']
        else:
            print_error(f"Step 2 failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
        # Step 3: Submit student info
        student_info = {
            "name": "Test Student",
            "grade": 10,
            "school": "Test High School"
        }
        
        headers = {"Authorization": f"Bearer {temp_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/auth/student/submit-info", 
            json=student_info,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("Step 3: Student info submitted successfully")
            if result.get('existing_courses'):
                print_info(f"Found {len(result['existing_courses'])} existing courses")
        else:
            print_error(f"Step 3 failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
        # Step 4: Enter course code (using a dummy code for testing)
        course_data = {"course_code": "MATH101"}
        
        response = requests.post(
            f"{BASE_URL}/api/auth/student/enter-course-code",
            json=course_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("Step 4: Course code submitted successfully")
            print_info(f"Access token: {result['access_token'][:20]}...")
            print_info(f"User type: {result['user_type']}")
            print_info(f"Student ID: {result['user_id']}")
            return result['access_token']
        else:
            print_error(f"Step 4 failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Exception during student login: {str(e)}")
        return None

def test_student_dashboard(token):
    """Test student dashboard access"""
    print_test_header("Student Dashboard")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get student profile
        response = requests.get(f"{BASE_URL}/api/students/profile", headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            print_success("Student profile retrieved successfully")
            print_info(f"Student name: {profile.get('name', 'N/A')}")
            print_info(f"Student grade: {profile.get('grade', 'N/A')}")
            print_info(f"Student school: {profile.get('school', 'N/A')}")
            
            # Get student's courses
            courses_response = requests.get(f"{BASE_URL}/api/students/courses", headers=headers)
            
            if courses_response.status_code == 200:
                courses = courses_response.json()
                print_success(f"Retrieved {len(courses)} enrolled courses")
                for course in courses[:3]:  # Show first 3 courses
                    print_info(f"  - Course: {course.get('title', 'N/A')} (Teacher: {course.get('teacher_name', 'N/A')})")
            else:
                print_error(f"Failed to get courses: {courses_response.status_code}")
                
            return True
        else:
            print_error(f"Failed to get student profile: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Exception accessing student dashboard: {str(e)}")
        return False

def test_class_management(teacher_token, course_id):
    """Test class management (add/remove students)"""
    print_test_header("Class Management")
    
    try:
        headers = {
            "Authorization": f"Bearer {teacher_token}",
            "Content-Type": "application/json"
        }
        
        # Get course details
        response = requests.get(
            f"{BASE_URL}/api/teachers/courses/{course_id}", 
            headers=headers
        )
        
        if response.status_code == 200:
            course = response.json()
            print_success("Course details retrieved")
            print_info(f"Course: {course.get('title', 'N/A')}")
            print_info(f"Enrolled students: {len(course.get('students', []))}")
            
            # List students in the course
            if course.get('students'):
                print_info("Students in course:")
                for student in course['students'][:5]:  # Show first 5
                    print_info(f"  - {student.get('name', 'N/A')} (Grade {student.get('grade', 'N/A')})")
            
            return True
        else:
            print_error(f"Failed to get course details: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception in class management: {str(e)}")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Duotopia Comprehensive System Test{RESET}")
    print(f"{BLUE}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Test results tracking
    results = {
        "teacher_login": False,
        "teacher_dashboard": False,
        "course_creation": False,
        "student_login": False,
        "student_dashboard": False,
        "class_management": False
    }
    
    # 1. Test Teacher Login
    teacher_token = test_teacher_login()
    if teacher_token:
        results["teacher_login"] = True
        
        # 2. Test Teacher Dashboard
        if test_teacher_dashboard(teacher_token):
            results["teacher_dashboard"] = True
        
        # 3. Test Course Creation
        course_id = test_create_course(teacher_token)
        if course_id:
            results["course_creation"] = True
            
            # 6. Test Class Management
            if test_class_management(teacher_token, course_id):
                results["class_management"] = True
    
    # 4. Test Student Login
    student_token = test_student_login()
    if student_token:
        results["student_login"] = True
        
        # 5. Test Student Dashboard
        if test_student_dashboard(student_token):
            results["student_dashboard"] = True
    
    # Print summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{BLUE}Total: {passed_tests}/{total_tests} tests passed{RESET}")
    
    if passed_tests == total_tests:
        print(f"\n{GREEN}All tests passed successfully!{RESET}")
        return 0
    else:
        print(f"\n{RED}Some tests failed. Please check the errors above.{RESET}")
        return 1

if __name__ == "__main__":
    # Check if backend is running by trying to access the docs
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print_error("Backend is not responding correctly.")
            sys.exit(1)
    except:
        print_error("Cannot connect to backend at http://localhost:8000")
        print_info("Please ensure the backend is running: python main.py")
        sys.exit(1)
    
    # Run all tests
    exit_code = run_all_tests()
    sys.exit(exit_code)