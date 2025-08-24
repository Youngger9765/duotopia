# 📡 Individual Teacher Dashboard API Documentation

## Overview

The Individual Teacher Dashboard API provides comprehensive endpoints for managing classrooms, students, and courses for individual teachers using the Duotopia platform.

**Base URL**: `http://localhost:8000/api/individual`  
**Authentication**: Bearer Token (JWT)  
**API Version**: v2 (uses original system models)

---

## 🔐 Authentication

### Login Endpoint
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=teacher@individual.com&password=password123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "teacher",
  "user_id": "9310c6d3-b78a-4fa5-be94-ce702ce2e37c",
  "full_name": "個體戶老師",
  "email": "teacher@individual.com",
  "is_individual_teacher": true,
  "is_institutional_admin": false,
  "current_role_context": "individual"
}
```

### Token Validation
```http
GET /api/auth/validate
Authorization: Bearer {access_token}
```

---

## 🏫 Classroom Management

### List Classrooms
```http
GET /api/individual/classrooms
Authorization: Bearer {access_token}
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "小學英語基礎班",
    "grade_level": "小學三年級",
    "student_count": 3,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### Create Classroom
```http
POST /api/individual/classrooms
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "新英語班級",
  "grade_level": "小學五年級",
  "difficulty_level": "A1"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "新英語班級",
  "grade_level": "小學五年級",
  "student_count": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get Classroom Detail
```http
GET /api/individual/classrooms/{classroom_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "小學英語基礎班",
  "grade_level": "小學三年級",
  "teacher_name": "個體戶老師",
  "students": [
    {
      "id": "student_id_1",
      "name": "張小強",
      "email": "student4@duotopia.com"
    }
  ],
  "courses": [
    {
      "id": "course_id_1",
      "title": "自然發音與基礎拼讀",
      "description": "學習英語字母發音規則"
    }
  ],
  "student_count": 3,
  "course_count": 2
}
```

### Delete Classroom
```http
DELETE /api/individual/classrooms/{classroom_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "message": "教室已刪除"
}
```

---

## 👥 Student Management

### List Students
```http
GET /api/individual/students
Authorization: Bearer {access_token}
```

**Response:**
```json
[
  {
    "id": "85e24f62-0ca3-461b-8f8d-81d99e54c363",
    "full_name": "許小婷",
    "name": "許小婷",
    "email": "student11@duotopia.com",
    "birth_date": "2009-08-28",
    "classroom_names": ["個體戶老師的班級"],
    "referred_by": null,
    "learning_goals": null,
    "is_default_password": null,
    "default_password": null
  }
]
```

### Create Student
```http
POST /api/individual/students
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "新學生",
  "email": "new.student@example.com",
  "birth_date": "2010-05-15"
}
```

**Response:**
```json
{
  "id": "new_student_id",
  "full_name": "新學生",
  "name": "新學生",
  "email": "new.student@example.com",
  "birth_date": "2010-05-15",
  "classroom_names": []
}
```

### Update Student
```http
PUT /api/individual/students/{student_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "更新的學生姓名",
  "email": "updated.email@example.com",
  "birth_date": "2010-05-15"
}
```

### Delete Student
```http
DELETE /api/individual/students/{student_id}
Authorization: Bearer {access_token}
```

---

## 📚 Course Management

### List Courses
```http
GET /api/individual/courses
Authorization: Bearer {access_token}
```

**Response:**
```json
[
  {
    "id": "b24745d0-e47f-4bd5-8dbc-cc736135330b",
    "title": "基礎英語會話 - 個體戶老師",
    "description": "培養日常英語對話能力",
    "difficulty_level": "A1",
    "lesson_count": 4
  }
]
```

### Create Course
```http
POST /api/individual/courses
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "新英語課程",
  "description": "課程描述",
  "difficulty_level": "A2"
}
```

**Response:**
```json
{
  "id": "new_course_id",
  "title": "新英語課程",
  "description": "課程描述",
  "difficulty_level": "A2",
  "lesson_count": 0
}
```

---

## 🔗 Classroom-Student Management

### Add Student to Classroom
```http
POST /api/individual/classrooms/{classroom_id}/students/{student_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "message": "學生已加入教室"
}
```

### Remove Student from Classroom
```http
DELETE /api/individual/classrooms/{classroom_id}/students/{student_id}
Authorization: Bearer {access_token}
```

### Get Classroom Students
```http
GET /api/individual/classrooms/{classroom_id}/students
Authorization: Bearer {access_token}
```

**Response:**
```json
[
  {
    "id": "student_id",
    "full_name": "學生姓名",
    "name": "學生姓名",
    "email": "student@example.com"
  }
]
```

---

## 📊 Statistics & Analytics

### Get Classroom Statistics
```http
GET /api/individual/classrooms/{classroom_id}/stats
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "total_students": 18,
  "active_assignments": 5,
  "completion_rate": 85,
  "average_score": 87.5
}
```

---

## 🚨 Error Handling

### Common HTTP Status Codes

| Status Code | Description | Example Response |
|-------------|-------------|------------------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Invalid or missing authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `422` | Validation Error | Request data validation failed |
| `500` | Internal Server Error | Server processing error |

### Error Response Format
```json
{
  "detail": "Error message describing the issue"
}
```

### Validation Error Response
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## 🔄 Data Models

### Classroom Model
```typescript
interface Classroom {
  id: string
  name: string
  grade_level?: string
  student_count: number
  created_at: string
}
```

### Student Model
```typescript
interface Student {
  id: string
  full_name: string
  name?: string
  email?: string
  birth_date: string
  classroom_names: string[]
  referred_by?: string
  learning_goals?: string
  is_default_password?: boolean
  default_password?: string
}
```

### Course Model
```typescript
interface Course {
  id: string
  title: string
  description?: string
  difficulty_level?: 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2'
  lesson_count: number
}
```

---

## 🧪 Testing

### Test Account Credentials
```
Email: teacher@individual.com
Password: password123
```

### Sample API Calls
```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teacher@individual.com&password=password123"

# Get Classrooms
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/individual/classrooms"

# Get Students  
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/individual/students"

# Get Courses
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8000/api/individual/courses"
```

---

## 📈 Performance Benchmarks

| Endpoint | Average Response Time | Notes |
|----------|----------------------|-------|
| Login | 0.2s | Authentication processing |
| Get Classrooms | 0.1s | Includes student count |
| Get Students | 0.3s | With classroom relationships |
| Get Courses | 0.1s | With lesson count |
| Create Operations | 0.2s | Database write operations |

---

## 🔒 Security Considerations

- **Authentication**: JWT tokens with expiration
- **Authorization**: Role-based access control
- **Input Validation**: All inputs validated and sanitized  
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **CORS**: Configured for frontend domains only
- **Rate Limiting**: Recommended for production deployment

---

*Last Updated: 2024-08-23*  
*API Version: individual_v2*