import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import { toast } from 'sonner';
import {
  BookOpen,
  Clock,
  Calendar,
  Play,
  CheckCircle,
  AlertCircle,
  BarChart3,
  ChevronRight
} from 'lucide-react';
import {
  StudentAssignmentCard,
  AssignmentStatusEnum
} from '@/types';

export default function StudentAssignmentList() {
  const navigate = useNavigate();
  const { token, user } = useStudentAuthStore();
  const [assignments, setAssignments] = useState<StudentAssignmentCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('active');
  const [stats, setStats] = useState({
    totalAssignments: 0,
    completedAssignments: 0,
    inProgressAssignments: 0,
    averageScore: 0
  });

  useEffect(() => {
    if (!user || !token) {
      navigate('/student/login');
      return;
    }
    loadAssignments();
  }, [user, token, navigate]);

  const loadAssignments = async () => {
    try {
      setLoading(true);
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

      // Transform data to match StudentAssignmentCard type
      interface AssignmentData {
        id: number;
        title: string;
        status?: string;
        due_date?: string;
        assigned_at?: string;
        submitted_at?: string;
        score?: number;
        feedback?: string;
        content_id?: number;
        classroom_id: number;
      }
      const assignmentCards: StudentAssignmentCard[] = data.map((assignment: AssignmentData) => ({
        id: assignment.id,
        title: assignment.title,
        status: assignment.status || 'NOT_STARTED',
        due_date: assignment.due_date,
        assigned_at: assignment.assigned_at,
        submitted_at: assignment.submitted_at,
        score: assignment.score,
        feedback: assignment.feedback,
        content_id: assignment.content_id,
        classroom_id: assignment.classroom_id,
        progress_percentage: 0,
        total_contents: 1,
        completed_contents: assignment.status === 'GRADED' || assignment.status === 'SUBMITTED' ? 1 : 0
      }));

      setAssignments(assignmentCards);

      // Calculate stats
      const completed = assignmentCards.filter(a => a.status === 'GRADED').length;
      const inProgress = assignmentCards.filter(a => a.status === 'IN_PROGRESS').length;
      const scores = assignmentCards.filter(a => a.score).map(a => a.score || 0);
      const avgScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;

      setStats({
        totalAssignments: assignmentCards.length,
        completedAssignments: completed,
        inProgressAssignments: inProgress,
        averageScore: Math.round(avgScore)
      });
    } catch (error) {
      console.error('Failed to load assignments:', error);
      toast.error('無法載入作業列表');
    } finally {
      setLoading(false);
    }
  };

  const getStatusDisplay = (status: AssignmentStatusEnum) => {
    switch (status) {
      case 'NOT_STARTED':
        return { text: '未開始', color: 'bg-gray-100 text-gray-800' };
      case 'IN_PROGRESS':
        return { text: '進行中', color: 'bg-blue-100 text-blue-800' };
      case 'SUBMITTED':
        return { text: '已提交', color: 'bg-yellow-100 text-yellow-800' };
      case 'GRADED':
        return { text: '已評分', color: 'bg-green-100 text-green-800' };
      case 'RETURNED':
        return { text: '已退回', color: 'bg-orange-100 text-orange-800' };
      case 'RESUBMITTED':
        return { text: '重新提交', color: 'bg-purple-100 text-purple-800' };
      default:
        return { text: status, color: 'bg-gray-100 text-gray-800' };
    }
  };

  const getStatusIcon = (status: AssignmentStatusEnum) => {
    switch (status) {
      case 'NOT_STARTED':
        return <Clock className="h-4 w-4" />;
      case 'IN_PROGRESS':
        return <Play className="h-4 w-4" />;
      case 'SUBMITTED':
      case 'RESUBMITTED':
        return <CheckCircle className="h-4 w-4" />;
      case 'GRADED':
        return <BarChart3 className="h-4 w-4" />;
      case 'RETURNED':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <BookOpen className="h-4 w-4" />;
    }
  };

  const formatDueDate = (dueDate?: string) => {
    if (!dueDate) return null;

    const due = new Date(dueDate);
    const now = new Date();
    const diffTime = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { text: `已逾期 ${Math.abs(diffDays)} 天`, isOverdue: true };
    } else if (diffDays === 0) {
      return { text: '今天到期', isOverdue: false };
    } else if (diffDays <= 3) {
      return { text: `${diffDays} 天後到期`, isOverdue: false };
    } else {
      return { text: due.toLocaleDateString('zh-TW'), isOverdue: false };
    }
  };

  const handleStartAssignment = (assignmentId: number) => {
    navigate(`/student/assignment/${assignmentId}/detail`);
  };

  const renderAssignmentCard = (assignment: StudentAssignmentCard) => {
    const statusDisplay = getStatusDisplay(assignment.status);
    const statusIcon = getStatusIcon(assignment.status);
    const dueDateInfo = formatDueDate(assignment.due_date);
    const canStart = assignment.status === 'NOT_STARTED' || assignment.status === 'IN_PROGRESS';

    return (
      <Card
        key={assignment.id}
        className="hover:shadow-lg transition-all duration-200 border-gray-200"
        data-testid="assignment-card"
      >
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <CardTitle className="text-lg font-semibold text-gray-900 mb-1">
                {assignment.title}
              </CardTitle>
              {assignment.classroom_name && (
                <p className="text-sm text-gray-500">
                  {assignment.classroom_name} {assignment.teacher_name && `• ${assignment.teacher_name}`}
                </p>
              )}
            </div>
            <Badge className={`${statusDisplay.color} flex items-center gap-1 px-3 py-1`}>
              {statusIcon}
              <span className="font-medium">{statusDisplay.text}</span>
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {/* Progress */}
          {(assignment.status !== 'NOT_STARTED') && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-600 font-medium">完成進度</span>
                <span className="font-semibold text-gray-900">
                  {assignment.completed_count || 0} / {assignment.content_count || 1} 個活動
                </span>
              </div>
              <Progress
                value={assignment.progress_percentage || 0}
                className="h-2.5 bg-gray-200"
              />
            </div>
          )}

          {/* Details */}
          <div className="flex flex-wrap gap-3 text-sm">
            <div className="flex items-center gap-1.5 text-gray-600">
              <BookOpen className="h-4 w-4 text-gray-400" />
              <span>{assignment.content_type || '朗讀練習'}</span>
            </div>
            {assignment.estimated_time && (
              <div className="flex items-center gap-1.5 text-gray-600">
                <Clock className="h-4 w-4 text-gray-400" />
                <span>{assignment.estimated_time}</span>
              </div>
            )}
            {dueDateInfo && (
              <div className={`flex items-center gap-1.5 font-medium ${
                dueDateInfo.isOverdue ? 'text-red-600' : 'text-gray-700'
              }`}>
                <Calendar className={`h-4 w-4 ${dueDateInfo.isOverdue ? 'text-red-500' : 'text-gray-400'}`} />
                <span>{dueDateInfo.text}</span>
              </div>
            )}
          </div>

          {/* Score */}
          {assignment.score !== undefined && assignment.status === 'GRADED' && (
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium text-green-600">
                分數: {assignment.score}
              </span>
            </div>
          )}

          {/* Action Button */}
          <div className="pt-3 mt-2 border-t border-gray-100">
            <Button
              onClick={() => handleStartAssignment(assignment.id)}
              disabled={!canStart && assignment.status !== 'GRADED' && assignment.status !== 'SUBMITTED' && assignment.status !== 'RETURNED'}
              className={`w-full font-medium transition-all ${
                canStart || assignment.status === 'RETURNED'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
              data-testid="assignment-action-button"
            >
              {assignment.status === 'NOT_STARTED' && (
                <>開始作業 <ChevronRight className="ml-1 h-4 w-4 inline" /></>
              )}
              {assignment.status === 'IN_PROGRESS' && (
                <>繼續作業 <ChevronRight className="ml-1 h-4 w-4 inline" /></>
              )}
              {assignment.status === 'SUBMITTED' && '檢視作業'}
              {assignment.status === 'GRADED' && '查看結果'}
              {assignment.status === 'RETURNED' && (
                <>重新提交 <AlertCircle className="ml-1 h-4 w-4 inline" /></>
              )}
              {assignment.status === 'RESUBMITTED' && '檢視作業'}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
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
    <div className="p-4 lg:p-8">
      <div className="max-w-7xl mx-auto">

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BookOpen className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.totalAssignments}</p>
                  <p className="text-gray-600 text-sm">總作業數</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats.completedAssignments}</p>
                  <p className="text-gray-600 text-sm">已完成</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <BarChart3 className="h-6 w-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {stats.averageScore || '--'}
                  </p>
                  <p className="text-gray-600 text-sm">平均分數</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Clock className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {stats.inProgressAssignments}
                  </p>
                  <p className="text-gray-600 text-sm">進行中</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Assignment Lists */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2 bg-gray-100 p-1 rounded-lg">
            <TabsTrigger
              value="active"
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-sm font-medium transition-all"
            >
              進行中作業
            </TabsTrigger>
            <TabsTrigger
              value="completed"
              className="data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-sm font-medium transition-all"
            >
              已完成作業
            </TabsTrigger>
          </TabsList>

          <TabsContent value="active" className="space-y-4">
            {(() => {
              const activeAssignments = assignments.filter(a =>
                a.status === 'NOT_STARTED' || a.status === 'IN_PROGRESS' || a.status === 'RETURNED'
              );
              return activeAssignments.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12">
                    <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">沒有進行中的作業</h3>
                    <p className="text-gray-500">你已經完成了所有指派的作業！</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {activeAssignments.map(renderAssignmentCard)}
                </div>
              );
            })()}
          </TabsContent>

          <TabsContent value="completed" className="space-y-4">
            {(() => {
              const completedAssignments = assignments.filter(a =>
                a.status === 'GRADED' || a.status === 'SUBMITTED' || a.status === 'RESUBMITTED'
              );
              return completedAssignments.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12">
                    <CheckCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">還沒有完成的作業</h3>
                    <p className="text-gray-500">完成作業後，結果會顯示在這裡。</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {completedAssignments.map(renderAssignmentCard)}
                </div>
              );
            })()}
          </TabsContent>
        </Tabs>

        {/* Recent Activity - Removed for now since we don't have this data yet */}
      </div>
    </div>
  );
}
