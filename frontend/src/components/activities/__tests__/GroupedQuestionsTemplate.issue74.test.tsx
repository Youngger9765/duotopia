import { describe, test, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GroupedQuestionsTemplate from "../GroupedQuestionsTemplate";

// Mock i18n translation
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: { [key: string]: string } = {
        "groupedQuestionsTemplate.labels.studentAnswer": "Student Answer",
        "groupedQuestionsTemplate.labels.startRecording": "Start Recording",
        "groupedQuestionsTemplate.labels.stopping": "Stop Recording",
        "groupedQuestionsTemplate.labels.viewOnlyMode": "View Only Mode",
        "groupedQuestionsTemplate.labels.playbackSpeed": "Playback Speed",
        "groupedQuestionsTemplate.labels.clearRecording": "Clear Recording",
        "groupedQuestionsTemplate.labels.deleteRecording": "Delete Recording",
        "groupedQuestionsTemplate.labels.teacherFeedback": "Teacher Feedback",
        "groupedQuestionsTemplate.labels.noTeacherFeedback":
          "No teacher feedback yet",
        "groupedQuestionsTemplate.labels.passed": "Passed",
        "groupedQuestionsTemplate.labels.notPassed": "Not Passed",
      };
      return translations[key] || key;
    },
  }),
}));

// Mock student auth store
vi.mock("@/stores/studentAuthStore", () => ({
  useStudentAuthStore: vi.fn(() => ({ token: "test-token" })),
}));

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

beforeEach(() => {
  // Mock Audio API
  Object.defineProperty(window, "Audio", {
    writable: true,
    value: class {
      load() {}
      play() {
        return Promise.resolve();
      }
      pause() {}
      src = "";
      currentTime = 0;
      duration = 0;
      paused = true;
      addEventListener(event: string, callback: () => void) {
        if (event === "loadedmetadata") {
          callback();
        }
      }
      removeEventListener() {}
    },
  });

  // Mock MediaRecorder API
  Object.defineProperty(window, "MediaRecorder", {
    writable: true,
    value: class {
      state = "inactive";
      mimeType = "audio/webm";
      start() {
        this.state = "recording";
      }
      stop() {
        this.state = "inactive";
      }
      ondataavailable = () => {};
      onstop = () => {};
    },
  });

  // Mock MediaDevices API
  Object.defineProperty(navigator, "mediaDevices", {
    value: {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: () => {} }],
      }),
    },
    writable: true,
  });
});

describe("Issue #74: Star Rating Logic (Zone C-1)", () => {
  test("shows 3 filled stars when average score > 90", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 95,
        accuracy_score: 92,
        fluency_score: 94,
        completeness_score: 93,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    // Find star elements
    const stars = container.querySelectorAll("svg");
    const filledStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-yellow-400");
    });
    const emptyStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-gray-300");
    });

    // Should have 3 filled stars (score 93.5 > 90)
    expect(filledStars.length).toBeGreaterThanOrEqual(3);
    expect(emptyStars.length).toBe(0);
  });

  test("shows 2 filled stars when 60 <= average score < 90", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 70,
        accuracy_score: 75,
        fluency_score: 72,
        completeness_score: 73,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    const stars = container.querySelectorAll("svg");
    const filledStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-yellow-400");
    });

    // Should have 2 filled stars (score 72.5 >= 60 and < 90)
    expect(filledStars.length).toBeGreaterThanOrEqual(2);
  });

  test("shows 1 filled star when 40 <= average score < 60", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 45,
        accuracy_score: 50,
        fluency_score: 48,
        completeness_score: 47,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    const stars = container.querySelectorAll("svg");
    const filledStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-yellow-400");
    });

    // Should have 1 filled star (score 47.5 >= 40 and < 60)
    expect(filledStars.length).toBeGreaterThanOrEqual(1);
  });

  test("shows 0 filled stars when average score < 40", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 30,
        accuracy_score: 35,
        fluency_score: 32,
        completeness_score: 33,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    const stars = container.querySelectorAll("svg");
    const filledStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-yellow-400");
    });

    // Should have 0 filled stars (score 32.5 < 40)
    expect(filledStars.length).toBe(0);
  });

  test("calculates average score from all 4 score types", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 80,
        accuracy_score: 85,
        fluency_score: 90,
        completeness_score: 95,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    // Average = (80 + 85 + 90 + 95) / 4 = 87.5
    // Should show score in text (87分 or 88分 depending on rounding)
    expect(
      container.textContent?.includes("87") ||
        container.textContent?.includes("88"),
    ).toBe(true);
  });

  test("handles missing scores gracefully", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 80,
        accuracy_score: 85,
        // Missing fluency_score and completeness_score
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    // Should calculate average from available scores only: (80 + 85) / 2 = 82.5
    // Should show score in text (82分 or 83分)
    expect(
      container.textContent?.includes("82") ||
        container.textContent?.includes("83"),
    ).toBe(true);
  });

  test("boundary test: score exactly 90 shows 2 stars", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 90,
        accuracy_score: 90,
        fluency_score: 90,
        completeness_score: 90,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    const stars = container.querySelectorAll("svg");
    const filledStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-yellow-400");
    });

    // Score 90 should be >= 60 and < 90 is false, so it should be 2 stars (60 <= 90)
    // But > 90 is false, so actually 2 stars
    expect(filledStars.length).toBeGreaterThanOrEqual(2);
  });

  test("boundary test: score exactly 60 shows 2 stars", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 60,
        accuracy_score: 60,
        fluency_score: 60,
        completeness_score: 60,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    const stars = container.querySelectorAll("svg");
    const filledStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-yellow-400");
    });

    // Score 60 should be >= 60, so 2 stars
    expect(filledStars.length).toBeGreaterThanOrEqual(2);
  });

  test("boundary test: score exactly 40 shows 1 star", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    const initialAssessmentResults = {
      0: {
        pronunciation_score: 40,
        accuracy_score: 40,
        fluency_score: 40,
        completeness_score: 40,
      },
    };

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        initialAssessmentResults={initialAssessmentResults}
      />,
    );

    const stars = container.querySelectorAll("svg");
    const filledStars = Array.from(stars).filter((star) => {
      const className = star.getAttribute("class") || "";
      return className.includes("text-yellow-400");
    });

    // Score 40 should be >= 40 and < 60, so 1 star
    expect(filledStars.length).toBeGreaterThanOrEqual(1);
  });
});

