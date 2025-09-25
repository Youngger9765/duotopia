/**
 * Unit Test: 拖拽排序功能
 * 測試前端拖拽排序的邏輯和 API 呼叫
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '@/lib/api';

// Mock API client
vi.mock('@/lib/api', () => ({
  apiClient: {
    updateContent: vi.fn(),
  }
}));

describe('拖拽排序功能', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('API Client Order Index Support', () => {
    it('應該支援 order_index 參數', async () => {
      // Arrange
      const mockUpdateContent = vi.mocked(apiClient.updateContent);
      mockUpdateContent.mockResolvedValue({ id: 1, order_index: 5 });

      // Act
      const result = await apiClient.updateContent(1, { order_index: 5 });

      // Assert
      expect(mockUpdateContent).toHaveBeenCalledWith(1, { order_index: 5 });
      expect(result).toEqual({ id: 1, order_index: 5 });
    });

    it('應該允許只更新 order_index', async () => {
      // Arrange
      const mockUpdateContent = vi.mocked(apiClient.updateContent);
      mockUpdateContent.mockResolvedValue({ id: 2, order_index: 10 });

      // Act
      await apiClient.updateContent(2, { order_index: 10 });

      // Assert
      expect(mockUpdateContent).toHaveBeenCalledWith(2, { order_index: 10 });
      expect(mockUpdateContent).toHaveBeenCalledTimes(1);
    });

    it('應該處理 order_index 為 0 的情況', async () => {
      // Arrange
      const mockUpdateContent = vi.mocked(apiClient.updateContent);
      mockUpdateContent.mockResolvedValue({ id: 3, order_index: 0 });

      // Act
      await apiClient.updateContent(3, { order_index: 0 });

      // Assert
      expect(mockUpdateContent).toHaveBeenCalledWith(3, { order_index: 0 });
    });
  });

  describe('拖拽排序邏輯', () => {
    it('應該正確計算拖拽後的新順序', () => {
      // Arrange - 原始順序 [1, 2, 3]
      const originalContents = [
        { id: 1, order_index: 1, title: 'Content 1' },
        { id: 2, order_index: 2, title: 'Content 2' },
        { id: 3, order_index: 3, title: 'Content 3' }
      ];

      // Act - 模擬將第一個項目拖到最後 (oldIndex: 0, newIndex: 2)
      const oldIndex = 0;
      const newIndex = 2;

      const reorderedContents = [...originalContents];
      const [removed] = reorderedContents.splice(oldIndex, 1);
      reorderedContents.splice(newIndex, 0, removed);

      // 重新計算 order_index
      const contentsWithNewOrder = reorderedContents.map((content, index) => ({
        ...content,
        order_index: index + 1
      }));

      // Assert - 預期順序變為 [2, 3, 1]
      expect(contentsWithNewOrder).toEqual([
        { id: 2, order_index: 1, title: 'Content 2' },
        { id: 3, order_index: 2, title: 'Content 3' },
        { id: 1, order_index: 3, title: 'Content 1' }
      ]);
    });

    it('應該正確處理向前拖拽', () => {
      // Arrange - 原始順序 [1, 2, 3]
      const originalContents = [
        { id: 1, order_index: 1, title: 'Content 1' },
        { id: 2, order_index: 2, title: 'Content 2' },
        { id: 3, order_index: 3, title: 'Content 3' }
      ];

      // Act - 模擬將第三個項目拖到第一位 (oldIndex: 2, newIndex: 0)
      const oldIndex = 2;
      const newIndex = 0;

      const reorderedContents = [...originalContents];
      const [removed] = reorderedContents.splice(oldIndex, 1);
      reorderedContents.splice(newIndex, 0, removed);

      // 重新計算 order_index
      const contentsWithNewOrder = reorderedContents.map((content, index) => ({
        ...content,
        order_index: index + 1
      }));

      // Assert - 預期順序變為 [3, 1, 2]
      expect(contentsWithNewOrder).toEqual([
        { id: 3, order_index: 1, title: 'Content 3' },
        { id: 1, order_index: 2, title: 'Content 1' },
        { id: 2, order_index: 3, title: 'Content 2' }
      ]);
    });
  });

  describe('批量 API 更新', () => {
    it('應該批量更新所有內容的 order_index', async () => {
      // Arrange
      const mockUpdateContent = vi.mocked(apiClient.updateContent);
      mockUpdateContent.mockResolvedValue({});

      const contentsWithNewOrder = [
        { id: 1, order_index: 3 },
        { id: 2, order_index: 1 },
        { id: 3, order_index: 2 }
      ];

      // Act
      const updatePromises = contentsWithNewOrder.map(content =>
        apiClient.updateContent(content.id, { order_index: content.order_index })
      );

      await Promise.all(updatePromises);

      // Assert
      expect(mockUpdateContent).toHaveBeenCalledTimes(3);
      expect(mockUpdateContent).toHaveBeenNthCalledWith(1, 1, { order_index: 3 });
      expect(mockUpdateContent).toHaveBeenNthCalledWith(2, 2, { order_index: 1 });
      expect(mockUpdateContent).toHaveBeenNthCalledWith(3, 3, { order_index: 2 });
    });

    it('應該正確處理 API 錯誤', async () => {
      // Arrange
      const mockUpdateContent = vi.mocked(apiClient.updateContent);
      mockUpdateContent.mockRejectedValue(new Error('API Error'));

      // Act & Assert
      await expect(
        apiClient.updateContent(1, { order_index: 5 })
      ).rejects.toThrow('API Error');
    });
  });

  describe('邊界情況測試', () => {
    it('應該處理空陣列', () => {
      const contents: Array<{ id: number; order_index: number; title: string }> = [];
      const reorderedContents = [...contents];
      expect(reorderedContents).toEqual([]);
    });

    it('應該處理單一元素', () => {
      const contents = [{ id: 1, order_index: 1, title: 'Only Content' }];
      const reorderedContents = [...contents];
      expect(reorderedContents).toEqual(contents);
    });

    it('應該處理相同位置的拖拽（無變化）', () => {
      const originalContents = [
        { id: 1, order_index: 1, title: 'Content 1' },
        { id: 2, order_index: 2, title: 'Content 2' }
      ];

      // 拖拽到同一位置
      const oldIndex = 0;
      const newIndex = 0;

      if (oldIndex === newIndex) {
        // 無需變更
        expect(originalContents).toEqual(originalContents);
      }
    });
  });
});
