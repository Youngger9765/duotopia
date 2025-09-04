import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import TeacherPrograms from '../TeacherPrograms'
import { apiClient } from '@/lib/api'
import { toast } from 'sonner'

// Mock the dependencies
vi.mock('@/lib/api', () => ({
  apiClient: {
    getTeacherPrograms: vi.fn(),
    getTeacherClassrooms: vi.fn(),
    getTeacherDashboard: vi.fn(),
    createProgram: vi.fn(),
    updateProgram: vi.fn(),
    deleteProgram: vi.fn(),
  }
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  }
}))

const mockPrograms = [
  {
    id: 1,
    name: '初級英語課程',
    description: '適合初學者的基礎課程',
    classroom_id: 1,
    classroom_name: '測試班級A',
    estimated_hours: 20,
    level: 'beginner',
    status: 'active',
    lesson_count: 10,
    student_count: 15,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
  {
    id: 2,
    name: '進階口說訓練',
    description: '提升口語表達能力',
    classroom_id: 2,
    classroom_name: '測試班級B',
    estimated_hours: 30,
    level: 'intermediate',
    status: 'draft',
    lesson_count: 5,
    student_count: 10,
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2024-01-20T00:00:00Z',
  }
]

const mockClassrooms = [
  { id: 1, name: '測試班級A' },
  { id: 2, name: '測試班級B' },
]

describe('TeacherPrograms', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(apiClient.getTeacherPrograms as any).mockResolvedValue(mockPrograms)
    ;(apiClient.getTeacherClassrooms as any).mockResolvedValue(mockClassrooms)
    ;(apiClient.getTeacherDashboard as any).mockResolvedValue({
      teacher: { name: 'Test Teacher', email: 'teacher@test.com', is_demo: false },
      classroom_count: 2,
      student_count: 25,
      program_count: 2,
      classrooms: [],
      recent_students: []
    })
  })

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <TeacherPrograms />
      </BrowserRouter>
    )
  }

  it('應該顯示載入狀態', async () => {
    renderComponent()
    expect(screen.getByText('載入中...')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByText('載入中...')).not.toBeInTheDocument()
    })
  })

  it('應該顯示課程列表', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('初級英語課程')).toBeInTheDocument()
      expect(screen.getByText('進階口說訓練')).toBeInTheDocument()
      expect(screen.getByText('適合初學者的基礎課程')).toBeInTheDocument()
    })
  })

  it('應該顯示統計卡片', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('總課程數')).toBeInTheDocument()
      // 檢查是否有數字 2 出現（總數）
      const totalCount = screen.getByText('總課程數').parentElement?.parentElement?.querySelector('.text-2xl')
      expect(totalCount?.textContent).toBe('2')
      // Use getAllByText since there might be multiple elements with '進行中'
      const activeElements = screen.getAllByText('進行中')
      expect(activeElements.length).toBeGreaterThan(0)
      // Use getAllByText since there might be multiple elements with '草稿'
      const draftElements = screen.getAllByText('草稿')
      expect(draftElements.length).toBeGreaterThan(0)
    })
  })

  describe('新增課程', () => {
    it('應該開啟新增課程對話框', async () => {
      renderComponent()

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /新增課程/i })
        fireEvent.click(addButton)
      })

      // Check that dialog is open with form fields
      expect(screen.getByLabelText('課程名稱')).toBeInTheDocument()
      expect(screen.getByLabelText('課程描述')).toBeInTheDocument()
      expect(screen.getByLabelText('所屬班級')).toBeInTheDocument()
      expect(screen.getByLabelText('課程等級')).toBeInTheDocument()
    })

    it('應該成功新增課程', async () => {
      const newProgram = {
        id: 3,
        name: '新課程',
        description: '新課程描述',
        classroom_id: 1,
        classroom_name: '測試班級A',
        level: 'beginner',
        estimated_hours: 10,
      }

      ;(apiClient.createProgram as any).mockResolvedValue(newProgram)

      renderComponent()

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /新增課程/i })
        fireEvent.click(addButton)
      })

      // 填寫表單
      fireEvent.change(screen.getByLabelText('課程名稱'), {
        target: { value: '新課程' }
      })
      fireEvent.change(screen.getByLabelText('課程描述'), {
        target: { value: '新課程描述' }
      })
      fireEvent.change(screen.getByLabelText('所屬班級'), {
        target: { value: '1' }
      })

      // 提交
      const submitButton = screen.getByRole('button', { name: /確定新增/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(apiClient.createProgram).toHaveBeenCalledWith({
          name: '新課程',
          description: '新課程描述',
          classroom_id: 1,
          level: 'beginner',
          estimated_hours: 10,
        })
        expect(toast.success).toHaveBeenCalledWith('課程「新課程」已成功新增')
      })
    })

    it('應該驗證必填欄位', async () => {
      renderComponent()

      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /新增課程/i })
        fireEvent.click(addButton)
      })

      // Wait for dialog to be fully open
      await waitFor(() => {
        expect(screen.getByLabelText('課程名稱')).toBeInTheDocument()
      })

      // 不填寫直接提交
      const submitButton = screen.getByRole('button', { name: /確定新增/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('課程名稱為必填')).toBeInTheDocument()
        // Check for error message specifically, not the option text
        const errorMessages = screen.getAllByText('請選擇班級')
        // Should have at least 2 instances: one in option, one as error
        expect(errorMessages.length).toBeGreaterThanOrEqual(2)
      })
    })
  })

  describe('編輯課程', () => {
    it('應該開啟編輯對話框並顯示現有資料', async () => {
      renderComponent()

      await waitFor(() => {
        const editButtons = screen.getAllByTitle('編輯')
        fireEvent.click(editButtons[0])
      })

      expect(screen.getByText('編輯課程')).toBeInTheDocument()
      expect(screen.getByDisplayValue('初級英語課程')).toBeInTheDocument()
      expect(screen.getByDisplayValue('適合初學者的基礎課程')).toBeInTheDocument()
    })

    it('應該成功更新課程', async () => {
      ;(apiClient.updateProgram as any).mockResolvedValue({
        ...mockPrograms[0],
        name: '更新後的課程名稱'
      })

      renderComponent()

      await waitFor(() => {
        const editButtons = screen.getAllByTitle('編輯')
        fireEvent.click(editButtons[0])
      })

      // 修改名稱
      const nameInput = screen.getByLabelText('課程名稱')
      fireEvent.change(nameInput, { target: { value: '更新後的課程名稱' } })

      // 提交
      const submitButton = screen.getByRole('button', { name: /儲存變更/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(apiClient.updateProgram).toHaveBeenCalledWith(1, expect.objectContaining({
          name: '更新後的課程名稱'
        }))
        expect(toast.success).toHaveBeenCalledWith('課程「更新後的課程名稱」已更新')
      })
    })
  })

  describe('刪除課程', () => {
    it('應該顯示刪除確認對話框', async () => {
      renderComponent()

      await waitFor(() => {
        const deleteButtons = screen.getAllByTitle('刪除')
        fireEvent.click(deleteButtons[0])
      })

      expect(screen.getByText('確認刪除課程')).toBeInTheDocument()
      expect(screen.getByText(/確定要刪除課程「初級英語課程」嗎/)).toBeInTheDocument()
    })

    it('應該成功刪除課程', async () => {
      ;(apiClient.deleteProgram as any).mockResolvedValue({})

      renderComponent()

      await waitFor(() => {
        const deleteButtons = screen.getAllByTitle('刪除')
        fireEvent.click(deleteButtons[0])
      })

      // 確認刪除
      const confirmButton = screen.getByRole('button', { name: /確認刪除/i })
      fireEvent.click(confirmButton)

      await waitFor(() => {
        expect(apiClient.deleteProgram).toHaveBeenCalledWith(1)
        expect(toast.success).toHaveBeenCalledWith('課程「初級英語課程」已刪除')
      })
    })

    it('應該可以取消刪除', async () => {
      renderComponent()

      await waitFor(() => {
        const deleteButtons = screen.getAllByTitle('刪除')
        fireEvent.click(deleteButtons[0])
      })

      // 取消刪除
      const cancelButton = screen.getByRole('button', { name: /取消/i })
      fireEvent.click(cancelButton)

      await waitFor(() => {
        expect(apiClient.deleteProgram).not.toHaveBeenCalled()
        expect(screen.queryByText('確認刪除課程')).not.toBeInTheDocument()
      })
    })
  })

  describe('查看課程詳情', () => {
    it('應該開啟詳情對話框', async () => {
      renderComponent()

      await waitFor(() => {
        const viewButtons = screen.getAllByTitle('查看')
        fireEvent.click(viewButtons[0])
      })

      expect(screen.getByText('課程詳情')).toBeInTheDocument()
      // 檢查課程名稱是否在對話框中
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveTextContent('初級英語課程')
      expect(dialog).toHaveTextContent('測試班級A')
      expect(dialog).toHaveTextContent('20 小時')
      expect(dialog).toHaveTextContent('10 個課程單元')
      expect(dialog).toHaveTextContent('15 位學生')
    })
  })

  describe('篩選功能', () => {
    it('應該按班級篩選課程', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('初級英語課程')).toBeInTheDocument()
      })

      const filterSelect = screen.getByRole('combobox')
      fireEvent.change(filterSelect, { target: { value: '1' } })

      await waitFor(() => {
        expect(screen.getByText('初級英語課程')).toBeInTheDocument()
        expect(screen.queryByText('進階口說訓練')).not.toBeInTheDocument()
      })
    })

    it('應該顯示所有班級的課程', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('初級英語課程')).toBeInTheDocument()
        expect(screen.getByText('進階口說訓練')).toBeInTheDocument()
      })

      const filterSelect = screen.getByRole('combobox')
      fireEvent.change(filterSelect, { target: { value: '' } })

      await waitFor(() => {
        expect(screen.getByText('初級英語課程')).toBeInTheDocument()
        expect(screen.getByText('進階口說訓練')).toBeInTheDocument()
      })
    })
  })

  describe('重新載入', () => {
    it('應該重新獲取資料', async () => {
      renderComponent()

      await waitFor(() => {
        expect(apiClient.getTeacherPrograms).toHaveBeenCalledTimes(1)
      })

      const refreshButton = screen.getByRole('button', { name: /重新載入/i })
      fireEvent.click(refreshButton)

      await waitFor(() => {
        expect(apiClient.getTeacherPrograms).toHaveBeenCalledTimes(2)
        expect(apiClient.getTeacherClassrooms).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('空狀態', () => {
    it('應該顯示空狀態訊息', async () => {
      ;(apiClient.getTeacherPrograms as any).mockResolvedValue([])

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('尚未建立課程')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /建立第一個課程/i })).toBeInTheDocument()
      })
    })
  })
})
