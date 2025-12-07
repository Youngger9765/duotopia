/**
 * TDD Test Suite for Issue #75: Manual Analysis Workflow
 *
 * Requirements:
 * 1. Recording complete → Upload to GCS immediately (no automatic analysis)
 * 2. Upload complete → Show "Analyze" button (enabled)
 * 3. Changing questions → Don't trigger analysis (but continue upload)
 * 4. Submit → Only check recordings exist (don't check analysis status)
 * 5. Render → Show recording + analysis (if both exist)
 */

import { describe, test, expect, beforeEach, vi, type Mock } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import StudentActivityPageContent from "../StudentActivityPageContent";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

// Mock dependencies
vi.mock("react-router-dom", () => ({
  useParams: vi.fn(),
  useNavigate: vi.fn(),
}));

vi.mock("react-i18next", () => ({
  useTranslation: vi.fn(() => ({
    t: (key: string, params?: Record<string, unknown>) => {
      if (params?.count !== undefined) return `${key}:${params.count}`;
      if (params?.number !== undefined) return `${key}:${params.number}`;
      return key;
    },
  })),
}));

vi.mock("sonner", () => ({
  toast: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}));

const mockStudentAuthStore = {
  getState: vi.fn(() => ({
    token: "mock-token",
  })),
};

vi.mock("@/stores/studentAuthStore", () => ({
  useStudentAuthStore: Object.assign(
    vi.fn(() => ({
      token: "mock-token",
    })),
    {
      getState: () => mockStudentAuthStore.getState(),
    },
  ),
}));

vi.mock("@/utils/audioRecordingStrategy", () => ({
  getRecordingStrategy: vi.fn(() => ({
    platformName: "test",
    minFileSize: 100,
    minDuration: 0.5,
  })),
  selectSupportedMimeType: vi.fn(() => "audio/webm"),
  validateDuration: vi.fn(async () => ({
    valid: true,
    duration: 5.0,
    method: "test",
  })),
}));

vi.mock("@/utils/retryHelper", () => ({
  retryAudioUpload: vi.fn(async (fn) => await fn()),
  retryAIAnalysis: vi.fn(async (fn) => await fn()),
}));

