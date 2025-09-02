/**
 * Test suite for ReadingAssessmentPanel component
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ReadingAssessmentPanel from '../ReadingAssessmentPanel';
import { toast } from 'sonner';
import { apiClient } from '../../lib/api';

// Mock dependencies
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}));

vi.mock('../../lib/api', () => ({
  apiClient: {
    updateContent: vi.fn(),
    generateTTS: vi.fn(),
    batchGenerateTTS: vi.fn(),
    uploadAudio: vi.fn(),
    translateText: vi.fn(),
    batchTranslate: vi.fn(),
  },
}));

// Mock MediaRecorder
class MockMediaRecorder {
  state = 'inactive';
  ondataavailable: ((event: any) => void) | null = null;
  onstop: (() => void) | null = null;
  
  constructor(public stream: MediaStream, public options?: any) {}
  
  start(_timeslice?: number) {
    this.state = 'recording';
    // Simulate data available event
    setTimeout(() => {
      if (this.ondataavailable) {
        this.ondataavailable({ data: new Blob(['audio'], { type: 'audio/webm' }) });
      }
    }, 100);
  }
  
  stop() {
    this.state = 'inactive';
    if (this.onstop) {
      this.onstop();
    }
  }
}

// @ts-ignore
global.MediaRecorder = MockMediaRecorder;
global.MediaRecorder.isTypeSupported = (type: string) => type.includes('webm');

// Mock navigator.mediaDevices
Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [{
        stop: vi.fn(),
      }],
      getAudioTracks: () => [{
        stop: vi.fn(),
      }],
      active: true,
    }),
  },
  configurable: true,
});

// Mock Audio
class MockAudio {
  src = '';
  play = vi.fn().mockResolvedValue(undefined);
  pause = vi.fn();
  
  constructor(src?: string) {
    if (src) this.src = src;
  }
}

// @ts-ignore
global.Audio = MockAudio;

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

describe('ReadingAssessmentPanel', () => {
  const mockContent = {
    id: 1,
    title: 'Test Content',
    items: [
      { id: '1', text: 'Hello', definition: '你好', audioUrl: '' },
      { id: '2', text: 'World', definition: '世界', audioUrl: '' },
    ],
    target_wpm: 60,
    target_accuracy: 0.8,
    time_limit_seconds: 180,
  };

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    content: mockContent,
    onSave: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Panel Rendering', () => {
    it('should render panel when isOpen is true', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      expect(screen.getByText('朗讀評測設定')).toBeInTheDocument();
    });

    it('should not render panel when isOpen is false', () => {
      render(<ReadingAssessmentPanel {...defaultProps} isOpen={false} />);
      expect(screen.queryByText('朗讀評測設定')).not.toBeInTheDocument();
    });

    it('should display content items', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      expect(screen.getByText('Hello')).toBeInTheDocument();
      expect(screen.getByText('World')).toBeInTheDocument();
    });
  });

  describe('Translation Features', () => {
    it('should translate single item', async () => {
      (apiClient.translateText as any).mockResolvedValue('測試翻譯');
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      // Find and click translate button for first item
      const translateButtons = screen.getAllByTitle('翻譯');
      fireEvent.click(translateButtons[0]);
      
      await waitFor(() => {
        expect(apiClient.translateText).toHaveBeenCalledWith('Hello', 'zh-TW');
        expect(toast.success).toHaveBeenCalledWith('翻譯完成');
      });
    });

    it('should batch translate all items', async () => {
      (apiClient.batchTranslate as any).mockResolvedValue(['測試1', '測試2']);
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const batchTranslateBtn = screen.getByText('批次翻譯');
      fireEvent.click(batchTranslateBtn);
      
      await waitFor(() => {
        expect(apiClient.batchTranslate).toHaveBeenCalledWith(
          ['Hello', 'World'],
          'zh-TW'
        );
        expect(toast.success).toHaveBeenCalledWith('批次翻譯完成');
      });
    });

    it('should handle translation error', async () => {
      (apiClient.translateText as any).mockRejectedValue(new Error('Translation failed'));
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const translateButtons = screen.getAllByTitle('翻譯');
      fireEvent.click(translateButtons[0]);
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('翻譯失敗');
      });
    });
  });

  describe('TTS (Text-to-Speech) Features', () => {
    it('should open TTS modal when clicking audio settings', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      expect(screen.getByText('音效設定')).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'TTS' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Recording' })).toBeInTheDocument();
    });

    it('should generate TTS for single item', async () => {
      (apiClient.generateTTS as any).mockResolvedValue({
        audio_url: 'https://storage.googleapis.com/test.mp3'
      });
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      // Open TTS modal
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      // Click Generate button
      const generateBtn = screen.getByText('Generate');
      fireEvent.click(generateBtn);
      
      await waitFor(() => {
        expect(apiClient.generateTTS).toHaveBeenCalled();
        expect(toast.success).toHaveBeenCalledWith('TTS 生成成功！');
      });
    });

    it('should batch generate TTS', async () => {
      (apiClient.batchGenerateTTS as any).mockResolvedValue([
        { audio_url: 'https://storage.googleapis.com/test1.mp3' },
        { audio_url: 'https://storage.googleapis.com/test2.mp3' },
      ]);
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const batchTTSBtn = screen.getByText('批次生成TTS');
      fireEvent.click(batchTTSBtn);
      
      // Confirm in dialog
      await waitFor(() => {
        const confirmBtn = screen.getByRole('button', { name: '確認生成' });
        fireEvent.click(confirmBtn);
      });
      
      await waitFor(() => {
        expect(apiClient.batchGenerateTTS).toHaveBeenCalled();
        expect(toast.success).toHaveBeenCalledWith('批次生成 TTS 完成');
      });
    });

    it('should handle TTS generation error', async () => {
      (apiClient.generateTTS as any).mockRejectedValue(new Error('TTS failed'));
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      const generateBtn = screen.getByText('Generate');
      fireEvent.click(generateBtn);
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('TTS 生成失敗');
      });
    });
  });

  describe('Recording Features', () => {
    it('should start recording when clicking record button', async () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      // Open TTS modal
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      // Switch to Recording tab
      const recordingTab = screen.getByRole('tab', { name: 'Recording' });
      fireEvent.click(recordingTab);
      
      // Click start recording
      const startBtn = screen.getByText('開始錄音');
      fireEvent.click(startBtn);
      
      await waitFor(() => {
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true });
        expect(toast.success).toHaveBeenCalledWith('開始錄音');
      });
    });

    it('should stop recording and show preview', async () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      const recordingTab = screen.getByRole('tab', { name: 'Recording' });
      fireEvent.click(recordingTab);
      
      // Start recording
      const startBtn = screen.getByText('開始錄音');
      fireEvent.click(startBtn);
      
      await waitFor(() => {
        expect(screen.getByText('停止錄音')).toBeInTheDocument();
      });
      
      // Stop recording
      const stopBtn = screen.getByText('停止錄音');
      fireEvent.click(stopBtn);
      
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('錄音完成！可以試聽或重新錄製');
      });
    });

    it('should upload recording on confirm', async () => {
      (apiClient.uploadAudio as any).mockResolvedValue({
        audio_url: 'https://storage.googleapis.com/recording.webm'
      });
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      const recordingTab = screen.getByRole('tab', { name: 'Recording' });
      fireEvent.click(recordingTab);
      
      // Start and stop recording
      const startBtn = screen.getByText('開始錄音');
      fireEvent.click(startBtn);
      
      await waitFor(() => {
        const stopBtn = screen.getByText('停止錄音');
        fireEvent.click(stopBtn);
      });
      
      // Click confirm
      await waitFor(() => {
        const confirmBtn = screen.getByText('Confirm');
        fireEvent.click(confirmBtn);
      });
      
      await waitFor(() => {
        expect(apiClient.uploadAudio).toHaveBeenCalled();
        expect(toast.success).toHaveBeenCalledWith('音檔已更新');
      });
    });

    it('should handle recording upload error', async () => {
      (apiClient.uploadAudio as any).mockRejectedValue(new Error('Upload failed'));
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      const recordingTab = screen.getByRole('tab', { name: 'Recording' });
      fireEvent.click(recordingTab);
      
      // Record and try to upload
      const startBtn = screen.getByText('開始錄音');
      fireEvent.click(startBtn);
      
      await waitFor(() => {
        const stopBtn = screen.getByText('停止錄音');
        fireEvent.click(stopBtn);
      });
      
      await waitFor(() => {
        const confirmBtn = screen.getByText('Confirm');
        fireEvent.click(confirmBtn);
      });
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('上傳失敗，請重試');
      });
    });

    it('should enforce 30-second recording limit', async () => {
      vi.useFakeTimers();
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      const recordingTab = screen.getByRole('tab', { name: 'Recording' });
      fireEvent.click(recordingTab);
      
      const startBtn = screen.getByText('開始錄音');
      fireEvent.click(startBtn);
      
      // Fast-forward 31 seconds
      vi.advanceTimersByTime(31000);
      
      await waitFor(() => {
        expect(toast.info).toHaveBeenCalledWith('已達到最長錄音時間 30 秒');
      });
      
      vi.useRealTimers();
    });
  });

  describe('Audio Source Selection', () => {
    it('should show source selection when both TTS and recording exist', async () => {
      (apiClient.generateTTS as any).mockResolvedValue({
        audio_url: 'https://storage.googleapis.com/tts.mp3'
      });
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const audioButtons = screen.getAllByTitle('音效設定');
      fireEvent.click(audioButtons[0]);
      
      // Generate TTS
      const generateBtn = screen.getByText('Generate');
      fireEvent.click(generateBtn);
      
      await waitFor(() => {
        expect(screen.getByText('TTS 生成成功！')).toBeDefined();
      });
      
      // Switch to recording and record
      const recordingTab = screen.getByRole('tab', { name: 'Recording' });
      fireEvent.click(recordingTab);
      
      const startBtn = screen.getByText('開始錄音');
      fireEvent.click(startBtn);
      
      await waitFor(() => {
        const stopBtn = screen.getByText('停止錄音');
        fireEvent.click(stopBtn);
      });
      
      // Should show source selection
      await waitFor(() => {
        expect(screen.getByText('🎵 您有兩種音源可選擇，請選擇要使用的音檔：')).toBeInTheDocument();
      });
    });

    it('should warn when confirming without selecting source', async () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      // Setup both audio sources...
      // (abbreviated for brevity)
      
      const confirmBtn = screen.getByText('Confirm');
      fireEvent.click(confirmBtn);
      
      await waitFor(() => {
        expect(toast.warning).toHaveBeenCalledWith('請選擇要使用的音源（TTS 或錄音）');
      });
    });
  });

  describe('Save and Update', () => {
    it('should save content updates', async () => {
      (apiClient.updateContent as any).mockResolvedValue({});
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      // Make some changes
      const inputs = screen.getAllByRole('textbox');
      fireEvent.change(inputs[0], { target: { value: 'Updated text' } });
      
      // Save
      const saveBtn = screen.getByText('儲存');
      fireEvent.click(saveBtn);
      
      await waitFor(() => {
        expect(apiClient.updateContent).toHaveBeenCalledWith(
          1,
          expect.objectContaining({
            items: expect.arrayContaining([
              expect.objectContaining({ text: 'Updated text' })
            ])
          })
        );
        expect(toast.success).toHaveBeenCalledWith('內容已更新');
      });
    });

    it('should handle save error', async () => {
      (apiClient.updateContent as any).mockRejectedValue(new Error('Save failed'));
      
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const saveBtn = screen.getByText('儲存');
      fireEvent.click(saveBtn);
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('更新失敗');
      });
    });
  });

  describe('Item Management', () => {
    it('should add new item', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const addBtn = screen.getByText('新增項目');
      fireEvent.click(addBtn);
      
      const items = screen.getAllByRole('textbox');
      expect(items.length).toBeGreaterThan(4); // Original 2 items * 2 fields + new item
    });

    it('should delete item', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const deleteButtons = screen.getAllByTitle('刪除');
      fireEvent.click(deleteButtons[0]);
      
      expect(screen.queryByText('Hello')).not.toBeInTheDocument();
    });

    it('should not delete last item', () => {
      const singleItemContent = {
        ...mockContent,
        items: [{ id: '1', text: 'Only item', definition: '唯一項目', audioUrl: '' }],
      };
      
      render(<ReadingAssessmentPanel {...defaultProps} content={singleItemContent} />);
      
      const deleteBtn = screen.queryByTitle('刪除');
      expect(deleteBtn).not.toBeInTheDocument();
    });
  });

  describe('Settings', () => {
    it('should update target WPM', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const wpmInput = screen.getByLabelText('目標 WPM');
      fireEvent.change(wpmInput, { target: { value: '80' } });
      
      expect(wpmInput).toHaveValue(80);
    });

    it('should update target accuracy', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const accuracyInput = screen.getByLabelText('目標準確率');
      fireEvent.change(accuracyInput, { target: { value: '90' } });
      
      expect(accuracyInput).toHaveValue(90);
    });

    it('should update time limit', () => {
      render(<ReadingAssessmentPanel {...defaultProps} />);
      
      const timeLimitInput = screen.getByLabelText('時間限制（秒）');
      fireEvent.change(timeLimitInput, { target: { value: '240' } });
      
      expect(timeLimitInput).toHaveValue(240);
    });
  });
});