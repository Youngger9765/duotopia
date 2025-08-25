import type { User } from '@/types'
import { api } from '@/lib/api'

export const authApi = {
  // 主要登入方法，包含角色判斷邏輯
  login: async (email: string, password: string) => {
    // This is already implemented correctly in LoginPage.tsx
    // Just need to parse the response properly
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    
    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    })
    
    const data = response.data
    
    // Determine roles based on user type
    let roles = []
    if (data.is_individual_teacher) {
      roles.push('individual_teacher')
    }
    if (data.is_institutional_admin) {
      roles.push('institutional_admin')
    }
    if (data.user_type === 'admin') {
      roles.push('admin')
    }
    if (roles.length === 0) {
      roles.push('teacher') // Default role
    }
    
    // Return the response in the expected format
    return {
      access_token: data.access_token,
      user: {
        id: data.user_id,
        email: email,
        full_name: data.full_name || email,
        name: data.full_name || email,
        role: roles[0], // Primary role
        has_multiple_roles: roles.length > 1,
        is_individual_teacher: data.is_individual_teacher || false
      } as User,
      roles: roles,
    }
  },

  validateToken: async (token: string) => {
    // Call the backend API to validate token and get user info
    try {
      const response = await api.get('/api/auth/validate', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      return {
        id: response.data.user_id,
        email: response.data.email,
        full_name: response.data.full_name,
        name: response.data.full_name
      } as User
    } catch (error) {
      // If validation fails, throw error to force re-login
      throw new Error('Token validation failed')
    }
  },

  // Google OAuth 登入
  googleLogin: async (idToken: string) => {
    const response = await api.post('/api/auth/google', { id_token: idToken })
    return response.data
  },

  // 學生登入
  studentLogin: async (email: string, birthDate: string) => {
    const response = await api.post('/api/auth/student/login', { 
      email, 
      birth_date: birthDate 
    })
    return response.data
  },

  // 註冊新用戶
  register: async (data: any) => {
    const response = await api.post('/api/auth/register', data)
    return response.data
  },

  // 驗證 token
  validate: async () => {
    const response = await api.get('/api/auth/validate')
    return response.data
  }
}