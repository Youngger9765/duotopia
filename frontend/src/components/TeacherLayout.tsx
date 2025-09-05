import { ReactNode } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Users,
  GraduationCap,
  BookOpen,
  LogOut,
  Home,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useState, useEffect } from 'react';

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
  const [teacherProfile, setTeacherProfile] = useState<TeacherProfile | null>(null);

  useEffect(() => {
    fetchTeacherProfile();
  }, []);

  const fetchTeacherProfile = async () => {
    try {
      const data = await apiClient.getTeacherDashboard() as { teacher: TeacherProfile };
      setTeacherProfile(data.teacher);
    } catch (err) {
      console.error('Failed to fetch teacher profile:', err);
      if (err instanceof Error && err.message.includes('401')) {
        handleLogout();
      }
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    navigate('/teacher/login');
  };

  const sidebarItems = [
    { id: 'dashboard', label: '儀表板', icon: Home, path: '/teacher/dashboard' },
    { id: 'classrooms', label: '我的班級', icon: GraduationCap, path: '/teacher/classrooms' },
    { id: 'students', label: '所有學生', icon: Users, path: '/teacher/students' },
    { id: 'programs', label: '公版課程', icon: BookOpen, path: '/teacher/programs' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex">
      {/* Sidebar */}
      <div className={`bg-white shadow-lg transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-64'} flex flex-col h-screen sticky top-0`}>
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
            className="ml-auto"
          >
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
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
                  <Link
                    to={item.path}
                    className="block"
                  >
                    <Button
                      variant={active ? 'default' : 'ghost'}
                      className={`w-full justify-start ${sidebarCollapsed ? 'px-3' : 'px-4'}`}
                    >
                      <Icon className="h-4 w-4" />
                      {!sidebarCollapsed && <span className="ml-2">{item.label}</span>}
                    </Button>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User Info & Logout */}
        <div className="p-4 border-t">
          {teacherProfile && (
            <div className="mb-4">
              {sidebarCollapsed ? (
                // 收合時顯示頭像
                <div className="flex justify-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">
                      {teacherProfile.name?.charAt(0) || 'T'}
                    </span>
                  </div>
                </div>
              ) : (
                // 展開時顯示完整資訊
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-lg font-medium text-blue-600">
                        {teacherProfile.name?.charAt(0) || 'T'}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{teacherProfile.name}</p>
                      <p className="text-xs text-gray-500">{teacherProfile.email}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            className={`w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 ${sidebarCollapsed ? 'px-3' : 'px-4'}`}
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            {!sidebarCollapsed && <span className="ml-2">登出</span>}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 overflow-auto">
        {children}
      </div>
    </div>
  );
}
