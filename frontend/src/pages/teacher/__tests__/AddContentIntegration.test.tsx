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
    createLesson: vi.fn(),
    updateLesson: vi.fn(),
    deleteLesson: vi.fn(),
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

const mockPrograms = [
  {
    id: 1,
    name: 'Test Program',
    description: 'Test program description',
    level: 'A1',
    estimated_hours: 20,
    order_index: 1,
    lessons: [
      {
        id: 1,
        name: 'Unit 1: Greetings',
        description: 'Learn basic greetings',
        order_index: 1,
        estimated_minutes: 30,
        program_id: 1,
        contents: []
      }
    ]
  }
]

describe('Add Content Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(apiClient.getTeacherClassrooms as any).mockResolvedValue([mockClassroom])
    ;(apiClient.getTeacherPrograms as any).mockResolvedValue(mockPrograms)
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

  it('should open content type dialog when clicking add content button', async () => {
    renderComponent()
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Test Classroom')).toBeInTheDocument()
    })
    
    // Switch to programs tab
    const programsTab = screen.getByText('課程內容')
    fireEvent.click(programsTab)
    
    // Wait for programs to load
    await waitFor(() => {
      expect(screen.getByText('Test Program')).toBeInTheDocument()
    })
    
    // Expand the program accordion
    const programAccordion = screen.getByText('Test Program')
    fireEvent.click(programAccordion)
    
    // Wait for lessons to be visible
    await waitFor(() => {
      expect(screen.getByText('Unit 1: Greetings')).toBeInTheDocument()
    })
    
    // Click add content button
    const addContentButton = screen.getByRole('button', { name: /新增內容/i })
    fireEvent.click(addContentButton)
    
    // Verify content type dialog opens
    await waitFor(() => {
      expect(screen.getByText('選擇內容類型')).toBeInTheDocument()
      expect(screen.getByText(/為 「Unit 1: Greetings」 選擇要新增的內容類型/)).toBeInTheDocument()
    })
  })

  it('should display all content types in the dialog', async () => {
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
    
    // Verify all content types are displayed
    await waitFor(() => {
      expect(screen.getByText('朗讀錄音')).toBeInTheDocument()
      expect(screen.getByText('口說練習')).toBeInTheDocument()
      expect(screen.getByText('情境對話')).toBeInTheDocument()
      expect(screen.getByText('聽力填空')).toBeInTheDocument()
      expect(screen.getByText('造句練習')).toBeInTheDocument()
      expect(screen.getByText('口說測驗')).toBeInTheDocument()
      
      // Check that only reading is enabled
      expect(screen.getAllByText('即將推出')).toHaveLength(5)
    })
  })

  it('should show success toast when selecting content type', async () => {
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
    
    // Select a content type
    await waitFor(() => {
      expect(screen.getByText('朗讀評測')).toBeInTheDocument()
    })
    
    const readingAssessmentCard = screen.getByTestId('content-type-card-reading_assessment')
    fireEvent.click(readingAssessmentCard)
    
    // Verify success toast
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('開始建立 reading_assessment 內容')
    })
  })

  it('should close dialog after selecting content type', async () => {
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
    
    // Select a content type
    await waitFor(() => {
      expect(screen.getByText('口說練習')).toBeInTheDocument()
    })
    
    const speakingPracticeCard = screen.getByTestId('content-type-card-speaking_practice')
    fireEvent.click(speakingPracticeCard)
    
    // Verify dialog closes
    await waitFor(() => {
      expect(screen.queryByText('選擇內容類型')).not.toBeInTheDocument()
    })
  })

  it('should allow canceling content type selection', async () => {
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
    
    // Click cancel button
    await waitFor(() => {
      expect(screen.getByText('選擇內容類型')).toBeInTheDocument()
    })
    
    const cancelButton = screen.getByRole('button', { name: /取消/i })
    fireEvent.click(cancelButton)
    
    // Verify dialog closes without showing toast
    await waitFor(() => {
      expect(screen.queryByText('選擇內容類型')).not.toBeInTheDocument()
      expect(toast.success).not.toHaveBeenCalled()
    })
  })
})