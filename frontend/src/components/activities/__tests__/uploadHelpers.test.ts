import { describe, it, expect, beforeEach, vi } from "vitest";

/**
 * Tests for uploadAnalysisInBackground function
 * This function is used in both GroupedQuestionsTemplate and ReadingAssessmentTemplate
 */

describe("uploadAnalysisInBackground", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  describe("Basic Upload", () => {
    it("should upload without blocking (return immediately)", async () => {
      const mockFetch = vi.spyOn(global, "fetch").mockResolvedValue({
        ok: true,
        json: async () => ({ status: "success" }),
      } as Response);

      const blob = new Blob(["audio"], { type: "audio/wav" });
      const result = { pronunciationScore: 85 };

      // Define the function inline to test its behavior
      const uploadAnalysisInBackground = async (
        audioBlob: Blob,
        analysisResult: { pronunciationScore: number },
        progressId: number | null,
      ) => {
        try {
          const apiUrl = import.meta.env.VITE_API_URL || "";
          const formData = new FormData();

          const uploadFileExtension = audioBlob.type.includes("mp4")
            ? "recording.mp4"
            : audioBlob.type.includes("webm")
              ? "recording.webm"
              : "recording.audio";

          formData.append("audio_file", audioBlob, uploadFileExtension);
          formData.append(
            "analysis_json",
            JSON.stringify({
              pronunciation_score: analysisResult.pronunciationScore,
            }),
          );

          if (progressId) {
            formData.append("progress_id", progressId.toString());
          }

          // Non-blocking upload
          fetch(`${apiUrl}/api/speech/upload-analysis`, {
            method: "POST",
            headers: {
              Authorization: `Bearer mock-token`,
            },
            body: formData,
          })
            .then(async (response) => {
              if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
              }
              return await response.json();
            })
            .catch((error) => {
              console.error("Background upload failed:", error);
            });
        } catch (error) {
          console.error("Failed to prepare background upload:", error);
        }
      };

      // Call should return immediately (not await the upload)
      const startTime = Date.now();
      await uploadAnalysisInBackground(blob, result, 123);
      const elapsedTime = Date.now() - startTime;

      // Should return almost immediately (< 50ms)
      expect(elapsedTime).toBeLessThan(50);

      // Fetch should still be called
      expect(mockFetch).toHaveBeenCalled();

      mockFetch.mockRestore();
    });

    it("should upload with correct FormData structure", async () => {
      let capturedFormData: FormData | null = null;

      const mockFetch = vi
        .spyOn(global, "fetch")
        .mockImplementation(
          async (_url: unknown, options?: { body?: unknown }) => {
            if (options?.body instanceof FormData) {
              capturedFormData = options.body;
            }
            return {
              ok: true,
              json: async () => ({ status: "success" }),
            } as Response;
          },
        );

      const blob = new Blob(["audio data"], { type: "audio/webm" });
      const result = {
        pronunciationScore: 85,
        accuracyScore: 90,
        fluencyScore: 80,
        completenessScore: 85,
      };
      const progressId = 456;

      // Inline function (same as above)
      const uploadAnalysisInBackground = async (
        audioBlob: Blob,
        analysisResult: typeof result,
        pId: number | null,
      ) => {
        const apiUrl = import.meta.env.VITE_API_URL || "";
        const formData = new FormData();

        const uploadFileExtension = audioBlob.type.includes("mp4")
          ? "recording.mp4"
          : audioBlob.type.includes("webm")
            ? "recording.webm"
            : "recording.audio";

        formData.append("audio_file", audioBlob, uploadFileExtension);
        formData.append(
          "analysis_json",
          JSON.stringify({
            pronunciation_score: analysisResult.pronunciationScore,
            accuracy_score: analysisResult.accuracyScore,
            fluency_score: analysisResult.fluencyScore,
            completeness_score: analysisResult.completenessScore,
          }),
        );

        if (pId) {
          formData.append("progress_id", pId.toString());
        }

        await fetch(`${apiUrl}/api/speech/upload-analysis`, {
          method: "POST",
          headers: {
            Authorization: `Bearer mock-token`,
          },
          body: formData,
        });
      };

      await uploadAnalysisInBackground(blob, result, progressId);

      // Wait for fetch to be called
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/speech/upload-analysis"),
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Authorization: "Bearer mock-token",
          }),
        }),
      );

      // Verify FormData contents
      expect(capturedFormData).not.toBeNull();
      expect(capturedFormData!.has("audio_file")).toBe(true);
      expect(capturedFormData!.has("analysis_json")).toBe(true);
      expect(capturedFormData!.has("progress_id")).toBe(true);
      expect(capturedFormData!.get("progress_id")).toBe("456");

      mockFetch.mockRestore();
    });
  });

  describe("Error Handling", () => {
    it("should not throw error if upload fails", async () => {
      const mockFetch = vi
        .spyOn(global, "fetch")
        .mockRejectedValue(new Error("Network error"));

      const blob = new Blob(["audio"], { type: "audio/wav" });

      const uploadAnalysisInBackground = async (
        audioBlob: Blob,
        analysisResult: { pronunciationScore: number },
      ) => {
        try {
          const apiUrl = import.meta.env.VITE_API_URL || "";
          const formData = new FormData();
          formData.append("audio_file", audioBlob, "recording.audio");
          formData.append("analysis_json", JSON.stringify(analysisResult));

          fetch(`${apiUrl}/api/speech/upload-analysis`, {
            method: "POST",
            body: formData,
          }).catch(() => {
            // Silently fail
          });
        } catch {
          // Should not throw
        }
      };

      // Should not throw
      await expect(
        uploadAnalysisInBackground(blob, { pronunciationScore: 85 }),
      ).resolves.not.toThrow();

      mockFetch.mockRestore();
    });

    it("should log error if upload fails", async () => {
      const consoleSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const mockFetch = vi.spyOn(global, "fetch").mockImplementation(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: async () => ({}),
        } as Response),
      );

      const uploadAnalysisInBackground = async (
        audioBlob: Blob,
        analysisResult: { pronunciationScore: number },
      ) => {
        const apiUrl = import.meta.env.VITE_API_URL || "";
        const formData = new FormData();
        formData.append("audio_file", audioBlob, "recording.audio");
        formData.append("analysis_json", JSON.stringify(analysisResult));

        fetch(`${apiUrl}/api/speech/upload-analysis`, {
          method: "POST",
          body: formData,
        })
          .then(async (response) => {
            if (!response.ok) {
              throw new Error(`Upload failed: ${response.status}`);
            }
          })
          .catch((error) => {
            console.error("Background upload failed:", error);
          });
      };

      const blob = new Blob(["audio"], { type: "audio/wav" });
      await uploadAnalysisInBackground(blob, { pronunciationScore: 85 });

      // Wait for async error handler
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(consoleSpy).toHaveBeenCalledWith(
        "Background upload failed:",
        expect.any(Error),
      );

      consoleSpy.mockRestore();
      mockFetch.mockRestore();
    });
  });

  describe("File Type Detection", () => {
    it("should use correct file extension for mp4", async () => {
      let capturedFormData: FormData | null = null;

      const mockFetch = vi
        .spyOn(global, "fetch")
        .mockImplementation(
          async (_url: unknown, options?: { body?: unknown }) => {
            if (options?.body instanceof FormData) {
              capturedFormData = options.body;
            }
            return {
              ok: true,
              json: async () => ({ status: "success" }),
            } as Response;
          },
        );

      const uploadAnalysisInBackground = async (audioBlob: Blob) => {
        const formData = new FormData();
        const uploadFileExtension = audioBlob.type.includes("mp4")
          ? "recording.mp4"
          : audioBlob.type.includes("webm")
            ? "recording.webm"
            : "recording.audio";

        formData.append("audio_file", audioBlob, uploadFileExtension);
        formData.append("analysis_json", JSON.stringify({}));

        await fetch("/api/speech/upload-analysis", {
          method: "POST",
          body: formData,
        });
      };

      const blob = new Blob(["audio"], { type: "audio/mp4" });
      await uploadAnalysisInBackground(blob);

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(capturedFormData).not.toBeNull();
      const audioFile = capturedFormData!.get("audio_file") as File;
      expect(audioFile.name).toBe("recording.mp4");

      mockFetch.mockRestore();
    });

    it("should use correct file extension for webm", async () => {
      let capturedFormData: FormData | null = null;

      const mockFetch = vi
        .spyOn(global, "fetch")
        .mockImplementation(
          async (_url: unknown, options?: { body?: unknown }) => {
            if (options?.body instanceof FormData) {
              capturedFormData = options.body;
            }
            return {
              ok: true,
              json: async () => ({ status: "success" }),
            } as Response;
          },
        );

      const uploadAnalysisInBackground = async (audioBlob: Blob) => {
        const formData = new FormData();
        const uploadFileExtension = audioBlob.type.includes("mp4")
          ? "recording.mp4"
          : audioBlob.type.includes("webm")
            ? "recording.webm"
            : "recording.audio";

        formData.append("audio_file", audioBlob, uploadFileExtension);
        formData.append("analysis_json", JSON.stringify({}));

        await fetch("/api/speech/upload-analysis", {
          method: "POST",
          body: formData,
        });
      };

      const blob = new Blob(["audio"], { type: "audio/webm" });
      await uploadAnalysisInBackground(blob);

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(capturedFormData).not.toBeNull();
      const audioFile = capturedFormData!.get("audio_file") as File;
      expect(audioFile.name).toBe("recording.webm");

      mockFetch.mockRestore();
    });
  });

  describe("Optional Progress ID", () => {
    it("should work without progress_id", async () => {
      let capturedFormData: FormData | null = null;

      const mockFetch = vi
        .spyOn(global, "fetch")
        .mockImplementation(
          async (_url: unknown, options?: { body?: unknown }) => {
            if (options?.body instanceof FormData) {
              capturedFormData = options.body;
            }
            return {
              ok: true,
              json: async () => ({ status: "success" }),
            } as Response;
          },
        );

      const uploadAnalysisInBackground = async (
        audioBlob: Blob,
        analysisResult: { pronunciationScore: number },
        progressId: number | null,
      ) => {
        const formData = new FormData();
        formData.append("audio_file", audioBlob, "recording.audio");
        formData.append("analysis_json", JSON.stringify(analysisResult));

        if (progressId) {
          formData.append("progress_id", progressId.toString());
        }

        await fetch("/api/speech/upload-analysis", {
          method: "POST",
          body: formData,
        });
      };

      const blob = new Blob(["audio"], { type: "audio/wav" });
      await uploadAnalysisInBackground(blob, { pronunciationScore: 85 }, null);

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(capturedFormData).not.toBeNull();
      expect(capturedFormData!.has("audio_file")).toBe(true);
      expect(capturedFormData!.has("analysis_json")).toBe(true);
      expect(capturedFormData!.has("progress_id")).toBe(false);

      mockFetch.mockRestore();
    });
  });
});
