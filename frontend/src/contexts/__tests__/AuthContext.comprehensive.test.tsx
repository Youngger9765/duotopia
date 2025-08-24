import React from 'react'
import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { AuthProvider, useAuth } from '../AuthContext'
import { authApi } from '@/api/auth'

// Mock the auth API
vi.mock('@/api/auth')

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    })
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('AuthContext Comprehensive Tests', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  )

  beforeEach(() => {
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Initial State and Loading', () => {
    it('should initialize with null user and loading state', () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      expect(result.current.user).toBeNull()
      expect(result.current.isLoading).toBe(true)
      expect(result.current.roles).toEqual([])
      expect(result.current.currentRole).toBeNull()
    })

    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      expect(() => renderHook(() => useAuth())).toThrow(
        'useAuth must be used within an AuthProvider'
      )
      
      consoleSpy.mockRestore()
    })
  })

  describe('Authentication with Saved Token', () => {
    it('should restore user from localStorage on mount', async () => {
      // Setup localStorage data
      localStorageMock.setItem('token', 'valid-token')
      localStorageMock.setItem('userEmail', 'teacher@individual.com')
      localStorageMock.setItem('userFullName', '個體戶老師')
      localStorageMock.setItem('userId', '123')
      localStorageMock.setItem('userRole', 'individual_teacher')

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toEqual({
        id: 123,
        email: 'teacher@individual.com',
        full_name: '個體戶老師',
        name: '個體戶老師',
        role: 'individual_teacher',
        has_multiple_roles: true,
        is_individual_teacher: true
      })

      expect(result.current.roles).toEqual(['individual_teacher', 'teacher'])
      expect(result.current.currentRole).toBe('individual_teacher')
    })

    it('should handle missing localStorage data gracefully', async () => {
      localStorageMock.setItem('token', 'valid-token')
      localStorageMock.setItem('userEmail', 'test@example.com')
      // Missing fullName and userId

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toEqual({
        id: 1, // Default ID
        email: 'test@example.com',
        full_name: 'test@example.com', // Falls back to email
        name: 'test@example.com',
        role: 'teacher', // Default role
        has_multiple_roles: false,
        is_individual_teacher: false
      })
    })

    it('should validate token with API when localStorage data is incomplete', async () => {
      const mockUser = {
        id: 456,
        email: 'api@example.com',
        full_name: 'API User',
        role: 'teacher'
      }

      vi.mocked(authApi.validateToken).mockResolvedValueOnce(mockUser)
      localStorageMock.setItem('token', 'valid-token')

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(authApi.validateToken).toHaveBeenCalledWith('valid-token')
      expect(result.current.user).toEqual(mockUser)
    })

    it('should clear invalid token and redirect to login', async () => {
      vi.mocked(authApi.validateToken).mockRejectedValueOnce(new Error('Invalid token'))
      localStorageMock.setItem('token', 'invalid-token')

      // Mock window.location.href
      delete (window as any).location
      window.location = { href: '' } as any

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userEmail')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userFullName')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userRole')
      expect(window.location.href).toBe('/login')
    })
  })

  describe('Login Functionality', () => {
    it('should handle successful login with individual teacher', async () => {
      const mockResponse = {
        access_token: 'new-token',
        user: {
          id: 789,
          email: 'teacher@individual.com',
          full_name: 'Individual Teacher',
          role: 'teacher'
        },
        roles: ['individual_teacher', 'teacher']
      }

      vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login('teacher@individual.com', 'password123')
      })

      expect(authApi.login).toHaveBeenCalledWith('teacher@individual.com', 'password123')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'new-token')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('userEmail', 'teacher@individual.com')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('userFullName', 'Individual Teacher')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('userId', '789')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('userRole', 'individual_teacher')

      expect(result.current.user).toEqual({
        ...mockResponse.user,
        has_multiple_roles: true,
        is_individual_teacher: true
      })
      expect(result.current.roles).toEqual(['individual_teacher', 'teacher'])
      expect(result.current.currentRole).toBe('individual_teacher')
    })

    it('should handle login with single role', async () => {
      const mockResponse = {
        access_token: 'admin-token',
        user: {
          id: 111,
          email: 'admin@institution.com',
          full_name: 'Admin User',
          role: 'admin'
        },
        roles: ['admin']
      }

      vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login('admin@institution.com', 'password')
      })

      expect(result.current.user).toEqual({
        ...mockResponse.user,
        has_multiple_roles: false,
        is_individual_teacher: false
      })
      expect(result.current.roles).toEqual(['admin'])
      expect(result.current.currentRole).toBe('admin')
    })

    it('should handle login failure', async () => {
      const error = new Error('Invalid credentials')
      vi.mocked(authApi.login).mockRejectedValueOnce(error)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await expect(
        result.current.login('wrong@example.com', 'wrongpass')
      ).rejects.toThrow('Invalid credentials')

      expect(result.current.user).toBeNull()
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('should handle login response without user data', async () => {
      const mockResponse = {
        access_token: 'token-only',
        roles: ['teacher']
      }

      vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse as any)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login('test@example.com', 'password')
      })

      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'token-only')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('userEmail', 'test@example.com')
      // Should not set undefined values
      expect(localStorageMock.setItem).not.toHaveBeenCalledWith('userFullName', undefined)
      expect(localStorageMock.setItem).not.toHaveBeenCalledWith('userId', 'undefined')
    })
  })

  describe('Logout Functionality', () => {
    it('should clear all auth data on logout', async () => {
      // Setup initial logged-in state
      localStorageMock.setItem('token', 'valid-token')
      localStorageMock.setItem('userEmail', 'user@example.com')
      localStorageMock.setItem('userFullName', 'Test User')
      localStorageMock.setItem('userId', '123')
      localStorageMock.setItem('userRole', 'teacher')

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.user).not.toBeNull()
      })

      act(() => {
        result.current.logout()
      })

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userEmail')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userFullName')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userId')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('userRole')

      expect(result.current.user).toBeNull()
      expect(result.current.roles).toEqual([])
      expect(result.current.currentRole).toBeNull()
    })
  })

  describe('Role Switching', () => {
    it('should switch between available roles', async () => {
      const mockResponse = {
        access_token: 'multi-role-token',
        user: {
          id: 999,
          email: 'multi@example.com',
          full_name: 'Multi Role User'
        },
        roles: ['teacher', 'admin', 'individual_teacher']
      }

      vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login('multi@example.com', 'password')
      })

      expect(result.current.currentRole).toBe('teacher') // First role

      act(() => {
        result.current.switchRole('admin')
      })

      expect(result.current.currentRole).toBe('admin')

      act(() => {
        result.current.switchRole('individual_teacher')
      })

      expect(result.current.currentRole).toBe('individual_teacher')
    })

    it('should not switch to unavailable role', async () => {
      const mockResponse = {
        access_token: 'limited-token',
        user: { id: 1, email: 'limited@example.com', full_name: 'Limited User' },
        roles: ['teacher']
      }

      vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login('limited@example.com', 'password')
      })

      expect(result.current.currentRole).toBe('teacher')

      act(() => {
        result.current.switchRole('admin') // Not in available roles
      })

      expect(result.current.currentRole).toBe('teacher') // Should not change
    })
  })

  describe('Edge Cases and Error Handling', () => {
    it('should handle empty roles array', async () => {
      const mockResponse = {
        access_token: 'no-roles-token',
        user: { id: 1, email: 'noroles@example.com', full_name: 'No Roles User' },
        roles: []
      }

      vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login('noroles@example.com', 'password')
      })

      expect(result.current.roles).toEqual([])
      expect(result.current.currentRole).toBeNull()
    })

    it('should handle network errors during initialization', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      vi.mocked(authApi.validateToken).mockRejectedValueOnce(new Error('Network error'))
      localStorageMock.setItem('token', 'valid-token')

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toBeNull()
      
      consoleErrorSpy.mockRestore()
    })

    it('should handle malformed user ID in localStorage', async () => {
      localStorageMock.setItem('token', 'valid-token')
      localStorageMock.setItem('userEmail', 'test@example.com')
      localStorageMock.setItem('userId', 'not-a-number')
      localStorageMock.setItem('userRole', 'teacher')

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user?.id).toBe(1) // Should fallback to default
    })
  })
})