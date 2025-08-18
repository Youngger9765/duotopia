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
  login: (email: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username: email, password })),
  
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
  
  createClass: (data: any) =>
    api.post('/api/teachers/classes', data),
  
  getClasses: () =>
    api.get('/api/teachers/classes'),
  
  addStudentsToClass: (classId: string, studentIds: string[]) =>
    api.post(`/api/teachers/classes/${classId}/students`, { student_ids: studentIds }),
  
  createCourse: (data: any) =>
    api.post('/api/teachers/courses', data),
  
  getCourses: () =>
    api.get('/api/teachers/courses'),
  
  createLesson: (courseId: string, data: any) =>
    api.post(`/api/teachers/courses/${courseId}/lessons`, data),
  
  createAssignments: (data: any) =>
    api.post('/api/teachers/assignments', data),
}

// Student API
export const studentApi = {
  register: (data: any) =>
    api.post('/api/students/register', data),
  
  searchTeacher: (email: string) =>
    api.get(`/api/students/teachers/search?email=${email}`),
  
  getTeacherClasses: (teacherId: string) =>
    api.get(`/api/students/teachers/${teacherId}/classes`),
  
  getClassStudents: (classId: string) =>
    api.get(`/api/students/classes/${classId}/students`),
  
  getAssignments: (studentId: string) =>
    api.get(`/api/students/${studentId}/assignments`),
  
  getCourses: (studentId: string) =>
    api.get(`/api/students/${studentId}/courses`),
  
  submitAssignment: (assignmentId: string, data: any) =>
    api.post(`/api/students/assignments/${assignmentId}/submit`, data),
  
  updateParentInfo: (studentId: string, parentEmail: string, parentPhone: string) =>
    api.put(`/api/students/${studentId}/parent-info`, { parent_email: parentEmail, parent_phone: parentPhone }),
}