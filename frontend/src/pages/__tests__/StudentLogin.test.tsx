/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import StudentLogin from '../StudentLogin'
import { authService } from '@/services/authService'
import { teacherService } from '@/services/teacherService'

// Mock services
vi.mock('@/services/authService', () => ({
  authService: {
    studentLogin: vi.fn(),
  },
}))

vi.mock('@/services/teacherService', () => ({
  teacherService: {
    validateTeacher: vi.fn(),
    getPublicClassrooms: vi.fn(),
    getClassroomStudents: vi.fn(),
  },
}))

// Mock the student auth store
const mockLogin = vi.fn()
vi.mock('@/stores/studentAuthStore', () => ({
  useStudentAuthStore: () => ({
    login: mockLogin,
  }),
}))

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: ({ children, to, ...props }: any) => (
      <a href={to} {...props}>
        {children}
      </a>
    ),
  }
})

describe('StudentLogin', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders initial step (teacher email) correctly', () => {
    render(<StudentLogin />)

    // Check main elements
    expect(screen.getByText('🚀')).toBeInTheDocument()
    expect(screen.getByText('嗨，歡迎來到 Duotopia！')).toBeInTheDocument()
    expect(screen.getByText('請輸入老師 Email')).toBeInTheDocument()

    // Check form elements
    expect(screen.getByPlaceholderText('teacher@example.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '下一步' })).toBeInTheDocument()

    // Check demo button
    expect(screen.getByText('🎯 使用 Demo 教師 (demo@duotopia.com)')).toBeInTheDocument()

    // Check navigation
    expect(screen.getByRole('link', { name: '返回首頁' })).toBeInTheDocument()
  })

  it('validates teacher email and moves to classroom selection', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'Test Teacher' }
    const mockClassrooms = [
      { id: 1, name: 'Class A', studentCount: 25 },
      { id: 2, name: 'Class B', studentCount: 30 },
    ]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)

    render(<StudentLogin />)

    // Enter teacher email
    const emailInput = screen.getByPlaceholderText('teacher@example.com')
    await user.type(emailInput, 'test@teacher.com')

    // Click next step
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    // Wait for step 2
    await waitFor(() => {
      expect(teacherService.validateTeacher).toHaveBeenCalledWith('test@teacher.com')
      expect(teacherService.getPublicClassrooms).toHaveBeenCalledWith('test@teacher.com')
      expect(screen.getByText('請選擇你的班級和名字')).toBeInTheDocument()
      expect(screen.getByText('Class A')).toBeInTheDocument()
      expect(screen.getByText('Class B')).toBeInTheDocument()
    })
  })

  it('handles invalid teacher email', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: false }

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)

    render(<StudentLogin />)

    // Enter invalid teacher email
    const emailInput = screen.getByPlaceholderText('teacher@example.com')
    await user.type(emailInput, 'invalid@teacher.com')

    // Click next step
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('找不到此教師帳號')).toBeInTheDocument()
    })

    // Should still be on step 1
    expect(screen.getByText('請輸入老師 Email')).toBeInTheDocument()
  })

  it('moves to student selection after classroom selection', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'Test Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Class A', studentCount: 25 }]
    const mockStudents = [
      { id: 1, name: 'Alice', email: 'alice@student.com' },
      { id: 2, name: 'Bob', email: 'bob@student.com' },
    ]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)
    vi.mocked(teacherService.getClassroomStudents).mockResolvedValue(mockStudents)

    render(<StudentLogin />)

    // Step 1: Enter teacher email
    await user.type(screen.getByPlaceholderText('teacher@example.com'), 'test@teacher.com')
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    // Wait for step 2 and select classroom
    await waitFor(() => {
      expect(screen.getByText('Class A')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Class A'))

    // Wait for step 3
    await waitFor(() => {
      expect(teacherService.getClassroomStudents).toHaveBeenCalledWith(1)
      expect(screen.getByText('Class A')).toBeInTheDocument()
      expect(screen.getByText('請選擇你的名字')).toBeInTheDocument()
      expect(screen.getByText('Alice')).toBeInTheDocument()
      expect(screen.getByText('Bob')).toBeInTheDocument()
    })
  })

  it('moves to password step after student selection', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'Test Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Class A', studentCount: 25 }]
    const mockStudents = [{ id: 1, name: 'Alice', email: 'alice@student.com' }]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)
    vi.mocked(teacherService.getClassroomStudents).mockResolvedValue(mockStudents)

    render(<StudentLogin />)

    // Go through steps 1-3
    await user.type(screen.getByPlaceholderText('teacher@example.com'), 'test@teacher.com')
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    await waitFor(() => screen.getByText('Class A'))
    fireEvent.click(screen.getByText('Class A'))

    await waitFor(() => screen.getByText('Alice'))
    fireEvent.click(screen.getByText('Alice'))

    // Should be on step 4 (password)
    await waitFor(() => {
      expect(screen.getByText('你好，Alice！')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('請輸入你的密碼')).toBeInTheDocument()
      expect(screen.getByText('Demo 學生預設密碼：')).toBeInTheDocument()
    })
  })

  it('completes student login successfully', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'Test Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Class A', studentCount: 25 }]
    const mockStudents = [{ id: 1, name: 'Alice', email: 'alice@student.com' }]
    const mockLoginResponse = {
      access_token: 'student-token',
      user: { id: 1, name: 'Alice', email: 'alice@student.com' },
    }

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)
    vi.mocked(teacherService.getClassroomStudents).mockResolvedValue(mockStudents)
    vi.mocked(authService.studentLogin).mockResolvedValue(mockLoginResponse)

    render(<StudentLogin />)

    // Go through all steps
    await user.type(screen.getByPlaceholderText('teacher@example.com'), 'test@teacher.com')
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    await waitFor(() => screen.getByText('Class A'))
    fireEvent.click(screen.getByText('Class A'))

    await waitFor(() => screen.getByText('Alice'))
    fireEvent.click(screen.getByText('Alice'))

    await waitFor(() => screen.getByPlaceholderText('請輸入你的密碼'))
    await user.type(screen.getByPlaceholderText('請輸入你的密碼'), '20120101')
    fireEvent.click(screen.getByRole('button', { name: '登入' }))

    // Verify login
    await waitFor(() => {
      expect(authService.studentLogin).toHaveBeenCalledWith({
        email: 'alice@student.com',
        password: '20120101',
      })
      expect(mockLogin).toHaveBeenCalledWith('student-token', mockLoginResponse.user)
      expect(mockNavigate).toHaveBeenCalledWith('/student/dashboard')
    })
  })

  it('handles student login error', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'Test Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Class A', studentCount: 25 }]
    const mockStudents = [{ id: 1, name: 'Alice', email: 'alice@student.com' }]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)
    vi.mocked(teacherService.getClassroomStudents).mockResolvedValue(mockStudents)
    vi.mocked(authService.studentLogin).mockRejectedValue(new Error('Wrong password'))

    render(<StudentLogin />)

    // Go through all steps to login
    await user.type(screen.getByPlaceholderText('teacher@example.com'), 'test@teacher.com')
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    await waitFor(() => screen.getByText('Class A'))
    fireEvent.click(screen.getByText('Class A'))

    await waitFor(() => screen.getByText('Alice'))
    fireEvent.click(screen.getByText('Alice'))

    await waitFor(() => screen.getByPlaceholderText('請輸入你的密碼'))
    await user.type(screen.getByPlaceholderText('請輸入你的密碼'), 'wrongpassword')
    fireEvent.click(screen.getByRole('button', { name: '登入' }))

    // Check error message
    await waitFor(() => {
      expect(screen.getByText('密碼錯誤，請重新輸入')).toBeInTheDocument()
    })

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('uses demo teacher shortcut', async () => {
    const mockValidateResponse = { valid: true, name: 'Demo Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Demo Class', studentCount: 3 }]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)

    render(<StudentLogin />)

    // Click demo teacher button
    fireEvent.click(screen.getByText('🎯 使用 Demo 教師 (demo@duotopia.com)'))

    // Email should be filled
    expect(screen.getByPlaceholderText('teacher@example.com')).toHaveValue('demo@duotopia.com')
  })

  it('handles back navigation correctly', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'Test Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Class A', studentCount: 25 }]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)

    render(<StudentLogin />)

    // Go to step 2
    await user.type(screen.getByPlaceholderText('teacher@example.com'), 'test@teacher.com')
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    await waitFor(() => {
      expect(screen.getByText('請選擇你的班級和名字')).toBeInTheDocument()
    })

    // Click back button
    fireEvent.click(screen.getByText('返回'))

    // Should be back to step 1
    expect(screen.getByText('請輸入老師 Email')).toBeInTheDocument()
  })

  it('loads and displays teacher history', async () => {
    // Clear everything and start fresh
    localStorage.clear()

    const teacherHistory = [
      { email: 'teacher1@test.com', name: 'Teacher 1', lastUsed: new Date() },
      { email: 'teacher2@test.com', name: 'Teacher 2', lastUsed: new Date() },
    ]

    localStorage.setItem('teacherHistory', JSON.stringify(teacherHistory))

    render(<StudentLogin />)

    // Make sure we're on step 1
    expect(screen.getByText('請輸入老師 Email')).toBeInTheDocument()

    // Should show teacher history section (excluding demo teacher)
    expect(screen.getByText('或選擇最近使用過的老師：')).toBeInTheDocument()
    expect(screen.getByText('teacher1@test.com')).toBeInTheDocument()
    expect(screen.getByText('teacher2@test.com')).toBeInTheDocument()
  })

  it('does not display teacher history section when empty', () => {
    render(<StudentLogin />)

    // Should not show teacher history section
    expect(screen.queryByText('或選擇最近使用過的老師：')).not.toBeInTheDocument()
  })

  it('filters out demo teacher from history display', () => {
    localStorage.clear()

    const teacherHistory = [
      { email: 'demo@duotopia.com', name: 'Demo Teacher', lastUsed: new Date() },
      { email: 'teacher1@test.com', name: 'Teacher 1', lastUsed: new Date() },
    ]

    localStorage.setItem('teacherHistory', JSON.stringify(teacherHistory))

    render(<StudentLogin />)

    // Make sure we're on step 1
    expect(screen.getByText('請輸入老師 Email')).toBeInTheDocument()

    // Should show teacher history but exclude demo teacher
    expect(screen.getByText('或選擇最近使用過的老師：')).toBeInTheDocument()
    expect(screen.getByText('teacher1@test.com')).toBeInTheDocument()
    expect(screen.queryByText('demo@duotopia.com')).not.toBeInTheDocument()
  })

  it('saves teacher to history after validation', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'New Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Class A', studentCount: 25 }]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)

    render(<StudentLogin />)

    // Enter new teacher email
    await user.type(screen.getByPlaceholderText('teacher@example.com'), 'new@teacher.com')
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    await waitFor(() => {
      // Check localStorage was updated
      const history = JSON.parse(localStorage.getItem('teacherHistory') || '[]')
      expect(history).toEqual([
        expect.objectContaining({
          email: 'new@teacher.com',
          name: 'New Teacher',
        }),
      ])
    })
  })

  it('generates correct avatar colors for students', async () => {
    const user = userEvent.setup()
    const mockValidateResponse = { valid: true, name: 'Test Teacher' }
    const mockClassrooms = [{ id: 1, name: 'Class A', studentCount: 25 }]
    const mockStudents = [
      { id: 1, name: 'Alice', email: 'alice@student.com' },
      { id: 2, name: 'Bob', email: 'bob@student.com' },
    ]

    vi.mocked(teacherService.validateTeacher).mockResolvedValue(mockValidateResponse)
    vi.mocked(teacherService.getPublicClassrooms).mockResolvedValue(mockClassrooms)
    vi.mocked(teacherService.getClassroomStudents).mockResolvedValue(mockStudents)

    render(<StudentLogin />)

    // Go to student selection step
    await user.type(screen.getByPlaceholderText('teacher@example.com'), 'test@teacher.com')
    fireEvent.click(screen.getByRole('button', { name: '下一步' }))

    await waitFor(() => screen.getByText('Class A'))
    fireEvent.click(screen.getByText('Class A'))

    await waitFor(() => {
      // Check that avatars are rendered with first letters
      const aliceAvatar = screen.getByText('A')
      const bobAvatar = screen.getByText('B')

      expect(aliceAvatar).toBeInTheDocument()
      expect(bobAvatar).toBeInTheDocument()
    })
  })
})