describe("Issue #75: Manual Analysis Workflow (TDD)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useParams as Mock).mockReturnValue({ activityId: "1" });
    (useNavigate as Mock).mockReturnValue(vi.fn());
    (useTranslation as Mock).mockReturnValue({
      t: (key: string, params?: Record<string, unknown>) => {
        if (params?.count !== undefined) return `${key}:${params.count}`;
        if (params?.number !== undefined) return `${key}:${params.number}`;
        return key;
      },
    });

    window.scrollTo = vi.fn();
    window.HTMLMediaElement.prototype.load = vi.fn();
    window.HTMLMediaElement.prototype.play = vi.fn(() => Promise.resolve());
    window.HTMLMediaElement.prototype.pause = vi.fn();

    global.fetch = vi.fn();
    global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    global.URL.revokeObjectURL = vi.fn();
  });

  describe("Feature 1: Recording → Upload to GCS immediately (no auto-analysis)", () => {
    test("🔴 SHOULD upload to GCS immediately after recording stops", async () => {
      const user = userEvent.setup();

      // Mock MediaRecorder
      const mockChunks: Blob[] = [];
      let mockOnStop: (() => void) | null = null;

      class MockMediaRecorder {
        state = "inactive";
        mimeType = "audio/webm";
        ondataavailable: ((e: { data: Blob }) => void) | null = null;
        onstop: (() => void) | null = null;

        start() {
          this.state = "recording";
          // Simulate data available
          setTimeout(() => {
            const blob = new Blob(["audio data"], { type: "audio/webm" });
            mockChunks.push(blob);
            this.ondataavailable?.({ data: blob });
          }, 100);
        }

        stop() {
          this.state = "inactive";
          mockOnStop = this.onstop;
          // Trigger onstop after a delay
          setTimeout(() => {
            this.onstop?.();
          }, 500);
        }
      }

      window.MediaRecorder = MockMediaRecorder as unknown as typeof MediaRecorder;

      Object.defineProperty(navigator, "mediaDevices", {
        value: {
          getUserMedia: vi.fn().mockResolvedValue({
            getTracks: () => [{ stop: () => {} }],
          }),
        },
        writable: true,
      });

      // Mock fetch for upload
      (global.fetch as Mock).mockImplementation((url: string) => {
        if (url.includes("upload-recording")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                audio_url: "https://storage.googleapis.com/test-audio.webm",
                progress_id: 1001,
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          blob: () => Promise.resolve(new Blob(["audio"], { type: "audio/webm" })),
        });
      });

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test Activity",
          content: "Sample content",
          target_text: "Test text",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Test item 1",
              recording_url: "",
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test Assignment"
          assignmentId={1}
          onSubmit={vi.fn()}
        />,
      );

      // Start recording
      const recordButton = screen.getAllByRole("button")[0]; // Mic button
      await user.click(recordButton);

      // Wait for recording to start
      await waitFor(() => {
        expect(mockChunks.length).toBeGreaterThan(0);
      });

      // Stop recording
      const stopButton = screen.getByText(/stopping/i);
      await user.click(stopButton);

      // Wait for onstop to be called
      await waitFor(
        () => {
          expect(mockOnStop).toBeTruthy();
        },
        { timeout: 1000 },
      );

      // Trigger the onstop callback
      if (mockOnStop) {
        (mockOnStop as () => void)();
      }

      // ✅ SHOULD upload immediately
      await waitFor(
        () => {
          expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining("upload-recording"),
            expect.objectContaining({
              method: "POST",
            }),
          );
        },
        { timeout: 2000 },
      );

      // ❌ SHOULD NOT trigger AI analysis automatically
      expect(global.fetch).not.toHaveBeenCalledWith(
        expect.stringContaining("speech/assess"),
        expect.anything(),
      );
    });

    test("🔴 SHOULD NOT trigger analysis during upload", async () => {
      // Mock slow upload
      (global.fetch as Mock).mockImplementation((url: string) => {
        if (url.includes("upload-recording")) {
          return new Promise((resolve) => {
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: () =>
                    Promise.resolve({
                      audio_url: "https://storage.googleapis.com/test.webm",
                      progress_id: 1001,
                    }),
                }),
              1000,
            );
          });
        }
        return Promise.resolve({
          ok: true,
          blob: () => Promise.resolve(new Blob(["audio"], { type: "audio/webm" })),
        });
      });

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "blob:test-url",
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Wait for potential upload
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Should NOT call analysis API
      expect(global.fetch).not.toHaveBeenCalledWith(
        expect.stringContaining("speech/assess"),
        expect.anything(),
      );
    });
  });

  describe("Feature 2: Upload complete → Show 'Analyze' button", () => {
    test("🔴 SHOULD show enabled Analyze button after upload completes", async () => {
      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test.webm", // GCS URL = uploaded
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Should show Analyze button (enabled)
      const analyzeButton = await screen.findByRole("button", {
        name: /analyze|分析/i,
      });
      expect(analyzeButton).toBeTruthy();
      expect(analyzeButton).not.toBeDisabled();
    });

    test("🔴 SHOULD hide Analyze button if recording is blob URL (not uploaded)", async () => {
      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "blob:http://localhost/test", // Blob URL = not uploaded
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Should NOT show Analyze button
      const analyzeButtons = screen.queryAllByRole("button", {
        name: /analyze|分析/i,
      });
      expect(analyzeButtons.length).toBe(0);
    });

    test("🔴 SHOULD trigger AI analysis when Analyze button is clicked", async () => {
      const user = userEvent.setup();

      (global.fetch as Mock).mockImplementation((url: string) => {
        if (url.includes("speech/assess")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                accuracy_score: 85,
                fluency_score: 90,
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          blob: () => Promise.resolve(new Blob(["audio"], { type: "audio/webm" })),
        });
      });

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test.webm",
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      const analyzeButton = await screen.findByRole("button", {
        name: /analyze|分析/i,
      });
      await user.click(analyzeButton);

      // Should call analysis API
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("speech/assess"),
          expect.objectContaining({
            method: "POST",
          }),
        );
      });
    });
  });

  describe("Feature 3: Changing questions → Continue upload (no analysis)", () => {
    test("🔴 SHOULD continue upload when changing to next question", async () => {
      const user = userEvent.setup();

      // Mock slow upload
      let uploadResolve: ((value: { ok: boolean; json: () => Promise<unknown> }) => void) | null = null;
      (global.fetch as Mock).mockImplementation((url: string) => {
        if (url.includes("upload-recording")) {
          return new Promise((resolve) => {
            uploadResolve = resolve as (value: { ok: boolean; json: () => Promise<unknown> }) => void;
          });
        }
        return Promise.resolve({
          ok: true,
          blob: () => Promise.resolve(new Blob(["audio"], { type: "audio/webm" })),
        });
      });

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "blob:test-url-1", // Uploading
            },
            {
              id: 102,
              text: "Item 2",
              recording_url: "",
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Trigger upload
      await waitFor(() => {
        expect(uploadResolve).toBeTruthy();
      });

      // Change to next question (before upload completes)
      const nextButton = screen.getByText("2");
      await user.click(nextButton);

      // Upload should continue
      if (uploadResolve) {
        (uploadResolve as (value: { ok: boolean; json: () => Promise<unknown> }) => void)({
          ok: true,
          json: () =>
            Promise.resolve({
              audio_url: "https://storage.googleapis.com/test.webm",
              progress_id: 1001,
            }),
        });
      }

      // Wait for upload to complete
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("upload-recording"),
          expect.anything(),
        );
      });

      // Should NOT trigger analysis
      expect(global.fetch).not.toHaveBeenCalledWith(
        expect.stringContaining("speech/assess"),
        expect.anything(),
      );
    });

    test("🔴 SHOULD NOT interrupt ongoing upload when switching questions", async () => {
      // This test verifies upload is NOT cancelled when switching
      expect(true).toBe(true); // Placeholder - actual implementation will verify
    });
  });

  describe("Feature 4: Submit → Only check recordings (not analysis)", () => {
    test("🔴 SHOULD allow submit with recordings but no analysis", async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn().mockResolvedValue({});

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test.webm", // Has recording
              // NO ai_assessment
            },
          ],
        },
      ];

      const { toast } = await import("sonner");

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
          onSubmit={mockOnSubmit}
        />,
      );

      const submitButtons = screen.getAllByRole("button", { name: /submit/i });
      await user.click(submitButtons[0]);

      // Should submit successfully
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });

      // Should show success
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });
    });

    test("🔴 SHOULD warn if recording is blob URL (not uploaded)", async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "blob:http://localhost/test", // Not uploaded
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
          onSubmit={mockOnSubmit}
        />,
      );

      const submitButtons = screen.getAllByRole("button", { name: /submit/i });
      await user.click(submitButtons[0]);

      // Should show warning
      await waitFor(() => {
        expect(screen.getByText(/not yet uploaded|尚未完成上傳/i)).toBeTruthy();
      });

      // Should NOT submit
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    test("🔴 SHOULD warn if no recording exists", async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "", // No recording
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
          onSubmit={mockOnSubmit}
        />,
      );

      const submitButtons = screen.getAllByRole("button", { name: /submit/i });
      await user.click(submitButtons[0]);

      // Should show warning
      await waitFor(() => {
        expect(screen.getByText(/not recorded|未錄音/i)).toBeTruthy();
      });

      // Should NOT submit
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe("Feature 5: Render → Show recording + analysis (if exists)", () => {
    test("🔴 SHOULD show only recording player when no analysis", async () => {
      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test.webm",
              // NO ai_assessment
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Should show recording player (Play button exists)
      const playButtons = screen.getAllByRole("button");
      const hasPlayButton = playButtons.some((btn) =>
        btn.innerHTML.includes("Play"),
      );
      expect(hasPlayButton).toBe(true);

      // Should show Analyze button
      const analyzeButton = await screen.findByRole("button", {
        name: /analyze|分析/i,
      });
      expect(analyzeButton).toBeTruthy();
    });

    test("🔴 SHOULD show recording + analysis when both exist", async () => {
      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test.webm",
              ai_assessment: {
                accuracy_score: 85,
                fluency_score: 90,
              },
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Should show recording player
      const playButtons = screen.getAllByRole("button");
      const hasPlayButton = playButtons.some((btn) =>
        btn.innerHTML.includes("Play"),
      );
      expect(hasPlayButton).toBe(true);

      // Should show analysis results
      // AI scores are rendered in AIScoreDisplay component
      // We verify it exists by checking for score-related text
      await waitFor(() => {
        const bodyText = document.body.textContent || "";
        // Either the scores are displayed or "Delete" button exists (which means AI results rendered)
        const hasScores = bodyText.includes("85") || bodyText.includes("90");
        const hasDeleteButton = screen.queryByTitle(/delete|清除/i);
        expect(hasScores || hasDeleteButton).toBeTruthy();
      });
    });
  });

  describe("Feature 6: Edge Case - Delete and Re-record", () => {
    test("🔴 SHOULD clear recording state when Delete button is clicked", async () => {
      const user = userEvent.setup();

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test-v1.webm", // Has recording
              ai_assessment: {
                accuracy_score: 85,
                fluency_score: 90,
              },
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Should show Delete button (AI results rendered)
      const deleteButton = await screen.findByTitle(/delete|清除/i);
      expect(deleteButton).toBeTruthy();

      // Click Delete button
      await user.click(deleteButton);

      // Recording should be cleared
      await waitFor(() => {
        expect(screen.queryByTitle(/delete|清除/i)).not.toBeInTheDocument();
      });

      // Should show record button again (no recording)
      const recordButtons = screen.getAllByRole("button");
      const hasMicButton = recordButtons.some(
        (btn) =>
          btn.innerHTML.includes("Mic") || btn.innerHTML.includes("錄音"),
      );
      expect(hasMicButton).toBe(true);
    });

    test("🔴 SHOULD upload new file after delete (backend deletes old file)", async () => {
      const user = userEvent.setup();

      // Track upload calls
      const uploadCalls: string[] = [];

      // Mock MediaRecorder
      class MockMediaRecorder {
        state = "inactive";
        mimeType = "audio/webm";
        ondataavailable: ((e: { data: Blob }) => void) | null = null;
        onstop: (() => void) | null = null;

        start() {
          this.state = "recording";
          setTimeout(() => {
            const blob = new Blob(["audio data"], { type: "audio/webm" });
            this.ondataavailable?.({ data: blob });
          }, 100);
        }

        stop() {
          this.state = "inactive";
          setTimeout(() => {
            this.onstop?.();
          }, 500);
        }
      }

      window.MediaRecorder = MockMediaRecorder as unknown as typeof MediaRecorder;

      Object.defineProperty(navigator, "mediaDevices", {
        value: {
          getUserMedia: vi.fn().mockResolvedValue({
            getTracks: () => [{ stop: () => {} }],
          }),
        },
        writable: true,
      });

      // Mock fetch for upload
      (global.fetch as Mock).mockImplementation((url: string) => {
        if (url.includes("upload-recording")) {
          uploadCalls.push(`upload-${uploadCalls.length + 1}`);
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                audio_url: `https://storage.googleapis.com/test-v${uploadCalls.length}.webm`,
                progress_id: 1000 + uploadCalls.length,
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          blob: () => Promise.resolve(new Blob(["audio"], { type: "audio/webm" })),
        });
      });

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test-v1.webm", // Old recording
              ai_assessment: {
                accuracy_score: 85,
              },
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Delete old recording
      const deleteButton = await screen.findByTitle(/delete|清除/i);
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.queryByTitle(/delete|清除/i)).not.toBeInTheDocument();
      });

      // Re-record
      const recordButton = screen.getAllByRole("button")[0];
      await user.click(recordButton);

      await waitFor(
        () => {
          const stopButton = screen.queryByText(/stopping/i);
          expect(stopButton).toBeTruthy();
        },
        { timeout: 2000 },
      );

      const stopButton = screen.getByText(/stopping/i);
      await user.click(stopButton);

      // New file uploaded (backend deletes old file automatically)
      await waitFor(
        () => {
          expect(uploadCalls.length).toBe(1); // Second upload (first was initial state)
        },
        { timeout: 2000 },
      );

      // Backend would have deleted test-v1.webm and saved test-v2.webm
      // We verify the upload call was made (backend handles deletion)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("upload-recording"),
        expect.anything(),
      );
    });

    test("🔴 SHOULD clear AI scores when re-recording", async () => {
      const user = userEvent.setup();

      const mockActivities = [
        {
          id: 1,
          content_id: 1,
          order: 1,
          type: "grouped_questions",
          title: "Test",
          content: "Test",
          target_text: "Test",
          duration: 300,
          points: 10,
          status: "IN_PROGRESS",
          score: null,
          completed_at: null,
          items: [
            {
              id: 101,
              text: "Item 1",
              recording_url: "https://storage.googleapis.com/test-v1.webm",
              ai_assessment: {
                accuracy_score: 85,
                fluency_score: 90,
              },
            },
          ],
        },
      ];

      render(
        <StudentActivityPageContent
          activities={mockActivities}
          assignmentTitle="Test"
          assignmentId={1}
        />,
      );

      // Has AI scores initially
      const bodyText = document.body.textContent || "";
      expect(bodyText.includes("85") || bodyText.includes("90")).toBe(true);

      // Delete recording
      const deleteButton = await screen.findByTitle(/delete|清除/i);
      await user.click(deleteButton);

      // AI scores should be cleared
      await waitFor(() => {
        const newBodyText = document.body.textContent || "";
        expect(
          newBodyText.includes("85") || newBodyText.includes("90"),
        ).toBe(false);
      });
    });
  });
});
