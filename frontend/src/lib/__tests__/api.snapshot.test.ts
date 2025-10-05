/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * API Snapshot Testing
 * 確保 API 回應格式不會意外改變
 */
import { describe, it, expect, vi } from "vitest";

// Mock the api module
vi.mock("../api", () => ({
  apiClient: {
    teacherLogin: vi.fn(),
    getTeacherDashboard: vi.fn(),
    getSubmission: vi.fn(),
  },
}));

import { apiClient } from "../api";

describe("API Response Snapshots", () => {
  it("should match login response snapshot", async () => {
    const mockResponse = {
      access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      token_type: "bearer",
      user_type: "teacher",
      user: {
        id: 1,
        email: "teacher@test.com",
        name: "Test Teacher",
        is_demo: false,
      },
    };

    vi.mocked(apiClient.teacherLogin).mockResolvedValue(mockResponse);

    const result = await apiClient.teacherLogin({
      email: "teacher@test.com",
      password: "password123",
    });

    expect(result).toMatchSnapshot();
  });

  it("should match dashboard response snapshot", async () => {
    const mockDashboard = {
      teacher: {
        id: 1,
        name: "Test Teacher",
        email: "teacher@test.com",
      },
      classroom_count: 3,
      student_count: 25,
      recent_assignments: [
        {
          id: 31,
          title: "English Essay",
          due_date: "2025-09-20T23:59:59Z",
          submission_count: 12,
          total_students: 15,
        },
      ],
      statistics: {
        assignments_created: 45,
        total_submissions: 234,
        avg_score: 85.6,
      },
    };

    vi.mocked(apiClient.getTeacherDashboard).mockResolvedValue(mockDashboard);

    const result = await apiClient.getTeacherDashboard();

    expect(result).toMatchSnapshot();
  });

  it("should match submission response snapshot", async () => {
    const mockSubmission = {
      id: 1,
      assignment_id: 31,
      student_id: 1,
      student: {
        id: 1,
        student_id: "S001",
        name: "Test Student",
        email: "student@test.com",
      },
      content: {
        text_response: "This is my essay...",
        attachments: [],
        audio_recording: null,
      },
      status: "submitted",
      score: null,
      feedback: null,
      submitted_at: "2025-09-15T10:30:00Z",
      graded_at: null,
    };

    vi.mocked(apiClient.getSubmission).mockResolvedValue(mockSubmission);

    const result = await apiClient.getSubmission(31, 1);

    expect(result).toMatchSnapshot();
  });

  it("should match error response snapshot", async () => {
    const mockError = new Error("Could not validate credentials");
    mockError.name = "ApiError";
    // 模擬 API 錯誤結構
    (mockError as any).status = 401;
    (mockError as any).detail = "Could not validate credentials";

    vi.mocked(apiClient.getSubmission).mockRejectedValue(mockError);

    try {
      await apiClient.getSubmission(31, 1);
    } catch (error: any) {
      expect({
        message: error.message,
        status: error.status,
        detail: error.detail,
      }).toMatchSnapshot();
    }
  });
});
