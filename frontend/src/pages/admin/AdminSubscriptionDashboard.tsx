import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Users,
  Crown,
  Search,
  TrendingUp,
  DollarSign,
  CheckCircle,
  XCircle,
  Edit,
  Loader2,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import { apiClient } from "@/lib/api";

// Types
interface TeacherSubscriptionInfo {
  teacher_id: number;
  teacher_name: string;
  teacher_email: string;
  current_subscription: {
    period_id: number;
    plan_name: string;
    quota_total: number;
    quota_used: number;
    end_date: string;
    status: string;
  } | null;
}

interface SubscriptionPeriod {
  id: number;
  plan_name: string;
  quota_total: number;
  quota_used: number;
  start_date: string;
  end_date: string;
  status: string;
  payment_method: string;
  payment_status: string;
  amount_paid?: number;
}

interface EditHistoryRecord {
  action: string;
  admin_email: string;
  admin_name: string;
  admin_id: number;
  timestamp: string;
  reason: string;
  changes: {
    // For create action: direct values
    plan_name?: string | { from: string; to: string };
    quota_total?: number | { from: number; to: number };
    end_date?: string | { from: string; to: string };
    status?: string | { from: string; to: string };
  };
}

interface AdminStats {
  total_teachers: number;
  active_subscriptions: number;
  monthly_revenue: number;
  quota_usage_percentage: number;
}

interface ApiError {
  response?: {
    status?: number;
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === "object" &&
    error !== null &&
    ("response" in error || "message" in error)
  );
}

