import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ProtectedRoute } from "../ProtectedRoute";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

vi.mock("@/stores/teacherAuthStore");

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("應該在已登入時渲染子元素", () => {
    vi.mocked(useTeacherAuthStore).mockReturnValue(true);

    render(
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>,
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("應該在未登入時轉到登入頁", () => {
    vi.mocked(useTeacherAuthStore).mockReturnValue(false);

    render(
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/teacher/login" element={<div>Login Page</div>} />
        </Routes>
      </BrowserRouter>,
    );

    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });
});
