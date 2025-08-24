#!/usr/bin/env python3
"""
Test course management features
"""
import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWFjaGVyMUBkdW90b3BpYS5jb20iLCJleHAiOjE3NTU2NjUzODN9.QxGIHg1JSyCmBgoCAZdhffAMAZQveWDfSBV1jh1UdtU"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_get_courses():
    """Test getting courses"""
    print("=== Testing Get Courses ===")
    response = requests.get(f"{BASE_URL}/api/teachers/courses", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        courses = response.json()
        print(f"Found {len(courses)} courses")
        if courses:
            course_id = courses[0]['id']
            print(f"First course: {courses[0]['title']}")
            return course_id
    else:
        print(f"Error: {response.text}")
    return None

def test_get_lessons(course_id):
    """Test getting lessons for a course"""
    print(f"\n=== Testing Get Lessons for course {course_id} ===")
    response = requests.get(f"{BASE_URL}/api/teachers/courses/{course_id}/lessons", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        lessons = response.json()
        print(f"Found {len(lessons)} lessons")
        for lesson in lessons[:3]:  # Show first 3
            print(f"  - {lesson['title']} (type: {lesson.get('activity_type', 'unknown')})")
    else:
        print(f"Error: {response.text}")

def test_create_lesson(course_id):
    """Test creating a new lesson"""
    print(f"\n=== Testing Create Lesson ===")
    lesson_data = {
        "title": "測試活動 - API Test",
        "lesson_number": 10,
        "activity_type": "listening_cloze",
        "content": {
            "type": "activity",
            "instructions": "請完成以下活動",
            "sections": []
        },
        "time_limit_minutes": 30
    }
    
    response = requests.post(
        f"{BASE_URL}/api/teachers/courses/{course_id}/lessons", 
        headers=headers,
        json=lesson_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        lesson = response.json()
        print(f"Created lesson: {lesson['title']} (ID: {lesson['id']})")
        return lesson['id']
    else:
        print(f"Error: {response.text}")
    return None

def test_create_course():
    """Test creating a new course"""
    print("\n=== Testing Create Course ===")
    course_data = {
        "title": "測試課程 - API Test",
        "description": "這是一個測試課程",
        "grade_level": 10,
        "subject": "English"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/teachers/courses", 
        headers=headers,
        json=course_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        course = response.json()
        print(f"Created course: {course['title']} (ID: {course['id']})")
        return course['id']
    else:
        print(f"Error: {response.text}")
    return None

if __name__ == "__main__":
    # Test getting courses
    course_id = test_get_courses()
    
    if course_id:
        # Test getting lessons
        test_get_lessons(course_id)
        
        # Test creating a lesson
        lesson_id = test_create_lesson(course_id)
    
    # Test creating a course
    new_course_id = test_create_course()
    
    print("\n✅ All tests completed!")