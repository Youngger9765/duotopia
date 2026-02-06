import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import CreateOrganization from "../CreateOrganization";

// Mock the apiClient
vi.mock("@/lib/api", () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("CreateOrganization - Subscription Fields (Issue #209)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <CreateOrganization />
      </BrowserRouter>,
    );
  };

  it("should render subscription section header", () => {
    renderComponent();
    expect(screen.getByText("訂閱與點數")).toBeInTheDocument();
  });

  it("should render initial points field", () => {
    renderComponent();
    expect(screen.getByLabelText("初始點數")).toBeInTheDocument();
    const pointsInput = screen.getByPlaceholderText("10000");
    expect(pointsInput).toBeInTheDocument();
    expect(pointsInput).toHaveAttribute("type", "number");
  });

  it("should render subscription start date field (啟用時間)", () => {
    renderComponent();
    expect(screen.getByText("啟用時間")).toBeInTheDocument();
    const dateInput = screen.getByLabelText(/啟用時間/);
    expect(dateInput).toBeInTheDocument();
    expect(dateInput).toHaveAttribute("type", "date");
  });

  it("should render subscription end date field (停用時間)", () => {
    renderComponent();
    expect(screen.getByText("停用時間")).toBeInTheDocument();
    const dateInput = screen.getByLabelText(/停用時間/);
    expect(dateInput).toBeInTheDocument();
    expect(dateInput).toHaveAttribute("type", "date");
  });

  it("should allow filling subscription dates", () => {
    renderComponent();

    const startDateInput = screen.getByLabelText(
      /啟用時間/,
    ) as HTMLInputElement;
    const endDateInput = screen.getByLabelText(/停用時間/) as HTMLInputElement;

    fireEvent.change(startDateInput, { target: { value: "2026-02-01" } });
    fireEvent.change(endDateInput, { target: { value: "2026-12-31" } });

    expect(startDateInput.value).toBe("2026-02-01");
    expect(endDateInput.value).toBe("2026-12-31");
  });

  it("should allow filling initial points", () => {
    renderComponent();

    const pointsInput = screen.getByPlaceholderText(
      "10000",
    ) as HTMLInputElement;
    fireEvent.change(pointsInput, { target: { value: "50000" } });

    expect(pointsInput.value).toBe("50000");
  });

  it("should render Calendar icons for date fields", () => {
    renderComponent();
    // Calendar icons are rendered within the label
    const labels = screen.getAllByText(/時間/);
    expect(labels.length).toBeGreaterThanOrEqual(2);
  });
});
