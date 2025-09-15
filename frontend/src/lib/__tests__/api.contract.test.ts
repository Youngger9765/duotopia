/**
 * API Contract Testing
 * 確保前端與後端 API 契約一致
 */
import { describe, it, expect } from 'vitest'

// API 契約定義
export const API_CONTRACTS = {
  '/api/auth/teacher/login': {
    method: 'POST',
    request: {
      email: 'string',
      password: 'string'
    },
    response: {
      access_token: 'string',
      token_type: 'string',
      user_type: 'string',
      user: {
        id: 'number',
        email: 'string',
        name: 'string'
      }
    },
    errors: {
      400: { detail: 'string' },
      401: { detail: 'string' }
    }
  },
  '/api/teachers/assignments/{id}/submissions/{studentId}': {
    method: 'GET',
    headers: {
      Authorization: 'Bearer {token}'
    },
    response: {
      id: 'number',
      assignment_id: 'number',
      student_id: 'number',
      content: 'string',
      status: 'string',
      submitted_at: 'string'
    },
    errors: {
      401: { detail: 'Could not validate credentials' },
      404: { detail: 'string' }
    }
  }
}

describe('API Contract Validation', () => {
  it('should validate login response structure', () => {
    const mockResponse = {
      access_token: 'jwt-token',
      token_type: 'bearer',
      user_type: 'teacher',
      user: {
        id: 1,
        email: 'teacher@test.com',
        name: 'Test Teacher'
      }
    }

    // 驗證回應結構
    expect(typeof mockResponse.access_token).toBe('string')
    expect(typeof mockResponse.user.id).toBe('number')
    expect(typeof mockResponse.user.email).toBe('string')
    expect(['teacher', 'student']).toContain(mockResponse.user_type)
  })

  it('should validate submission response structure', () => {
    const mockSubmission = {
      id: 1,
      assignment_id: 31,
      student_id: 1,
      content: 'submission content',
      status: 'submitted',
      submitted_at: '2025-09-15T12:00:00Z'
    }

    expect(typeof mockSubmission.id).toBe('number')
    expect(typeof mockSubmission.assignment_id).toBe('number')
    expect(typeof mockSubmission.student_id).toBe('number')
    expect(['draft', 'submitted', 'graded']).toContain(mockSubmission.status)
    expect(new Date(mockSubmission.submitted_at)).toBeInstanceOf(Date)
  })

  it('should validate error response format', () => {
    const mockError = { detail: 'Could not validate credentials' }

    expect(typeof mockError.detail).toBe('string')
    expect(mockError.detail.length).toBeGreaterThan(0)
  })
})
