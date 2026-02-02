import { ReactNode, useMemo, useCallback, useRef } from "react";
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
  Building2,
} from "lucide-react";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { apiClient } from "@/lib/api";
import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { getSidebarGroups } from "@/config/sidebarConfig";
import { useSidebarRoles } from "@/hooks/useSidebarRoles";
import { SidebarGroup } from "@/components/sidebar/SidebarGroup";
import { WorkspaceProvider, useWorkspace } from "@/contexts/WorkspaceContext";
import { WorkspaceSwitcher } from "@/components/workspace";

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

// Inner component that uses workspace context
interface TeacherLayoutInnerProps extends TeacherLayoutProps {
  teacherProfile: TeacherProfile;
}

function TeacherLayoutInner({ children, teacherProfile }: TeacherLayoutInnerProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [config, setConfig] = useState<SystemConfig | null>(null);

  // Get user role and roles from auth store
  const user = useTeacherAuthStore((state) => state.user);
  const userRoles = useTeacherAuthStore((state) => state.userRoles);

  // Get workspace context
  const { mode, selectedSchool } = useWorkspace();

  // Check if user has organization management role
  const hasOrgRole = useMemo(() => {
    const managementRoles = [
      "org_owner",
      "org_admin",
      "school_admin",
      "school_director",
    ];

    // Check if user has any management role in their roles array
    const hasRole = userRoles.some((role) => managementRoles.includes(role));

    // Debug logging
    console.log("🔍 TeacherLayout Debug:");
    console.log("  userRoles:", userRoles);
    console.log("  hasOrgRole:", hasRole);
    console.log("  user.role (single):", user?.role);

    return hasRole;
  }, [userRoles, user?.role]);

  // Determine which sidebar items are read-only
  const readOnlyItemIds = useMemo(() => {
    // In organization mode with a school selected, classrooms and students are read-only
    if (mode === 'organization' && selectedSchool) {
      return ['classrooms', 'students'];
    }
    return [];
  }, [mode, selectedSchool]);

  // 使用 hook 獲取 sidebar 配置和角色過濾
  const sidebarGroups = useMemo(() => getSidebarGroups(t), [t]);
  const { visibleGroups } = useSidebarRoles(
    sidebarGroups,
    config,
    teacherProfile,
  );

  // ✅ 根據 workspace mode 過濾 sidebar 內容
  // 個人模式：過濾掉組織相關功能（組織架構、學校教材）
  // 機構模式：顯示所有功能
  const filteredGroups = useMemo(() => {
    return visibleGroups
      .filter((group) => {
        // 個人模式下過濾掉組織管理 group
        if (mode === 'personal' && group.id === "organization-hub") {
          return false;
        }
        return true;
      })
      .map((group) => {
        // 個人模式下過濾掉「學校教材」item
        if (mode === 'personal' && group.id === 'class-management') {
          return {
            ...group,
            items: group.items.filter((item) => item.id !== 'school-materials'),
          };
        }
        return group;
      });
  }, [visibleGroups, mode]);

  const handleLogout = useCallback(() => {
    apiClient.logout();
    navigate("/teacher/login");
  }, [navigate]);

  // ✅ 使用 useRef 防止重複執行
  const hasFetchedConfig = useRef(false);

  useEffect(() => {
    // 只在 mount 時執行一次
    if (hasFetchedConfig.current) return;
    hasFetchedConfig.current = true;

    const fetchConfig = async () => {
      try {
        const data = await apiClient.getConfig();
        setConfig(data);
      } catch (err) {
        console.error("Failed to fetch system config:", err);
      }
    };

    fetchConfig();
  }, []); // 只在 mount 時執行

  const isActive = useCallback(
    (path: string) => location.pathname === path,
    [location.pathname],
  );

  // Memoize SidebarContent to prevent unnecessary re-renders
  const SidebarContent = useMemo(
    () =>
      ({ onNavigate }: { onNavigate?: () => void }) => (
        <>
          {/* Header */}
          <div className="p-4 border-b dark:border-gray-700">
            <div className="flex items-start justify-between">
              {!sidebarCollapsed ? (
                <div className="flex-1">
                  <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                    {t("teacherLayout.title")}
                  </h1>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("teacherLayout.subtitle")}
                  </p>
                </div>
              ) : null}
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
          </div>

          {/* Workspace Switcher - Personal / Organization Tabs */}
          {!sidebarCollapsed && teacherProfile && (
            <div className="px-3 pt-4">
              <WorkspaceSwitcher />
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-4 overflow-y-auto">
            <ul className="space-y-1">
              {filteredGroups.map((group) => (
                <SidebarGroup
                  key={group.id}
                  group={group}
                  isCollapsed={sidebarCollapsed}
                  isActive={isActive}
                  readOnlyItemIds={readOnlyItemIds}
                  onNavigate={onNavigate}
                />
              ))}
            </ul>
          </nav>

          {/* User Info & Logout */}
          <div className="p-4 border-t dark:border-gray-700">
            {/* 語言切換器 */}
            {!sidebarCollapsed && (
              <div className="mb-4">
                <LanguageSwitcher />
              </div>
            )}

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
            <Link
              to="/teacher/profile"
              className="block mb-2"
              onClick={onNavigate}
            >
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
              <Link
                to="/teacher/subscription"
                className="block mb-2"
                onClick={onNavigate}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className={`w-full justify-start h-12 min-h-12 ${sidebarCollapsed ? "px-3" : "px-4"}`}
                >
                  <CreditCard className="h-4 w-4" />
                  {!sidebarCollapsed && (
                    <span className="ml-2">
                      {t("teacherLayout.nav.subscription")}
                    </span>
                  )}
                </Button>
              </Link>
            )}
            {hasOrgRole && (
              <Link
                to="/organization/dashboard"
                className="block mb-2"
                onClick={onNavigate}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className={`w-full justify-start h-12 min-h-12 ${sidebarCollapsed ? "px-3" : "px-4"}`}
                >
                  <Building2 className="h-4 w-4 text-blue-600" />
                  {!sidebarCollapsed && <span className="ml-2">組織管理</span>}
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
              {!sidebarCollapsed && (
                <span className="ml-2">{t("nav.logout")}</span>
              )}
            </Button>
          </div>
        </>
      ),
    [
      sidebarCollapsed,
      t,
      setSidebarCollapsed,
      filteredGroups,
      isActive,
      readOnlyItemIds,
      teacherProfile,
      config,
      hasOrgRole,
      handleLogout,
    ],
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

// Wrapper component that provides workspace context
export default function TeacherLayout({ children }: TeacherLayoutProps) {
  const [teacherProfile, setTeacherProfile] = useState<TeacherProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasFetchedProfile = useRef(false);

  useEffect(() => {
    if (hasFetchedProfile.current) return;
    hasFetchedProfile.current = true;

    const fetchTeacherProfile = async () => {
      try {
        const data = (await apiClient.getTeacherDashboard()) as {
          teacher: TeacherProfile;
        };
        setTeacherProfile(data.teacher);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch teacher profile:", err);
        setError("無法載入資料，請檢查網路連線後重試");
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeacherProfile();
  }, []);

  // Show error state if profile fetch failed
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center" role="alert" aria-live="assertive">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()} autoFocus>
            重試
          </Button>
        </div>
      </div>
    );
  }

  // Show loading state while fetching teacher profile
  if (isLoading || !teacherProfile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  return (
    <WorkspaceProvider teacherId={teacherProfile.id}>
      <TeacherLayoutInner teacherProfile={teacherProfile}>{children}</TeacherLayoutInner>
    </WorkspaceProvider>
  );
}
