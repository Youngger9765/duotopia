import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import TeacherLayout from "../TeacherLayout";

// Mock API client
vi.mock("@/lib/api", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

// Mock DigitalTeachingToolbar component
vi.mock("@/components/teachingTools/DigitalTeachingToolbar", () => ({
  default: () => (
    <div data-testid="digital-teaching-toolbar">DigitalTeachingToolbar</div>
  ),
}));

// Mock LanguageSwitcher
vi.mock("@/components/LanguageSwitcher", () => ({
  LanguageSwitcher: () => <div>LanguageSwitcher</div>,
}));

describe("TeacherLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    const mockProfile = {
      id: 1,
      email: "teacher@example.com",
      name: "Test Teacher",
      is_demo: false,
      is_active: true,
    };
    localStorage.setItem("teacherProfile", JSON.stringify(mockProfile));
  });

  it("should render DigitalTeachingToolbar", async () => {
    const { apiClient } = await import("@/lib/api");
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { enablePayment: true, environment: "development" },
    });

    render(
      <BrowserRouter>
        <TeacherLayout>
          <div>Content</div>
        </TeacherLayout>
      </BrowserRouter>,
    );

    await waitFor(() => {
      // Teachers SHOULD have access to teaching tools
      expect(
        screen.getByTestId("digital-teaching-toolbar"),
      ).toBeInTheDocument();
    });
  });

  it("should render teacher navigation", async () => {
    const { apiClient } = await import("@/lib/api");
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { enablePayment: true, environment: "development" },
    });

    render(
      <BrowserRouter>
        <TeacherLayout>
          <div>Content</div>
        </TeacherLayout>
      </BrowserRouter>,
    );

    await waitFor(() => {
      // Teachers should have their own navigation
      expect(screen.getByText("Test Teacher")).toBeInTheDocument();
    });
  });
});
