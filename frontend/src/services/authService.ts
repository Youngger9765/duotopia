import api from './api';

interface LoginCredentials {
  email: string;
  password: string;
}

interface StudentLoginCredentials {
  id: number;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    name: string;
    email: string;
    [key: string]: unknown;
  };
}

export const authService = {
  async studentLogin(credentials: StudentLoginCredentials): Promise<LoginResponse> {
    const response = await api.post('/api/auth/student/login', credentials);
    return response.data;
  },

  async teacherLogin(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await api.post('/api/auth/teacher/login', credentials);
    return response.data;
  },

  async validateToken(): Promise<unknown> {
    const response = await api.get('/api/auth/validate');
    return response.data;
  },

  async logout(): Promise<void> {
    // Clear local storage
    localStorage.removeItem('auth-storage');
    localStorage.removeItem('student-auth-storage');
  }
};
