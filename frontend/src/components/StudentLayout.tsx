import { useState } from "react";
import { Outlet, Link, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { useTranslation } from "react-i18next";
import {
  BookOpen,
  Home,
  Trophy,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Calendar,
  BarChart3,
  MessageSquare,
} from "lucide-react";

export default function StudentLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useStudentAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/student/login");
  };

  const navItems = [
    {
      path: "/student/dashboard",
      label: t("studentLayout.nav.home"),
      icon: Home,
      disabled: false,
    },
    {
      path: "/student/assignments",
      label: t("studentLayout.nav.assignments"),
      icon: BookOpen,
      disabled: false,
    },
    {
      path: "/student/progress",
      label: t("studentLayout.nav.progress"),
      icon: BarChart3,
      disabled: true,
    },
    {
      path: "/student/achievements",
      label: t("studentLayout.nav.achievements"),
      icon: Trophy,
      disabled: true,
    },
    {
      path: "/student/calendar",
      label: t("studentLayout.nav.calendar"),
      icon: Calendar,
      disabled: true,
    },
    {
      path: "/student/messages",
      label: t("studentLayout.nav.messages"),
      icon: MessageSquare,
      disabled: true,
    },
  ];

  const bottomNavItems = [
    {
      path: "/student/profile",
      label: t("studentLayout.nav.profile"),
      icon: User,
      disabled: false,
    },
    {
      path: "/student/settings",
      label: t("studentLayout.nav.settings"),
      icon: Settings,
      disabled: true,
    },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
        fixed lg:static inset-y-0 left-0 z-50
        transform ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        lg:translate-x-0 transition-transform duration-300 ease-in-out
        w-64 bg-white shadow-lg flex flex-col
      `}
      >
        {/* Logo Section */}
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <Link to="/student/dashboard" className="flex items-center gap-2">
              <span className="text-2xl">🚀</span>
              <span className="text-xl font-bold text-blue-600">Duotopia</span>
            </Link>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* User Info */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                {user?.name?.charAt(0).toUpperCase() || "S"}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-sm">
                  {user?.name || t("studentLayout.userInfo.defaultStudent")}
                </p>
                <p className="text-xs text-gray-600">
                  {user?.classroom_name ||
                    t("studentLayout.userInfo.defaultClass")}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            const disabled = item.disabled;

            if (disabled) {
              return (
                <div
                  key={item.path}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 dark:text-gray-600 cursor-not-allowed opacity-50"
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                  {item.path === "/student/messages" && (
                    <span className="ml-auto bg-gray-300 text-gray-600 text-xs px-2 py-0.5 rounded-full">
                      2
                    </span>
                  )}
                </div>
              );
            }

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                  ${
                    active
                      ? "bg-blue-50 text-blue-600 font-medium dark:bg-blue-900/30 dark:text-blue-400"
                      : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  }
                `}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className="h-5 w-5" />
                <span>{item.label}</span>
                {item.path === "/student/messages" && (
                  <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                    2
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom Section */}
        <div className="p-4 border-t dark:border-gray-700 space-y-1">
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            const disabled = item.disabled;

            if (disabled) {
              return (
                <div
                  key={item.path}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 dark:text-gray-600 cursor-not-allowed opacity-50"
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </div>
              );
            }

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                  ${
                    active
                      ? "bg-blue-50 text-blue-600 font-medium dark:bg-blue-900/30 dark:text-blue-400"
                      : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                  }
                `}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className="h-5 w-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <Button
            variant="ghost"
            className="w-full justify-start text-gray-700 hover:bg-gray-100 px-4 py-3 mt-2"
            onClick={handleLogout}
          >
            <LogOut className="h-5 w-5 mr-3" />
            {t("studentLayout.nav.logout")}
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                  onClick={() => setSidebarOpen(true)}
                >
                  <Menu className="h-5 w-5" />
                </Button>

                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {navItems.find((item) => isActive(item.path))?.label ||
                      t("studentLayout.header.defaultTitle")}
                  </h1>
                  <p className="text-sm text-gray-600">
                    {t("studentLayout.header.welcome", { name: user?.name })}
                  </p>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="hidden sm:flex items-center gap-4">
                <div className="text-right">
                  <p className="text-sm text-gray-600">
                    {t("studentLayout.stats.streak")}
                  </p>
                  <p className="text-lg font-semibold text-green-600">
                    {t("studentLayout.stats.days", { count: 7 })}
                  </p>
                </div>
                <div className="h-10 w-px bg-gray-200" />
                <div className="text-right">
                  <p className="text-sm text-gray-600">
                    {t("studentLayout.stats.weekProgress")}
                  </p>
                  <p className="text-lg font-semibold text-blue-600">85%</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
