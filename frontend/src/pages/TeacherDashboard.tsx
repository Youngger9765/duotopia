import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Users,
  GraduationCap,
  BookOpen,
  LogOut,
  UserCheck,
  Clock,
  TrendingUp,
} from "lucide-react";
import { apiClient } from "../lib/api";

interface TeacherProfile {
  id: number;
  email: string;
  name: string;
  phone?: string;
  is_demo: boolean;
  is_active: boolean;
}

interface ClassroomSummary {
  id: number;
  name: string;
  description?: string;
  student_count: number;
}

interface StudentSummary {
  id: number;
  name: string;
  email: string;
  classroom_name: string;
}

interface DashboardData {
  teacher: TeacherProfile;
  classroom_count: number;
  student_count: number;
  program_count: number;
  classrooms: ClassroomSummary[];
  recent_students: StudentSummary[];
  subscription_status?: string;
  subscription_end_date?: string;
  days_remaining?: number;
  can_assign_homework?: boolean;
}

// Removed unused interfaces - they're in TeacherDashboardWithSidebar.tsx

export default function TeacherDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Note: This is the old dashboard without sidebar.
  // Use TeacherDashboardWithSidebar for full functionality.

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTeacherDashboard();
      setDashboardData(data as DashboardData);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setError(t("teacherDashboard.errors.loadFailed"));
      // If unauthorized, redirect to login
      if (err instanceof Error && err.message.includes("401")) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  // Removed unused functions for old sidebar functionality

  const handleLogout = () => {
    apiClient.logout();
    navigate("/teacher/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">{t("teacherDashboard.loading")}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <p className="text-red-600 text-center mb-4">{error}</p>
            <Button
              onClick={() => navigate("/teacher/login")}
              className="w-full"
            >
              {t("teacherDashboard.buttons.backToLogin")}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboardData) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center py-4 space-y-4 sm:space-y-0">
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
              <div className="flex items-center space-x-2">
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                  Duotopia
                </h1>
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded whitespace-nowrap">
                  {t("teacherDashboard.header.teacherPortal")}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {dashboardData.teacher.is_demo && (
                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded whitespace-nowrap">
                    {t("teacherDashboard.header.demoAccount")}
                  </span>
                )}
                {dashboardData.subscription_status === "trial" &&
                  dashboardData.days_remaining && (
                    <span className="px-3 py-1 text-xs sm:text-sm bg-green-100 text-green-700 rounded-full font-medium whitespace-nowrap">
                      🎉{" "}
                      {t("teacherDashboard.header.trialDaysRemaining", {
                        days: dashboardData.days_remaining,
                      })}
                    </span>
                  )}
              </div>
            </div>
            <div className="flex items-center justify-between w-full sm:w-auto sm:space-x-4">
              <div className="text-left sm:text-right">
                <p className="text-sm font-medium text-gray-900">
                  {dashboardData.teacher.name}
                </p>
                <p className="text-xs text-gray-500">
                  {dashboardData.teacher.email}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="ml-4"
              >
                <LogOut className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">
                  {t("teacherDashboard.buttons.logout")}
                </span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        {/* Welcome Section */}
        <div className="mb-6 sm:mb-8">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            {t("teacherDashboard.welcome.title", {
              name: dashboardData.teacher.name,
            })}
          </h2>
          <p className="text-sm sm:text-base text-gray-600">
            {t("teacherDashboard.welcome.subtitle")}
          </p>
        </div>

        {/* Subscription Status Card */}
        {dashboardData.subscription_status === "trial" &&
          dashboardData.days_remaining && (
            <Card className="mb-6 sm:mb-8 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
              <CardContent className="pt-4 sm:pt-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-4 sm:space-y-0">
                  <div className="flex-1">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900">
                      {t("teacherDashboard.subscription.trialTitle")}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {t("teacherDashboard.subscription.trialDescription", {
                        days: dashboardData.days_remaining,
                      })}
                    </p>
                    {dashboardData.subscription_end_date && (
                      <p className="text-xs text-gray-500 mt-2">
                        {t("teacherDashboard.subscription.expiryDate")}{" "}
                        {new Date(
                          dashboardData.subscription_end_date,
                        ).toLocaleDateString("zh-TW")}
                      </p>
                    )}
                  </div>
                  <div className="text-center sm:text-right">
                    <div className="text-2xl sm:text-3xl font-bold text-green-600">
                      {dashboardData.days_remaining}
                    </div>
                    <div className="text-sm text-gray-600">
                      {t("teacherDashboard.subscription.days")}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs sm:text-sm font-medium">
                {t("teacherDashboard.stats.classroomCount")}
              </CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-xl sm:text-2xl font-bold">
                {dashboardData.classroom_count}
              </div>
              <p className="text-xs text-muted-foreground">
                {t("teacherDashboard.stats.activeClassrooms")}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs sm:text-sm font-medium">
                {t("teacherDashboard.stats.studentCount")}
              </CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-xl sm:text-2xl font-bold">
                {dashboardData.student_count}
              </div>
              <p className="text-xs text-muted-foreground">
                {t("teacherDashboard.stats.allStudents")}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs sm:text-sm font-medium">
                {t("teacherDashboard.stats.programCount")}
              </CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-xl sm:text-2xl font-bold">
                {dashboardData.program_count}
              </div>
              <p className="text-xs text-muted-foreground">
                {t("teacherDashboard.stats.createdPrograms")}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
          {/* Classrooms */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <GraduationCap className="h-5 w-5 mr-2" />
                {t("teacherDashboard.classrooms.title")}
              </CardTitle>
              <CardDescription>
                {t("teacherDashboard.classrooms.description")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData.classrooms.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  {t("teacherDashboard.classrooms.noClassrooms")}
                </p>
              ) : (
                <div className="space-y-3 sm:space-y-4">
                  {dashboardData.classrooms.map((classroom) => (
                    <div
                      key={classroom.id}
                      className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 sm:p-4 border rounded-lg space-y-2 sm:space-y-0"
                    >
                      <div className="flex-1">
                        <h4 className="font-medium text-sm sm:text-base">
                          {classroom.name}
                        </h4>
                        <p className="text-xs sm:text-sm text-gray-500">
                          {classroom.description}
                        </p>
                      </div>
                      <div className="flex items-center justify-between sm:justify-end w-full sm:w-auto sm:text-right">
                        <p className="text-xs sm:text-sm font-medium">
                          {t("teacherDashboard.classrooms.studentsCount", {
                            count: classroom.student_count,
                          })}
                        </p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="ml-4 sm:ml-0 sm:mt-2"
                        >
                          {t("teacherDashboard.buttons.manage")}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <Button className="w-full mt-4" size="sm">
                <Users className="h-4 w-4 mr-2" />
                {t("teacherDashboard.buttons.createClassroom")}
              </Button>
            </CardContent>
          </Card>

          {/* Recent Students */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                {t("teacherDashboard.students.title")}
              </CardTitle>
              <CardDescription>
                {t("teacherDashboard.students.description")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData.recent_students.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  {t("teacherDashboard.students.noStudents")}
                </p>
              ) : (
                <div className="space-y-3">
                  {dashboardData.recent_students.map((student) => (
                    <div
                      key={student.id}
                      className="flex items-center justify-between p-3 border rounded"
                    >
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-sm font-medium text-blue-600">
                            {student.name.charAt(0)}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-sm truncate">
                            {student.name}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {student.classroom_name}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="flex-shrink-0"
                      >
                        <Clock className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <Button variant="outline" className="w-full mt-4" size="sm">
                {t("teacherDashboard.buttons.viewAllStudents")}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="mt-6 sm:mt-8">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg">
              {t("teacherDashboard.quickActions.title")}
            </CardTitle>
            <CardDescription className="text-sm">
              {t("teacherDashboard.quickActions.description")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
              <Button
                variant="outline"
                className="h-16 sm:h-20 flex flex-col text-xs sm:text-sm"
              >
                <BookOpen className="h-5 w-5 sm:h-6 sm:w-6 mb-1 sm:mb-2" />
                {t("teacherDashboard.quickActions.createProgram")}
              </Button>
              <Button
                variant="outline"
                className="h-16 sm:h-20 flex flex-col text-xs sm:text-sm"
              >
                <Users className="h-5 w-5 sm:h-6 sm:w-6 mb-1 sm:mb-2" />
                {t("teacherDashboard.quickActions.manageStudents")}
              </Button>
              <Button
                variant="outline"
                className="h-16 sm:h-20 flex flex-col text-xs sm:text-sm sm:col-span-2 lg:col-span-1"
              >
                <TrendingUp className="h-5 w-5 sm:h-6 sm:w-6 mb-1 sm:mb-2" />
                {t("teacherDashboard.quickActions.viewStats")}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
