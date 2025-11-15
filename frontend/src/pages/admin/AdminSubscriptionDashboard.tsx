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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Users,
  Crown,
  Search,
  TrendingUp,
  DollarSign,
  CheckCircle,
  XCircle,
  Clock,
  Edit,
  History,
} from "lucide-react";
import { apiClient } from "@/lib/api";

// Types
interface TeacherSubscriptionInfo {
  id: number;
  email: string;
  name: string;
  plan_name: string | null;
  end_date: string | null;
  days_remaining: number | null;
  quota_used: number;
  quota_total: number | null;
  quota_percentage: number | null;
  status: "active" | "expired" | "cancelled" | "none";
  total_periods: number;
  created_at: string;
}

interface ExtensionHistoryRecord {
  id: number;
  teacher_email: string;
  teacher_name: string | null;
  plan_name: string;
  months: number;
  amount: number;
  extended_at: string;
  admin_email: string | null;
  admin_name: string | null;
  reason: string | null;
  quota_granted: number | null;
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
  const [history, setHistory] = useState<ExtensionHistoryRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

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
      const [statsRes, teachersRes, historyRes] = await Promise.all([
        apiClient.get("/api/admin/subscription/stats"),
        apiClient.get("/api/admin/subscription/teachers?limit=50"),
        apiClient.get("/api/admin/subscription/history?limit=50"),
      ]);

      setStats(statsRes as AdminStats);
      setTeachers(
        (teachersRes as { teachers: TeacherSubscriptionInfo[] }).teachers,
      );
      setHistory((historyRes as { history: ExtensionHistoryRecord[] }).history);
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
    setEditForm({
      action: "edit",
      plan_name: teacher.plan_name || "",
      end_date: teacher.end_date ? teacher.end_date.split("T")[0] : "",
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

    try {
      setLoading(true);
      let response: unknown;

      if (editForm.action === "cancel") {
        response = await apiClient.post("/api/admin/subscription/cancel", {
          teacher_email: selectedTeacher.email,
          reason: editForm.reason,
        });
      } else {
        response = await apiClient.post("/api/admin/subscription/edit", {
          teacher_email: selectedTeacher.email,
          plan_name: editForm.plan_name,
          end_date: editForm.end_date,
          quota_total: editForm.quota_total,
          reason: editForm.reason,
        });
      }

      setSuccessMessage(
        `Success! ${selectedTeacher.name} - ${
          (response as { message?: string })?.message || "Operation completed"
        }`,
      );

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
    try {
      setLoading(true);
      const response = await apiClient.get(
        `/api/admin/subscription/teachers?search=${encodeURIComponent(searchQuery)}&limit=100`,
      );
      setTeachers(
        (response as { teachers: TeacherSubscriptionInfo[] }).teachers,
      );
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
          <Clock className="w-8 h-8 animate-spin mx-auto mb-4" />
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

      <Tabs defaultValue="subscriptions" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 h-16 bg-gray-100 p-1 rounded-lg">
          <TabsTrigger
            value="subscriptions"
            className="flex items-center gap-2 text-base font-semibold data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-blue-600"
          >
            <Users className="w-5 h-5" />
            All Subscriptions
          </TabsTrigger>
          <TabsTrigger
            value="history"
            className="flex items-center gap-2 text-base font-semibold data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-blue-600"
          >
            <History className="w-5 h-5" />
            Operation History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="subscriptions">
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
                        <TableRow key={teacher.id}>
                          <TableCell className="font-mono text-sm">
                            {teacher.email}
                          </TableCell>
                          <TableCell>{teacher.name}</TableCell>
                          <TableCell>{teacher.plan_name || "-"}</TableCell>
                          <TableCell>{formatDate(teacher.end_date)}</TableCell>
                          <TableCell>
                            <span className="text-sm text-gray-600">
                              {teacher.total_periods > 0
                                ? `${teacher.total_periods} 期`
                                : "未訂閱"}
                            </span>
                          </TableCell>
                          <TableCell>
                            {teacher.quota_total ? (
                              <div className="space-y-1">
                                <div className="text-sm">
                                  {teacher.quota_used.toLocaleString()} /{" "}
                                  {teacher.quota_total.toLocaleString()}
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-blue-500 h-2 rounded-full"
                                    style={{
                                      width: `${Math.min(teacher.quota_percentage || 0, 100)}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            ) : (
                              "-"
                            )}
                          </TableCell>
                          <TableCell>
                            {teacher.status === "active" && (
                              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                                Active
                              </span>
                            )}
                            {teacher.status === "expired" && (
                              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">
                                Expired
                              </span>
                            )}
                            {teacher.status === "cancelled" && (
                              <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">
                                Cancelled
                              </span>
                            )}
                            {teacher.status === "none" && (
                              <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                                None
                              </span>
                            )}
                          </TableCell>
                          <TableCell>
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
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Admin Operation History
              </CardTitle>
              <CardDescription>
                View all admin subscription operations (extend, edit, cancel)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Time</TableHead>
                      <TableHead>Teacher</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Months</TableHead>
                      <TableHead>Quota</TableHead>
                      <TableHead>Admin</TableHead>
                      <TableHead>Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {history.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={7}
                          className="text-center text-gray-500"
                        >
                          No operation history
                        </TableCell>
                      </TableRow>
                    ) : (
                      history.map((record) => (
                        <TableRow key={record.id}>
                          <TableCell className="text-sm">
                            {formatDate(record.extended_at)}
                          </TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              <div className="font-medium">
                                {record.teacher_name || "-"}
                              </div>
                              <div className="text-xs text-gray-500 font-mono">
                                {record.teacher_email}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm">
                            {record.plan_name}
                          </TableCell>
                          <TableCell>{record.months} mo</TableCell>
                          <TableCell>
                            {record.quota_granted
                              ? record.quota_granted.toLocaleString() + " pts"
                              : "-"}
                          </TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              <div className="font-medium text-sm">
                                {record.admin_name || "-"}
                              </div>
                              <div className="text-xs text-gray-500 font-mono">
                                {record.admin_email || "-"}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm max-w-xs truncate">
                            {record.reason || "-"}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Subscription Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Subscription</DialogTitle>
            <DialogDescription>
              {selectedTeacher &&
                `${selectedTeacher.name} (${selectedTeacher.email})`}
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
                  <SelectItem value="edit">Edit Subscription</SelectItem>
                  <SelectItem value="cancel">Cancel Subscription</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Plan Name (only for edit) */}
            {editForm.action === "edit" && (
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Plan Name
                  {selectedTeacher?.plan_name && (
                    <span className="text-xs text-gray-500 ml-2">
                      (Current: {selectedTeacher.plan_name})
                    </span>
                  )}
                </label>
                <Select
                  value={editForm.plan_name || "NO_CHANGE"}
                  onValueChange={(value) =>
                    setEditForm({
                      ...editForm,
                      plan_name: value === "NO_CHANGE" ? "" : value,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NO_CHANGE">— No change —</SelectItem>
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

            {/* End Date (only for edit) */}
            {editForm.action === "edit" && (
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  End Date (optional)
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
                  Leave empty to keep current end date
                </p>
              </div>
            )}

            {/* Custom Quota (only for VIP plan) */}
            {editForm.action === "edit" && editForm.plan_name === "VIP" && (
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
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
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
