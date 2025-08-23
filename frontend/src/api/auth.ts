import type { User } from '@/types'
import { api } from '@/lib/api'

export const authApi = {
  login: async (email: string, password: string) => {
    // This is already implemented correctly in LoginPage.tsx
    // Just need to parse the response properly
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    
    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      body: formData,
    })
    
    if (!response.ok) {
      throw new Error('Login failed')
    }
    
    const data = await response.json()
    
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
}