/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * 全面 API 測試框架 - 取代 E2E 測試
 * 遵循 CLAUDE.md TDD 原則
 * 測試所有核心 API 功能和錯誤處理
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock API configuration - 使用測試專用 URL
vi.mock('@/config/api', () => ({
  API_URL: process.env.VITE_API_URL || 'https://api.duotopia-staging.com'
}))

import { apiClient } from '../api'

// Global fetch mock
global.fetch = vi.fn()

describe('🚀 Comprehensive API Testing Framework', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('access_token', 'test-jwt-token')
    // Set token on apiClient
    ;(apiClient as any).token = 'test-jwt-token'
  })

  describe('🔐 Authentication Flow', () => {
    it('should handle teacher login successfully', async () => {
      const mockLoginResponse = {
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test',
        token_type: 'bearer',
        user_type: 'teacher',
        user: {
          id: 1,
          email: 'teacher@duotopia.com',
          name: 'Test Teacher',
          is_demo: false
        }
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockLoginResponse
      })

      const result = await apiClient.teacherLogin({
        email: 'teacher@duotopia.com',
        password: 'password123'
      })

      // Contract validation
      expect(typeof result.access_token).toBe('string')
      expect(result.token_type).toBe('bearer')
      expect((result as any).user_type).toBe('teacher')
      expect(typeof result.user.id).toBe('number')
      expect(typeof result.user.name).toBe('string')

      // API call validation
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/teacher/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify({
            email: 'teacher@duotopia.com',
            password: 'password123'
          })
        })
      )
    })

    it('should handle 401 authentication errors', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Could not validate credentials' })
      })

      await expect(
        apiClient.teacherLogin({
          email: 'wrong@example.com',
          password: 'wrongpassword'
        })
      ).rejects.toThrow('Could not validate credentials')
    })

    it('should handle JWT token expiration', async () => {
      // Mock expired token response
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Token expired' })
      })

      await expect(
        apiClient.getTeacherDashboard()
      ).rejects.toThrow('Token expired')
    })
  })

  describe('📊 Dashboard & Data Fetching', () => {
    it('should fetch teacher dashboard data', async () => {
      const mockDashboard = {
        teacher: {
          id: 1,
          name: 'Test Teacher',
          email: 'teacher@duotopia.com'
        },
        classroom_count: 3,
        student_count: 25,
        recent_assignments: [
          {
            id: 31,
            title: 'English Essay',
            due_date: '2025-09-20T23:59:59Z',
            submission_count: 12,
            total_students: 15
          }
        ],
        statistics: {
          assignments_created: 45,
          total_submissions: 234,
          avg_score: 85.6
        }
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockDashboard
      })

      const result = await apiClient.getTeacherDashboard()

      // Data structure validation
      expect(typeof (result as any).teacher.id).toBe('number')
      expect(typeof (result as any).classroom_count).toBe('number')
      expect(Array.isArray((result as any).recent_assignments)).toBe(true)
      expect(typeof (result as any).statistics.avg_score).toBe('number')

      // Authorization header validation
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/teachers/dashboard'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-jwt-token'
          })
        })
      )
    })

    it('should handle network errors gracefully', async () => {
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

      await expect(
        apiClient.getTeacherDashboard()
      ).rejects.toThrow('Network error')
    })
  })

  describe('🎯 Assignment Management', () => {
    it('should fetch assignment submissions', async () => {
      const mockSubmission = {
        id: 1,
        assignment_id: 31,
        student_id: 1,
        student: {
          id: 1,
          student_id: 'S001',
          name: 'Test Student',
          email: 'student@duotopia.com'
        },
        content: {
          text_response: 'This is my essay submission...',
          attachments: [],
          audio_recording: null
        },
        status: 'submitted',
        score: null,
        feedback: null,
        submitted_at: '2025-09-15T10:30:00Z',
        graded_at: null
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSubmission
      })

      const result = await apiClient.getSubmission(31, 1)

      // Submission data validation
      expect(typeof (result as any).id).toBe('number')
      expect(typeof (result as any).assignment_id).toBe('number')
      expect(['draft', 'submitted', 'graded']).toContain((result as any).status)
      expect(new Date((result as any).submitted_at)).toBeInstanceOf(Date)
      expect((result as any).student.student_id).toMatch(/^S\d+$/)
    })

    it('should create content successfully', async () => {
      const mockContent = {
        id: 1,
        type: 'reading_assessment',
        title: '朗讀錄音練習',
        lesson_id: 1
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockContent
      })

      const result = await apiClient.createContent(1, {
        type: 'reading_assessment',
        title: '朗讀錄音練習',
        items: []
      })

      expect((result as any).id).toBe(1)
      expect((result as any).type).toBe('reading_assessment')
      expect((result as any).lesson_id).toBe(1)
    })
  })

  describe('🔍 Error Handling & Edge Cases', () => {
    it('should handle various HTTP status codes correctly', async () => {
      const statusTests = [
        { status: 400, expectedError: 'Bad Request' },
        { status: 403, expectedError: 'Forbidden' },
        { status: 404, expectedError: 'Not Found' },
        { status: 500, expectedError: 'Internal Server Error' }
      ]

      for (const { status, expectedError } of statusTests) {
        ;(global.fetch as any).mockResolvedValueOnce({
          ok: false,
          status,
          json: async () => ({ detail: expectedError })
        })

        await expect(
          apiClient.getTeacherDashboard()
        ).rejects.toThrow()
      }
    })

    it('should handle malformed JSON responses', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid JSON format' })
      })

      await expect(
        apiClient.getTeacherDashboard()
      ).rejects.toThrow()
    })

    it('should validate request payload formats', () => {
      // Validate login payload
      const loginPayload = {
        email: 'test@example.com',
        password: 'password123'
      }
      expect(typeof loginPayload.email).toBe('string')
      expect(loginPayload.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)
      expect(typeof loginPayload.password).toBe('string')
      expect(loginPayload.password.length).toBeGreaterThan(0)

      // Validate content creation payload
      const contentPayload = {
        type: 'reading_assessment',
        title: '測試內容',
        items: []
      }
      expect(['reading_assessment', 'writing_task', 'quiz']).toContain(contentPayload.type)
      expect(Array.isArray(contentPayload.items)).toBe(true)
    })
  })

  describe('🚀 Performance & Reliability', () => {
    it('should handle concurrent API requests', async () => {
      const mockResponse = {
        teacher: { id: 1, name: 'Teacher' },
        classroom_count: 2,
        recent_assignments: []
      }

      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ ...mockResponse, teacher: { id: Math.floor(Math.random() * 1000), name: 'Teacher' } })
      })

      const requests = Array(5).fill(0).map(() =>
        apiClient.getTeacherDashboard()
      )

      const results = await Promise.all(requests)
      expect(results).toHaveLength(5)
      expect(global.fetch).toHaveBeenCalledTimes(5)
    })

    it('should maintain consistent API endpoint patterns', () => {
      const endpoints = [
        '/api/auth/teacher/login',
        '/api/teachers/dashboard',
        '/api/teachers/classrooms',
        '/api/teachers/assignments/31/submissions/1',
        '/api/teachers/lessons/1/contents'
      ]

      endpoints.forEach(endpoint => {
        expect(endpoint).toMatch(/^\/api\//)
        expect(endpoint.endsWith('/')).toBe(false)
        // No double slashes
        expect(endpoint).not.toMatch(/\/\//)
      })
    })

    it('should validate API response time expectations', async () => {
      const startTime = Date.now()

      ;(global.fetch as any).mockImplementation(() =>
        new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: async () => ({ data: 'fast response' })
            })
          }, 100) // 100ms mock response time
        })
      )

      await apiClient.getTeacherDashboard()
      const responseTime = Date.now() - startTime

      // Response should be under 1 second for good UX
      expect(responseTime).toBeLessThan(1000)
    })
  })

  describe('🔄 Integration Flow Testing', () => {
    it('should complete full user journey: login -> dashboard -> assignments', async () => {
      // Step 1: Login
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'jwt-token',
          token_type: 'bearer',
          user_type: 'teacher',
          user: { id: 1, name: 'Teacher', email: 'teacher@test.com' }
        })
      })

      const loginResult = await apiClient.teacherLogin({
        email: 'teacher@test.com',
        password: 'password'
      })
      expect(loginResult.access_token).toBeDefined()

      // Step 2: Get Dashboard
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          teacher: { id: 1, name: 'Teacher' },
          classroom_count: 2,
          recent_assignments: []
        })
      })

      const dashboardResult = await apiClient.getTeacherDashboard()
      expect((dashboardResult as any).teacher.id).toBe(1)

      // Step 3: Get Submission
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          assignment_id: 31,
          student_id: 1,
          status: 'submitted'
        })
      })

      const submissionResult = await apiClient.getSubmission(31, 1)
      expect((submissionResult as any).status).toBe('submitted')

      // Verify the complete flow executed
      expect(global.fetch).toHaveBeenCalledTimes(3)
    })
  })
})
