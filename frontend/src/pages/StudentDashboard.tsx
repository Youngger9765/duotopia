import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import { toast } from 'sonner';
import {
  BookOpen,
  Trophy,
  Clock,
  Target,
  ChevronRight,
  Calendar,
  Mail,
  X,
  CheckCircle,
  User,
  Loader2
} from 'lucide-react';
import { Assignment } from '@/types';

export default function StudentDashboard() {
  const navigate = useNavigate();
  const { user, token } = useStudentAuthStore();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [stats, setStats] = useState({
    completedAssignments: 0,
    averageScore: 0,
    totalPracticeTime: 0,
    practiceDays: 0
  });
  const [showEmailPrompt, setShowEmailPrompt] = useState(false);
  const [showEmailSetup, setShowEmailSetup] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [emailInitialized, setEmailInitialized] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [currentEmail, setCurrentEmail] = useState('');
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  useEffect(() => {
    if (!user || !token) {
      navigate('/student/login');
      return;
    }
    loadAssignments();
    loadStats();
    loadEmailStatus();
  }, [user, token, navigate]);

  const loadAssignments = async () => {
    try {
      // Directly use fetch with student token
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/students/assignments`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAssignments(data as Assignment[]);
    } catch (error) {
      console.error('Failed to load assignments:', error);
      toast.error('無法載入作業列表');
      // Use mock data as fallback
      setAssignments([
        {
          id: 1,
          title: 'Unit 1: Greetings 問候語練習',
          content_id: 1,
          content: {
            type: 'reading_assessment',
            title: 'Greetings'
          },
          status: 'NOT_STARTED',
          due_date: '2025-09-01',
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          title: 'Unit 2: Numbers 數字練習',
          content_id: 2,
          content: {
            type: 'reading_assessment',
            title: 'Numbers'
          },
          status: 'NOT_STARTED',
          due_date: '2025-09-05',
          created_at: new Date().toISOString()
        },
        {
          id: 3,
          title: 'Daily Conversation 日常對話',
          content_id: 3,
          content: {
            type: 'speaking_scenario',
            title: 'Daily Conversation'
          },
          status: 'GRADED',
          due_date: '2025-08-28',
          score: 85,
          created_at: new Date().toISOString()
        }
      ]);
    }
  };

  const loadStats = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/students/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setStats({
        completedAssignments: data.completedAssignments || 0,
        averageScore: data.averageScore || 0,
        totalPracticeTime: data.totalPracticeTime || 0,
        practiceDays: data.practiceDays || 0
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
      // Fallback to zero if API fails
      setStats({
        completedAssignments: 0,
        averageScore: 0,
        totalPracticeTime: 0,
        practiceDays: 0
      });
    }
  };

  const loadEmailStatus = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      // 使用 /me 端點來獲取當前學生資訊
      const response = await fetch(`${apiUrl}/api/students/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();

        // 如果有 email，預填到輸入框
        if (data.email && !emailInitialized) {
          setNewEmail(data.email);
          setCurrentEmail(data.email);
          setEmailInitialized(true);
        }

        // 設定驗證狀態
        setEmailVerified(data.email_verified === true);

        // 如果沒有驗證過 email，就顯示提醒
        if (!data.email_verified) {
          setShowEmailPrompt(true);
        }
      }
    } catch (error) {
      console.error('Failed to load email status:', error);
    }
  };

  const handleStartAssignment = (assignmentId: number) => {
    navigate(`/student/assignment/${assignmentId}/detail`);
  };

  const handleViewAllAssignments = () => {
    navigate('/student/assignments');
  };

  const handleEmailPromptClose = () => {
    setShowEmailPrompt(false);
    // 不記錄，下次登入還是會顯示
  };

  const handleEmailUpdate = async () => {
    if (!newEmail || !newEmail.includes('@')) {
      toast.error('請輸入有效的 Email 地址');
      return;
    }

    setIsSendingEmail(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      // 使用正確的 update-email 端點
      const response = await fetch(`${apiUrl}/api/students/update-email`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: newEmail })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.verification_sent) {
          toast.success('驗證信已發送！請檢查您的信箱');
        } else {
          toast.success('Email 已更新');
        }
        setShowEmailPrompt(false);
        setShowEmailSetup(false);
        // 重新載入 email 狀態
        loadEmailStatus();
      } else {
        const error = await response.text();
        toast.error(`設定失敗：${error}`);
      }
    } catch (error) {
      console.error('Failed to update email:', error);
      toast.error('設定失敗，請稍後再試');
    } finally {
      setIsSendingEmail(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'GRADED':
      case 'RETURNED': return 'bg-green-100 text-green-800';
      case 'SUBMITTED': return 'bg-yellow-100 text-yellow-800';
      case 'IN_PROGRESS': return 'bg-blue-100 text-blue-800';
      case 'NOT_STARTED': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'NOT_STARTED': return '待完成';
      case 'IN_PROGRESS': return '進行中';
      case 'SUBMITTED': return '已提交';
      case 'GRADED': return '已評分';
      case 'RETURNED': return '已退回';
      default: return status;
    }
  };

  return (
    <div className="p-4 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Welcome Message */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            你好，{user?.name || '同學'}！歡迎回到 Duotopia 🚀
          </h1>
          <p className="text-gray-600">繼續你的英語學習之旅吧</p>

          {/* Email 狀態顯示 */}
          {currentEmail && (
            <div className="mt-4 flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm bg-gray-50 px-3 py-2 rounded-lg">
                <Mail className="h-4 w-4 text-gray-500" />
                <span className="text-gray-700">{currentEmail}</span>
                {emailVerified ? (
                  <div className="flex items-center gap-1 text-blue-600">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-xs font-medium">已驗證</span>
                  </div>
                ) : (
                  <Badge variant="outline" className="text-xs text-orange-600 border-orange-300">
                    待驗證
                  </Badge>
                )}
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => navigate('/student/profile')}
                className="text-xs flex items-center gap-1 hover:bg-gray-100"
              >
                <User className="h-3 w-3" />
                個人資料
              </Button>
            </div>
          )}
        </div>

        {/* Email Setup Form */}
        {(showEmailPrompt || showEmailSetup) && (
          <Card className="mb-6 bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="bg-blue-100 p-2 rounded-full">
                    <Mail className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-blue-900 mb-3">
                      📧 設定 Email 通知
                    </h3>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-blue-800 mb-2">
                          你的 Email 地址
                        </label>
                        <Input
                          type="email"
                          value={newEmail}
                          onChange={(e) => setNewEmail(e.target.value)}
                          placeholder="請輸入你的 Email 地址"
                          className="border-blue-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>

                      <div className="text-xs text-blue-600 bg-blue-100 p-2 rounded">
                        <p>📌 點擊「發送驗證信」後，會發送驗證信到你的 Email，點擊信中連結即可完成設定</p>
                      </div>

                      <div className="flex gap-2 pt-2">
                        <Button
                          size="sm"
                          onClick={handleEmailUpdate}
                          disabled={isSendingEmail || !newEmail || !newEmail.includes('@')}
                          className="bg-gray-800 hover:bg-gray-900 text-white disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:hover:bg-gray-600"
                        >
                          {isSendingEmail ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              發送中...
                            </>
                          ) : (
                            '驗證我的 Email'
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleEmailPromptClose}
                  className="text-blue-400 hover:text-blue-600 hover:bg-blue-100"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">完成作業</p>
                  <p className="text-lg sm:text-2xl font-bold">{stats.completedAssignments}</p>
                </div>
                <BookOpen className="h-6 w-6 sm:h-8 sm:w-8 text-blue-500 flex-shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">平均分數</p>
                  <p className="text-lg sm:text-2xl font-bold">{stats.averageScore}分</p>
                </div>
                <Trophy className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-500 flex-shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">練習時間</p>
                  <p className="text-lg sm:text-2xl font-bold">{stats.totalPracticeTime}分</p>
                </div>
                <Clock className="h-6 w-6 sm:h-8 sm:w-8 text-green-500 flex-shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">練習天數</p>
                  <p className="text-lg sm:text-2xl font-bold">{stats.practiceDays}天</p>
                </div>
                <Target className="h-6 w-6 sm:h-8 sm:w-8 text-purple-500 flex-shrink-0" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Assignments Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                我的作業
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={handleViewAllAssignments}
                className="flex items-center gap-2"
              >
                查看全部
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
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
                      <Badge className={getStatusColor(assignment.status || '')}>
                        {getStatusText(assignment.status || '')}
                      </Badge>
                      {assignment.content && (
                        <span className="text-xs text-gray-500">
                          ({assignment.content.type === 'reading_assessment' ? '朗讀評測' : assignment.content.type})
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      {assignment.due_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          截止日期：{new Date(assignment.due_date).toLocaleDateString('zh-TW')}
                        </span>
                      )}
                      {assignment.score !== undefined && (
                        <span className="flex items-center gap-1">
                          <Trophy className="h-3 w-3" />
                          得分：{assignment.score}分
                        </span>
                      )}
                    </div>
                    {assignment.instructions && (
                      <p className="text-sm text-gray-500 mt-1">{assignment.instructions}</p>
                    )}
                  </div>

                  {(assignment.status === 'NOT_STARTED' || assignment.status === 'IN_PROGRESS') && (
                    <Button
                      onClick={() => handleStartAssignment(assignment.id)}
                      className="ml-4"
                    >
                      開始練習
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  )}

                  {(assignment.status === 'SUBMITTED' || assignment.status === 'GRADED' || assignment.status === 'RETURNED') && (
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
      </div>
    </div>
  );
}
