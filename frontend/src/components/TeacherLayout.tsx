import { ReactNode } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import DigitalTeachingToolbar from "@/components/teachingTools/DigitalTeachingToolbar";
import {
  LogOut,
  ChevronLeft,
  ChevronRight,
  Menu,
  Crown,
  User,
  CreditCard,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { getSidebarGroups } from "@/config/sidebarConfig";
import { useSidebarRoles } from "@/hooks/useSidebarRoles";
import { SidebarGroup } from "@/components/sidebar/SidebarGroup";

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
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set(["dashboard", "class-management", "account"]),
  );

  // 使用 hook 獲取 sidebar 配置和角色過濾
  const sidebarGroups = getSidebarGroups(t);
  const { visibleGroups } = useSidebarRoles(
    sidebarGroups,
    config,
    teacherProfile
  );

  useEffect(() => {
    fetchTeacherProfile();
    fetchConfig();
  }, []);

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(groupId)) {
        newSet.delete(groupId);
      } else {
        newSet.add(groupId);
      }
      return newSet;
    });
  };

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
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-1">
          {visibleGroups.map((group) => (
            <SidebarGroup
              key={group.id}
              group={group}
              isExpanded={expandedGroups.has(group.id)}
              isCollapsed={sidebarCollapsed}
              isActive={isActive}
              onToggle={() => toggleGroup(group.id)}
              onNavigate={onNavigate}
            />
          ))}
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
        {config?.enablePayment && (
          <Link to="/teacher/subscription" className="block mb-2" onClick={onNavigate}>
            <Button
              variant="ghost"
              size="sm"
              className={`w-full justify-start h-12 min-h-12 ${sidebarCollapsed ? "px-3" : "px-4"}`}
            >
              <CreditCard className="h-4 w-4" />
              {!sidebarCollapsed && (
                <span className="ml-2">{t("teacherLayout.nav.subscription")}</span>
              )}
            </Button>
          </Link>
        )}
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
