import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ClassroomDetail from '../ClassroomDetail'
import { apiClient } from '@/lib/api'
import { toast } from 'sonner'

// Mock dependencies
vi.mock('@/lib/api', () => ({
  apiClient: {
    getTeacherClassrooms: vi.fn(),
    getTeacherPrograms: vi.fn(),
    getTeacherDashboard: vi.fn(),
    createContent: vi.fn(),
    getProgramDetail: vi.fn(),
  }
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  }
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: '1' }),
    useNavigate: () => vi.fn(),
  }
})

const mockClassroom = {
  id: 1,
  name: 'Test Classroom',
  description: 'Test description',
  level: 'A1',
  student_count: 5,
  students: [],
  program_count: 1
}

const mockProgramsWithoutContent = [
  {
    id: 1,
    name: 'Test Program',
    description: 'Test program description',
    level: 'A1',
    estimated_hours: 20,
    order_index: 1,
    classroom_id: 1,
    lessons: [
      {
        id: 1,
        name: 'Unit 1: Greetings',
        description: 'Learn basic greetings',
        order_index: 1,
        estimated_minutes: 30,
        program_id: 1,
        contents: [] // No contents initially
      }
    ]
  }
]

const mockProgramsWithContent = [
  {
    id: 1,
    name: 'Test Program',
    description: 'Test program description',
    level: 'A1',
    estimated_hours: 20,
    order_index: 1,
    classroom_id: 1,
    lessons: [
      {
        id: 1,
        name: 'Unit 1: Greetings',
        description: 'Learn basic greetings',
        order_index: 1,
        estimated_minutes: 30,
        program_id: 1,
        contents: [
          {
            id: 1,
            type: 'reading_assessment',
            title: '朗讀錄音練習',
            items_count: 0,
            estimated_time: '5 分鐘'
          }
        ]
      }
    ]
  }
]

describe('Create Content', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(apiClient.getTeacherClassrooms as any).mockResolvedValue([mockClassroom])
    ;(apiClient.getTeacherDashboard as any).mockResolvedValue({
      teacher_name: 'Test Teacher',
      total_students: 10,
      total_classrooms: 2,
      total_programs: 3
    })
  })

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <ClassroomDetail />
      </BrowserRouter>
    )
  }

  it('should create content when selecting content type', async () => {
    // Start with no contents - mock both initial and refresh calls
    ;(apiClient.getTeacherPrograms as any)
      .mockResolvedValueOnce(mockProgramsWithoutContent) // Initial load
      .mockResolvedValueOnce(mockProgramsWithContent)    // After content creation

    ;(apiClient.getProgramDetail as any)
      .mockResolvedValueOnce(mockProgramsWithoutContent[0]) // Initial load
      .mockResolvedValueOnce(mockProgramsWithContent[0])    // After content creation

    // Mock successful content creation
    ;(apiClient.createContent as any).mockResolvedValue({
      id: 1,
      type: 'reading_assessment',
      title: '朗讀錄音練習',
      lesson_id: 1
    })

    renderComponent()

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Classroom')).toBeInTheDocument()
    })

    // Navigate to programs tab
    const programsTab = screen.getByText('課程內容')
    fireEvent.click(programsTab)

    // Wait for programs to load
    await waitFor(() => {
      expect(screen.getByText('Test Program')).toBeInTheDocument()
    })

    // Expand program
    const programAccordion = screen.getByText('Test Program')
    fireEvent.click(programAccordion)

    // Wait for lesson to be visible
    await waitFor(() => {
      expect(screen.getByText('Unit 1: Greetings')).toBeInTheDocument()
    })

    // Verify no content initially
    expect(screen.getByText('尚無內容，請新增內容')).toBeInTheDocument()

    // Click add content button
    const addContentButton = screen.getByRole('button', { name: /新增內容/i })
    fireEvent.click(addContentButton)

    // Wait for dialog
    await waitFor(() => {
      expect(screen.getByText('選擇內容類型')).toBeInTheDocument()
    })

    // Select reading assessment
    const readingCard = screen.getByTestId('content-type-card-reading_assessment')
    fireEvent.click(readingCard)

    // Verify API was called with empty items array
    await waitFor(() => {
      expect(apiClient.createContent).toHaveBeenCalledWith(1, {
        type: 'reading_assessment',
        title: '朗讀錄音練習',
        items: [],
        target_wpm: 60,
        target_accuracy: 0.8
      })
    })

    // Verify success toast
    expect(toast.success).toHaveBeenCalledWith('內容已創建成功')

    // Verify programs are refreshed and content is shown
    await waitFor(() => {
      expect(screen.getByText('朗讀錄音練習')).toBeInTheDocument()
      expect(screen.queryByText('尚無內容，請新增內容')).not.toBeInTheDocument()
    })
  })

  it('should handle content creation error', async () => {
    ;(apiClient.getTeacherPrograms as any).mockResolvedValue(mockProgramsWithoutContent)
    ;(apiClient.getProgramDetail as any).mockResolvedValue(mockProgramsWithoutContent[0])

    // Mock failed content creation
    ;(apiClient.createContent as any).mockRejectedValue(new Error('API Error'))

    renderComponent()

    // Navigate to add content
    await waitFor(() => {
      expect(screen.getByText('Test Classroom')).toBeInTheDocument()
    })

    const programsTab = screen.getByText('課程內容')
    fireEvent.click(programsTab)

    await waitFor(() => {
      expect(screen.getByText('Test Program')).toBeInTheDocument()
    })

    const programAccordion = screen.getByText('Test Program')
    fireEvent.click(programAccordion)

    await waitFor(() => {
      expect(screen.getByText('Unit 1: Greetings')).toBeInTheDocument()
    })

    const addContentButton = screen.getByRole('button', { name: /新增內容/i })
    fireEvent.click(addContentButton)

    await waitFor(() => {
      expect(screen.getByText('選擇內容類型')).toBeInTheDocument()
    })

    const readingCard = screen.getByTestId('content-type-card-reading_assessment')
    fireEvent.click(readingCard)

    // Verify error handling
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('創建內容失敗，請稍後再試')
    })

    // Content should still not be present
    expect(screen.getByText('尚無內容，請新增內容')).toBeInTheDocument()
  })

  it('should not allow creating content for disabled types', async () => {
    ;(apiClient.getTeacherPrograms as any).mockResolvedValue(mockProgramsWithoutContent)
    ;(apiClient.getProgramDetail as any).mockResolvedValue(mockProgramsWithoutContent[0])

    renderComponent()

    // Navigate to add content dialog
    await waitFor(() => {
      expect(screen.getByText('Test Classroom')).toBeInTheDocument()
    })

    const programsTab = screen.getByText('課程內容')
    fireEvent.click(programsTab)

    await waitFor(() => {
      expect(screen.getByText('Test Program')).toBeInTheDocument()
    })

    const programAccordion = screen.getByText('Test Program')
    fireEvent.click(programAccordion)

    await waitFor(() => {
      expect(screen.getByText('Unit 1: Greetings')).toBeInTheDocument()
    })

    const addContentButton = screen.getByRole('button', { name: /新增內容/i })
    fireEvent.click(addContentButton)

    await waitFor(() => {
      expect(screen.getByText('選擇內容類型')).toBeInTheDocument()
    })

    // Try to click disabled content type
    const disabledCard = screen.getByTestId('content-type-card-speaking_practice')
    fireEvent.click(disabledCard)

    // API should not be called
    expect(apiClient.createContent).not.toHaveBeenCalled()

    // Dialog should still be open
    expect(screen.getByText('選擇內容類型')).toBeInTheDocument()
  })
})
