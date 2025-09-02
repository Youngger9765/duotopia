import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import TeacherLayout from '@/components/TeacherLayout';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Edit2,
  Save,
  X,
  Calendar,
  Users,
  FileText,
  CheckCircle,
  Clock,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  Search
} from 'lucide-react';

interface Student {
  id: number;
  name: string;
  email: string;
  student_number?: string;
}

interface AssignmentDetail {
  id: number;
  title: string;
  instructions?: string;
  content_type: string;
  content_id: number;
  due_date?: string;
  assigned_at?: string;
  assigned_date?: string; // Alternative field name
  created_at?: string; // Another alternative
  classroom_id: number;
  student_ids?: number[];
  students?: number[]; // Alternative field name
  status?: string;
  completion_rate?: number;
  student_count?: number;
  content?: {
    title: string;
    type: string;
    items?: any[];
    target_wpm?: number;
    target_accuracy?: number;
    time_limit_seconds?: number;
  };
}

interface StudentProgress {
  student_id: number;
  student_name: string;
  // 對應後端 AssignmentStatus
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'GRADED' | 'RETURNED' | 'RESUBMITTED' | 'unassigned';
  submission_date?: string;
  score?: number;
  attempts?: number;
  last_activity?: string;
  is_assigned?: boolean;
}

