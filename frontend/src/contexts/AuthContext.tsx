import React, { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '@/api/auth'
import type { User } from '@/types'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  roles: string[]
  currentRole: string | null
  switchRole: (role: string) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [roles, setRoles] = useState<string[]>([])
  const [currentRole, setCurrentRole] = useState<string | null>(null)

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          // For now, get user info from localStorage
          const savedEmail = localStorage.getItem('userEmail')
          const savedFullName = localStorage.getItem('userFullName')
          const savedUserId = localStorage.getItem('userId')
          const savedRole = localStorage.getItem('userRole')
          
          if (savedEmail) {
            // Use saved data directly
            const userData = {
              id: parseInt(savedUserId || '1'),
              email: savedEmail,
              full_name: savedFullName || savedEmail,
              name: savedFullName || savedEmail,
              role: savedRole || 'teacher',
              has_multiple_roles: savedRole === 'individual_teacher',
              is_individual_teacher: savedRole === 'individual_teacher'
            }
            setUser(userData)
            
            // Set roles based on saved role
            if (savedRole === 'individual_teacher') {
              setRoles(['individual_teacher', 'teacher'])
              setCurrentRole('individual_teacher')
            } else {
              setRoles([savedRole || 'teacher'])
              setCurrentRole(savedRole || 'teacher')
            }
          } else {
            // Try to validate token from API
            try {
              const user = await authApi.validateToken(token)
              setUser(user)
            } catch (error) {
              // If API fails, clear token and force re-login
              localStorage.removeItem('token')
              localStorage.removeItem('userEmail')
              localStorage.removeItem('userFullName')
              localStorage.removeItem('userRole')
            }
          }
        } catch (error) {
          localStorage.removeItem('token')
          localStorage.removeItem('userEmail')
          localStorage.removeItem('userFullName')
          localStorage.removeItem('userRole')
          window.location.href = '/login'
        }
      }
      setIsLoading(false)
    }
    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password)
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('userEmail', email) // Save email for validateToken
      if (response.user?.full_name) {
        localStorage.setItem('userFullName', response.user.full_name)
      }
      if (response.user?.id) {
        localStorage.setItem('userId', response.user.id.toString())
      }
      // Save the current role
      if (response.roles && response.roles.length > 0) {
        localStorage.setItem('userRole', response.roles[0])
      }
      
      // Enhance user object with role information
      const enhancedUser = {
        ...response.user,
        has_multiple_roles: response.roles && response.roles.length > 1,
        is_individual_teacher: response.roles && response.roles.includes('individual_teacher')
      }
      
      setUser(enhancedUser)
      setRoles(response.roles)
      setCurrentRole(response.roles[0] || null)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userFullName')
    localStorage.removeItem('userId')
    localStorage.removeItem('userRole')
    setUser(null)
    setRoles([])
    setCurrentRole(null)
  }

  const switchRole = (role: string) => {
    if (roles.includes(role)) {
      setCurrentRole(role)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
        roles,
        currentRole,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}