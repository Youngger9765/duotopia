import { describe, it, expect, beforeEach, vi } from "vitest";
import { AzureSpeechService } from "../azureSpeechService";
import axios from "axios";

// Mock axios
vi.mock("axios", () => ({
  default: {
    post: vi.fn(),
  },
}));

// Mock student auth store
vi.mock("@/stores/studentAuthStore", () => ({
  useStudentAuthStore: {
    getState: vi.fn(() => ({
      token: "mock-student-token",
    })),
  },
}));

// Mock teacher auth store
vi.mock("@/stores/teacherAuthStore", () => ({
  useTeacherAuthStore: {
    getState: vi.fn(() => ({
      token: null, // Default: no teacher token (student mode)
    })),
  },
}));

// Mock Azure Speech SDK
vi.mock("microsoft-cognitiveservices-speech-sdk", () => ({
  SpeechConfig: {
    fromAuthorizationToken: vi.fn(() => ({
      speechRecognitionLanguage: "",
    })),
  },
  AudioConfig: {
    fromWavFileInput: vi.fn(),
  },
  SpeechRecognizer: vi.fn(),
  PronunciationAssessmentConfig: vi.fn(),
  PronunciationAssessmentResult: {
    fromResult: vi.fn(() => ({
      pronunciationScore: 85,
      accuracyScore: 90,
      fluencyScore: 80,
      completenessScore: 85,
    })),
  },
  ResultReason: {
    RecognizedSpeech: 3,
    NoMatch: 0,
  },
  PronunciationAssessmentGradingSystem: {
    HundredMark: 1,
  },
  PronunciationAssessmentGranularity: {
    Phoneme: 1,
  },
}));

describe("AzureSpeechService", () => {
  let service: AzureSpeechService;

  beforeEach(() => {
    service = new AzureSpeechService();
    vi.clearAllMocks();
  });

  describe("Token Management", () => {
    it("should fetch token from API on first call", async () => {
      const mockTokenResponse = {
        data: {
          token: "test-token-abc123",
          region: "eastasia",
          expires_in: 600,
        },
      };

      vi.mocked(axios.post).mockResolvedValueOnce(mockTokenResponse);

      const result = await service["getToken"]();

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining("/api/azure-speech/token"),
        null,
        expect.objectContaining({
          headers: { Authorization: "Bearer mock-student-token" },
        }),
      );
      expect(result.token).toBe("test-token-abc123");
      expect(result.region).toBe("eastasia");
    });

    it("should cache token and reuse within expiration time", async () => {
      const mockTokenResponse = {
        data: {
          token: "cached-token",
          region: "eastasia",
          expires_in: 600,
        },
      };

      vi.mocked(axios.post).mockResolvedValueOnce(mockTokenResponse);

      // First call - should fetch from API
      await service["getToken"]();
      expect(axios.post).toHaveBeenCalledTimes(1);

      // Second call - should use cache
      await service["getToken"]();
      expect(axios.post).toHaveBeenCalledTimes(1); // Still 1

      // Third call - should still use cache
      await service["getToken"]();
      expect(axios.post).toHaveBeenCalledTimes(1); // Still 1
    });

    it("should refresh token after expiration", async () => {
      const mockToken1 = {
        data: { token: "token-1", region: "eastasia", expires_in: 1 }, // 1 second
      };
      const mockToken2 = {
        data: { token: "token-2", region: "eastasia", expires_in: 600 },
      };

      vi.mocked(axios.post)
        .mockResolvedValueOnce(mockToken1)
        .mockResolvedValueOnce(mockToken2);

      // First call
      const result1 = await service["getToken"]();
      expect(result1.token).toBe("token-1");

      // Wait for token to expire
      await new Promise((resolve) => setTimeout(resolve, 1100));

      // Second call - should fetch new token
      const result2 = await service["getToken"]();
      expect(result2.token).toBe("token-2");
      expect(axios.post).toHaveBeenCalledTimes(2);
    });

    it("should handle token fetch error gracefully", async () => {
      vi.mocked(axios.post).mockRejectedValueOnce(new Error("Network error"));

      await expect(service["getToken"]()).rejects.toThrow(
        "无法获取语音分析授权，请刷新页面重试",
      );
    });
  });

  describe("Background Upload", () => {
    it("should upload audio and analysis in background", async () => {
      const mockBlob = new Blob(["fake audio"], { type: "audio/wav" });
      const mockAnalysis = { pronunciationScore: 85 };
      const latencyMs = 1500;

      vi.mocked(axios.post).mockResolvedValueOnce({
        data: { status: "success", attempt_id: 123 },
      });

      await service.uploadAnalysisInBackground(
        mockBlob,
        mockAnalysis,
        latencyMs,
      );

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining("/api/speech/upload-analysis"),
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            "Content-Type": "multipart/form-data",
            Authorization: "Bearer mock-student-token",
          }),
        }),
      );
    });

    it("should not throw error if upload fails", async () => {
      const mockBlob = new Blob(["fake audio"], { type: "audio/wav" });

      vi.mocked(axios.post).mockRejectedValueOnce(new Error("Upload failed"));

      // Should not throw
      await expect(
        service.uploadAnalysisInBackground(mockBlob, {}, 1000),
      ).resolves.not.toThrow();
    });

    it("should log error if upload fails", async () => {
      const consoleSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});
      const mockBlob = new Blob(["fake audio"], { type: "audio/wav" });

      vi.mocked(axios.post).mockRejectedValueOnce(new Error("Upload failed"));

      await service.uploadAnalysisInBackground(mockBlob, {}, 1000);

      expect(consoleSpy).toHaveBeenCalledWith(
        "Background upload failed:",
        expect.any(Error),
      );

      consoleSpy.mockRestore();
    });
  });
});
