import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the API_URL
vi.mock("@/config/api", () => ({
  API_URL: import.meta.env.VITE_API_URL,
}));

import { apiClient, ApiError } from "../api";

global.fetch = vi.fn() as unknown as typeof fetch;

describe("API Error Handling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("🔴 should throw ApiError with status and detail", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Invalid input data" }),
    } as Response);

    try {
      await apiClient.get("/api/test");
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(400);
      expect((err as ApiError).detail).toBe("Invalid input data");
    }
  });

  it("🔴 should handle 401 unauthorized errors", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Unauthorized access" }),
    } as Response);

    try {
      await apiClient.get("/api/protected");
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).isUnauthorized()).toBe(true);
      expect((err as ApiError).status).toBe(401);
    }
  });

  it("🔴 should handle 404 not found errors", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Resource not found" }),
    } as Response);

    try {
      await apiClient.get("/api/missing");
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).isNotFound()).toBe(true);
      expect((err as ApiError).detail).toBe("Resource not found");
    }
  });

  it("🔴 should handle validation errors with field details", async () => {
    const validationError = {
      detail: "Validation failed",
      errors: {
        email: "Invalid email format",
        password: "Password too short",
      },
    };

    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => validationError,
    } as Response);

    try {
      await apiClient.post("/api/register", {
        email: "invalid",
        password: "123",
      });
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).isValidationError()).toBe(true);
      expect((err as ApiError).getValidationErrors()).toEqual({
        email: "Invalid email format",
        password: "Password too short",
      });
    }
  });

  it("🔴 should handle Pydantic validation error array format (422)", async () => {
    const pydanticErrors = {
      detail: [
        {
          type: "missing",
          loc: ["body", "students", 0, "birthdate"],
          msg: "Field required",
          input: { name: "Test Student" },
          url: "https://errors.pydantic.dev/2.6/v/missing",
        },
        {
          type: "string_type",
          loc: ["body", "students", 1, "name"],
          msg: "Input should be a valid string",
          input: 123,
          url: "https://errors.pydantic.dev/2.6/v/string_type",
        },
      ],
    };

    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => pydanticErrors,
    } as Response);

    try {
      await apiClient.post("/api/schools/s1/students/batch-import", {
        students: [],
      });
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).isValidationError()).toBe(true);
      // message should be formatted as "field: msg; field: msg"
      expect((err as ApiError).message).toBe(
        "birthdate: Field required; name: Input should be a valid string",
      );
    }
  });

  it("🔴 should handle Pydantic error array with missing loc/msg", async () => {
    const pydanticErrors = {
      detail: [
        { type: "missing" },
        { type: "value_error", msg: "Custom error" },
      ],
    };

    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => pydanticErrors,
    } as Response);

    try {
      await apiClient.post("/api/test", {});
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      // missing loc+msg → fallback "驗證錯誤"; missing loc → use msg directly
      expect((err as ApiError).message).toBe("驗證錯誤; Custom error");
    }
  });

  it("✅ should handle network errors gracefully", async () => {
    vi.mocked(global.fetch).mockRejectedValue(
      new Error("Network connection failed"),
    );

    try {
      await apiClient.get("/api/test");
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(0); // Network errors have status 0
      expect((err as ApiError).detail).toContain("Network connection failed");
    }
  });

  it("✅ should preserve original error data", async () => {
    const originalError = {
      detail: "Payment failed",
      code: "PAYMENT_DECLINED",
      transaction_id: "txn_12345",
    };

    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 402,
      json: async () => originalError,
    } as Response);

    try {
      await apiClient.post("/api/payment", { amount: 100 });
      expect.fail("Should have thrown an error");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).getErrorCode()).toBe("PAYMENT_DECLINED");
      expect((err as ApiError).originalError).toEqual(originalError);
    }
  });
});
