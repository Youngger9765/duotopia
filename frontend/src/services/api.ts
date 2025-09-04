import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  // Check for teacher token
  const teacherAuth = localStorage.getItem('auth-storage');
  if (teacherAuth) {
    const { state } = JSON.parse(teacherAuth);
    if (state?.token) {
      config.headers.Authorization = `Bearer ${state.token}`;
    }
  }

  // Check for student token
  const studentAuth = localStorage.getItem('student-auth-storage');
  if (studentAuth) {
    const { state } = JSON.parse(studentAuth);
    if (state?.token) {
      config.headers.Authorization = `Bearer ${state.token}`;
    }
  }

  return config;
});

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear auth and redirect to login
      localStorage.removeItem('auth-storage');
      localStorage.removeItem('student-auth-storage');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
