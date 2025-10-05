import { ReactNode } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
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
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

interface TeacherProfile {
  id: number;
  email: string;
  name: string;
  phone?: string;
  is_demo: boolean;
  is_active: boolean;
}

interface TeacherLayoutProps {
  children: ReactNode;
}

export default function TeacherLayout({ children }: TeacherLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [teacherProfile, setTeacherProfile] = useState<TeacherProfile | null>(
    null,
  );

  useEffect(() => {
    fetchTeacherProfile();
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

  const handleLogout = () => {
    apiClient.logout();
    navigate("/teacher/login");
  };

  const sidebarItems = [
    {
      id: "dashboard",
      label: "儀表板",
      icon: Home,
      path: "/teacher/dashboard",
    },
    {
      id: "classrooms",
      label: "我的班級",
      icon: GraduationCap,
      path: "/teacher/classrooms",
    },
    {
      id: "students",
      label: "所有學生",
      icon: Users,
      path: "/teacher/students",
    },
    {
      id: "programs",
      label: "公版課程",
      icon: BookOpen,
      path: "/teacher/programs",
    },
    {
      id: "subscription",
      label: "訂閱管理",
      icon: CreditCard,
      path: "/teacher/subscription",
    },
  ];

  const isActive = (path: string) => location.pathname === path;

  // Sidebar content component (reused in both mobile and desktop)
  const SidebarContent = ({ onNavigate }: { onNavigate?: () => void }) => (
    <>
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        {!sidebarCollapsed && (
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Duotopia
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">教師後台</p>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="ml-auto md:block hidden h-10 min-h-10 w-10"
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
        <Button
          variant="ghost"
          size="sm"
          className={`w-full justify-start h-12 min-h-12 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 ${sidebarCollapsed ? "px-3" : "px-4"}`}
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
          {!sidebarCollapsed && <span className="ml-2">登出</span>}
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
              Duotopia
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">教師後台</p>
          </div>
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="sm" className="h-12 min-h-12 w-12">
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

      <div className="flex">
        {/* Desktop Sidebar */}
        <div
          className={`hidden md:flex bg-white dark:bg-gray-800 shadow-lg transition-all duration-300 ${sidebarCollapsed ? "w-16" : "w-64"} flex-col h-screen sticky top-0`}
        >
          <SidebarContent />
        </div>

        {/* Main Content */}
        <div className="flex-1 p-4 md:p-6 overflow-auto">{children}</div>
      </div>
    </div>
  );
}
