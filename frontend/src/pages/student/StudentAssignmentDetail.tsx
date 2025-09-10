import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import { toast } from 'sonner';
import {
  ChevronLeft,
  BookOpen,
  Clock,
  Calendar,
  Target,
  Play,
  CheckCircle,
  AlertCircle,
  BarChart3,
  User,
  FileText,
  Headphones,
  Mic
} from 'lucide-react';
import {
  StudentAssignment,
  StudentContentProgress,
  AssignmentStatusEnum
} from '@/types';

export default function StudentAssignmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useStudentAuthStore();

  const [assignment, setAssignment] = useState<StudentAssignment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id && token) {
      loadAssignmentDetail();
    }
  }, [id, token]);

  const loadAssignmentDetail = async () => {
    try {
      setLoading(true);
      // Get all assignments and find the specific one
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

      interface AssignmentData {
        id: number;
        assignment_id?: number;
        student_number: number;
        classroom_id: number;
        title: string;
        status?: string;
        score?: number;
        feedback?: string;
        is_active?: boolean;
        assigned_at?: string;
        created_at?: string;
        due_date?: string;
        submitted_at?: string;
      }
      const assignments = await response.json();
      const foundAssignment = assignments.find((a: AssignmentData) => a.id === parseInt(id!));

      if (foundAssignment) {
        // Transform to StudentAssignment type
        const assignmentDetail: StudentAssignment = {
          id: foundAssignment.id,
          assignment_id: foundAssignment.assignment_id,
          student_number: foundAssignment.student_id,
          classroom_id: foundAssignment.classroom_id,
          title: foundAssignment.title,
          status: foundAssignment.status || 'NOT_STARTED',
          score: foundAssignment.score,
          feedback: foundAssignment.feedback,
          is_active: foundAssignment.is_active !== false,
          created_at: foundAssignment.assigned_at || foundAssignment.created_at,
          due_date: foundAssignment.due_date,
          submitted_at: foundAssignment.submitted_at,
          content_progress: [],
          progress_percentage: 0
        };
        setAssignment(assignmentDetail);
      } else {
        throw new Error('Assignment not found');
      }
    } catch (error) {
      console.error('Failed to load assignment detail:', error);
      toast.error('無法載入作業詳情');
      navigate('/student/assignments');
    } finally {
      setLoading(false);
    }
  };

  const getStatusDisplay = (status: AssignmentStatusEnum) => {
    switch (status) {
      case 'NOT_STARTED':
        return { text: '未開始', color: 'bg-gray-100 text-gray-800', icon: <Clock className="h-4 w-4" /> };
      case 'IN_PROGRESS':
        return { text: '進行中', color: 'bg-blue-100 text-blue-800', icon: <Play className="h-4 w-4" /> };
      case 'SUBMITTED':
        return { text: '已提交', color: 'bg-yellow-100 text-yellow-800', icon: <CheckCircle className="h-4 w-4" /> };
      case 'GRADED':
        return { text: '已評分', color: 'bg-green-100 text-green-800', icon: <BarChart3 className="h-4 w-4" /> };
      case 'RETURNED':
        return { text: '已退回', color: 'bg-orange-100 text-orange-800', icon: <AlertCircle className="h-4 w-4" /> };
      case 'RESUBMITTED':
        return { text: '重新提交', color: 'bg-purple-100 text-purple-800', icon: <CheckCircle className="h-4 w-4" /> };
      default:
        return { text: status, color: 'bg-gray-100 text-gray-800', icon: <BookOpen className="h-4 w-4" /> };
    }
  };

  const getContentTypeIcon = (type?: string) => {
    switch (type) {
      case 'reading_assessment':
        return <Mic className="h-4 w-4" />;
      case 'listening':
        return <Headphones className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
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

  const handleStartActivity = (progressId: number) => {
    navigate(`/student/assignment/${id}/activity/${progressId}`);
  };

  const handleStartAssignment = () => {
    navigate(`/student/assignment/${id}/activity`);
  };

  const renderContentProgress = (progress: StudentContentProgress) => {
    const statusDisplay = getStatusDisplay(progress.status);
    const contentTypeIcon = getContentTypeIcon(progress.content?.type);

    return (
      <Card key={progress.id} className="hover:shadow-sm transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1">
              <div className="p-2 bg-blue-50 rounded-lg">
                {contentTypeIcon}
              </div>
              <div className="flex-1">
                <h4 className="font-medium">{progress.content?.title || `活動 ${progress.order_index + 1}`}</h4>
                <p className="text-sm text-gray-600">
                  {progress.content?.type === 'reading_assessment' && '朗讀評測'}
                  {progress.content?.type === 'listening' && '聽力練習'}
                  {progress.estimated_time && ` • ${progress.estimated_time}`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Badge className={statusDisplay.color}>
                {statusDisplay.icon}
                <span className="ml-1">{statusDisplay.text}</span>
              </Badge>

              {progress.score !== undefined && progress.status === 'GRADED' && (
                <div className="text-sm font-medium text-green-600">
                  {progress.score}分
                </div>
              )}

              <Button
                size="sm"
                onClick={() => handleStartActivity(progress.id)}
                disabled={progress.status === 'SUBMITTED' && assignment?.status !== 'RETURNED'}
                variant={progress.status === 'NOT_STARTED' ? 'default' : 'outline'}
              >
                {progress.status === 'NOT_STARTED' && '開始'}
                {progress.status === 'IN_PROGRESS' && '繼續'}
                {(progress.status === 'SUBMITTED' || progress.status === 'GRADED') && '查看'}
              </Button>
            </div>
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

  if (!assignment) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600 mb-4">找不到作業詳情</p>
          <Button onClick={() => navigate('/student/assignments')}>
            返回作業列表
          </Button>
        </div>
      </div>
    );
  }

  const statusDisplay = getStatusDisplay(assignment.status);
  const dueDateInfo = formatDueDate(assignment.due_date);
  const canStart = assignment.status === 'NOT_STARTED' || assignment.status === 'IN_PROGRESS' || assignment.status === 'RETURNED';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <Button
          variant="ghost"
          onClick={() => navigate('/student/assignments')}
          className="mb-6"
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          返回作業列表
        </Button>

        {/* Assignment Overview */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-2xl mb-2">{assignment.title}</CardTitle>
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
                  <div className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    <span>班級作業</span>
                  </div>
                  {assignment.estimated_time && (
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      <span>預估時間: {assignment.estimated_time}</span>
                    </div>
                  )}
                </div>
              </div>
              <Badge className={statusDisplay.color}>
                {statusDisplay.icon}
                <span className="ml-2">{statusDisplay.text}</span>
              </Badge>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">整體進度</span>
                <span className="font-medium">
                  {assignment.completed_count} / {assignment.content_count} 完成
                </span>
              </div>
              <Progress value={assignment.progress_percentage} className="h-3" />
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Due Date */}
            {dueDateInfo && (
              <div className={`flex items-center gap-2 text-sm ${
                dueDateInfo.isOverdue ? 'text-red-600' : 'text-gray-600'
              }`}>
                <Calendar className="h-4 w-4" />
                <span>{dueDateInfo.text}</span>
              </div>
            )}

            {/* Assignment Targets */}
            {(assignment.contents?.[0]?.target_wpm || assignment.contents?.[0]?.target_accuracy) && (
              <div className="flex gap-6">
                {assignment.contents[0].target_wpm && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Clock className="h-4 w-4" />
                    <span>目標語速: {assignment.contents[0].target_wpm} WPM</span>
                  </div>
                )}
                {assignment.contents[0].target_accuracy && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Target className="h-4 w-4" />
                    <span>目標準確率: {assignment.contents[0].target_accuracy}%</span>
                  </div>
                )}
              </div>
            )}

            {/* Quick Start Button */}
            {canStart && (
              <div className="pt-4 border-t">
                <Button
                  onClick={handleStartAssignment}
                  size="lg"
                  className="w-full sm:w-auto"
                >
                  <Play className="h-4 w-4 mr-2" />
                  {assignment.status === 'NOT_STARTED' ? '開始作業' :
                   assignment.status === 'IN_PROGRESS' ? '繼續作業' : '重新提交'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Content Progress */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              活動進度
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {assignment.content_progress && assignment.content_progress.length > 0 ? (
              assignment.content_progress
                .sort((a, b) => a.order_index - b.order_index)
                .map(renderContentProgress)
            ) : (
              <div className="text-center py-8 text-gray-500">
                <BookOpen className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>此作業尚未包含活動內容</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Score and Feedback */}
        {assignment.status === 'GRADED' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                評分結果
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {assignment.score !== undefined && (
                <div className="text-center">
                  <div className="text-4xl font-bold text-blue-600 mb-2">
                    {assignment.score}
                  </div>
                  <div className="text-gray-600">總分</div>
                </div>
              )}

              <Separator />

              {assignment.feedback && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium mb-2 text-blue-900">教師評語</h4>
                  <p className="text-blue-800">{assignment.feedback}</p>
                </div>
              )}

              {/* Individual Activity Scores */}
              {assignment.content_progress?.some(p => p.score !== undefined) && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-900">各活動分數</h4>
                  <div className="space-y-2">
                    {assignment.content_progress
                      .filter(p => p.score !== undefined)
                      .map((progress) => (
                        <div key={progress.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <span className="font-medium">
                            {progress.content?.title || `活動 ${progress.order_index + 1}`}
                          </span>
                          <span className="text-lg font-bold text-green-600">
                            {progress.score}分
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