export default function AdminSubscriptionDashboard() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [teachers, setTeachers] = useState<TeacherSubscriptionInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [expandedTeacherId, setExpandedTeacherId] = useState<number | null>(
    null,
  );
  const [expandedPeriodId, setExpandedPeriodId] = useState<number | null>(null);
  const [teacherPeriods, setTeacherPeriods] = useState<
    Record<number, SubscriptionPeriod[]>
  >({});
  const [periodHistory, setPeriodHistory] = useState<
    Record<number, EditHistoryRecord[]>
  >({});

  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedTeacher, setSelectedTeacher] =
    useState<TeacherSubscriptionInfo | null>(null);
  const [editForm, setEditForm] = useState({
    action: "extend", // extend, cancel, edit
    plan_name: "",
    end_date: "",
    quota_total: undefined as number | undefined,
    reason: "",
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, teachersRes] = await Promise.all([
        apiClient.get("/api/admin/subscription/stats"),
        apiClient.get("/api/admin/subscription/all-teachers"),
      ]);

      setStats(statsRes as AdminStats);
      setTeachers(
        (teachersRes as { teachers: TeacherSubscriptionInfo[] }).teachers,
      );
    } catch (error: unknown) {
      console.error("Failed to load dashboard data:", error);
      if (isApiError(error) && error.response?.status === 403) {
        setErrorMessage("No admin permission");
        setTimeout(() => navigate("/teacher/dashboard"), 2000);
      } else if (isApiError(error)) {
        setErrorMessage(
          "Load failed: " +
            (error.response?.data?.detail || error.message || "Unknown error"),
        );
      } else {
        setErrorMessage("Load failed: Unknown error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOpenEditModal = (teacher: TeacherSubscriptionInfo) => {
    setSelectedTeacher(teacher);
    const hasSubscription = !!teacher.current_subscription;
    setEditForm({
      action: hasSubscription ? "edit" : "create",
      plan_name: teacher.current_subscription?.plan_name || "",
      end_date: teacher.current_subscription?.end_date
        ? teacher.current_subscription.end_date.split("T")[0]
        : "",
      quota_total: undefined,
      reason: "",
    });
    setEditModalOpen(true);
  };

  const handleSubmitEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeacher || !editForm.reason) {
      setErrorMessage("Please fill all required fields");
      return;
    }

    // Validation for create action
    if (editForm.action === "create" && !editForm.plan_name) {
      setErrorMessage("Please select a plan for creating subscription");
      return;
    }

    try {
      setLoading(true);
      let response: unknown;

      if (editForm.action === "cancel") {
        response = await apiClient.post("/api/admin/subscription/cancel", {
          teacher_email: selectedTeacher.teacher_email,
          reason: editForm.reason,
        });
      } else if (editForm.action === "create") {
        response = await apiClient.post("/api/admin/subscription/create", {
          teacher_email: selectedTeacher.teacher_email,
          plan_name: editForm.plan_name,
          end_date: editForm.end_date,
          quota_total: editForm.quota_total,
          reason: editForm.reason,
        });
      } else {
        response = await apiClient.post("/api/admin/subscription/edit", {
          teacher_email: selectedTeacher.teacher_email,
          plan_name: editForm.plan_name,
          end_date: editForm.end_date,
          quota_total: editForm.quota_total,
          reason: editForm.reason,
        });
      }

      setSuccessMessage(
        `Success! ${selectedTeacher.teacher_name} - ${
          (response as { message?: string })?.message || "Operation completed"
        }`,
      );

      // Clear cached periods and history to force refresh
      setTeacherPeriods({});
      setPeriodHistory({});
      setExpandedTeacherId(null);
      setExpandedPeriodId(null);

      await loadDashboardData();
      setEditModalOpen(false);
      setEditForm({
        action: "edit",
        plan_name: "",
        end_date: "",
        quota_total: undefined,
        reason: "",
      });
    } catch (error: unknown) {
      console.error("Failed to process subscription:", error);
      setErrorMessage(
        "Failed: " +
          (isApiError(error)
            ? error.message || "Unknown error"
            : "Unknown error"),
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // If search is empty, reload all teachers
      await loadDashboardData();
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.get(
        "/api/admin/subscription/all-teachers",
      );
      const allTeachers = (response as { teachers: TeacherSubscriptionInfo[] })
        .teachers;

      // Filter teachers by email or name
      const filtered = allTeachers.filter(
        (teacher) =>
          teacher.teacher_email
            .toLowerCase()
            .includes(searchQuery.toLowerCase()) ||
          teacher.teacher_name
            .toLowerCase()
            .includes(searchQuery.toLowerCase()),
      );

      setTeachers(filtered);
    } catch (error: unknown) {
      console.error("Search failed:", error);
      if (isApiError(error)) {
        setErrorMessage(
          "Search failed: " +
            (error.response?.data?.detail || error.message || "Unknown error"),
        );
      } else {
        setErrorMessage("Search failed: Unknown error");
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleTeacherExpand = async (teacherId: number) => {
    if (expandedTeacherId === teacherId) {
      setExpandedTeacherId(null);
      setExpandedPeriodId(null);
    } else {
      setExpandedTeacherId(teacherId);
      setExpandedPeriodId(null);

      // Fetch periods if not already loaded
      if (!teacherPeriods[teacherId]) {
        try {
          const response = await apiClient.get(
            `/api/admin/subscription/teacher/${teacherId}/periods`,
          );
          setTeacherPeriods((prev) => ({
            ...prev,
            [teacherId]: (response as { periods: SubscriptionPeriod[] })
              .periods,
          }));
        } catch (error) {
          console.error("Failed to load periods:", error);
          setErrorMessage("Failed to load subscription periods");
        }
      }
    }
  };

  const togglePeriodExpand = async (periodId: number | undefined) => {
    if (!periodId) {
      console.error("Period ID is undefined");
      return;
    }

    if (expandedPeriodId === periodId) {
      setExpandedPeriodId(null);
    } else {
      setExpandedPeriodId(periodId);

      // Fetch history if not already loaded
      if (!periodHistory[periodId]) {
        try {
          const response = await apiClient.get(
            `/api/admin/subscription/period/${periodId}/history`,
          );
          const history = (response as { edit_history: EditHistoryRecord[] })
            .edit_history;
          // Reverse to show newest first
          setPeriodHistory((prev) => ({
            ...prev,
            [periodId]: [...history].reverse(),
          }));
        } catch (error) {
          console.error("Failed to load period history:", error);
          setErrorMessage("Failed to load edit history");
        }
      }
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    const date = new Date(dateString);
    return date.toLocaleDateString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      timeZone: "Asia/Taipei",
    });
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Crown className="w-8 h-8 text-yellow-500" />
            Admin Subscription Dashboard
          </h1>
          <p className="text-gray-600 mt-2">
            Manage user subscriptions and extend VIP access
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate("/teacher/dashboard")}
        >
          Back to Dashboard
        </Button>
      </div>

      {successMessage && (
        <Alert className="mb-4 bg-green-50 border-green-200">
          <CheckCircle className="w-4 h-4 text-green-600" />
          <AlertDescription className="text-green-800">
            {successMessage}
          </AlertDescription>
        </Alert>
      )}

      {errorMessage && (
        <Alert className="mb-4 bg-red-50 border-red-200">
          <XCircle className="w-4 h-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errorMessage}
          </AlertDescription>
        </Alert>
      )}

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Teachers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-500" />
                <span className="text-2xl font-bold">
                  {stats.total_teachers}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Active Subs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-2xl font-bold">
                  {stats.active_subscriptions}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Monthly Revenue
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-yellow-500" />
                <span className="text-2xl font-bold">
                  ${stats.monthly_revenue.toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Quota Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-500" />
                <span className="text-2xl font-bold">
                  {stats.quota_usage_percentage.toFixed(1)}%
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            All Subscriptions
          </CardTitle>
          <CardDescription>
            View all teacher subscription status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <div className="flex-1">
              <Input
                placeholder="Search email or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
              />
            </div>
            <Button onClick={handleSearch} disabled={loading}>
              <Search className="w-4 h-4 mr-2" />
              Search
            </Button>
          </div>

          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>End Date</TableHead>
                  <TableHead>Periods</TableHead>
                  <TableHead>Quota</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teachers.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={8}
                      className="text-center text-gray-500"
                    >
                      No data
                    </TableCell>
                  </TableRow>
                ) : (
                  teachers.map((teacher) => (
                    <>
                      <TableRow
                        key={teacher.teacher_email}
                        className="cursor-pointer hover:bg-gray-50"
                        onClick={() => toggleTeacherExpand(teacher.teacher_id)}
                      >
                        <TableCell className="font-mono text-sm">
                          <div className="flex items-center gap-2">
                            {expandedTeacherId === teacher.teacher_id ? (
                              <ChevronDown className="w-4 h-4 text-gray-500" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-gray-500" />
                            )}
                            {teacher.teacher_email}
                          </div>
                        </TableCell>
                        <TableCell>{teacher.teacher_name}</TableCell>
                        <TableCell>
                          {teacher.current_subscription?.plan_name || "-"}
                        </TableCell>
                        <TableCell>
                          {teacher.current_subscription
                            ? formatDate(teacher.current_subscription.end_date)
                            : "-"}
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-gray-600">
                            {teacherPeriods[teacher.teacher_id]?.length || "-"}
                          </span>
                        </TableCell>
                        <TableCell>
                          {teacher.current_subscription ? (
                            <div className="space-y-1">
                              <div className="text-sm">
                                {teacher.current_subscription.quota_used.toLocaleString()}{" "}
                                /{" "}
                                {teacher.current_subscription.quota_total.toLocaleString()}
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-500 h-2 rounded-full"
                                  style={{
                                    width: `${Math.min((teacher.current_subscription.quota_used / teacher.current_subscription.quota_total) * 100 || 0, 100)}%`,
                                  }}
                                />
                              </div>
                            </div>
                          ) : (
                            "-"
                          )}
                        </TableCell>
                        <TableCell>
                          {teacher.current_subscription?.status === "active" ? (
                            <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                              Active
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                              None
                            </span>
                          )}
                        </TableCell>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleOpenEditModal(teacher)}
                            className="h-8"
                          >
                            <Edit className="w-3 h-3 mr-1" />
                            Edit
                          </Button>
                        </TableCell>
                      </TableRow>

                      {/* Layer 2: Subscription Periods */}
                      {expandedTeacherId === teacher.teacher_id &&
                        teacherPeriods[teacher.teacher_id] && (
                          <TableRow key={`${teacher.teacher_email}-periods`}>
                            <TableCell colSpan={8} className="bg-gray-50 p-0">
                              <div className="p-4">
                                <h4 className="font-semibold mb-3 text-sm">
                                  Subscription Periods
                                </h4>
                                <Table>
                                  <TableHeader>
                                    <TableRow>
                                      <TableHead className="w-12"></TableHead>
                                      <TableHead>Plan</TableHead>
                                      <TableHead>Start Date</TableHead>
                                      <TableHead>End Date</TableHead>
                                      <TableHead>Quota</TableHead>
                                      <TableHead>Payment</TableHead>
                                      <TableHead>Status</TableHead>
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {teacherPeriods[teacher.teacher_id].map(
                                      (period) => (
                                        <>
                                          <TableRow
                                            key={period.id}
                                            className="cursor-pointer hover:bg-gray-100"
                                            onClick={() =>
                                              togglePeriodExpand(period.id)
                                            }
                                          >
                                            <TableCell>
                                              {expandedPeriodId ===
                                              period.id ? (
                                                <ChevronDown className="w-4 h-4 text-gray-500" />
                                              ) : (
                                                <ChevronRight className="w-4 h-4 text-gray-500" />
                                              )}
                                            </TableCell>
                                            <TableCell>
                                              {period.plan_name}
                                            </TableCell>
                                            <TableCell>
                                              {formatDate(period.start_date)}
                                            </TableCell>
                                            <TableCell>
                                              {formatDate(period.end_date)}
                                            </TableCell>
                                            <TableCell>
                                              {period.quota_used.toLocaleString()}{" "}
                                              /{" "}
                                              {period.quota_total.toLocaleString()}
                                            </TableCell>
                                            <TableCell>
                                              <div className="text-sm">
                                                <div>
                                                  {period.payment_method}
                                                </div>
                                                <div className="text-xs text-gray-500">
                                                  $
                                                  {period.amount_paid?.toLocaleString() ||
                                                    "0"}
                                                </div>
                                              </div>
                                            </TableCell>
                                            <TableCell>
                                              <span
                                                className={`px-2 py-1 rounded text-xs ${
                                                  period.status === "active"
                                                    ? "bg-green-100 text-green-800"
                                                    : "bg-gray-100 text-gray-800"
                                                }`}
                                              >
                                                {period.status}
                                              </span>
                                            </TableCell>
                                          </TableRow>

                                          {/* Layer 3: Edit History */}
                                          {expandedPeriodId === period.id &&
                                            periodHistory[period.id] && (
                                              <TableRow
                                                key={`${period.id}-history`}
                                              >
                                                <TableCell
                                                  colSpan={7}
                                                  className="bg-blue-50 p-0"
                                                >
                                                  <div className="p-4">
                                                    <h5 className="font-semibold mb-3 text-sm">
                                                      Edit History
                                                    </h5>
                                                    {periodHistory[period.id]
                                                      .length === 0 ? (
                                                      <p className="text-sm text-gray-500">
                                                        No edit history
                                                      </p>
                                                    ) : (
                                                      <div className="space-y-2">
                                                        {periodHistory[
                                                          period.id
                                                        ].map((record, idx) => (
                                                          <div
                                                            key={idx}
                                                            className="bg-white p-3 rounded border text-sm"
                                                          >
                                                            <div className="flex justify-between mb-2">
                                                              <span
                                                                className={`font-semibold capitalize ${
                                                                  record.action ===
                                                                  "create"
                                                                    ? "text-green-700"
                                                                    : record.action ===
                                                                        "cancel"
                                                                      ? "text-red-700"
                                                                      : "text-blue-700"
                                                                }`}
                                                              >
                                                                {record.action}
                                                              </span>
                                                              <span className="text-xs text-gray-500">
                                                                {new Date(
                                                                  record.timestamp,
                                                                ).toLocaleString(
                                                                  "zh-TW",
                                                                )}
                                                              </span>
                                                            </div>
                                                            <div className="text-xs text-gray-600 mb-2">
                                                              Admin:{" "}
                                                              {
                                                                record.admin_name
                                                              }{" "}
                                                              (
                                                              {
                                                                record.admin_email
                                                              }
                                                              )
                                                            </div>
                                                            {Object.keys(
                                                              record.changes,
                                                            ).length > 0 && (
                                                              <div className="text-xs bg-gray-50 p-2 rounded mb-2 space-y-1">
                                                                <div className="font-semibold">
                                                                  {record.action ===
                                                                  "create"
                                                                    ? "Initial Values:"
                                                                    : "Changes:"}
                                                                </div>
                                                                {record.action ===
                                                                "create" ? (
                                                                  <>
                                                                    {typeof record
                                                                      .changes
                                                                      .plan_name ===
                                                                      "string" && (
                                                                      <div>
                                                                        Plan:{" "}
                                                                        {
                                                                          record
                                                                            .changes
                                                                            .plan_name
                                                                        }
                                                                      </div>
                                                                    )}
                                                                    {typeof record
                                                                      .changes
                                                                      .quota_total ===
                                                                      "number" && (
                                                                      <div>
                                                                        Quota:{" "}
                                                                        {record.changes.quota_total.toLocaleString()}
                                                                      </div>
                                                                    )}
                                                                    {typeof record
                                                                      .changes
                                                                      .end_date ===
                                                                      "string" && (
                                                                      <div>
                                                                        End
                                                                        Date:{" "}
                                                                        {formatDate(
                                                                          record
                                                                            .changes
                                                                            .end_date,
                                                                        )}
                                                                      </div>
                                                                    )}
                                                                    {typeof record
                                                                      .changes
                                                                      .status ===
                                                                      "string" && (
                                                                      <div>
                                                                        Status:{" "}
                                                                        {
                                                                          record
                                                                            .changes
                                                                            .status
                                                                        }
                                                                      </div>
                                                                    )}
                                                                  </>
                                                                ) : (
                                                                  <>
                                                                    {record
                                                                      .changes
                                                                      .plan_name &&
                                                                      typeof record
                                                                        .changes
                                                                        .plan_name ===
                                                                        "object" && (
                                                                        <div>
                                                                          Plan:{" "}
                                                                          {
                                                                            record
                                                                              .changes
                                                                              .plan_name
                                                                              .from
                                                                          }{" "}
                                                                          →{" "}
                                                                          {
                                                                            record
                                                                              .changes
                                                                              .plan_name
                                                                              .to
                                                                          }
                                                                        </div>
                                                                      )}
                                                                    {record
                                                                      .changes
                                                                      .quota_total &&
                                                                      typeof record
                                                                        .changes
                                                                        .quota_total ===
                                                                        "object" && (
                                                                        <div>
                                                                          Quota:{" "}
                                                                          {record.changes.quota_total.from.toLocaleString()}{" "}
                                                                          →{" "}
                                                                          {record.changes.quota_total.to.toLocaleString()}
                                                                        </div>
                                                                      )}
                                                                    {record
                                                                      .changes
                                                                      .end_date &&
                                                                      typeof record
                                                                        .changes
                                                                        .end_date ===
                                                                        "object" && (
                                                                        <div>
                                                                          End
                                                                          Date:{" "}
                                                                          {formatDate(
                                                                            record
                                                                              .changes
                                                                              .end_date
                                                                              .from,
                                                                          )}{" "}
                                                                          →{" "}
                                                                          {formatDate(
                                                                            record
                                                                              .changes
                                                                              .end_date
                                                                              .to,
                                                                          )}
                                                                        </div>
                                                                      )}
                                                                    {record
                                                                      .changes
                                                                      .status &&
                                                                      typeof record
                                                                        .changes
                                                                        .status ===
                                                                        "object" && (
                                                                        <div>
                                                                          Status:{" "}
                                                                          {
                                                                            record
                                                                              .changes
                                                                              .status
                                                                              .from
                                                                          }{" "}
                                                                          →{" "}
                                                                          {
                                                                            record
                                                                              .changes
                                                                              .status
                                                                              .to
                                                                          }
                                                                        </div>
                                                                      )}
                                                                  </>
                                                                )}
                                                              </div>
                                                            )}
                                                            <div className="text-xs text-gray-700 bg-yellow-50 p-2 rounded">
                                                              <span className="font-semibold">
                                                                Reason:
                                                              </span>{" "}
                                                              {record.reason}
                                                            </div>
                                                          </div>
                                                        ))}
                                                      </div>
                                                    )}
                                                  </div>
                                                </TableCell>
                                              </TableRow>
                                            )}
                                        </>
                                      ),
                                    )}
                                  </TableBody>
                                </Table>
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                    </>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Edit Subscription Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editForm.action === "create"
                ? "Create Subscription"
                : editForm.action === "cancel"
                  ? "Cancel Subscription"
                  : "Edit Subscription"}
            </DialogTitle>
            <DialogDescription>
              {selectedTeacher &&
                `${selectedTeacher.teacher_name} (${selectedTeacher.teacher_email})`}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmitEdit} className="space-y-4 mt-4">
            {/* Action Selector */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Action</label>
              <Select
                value={editForm.action}
                onValueChange={(value) =>
                  setEditForm({ ...editForm, action: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {!selectedTeacher?.current_subscription && (
                    <SelectItem value="create">Create Subscription</SelectItem>
                  )}
                  {selectedTeacher?.current_subscription && (
                    <>
                      <SelectItem value="edit">Edit Subscription</SelectItem>
                      <SelectItem value="cancel">
                        Cancel Subscription
                      </SelectItem>
                    </>
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Plan Name (for create and edit) */}
            {(editForm.action === "create" || editForm.action === "edit") && (
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Plan Name{" "}
                  {editForm.action === "create" && (
                    <span className="text-red-500">*</span>
                  )}
                  {editForm.action === "edit" &&
                    selectedTeacher?.current_subscription?.plan_name && (
                      <span className="text-xs text-gray-500 ml-2">
                        (Current:{" "}
                        {selectedTeacher.current_subscription.plan_name})
                      </span>
                    )}
                </label>
                <Select
                  value={
                    editForm.plan_name ||
                    (editForm.action === "create" ? "" : "NO_CHANGE")
                  }
                  onValueChange={(value) =>
                    setEditForm({
                      ...editForm,
                      plan_name: value === "NO_CHANGE" ? "" : value,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue
                      placeholder={
                        editForm.action === "create"
                          ? "Select a plan"
                          : "— No change —"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {editForm.action === "edit" && (
                      <SelectItem value="NO_CHANGE">— No change —</SelectItem>
                    )}
                    <SelectItem value="30-Day Trial">30-Day Trial</SelectItem>
                    <SelectItem value="Tutor Teachers">
                      Tutor Teachers
                    </SelectItem>
                    <SelectItem value="School Teachers">
                      School Teachers
                    </SelectItem>
                    <SelectItem value="Demo Unlimited Plan">
                      Demo Unlimited Plan
                    </SelectItem>
                    <SelectItem value="VIP">VIP</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* End Date (for create and edit) */}
            {(editForm.action === "create" || editForm.action === "edit") && (
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  End Date{" "}
                  {editForm.action === "create" ? (
                    <span className="text-xs text-gray-500">
                      (optional, defaults to plan duration)
                    </span>
                  ) : (
                    "(optional)"
                  )}
                </label>
                <Input
                  type="date"
                  value={editForm.end_date}
                  onChange={(e) =>
                    setEditForm({ ...editForm, end_date: e.target.value })
                  }
                  placeholder="YYYY-MM-DD"
                />
                <p className="text-xs text-gray-500">
                  {editForm.action === "create"
                    ? "Leave empty to use default plan duration"
                    : "Leave empty to keep current end date"}
                </p>
              </div>
            )}

            {/* Custom Quota (for VIP plan in create and edit) */}
            {(editForm.action === "create" || editForm.action === "edit") &&
              editForm.plan_name === "VIP" && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Custom Quota (optional)
                  </label>
                  <Input
                    type="number"
                    value={editForm.quota_total || ""}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        quota_total: e.target.value
                          ? parseInt(e.target.value)
                          : undefined,
                      })
                    }
                    placeholder="Enter custom quota (e.g., 50000)"
                    min="1"
                  />
                  <p className="text-xs text-gray-500">
                    Leave empty to keep current quota for VIP plan
                  </p>
                </div>
              )}

            {/* Reason (always required) */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Reason *</label>
              <Textarea
                value={editForm.reason}
                onChange={(e) =>
                  setEditForm({ ...editForm, reason: e.target.value })
                }
                placeholder="Enter reason for this action..."
                required
                rows={3}
              />
            </div>

            {/* Buttons */}
            <div className="flex gap-2 justify-end pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditModalOpen(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading || !editForm.reason}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : editForm.action === "cancel" ? (
                  "Cancel Subscription"
                ) : (
                  "Update Subscription"
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
