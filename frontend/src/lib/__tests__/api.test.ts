
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock the config
vi.mock('@/config/api', () => ({
  API_URL: import.meta.env.VITE_API_URL
}))

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Import after mocking
import { apiClient } from '../api'

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('teacherLogin', () => {
    const loginData = {
      email: 'teacher@test.com',
      password: 'password123',
    }

    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: 1,
        email: 'teacher@test.com',
        name: 'Test Teacher',
        is_demo: false,
      },
    }

    it('should login teacher successfully', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.teacherLogin(loginData)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/teacher/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(loginData),
        })
      )

      expect(result).toEqual(mockResponse)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'test-token')
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockResponse.user))
    })

    it('should handle login error', async () => {
      const errorResponse = { detail: 'Invalid credentials' }
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve(errorResponse),
      })

      await expect(apiClient.teacherLogin(loginData)).rejects.toThrow('Invalid credentials')
    })

    it('should handle network error', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('Network error')),
      })

      await expect(apiClient.teacherLogin(loginData)).rejects.toThrow('HTTP error! status: 500')
    })
  })

  describe('teacherRegister', () => {
    const registerData = {
      email: 'newteacher@test.com',
      password: 'password123',
      name: 'New Teacher',
      phone: '1234567890',
    }

    const mockResponse = {
      access_token: 'register-token',
      token_type: 'bearer',
      user: {
        id: 2,
        email: 'newteacher@test.com',
        name: 'New Teacher',
        is_demo: false,
      },
    }

    it('should register teacher successfully', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.teacherRegister(registerData)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/teacher/register'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(registerData),
        })
      )

      expect(result).toEqual(mockResponse)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'register-token')
    })
  })

  describe('logout', () => {
    it('should clear tokens and user data', () => {
      apiClient.logout()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user')
    })
  })

  describe('isAuthenticated', () => {
    it('should return true when token exists', () => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
      // Create new instance to pick up the mocked localStorage
      const { apiClient: newClient } = require('../api')

      expect(newClient.isAuthenticated()).toBe(true)
    })

    it('should return false when no token exists', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      expect(apiClient.isAuthenticated()).toBe(false)
    })
  })

  describe('getCurrentUser', () => {
    it('should return user data when exists', () => {
      const mockUser = { id: 1, name: 'Test User', email: 'test@test.com' }
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockUser))

      const user = apiClient.getCurrentUser()

      expect(user).toEqual(mockUser)
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('user')
    })

    it('should return null when no user data exists', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      const user = apiClient.getCurrentUser()

      expect(user).toBeNull()
    })
  })

  describe('authenticated requests', () => {
    beforeEach(() => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
    })

    it('should include authorization header in authenticated requests', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })

      await apiClient.getTeacherProfile()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/teachers/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      )
    })

    it('should handle teacher dashboard request', async () => {
      const mockDashboard = {
        teacher: { id: 1, name: 'Test Teacher' },
        classroom_count: 3,
        student_count: 25,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockDashboard),
      })

      const result = await apiClient.getTeacherDashboard()

      expect(result).toEqual(mockDashboard)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/teachers/dashboard'),
        expect.objectContaining({
          method: undefined, // GET request
        })
      )
    })

    it('should handle teacher classrooms request', async () => {
      const mockClassrooms = [
        { id: 1, name: 'Class A', students: [] },
        { id: 2, name: 'Class B', students: [] },
      ]

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockClassrooms),
      })

      const result = await apiClient.getTeacherClassrooms()

      expect(result).toEqual(mockClassrooms)
    })

    it('should handle teacher programs request', async () => {
      const mockPrograms = [
        { id: 1, title: 'English 101', lessons: [] },
        { id: 2, title: 'English 102', lessons: [] },
      ]

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockPrograms),
      })

      const result = await apiClient.getTeacherPrograms()

      expect(result).toEqual(mockPrograms)
    })
  })

  describe('classroom CRUD operations', () => {
    beforeEach(() => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
    })

    it('should create classroom', async () => {
      const classroomData = {
        name: 'New Classroom',
        description: 'A new classroom',
        level: 'beginner',
      }

      const mockResponse = { id: 1, ...classroomData }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.createClassroom(classroomData)

      expect(result).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/teachers/classrooms'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(classroomData),
        })
      )
    })

    it('should update classroom', async () => {
      const classroomId = 1
      const updateData = { name: 'Updated Classroom' }

      const mockResponse = { id: classroomId, ...updateData }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.updateClassroom(classroomId, updateData)

      expect(result).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/teachers/classrooms/${classroomId}`),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      )
    })

    it('should delete classroom', async () => {
      const classroomId = 1

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      })

      await apiClient.deleteClassroom(classroomId)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/teachers/classrooms/${classroomId}`),
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })
  })

  describe('error handling', () => {
    it('should throw error with detail message when available', async () => {
      const errorDetail = 'Specific error message'
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: errorDetail }),
      })

      await expect(apiClient.getTeacherProfile()).rejects.toThrow(errorDetail)
    })

    it('should throw generic error when detail not available', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({}),
      })

      await expect(apiClient.getTeacherProfile()).rejects.toThrow('HTTP error! status: 500')
    })

    it('should handle JSON parsing errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.reject(new Error('Invalid JSON')),
      })

      await expect(apiClient.getTeacherProfile()).rejects.toThrow('HTTP error! status: 400')
    })
  })
})
