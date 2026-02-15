import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AssignTeacherDialog } from "../AssignTeacherDialog";
import { apiClient, ApiError } from "@/lib/api";
import { toast } from "sonner";

// Mock dependencies
vi.mock("@/lib/api", () => ({
  apiClient: {
    getOrganizationTeachers: vi.fn(),
    addTeacherToSchool: vi.fn(),
    assignTeacherToClassroom: vi.fn(),
    inviteTeacherToOrganization: vi.fn(),
  },
  ApiError: class extends Error {
    status: number;
    detail: string;
    constructor(status: number, detail: string) {
      super(detail);
      this.name = "ApiError";
      this.status = status;
      this.detail = detail;
    }
  },
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/utils/errorLogger", () => ({
  logError: vi.fn(),
}));

const mockSchoolTeachers = [
  { id: 1, name: "王老師", email: "wang@school.com", roles: ["teacher"] },
  {
    id: 2,
    name: "李主任",
    email: "li@school.com",
    roles: ["school_director"],
  },
];

const mockOrgTeachers = [
  {
    id: 1,
    name: "王老師",
    email: "wang@school.com",
    role: "teacher",
    is_active: true,
  },
  {
    id: 2,
    name: "李主任",
    email: "li@school.com",
    role: "school_director",
    is_active: true,
  },
  {
    id: 3,
    name: "張教授",
    email: "zhang@org.com",
    role: "teacher",
    is_active: true,
  },
  {
    id: 4,
    name: "陳老師",
    email: "chen@org.com",
    role: "teacher",
    is_active: false,
  },
];

const mockClassroom = {
  id: "10",
  name: "一年一班",
  teacher_name: null,
  teacher_id: null,
};

const mockClassroomWithTeacher = {
  id: "10",
  name: "一年一班",
  teacher_name: "王老師",
  teacher_id: 1,
};

