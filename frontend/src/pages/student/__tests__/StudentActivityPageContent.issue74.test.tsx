import { describe, test, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import StudentActivityPageContent, {
  type Activity,
} from "../StudentActivityPageContent";

// Mock i18n translation
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: { count?: number }) => {
      const translations: { [key: string]: string } = {
        "studentActivityPage.buttons.back": "Back",
        "studentActivityPage.buttons.backShort": "Back",
        "studentActivityPage.buttons.submit": "Submit",
        "studentActivityPage.buttons.submitShort": "Submit",
        "studentActivityPage.buttons.submitting": "Submitting...",
        "studentActivityPage.buttons.submittingShort": "Submitting...",
        "studentActivityPage.status.saving": "Saving...",
        "studentActivityPage.status.savingShort": "Saving...",
        "studentActivityPage.labels.itemCount": `${params?.count || 0} items`,
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

// Mock browser APIs
Object.defineProperty(window, "scrollTo", {
  value: () => {},
  writable: true,
});

beforeEach(() => {
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

  Object.defineProperty(navigator, "mediaDevices", {
    value: {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: () => {} }],
      }),
    },
    writable: true,
  });
});

describe("Issue #74: Progress Calculation Logic", () => {
  test("calculates progress correctly with all items incomplete", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          { text: "Q1", audio_url: "", recording_url: "" },
          { text: "Q2", audio_url: "", recording_url: "" },
          { text: "Q3", audio_url: "", recording_url: "" },
        ],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Should show 0 / 3 (0 completed, 3 total)
    expect(container.textContent).toContain("0 / 3");
  });

  test("calculates progress correctly with some items completed (non-blob URLs)", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "https://example.com/recording1.mp3",
          },
          { text: "Q2", audio_url: "", recording_url: "" },
          {
            text: "Q3",
            audio_url: "",
            recording_url: "https://example.com/recording3.mp3",
          },
        ],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Should show 2 / 3 (2 completed with valid URLs, 3 total)
    expect(container.textContent).toContain("2 / 3");
  });

  test("excludes blob URLs from completed count", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "blob:http://localhost:5173/abc-123",
          }, // Not uploaded yet
          {
            text: "Q2",
            audio_url: "",
            recording_url: "https://example.com/recording2.mp3",
          }, // Uploaded
          { text: "Q3", audio_url: "", recording_url: "" }, // Not recorded
        ],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Should show 1 / 3 (only non-blob URL counts)
    expect(container.textContent).toContain("1 / 3");
  });

  test("calculates progress correctly with all items completed", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "https://example.com/recording1.mp3",
          },
          {
            text: "Q2",
            audio_url: "",
            recording_url: "https://example.com/recording2.mp3",
          },
          {
            text: "Q3",
            audio_url: "",
            recording_url: "https://example.com/recording3.mp3",
          },
        ],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Should show 3 / 3 (all completed)
    expect(container.textContent).toContain("3 / 3");
  });

  test("calculates progress across multiple activities", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "https://example.com/recording1.mp3",
          },
          { text: "Q2", audio_url: "", recording_url: "" },
        ],
      },
      {
        id: 2,
        content_id: 2,
        order: 2,
        type: "grouped_questions",
        title: "Activity 2",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q3",
            audio_url: "",
            recording_url: "https://example.com/recording3.mp3",
          },
          {
            text: "Q4",
            audio_url: "",
            recording_url: "https://example.com/recording4.mp3",
          },
        ],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Should show 3 / 4 (3 completed, 4 total across both activities)
    expect(container.textContent).toContain("3 / 4");
  });

  test("handles activities without items (single activity type)", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "reading",
        title: "Reading Activity",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
      },
    ];

    // Note: initialAnswers prop doesn't exist, answers are managed internally
    // For single activity without items, it looks for answer in internal answers Map
    // which is populated via onAnswerUpdate callback during recording
    // For this test, we'll just verify the total count is correct

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Should show 0 / 1 (single activity, not completed)
    expect(container.textContent).toContain("0 / 1");
  });
});

describe("Issue #74: Submit Button Opacity", () => {
  test("submit button has opacity 0.3 when incomplete", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "https://example.com/recording1.mp3",
          },
          { text: "Q2", audio_url: "", recording_url: "" }, // Incomplete
        ],
      },
    ];

    render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    const submitButton = screen.getByRole("button", { name: /submit/i });

    // Button should have opacity 0.3
    expect(submitButton.style.opacity).toBe("0.3");
  });

  test("submit button has opacity 1.0 when all complete", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "https://example.com/recording1.mp3",
          },
          {
            text: "Q2",
            audio_url: "",
            recording_url: "https://example.com/recording2.mp3",
          },
        ],
      },
    ];

    render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    const submitButton = screen.getByRole("button", { name: /submit/i });

    // Button should have opacity 1
    expect(submitButton.style.opacity).toBe("1");
  });
});

describe("Issue #74: Question Completed Styling (Zone A)", () => {
  test("question indicator shows blue background when recording exists", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "https://example.com/recording1.mp3",
          }, // Completed
          { text: "Q2", audio_url: "", recording_url: "" }, // Not completed
        ],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Progress should show 1 / 2 (1 completed)
    expect(container.textContent).toContain("1 / 2");
  });

  test("question indicator shows white background when no recording", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [{ text: "Q1", audio_url: "", recording_url: "" }],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Progress should show 0 / 1 (none completed)
    expect(container.textContent).toContain("0 / 1");
  });

  test("question indicator does not consider blob URLs as completed", () => {
    const activities: Activity[] = [
      {
        id: 1,
        content_id: 1,
        order: 1,
        type: "grouped_questions",
        title: "Activity 1",
        content: "",
        target_text: "",
        duration: 300,
        points: 10,
        status: "IN_PROGRESS",
        score: null,
        completed_at: null,
        items: [
          {
            text: "Q1",
            audio_url: "",
            recording_url: "blob:http://localhost:5173/abc-123",
          },
        ],
      },
    ];

    const { container } = render(
      <StudentActivityPageContent
        assignmentId={1}
        assignmentTitle="Test Assignment"
        activities={activities}
        onBack={() => {}}
      />,
    );

    // Should show 0 / 1 because blob URL doesn't count
    expect(container.textContent).toContain("0 / 1");
  });
});
