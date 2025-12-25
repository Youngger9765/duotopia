import { ReactNode } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import DigitalTeachingToolbar from "@/components/teachingTools/DigitalTeachingToolbar";
import {
  Users,
  GraduationCap,
  BookOpen,
  LogOut,
  Home,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  Menu,
  Crown,
  User,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

interface TeacherProfile {
  id: number;
  email: string;
  name: string;
  phone?: string;
  is_demo: boolean;
  is_active: boolean;
  is_admin?: boolean;
}

interface SystemConfig {
  enablePayment: boolean;
  environment: string;
}

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
  adminOnly?: boolean;
}

interface TeacherLayoutProps {
  children: ReactNode;
}

export default function TeacherLayout({ children }: TeacherLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [teacherProfile, setTeacherProfile] = useState<TeacherProfile | null>(
    null,
  );
  const [config, setConfig] = useState<SystemConfig | null>(null);

  useEffect(() => {
    fetchTeacherProfile();
    fetchConfig();
  }, []);

  const fetchTeacherProfile = async () => {
    try {
      const data = (await apiClient.getTeacherDashboard()) as {
        teacher: TeacherProfile;
      };
      setTeacherProfile(data.teacher);
    } catch (err) {
      console.error("Failed to fetch teacher profile:", err);
      if (err instanceof Error && err.message.includes("401")) {
        handleLogout();
      }
    }
  };

  const fetchConfig = async () => {
    try {
      const data = await apiClient.getConfig();
      setConfig(data);
    } catch (err) {
      console.error("Failed to fetch system config:", err);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    navigate("/teacher/login");
  };

  const allSidebarItems: SidebarItem[] = [
    {
      id: "dashboard",
      label: t("teacherLayout.nav.dashboard"),
      icon: Home,
      path: "/teacher/dashboard",
    },
    {
      id: "classrooms",
      label: t("teacherLayout.nav.myClassrooms"),
      icon: GraduationCap,
      path: "/teacher/classrooms",
    },
    {
      id: "students",
      label: t("teacherLayout.nav.allStudents"),
      icon: Users,
      path: "/teacher/students",
    },
    {
      id: "programs",
      label: t("teacherLayout.nav.publicPrograms"),
      icon: BookOpen,
      path: "/teacher/programs",
    },
    {
      id: "subscription",
      label: t("teacherLayout.nav.subscription"),
      icon: CreditCard,
      path: "/teacher/subscription",
    },
  ];

  // 根據系統配置過濾選單項目
  const sidebarItems = allSidebarItems.filter((item) => {
    // 如果是訂閱選單，只在付款功能啟用時顯示
    if (item.id === "subscription") {
      return config?.enablePayment === true;
    }
    // 如果是 Admin 選單，只有 is_admin 的人才看得到
    if (item.adminOnly) {
      return teacherProfile?.is_admin === true;
    }
    return true;
  });

  const isActive = (path: string) => location.pathname === path;

  // Sidebar content component (reused in both mobile and desktop)
  const SidebarContent = ({ onNavigate }: { onNavigate?: () => void }) => (
    <>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-start justify-between mb-3">
          {!sidebarCollapsed ? (
            <div className="flex-1">
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {t("teacherLayout.title")}
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("teacherLayout.subtitle")}
              </p>
            </div>
          ) : (
            <div className="flex-1" />
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="md:flex hidden h-8 w-8 p-0 items-center justify-center flex-shrink-0"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>
        {!sidebarCollapsed && (
          <div>
            <LanguageSwitcher />
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <li key={item.id}>
                <Link to={item.path} className="block" onClick={onNavigate}>
                  <Button
                    variant={active ? "default" : "ghost"}
                    className={`w-full justify-start h-12 min-h-12 ${sidebarCollapsed ? "px-3" : "px-4"}`}
                  >
                    <Icon className="h-4 w-4" />
                    {!sidebarCollapsed && (
                      <span className="ml-2">{item.label}</span>
                    )}
                  </Button>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User Info & Logout */}
      <div className="p-4 border-t dark:border-gray-700">
        {teacherProfile && (
          <div className="mb-4">
            {sidebarCollapsed ? (
              <div className="flex justify-center">
                <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    {teacherProfile.name?.charAt(0) || "T"}
                  </span>
                </div>
              </div>
            ) : (
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                    <span className="text-lg font-medium text-blue-600 dark:text-blue-400">
                      {teacherProfile.name?.charAt(0) || "T"}
                    </span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {teacherProfile.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {teacherProfile.email}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        {teacherProfile?.is_admin && (
          <Link to="/admin" className="block mb-2" onClick={onNavigate}>
            <Button
              variant="ghost"
              size="sm"
              className={`w-full justify-start h-12 min-h-12 ${sidebarCollapsed ? "px-3" : "px-4"}`}
            >
              <Crown className="h-4 w-4 text-yellow-500" />
              {!sidebarCollapsed && (
                <span className="ml-2">
                  {t("teacherLayout.nav.systemAdmin")}
                </span>
              )}
            </Button>
          </Link>
        )}
        <Link to="/teacher/profile" className="block mb-2" onClick={onNavigate}>
          <Button
            variant="ghost"
            size="sm"
            className={`w-full justify-start h-12 min-h-12 ${sidebarCollapsed ? "px-3" : "px-4"}`}
          >
            <User className="h-4 w-4" />
            {!sidebarCollapsed && (
              <span className="ml-2">{t("teacherLayout.nav.profile")}</span>
            )}
          </Button>
        </Link>
        <Button
          variant="ghost"
          size="sm"
          className={`w-full justify-start h-12 min-h-12 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 ${sidebarCollapsed ? "px-3" : "px-4"}`}
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
          {!sidebarCollapsed && <span className="ml-2">{t("nav.logout")}</span>}
        </Button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Mobile Header */}
      <div className="md:hidden bg-white dark:bg-gray-800 border-b dark:border-gray-700 sticky top-0 z-50">
        <div className="flex items-center justify-between p-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {t("teacherLayout.title")}
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("teacherLayout.subtitle")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-12 min-h-12 w-12"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64 p-0">
                <div className="flex flex-col h-full bg-white dark:bg-gray-800">
                  <SidebarContent onNavigate={() => {}} />
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Desktop Sidebar */}
        <div
          className={`hidden md:flex bg-white dark:bg-gray-800 shadow-lg transition-all duration-300 ${sidebarCollapsed ? "w-16" : "w-64"} flex-col h-screen sticky top-0`}
        >
          <SidebarContent />
        </div>

        {/* Main Content */}
        <div className="flex-1 p-4 md:p-6 overflow-auto relative">
          <DigitalTeachingToolbar />
          {children}
        </div>
      </div>
    </div>
  );
}
