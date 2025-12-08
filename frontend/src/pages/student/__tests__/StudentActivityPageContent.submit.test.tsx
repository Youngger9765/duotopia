import { describe, test, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import StudentActivityPageContent from "../StudentActivityPageContent";

// Mock i18n translation
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: { [key: string]: string } = {
        "studentActivityPage.validation.itemNumber": "Item",
        "studentActivityPage.validation.notRecorded": " not recorded",
        "studentActivityPage.validation.notUploaded": " not yet uploaded",
        "studentActivityPage.preview.cannotSubmit":
          "Cannot submit in preview mode",
        "studentActivityPage.buttons.submit": "Submit",
        "studentActivityPage.messages.submitSuccess": "Submitted successfully!",
        "studentActivityPage.messages.submitError": "Submission failed",
      };
      return translations[key] || key;
    },
  }),
}));

// Mock sonner toast library
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

// Mock browser APIs that aren't supported in JSDOM
Object.defineProperty(window, "scrollTo", {
  value: () => {},
  writable: true,
});

beforeEach(() => {
  // Mock Audio and MediaRecorder to prevent browser API issues
  Object.defineProperty(window, "Audio", {
    writable: true,
    value: class {
      load() {}
      play() {}
      pause() {}
      src = "";
      currentTime = 0;
      duration = 0;
      addEventListener(event: string, callback: () => void) {
        if (event === "loadedmetadata") {
          callback();
        }
      }
      removeEventListener() {}
    },
  });

  Object.defineProperty(window, "MediaRecorder", {
    writable: true,
    value: class {
      state = "inactive";
      mimeType = "audio/webm";
      start() {}
      stop() {}
      ondataavailable = () => {};
      onstop = () => {};
    },
  });

  // Mock MediaDevices
  Object.defineProperty(navigator, "mediaDevices", {
    value: {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: () => {} }],
      }),
    },
    writable: true,
  });
});

describe("StudentActivityPageContent - Submission with Blob URLs", () => {
  test("🔴 Should NOT allow submission with blob URLs", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();

    const activities = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Test Activity",
        content: "Test content",
        target_text: "Test text",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            id: 101,
            text: "Item 1",
            recording_url: "blob:http://localhost:3000/abc123", // ⚠️ blob URL
            progress_id: 1001,
          },
        ],
      },
    ];

    render(
      <StudentActivityPageContent
        activities={activities}
        assignmentTitle="Test"
        assignmentId={1}
        onSubmit={mockOnSubmit}
      />,
    );

    // Click submit
    const submitButtons = screen.getAllByRole("button", { name: /Submit/i });
    await user.click(submitButtons[0]);

    // ✅ Should show warning dialog (item not uploaded)
    await waitFor(() => {
      expect(screen.getByText(/not yet uploaded/i)).toBeInTheDocument();
    });

    // ✅ Should NOT call onSubmit
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test("✅ Should allow submission with GCS URLs", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn().mockResolvedValue({});

    const activities = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Test Activity",
        content: "Test content",
        target_text: "Test text",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            id: 101,
            text: "Item 1",
            recording_url: "https://storage.googleapis.com/duotopia/audio.webm", // ✅ GCS URL
            progress_id: 1001,
          },
        ],
      },
    ];

    const { toast } = await import("sonner");

    render(
      <StudentActivityPageContent
        activities={activities}
        assignmentTitle="Test"
        assignmentId={1}
        onSubmit={mockOnSubmit}
      />,
    );

    // Click submit
    const submitButtons = screen.getAllByRole("button", { name: /Submit/i });
    await user.click(submitButtons[0]);

    // ✅ Should call onSubmit
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });

    // ✅ Should show success toast
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        expect.stringContaining("Submitted successfully!"),
      );
    });
  });

  test("⚠️ Should warn about mixed blob and GCS URLs", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();

    const activities = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Test Activity",
        content: "Test content",
        target_text: "Test text",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            id: 101,
            text: "Item 1",
            recording_url:
              "https://storage.googleapis.com/duotopia/audio1.webm", // ✅ GCS
          },
          {
            id: 102,
            text: "Item 2",
            recording_url: "blob:http://localhost:3000/xyz789", // ⚠️ blob
          },
        ],
      },
    ];

    render(
      <StudentActivityPageContent
        activities={activities}
        assignmentTitle="Test"
        assignmentId={1}
        onSubmit={mockOnSubmit}
      />,
    );

    const submitButtons = screen.getAllByRole("button", { name: /Submit/i });
    await user.click(submitButtons[0]);

    // ✅ Should show warning dialog (not yet uploaded)
    await waitFor(() => {
      expect(screen.getByText(/not yet uploaded/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });
});
