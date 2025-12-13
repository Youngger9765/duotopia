/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the API_URL before importing apiClient
vi.mock("@/config/api", () => ({
  API_URL: import.meta.env.VITE_API_URL,
}));

import { apiClient } from "../api";

// Mock fetch globally
global.fetch = vi.fn();

describe("apiClient.createContent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset localStorage
    localStorage.clear();

    // Set up proper auth storage structure (matches what apiClient.getToken() expects)
    localStorage.setItem(
      "teacher-auth-storage",
      JSON.stringify({
        state: {
          token: "test-token",
          user: { id: 1, name: "Test Teacher", email: "test@example.com" },
          isAuthenticated: true,
        },
        version: 0,
      }),
    );
  });

  it("should create content with correct API call", async () => {
    const mockResponse = {
      id: 1,
      type: "EXAMPLE_SENTENCES",
      title: "朗讀錄音練習",
      lesson_id: 1,
    };

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await apiClient.createContent(1, {
      type: "EXAMPLE_SENTENCES",
      title: "朗讀錄音練習",
      items: [],
    });

    // Verify fetch was called correctly
    const fetchCall = (global.fetch as any).mock.calls[0];
    expect(fetchCall[0]).toContain("/api/teachers/lessons/1/contents");
    expect(fetchCall[1]).toMatchObject({
      method: "POST",
      headers: expect.objectContaining({
        "Content-Type": "application/json",
        Authorization: "Bearer test-token",
      }),
      body: JSON.stringify({
        type: "EXAMPLE_SENTENCES",
        title: "朗讀錄音練習",
        items: [],
      }),
    });

    expect(result).toEqual(mockResponse);
  });

  it("should handle content creation error", async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Invalid content type" }),
    });

    await expect(
      apiClient.createContent(1, {
        type: "invalid_type",
        title: "Test",
        items: [],
      }),
    ).rejects.toThrow("Invalid content type");
  });
});
