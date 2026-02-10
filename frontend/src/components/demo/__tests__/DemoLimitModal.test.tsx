import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DemoLimitModal } from "../DemoLimitModal";

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "demo.limitReached.title": "今日免費試用次數已達上限",
        "demo.limitReached.description": `您今日已使用完 ${opts?.limit ?? 60} 次免費語音練習機會。`,
        "demo.limitReached.ctaTitle": "註冊帳號即可無限使用！",
        "demo.limitReached.ctaDescription": "完全免費，立即解鎖所有功能",
        "demo.limitReached.resetInfo": `或等待 ${opts?.resetTime ?? ""} 後重置免費額度`,
        "demo.limitReached.login": "登入",
        "demo.limitReached.register": "免費註冊",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("DemoLimitModal", () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    resetAt: "2025-01-02T16:00:00Z",
    limit: 60,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render when open", () => {
    render(<DemoLimitModal {...defaultProps} />);
    expect(screen.getByText("今日免費試用次數已達上限")).toBeInTheDocument();
  });

  it("should display limit info", () => {
    render(<DemoLimitModal {...defaultProps} />);
    expect(
      screen.getByText(/您今日已使用完 60 次免費語音練習機會/),
    ).toBeInTheDocument();
  });

  it("should show registration CTA", () => {
    render(<DemoLimitModal {...defaultProps} />);
    expect(screen.getByText("註冊帳號即可無限使用！")).toBeInTheDocument();
    expect(screen.getByText("完全免費，立即解鎖所有功能")).toBeInTheDocument();
  });

  it("should navigate to /register on register click", () => {
    render(<DemoLimitModal {...defaultProps} />);
    fireEvent.click(screen.getByText("免費註冊"));
    expect(defaultProps.onClose).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/register");
  });

  it("should navigate to /login on login click", () => {
    render(<DemoLimitModal {...defaultProps} />);
    fireEvent.click(screen.getByText("登入"));
    expect(defaultProps.onClose).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });

  it("should not render when closed", () => {
    render(<DemoLimitModal {...defaultProps} open={false} />);
    expect(
      screen.queryByText("今日免費試用次數已達上限"),
    ).not.toBeInTheDocument();
  });

  it("should display formatted reset time", () => {
    render(<DemoLimitModal {...defaultProps} />);
    // The reset time display should appear somewhere in the text
    expect(screen.getByText(/後重置免費額度/)).toBeInTheDocument();
  });
});
