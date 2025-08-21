/**
 * useStudents Hook 單元測試
 * 測試學生管理相關的自訂 Hook
 */
import React from 'react';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useStudents } from '../useStudents';
import { studentsApi } from '@/api/students';
import type { Student } from '@/types';

// Mock API
vi.mock('@/api/students');

// Mock toast
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

// 測試資料
const mockStudents: Student[] = [
  {
    id: 1,
    name: '張小明',
    email: 'xiaoming@test.com',
    birth_date: '2010-01-01',
    teacher_id: 1,
    password_status: 'default',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: '李小華',
    email: null,
    birth_date: '2010-02-15',
    teacher_id: 1,
    password_status: 'custom',
    created_at: '2024-01-02T00:00:00Z',
  },
];

// Helper function to create wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useStudents Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('查詢學生列表', () => {
    it('應該成功載入學生列表', async () => {
      (studentsApi.getStudents as vi.Mock).mockResolvedValueOnce(mockStudents);

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      // 初始狀態
      expect(result.current.isLoading).toBe(true);
      expect(result.current.students).toBeUndefined();

      // 等待資料載入
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.students).toEqual(mockStudents);
      expect(studentsApi.getStudents).toHaveBeenCalledTimes(1);
    });

    it('應該處理載入錯誤', async () => {
      const error = new Error('Failed to fetch students');
      (studentsApi.getStudents as vi.Mock).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
      expect(result.current.students).toBeUndefined();
    });
  });

  describe('新增學生', () => {
    it('應該成功新增學生', async () => {
      const newStudent = {
        name: '王小美',
        birth_date: '2010-03-20',
        email: 'xiaomei@test.com',
      };

      const createdStudent = { id: 3, ...newStudent, teacher_id: 1 };

      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);
      (studentsApi.createStudent as vi.Mock).mockResolvedValueOnce(createdStudent);

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.createStudent(newStudent);
      });

      expect(studentsApi.createStudent).toHaveBeenCalledWith(newStudent);
      expect(mockToast).toHaveBeenCalledWith({
        title: '新增成功',
        description: expect.stringContaining('學生 王小美 已新增'),
      });
    });

    it('應該處理新增失敗', async () => {
      const newStudent = {
        name: '王小美',
        birth_date: '2010-03-20',
      };

      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);
      (studentsApi.createStudent as vi.Mock).mockRejectedValueOnce(
        new Error('Failed to create student')
      );

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        try {
          await result.current.createStudent(newStudent);
        } catch (error) {
          // Expected error
        }
      });

      expect(mockToast).toHaveBeenCalledWith({
        title: '新增失敗',
        description: '無法新增學生，請稍後再試',
        variant: 'destructive',
      });
    });
  });

  describe('更新學生', () => {
    it('應該成功更新學生資料', async () => {
      const updatedData = {
        id: 1,
        name: '張小明（更新）',
        email: 'new_xiaoming@test.com',
      };

      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);
      (studentsApi.updateStudent as vi.Mock).mockResolvedValueOnce({
        ...mockStudents[0],
        ...updatedData,
      });

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.updateStudent(1, updatedData);
      });

      expect(studentsApi.updateStudent).toHaveBeenCalledWith(1, updatedData);
      expect(mockToast).toHaveBeenCalledWith({
        title: '更新成功',
        description: '學生資料已更新',
      });
    });
  });

  describe('刪除學生', () => {
    it('應該成功刪除學生', async () => {
      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);
      (studentsApi.deleteStudent as vi.Mock).mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.deleteStudent(1);
      });

      expect(studentsApi.deleteStudent).toHaveBeenCalledWith(1);
      expect(mockToast).toHaveBeenCalledWith({
        title: '刪除成功',
        description: '學生已刪除',
      });
    });
  });

  describe('重置密碼', () => {
    it('應該成功重置學生密碼', async () => {
      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);
      (studentsApi.resetPassword as vi.Mock).mockResolvedValueOnce({
        message: '密碼已重置',
        default_password: '20100101',
      });

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.resetPassword(1);
      });

      expect(studentsApi.resetPassword).toHaveBeenCalledWith(1);
      expect(mockToast).toHaveBeenCalledWith({
        title: '密碼重置成功',
        description: '密碼已重置為生日：20100101',
      });
    });
  });

  describe('批量操作', () => {
    it('應該成功批量分配學生到班級', async () => {
      const studentIds = [1, 2];
      const classId = 5;

      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);
      (studentsApi.bulkAssignToClass as vi.Mock).mockResolvedValueOnce({
        success: true,
        assigned_count: 2,
      });

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.bulkAssignToClass(studentIds, classId);
      });

      expect(studentsApi.bulkAssignToClass).toHaveBeenCalledWith(studentIds, classId);
      expect(mockToast).toHaveBeenCalledWith({
        title: '分配成功',
        description: '已將 2 位學生分配到班級',
      });
    });

    it('應該處理批量操作失敗', async () => {
      const studentIds = [1, 2, 3];
      const classId = 5;

      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);
      (studentsApi.bulkAssignToClass as vi.Mock).mockRejectedValueOnce(
        new Error('Class is full')
      );

      const { result } = renderHook(() => useStudents(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        try {
          await result.current.bulkAssignToClass(studentIds, classId);
        } catch (error) {
          // Expected error
        }
      });

      expect(mockToast).toHaveBeenCalledWith({
        title: '分配失敗',
        description: '班級已滿或發生錯誤',
        variant: 'destructive',
      });
    });
  });

  describe('搜尋和篩選', () => {
    it('應該根據關鍵字篩選學生', () => {
      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);

      const { result } = renderHook(() => useStudents({ search: '小明' }), {
        wrapper: createWrapper(),
      });

      waitFor(() => {
        expect(result.current.filteredStudents).toHaveLength(1);
        expect(result.current.filteredStudents[0].name).toBe('張小明');
      });
    });

    it('應該根據班級篩選學生', () => {
      const studentsWithClass = [
        { ...mockStudents[0], class_id: 1 },
        { ...mockStudents[1], class_id: 2 },
      ];

      (studentsApi.getStudents as vi.Mock).mockResolvedValue(studentsWithClass);

      const { result } = renderHook(() => useStudents({ classId: 1 }), {
        wrapper: createWrapper(),
      });

      waitFor(() => {
        expect(result.current.filteredStudents).toHaveLength(1);
        expect(result.current.filteredStudents[0].class_id).toBe(1);
      });
    });

    it('應該根據密碼狀態篩選學生', () => {
      (studentsApi.getStudents as vi.Mock).mockResolvedValue(mockStudents);

      const { result } = renderHook(
        () => useStudents({ passwordStatus: 'custom' }),
        {
          wrapper: createWrapper(),
        }
      );

      waitFor(() => {
        expect(result.current.filteredStudents).toHaveLength(1);
        expect(result.current.filteredStudents[0].name).toBe('李小華');
      });
    });
  });

  describe('分頁功能', () => {
    it('應該正確處理分頁', () => {
      const manyStudents = Array.from({ length: 25 }, (_, i) => ({
        id: i + 1,
        name: `學生${i + 1}`,
        birth_date: '2010-01-01',
        teacher_id: 1,
      }));

      (studentsApi.getStudents as vi.Mock).mockResolvedValue(manyStudents);

      const { result } = renderHook(
        () => useStudents({ page: 1, pageSize: 10 }),
        {
          wrapper: createWrapper(),
        }
      );

      waitFor(() => {
        expect(result.current.paginatedStudents).toHaveLength(10);
        expect(result.current.totalPages).toBe(3);
        expect(result.current.currentPage).toBe(1);
      });
    });
  });
});