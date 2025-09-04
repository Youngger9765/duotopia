// 認證相關的類型定義
export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData extends LoginData {
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_type: 'teacher' | 'student';
  user_id: number;
  name: string;
}

export interface User {
  id: number;
  email: string;
  name: string;
  user_type: 'teacher' | 'student';
  is_active: boolean;
}

// API 請求函數
const API_BASE_URL = '/api';

export async function loginTeacher(data: LoginData): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/teacher/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

export async function loginStudent(data: LoginData): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/student/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

export async function registerTeacher(data: RegisterData) {
  const response = await fetch(`${API_BASE_URL}/auth/teacher/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

export async function registerStudent(data: RegisterData) {
  const response = await fetch(`${API_BASE_URL}/auth/student/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

export async function getCurrentUser(): Promise<User> {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('No token found');
  }

  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get user info');
  }

  return response.json();
}

// Token 管理
export function setAuthToken(token: string) {
  localStorage.setItem('token', token);
}

export function removeAuthToken() {
  localStorage.removeItem('token');
}

export function getAuthToken(): string | null {
  return localStorage.getItem('token');
}

export function setUserInfo(user: AuthResponse) {
  localStorage.setItem('userInfo', JSON.stringify({
    id: user.user_id,
    name: user.name,
    user_type: user.user_type
  }));
}

export function getUserInfo() {
  const userInfo = localStorage.getItem('userInfo');
  return userInfo ? JSON.parse(userInfo) : null;
}

export function clearAuthData() {
  removeAuthToken();
  localStorage.removeItem('userInfo');
}
