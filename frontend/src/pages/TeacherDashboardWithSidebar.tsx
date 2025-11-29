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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Users,
  GraduationCap,
  BookOpen,
  LogOut,
  UserCheck,
  TrendingUp,
  Home,
  ChevronLeft,
  ChevronRight,
  Filter,
  Share2,
  Copy,
  Check,
} from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
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

interface ClassroomDetail {
  id: number;
  name: string;
  description?: string;
  student_count: number;
  students: StudentDetail[];
}

interface StudentDetail {
  id: number;
  name: string;
  email: string;
}

interface Program {
  id: number;
  name: string;
  description?: string;
  classroom_id: number;
  classroom_name: string;
  estimated_hours?: number;
  level: string;
}

type SidebarView = "dashboard" | "classrooms" | "students" | "programs";

export default function TeacherDashboardWithSidebar() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Sidebar state
  const [currentView, setCurrentView] = useState<SidebarView>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Share dialog state
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [copied, setCopied] = useState(false);

  // Data for different views
  const [classroomsDetail, setClassroomsDetail] = useState<ClassroomDetail[]>(
    [],
  );
  const [programs, setPrograms] = useState<Program[]>([]);
  const [selectedClassroom, setSelectedClassroom] = useState<number | null>(
    null,
  );

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
      setError("載入儀表板失敗，請重新登入");
      if (err instanceof Error && err.message.includes("401")) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchClassroomsDetail = async () => {
    try {
      const data = await apiClient.getTeacherClassrooms();
      setClassroomsDetail(data as ClassroomDetail[]);
    } catch (err) {
      console.error("Fetch classrooms error:", err);
    }
  };

  const fetchPrograms = async () => {
    try {
      const data = await apiClient.getTeacherPrograms();
      setPrograms(data as Program[]);
    } catch (err) {
      console.error("Fetch programs error:", err);
    }
  };

  const handleViewChange = async (view: SidebarView) => {
    setCurrentView(view);
    if (view === "classrooms" && classroomsDetail.length === 0) {
      await fetchClassroomsDetail();
    }
    if (view === "programs" && programs.length === 0) {
      await fetchPrograms();
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    navigate("/teacher/login");
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
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
              返回登入
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboardData) return null;

  // Filter students by selected classroom
  const filteredStudents = selectedClassroom
    ? classroomsDetail.find((c) => c.id === selectedClassroom)?.students || []
    : classroomsDetail.flatMap((c) => c.students);

  // Filter programs by selected classroom
  const filteredPrograms = selectedClassroom
    ? programs.filter((p) => p.classroom_id === selectedClassroom)
    : programs;

  const sidebarItems = [
    { id: "dashboard", label: "儀表板", icon: Home },
    { id: "classrooms", label: "我的班級", icon: GraduationCap },
    { id: "students", label: "所有學生", icon: Users },
    { id: "programs", label: "課程列表", icon: BookOpen },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex">
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
              <Input
                value={getStudentLoginUrl()}
                readOnly
                className="flex-1"
              />
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

      {/* Sidebar */}
      <div
        className={`bg-white shadow-lg transition-all duration-300 ${sidebarCollapsed ? "w-16" : "w-64"} flex flex-col`}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          {!sidebarCollapsed && (
            <div>
              <h1 className="text-xl font-bold text-gray-900">Duotopia</h1>
              <p className="text-sm text-gray-500">教師後台</p>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.id}>
                  <Button
                    variant={currentView === item.id ? "default" : "ghost"}
                    className={`w-full justify-start ${sidebarCollapsed ? "px-3" : "px-4"}`}
                    onClick={() => handleViewChange(item.id as SidebarView)}
                  >
                    <Icon className="h-4 w-4" />
                    {!sidebarCollapsed && (
                      <span className="ml-2">{item.label}</span>
                    )}
                  </Button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User Info & Logout */}
        <div className="p-4 border-t">
          {!sidebarCollapsed && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-900">
                {dashboardData.teacher.name}
              </p>
              <p className="text-xs text-gray-500">
                {dashboardData.teacher.email}
              </p>
              {dashboardData.teacher.is_demo && (
                <span className="inline-block mt-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                  Demo 帳號
                </span>
              )}
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            className={`w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 ${sidebarCollapsed ? "px-3" : "px-4"}`}
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            {!sidebarCollapsed && <span className="ml-2">登出</span>}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 overflow-auto">
        {currentView === "dashboard" && (
          <DashboardContent
            dashboardData={dashboardData}
            onShareClick={() => setShowShareDialog(true)}
          />
        )}

        {currentView === "classrooms" && (
          <ClassroomsContent
            classrooms={classroomsDetail}
            onRefresh={fetchClassroomsDetail}
          />
        )}

        {currentView === "students" && (
          <StudentsContent
            students={filteredStudents}
            classrooms={classroomsDetail}
            selectedClassroom={selectedClassroom}
            onClassroomFilter={setSelectedClassroom}
          />
        )}

        {currentView === "programs" && (
          <ProgramsContent
            programs={filteredPrograms}
            classrooms={classroomsDetail}
            selectedClassroom={selectedClassroom}
            onClassroomFilter={setSelectedClassroom}
            onRefresh={fetchPrograms}
          />
        )}
      </div>
    </div>
  );
}

// Dashboard Content Component
function DashboardContent({
  dashboardData,
  onShareClick,
}: {
  dashboardData: DashboardData;
  onShareClick: () => void;
}) {
  const { t } = useTranslation();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-gray-900">
          {t("teacherDashboard.welcome.title", {
            name: dashboardData.teacher.name,
          })}
        </h2>
        <Button onClick={onShareClick} className="flex items-center gap-2">
          <Share2 className="h-4 w-4" />
          {t("teacherDashboard.share.button")}
        </Button>
      </div>

      {/* Subscription Status Card */}
      {dashboardData.subscription_status === "trial" &&
        dashboardData.days_remaining && (
          <Card className="mb-6 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    🎉 30天免費試用期
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    您的免費試用將在 {dashboardData.days_remaining} 天後到期
                  </p>
                  {dashboardData.subscription_end_date && (
                    <p className="text-xs text-gray-500 mt-2">
                      到期日:{" "}
                      {new Date(
                        dashboardData.subscription_end_date,
                      ).toLocaleDateString("zh-TW")}
                    </p>
                  )}
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {dashboardData.days_remaining}
                  </div>
                  <div className="text-sm text-gray-600">天</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">班級數量</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.classroom_count}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">學生總數</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.student_count}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">課程計畫</CardTitle>
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
            <CardTitle>班級概覽</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.classrooms.map((classroom) => (
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
                      {classroom.student_count} 位學生
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>最近活動學生</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.recent_students.map((student) => (
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
  );
}

// Classrooms Content Component
function ClassroomsContent({
  classrooms,
  onRefresh,
}: {
  classrooms: ClassroomDetail[];
  onRefresh: () => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-gray-900">我的班級</h2>
        <Button onClick={onRefresh}>
          <TrendingUp className="h-4 w-4 mr-2" />
          重新載入
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {classrooms.map((classroom) => (
          <Card key={classroom.id}>
            <CardHeader>
              <CardTitle>{classroom.name}</CardTitle>
              <CardDescription>{classroom.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                {classroom.student_count} 位學生
              </p>
              <div className="space-y-2">
                <h4 className="font-medium text-sm">學生列表：</h4>
                <div className="grid grid-cols-1 gap-2">
                  {classroom.students.map((student) => (
                    <div
                      key={student.id}
                      className="flex items-center space-x-2 p-2 bg-gray-50 rounded"
                    >
                      <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium text-blue-600">
                          {student.name.charAt(0)}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium">{student.name}</p>
                        <p className="text-xs text-gray-500">{student.email}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Students Content Component
function StudentsContent({
  students,
  classrooms,
  selectedClassroom,
  onClassroomFilter,
}: {
  students: StudentDetail[];
  classrooms: ClassroomDetail[];
  selectedClassroom: number | null;
  onClassroomFilter: (classroomId: number | null) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-gray-900">所有學生</h2>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <select
            value={selectedClassroom || ""}
            onChange={(e) =>
              onClassroomFilter(e.target.value ? Number(e.target.value) : null)
            }
            className="px-3 py-2 border rounded-md text-sm"
          >
            <option value="">所有班級</option>
            {classrooms.map((classroom) => (
              <option key={classroom.id} value={classroom.id}>
                {classroom.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {students.map((student) => (
          <Card key={student.id}>
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="font-medium text-blue-600">
                    {student.name.charAt(0)}
                  </span>
                </div>
                <div>
                  <h3 className="font-medium">{student.name}</h3>
                  <p className="text-sm text-gray-500">{student.email}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {students.length === 0 && (
        <div className="text-center py-12">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {selectedClassroom ? "此班級暫無學生" : "尚未建立學生"}
          </p>
        </div>
      )}
    </div>
  );
}

// Programs Content Component
function ProgramsContent({
  programs,
  classrooms,
  selectedClassroom,
  onClassroomFilter,
  onRefresh,
}: {
  programs: Program[];
  classrooms: ClassroomDetail[];
  selectedClassroom: number | null;
  onClassroomFilter: (classroomId: number | null) => void;
  onRefresh: () => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-gray-900">課程列表</h2>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              value={selectedClassroom || ""}
              onChange={(e) =>
                onClassroomFilter(
                  e.target.value ? Number(e.target.value) : null,
                )
              }
              className="px-3 py-2 border rounded-md text-sm"
            >
              <option value="">所有班級</option>
              {classrooms.map((classroom) => (
                <option key={classroom.id} value={classroom.id}>
                  {classroom.name}
                </option>
              ))}
            </select>
          </div>
          <Button onClick={onRefresh}>
            <BookOpen className="h-4 w-4 mr-2" />
            重新載入
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {programs.map((program) => (
          <Card key={program.id}>
            <CardHeader>
              <CardTitle>{program.name}</CardTitle>
              <CardDescription>{program.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">班級:</span>
                  <span className="font-medium">{program.classroom_name}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">等級:</span>
                  <span className="font-medium">{program.level}</span>
                </div>
                {program.estimated_hours && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">預計時數:</span>
                    <span className="font-medium">
                      {program.estimated_hours} 小時
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {programs.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">
            {selectedClassroom ? "此班級暫無課程" : "尚未建立課程"}
          </p>
        </div>
      )}
    </div>
  );
}
