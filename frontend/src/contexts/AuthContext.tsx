import React, { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '@/lib/api'

interface User {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'teacher' | 'student'
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  googleLogin: (idToken: string) => Promise<void>
  studentLogin: (email: string, birthDate: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    validateToken()
  }, [])

  const validateToken = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const response = await authApi.validate()
      setUser(response.data)
    } catch (error) {
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password)
    localStorage.setItem('token', response.data.access_token)
    await validateToken()
  }

  const googleLogin = async (idToken: string) => {
    const response = await authApi.googleLogin(idToken)
    localStorage.setItem('token', response.data.access_token)
    await validateToken()
  }

  const studentLogin = async (email: string, birthDate: string) => {
    const response = await authApi.studentLogin(email, birthDate)
    localStorage.setItem('token', response.data.access_token)
    await validateToken()
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, googleLogin, studentLogin, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}