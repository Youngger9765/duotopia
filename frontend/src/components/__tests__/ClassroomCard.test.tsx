/**
 * ClassroomCard 元件單元測試
 * 測試班級卡片的顯示和互動功能
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ClassroomCard } from '../ClassroomCard';
import type { Class } from '@/types';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// 測試資料
const mockClassroom: Class = {
  id: 1,
  name: '測試班級A',
  grade: '國小三年級',
  capacity: 30,
  teacher_id: 1,
  description: '這是一個測試班級',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('ClassroomCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('班級資訊顯示', () => {
    it('應該顯示班級名稱和年級', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      expect(screen.getByText('測試班級A')).toBeInTheDocument();
      expect(screen.getByText('國小三年級')).toBeInTheDocument();
    });

    it('應該顯示班級描述', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      expect(screen.getByText('這是一個測試班級')).toBeInTheDocument();
    });

    it('應該在沒有描述時顯示預設文字', () => {
      const classroomWithoutDesc = { ...mockClassroom, description: undefined };
      
      renderWithRouter(
        <ClassroomCard
          classroom={classroomWithoutDesc}
          studentCount={0}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      expect(screen.getByText('暫無描述')).toBeInTheDocument();
    });
  });

  describe('學生人數顯示', () => {
    it('應該顯示學生人數和容量', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={15}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      expect(screen.getByText('15/30')).toBeInTheDocument();
      expect(screen.getByText('學生人數')).toBeInTheDocument();
    });

    it('應該在班級滿員時顯示不同樣式', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={30}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      const badge = screen.getByText('30/30');
      expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('應該在班級未滿時顯示正常樣式', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={15}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      const badge = screen.getByText('15/30');
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });
  });

  describe('操作按鈕', () => {
    it('應該顯示查看詳情按鈕', async () => {
      const user = userEvent.setup();

      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      const detailButton = screen.getByText('查看詳情');
      await user.click(detailButton);

      expect(mockNavigate).toHaveBeenCalledWith('/classroom/1');
    });

    it('應該顯示編輯按鈕並觸發 onEdit', async () => {
      const user = userEvent.setup();
      const mockOnEdit = vi.fn();

      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={mockOnEdit}
          onDelete={vi.fn()}
        />
      );

      const editButton = screen.getByLabelText('編輯班級');
      await user.click(editButton);

      expect(mockOnEdit).toHaveBeenCalledWith(mockClassroom);
    });

    it('應該顯示刪除按鈕並觸發 onDelete', async () => {
      const user = userEvent.setup();
      const mockOnDelete = vi.fn();

      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={vi.fn()}
          onDelete={mockOnDelete}
        />
      );

      const deleteButton = screen.getByLabelText('刪除班級');
      await user.click(deleteButton);

      expect(mockOnDelete).toHaveBeenCalledWith(mockClassroom);
    });

    it('應該在有學生時禁用刪除按鈕', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={5}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      const deleteButton = screen.getByLabelText('刪除班級');
      expect(deleteButton).toBeDisabled();
    });

    it('應該在有學生時顯示提示訊息', async () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={5}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      const deleteButton = screen.getByLabelText('刪除班級');
      
      // 檢查按鈕有正確的 title 屬性
      expect(deleteButton).toHaveAttribute('title', '請先移除所有學生');
    });
  });

  describe('響應式設計', () => {
    it('應該在小螢幕時適當顯示', () => {
      // 設置小螢幕尺寸
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));

      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      // 檢查卡片是否仍然正確渲染
      expect(screen.getByText('測試班級A')).toBeInTheDocument();
      expect(screen.getByText('查看詳情')).toBeInTheDocument();
    });
  });

  describe('載入狀態', () => {
    it('應該在載入時顯示骨架屏', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
          isLoading={true}
        />
      );

      // 應該顯示載入動畫
      expect(screen.getByTestId('classroom-card-skeleton')).toBeInTheDocument();
    });
  });

  describe('無障礙功能', () => {
    it('應該有適當的 ARIA 標籤', () => {
      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={15}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );

      // 檢查按鈕的無障礙標籤
      expect(screen.getByLabelText('編輯班級')).toBeInTheDocument();
      expect(screen.getByLabelText('刪除班級')).toBeInTheDocument();
      
      // 檢查卡片存在（不使用 role，因為 Card 組件渲染為 div）
      const card = screen.getByText('測試班級A').closest('.bg-white');
      expect(card).toBeInTheDocument();
    });

    it('應該支援鍵盤導航', async () => {
      const user = userEvent.setup();
      const mockOnEdit = vi.fn();

      renderWithRouter(
        <ClassroomCard
          classroom={mockClassroom}
          studentCount={0}
          onEdit={mockOnEdit}
          onDelete={vi.fn()}
        />
      );

      // Tab 到編輯按鈕
      await user.tab();
      await user.tab(); // 可能需要多次 tab
      
      // Enter 觸發編輯
      await user.keyboard('{Enter}');
      
      expect(mockOnEdit).toHaveBeenCalled();
    });
  });
});