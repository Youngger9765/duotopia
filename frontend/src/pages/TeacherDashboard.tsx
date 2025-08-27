import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Users, 
  GraduationCap, 
  BookOpen, 
  LogOut,
  UserCheck,
  Clock,
  TrendingUp
} from 'lucide-react';
import { apiClient } from '../lib/api';

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
}

// Removed unused interfaces - they're in TeacherDashboardWithSidebar.tsx

export default function TeacherDashboard() {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
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
      console.error('Dashboard fetch error:', err);
      setError('載入儀表板失敗，請重新登入');
      // If unauthorized, redirect to login
      if (err instanceof Error && err.message.includes('401')) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  // Removed unused functions for old sidebar functionality

  const handleLogout = () => {
    apiClient.logout();
    navigate('/teacher/login');
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
            <Button onClick={() => navigate('/teacher/login')} className="w-full">
              返回登入
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
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Duotopia</h1>
              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">教師後台</span>
              {dashboardData.teacher.is_demo && (
                <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">Demo 帳號</span>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{dashboardData.teacher.name}</p>
                <p className="text-xs text-gray-500">{dashboardData.teacher.email}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                登出
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            歡迎回來，{dashboardData.teacher.name}！
          </h2>
          <p className="text-gray-600">
            管理您的班級、課程與學生學習進度
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">班級數量</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.classroom_count}</div>
              <p className="text-xs text-muted-foreground">
                管理中的班級
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">學生總數</CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.student_count}</div>
              <p className="text-xs text-muted-foreground">
                所有班級學生
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">課程計畫</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData.program_count}</div>
              <p className="text-xs text-muted-foreground">
                建立的課程
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Classrooms */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <GraduationCap className="h-5 w-5 mr-2" />
                我的班級
              </CardTitle>
              <CardDescription>
                目前管理的班級列表
              </CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData.classrooms.length === 0 ? (
                <p className="text-gray-500 text-center py-8">尚未建立班級</p>
              ) : (
                <div className="space-y-4">
                  {dashboardData.classrooms.map((classroom) => (
                    <div key={classroom.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h4 className="font-medium">{classroom.name}</h4>
                        <p className="text-sm text-gray-500">{classroom.description}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{classroom.student_count} 位學生</p>
                        <Button variant="outline" size="sm" className="mt-2">
                          管理
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <Button className="w-full mt-4">
                <Users className="h-4 w-4 mr-2" />
                建立新班級
              </Button>
            </CardContent>
          </Card>

          {/* Recent Students */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                最近活動學生
              </CardTitle>
              <CardDescription>
                各班級的學生列表
              </CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData.recent_students.length === 0 ? (
                <p className="text-gray-500 text-center py-8">尚無學生資料</p>
              ) : (
                <div className="space-y-3">
                  {dashboardData.recent_students.map((student) => (
                    <div key={student.id} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {student.name.charAt(0)}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-sm">{student.name}</p>
                          <p className="text-xs text-gray-500">{student.classroom_name}</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        <Clock className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <Button variant="outline" className="w-full mt-4">
                查看所有學生
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>快速動作</CardTitle>
            <CardDescription>
              常用功能快捷入口
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button variant="outline" className="h-20 flex flex-col">
                <BookOpen className="h-6 w-6 mb-2" />
                建立課程
              </Button>
              <Button variant="outline" className="h-20 flex flex-col">
                <Users className="h-6 w-6 mb-2" />
                管理學生
              </Button>
              <Button variant="outline" className="h-20 flex flex-col">
                <TrendingUp className="h-6 w-6 mb-2" />
                查看統計
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}