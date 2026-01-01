import { ReactNode, useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  LogOut,
  ChevronLeft,
  ChevronRight,
  Building2,
  School,
  Users,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { OrganizationProvider } from "@/contexts/OrganizationContext";

interface OrganizationLayoutProps {
  children?: ReactNode;
}

export default function OrganizationLayout({
  children,
}: OrganizationLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { token, logout: storeLogout } = useTeacherAuthStore();

  // Check permissions on mount
  useEffect(() => {
    const checkPermissions = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/teachers/me/roles`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );

        if (response.ok) {
          const data = await response.json();
          const hasOrgRole = data.all_roles?.some((role: string) =>
            ["org_owner", "org_admin", "school_admin"].includes(role),
          );

          if (!hasOrgRole) {
            // No organization role, redirect to teacher dashboard
            navigate("/teacher/dashboard", { replace: true });
          }
        }
      } catch (error) {
        console.error("Failed to check permissions:", error);
      }
    };

    if (token) {
      checkPermissions();
    }
  }, [token, navigate]);

  const handleLogout = () => {
    apiClient.logout();
    storeLogout();
    navigate("/teacher/login");
  };

  return (
    <OrganizationProvider>
      <div className="flex h-screen bg-gray-50">
        {/* Sidebar */}
        <aside
          className={cn(
            "flex flex-col border-r bg-white transition-all duration-300",
            sidebarCollapsed ? "w-16" : "w-64",
          )}
        >
          {/* Sidebar Header */}
          <div className="flex h-16 items-center justify-between border-b px-4">
            {!sidebarCollapsed && (
              <div className="flex items-center gap-2">
                <Building2 className="h-6 w-6 text-primary" />
                <span className="font-semibold">組織管理</span>
              </div>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="ml-auto"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Sidebar Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            <div className="space-y-2">
              <Button
                variant={
                  location.pathname === "/organization/dashboard"
                    ? "default"
                    : "ghost"
                }
                className={cn(
                  "w-full justify-start",
                  sidebarCollapsed && "justify-center px-2",
                )}
                onClick={() => navigate("/organization/dashboard")}
              >
                <Building2 className="h-4 w-4" />
                {!sidebarCollapsed && <span className="ml-2">組織架構</span>}
              </Button>

              <Button
                variant={
                  location.pathname.includes("/organization/schools") ||
                  location.pathname.includes("/schools")
                    ? "default"
                    : "ghost"
                }
                className={cn(
                  "w-full justify-start",
                  sidebarCollapsed && "justify-center px-2",
                )}
                onClick={() => navigate("/organization/schools")}
              >
                <School className="h-4 w-4" />
                {!sidebarCollapsed && <span className="ml-2">學校管理</span>}
              </Button>

              <Button
                variant={
                  location.pathname.includes("/organization/teachers") ||
                  location.pathname.includes("/teachers")
                    ? "default"
                    : "ghost"
                }
                className={cn(
                  "w-full justify-start",
                  sidebarCollapsed && "justify-center px-2",
                )}
                onClick={() => navigate("/organization/teachers")}
              >
                <Users className="h-4 w-4" />
                {!sidebarCollapsed && <span className="ml-2">教師管理</span>}
              </Button>
            </div>
          </nav>

          {/* Sidebar Footer */}
          <div className="border-t p-4">
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50",
                sidebarCollapsed && "justify-center px-2",
              )}
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              {!sidebarCollapsed && <span className="ml-2">登出</span>}
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Top Bar */}
          <header className="flex h-16 items-center justify-between border-b bg-white px-6">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold">組織管理後台</h1>
            </div>
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate("/teacher/dashboard")}
              >
                切換到教師後台
              </Button>
            </div>
          </header>

          {/* Content Area */}
          <main className="flex-1 overflow-y-auto p-6">
            {children || <Outlet />}
          </main>
        </div>
      </div>
    </OrganizationProvider>
  );
}
