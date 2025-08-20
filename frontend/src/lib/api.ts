import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) => {
    const formData = new URLSearchParams({ username: email, password })
    return api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    })
  },
  
  googleLogin: (idToken: string) =>
    api.post('/api/auth/google', { id_token: idToken }),
  
  studentLogin: (email: string, birthDate: string) =>
    api.post('/api/auth/student/login', { email, birth_date: birthDate }),
  
  register: (data: any) =>
    api.post('/api/auth/register', data),
  
  validate: () =>
    api.get('/api/auth/validate'),
}

// Teacher API
export const teacherApi = {
  getDashboard: () =>
    api.get('/api/teachers/dashboard'),
  
  createClassroom: (data: any) =>
    api.post('/api/teachers/classrooms', data),
  
  getClassrooms: () =>
    api.get('/api/teachers/classrooms'),
    
  getClassroom: (classroomId: string) =>
    api.get(`/api/teachers/classrooms/${classroomId}`),
    
  getClassroomStudents: (classroomId: string) =>
    api.get(`/api/teachers/classrooms/${classroomId}/students`),
    
  updateClassroom: (classroomId: string, data: any) =>
    api.put(`/api/teachers/classrooms/${classroomId}`, data),
    
  deleteClassroom: (classroomId: string) =>
    api.delete(`/api/teachers/classrooms/${classroomId}`),
  
  addStudentsToClassroom: (classroomId: string, studentIds: string[]) =>
    api.post(`/api/teachers/classrooms/${classroomId}/students`, { student_ids: studentIds }),
  
  createCourse: (data: any) =>
    api.post('/api/teachers/courses', data),
  
  getCourses: () =>
    api.get('/api/teachers/courses'),
    
  getCourse: (courseId: string) =>
    api.get(`/api/teachers/courses/${courseId}`),
    
  updateCourse: (courseId: string, data: any) =>
    api.put(`/api/teachers/courses/${courseId}`, data),
    
  deleteCourse: (courseId: string) =>
    api.delete(`/api/teachers/courses/${courseId}`),
  
  createLesson: (courseId: string, data: any) =>
    api.post(`/api/teachers/courses/${courseId}/lessons`, data),
    
  getLessons: (courseId: string) =>
    api.get(`/api/teachers/courses/${courseId}/lessons`),
  
  createAssignments: (data: any) =>
    api.post('/api/teachers/assignments', data),
}

// Student API
export const studentApi = {
  register: (data: any) =>
    api.post('/api/students/register', data),
  
  searchTeacher: (email: string) =>
    api.get(`/api/students/teachers/search?email=${email}`),
  
  getTeacherClassrooms: (teacherId: string) =>
    api.get(`/api/students/teachers/${teacherId}/classrooms`),
  
  getClassroomStudents: (classroomId: string) =>
    api.get(`/api/students/classrooms/${classroomId}/students`),
  
  getAssignments: (studentId: string) =>
    api.get(`/api/students/${studentId}/assignments`),
  
  getCourses: (studentId: string) =>
    api.get(`/api/students/${studentId}/courses`),
  
  submitAssignment: (assignmentId: string, data: any) =>
    api.post(`/api/students/assignments/${assignmentId}/submit`, data),
  
  updateParentInfo: (studentId: string, parentEmail: string, parentPhone: string) =>
    api.put(`/api/students/${studentId}/parent-info`, { parent_email: parentEmail, parent_phone: parentPhone }),
}

// Admin API
export const adminApi = {
  // Schools/Institutions Management
  getSchools: () =>
    api.get('/api/admin/schools'),
    
  getSchool: (schoolId: string) =>
    api.get(`/api/admin/schools/${schoolId}`),
    
  createSchool: (data: any) =>
    api.post('/api/admin/schools', data),
    
  updateSchool: (schoolId: string, data: any) =>
    api.put(`/api/admin/schools/${schoolId}`, data),
    
  deleteSchool: (schoolId: string) =>
    api.delete(`/api/admin/schools/${schoolId}`),
  
  // Staff/User Management
  getUsers: (params?: { role?: string; school_id?: string }) =>
    api.get('/api/admin/users', { params }),
    
  getUser: (userId: string) =>
    api.get(`/api/admin/users/${userId}`),
    
  createUser: (data: any) =>
    api.post('/api/admin/users', data),
    
  updateUser: (userId: string, data: any) =>
    api.put(`/api/admin/users/${userId}`, data),
    
  deleteUser: (userId: string) =>
    api.delete(`/api/admin/users/${userId}`),
    
  updateUserStatus: (userId: string, status: string) =>
    api.put(`/api/admin/users/${userId}/status`, { status }),
  
  // Student Management (Admin)
  getStudents: (params?: { school_id?: string; class_id?: string; search?: string }) =>
    api.get('/api/admin/students', { params }),
    
  getStudent: (studentId: string) =>
    api.get(`/api/admin/students/${studentId}`),
    
  createStudent: (data: any) =>
    api.post('/api/admin/students', data),
    
  updateStudent: (studentId: string, data: any) =>
    api.put(`/api/admin/students/${studentId}`, data),
    
  deleteStudent: (studentId: string) =>
    api.delete(`/api/admin/students/${studentId}`),
  
  // Statistics
  getStats: () =>
    api.get('/api/admin/stats'),
    
  getClassStats: (classId: string) =>
    api.get(`/api/teachers/classes/${classId}/stats`),
    
  getCourseStats: (courseId: string) =>
    api.get(`/api/teachers/courses/${courseId}/stats`),
}