import { vi } from 'vitest'

// Mock API responses
export const mockApiResponses = {
  successfulLogin: {
    access_token: 'mock-token',
    token_type: 'bearer',
    user: {
      id: 1,
      email: 'test@test.com',
      name: 'Test User',
      is_active: true,
    },
  },
  teacherDashboard: {
    classrooms: [
      {
        id: 1,
        name: 'Test Classroom',
        description: 'A test classroom',
        teacher_id: 1,
        students: [],
      },
    ],
    recent_activities: [],
  },
  studentDashboard: {
    assignments: [
      {
        id: 1,
        title: 'Test Assignment',
        description: 'A test assignment',
        due_date: '2024-12-31T23:59:59',
        status: 'pending',
      },
    ],
    progress: {
      completed: 5,
      total: 10,
      percentage: 50,
    },
  },
}

// Mock fetch implementation
export const createMockFetch = (mockResponse: any, status: number = 200) => {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(mockResponse),
    text: () => Promise.resolve(JSON.stringify(mockResponse)),
  })
}

// Mock localStorage
export const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

// Mock router functions
export const mockNavigate = vi.fn()
export const mockUseLocation = vi.fn(() => ({ pathname: '/' }))
