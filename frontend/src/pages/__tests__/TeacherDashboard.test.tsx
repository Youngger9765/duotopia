import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/test-utils'
import TeacherDashboard from '../TeacherDashboard'
import { apiClient } from '@/lib/api'

// Mock the API client
vi.mock('@/lib/api', () => ({
  apiClient: {
    getTeacherDashboard: vi.fn(),
    logout: vi.fn(),
  },
}))

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const mockDashboardData = {
  teacher: {
    id: 1,
    email: 'teacher@test.com',
    name: 'Test Teacher',
    phone: '1234567890',
    is_demo: false,
    is_active: true,
  },
  classroom_count: 3,
  student_count: 45,
  program_count: 12,
  classrooms: [
    {
      id: 1,
      name: '六年級甲班',
      description: '六年級英語班',
      student_count: 25,
    },
    {
      id: 2,
      name: '五年級乙班',
      description: '五年級英語班',
      student_count: 20,
    },
  ],
  recent_students: [
    {
      id: 1,
      name: 'Alice',
      email: 'alice@student.com',
      classroom_name: '六年級甲班',
    },
    {
      id: 2,
      name: 'Bob',
      email: 'bob@student.com',
      classroom_name: '五年級乙班',
    },
  ],
}

const mockDemoDashboardData = {
  ...mockDashboardData,
  teacher: {
    ...mockDashboardData.teacher,
    email: 'demo@duotopia.com',
    name: 'Demo Teacher',
    is_demo: true,
  },
}

describe('TeacherDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockImplementation(
      () => new Promise(() => {}) // Never resolves to keep loading
    )

    render(<TeacherDashboard />)

    expect(screen.getByText('載入中...')).toBeInTheDocument()
    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument() // Loading spinner
  })

  it('renders dashboard with data successfully', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText('載入中...')).not.toBeInTheDocument()
    })

    // Check header
    expect(screen.getByText('Duotopia')).toBeInTheDocument()
    expect(screen.getByText('教師後台')).toBeInTheDocument()
    expect(screen.getByText('Test Teacher')).toBeInTheDocument()
    expect(screen.getByText('teacher@test.com')).toBeInTheDocument()

    // Check welcome message
    expect(screen.getByText('歡迎回來，Test Teacher！')).toBeInTheDocument()
    expect(screen.getByText('管理您的班級、課程與學生學習進度')).toBeInTheDocument()

    // Check stats cards
    expect(screen.getByText('班級數量')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument() // classroom_count
    expect(screen.getByText('學生總數')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument() // student_count
    expect(screen.getByText('課程計畫')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument() // program_count
  })

  it('displays demo account badge for demo users', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDemoDashboardData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText('Demo 帳號')).toBeInTheDocument()
    })
  })

  it('renders classrooms correctly', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      // Check classrooms section
      expect(screen.getByText('我的班級')).toBeInTheDocument()
      expect(screen.getByText('目前管理的班級列表')).toBeInTheDocument()

      // Check individual classrooms
      expect(screen.getByText('六年級甲班')).toBeInTheDocument()
      expect(screen.getByText('六年級英語班')).toBeInTheDocument()
      expect(screen.getByText('25 位學生')).toBeInTheDocument()

      expect(screen.getByText('五年級乙班')).toBeInTheDocument()
      expect(screen.getByText('五年級英語班')).toBeInTheDocument()
      expect(screen.getByText('20 位學生')).toBeInTheDocument()
    })
  })

  it('renders recent students correctly', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      // Check recent students section
      expect(screen.getByText('最近活動學生')).toBeInTheDocument()
      expect(screen.getByText('各班級的學生列表')).toBeInTheDocument()

      // Check individual students
      expect(screen.getByText('Alice')).toBeInTheDocument()
      expect(screen.getByText('Bob')).toBeInTheDocument()

      // Check avatar initials
      expect(screen.getByText('A')).toBeInTheDocument()
      expect(screen.getByText('B')).toBeInTheDocument()
    })
  })

  it('shows empty state when no classrooms exist', async () => {
    const emptyData = {
      ...mockDashboardData,
      classrooms: [],
    }
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(emptyData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText('尚未建立班級')).toBeInTheDocument()
    })
  })

  it('shows empty state when no students exist', async () => {
    const emptyData = {
      ...mockDashboardData,
      recent_students: [],
    }
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(emptyData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText('尚無學生資料')).toBeInTheDocument()
    })
  })

  it('renders quick actions section', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText('快速動作')).toBeInTheDocument()
      expect(screen.getByText('常用功能快捷入口')).toBeInTheDocument()

      // Check action buttons
      expect(screen.getByText('建立課程')).toBeInTheDocument()
      expect(screen.getByText('管理學生')).toBeInTheDocument()
      expect(screen.getByText('查看統計')).toBeInTheDocument()
    })
  })

  it('handles logout correctly', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText('登出')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('登出'))

    expect(apiClient.logout).toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/teacher/login')
  })

  it('handles API errors and shows error message', async () => {
    const errorMessage = '載入儀表板失敗，請重新登入'
    vi.mocked(apiClient.getTeacherDashboard).mockRejectedValue(new Error('API Error'))

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
      expect(screen.getByText('返回登入')).toBeInTheDocument()
    })
  })

  it('handles 401 unauthorized error by redirecting to login', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockRejectedValue(new Error('401 Unauthorized'))

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(apiClient.logout).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/teacher/login')
    })
  })

  it('navigates to login when clicking return login button', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockRejectedValue(new Error('API Error'))

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText('返回登入')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('返回登入'))

    expect(mockNavigate).toHaveBeenCalledWith('/teacher/login')
  })

  it('calls getTeacherDashboard on mount', () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    expect(apiClient.getTeacherDashboard).toHaveBeenCalledTimes(1)
  })

  it('shows classroom and student management buttons', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      // Classroom management buttons
      expect(screen.getAllByText('管理')).toHaveLength(2) // One for each classroom
      expect(screen.getByText('建立新班級')).toBeInTheDocument()

      // Student management buttons
      expect(screen.getByText('查看所有學生')).toBeInTheDocument()
    })
  })

  it('displays correct student count for each classroom', async () => {
    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboardData)

    render(<TeacherDashboard />)

    await waitFor(() => {
      expect(screen.getByText('25 位學生')).toBeInTheDocument()
      expect(screen.getByText('20 位學生')).toBeInTheDocument()
    })
  })
})