describe("AssignTeacherDialog", () => {
  const mockOnOpenChange = vi.fn();
  const mockOnSuccess = vi.fn();

  const defaultProps = {
    open: true,
    onOpenChange: mockOnOpenChange,
    classroom: mockClassroom,
    teachers: mockSchoolTeachers,
    organizationId: "org-1",
    schoolId: "school-1",
    onSuccess: mockOnSuccess,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.getOrganizationTeachers).mockResolvedValue(
      mockOrgTeachers,
    );
  });

  const renderComponent = (props = {}) => {
    return render(<AssignTeacherDialog {...defaultProps} {...props} />);
  };

  it("should render dialog title for assigning teacher", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("指派導師")).toBeInTheDocument();
    });
  });

  it("should render dialog title for changing teacher when classroom already has one", async () => {
    renderComponent({ classroom: mockClassroomWithTeacher });

    await waitFor(() => {
      expect(screen.getByText("更換導師")).toBeInTheDocument();
    });
  });

  it("should display search input", async () => {
    renderComponent();

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("輸入姓名或 Email 搜尋..."),
      ).toBeInTheDocument();
    });
  });

  it("should fetch org teachers on open", async () => {
    renderComponent();

    await waitFor(() => {
      expect(apiClient.getOrganizationTeachers).toHaveBeenCalledWith("org-1");
    });
  });

  it("should not fetch org teachers when dialog is closed", () => {
    renderComponent({ open: false });

    expect(apiClient.getOrganizationTeachers).not.toHaveBeenCalled();
  });

  it("should display school teachers grouped under school heading", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
      expect(screen.getByText("李主任")).toBeInTheDocument();
      expect(screen.getByText(/分校教師/)).toBeInTheDocument();
    });
  });

  it("should display org-only teachers (not in school) under org heading", async () => {
    renderComponent();

    await waitFor(() => {
      // 張教授 is only in org (id=3), not in school teachers
      expect(screen.getByText("張教授")).toBeInTheDocument();
      expect(screen.getByText(/機構教師 - 尚未加入此分校/)).toBeInTheDocument();
    });
  });

  it("should filter out inactive org teachers", async () => {
    renderComponent();

    await waitFor(() => {
      // 陳老師 (id=4) is inactive, should not appear
      expect(screen.queryByText("陳老師")).not.toBeInTheDocument();
    });
  });

  it("should deduplicate teachers between school and org lists", async () => {
    renderComponent();

    await waitFor(() => {
      // 王老師 is in both school and org list, should only appear once under school
      const wangElements = screen.getAllByText("王老師");
      expect(wangElements).toHaveLength(1);
    });
  });

  it("should filter teachers by search query", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, { target: { value: "zhang" } });

    await waitFor(() => {
      expect(screen.getByText("張教授")).toBeInTheDocument();
      expect(screen.queryByText("王老師")).not.toBeInTheDocument();
      expect(screen.queryByText("李主任")).not.toBeInTheDocument();
    });
  });

  it("should filter teachers by name in Chinese", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, { target: { value: "張" } });

    await waitFor(() => {
      expect(screen.getByText("張教授")).toBeInTheDocument();
      expect(screen.queryByText("王老師")).not.toBeInTheDocument();
    });
  });

  it("should show no-result message when search has no matches", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, { target: { value: "nonexistent" } });

    await waitFor(() => {
      expect(screen.getByText(/找不到符合/)).toBeInTheDocument();
    });
  });

  it("should show invite option when email search has no matches", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, {
      target: { value: "newteacher@email.com" },
    });

    await waitFor(() => {
      expect(
        screen.getByText(/邀請 newteacher@email.com 為新教師/),
      ).toBeInTheDocument();
    });
  });

  it("should assign school teacher to classroom on click", async () => {
    vi.mocked(apiClient.assignTeacherToClassroom).mockResolvedValue({});

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("王老師"));

    await waitFor(() => {
      expect(apiClient.assignTeacherToClassroom).toHaveBeenCalledWith(10, 1);
      expect(toast.success).toHaveBeenCalledWith(
        "已指派 王老師 為 一年一班 的導師",
      );
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  it("should add org teacher to school then assign to classroom", async () => {
    vi.mocked(apiClient.addTeacherToSchool).mockResolvedValue({});
    vi.mocked(apiClient.assignTeacherToClassroom).mockResolvedValue({});

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("張教授")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("張教授"));

    await waitFor(() => {
      expect(apiClient.addTeacherToSchool).toHaveBeenCalledWith("school-1", {
        teacher_id: 3,
        roles: ["teacher"],
      });
      expect(apiClient.assignTeacherToClassroom).toHaveBeenCalledWith(10, 3);
      expect(toast.success).toHaveBeenCalled();
    });
  });

  it("should handle 409 when adding org teacher already in school", async () => {
    vi.mocked(apiClient.addTeacherToSchool).mockRejectedValue(
      new ApiError(409, "Already exists"),
    );
    vi.mocked(apiClient.assignTeacherToClassroom).mockResolvedValue({});

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("張教授")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("張教授"));

    await waitFor(() => {
      // Should still proceed to assign despite 409
      expect(apiClient.assignTeacherToClassroom).toHaveBeenCalledWith(10, 3);
      expect(toast.success).toHaveBeenCalled();
    });
  });

  it("should show error when adding org teacher to school fails with non-409", async () => {
    vi.mocked(apiClient.addTeacherToSchool).mockRejectedValue(
      new ApiError(500, "Server error"),
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("張教授")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("張教授"));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("將教師加入分校失敗");
      expect(apiClient.assignTeacherToClassroom).not.toHaveBeenCalled();
    });
  });

  it("should show unassign option when classroom has a teacher", async () => {
    renderComponent({ classroom: mockClassroomWithTeacher });

    await waitFor(() => {
      expect(screen.getByText("取消導師指派")).toBeInTheDocument();
    });
  });

  it("should not show unassign option when classroom has no teacher", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    expect(screen.queryByText("取消導師指派")).not.toBeInTheDocument();
  });

  it("should unassign teacher on click", async () => {
    vi.mocked(apiClient.assignTeacherToClassroom).mockResolvedValue({});

    renderComponent({ classroom: mockClassroomWithTeacher });

    await waitFor(() => {
      expect(screen.getByText("取消導師指派")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("取消導師指派"));

    await waitFor(() => {
      expect(apiClient.assignTeacherToClassroom).toHaveBeenCalledWith(10, null);
      expect(toast.success).toHaveBeenCalledWith("已取消導師指派");
    });
  });

  it("should show invite form when invite button is clicked", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, {
      target: { value: "newteacher@email.com" },
    });

    await waitFor(() => {
      const inviteButton = screen.getByText(
        /邀請 newteacher@email.com 為新教師/,
      );
      fireEvent.click(inviteButton);
    });

    await waitFor(() => {
      expect(screen.getByText("邀請新教師加入機構")).toBeInTheDocument();
      expect(screen.getByLabelText(/姓名/)).toBeInTheDocument();
    });
  });

  it("should invite and assign new teacher", async () => {
    vi.mocked(apiClient.inviteTeacherToOrganization).mockResolvedValue({
      teacher_id: 99,
    });
    vi.mocked(apiClient.addTeacherToSchool).mockResolvedValue({});
    vi.mocked(apiClient.assignTeacherToClassroom).mockResolvedValue({});

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    // Search for email
    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, {
      target: { value: "newteacher@email.com" },
    });

    await waitFor(() => {
      fireEvent.click(screen.getByText(/邀請 newteacher@email.com 為新教師/));
    });

    // Fill in name and submit
    await waitFor(() => {
      const nameInput = screen.getByPlaceholderText("請輸入教師姓名");
      fireEvent.change(nameInput, { target: { value: "新老師" } });
    });

    fireEvent.click(screen.getByText("邀請並指派為導師"));

    await waitFor(() => {
      expect(apiClient.inviteTeacherToOrganization).toHaveBeenCalledWith(
        "org-1",
        {
          email: "newteacher@email.com",
          name: "新老師",
          role: "teacher",
        },
      );
      expect(apiClient.addTeacherToSchool).toHaveBeenCalledWith("school-1", {
        teacher_id: 99,
        roles: ["teacher"],
      });
      expect(apiClient.assignTeacherToClassroom).toHaveBeenCalledWith(10, 99);
      expect(toast.success).toHaveBeenCalled();
    });
  });

  it("should handle 409 when inviting teacher already in org", async () => {
    vi.mocked(apiClient.inviteTeacherToOrganization).mockRejectedValue(
      new ApiError(409, "Already in org"),
    );
    // First call (useEffect) returns original list without new teacher;
    // Second call (during invite 409 recovery) returns list with the teacher
    vi.mocked(apiClient.getOrganizationTeachers)
      .mockResolvedValueOnce(mockOrgTeachers)
      .mockResolvedValueOnce([
        ...mockOrgTeachers,
        {
          id: 99,
          name: "新老師",
          email: "newteacher@email.com",
          role: "teacher",
          is_active: true,
        },
      ]);
    vi.mocked(apiClient.addTeacherToSchool).mockResolvedValue({});
    vi.mocked(apiClient.assignTeacherToClassroom).mockResolvedValue({});

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, {
      target: { value: "newteacher@email.com" },
    });

    await waitFor(() => {
      expect(
        screen.getByText(/邀請 newteacher@email.com 為新教師/),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/邀請 newteacher@email.com 為新教師/));

    await waitFor(() => {
      const nameInput = screen.getByPlaceholderText("請輸入教師姓名");
      fireEvent.change(nameInput, { target: { value: "新老師" } });
    });

    fireEvent.click(screen.getByText("邀請並指派為導師"));

    await waitFor(() => {
      // Should still proceed: find existing teacher and assign
      expect(apiClient.assignTeacherToClassroom).toHaveBeenCalledWith(10, 99);
      expect(toast.success).toHaveBeenCalled();
    });
  });

  it("should clear search when X button is clicked", async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("王老師")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("輸入姓名或 Email 搜尋...");
    fireEvent.change(searchInput, { target: { value: "test" } });

    // Click the clear (X) button - find by its SVG class
    const xButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.querySelector('[class*="lucide-x"]'));

    expect(xButtons.length).toBeGreaterThan(0);
    fireEvent.click(xButtons[0]);

    // The search input should be cleared after clicking X
    expect(searchInput).toHaveValue("");
  });

  it("should return null when classroom is null", () => {
    const { container } = render(
      <AssignTeacherDialog {...defaultProps} classroom={null} />,
    );

    expect(container.innerHTML).toBe("");
  });

  it("should show current teacher indicator", async () => {
    renderComponent({ classroom: mockClassroomWithTeacher });

    await waitFor(() => {
      expect(screen.getByText("(目前導師)")).toBeInTheDocument();
    });
  });
});
