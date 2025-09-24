import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AdminMonitoringPage from '../AdminMonitoringPage';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('AdminMonitoringPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset fetch mock
    (global.fetch as unknown as ReturnType<typeof vi.fn>).mockReset();
  });

  describe('Component Rendering', () => {
    it('should render without authentication requirement', () => {
      renderWithRouter(<AdminMonitoringPage />);

      expect(screen.getByText(/系統監控面板/i)).toBeInTheDocument();
      expect(screen.getByText(/錄音上傳狀態/i)).toBeInTheDocument();
      expect(screen.getByText(/AI 分析狀態/i)).toBeInTheDocument();
    });

    it('should display monitoring sections', () => {
      renderWithRouter(<AdminMonitoringPage />);

      // Check for main sections
      expect(screen.getByText(/即時狀態/i)).toBeInTheDocument();
      expect(screen.getByText(/重試統計/i)).toBeInTheDocument();
      expect(screen.getByText(/錯誤日誌/i)).toBeInTheDocument();
    });
  });

  describe('Status Monitoring', () => {
    it('should fetch and display audio upload status', async () => {
      const mockStatus = {
        total_uploads: 150,
        successful: 145,
        failed: 5,
        in_progress: 2,
        retry_count: 3,
        last_updated: new Date().toISOString()
      };

      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus
      });

      renderWithRouter(<AdminMonitoringPage />);

      await waitFor(() => {
        expect(screen.getByText(/總上傳數: 150/i)).toBeInTheDocument();
        expect(screen.getByText(/成功: 145/i)).toBeInTheDocument();
        expect(screen.getByText(/失敗: 5/i)).toBeInTheDocument();
      });
    });

    it('should fetch and display AI analysis status', async () => {
      const mockStatus = {
        total_analyses: 100,
        successful: 95,
        failed: 3,
        in_queue: 2,
        avg_processing_time: 2.5,
        last_updated: new Date().toISOString()
      };

      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus
      });

      renderWithRouter(<AdminMonitoringPage />);

      await waitFor(() => {
        expect(screen.getByText(/總分析數: 100/i)).toBeInTheDocument();
        expect(screen.getByText(/成功: 95/i)).toBeInTheDocument();
        expect(screen.getByText(/失敗: 3/i)).toBeInTheDocument();
        expect(screen.getByText(/平均處理時間: 2.5秒/i)).toBeInTheDocument();
      });
    });
  });

  describe('Manual Testing', () => {
    it('should allow manual audio upload test', async () => {
      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          audio_url: 'https://example.com/test.mp3',
          message: '測試上傳成功'
        })
      });

      renderWithRouter(<AdminMonitoringPage />);

      const testButton = screen.getByText(/測試錄音上傳/i);
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(screen.getByText(/測試上傳成功/i)).toBeInTheDocument();
      });
    });

    it('should allow manual AI analysis test', async () => {
      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          overall_score: 85,
          message: 'AI 分析測試成功'
        })
      });

      renderWithRouter(<AdminMonitoringPage />);

      const testButton = screen.getByText(/測試 AI 分析/i);
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(screen.getByText(/AI 分析測試成功/i)).toBeInTheDocument();
        expect(screen.getByText(/分數: 85/i)).toBeInTheDocument();
      });
    });
  });

  describe('Retry Statistics', () => {
    it('should display retry statistics', async () => {
      const mockRetryStats = {
        audio_upload: {
          total_retries: 25,
          successful_after_retry: 20,
          failed_after_retry: 5,
          retry_distribution: {
            '1': 15,
            '2': 7,
            '3': 3
          }
        },
        ai_analysis: {
          total_retries: 15,
          successful_after_retry: 12,
          failed_after_retry: 3,
          retry_distribution: {
            '1': 10,
            '2': 4,
            '3': 1
          }
        }
      };

      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRetryStats
      });

      renderWithRouter(<AdminMonitoringPage />);

      await waitFor(() => {
        // Audio upload retry stats
        expect(screen.getByText(/錄音上傳重試統計/i)).toBeInTheDocument();
        expect(screen.getByText(/總重試次數: 25/i)).toBeInTheDocument();
        expect(screen.getByText(/重試後成功: 20/i)).toBeInTheDocument();

        // AI analysis retry stats
        expect(screen.getByText(/AI 分析重試統計/i)).toBeInTheDocument();
        expect(screen.getByText(/總重試次數: 15/i)).toBeInTheDocument();
        expect(screen.getByText(/重試後成功: 12/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Logs', () => {
    it('should display recent error logs', async () => {
      const mockErrorLogs = [
        {
          id: 1,
          timestamp: new Date().toISOString(),
          type: 'audio_upload',
          error: 'NetworkError: Failed to fetch',
          retry_count: 2,
          resolved: true
        },
        {
          id: 2,
          timestamp: new Date().toISOString(),
          type: 'ai_analysis',
          error: '429 Too Many Requests',
          retry_count: 3,
          resolved: false
        }
      ];

      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockErrorLogs
      });

      renderWithRouter(<AdminMonitoringPage />);

      await waitFor(() => {
        expect(screen.getByText(/NetworkError: Failed to fetch/i)).toBeInTheDocument();
        expect(screen.getByText(/429 Too Many Requests/i)).toBeInTheDocument();
      });
    });
  });

  describe('Auto Refresh', () => {
    it('should auto-refresh status every 5 seconds', async () => {
      vi.useFakeTimers();

      const mockStatus = {
        total_uploads: 100,
        successful: 95,
        failed: 5
      };

      (global.fetch as unknown as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockStatus
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockStatus, total_uploads: 105 })
        });

      renderWithRouter(<AdminMonitoringPage />);

      // Initial load
      await waitFor(() => {
        expect(screen.getByText(/總上傳數: 100/i)).toBeInTheDocument();
      });

      // Fast-forward 5 seconds
      vi.advanceTimersByTime(5000);

      await waitFor(() => {
        expect(screen.getByText(/總上傳數: 105/i)).toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('should allow manual refresh', async () => {
      const mockStatus = {
        total_uploads: 100,
        successful: 95,
        failed: 5
      };

      (global.fetch as unknown as ReturnType<typeof vi.fn>)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockStatus
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockStatus, total_uploads: 110 })
        });

      renderWithRouter(<AdminMonitoringPage />);

      await waitFor(() => {
        expect(screen.getByText(/總上傳數: 100/i)).toBeInTheDocument();
      });

      const refreshButton = screen.getByText(/重新整理/i);
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText(/總上傳數: 110/i)).toBeInTheDocument();
      });
    });
  });

  describe('Connection Status', () => {
    it('should show connection status to backend', async () => {
      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' })
      });

      renderWithRouter(<AdminMonitoringPage />);

      await waitFor(() => {
        expect(screen.getByText(/連線狀態: 正常/i)).toBeInTheDocument();
      });
    });

    it('should show error when backend is unreachable', async () => {
      (global.fetch as unknown as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'));

      renderWithRouter(<AdminMonitoringPage />);

      await waitFor(() => {
        expect(screen.getByText(/連線狀態: 離線/i)).toBeInTheDocument();
      });
    });
  });
});
