import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAzurePronunciation } from "../useAzurePronunciation";
import { azureSpeechService } from "@/services/azureSpeechService";
import { toast } from "sonner";

// Mock dependencies
vi.mock("@/services/azureSpeechService", () => ({
  azureSpeechService: {
    analyzePronunciation: vi.fn(),
    uploadAnalysisInBackground: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
  },
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("useAzurePronunciation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("analyzePronunciation", () => {
    it("should analyze pronunciation successfully", async () => {
      const mockResult = {
        pronunciationScore: 85,
        accuracyScore: 90,
        fluencyScore: 80,
        completenessScore: 85,
        words: [
          { word: "hello", accuracyScore: 95, errorType: "None" },
          { word: "world", accuracyScore: 85, errorType: "None" },
        ],
      };

      vi.mocked(azureSpeechService.analyzePronunciation).mockResolvedValue({
        result: mockResult as never,
        latencyMs: 1500,
      });

      const { result } = renderHook(() => useAzurePronunciation());

      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.result).toBeNull();

      const audioBlob = new Blob(["audio data"], { type: "audio/wav" });
      const referenceText = "hello world";

      const analysisPromise = result.current.analyzePronunciation(
        audioBlob,
        referenceText,
      );

      const analysisResult = await analysisPromise;

      // Should have result after completion
      await waitFor(() => {
        expect(result.current.isAnalyzing).toBe(false);
        expect(result.current.result).toEqual(mockResult);
        expect(analysisResult).toEqual(mockResult);
      });

      // Verify service was called correctly
      expect(azureSpeechService.analyzePronunciation).toHaveBeenCalledWith(
        audioBlob,
        referenceText,
      );

      // Verify background upload was triggered
      expect(
        azureSpeechService.uploadAnalysisInBackground,
      ).toHaveBeenCalledWith(expect.any(Blob), mockResult, 1500);
    });

    it("should handle analysis error gracefully", async () => {
      const mockError = new Error("Azure API error");
      vi.mocked(azureSpeechService.analyzePronunciation).mockRejectedValue(
        mockError,
      );

      const { result } = renderHook(() => useAzurePronunciation());

      const audioBlob = new Blob(["audio data"], { type: "audio/wav" });
      const analysisPromise = result.current.analyzePronunciation(
        audioBlob,
        "test",
      );

      const analysisResult = await analysisPromise;

      await waitFor(() => {
        expect(result.current.isAnalyzing).toBe(false);
        expect(result.current.error).toBe("Azure API error");
        expect(analysisResult).toBeNull();
      });

      // Should show error toast
      expect(toast.error).toHaveBeenCalledWith("errors.analysisFailed", {
        description: "Azure API error",
      });
    });

    it("should return null when analysis fails", async () => {
      vi.mocked(azureSpeechService.analyzePronunciation).mockRejectedValue(
        new Error("Network error"),
      );

      const { result } = renderHook(() => useAzurePronunciation());

      const analysisResult = await result.current.analyzePronunciation(
        new Blob(),
        "test",
      );

      expect(analysisResult).toBeNull();
    });

    it("should handle multiple consecutive analyses", async () => {
      const mockResult1 = {
        pronunciationScore: 85,
        accuracyScore: 90,
        fluencyScore: 80,
        completenessScore: 85,
      };

      const mockResult2 = {
        pronunciationScore: 92,
        accuracyScore: 95,
        fluencyScore: 90,
        completenessScore: 93,
      };

      vi.mocked(azureSpeechService.analyzePronunciation)
        .mockResolvedValueOnce({
          result: mockResult1 as never,
          latencyMs: 1500,
        })
        .mockResolvedValueOnce({
          result: mockResult2 as never,
          latencyMs: 1200,
        });

      const { result } = renderHook(() => useAzurePronunciation());

      // First analysis
      const audioBlob1 = new Blob(["audio1"], { type: "audio/wav" });
      await result.current.analyzePronunciation(audioBlob1, "hello");

      await waitFor(() => {
        expect(result.current.result).toEqual(mockResult1);
      });

      // Second analysis
      const audioBlob2 = new Blob(["audio2"], { type: "audio/wav" });
      await result.current.analyzePronunciation(audioBlob2, "world");

      await waitFor(() => {
        expect(result.current.result).toEqual(mockResult2);
      });
    });
  });

  describe("reset", () => {
    it("should reset all state", async () => {
      const mockResult = {
        pronunciationScore: 85,
        accuracyScore: 90,
        fluencyScore: 80,
        completenessScore: 85,
      };

      vi.mocked(azureSpeechService.analyzePronunciation).mockResolvedValue({
        result: mockResult as never,
        latencyMs: 1500,
      });

      const { result } = renderHook(() => useAzurePronunciation());

      // Analyze first
      await result.current.analyzePronunciation(new Blob(), "test");

      await waitFor(() => {
        expect(result.current.result).toEqual(mockResult);
      });

      // Reset
      await waitFor(() => {
        result.current.reset();
        expect(result.current.result).toBeNull();
        expect(result.current.error).toBeNull();
        expect(result.current.isAnalyzing).toBe(false);
      });
    });
  });

  describe("error state", () => {
    it("should set error when analysis fails with Error object", async () => {
      const errorMessage = "Custom error message";
      vi.mocked(azureSpeechService.analyzePronunciation).mockRejectedValue(
        new Error(errorMessage),
      );

      const { result } = renderHook(() => useAzurePronunciation());

      await result.current.analyzePronunciation(new Blob(), "test");

      await waitFor(() => {
        expect(result.current.error).toBe(errorMessage);
      });
    });

    it("should use fallback error message for non-Error failures", async () => {
      vi.mocked(azureSpeechService.analyzePronunciation).mockRejectedValue(
        "string error",
      );

      const { result } = renderHook(() => useAzurePronunciation());

      await result.current.analyzePronunciation(new Blob(), "test");

      await waitFor(() => {
        expect(result.current.error).toBe("errors.analysisFailedRetry");
      });
    });
  });

  describe("background upload", () => {
    it("should trigger background upload after successful analysis", async () => {
      const mockResult = {
        pronunciationScore: 85,
        accuracyScore: 90,
        fluencyScore: 80,
        completenessScore: 85,
      };

      vi.mocked(azureSpeechService.analyzePronunciation).mockResolvedValue({
        result: mockResult as never,
        latencyMs: 1234,
      });

      const { result } = renderHook(() => useAzurePronunciation());

      const audioBlob = new Blob(["audio"], { type: "audio/wav" });
      await result.current.analyzePronunciation(audioBlob, "test");

      await waitFor(() => {
        expect(
          azureSpeechService.uploadAnalysisInBackground,
        ).toHaveBeenCalledWith(expect.any(Blob), mockResult, 1234);
      });
    });

    it("should not trigger background upload when analysis fails", async () => {
      vi.mocked(azureSpeechService.analyzePronunciation).mockRejectedValue(
        new Error("Analysis failed"),
      );

      const { result } = renderHook(() => useAzurePronunciation());

      await result.current.analyzePronunciation(new Blob(), "test");

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(
        azureSpeechService.uploadAnalysisInBackground,
      ).not.toHaveBeenCalled();
    });
  });

  describe("latency logging", () => {
    it("should log latency in development mode", async () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});

      const mockResult = {
        pronunciationScore: 85,
        accuracyScore: 90,
        fluencyScore: 80,
        completenessScore: 85,
      };

      vi.mocked(azureSpeechService.analyzePronunciation).mockResolvedValue({
        result: mockResult as never,
        latencyMs: 1500,
      });

      const { result } = renderHook(() => useAzurePronunciation());

      await result.current.analyzePronunciation(new Blob(), "test");

      await waitFor(() => {
        // In development mode, the hook logs latency
        // This test verifies the console.log was called
        expect(consoleSpy).toHaveBeenCalled();
      });

      consoleSpy.mockRestore();
    });
  });
});