export default function TeacherAssignmentDetailPage() {
  const { classroomId, assignmentId } = useParams<{ classroomId: string; assignmentId: string }>();
  const navigate = useNavigate();

  const [assignment, setAssignment] = useState<AssignmentDetail | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [studentProgress, setStudentProgress] = useState<StudentProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editingData, setEditingData] = useState<Partial<AssignmentDetail>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showContent, setShowContent] = useState(false);
  const [expandedContent, setExpandedContent] = useState(false);

  useEffect(() => {
    if (classroomId && assignmentId) {
      fetchData();
    }
  }, [classroomId, assignmentId]);

  // Re-fetch progress when students are loaded
  useEffect(() => {
    if (students.length > 0 && assignment) {
      console.log('Students loaded, refreshing progress data');
      fetchStudentProgress();
    }
  }, [students, assignment]);

  const fetchData = async () => {
    // Fetch in sequence to ensure dependencies are met
    await fetchAssignmentDetail();
    await fetchStudents();
    // Don't fail if progress API doesn't exist
    try {
      await fetchStudentProgress();
    } catch (error) {
      console.log('Progress API failed, using fallback data');
    }
  };

  const fetchAssignmentDetail = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/assignments/${assignmentId}`);
      console.log('Assignment detail response:', response);

      // Handle different possible date field names
      const assignedDate = response.assigned_at || response.assigned_date || response.created_at;

      // Extract student IDs from students_progress
      let studentIds = [];
      if (response.students_progress && Array.isArray(response.students_progress)) {
        studentIds = response.students_progress.map((sp: any) => sp.student_id).filter((id: any) => id !== null);
        console.log('Extracted student IDs from students_progress:', studentIds);
      } else if (response.student_ids && Array.isArray(response.student_ids)) {
        studentIds = response.student_ids;
      } else if (response.students && Array.isArray(response.students)) {
        studentIds = response.students;
      }

      const assignmentData = {
        ...response,
        assigned_at: assignedDate,
        student_ids: studentIds,
        student_count: studentIds.length,
        instructions: response.description || response.instructions, // API returns 'description'
      };

      console.log('Final assignment data:', assignmentData);

      setAssignment(assignmentData);
      setEditingData({
        title: response.title,
        instructions: response.description || response.instructions,
        due_date: response.due_date ? response.due_date.split('T')[0] : ''
      });
    } catch (error) {
      console.error('Failed to fetch assignment detail:', error);
      toast.error('無法載入作業詳情');
      // Set mock data for development
      const mockAssignment: AssignmentDetail = {
        id: Number(assignmentId),
        title: '作業標題',
        instructions: '作業說明',
        content_type: 'READING_ASSESSMENT',
        content_id: 1,
        due_date: '2025-09-30',
        assigned_at: new Date().toISOString(),
        classroom_id: Number(classroomId),
        student_ids: [1, 2], // Mock 2 assigned students
        student_count: 2,
        completion_rate: 0
      };
      setAssignment(mockAssignment);
      setEditingData({
        title: mockAssignment.title,
        instructions: mockAssignment.instructions,
        due_date: mockAssignment.due_date
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get(`/api/classrooms/${classroomId}/students`);
      console.log('Fetched students:', response);
      const studentList = Array.isArray(response) ? response : [];
      setStudents(studentList);
      console.log('Set students state to:', studentList);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    }
  };

  const fetchStudentProgress = async () => {
    try {
      // Try to get progress data from API
      let response;
      try {
        response = await apiClient.get(`/api/assignments/${assignmentId}/progress`);
        console.log('Student progress response:', response);
      } catch (apiError) {
        console.log('Progress API not available, using student list');
        // If API doesn't exist, create empty response
        response = [];
      }

      // Handle both array and object responses
      const progressArray = Array.isArray(response) ? response : response.data || [];

      // Get assigned student IDs from assignment
      const assignedIds = assignment?.student_ids || assignment?.students || [];

      // If we have progress data from API
      if (progressArray.length > 0) {
        // Create a map of progress data
        const progressMap = new Map();
        progressArray.forEach((item: any) => {
          const studentId = item.student_id || item.id;
          progressMap.set(studentId, {
            student_id: studentId,
            student_name: item.student_name || item.name || '未知學生',
            status: item.status || 'not_started',
            submission_date: item.submission_date || item.submitted_at,
            score: item.score,
            attempts: item.attempts || 0,
            last_activity: item.last_activity || item.updated_at,
            is_assigned: true
          });
        });

        // Add all classroom students
        console.log('Building progress with students:', students);

        // Check if students are loaded
        if (students && students.length > 0) {
          const allProgress = students.map(student => {
            if (progressMap.has(student.id)) {
              return progressMap.get(student.id);
            } else {
              const isAssigned = assignedIds.includes(student.id);
              return {
                student_id: student.id,
                student_name: student.name,
                status: isAssigned ? 'not_started' : 'unassigned',
                submission_date: undefined,
                score: undefined,
                attempts: 0,
                last_activity: undefined,
                is_assigned: isAssigned
              };
            }
          });

          setStudentProgress(allProgress);
          console.log('Set student progress to:', allProgress);
        } else {
          // If students not loaded yet, just use the progress data we have
          const progressList = Array.from(progressMap.values());
          setStudentProgress(progressList);
          console.log('Students not loaded, using progress data only:', progressList);
        }
      } else {
        // No progress data from API, create mock
        createMockProgress();
      }
    } catch (error) {
      console.error('Failed to fetch student progress:', error);
      // Create mock data based on assigned students
      createMockProgress();
    }
  };

  const createMockProgress = () => {
    // Show all classroom students
    console.log('createMockProgress called, students:', students);
    console.log('assignment data:', assignment);

    if (students && students.length > 0) {
      const assignedIds = assignment?.student_ids || [];
      console.log('Assigned student IDs:', assignedIds);

      const mockProgress = students.map(student => {
        const isAssigned = assignedIds.includes(student.id);
        return {
          student_id: student.id,
          student_name: student.name,
          status: isAssigned ? 'not_started' as const : 'unassigned' as const,
          submission_date: undefined,
          score: undefined,
          attempts: 0,
          last_activity: undefined,
          is_assigned: isAssigned
        };
      });
      setStudentProgress(mockProgress);
      console.log('Created progress for all classroom students:', mockProgress);
    } else {
      console.log('No students data available, students:', students);
      setStudentProgress([]);
    }
  };

  const handleSave = async () => {
    if (!editingData.title) {
      toast.error('請輸入作業標題');
      return;
    }

    try {
      // Use PATCH for partial update
      const updateData = {
        title: editingData.title,
        instructions: editingData.instructions || '',
        due_date: editingData.due_date ? `${editingData.due_date}T00:00:00` : null
      };

      await apiClient.patch(`/api/assignments/${assignmentId}`, updateData);
      toast.success('作業資訊已更新');
      setIsEditing(false);

      // Update local state immediately
      if (assignment) {
        setAssignment({
          ...assignment,
          title: updateData.title,
          instructions: updateData.instructions,
          description: updateData.instructions, // Also update description field
          due_date: updateData.due_date
        });
      }

      // Refresh from server
      fetchAssignmentDetail();
    } catch (error) {
      console.error('Failed to update assignment:', error);
      toast.error('更新失敗，請稍後再試');
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditingData({
      title: assignment?.title,
      instructions: assignment?.instructions,
      due_date: assignment?.due_date ? assignment.due_date.split('T')[0] : ''
    });
  };

  const handleAssignStudent = async (studentId: number) => {
    try {
      // Get current assigned students
      const currentAssignedIds = assignment?.student_ids || [];
      const updatedStudentIds = [...currentAssignedIds, studentId];

      // Update assignment with new student list
      await apiClient.patch(`/api/assignments/${assignmentId}`, {
        student_ids: updatedStudentIds
      });

      // Update local state
      if (assignment) {
        setAssignment({
          ...assignment,
          student_ids: updatedStudentIds,
          student_count: updatedStudentIds.length
        });
      }

      // Update student progress
      setStudentProgress(prev => prev.map(p =>
        p.student_id === studentId
          ? { ...p, status: 'not_started' as const, is_assigned: true }
          : p
      ));

      toast.success('已成功指派給學生');
    } catch (error) {
      console.error('Failed to assign student:', error);
      toast.error('指派失敗，請稍後再試');
    }
  };

  const handleUnassignStudent = async (studentId: number, studentName: string, status: string) => {
    try {
      // Check if student has started
      if (status === 'in_progress') {
        const confirmed = window.confirm(
          `學生「${studentName}」已開始作業，確定要取消指派嗎？\n\n` +
          '注意：學生的進度將會被保留，但無法繼續作業。'
        );
        if (!confirmed) return;
      } else if (status === 'submitted' || status === 'completed' || status === 'graded') {
        toast.error(`學生「${studentName}」已完成作業，無法取消指派`);
        return;
      }

      // Call unassign API
      const response = await apiClient.post(`/api/assignments/${assignmentId}/unassign`, {
        student_ids: [studentId],
        force: status === 'in_progress'
      });

      if (response.protected && response.protected.length > 0) {
        toast.warning(response.protected[0].reason);
        return;
      }

      // Update local state
      const currentAssignedIds = assignment?.student_ids || [];
      const updatedStudentIds = currentAssignedIds.filter(id => id !== studentId);

      if (assignment) {
        setAssignment({
          ...assignment,
          student_ids: updatedStudentIds,
          student_count: updatedStudentIds.length
        });
      }

      // Update student progress
      setStudentProgress(prev => prev.map(p =>
        p.student_id === studentId
          ? { ...p, status: 'unassigned' as const, is_assigned: false }
          : p
      ));

      toast.success(`已取消指派學生「${studentName}」`);
    } catch (error) {
      console.error('Failed to unassign student:', error);
      toast.error('取消指派失敗');
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'NOT_STARTED': '未開始',
      'IN_PROGRESS': '進行中',
      'SUBMITTED': '待批改',
      'GRADED': '已完成',
      'RETURNED': '待訂正',
      'RESUBMITTED': '待批改(訂正)',
      'unassigned': '未指派'
    };
    return labels[status] || status;
  };

  const getStatusStyle = (status: string) => {
    const styles: Record<string, string> = {
      'NOT_STARTED': 'bg-gray-100 text-gray-600',
      'IN_PROGRESS': 'bg-blue-100 text-blue-600',
      'SUBMITTED': 'bg-orange-100 text-orange-600',
      'GRADED': 'bg-green-100 text-green-600',
      'RETURNED': 'bg-red-100 text-red-600',
      'RESUBMITTED': 'bg-yellow-100 text-yellow-600',
      'unassigned': 'bg-gray-50 text-gray-400'
    };
    return styles[status] || 'bg-gray-100 text-gray-600';
  };

  const getContentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'READING_ASSESSMENT': '朗讀評測',
      'SPEAKING_PRACTICE': '口說練習',
      'SPEAKING_SCENARIO': '情境對話',
      'LISTENING_CLOZE': '聽力填空',
      'SENTENCE_MAKING': '造句練習',
      'SPEAKING_QUIZ': '口說測驗',
    };
    return labels[type] || type;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'not_started': 'bg-gray-100 text-gray-800',
      'in_progress': 'bg-yellow-100 text-yellow-800',
      'submitted': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'overdue': 'bg-red-100 text-red-800',
      'unassigned': 'bg-gray-50 text-gray-400'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'in_progress':
        return <Clock className="h-4 w-4" />;
      case 'overdue':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  // Calculate statistics (only for assigned students)
  const assignedProgress = studentProgress.filter(p => p.status !== 'unassigned');
  const stats = {
    total: assignedProgress.length,
    notStarted: assignedProgress.filter(p => p.status === 'NOT_STARTED').length,
    inProgress: assignedProgress.filter(p => p.status === 'IN_PROGRESS').length,
    submitted: assignedProgress.filter(p => p.status === 'SUBMITTED' || p.status === 'RESUBMITTED').length,
    returned: assignedProgress.filter(p => p.status === 'RETURNED').length,
    graded: assignedProgress.filter(p => p.status === 'GRADED').length,
    unassigned: studentProgress.filter(p => p.status === 'unassigned').length
  };

  const completionRate = stats.total > 0
    ? Math.round((stats.graded / stats.total) * 100)
    : 0;

  // Filter students
  const filteredProgress = studentProgress.filter(progress => {
    const matchesSearch = progress.student_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || progress.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">載入中...</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  if (!assignment) {
    return (
      <TeacherLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">找不到作業資料</p>
          <Button
            className="mt-4"
            onClick={() => navigate(`/teacher/classroom/${classroomId}?tab=assignments`)}
          >
            返回作業列表
          </Button>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/teacher/classroom/${classroomId}?tab=assignments`)}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回作業列表
            </Button>
            <div>
              {isEditing ? (
                <Input
                  value={editingData.title || ''}
                  onChange={(e) => setEditingData({ ...editingData, title: e.target.value })}
                  className="text-2xl font-bold"
                  placeholder="作業標題"
                />
              ) : (
                <h1 className="text-3xl font-bold">{assignment.title}</h1>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button variant="outline" onClick={handleCancel}>
                  <X className="h-4 w-4 mr-2" />
                  取消
                </Button>
                <Button onClick={handleSave}>
                  <Save className="h-4 w-4 mr-2" />
                  儲存
                </Button>
              </>
            ) : (
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                <Edit2 className="h-4 w-4 mr-2" />
                編輯
              </Button>
            )}
          </div>
        </div>

        {/* Assignment Info Card */}
        <Card className="p-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="text-sm text-gray-600 mb-2 block">內容類型</label>
              <Badge variant="outline" className="text-base">
                {assignment.content_type ? getContentTypeLabel(assignment.content_type) : '未設定'}
              </Badge>
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-2 block">指派日期</label>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-500" />
                <span>
                  {assignment.assigned_at || assignment.created_at
                    ? new Date(assignment.assigned_at || assignment.created_at || '').toLocaleDateString('zh-TW')
                    : '未設定'}
                </span>
              </div>
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-2 block">截止日期</label>
              {isEditing ? (
                <Input
                  type="date"
                  value={editingData.due_date ? editingData.due_date.split('T')[0] : ''}
                  onChange={(e) => setEditingData({ ...editingData, due_date: e.target.value })}
                />
              ) : (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-500" />
                  <span>{assignment.due_date ? new Date(assignment.due_date).toLocaleDateString('zh-TW') : '未設定'}</span>
                </div>
              )}
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-2 block">指派學生數</label>
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-gray-500" />
                <span>
                  {(() => {
                    // Priority: actual assigned students count
                    const assignedStudentIds = assignment.student_ids || assignment.students || [];
                    const assignedProgressCount = studentProgress.filter(p => p.status !== 'unassigned').length;

                    // Use assignment data first, then fall back to progress data
                    // Be careful with 0 values - use !== undefined to check existence
                    let count = 0;
                    if (assignment.student_count !== undefined && assignment.student_count !== null) {
                      count = assignment.student_count;
                    } else if (assignedStudentIds.length > 0) {
                      count = assignedStudentIds.length;
                    } else if (assignedProgressCount > 0) {
                      count = assignedProgressCount;
                    }

                    console.log('Student count calculation:', {
                      student_count: assignment.student_count,
                      assignedStudentIds: assignedStudentIds.length,
                      assignedProgressCount,
                      final: count
                    });

                    return `${count} 人`;
                  })()}
                </span>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="mt-6">
            <label className="text-sm text-gray-600 mb-2 block">作業說明</label>
            {isEditing ? (
              <Textarea
                value={editingData.instructions || ''}
                onChange={(e) => setEditingData({ ...editingData, instructions: e.target.value })}
                placeholder="輸入作業說明..."
                rows={3}
              />
            ) : (
              <p className="text-gray-700">{assignment.instructions || '無說明'}</p>
            )}
          </div>
        </Card>

        {/* Content Details (Expandable) */}
        {assignment.content && (
          <Card className="p-6">
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedContent(!expandedContent)}
            >
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-semibold">內容詳情</h3>
              </div>
              {expandedContent ? <ChevronUp /> : <ChevronDown />}
            </div>

            {expandedContent && (
              <div className="mt-4 space-y-3">
                <div>
                  <span className="text-sm text-gray-600">內容標題：</span>
                  <span className="font-medium ml-2">{assignment.content.title}</span>
                </div>
                {assignment.content.items && assignment.content.items.length > 0 && (
                  <div>
                    <span className="text-sm text-gray-600">項目數量：</span>
                    <span className="font-medium ml-2">{assignment.content.items.length} 個項目</span>
                  </div>
                )}
                {assignment.content.target_wpm && (
                  <div>
                    <span className="text-sm text-gray-600">目標速度：</span>
                    <span className="font-medium ml-2">{assignment.content.target_wpm} WPM</span>
                  </div>
                )}
                {assignment.content.target_accuracy && (
                  <div>
                    <span className="text-sm text-gray-600">目標準確度：</span>
                    <span className="font-medium ml-2">{Math.round(assignment.content.target_accuracy * 100)}%</span>
                  </div>
                )}
              </div>
            )}
          </Card>
        )}

        {/* Progress Overview */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">完成進度</h3>

          {/* Completion Rate */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">整體完成率</span>
              <span className="text-2xl font-bold text-blue-600">{completionRate}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all"
                style={{ width: `${completionRate}%` }}
              />
            </div>
          </div>

          {/* Status Progress */}
          <div className="relative">
            {/* Progress Line */}
            <div className="absolute top-8 left-0 right-0 h-0.5 bg-gray-200" style={{ zIndex: 0 }}>
              <div
                className="h-full bg-gradient-to-r from-gray-400 via-blue-500 to-green-500"
                style={{ width: `${completionRate}%` }}
              />
            </div>

            {/* Status Cards - Horizontal Progress */}
            <div className="relative flex justify-between items-start">
              {/* 已指派 */}
              <div className="flex flex-col items-center flex-1">
                <div className="w-16 h-16 rounded-full bg-gray-100 border-4 border-white shadow-sm flex items-center justify-center relative z-10">
                  <div className="text-xl font-bold text-gray-600">
                    {stats.total}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">已指派</div>
                <div className="text-xs text-gray-400">{students.length || 0} 人</div>
              </div>

              {/* Arrow */}
              <div className="flex-shrink-0 flex items-center pt-6">
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              {/* 未開始 */}
              <div className="flex flex-col items-center flex-1">
                <div className={`w-16 h-16 rounded-full ${stats.notStarted > 0 ? 'bg-gray-100' : 'bg-gray-50'} border-4 border-white shadow-sm flex items-center justify-center relative z-10`}>
                  <div className={`text-xl font-bold ${stats.notStarted > 0 ? 'text-gray-500' : 'text-gray-300'}`}>
                    {stats.notStarted}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">未開始</div>
              </div>

              {/* Arrow */}
              <div className="flex-shrink-0 flex items-center pt-6">
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              {/* 進行中 */}
              <div className="flex flex-col items-center flex-1">
                <div className={`w-16 h-16 rounded-full ${stats.inProgress > 0 ? 'bg-blue-100' : 'bg-gray-50'} border-4 border-white shadow-sm flex items-center justify-center relative z-10`}>
                  <div className={`text-xl font-bold ${stats.inProgress > 0 ? 'text-blue-600' : 'text-gray-300'}`}>
                    {stats.inProgress}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">進行中</div>
              </div>

              {/* Arrow */}
              <div className="flex-shrink-0 flex items-center pt-6">
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              {/* 待批改 */}
              <div className="flex flex-col items-center flex-1">
                <div className={`w-16 h-16 rounded-full ${stats.submitted > 0 ? 'bg-orange-100' : 'bg-gray-50'} border-4 border-white shadow-sm flex items-center justify-center relative z-10`}>
                  <div className={`text-xl font-bold ${stats.submitted > 0 ? 'text-orange-600' : 'text-gray-300'}`}>
                    {stats.submitted}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">待批改</div>
              </div>

              {/* Arrow with fork for returned path */}
              <div className="flex-shrink-0 flex items-center pt-6">
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              {/* 待訂正 (branching path) */}
              {stats.returned > 0 && (
                <>
                  <div className="flex flex-col items-center flex-1">
                    <div className="w-16 h-16 rounded-full bg-red-100 border-4 border-white shadow-sm flex items-center justify-center relative z-10">
                      <div className="text-xl font-bold text-red-600">
                        {stats.returned}
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 mt-2 font-medium">待訂正</div>
                  </div>
                  <div className="flex-shrink-0 flex items-center pt-6">
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </div>
                </>
              )}

              {/* 已完成 */}
              <div className="flex flex-col items-center flex-1">
                <div className={`w-16 h-16 rounded-full ${stats.graded > 0 ? 'bg-green-100' : 'bg-gray-50'} border-4 border-white shadow-sm flex items-center justify-center relative z-10`}>
                  <div className={`text-xl font-bold ${stats.graded > 0 ? 'text-green-600' : 'text-gray-300'}`}>
                    {stats.graded}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">已完成</div>
              </div>
            </div>
          </div>
        </Card>

        {/* Student List */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">學生列表</h3>
              {/* Legend */}
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-gray-200" />
                  <span className="text-gray-600">未達到</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="relative w-3 h-3">
                    <div className="absolute inset-0 w-3 h-3 rounded-full bg-blue-500" />
                    <div className="absolute inset-0 w-3 h-3 rounded-full bg-blue-400 animate-ping" />
                  </div>
                  <span className="text-gray-600">當前狀態</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="搜尋學生姓名..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border rounded-md"
              >
                <option value="all">全部狀態</option>
                <option value="unassigned">未指派</option>
                <option value="not_started">未開始</option>
                <option value="in_progress">進行中</option>
                <option value="submitted">已提交</option>
                <option value="completed">已批改</option>
                <option value="overdue">已逾期</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="border rounded-lg overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 min-w-[150px]">學生姓名</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">已指派</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">未開始</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">進行中</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">待批改</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">待訂正</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">已完成</th>
                  <th className="px-3 py-3 text-center text-sm font-medium text-gray-700 w-20">分數</th>
                  <th className="px-3 py-3 text-center text-sm font-medium text-gray-700 w-20">查看</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 min-w-[120px]">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredProgress.length > 0 ? (
                  filteredProgress.map((progress) => {
                    const isAssigned = progress.is_assigned !== false && progress.status !== 'unassigned';
                    const currentStatus = progress.status?.toUpperCase() || 'unassigned';

                    // Status indicator function
                    const getStatusIndicator = (statusName: string) => {
                      const isActive = currentStatus === statusName;
                      const isPassed = ['NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'RETURNED', 'RESUBMITTED', 'GRADED'].indexOf(currentStatus) >
                                       ['NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'RETURNED', 'RESUBMITTED', 'GRADED'].indexOf(statusName);

                      if (!isAssigned && statusName !== 'ASSIGNED') {
                        return <div className="w-3 h-3 rounded-full bg-gray-200 mx-auto" />;
                      }

                      if (statusName === 'ASSIGNED') {
                        return isAssigned ?
                          <div className="w-3 h-3 rounded-full bg-green-500 mx-auto" /> :
                          <div className="w-3 h-3 rounded-full bg-gray-200 mx-auto" />;
                      }

                      if (isActive) {
                        // Current status - animated pulse
                        return (
                          <div className="relative w-3 h-3 mx-auto">
                            <div className="absolute inset-0 w-3 h-3 rounded-full bg-blue-500" />
                            <div className="absolute inset-0 w-3 h-3 rounded-full bg-blue-400 animate-ping" />
                          </div>
                        );
                      }

                      if (isPassed && statusName !== 'RETURNED') {
                        // Passed status
                        return <div className="w-3 h-3 rounded-full bg-green-400 mx-auto" />;
                      }

                      if (statusName === 'RETURNED' && (currentStatus === 'RETURNED' || currentStatus === 'RESUBMITTED')) {
                        // Special case for returned/resubmitted
                        return <div className="w-3 h-3 rounded-full bg-orange-500 mx-auto" />;
                      }

                      // Not reached yet
                      return <div className="w-3 h-3 rounded-full bg-gray-200 mx-auto" />;
                    };

                    return (
                      <tr
                        key={progress.student_id}
                        className={`border-t ${isAssigned ? 'hover:bg-gray-50' : 'bg-gray-50 opacity-60'}`}
                      >
                        <td className="px-4 py-3 min-w-[150px]">
                          <div className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-full ${isAssigned ? 'bg-blue-100' : 'bg-gray-100'} flex items-center justify-center`}>
                              <span className={`text-sm font-medium ${isAssigned ? 'text-blue-600' : 'text-gray-400'}`}>
                                {progress.student_name.charAt(0)}
                              </span>
                            </div>
                            <span className={`font-medium ${!isAssigned ? 'text-gray-400' : ''}`}>
                              {progress.student_name}
                            </span>
                          </div>
                        </td>
                        <td className="px-2 py-3 text-center w-20">
                          {getStatusIndicator('ASSIGNED')}
                        </td>
                        <td className="px-2 py-3 text-center w-20">
                          {getStatusIndicator('NOT_STARTED')}
                        </td>
                        <td className="px-2 py-3 text-center w-20">
                          {getStatusIndicator('IN_PROGRESS')}
                        </td>
                        <td className="px-2 py-3 text-center w-20">
                          {getStatusIndicator('SUBMITTED')}
                        </td>
                        <td className="px-2 py-3 text-center w-20">
                          {getStatusIndicator('RETURNED')}
                        </td>
                        <td className="px-2 py-3 text-center w-20">
                          {getStatusIndicator('GRADED')}
                        </td>
                        <td className="px-3 py-3 text-center w-20">
                          {isAssigned && (currentStatus === 'GRADED' || currentStatus === 'RETURNED') ? (
                            <span className={`font-bold ${progress.score && progress.score >= 80 ? 'text-green-600' : 'text-red-600'}`}>
                              {progress.score || 0}
                            </span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-center w-20">
                          {isAssigned ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 transition-colors"
                              onClick={() => {
                                toast.info(`查看 ${progress.student_name} 的作業詳情`);
                              }}
                            >
                              查看
                            </Button>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex gap-2 justify-center">
                            {isAssigned ? (
                              <>
                                {progress.status === 'SUBMITTED' || progress.status === 'RESUBMITTED' ? (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="text-orange-600 border-orange-600 hover:bg-orange-50 transition-colors"
                                    onClick={() => {
                                      toast.info('開始批改作業');
                                    }}
                                  >
                                    批改
                                  </Button>
                                ) : progress.status === 'NOT_STARTED' || progress.status === 'IN_PROGRESS' ? (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="text-red-600 border-red-600 hover:bg-red-50 transition-colors"
                                    onClick={() => handleUnassignStudent(progress.student_id, progress.student_name, progress.status)}
                                  >
                                    取消指派
                                  </Button>
                                ) : null}
                              </>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-green-600 border-green-600 hover:bg-green-50 hover:border-green-700 hover:text-green-700 transition-colors cursor-pointer"
                                onClick={() => handleAssignStudent(progress.student_id)}
                              >
                                指派
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                      沒有符合條件的學生
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </TeacherLayout>
  );
}