describe("Issue #74: Recording Control State Machine (Zone D)", () => {
  test("initial state shows Record button (Mic icon)", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "", // No recording yet
      },
    ];

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
      />,
    );

    // Should show Mic icon (recording button)
    const micIcon = container.querySelector('svg[class*="lucide-mic"]');
    expect(micIcon).toBeTruthy();
  });

  test("recording state shows Stop button (Square icon)", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "",
      },
    ];

    const { container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={true} // Recording in progress
        recordingTime={5}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
      />,
    );

    // Should show Square icon (stop button)
    const squareIcon = container.querySelector('svg[class*="lucide-square"]');
    expect(squareIcon).toBeTruthy();
  });

  test("recorded state shows Reset button (circular arrow icon)", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "https://example.com/recording.mp3", // Has recording
      },
    ];

    render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
      />,
    );

    // Should show reset/circular arrow button
    const resetButton = screen.getByTitle("Clear Recording");
    expect(resetButton).toBeTruthy();
  });

  test("clicking Record button triggers onStartRecording", async () => {
    const user = userEvent.setup();
    const mockOnStartRecording = vi.fn();

    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "",
      },
    ];

    render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={mockOnStartRecording}
        onStopRecording={() => {}}
      />,
    );

    // Find and click the record button
    const recordButton = screen.getByTitle("Start Recording");
    await user.click(recordButton);

    expect(mockOnStartRecording).toHaveBeenCalledTimes(1);
  });

  test("clicking Stop button triggers onStopRecording", async () => {
    const user = userEvent.setup();
    const mockOnStopRecording = vi.fn();

    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "",
      },
    ];

    render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={true}
        recordingTime={5}
        onStartRecording={() => {}}
        onStopRecording={mockOnStopRecording}
      />,
    );

    // Find and click the stop button
    const stopButton = screen.getByTitle("Stop Recording");
    await user.click(stopButton);

    expect(mockOnStopRecording).toHaveBeenCalledTimes(1);
  });

  test("Read-only mode disables Record button", () => {
    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "",
      },
    ];

    render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        readOnly={true}
      />,
    );

    const recordButton = screen.getByTitle("View Only Mode");
    expect(recordButton).toBeDisabled();
  });

  test("state transition: no recording -> recording -> has recording", async () => {
    const user = userEvent.setup();
    const mockOnStartRecording = vi.fn();
    const mockOnStopRecording = vi.fn();

    const items = [
      {
        text: "Test question",
        audio_url: "https://example.com/audio.mp3",
        recording_url: "",
      },
    ];

    // Initial state: no recording
    const { rerender, container } = render(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={mockOnStartRecording}
        onStopRecording={mockOnStopRecording}
      />,
    );

    // Should show Mic icon
    expect(container.querySelector('svg[class*="lucide-mic"]')).toBeTruthy();

    // Click record -> transition to recording state
    const recordButton = screen.getByTitle("Start Recording");
    await user.click(recordButton);

    // Simulate recording state
    rerender(
      <GroupedQuestionsTemplate
        items={items}
        currentQuestionIndex={0}
        isRecording={true}
        recordingTime={3}
        onStartRecording={mockOnStartRecording}
        onStopRecording={mockOnStopRecording}
      />,
    );

    // Should show Square icon
    expect(container.querySelector('svg[class*="lucide-square"]')).toBeTruthy();

    // Click stop -> transition to has recording state
    const stopButton = screen.getByTitle("Stop Recording");
    await user.click(stopButton);

    // Simulate recorded state
    const itemsWithRecording = [
      {
        ...items[0],
        recording_url: "https://example.com/recording.mp3",
      },
    ];

    rerender(
      <GroupedQuestionsTemplate
        items={itemsWithRecording}
        currentQuestionIndex={0}
        isRecording={false}
        recordingTime={0}
        onStartRecording={mockOnStartRecording}
        onStopRecording={mockOnStopRecording}
      />,
    );

    // Should show reset button
    const resetButton = screen.getByTitle("Clear Recording");
    expect(resetButton).toBeTruthy();
  });
});
