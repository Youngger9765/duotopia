import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import { 
  BookOpen, 
  Trophy, 
  Clock, 
  Target,
  LogOut,
  ChevronRight,
  Calendar
} from 'lucide-react';

interface Assignment {
  id: number;
  title: string;
  type: string;
  dueDate: string;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  score?: number;
}

export default function StudentDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useStudentAuthStore();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [stats, setStats] = useState({
    completedAssignments: 0,
    averageScore: 0,
    totalPracticeTime: 0,
    streak: 0
  });

  useEffect(() => {
    if (!user) {
      navigate('/student/login');
      return;
    }
    loadAssignments();
    loadStats();
  }, [user, navigate]);

  const loadAssignments = async () => {
    // Mock data - replace with API call
    setAssignments([
      {
        id: 1,
        title: 'Unit 1: Greetings 問候語練習',
        type: 'reading_recording',
        dueDate: '2025-09-01',
        status: 'pending'
      },
      {
        id: 2,
        title: 'Unit 2: Numbers 數字練習',
        type: 'reading_recording',
        dueDate: '2025-09-05',
        status: 'pending'
      },
      {
        id: 3,
        title: 'Daily Conversation 日常對話',
        type: 'speaking_scenario',
        dueDate: '2025-08-28',
        status: 'completed',
        score: 85
      }
    ]);
  };

  const loadStats = async () => {
    // Mock data - replace with API call
    setStats({
      completedAssignments: 12,
      averageScore: 82,
      totalPracticeTime: 240,
      streak: 5
    });
  };

  const handleLogout = () => {
    logout();
    navigate('/student/login');
  };

  const handleStartAssignment = (assignmentId: number) => {
    navigate(`/student/assignment/${assignmentId}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'overdue': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'in_progress': return '進行中';
      case 'overdue': return '已逾期';
      case 'pending': return '待完成';
      default: return status;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-blue-600">🚀 Duotopia</h1>
              <div className="text-gray-600">
                歡迎回來，<span className="font-semibold">{user?.name}</span>！
              </div>
            </div>
            <Button variant="ghost" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              登出
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">完成作業</p>
                  <p className="text-2xl font-bold">{stats.completedAssignments}</p>
                </div>
                <BookOpen className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">平均分數</p>
                  <p className="text-2xl font-bold">{stats.averageScore}分</p>
                </div>
                <Trophy className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">練習時間</p>
                  <p className="text-2xl font-bold">{stats.totalPracticeTime}分</p>
                </div>
                <Clock className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">連續天數</p>
                  <p className="text-2xl font-bold">{stats.streak}天</p>
                </div>
                <Target className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Assignments Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              我的作業
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {assignments.map((assignment) => (
                <div
                  key={assignment.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold">{assignment.title}</h3>
                      <Badge className={getStatusColor(assignment.status)}>
                        {getStatusText(assignment.status)}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        截止日期：{new Date(assignment.dueDate).toLocaleDateString('zh-TW')}
                      </span>
                      {assignment.score && (
                        <span className="flex items-center gap-1">
                          <Trophy className="h-3 w-3" />
                          得分：{assignment.score}分
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {assignment.status !== 'completed' && (
                    <Button
                      onClick={() => handleStartAssignment(assignment.id)}
                      className="ml-4"
                    >
                      開始練習
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  )}
                  
                  {assignment.status === 'completed' && (
                    <Button
                      variant="outline"
                      onClick={() => handleStartAssignment(assignment.id)}
                      className="ml-4"
                    >
                      查看結果
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Learning Progress */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              學習進度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">本週完成度</span>
                  <span className="text-sm font-semibold">75%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '75%' }}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">口說準確度</span>
                  <span className="text-sm font-semibold">82%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '82%' }}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">流暢度</span>
                  <span className="text-sm font-semibold">78%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full" style={{ width: '78%' }}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}