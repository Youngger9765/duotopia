import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDemoAzurePronunciation } from "../useDemoAzurePronunciation";
import { demoSpeechService } from "@/services/demoSpeechService";
import { DemoLimitExceededError } from "@/services/demoSpeechService";
import { toast } from "sonner";

// Mock dependencies
vi.mock("@/services/demoSpeechService", () => ({
  demoSpeechService: {
    analyzePronunciation: vi.fn(),
    getRemainingToday: vi.fn(() => -1),
  },
  DemoLimitExceededError: class DemoLimitExceededError extends Error {
    public readonly limit: number;
    public readonly resetAt: string;
    public readonly suggestion: string;
    constructor(data: {
      error: string;
      message: string;
      suggestion: string;
      limit: number;
      reset_at: string;
    }) {
      super(data.message);
      this.name = "DemoLimitExceededError";
      this.limit = data.limit;
      this.resetAt = data.reset_at;
      this.suggestion = data.suggestion;
    }
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

describe("useDemoAzurePronunciation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("should have correct initial values", () => {
      const { result } = renderHook(() => useDemoAzurePronunciation());

      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.result).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.limitExceeded).toBe(false);
      expect(result.current.limitError).toBeNull();
      expect(result.current.remainingToday).toBe(-1);
    });
  });

  describe("analyzePronunciation", () => {
    it("should analyze pronunciation successfully", async () => {
      const mockAnalysisResult = {
        pronunciationScore: 85,
        accuracyScore: 90,
        fluencyScore: 80,
        completenessScore: 85,
        words: [
          { word: "hello", accuracyScore: 95, errorType: "None" },
          { word: "world", accuracyScore: 85, errorType: "None" },
        ],
        privPronJson: {
          Words: [
            {
              Word: "hello",
              PronunciationAssessment: {
                AccuracyScore: 95,
                ErrorType: "None",
              },
            },
            {
              Word: "world",
              PronunciationAssessment: {
                AccuracyScore: 85,
                ErrorType: "None",
              },
            },
          ],
        },
      };

      vi.mocked(demoSpeechService.analyzePronunciation).mockResolvedValue({
        result: mockAnalysisResult as never,
        latencyMs: 1200,
      });
      vi.mocked(demoSpeechService.getRemainingToday).mockReturnValue(58);

      const { result } = renderHook(() => useDemoAzurePronunciation());
      const audioBlob = new Blob(["test"], { type: "audio/wav" });

      let analysisResult: unknown;
      await act(async () => {
        analysisResult = await result.current.analyzePronunciation(
          audioBlob,
          "hello world",
        );
      });

      expect(analysisResult).not.toBeNull();
      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.result?.pronunciationScore).toBe(85);
      expect(result.current.result?.detailed_words).toHaveLength(2);
      expect(result.current.remainingToday).toBe(58);
      expect(result.current.error).toBeNull();
    });

    it("should handle DemoLimitExceededError", async () => {
      const limitError = new DemoLimitExceededError({
        error: "daily_limit_exceeded",
        message: "Limit reached",
        suggestion: "Register",
        limit: 60,
        reset_at: "2025-01-02T16:00:00Z",
      });

      vi.mocked(demoSpeechService.analyzePronunciation).mockRejectedValue(
        limitError,
      );

      const { result } = renderHook(() => useDemoAzurePronunciation());
      const audioBlob = new Blob(["test"], { type: "audio/wav" });

      let analysisResult: unknown;
      await act(async () => {
        analysisResult = await result.current.analyzePronunciation(
          audioBlob,
          "hello",
        );
      });

      expect(analysisResult).toBeNull();
      expect(result.current.limitExceeded).toBe(true);
      expect(result.current.limitError).not.toBeNull();
      expect(result.current.isAnalyzing).toBe(false);
      // Should NOT show toast for limit error
      expect(toast.error).not.toHaveBeenCalled();
    });

    it("should handle generic errors with toast", async () => {
      vi.mocked(demoSpeechService.analyzePronunciation).mockRejectedValue(
        new Error("Network error"),
      );

      const { result } = renderHook(() => useDemoAzurePronunciation());
      const audioBlob = new Blob(["test"], { type: "audio/wav" });

      await act(async () => {
        await result.current.analyzePronunciation(audioBlob, "hello");
      });

      expect(result.current.error).toBe("Network error");
      expect(result.current.isAnalyzing).toBe(false);
      expect(toast.error).toHaveBeenCalledTimes(1);
    });

    it("should reject invalid analysis result format", async () => {
      // Return an object missing required fields → type guard should fail
      vi.mocked(demoSpeechService.analyzePronunciation).mockResolvedValue({
        result: { someOtherField: true } as never,
        latencyMs: 100,
      });

      const { result } = renderHook(() => useDemoAzurePronunciation());
      const audioBlob = new Blob(["test"], { type: "audio/wav" });

      await act(async () => {
        await result.current.analyzePronunciation(audioBlob, "hello");
      });

      expect(result.current.error).toBe("Invalid analysis result format");
      expect(toast.error).toHaveBeenCalledTimes(1);
    });
  });

  describe("reset", () => {
    it("should reset all analysis state", async () => {
      vi.mocked(demoSpeechService.analyzePronunciation).mockRejectedValue(
        new Error("test error"),
      );

      const { result } = renderHook(() => useDemoAzurePronunciation());
      const audioBlob = new Blob(["test"], { type: "audio/wav" });

      await act(async () => {
        await result.current.analyzePronunciation(audioBlob, "hello");
      });

      expect(result.current.error).not.toBeNull();

      act(() => {
        result.current.reset();
      });

      expect(result.current.result).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.isAnalyzing).toBe(false);
    });
  });

  describe("clearLimitError", () => {
    it("should clear limit exceeded state", async () => {
      const limitError = new DemoLimitExceededError({
        error: "daily_limit_exceeded",
        message: "Limit reached",
        suggestion: "Register",
        limit: 60,
        reset_at: "2025-01-02T16:00:00Z",
      });

      vi.mocked(demoSpeechService.analyzePronunciation).mockRejectedValue(
        limitError,
      );

      const { result } = renderHook(() => useDemoAzurePronunciation());
      const audioBlob = new Blob(["test"], { type: "audio/wav" });

      await act(async () => {
        await result.current.analyzePronunciation(audioBlob, "hello");
      });

      expect(result.current.limitExceeded).toBe(true);

      act(() => {
        result.current.clearLimitError();
      });

      expect(result.current.limitExceeded).toBe(false);
      expect(result.current.limitError).toBeNull();
    });
  });
});
