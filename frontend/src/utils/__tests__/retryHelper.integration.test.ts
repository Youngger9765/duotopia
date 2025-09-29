import { describe, it, expect, vi, beforeEach } from 'vitest';
import { retryAudioUpload, retryAIAnalysis } from '../retryHelper';

describe('Retry Helper Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('retryAudioUpload', () => {
    it('should retry audio upload on network error', async () => {
      const mockUpload = vi.fn()
        .mockRejectedValueOnce(new Error('NetworkError: Failed to fetch'))
        .mockRejectedValueOnce(new Error('NetworkError: Connection timeout'))
        .mockResolvedValueOnce({ audio_url: 'https://example.com/audio.mp3' });

      const onRetry = vi.fn();

      const result = await retryAudioUpload(mockUpload, onRetry);

      expect(result).toEqual({ audio_url: 'https://example.com/audio.mp3' });
      expect(mockUpload).toHaveBeenCalledTimes(3);
      expect(onRetry).toHaveBeenCalledTimes(2);
      expect(onRetry).toHaveBeenCalledWith(1, expect.objectContaining({
        message: 'NetworkError: Failed to fetch'
      }));
      expect(onRetry).toHaveBeenCalledWith(2, expect.objectContaining({
        message: 'NetworkError: Connection timeout'
      }));
    });

    it('should not retry on validation errors', async () => {
      const mockUpload = vi.fn()
        .mockRejectedValueOnce(new Error('ValidationError: File too large'));

      const onRetry = vi.fn();

      await expect(retryAudioUpload(mockUpload, onRetry))
        .rejects
        .toThrow('ValidationError: File too large');

      expect(mockUpload).toHaveBeenCalledTimes(1);
      expect(onRetry).not.toHaveBeenCalled();
    });

    it('should handle 500 server errors with retry', async () => {
      const mockUpload = vi.fn()
        .mockRejectedValueOnce(new Error('500 Internal Server Error'))
        .mockResolvedValueOnce({ audio_url: 'https://example.com/audio.mp3' });

      const result = await retryAudioUpload(mockUpload);

      expect(result).toEqual({ audio_url: 'https://example.com/audio.mp3' });
      expect(mockUpload).toHaveBeenCalledTimes(2);
    });
  });

  describe('retryAIAnalysis', () => {
    it('should retry AI analysis on rate limit error', async () => {
      const mockAnalyze = vi.fn()
        .mockRejectedValueOnce(new Error('429 Too Many Requests'))
        .mockRejectedValueOnce(new Error('Rate limit exceeded'))
        .mockResolvedValueOnce({ score: 85, feedback: 'Good job!' });

      const onRetry = vi.fn();

      const result = await retryAIAnalysis(mockAnalyze, onRetry);

      expect(result).toEqual({ score: 85, feedback: 'Good job!' });
      expect(mockAnalyze).toHaveBeenCalledTimes(3);
      expect(onRetry).toHaveBeenCalledTimes(2);
    }, 15000); // Increase timeout

    it('should retry on quota exceeded error', async () => {
      const mockAnalyze = vi.fn()
        .mockRejectedValueOnce(new Error('Quota exceeded for API'))
        .mockResolvedValueOnce({ score: 90 });

      const result = await retryAIAnalysis(mockAnalyze);

      expect(result).toEqual({ score: 90 });
      expect(mockAnalyze).toHaveBeenCalledTimes(2);
    });

    it('should not retry on authentication errors', async () => {
      const mockAnalyze = vi.fn()
        .mockRejectedValueOnce(new Error('401 Unauthorized'));

      await expect(retryAIAnalysis(mockAnalyze))
        .rejects
        .toThrow('401 Unauthorized');

      expect(mockAnalyze).toHaveBeenCalledTimes(1);
    });

    it('should handle timeout errors with exponential backoff', async () => {
      const mockAnalyze = vi.fn()
        .mockRejectedValueOnce(new Error('ETIMEDOUT'))
        .mockRejectedValueOnce(new Error('ETIMEDOUT'))
        .mockResolvedValueOnce({ success: true });

      const startTime = Date.now();
      const result = await retryAIAnalysis(mockAnalyze);
      const endTime = Date.now();

      expect(result).toEqual({ success: true });
      expect(mockAnalyze).toHaveBeenCalledTimes(3);
      // Should take at least 2000ms (first delay) + 4000ms (second delay)
      expect(endTime - startTime).toBeGreaterThanOrEqual(6000);
    }, 10000); // Increase timeout for this test
  });

  describe('Real-world scenarios', () => {
    it('should handle intermittent network issues', async () => {
      // Simulate intermittent network issues
      let callCount = 0;
      const mockUpload = vi.fn(() => {
        callCount++;
        if (callCount <= 2) {
          return Promise.reject(new Error('NetworkError: Connection reset'));
        }
        return Promise.resolve({ audio_url: 'https://example.com/audio.mp3' });
      });

      const result = await retryAudioUpload(mockUpload);

      expect(result).toEqual({ audio_url: 'https://example.com/audio.mp3' });
      expect(callCount).toBe(3);
    });

    it('should handle service degradation', async () => {
      // Simulate service degradation with increasing response times
      const mockAnalyze = vi.fn()
        .mockRejectedValueOnce(new Error('503 Service Unavailable'))
        .mockRejectedValueOnce(new Error('504 Gateway Timeout'))
        .mockResolvedValueOnce({ analysis: 'completed' });

      const result = await retryAIAnalysis(mockAnalyze);

      expect(result).toEqual({ analysis: 'completed' });
      expect(mockAnalyze).toHaveBeenCalledTimes(3);
    }, 15000); // Increase timeout
  });
});
