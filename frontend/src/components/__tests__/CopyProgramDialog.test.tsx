import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CopyProgramDialog from '../CopyProgramDialog'
import { apiClient } from '@/lib/api'
import { toast } from 'sonner'

// Mock dependencies
vi.mock('@/lib/api', () => ({
  apiClient: {
    getTeacherPrograms: vi.fn(),
    copyProgramToClassroom: vi.fn(),
  }
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  }
}))

const mockTeacherPrograms = [
  {
    id: 1,
    name: 'Basic English Course',
    description: 'Foundation course for beginners',
    level: 'beginner',
    estimated_hours: 20,
    lesson_count: 10,
  },
  {
    id: 2,
    name: 'Advanced Speaking',
    description: 'Improve oral communication skills',
    level: 'intermediate',
    estimated_hours: 30,
    lesson_count: 15,
  },
  {
    id: 3,
    name: 'Business English',
    description: 'Professional communication',
    level: 'advanced',
    estimated_hours: 40,
    lesson_count: 20,
  }
]

describe('CopyProgramDialog', () => {
  const mockOnClose = vi.fn()
  const mockOnSuccess = vi.fn()
  const classroomId = 1

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.getTeacherPrograms).mockResolvedValue(mockTeacherPrograms)
  })

  const renderComponent = (open = true) => {
    return render(
      <CopyProgramDialog
        open={open}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
        classroomId={classroomId}
      />
    )
  }

  it('should display dialog title and description', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('從課程庫複製')).toBeInTheDocument()
      expect(screen.getByText('選擇要複製到此班級的課程')).toBeInTheDocument()
    })
  })

  it('should load and display teacher programs', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Basic English Course')).toBeInTheDocument()
      expect(screen.getByText('Advanced Speaking')).toBeInTheDocument()
      expect(screen.getByText('Business English')).toBeInTheDocument()
    })
  })

  it('should display program details', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Basic English Course')).toBeInTheDocument()
      expect(screen.getByText('Foundation course for beginners')).toBeInTheDocument()
      expect(screen.getByText('10 個課程單元')).toBeInTheDocument()
      expect(screen.getByText('20 小時')).toBeInTheDocument()
    })
  })

  it('should show loading state while fetching programs', () => {
    renderComponent()

    expect(screen.getByText('載入課程中...')).toBeInTheDocument()
  })

  it('should allow selecting multiple programs', async () => {
    renderComponent()

    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes).toHaveLength(3)

      // Select first two programs
      fireEvent.click(checkboxes[0])
      fireEvent.click(checkboxes[1])

      expect(checkboxes[0]).toBeChecked()
      expect(checkboxes[1]).toBeChecked()
      expect(checkboxes[2]).not.toBeChecked()
    })
  })

  it('should display selected count', async () => {
    renderComponent()

    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox')

      fireEvent.click(checkboxes[0])
      fireEvent.click(checkboxes[1])

      expect(screen.getByText('已選擇 2 個課程')).toBeInTheDocument()
    })
  })

  it('should enable copy button only when programs are selected', async () => {
    renderComponent()

    await waitFor(() => {
      const copyButton = screen.getByRole('button', { name: /複製到班級/i })
      expect(copyButton).toBeDisabled()

      const checkbox = screen.getAllByRole('checkbox')[0]
      fireEvent.click(checkbox)

      expect(copyButton).not.toBeDisabled()
    })
  })

  it('should copy selected programs on submit', async () => {
    vi.mocked(apiClient.copyProgramToClassroom).mockResolvedValue({ success: true })

    renderComponent()

    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox')
      fireEvent.click(checkboxes[0])
      fireEvent.click(checkboxes[1])

      const copyButton = screen.getByRole('button', { name: /複製到班級/i })
      fireEvent.click(copyButton)
    })

    await waitFor(() => {
      expect(apiClient.copyProgramToClassroom).toHaveBeenCalledWith(classroomId, [1, 2])
      expect(toast.success).toHaveBeenCalledWith('成功複製 2 個課程到班級')
      expect(mockOnSuccess).toHaveBeenCalled()
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  it('should handle copy error', async () => {
    vi.mocked(apiClient.copyProgramToClassroom).mockRejectedValue(new Error('Copy failed'))

    renderComponent()

    await waitFor(() => {
      const checkbox = screen.getAllByRole('checkbox')[0]
      fireEvent.click(checkbox)

      const copyButton = screen.getByRole('button', { name: /複製到班級/i })
      fireEvent.click(copyButton)
    })

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('複製失敗，請稍後再試')
      expect(mockOnSuccess).not.toHaveBeenCalled()
    })
  })

  it('should close dialog on cancel', async () => {
    renderComponent()

    await waitFor(() => {
      const cancelButton = screen.getByRole('button', { name: /取消/i })
      fireEvent.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  it('should filter programs by search term', async () => {
    renderComponent()

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('搜尋課程名稱...')
      fireEvent.change(searchInput, { target: { value: 'Advanced' } })

      expect(screen.getByText('Advanced Speaking')).toBeInTheDocument()
      expect(screen.queryByText('Basic English Course')).not.toBeInTheDocument()
      expect(screen.queryByText('Business English')).not.toBeInTheDocument()
    })
  })

  it('should show empty state when no programs available', async () => {
    vi.mocked(apiClient.getTeacherPrograms).mockResolvedValue([])

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('目前沒有可複製的課程')).toBeInTheDocument()
      expect(screen.getByText('請先到「所有課程」頁面建立課程')).toBeInTheDocument()
    })
  })

  it('should show level badge with correct color', async () => {
    renderComponent()

    await waitFor(() => {
      const beginnerBadge = screen.getByText('beginner')
      const intermediateBadge = screen.getByText('intermediate')
      const advancedBadge = screen.getByText('advanced')

      expect(beginnerBadge).toHaveClass('bg-green-100')
      expect(intermediateBadge).toHaveClass('bg-blue-100')
      expect(advancedBadge).toHaveClass('bg-purple-100')
    })
  })

  it('should disable already copied programs', async () => {
    const programsWithStatus = mockTeacherPrograms.map((p, i) => ({
      ...p,
      already_in_classroom: i === 0 // First program is already in classroom
    }))
    vi.mocked(apiClient.getTeacherPrograms).mockResolvedValue(programsWithStatus)

    renderComponent()

    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes[0]).toBeDisabled()
      expect(checkboxes[1]).not.toBeDisabled()
      expect(checkboxes[2]).not.toBeDisabled()

      expect(screen.getByText('(已存在)')).toBeInTheDocument()
    })
  })
})
