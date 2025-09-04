/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import TeacherLogin from '../TeacherLogin'
import { apiClient } from '@/lib/api'

// Mock the API client
vi.mock('@/lib/api', () => ({
  apiClient: {
    teacherLogin: vi.fn(),
  },
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

describe('TeacherLogin', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset localStorage
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders teacher login form correctly', () => {
    render(<TeacherLogin />)

    // Check main elements
    expect(screen.getByText('Duotopia')).toBeInTheDocument()
    expect(screen.getByText('AI 驅動的英語學習平台')).toBeInTheDocument()
    expect(screen.getByText('教師登入')).toBeInTheDocument()
    expect(screen.getByText('使用您的 Email 帳號登入教師後台')).toBeInTheDocument()

    // Check form fields
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('密碼')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '登入' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Demo 教師快速登入' })).toBeInTheDocument()

    // Check navigation links
    expect(screen.getByRole('link', { name: '立即註冊' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '學生登入入口' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '返回首頁' })).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    render(<TeacherLogin />)

    const submitButton = screen.getByRole('button', { name: '登入' })
    fireEvent.click(submitButton)

    // Form should have required validation
    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('密碼')

    expect(emailInput).toBeRequired()
    expect(passwordInput).toBeRequired()
  })

  it('handles successful login', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: 1,
        email: 'test@test.com',
        name: 'Test Teacher',
        is_demo: false,
      },
    }

    vi.mocked(apiClient.teacherLogin).mockResolvedValue(mockResponse)

    render(<TeacherLogin />)

    // Fill in form
    await user.type(screen.getByLabelText('Email'), 'test@test.com')
    await user.type(screen.getByLabelText('密碼'), 'password123')

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: '登入' }))

    // Wait for API call and navigation
    await waitFor(() => {
      expect(apiClient.teacherLogin).toHaveBeenCalledWith({
        email: 'test@test.com',
        password: 'password123',
      })
      expect(mockNavigate).toHaveBeenCalledWith('/teacher/dashboard')
    })
  })

  it('handles login error', async () => {
    const user = userEvent.setup()
    const errorMessage = '登入失敗，帳號或密碼錯誤'

    vi.mocked(apiClient.teacherLogin).mockRejectedValue(new Error(errorMessage))

    render(<TeacherLogin />)

    // Fill in form
    await user.type(screen.getByLabelText('Email'), 'wrong@test.com')
    await user.type(screen.getByLabelText('密碼'), 'wrongpassword')

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: '登入' }))

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('shows loading state during login', async () => {
    const user = userEvent.setup()

    // Create a promise that we can control
    let resolveLogin: (value: any) => void
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve
    })

    vi.mocked(apiClient.teacherLogin).mockReturnValue(loginPromise)

    render(<TeacherLogin />)

    // Fill in form
    await user.type(screen.getByLabelText('Email'), 'test@test.com')
    await user.type(screen.getByLabelText('密碼'), 'password123')

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: '登入' }))

    // Check loading state
    await waitFor(() => {
      expect(screen.getByText('登入中...')).toBeInTheDocument()
    })

    // Form fields should be disabled
    expect(screen.getByLabelText('Email')).toBeDisabled()
    expect(screen.getByLabelText('密碼')).toBeDisabled()

    // Resolve the promise to finish the test
    resolveLogin!({
      access_token: 'test-token',
      token_type: 'bearer',
      user: { id: 1, email: 'test@test.com', name: 'Test Teacher', is_demo: false },
    })
  })

  it('handles demo login', async () => {
    const mockResponse = {
      access_token: 'demo-token',
      token_type: 'bearer',
      user: {
        id: 1,
        email: 'demo@duotopia.com',
        name: 'Demo Teacher',
        is_demo: true,
      },
    }

    vi.mocked(apiClient.teacherLogin).mockResolvedValue(mockResponse)

    render(<TeacherLogin />)

    // Click demo login button
    fireEvent.click(screen.getByRole('button', { name: 'Demo 教師快速登入' }))

    // Wait for API call and navigation
    await waitFor(() => {
      expect(apiClient.teacherLogin).toHaveBeenCalledWith({
        email: 'demo@duotopia.com',
        password: 'demo123',
      })
      expect(mockNavigate).toHaveBeenCalledWith('/teacher/dashboard')
    })
  })

  it('handles demo login error', async () => {
    vi.mocked(apiClient.teacherLogin).mockRejectedValue(new Error('Demo login failed'))

    render(<TeacherLogin />)

    // Click demo login button
    fireEvent.click(screen.getByRole('button', { name: 'Demo 教師快速登入' }))

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('Demo 帳號登入失敗')).toBeInTheDocument()
    })

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('updates form state correctly', async () => {
    const user = userEvent.setup()
    render(<TeacherLogin />)

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement
    const passwordInput = screen.getByLabelText('密碼') as HTMLInputElement

    // Type in email
    await user.type(emailInput, 'test@example.com')
    expect(emailInput.value).toBe('test@example.com')

    // Type in password
    await user.type(passwordInput, 'mypassword')
    expect(passwordInput.value).toBe('mypassword')
  })

  it('submits form on Enter key press', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: { id: 1, email: 'test@test.com', name: 'Test Teacher', is_demo: false },
    }

    vi.mocked(apiClient.teacherLogin).mockResolvedValue(mockResponse)

    render(<TeacherLogin />)

    // Fill form and press Enter on password field
    await user.type(screen.getByLabelText('Email'), 'test@test.com')
    await user.type(screen.getByLabelText('密碼'), 'password123{enter}')

    await waitFor(() => {
      expect(apiClient.teacherLogin).toHaveBeenCalled()
    })
  })

  it('disables buttons during loading', async () => {
    const user = userEvent.setup()

    // Create a promise that we can control
    let resolveLogin: (value: any) => void
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve
    })

    vi.mocked(apiClient.teacherLogin).mockReturnValue(loginPromise)

    render(<TeacherLogin />)

    // Fill in form
    await user.type(screen.getByLabelText('Email'), 'test@test.com')
    await user.type(screen.getByLabelText('密碼'), 'password123')

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: '登入' }))

    // Both buttons should be disabled during loading
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '登入中...' })).toBeDisabled()
      expect(screen.getByRole('button', { name: 'Demo 教師快速登入' })).toBeDisabled()
    })

    // Resolve the promise
    resolveLogin!({
      access_token: 'test-token',
      token_type: 'bearer',
      user: { id: 1, email: 'test@test.com', name: 'Test Teacher', is_demo: false },
    })
  })

  it('displays demo credentials hint', () => {
    render(<TeacherLogin />)

    expect(screen.getByText('Demo 帳號：demo@duotopia.com / demo123')).toBeInTheDocument()
  })
})
