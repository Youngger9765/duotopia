/**
 * API Client for Duotopia
 */

import { API_URL } from '../config/api';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    name: string;
    is_demo: boolean;
  };
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  phone?: string;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    this.baseUrl = API_URL;
    // Load token from localStorage if exists
    this.token = localStorage.getItem('access_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // ============ Auth Methods ============
  async teacherLogin(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/api/auth/teacher/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    // Save token
    this.token = response.access_token;
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));

    return response;
  }

  async teacherRegister(data: RegisterRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/api/auth/teacher/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    // Save token
    this.token = response.access_token;
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));

    return response;
  }

  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // ============ Teacher Methods ============
  async getTeacherProfile() {
    return this.request('/api/teachers/me');
  }

  async getTeacherDashboard() {
    return this.request('/api/teachers/dashboard');
  }

  async getTeacherClassrooms() {
    return this.request('/api/teachers/classrooms');
  }

  async getTeacherPrograms() {
    return this.request('/api/teachers/programs');
  }

  async getProgramDetail(programId: number) {
    return this.request(`/api/teachers/programs/${programId}`);
  }

  // ============ Classroom CRUD Methods ============
  async updateClassroom(classroomId: number, data: { name?: string; description?: string; level?: string }) {
    return this.request(`/api/teachers/classrooms/${classroomId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteClassroom(classroomId: number) {
    return this.request(`/api/teachers/classrooms/${classroomId}`, {
      method: 'DELETE',
    });
  }

  async createClassroom(data: { name: string; description?: string; level: string }) {
    return this.request('/api/teachers/classrooms', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============ Student CRUD Methods ============
  async createStudent(data: { 
    name: string; 
    email?: string;  // Email 改為選填
    student_id?: string;
    birthdate: string;
    phone?: string;
    classroom_id?: number;
  }) {
    return this.request('/api/teachers/students', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateStudent(studentId: number, data: {
    name?: string;
    email?: string;
    student_id?: string;
    birthdate?: string;
    phone?: string;
    classroom_id?: number;
    status?: string;
  }) {
    return this.request(`/api/teachers/students/${studentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteStudent(studentId: number) {
    return this.request(`/api/teachers/students/${studentId}`, {
      method: 'DELETE',
    });
  }

  async resetStudentPassword(studentId: number) {
    return this.request(`/api/teachers/students/${studentId}/reset-password`, {
      method: 'POST',
    });
  }

  // ============ Program CRUD Methods ============
  async createProgram(data: { 
    name: string; 
    description?: string; 
    level?: string;
    classroom_id: number;
    estimated_hours?: number;
  }) {
    return this.request('/api/teachers/programs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProgram(programId: number, data: {
    name?: string;
    description?: string;
    level?: string;
    estimated_hours?: number;
  }) {
    return this.request(`/api/teachers/programs/${programId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProgram(programId: number) {
    return this.request(`/api/teachers/programs/${programId}`, {
      method: 'DELETE',
    });
  }

  async reorderPrograms(orderData: { id: number; order_index: number }[]) {
    return this.request('/api/teachers/programs/reorder', {
      method: 'PUT',
      body: JSON.stringify(orderData),
    });
  }

  async reorderLessons(programId: number, orderData: { id: number; order_index: number }[]) {
    return this.request(`/api/teachers/programs/${programId}/lessons/reorder`, {
      method: 'PUT',
      body: JSON.stringify(orderData),
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();