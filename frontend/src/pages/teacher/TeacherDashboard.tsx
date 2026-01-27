import { useState, useEffect } from "react";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import TeacherLayout from "@/components/TeacherLayout";
import {
  Users,
  UserCheck,
  BookOpen,
  Settings,
  Share2,
  Copy,
  Check,
} from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { apiClient } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

interface DashboardData {
  teacher: {
    id: number;
    email: string;
    name: string;
    is_demo: boolean;
  };
  classroom_count: number;
  student_count: number;
  program_count: number;
  classrooms: Array<{
    id: number;
    name: string;
    description?: string;
    student_count: number;
    school_id?: string;
    school_name?: string;
    organization_id?: string;
  }>;
  recent_students: Array<{
    id: number;
    name: string;
    email: string;
    classroom_name: string;
    school_id?: string;
    school_name?: string;
    organization_id?: string;
  }>;
  subscription_status?: string;
  subscription_end_date?: string;
  days_remaining?: number;
  can_assign_homework?: boolean;
  is_test_account?: boolean; // 後端提供的白名單狀態
}

export default function TeacherDashboard() {
  const { t } = useTranslation();
  const { selectedSchool, selectedOrganization, mode } = useWorkspace();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Share dialog state
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = (await apiClient.getTeacherDashboard()) as DashboardData;
      setDashboardData(data);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      // 如果是 401 錯誤，轉到登入頁
      if (err instanceof Error && err.message.includes("401")) {
        navigate("/teacher/login");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopyUrl = async () => {
    if (!dashboardData) return;
    const studentLoginUrl = `${window.location.origin}/student/login?teacher_email=${dashboardData.teacher.email}`;
    try {
      await navigator.clipboard.writeText(studentLoginUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy URL:", err);
    }
  };

  const getStudentLoginUrl = () => {
    if (!dashboardData) return "";
    return `${window.location.origin}/student/login?teacher_email=${dashboardData.teacher.email}`;
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">
              {t("teacherDashboard.loading")}
            </p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  if (!dashboardData) {
    return (
      <TeacherLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">
            {t("teacherDashboard.error.loadFailed")}
          </p>
        </div>
      </TeacherLayout>
    );
  }

  // Filter classrooms based on workspace selection
  const filteredClassrooms = dashboardData.classrooms.filter((classroom) => {
    if (mode === "personal") return true;
    if (selectedSchool) {
      return classroom.school_id === selectedSchool.id;
    }
    if (selectedOrganization) {
      return classroom.organization_id === selectedOrganization.id;
    }
    return true;
  });

  // Filter students based on workspace selection
  const filteredStudents = dashboardData.recent_students.filter((student) => {
    if (mode === "personal") return true;
    if (selectedSchool) {
      return student.school_id === selectedSchool.id;
    }
    if (selectedOrganization) {
      return student.organization_id === selectedOrganization.id;
    }
    return true;
  });

  // Calculate filtered stats
  const filteredStudentCount = filteredClassrooms.reduce(
    (sum, c) => sum + c.student_count,
    0
  );

  return (
    <TeacherLayout>
      {/* Share to Students Dialog */}
      <Dialog open={showShareDialog} onOpenChange={setShowShareDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("teacherDashboard.share.title")}</DialogTitle>
            <DialogDescription>
              {t("teacherDashboard.share.description")}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* QR Code */}
            <div className="flex justify-center p-4 bg-white border rounded-lg">
              <QRCodeSVG value={getStudentLoginUrl()} size={200} />
            </div>

            {/* URL Input with Copy Button */}
            <div className="flex items-center space-x-2">
              <Input value={getStudentLoginUrl()} readOnly className="flex-1" />
              <Button
                size="sm"
                onClick={handleCopyUrl}
                className="flex-shrink-0"
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    {t("teacherDashboard.share.copied")}
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-2" />
                    {t("teacherDashboard.share.copy")}
                  </>
                )}
              </Button>
            </div>

            {/* Instructions */}
            <div className="text-sm text-gray-600 space-y-2">
              <p>{t("teacherDashboard.share.instructions")}</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>{t("teacherDashboard.share.instruction1")}</li>
                <li>{t("teacherDashboard.share.instruction2")}</li>
              </ul>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-gray-900">
            {t("teacherDashboard.welcome.title", {
              name: dashboardData.teacher.name,
            })}
          </h2>
          <Button
            onClick={() => setShowShareDialog(true)}
            className="flex items-center gap-2"
          >
            <Share2 className="h-4 w-4" />
            {t("teacherDashboard.share.button")}
          </Button>
        </div>

        {/* Subscription Status Card - Always Show */}
        <Card
          className={`mb-6 ${
            dashboardData.subscription_status === "subscribed"
              ? "bg-gradient-to-r from-green-50 to-blue-50 border-green-200"
              : "bg-gradient-to-r from-red-50 to-gray-50 border-red-200"
          }`}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {dashboardData.subscription_status === "subscribed"
                    ? t("teacherDashboard.subscription.statusSubscribed")
                    : t("teacherDashboard.subscription.statusNotSubscribed")}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {dashboardData.subscription_status === "subscribed"
                    ? t("teacherDashboard.subscription.willExpireIn", {
                        days: dashboardData.days_remaining || 0,
                      })
                    : t("teacherDashboard.subscription.noActiveSubscription")}
                </p>
                {dashboardData.subscription_end_date && (
                  <p className="text-xs text-gray-500 mt-2">
                    {t("teacherDashboard.subscription.expiryDateLabel")}{" "}
                    {new Date(
                      dashboardData.subscription_end_date,
                    ).toLocaleDateString("zh-TW")}
                  </p>
                )}
              </div>
              <div className="text-center">
                <div
                  className={`text-3xl font-bold ${
                    dashboardData.subscription_status === "subscribed"
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {(dashboardData.days_remaining ?? 0) > 0
                    ? dashboardData.days_remaining
                    : 0}
                </div>
                <div className="text-sm text-gray-600">
                  {t("teacherDashboard.subscription.remainingDays", {
                    days: dashboardData.days_remaining ?? 0,
                  })}
                </div>
              </div>
            </div>

            {/* Test Mode Button - Show for whitelist accounts */}
            {dashboardData.is_test_account && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <Button
                  onClick={() => navigate("/teacher/test-sub")}
                  className="w-full bg-purple-600 hover:bg-purple-700 dark:bg-purple-500 dark:hover:bg-purple-600 text-white"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  {t("teacherDashboard.subscription.testModeButton")}
                </Button>
                <p className="text-xs text-gray-500 text-center mt-2">
                  {t("teacherDashboard.subscription.testModeDescription")}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {t("teacherDashboard.stats.classrooms")}
              </CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {filteredClassrooms.length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {t("teacherDashboard.stats.students")}
              </CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {filteredStudentCount}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {t("teacherDashboard.stats.programs")}
              </CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardData.program_count}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>{t("teacherDashboard.classrooms.title")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredClassrooms.map((classroom) => (
                  <div
                    key={classroom.id}
                    className="flex items-center justify-between p-3 border rounded"
                  >
                    <div>
                      <h4 className="font-medium">{classroom.name}</h4>
                      <p className="text-sm text-gray-500">
                        {classroom.description}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {t("teacherDashboard.classrooms.studentsCount", {
                          count: classroom.student_count,
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("teacherDashboard.students.title")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {filteredStudents.map((student) => (
                  <div
                    key={student.id}
                    className="flex items-center space-x-3 p-3 border rounded"
                  >
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-blue-600">
                        {student.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-sm">{student.name}</p>
                      <p className="text-xs text-gray-500">
                        {student.classroom_name}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </TeacherLayout>
  );
}
