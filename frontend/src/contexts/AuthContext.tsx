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
          const user = await authApi.validateToken(token)
          setUser(user)
        } catch (error) {
          localStorage.removeItem('token')
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
      setUser(response.user)
      setRoles(response.roles)
      setCurrentRole(response.roles[0] || null)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
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