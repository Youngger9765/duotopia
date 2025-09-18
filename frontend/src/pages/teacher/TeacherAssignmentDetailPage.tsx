import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
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
  ChevronDown,
  ChevronUp,
  ChevronRight,
  Search
} from 'lucide-react';
import { Student, Assignment } from '@/types';

// Extended assignment interface for this specific page
interface AssignmentDetail extends Assignment {
  content_type: string;
  content_id: number;
  assigned_date?: string; // Alternative field name
  students?: number[]; // Alternative field name
  content?: {
    title: string;
    type: string;
    items?: Array<{text?: string; question?: string; answer?: string; options?: string[]}>;
    target_wpm?: number;
    target_accuracy?: number;
    time_limit_seconds?: number;
  };
}

interface StudentProgress {
  student_id: number;  // 🔥 改為 student_id (資料庫主鍵)
  student_number: string;  // 🔥 student_number 是學號字串（如 "S002"）
  student_name: string;
  // 對應後端 AssignmentStatus
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'GRADED' | 'RETURNED' | 'RESUBMITTED' | 'unassigned';
  submission_date?: string;
  score?: number;
  attempts?: number;
  last_activity?: string;
  is_assigned?: boolean;
  // 🔥 新增時間戳欄位用於狀態進度判斷（方案C）
  timestamps?: {
    started_at?: string;
    submitted_at?: string;
    graded_at?: string;
    returned_at?: string;
    resubmitted_at?: string;
    created_at?: string;
    updated_at?: string;
  };
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
  const [expandedContent, setExpandedContent] = useState(false);


  useEffect(() => {
    let isActive = true;
    const abortController = new AbortController();

    const fetchData = async () => {
      if (!isActive) return;

      // Fetch in sequence to ensure dependencies are met
      await fetchAssignmentDetail();
      if (!isActive) return;

      await fetchStudents();
      if (!isActive) return;

      // Don't fail if progress API doesn't exist
      try {
        await fetchStudentProgress();
      } catch {
        // Progress API might not exist yet, which is okay
      }
    };

    if (classroomId && assignmentId) {
      fetchData();
    }

    return () => {
      isActive = false;
      abortController.abort();
    };
  }, [classroomId, assignmentId]);

  const fetchAssignmentDetail = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<AssignmentDetail & {assigned_at?: string; assigned_date?: string; created_at?: string; students_progress?: Array<{student_number: number}>}>(`/api/teachers/assignments/${assignmentId}`);

      // Handle different possible date field names
      const assignedDate = response.assigned_at || response.assigned_date || response.created_at;

      // Extract student IDs - only count actually assigned students, not all students
      let studentIds: number[] = [];
      if (response.students_progress && Array.isArray(response.students_progress)) {
        // Only include students who are actually assigned
        studentIds = response.students_progress
          .filter((sp: {is_assigned?: boolean; student_number: number}) => sp.is_assigned === true)
          .map((sp: {is_assigned?: boolean; student_number: number}) => sp.student_number)
          .filter((id) => id !== null);
      }

      // Process assigned students

      const assignmentData = {
        ...response,
        assigned_at: assignedDate,
        students: studentIds,
        student_count: studentIds.length,
        instructions: (response as AssignmentDetail & {description?: string}).description || response.instructions, // API returns 'description'
      };


      setAssignment(assignmentData);
      setEditingData({
        title: response.title,
        instructions: (response as AssignmentDetail & {description?: string}).description || response.instructions,
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
        students: [1, 2], // Mock 2 assigned students
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
      const response = await apiClient.get(`/api/teachers/classrooms/${classroomId}/students`);
      const studentList = Array.isArray(response) ? response : [];
      setStudents(studentList);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    }
  };

  const [isLoadingProgress, setIsLoadingProgress] = useState(false);

  const fetchStudentProgress = async () => {
    if (isLoadingProgress) {
      // Skip duplicate request silently
      return;
    }

    setIsLoadingProgress(true);
    // Loading progress...
    try {
      // Try to get progress data from API
      let response;
      try {
        response = await apiClient.get(`/api/teachers/assignments/${assignmentId}/progress`);
      } catch {
        // If API doesn't exist, create empty response
        response = [];
      }

      // Handle both array and object responses
      const progressArray = Array.isArray(response) ? response : (response as {data?: unknown[]}).data || [];

      // Progress loaded successfully

      // If we have progress data from API
      if (progressArray.length > 0) {
        // Create a map of progress data
        const progressMap = new Map();

        interface ProgressItem {
          student_id?: number;     // 🔥 加入 student_id 欄位 (資料庫主鍵)
          student_number?: number;
          id?: number;
          student_name?: string;
          name?: string;
          status?: string;
          submission_date?: string;
          submitted_at?: string;
          score?: number;
          grading?: {score?: number};
          feedback?: string;
          attempts?: number;
          last_activity?: string;
          updated_at?: string;
          timestamps?: StudentProgress['timestamps'];
          is_assigned?: boolean;  // 🔥 加入 is_assigned 欄位
        }

        progressArray.forEach((item: ProgressItem) => {
          // 🔥 重要：item.student_id 是 student 的資料庫 ID (整數)
          // item.student_number 是學號 (字串，如 "S002")
          const studentId = item.student_id;  // 🔥 修復：使用 student_id 而非 id
          const studentNumber = item.student_number || '';  // 學號是字串

          // 🔥 修復：使用 API 回傳的真實 is_assigned 值
          const isAssigned = item.is_assigned === true;


          progressMap.set(studentId, {
            student_id: studentId,  // 🔥 資料庫 ID
            student_number: studentNumber,  // 🔥 學號字串
            student_name: item.student_name || item.name || '未知學生',
            status: item.status || (isAssigned ? 'NOT_STARTED' : 'unassigned'),
            submission_date: item.submission_date || item.submitted_at,
            score: item.score,
            attempts: item.attempts || 0,
            last_activity: item.last_activity || item.updated_at,
            timestamps: item.timestamps,  // 🔥 加入 timestamps
            is_assigned: isAssigned  // 🔥 使用真實值而不是強制設為 true
          });
        });

        // Add all classroom students

        // Check if students are loaded - only show data we have from API
        if (students && students.length > 0) {
          const allProgress = students.map(student => {
            if (progressMap.has(student.id)) {
              const progress = progressMap.get(student.id);
              return progress!;  // 🔥 確保不是 undefined
            } else {
              // If no progress data for this student, they are unassigned
              return {
                student_id: student.id,  // 🔥 資料庫 ID
                student_number: student.student_number || '',  // 🔥 學號字串
                student_name: student.name,
                status: 'unassigned' as const,
                submission_date: undefined,
                score: undefined,
                attempts: 0,
                last_activity: undefined,
                is_assigned: false
              };
            }
          });
          setStudentProgress(allProgress);
        } else {
          // If students not loaded yet, just use the progress data we have
          const progressList = Array.from(progressMap.values());
          setStudentProgress(progressList);
        }
      } else {
        // No progress data from API - API must provide real data
        // No progress data available
        setStudentProgress([]);
      }
    } catch (error) {
      console.error('Failed to fetch student progress:', error);
      // API failed - show empty, don't create fake data
      setStudentProgress([]);
    } finally {
      setIsLoadingProgress(false);
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
        due_date: editingData.due_date ? `${editingData.due_date}T00:00:00` : undefined
      };

      await apiClient.patch(`/api/teachers/assignments/${assignmentId}`, updateData);
      toast.success('作業資訊已更新');
      setIsEditing(false);

      // Update local state immediately
      if (assignment) {
        setAssignment({
          ...assignment,
          title: updateData.title,
          instructions: updateData.instructions,
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
      // Get current assigned students from studentProgress
      const currentAssignedIds = studentProgress
        .filter(p => p.is_assigned === true)
        .map(p => p.student_id);
      const updatedStudentIds = [...currentAssignedIds, studentId];

      // Update assignment with new student list
      await apiClient.patch(`/api/teachers/assignments/${assignmentId}`, {
        student_ids: updatedStudentIds  // 🔥 修復：後端期望 student_ids 而非 students
      });

      // Update local state
      if (assignment) {
        setAssignment({
          ...assignment,
          students: updatedStudentIds,
          student_count: updatedStudentIds.length
        });
      }

      // Update student progress
      setStudentProgress(prev => prev.map(p =>
        p.student_id === studentId  // 🔥 使用 student_id 比較，不是 student_number
          ? { ...p, status: 'NOT_STARTED' as const, is_assigned: true }
          : p
      ));

      // Refresh progress data to ensure sync
      await fetchStudentProgress();

      toast.success('已成功指派給學生');
    } catch (error) {
      console.error('Failed to assign student:', error);
      toast.error('指派失敗，請稍後再試');
    }
  };

  const handleUnassignStudent = async (studentId: number, studentName: string, status: string) => {
    // 🔥 重要：studentId 現在是資料庫的整數 ID，不是學號字串
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
      const response = await apiClient.post(`/api/teachers/assignments/${assignmentId}/unassign`, {
        student_ids: [studentId],
        force: status === 'in_progress'
      });

      interface UnassignResponse {
        protected?: Array<{reason: string}>;
      }

      if (response && typeof response === 'object' && 'protected' in response) {
        const typedResponse = response as UnassignResponse;
        if (typedResponse.protected && Array.isArray(typedResponse.protected) && typedResponse.protected.length > 0) {
          toast.warning(typedResponse.protected[0].reason);
          return;
        }
      }

      // Update local state - get current assigned students from studentProgress
      const currentAssignedIds = studentProgress
        .filter(p => p.is_assigned === true)
        .map(p => p.student_id);
      const updatedStudentIds = currentAssignedIds.filter((id: number) => id !== studentId);

      if (assignment) {
        setAssignment({
          ...assignment,
          students: updatedStudentIds,
          student_count: updatedStudentIds.length
        });
      }

      // Update student progress
      setStudentProgress(prev => prev.map(p =>
        p.student_id === studentId  // 🔥 使用 student_id 比較，不是 student_number
          ? { ...p, status: 'unassigned' as const, is_assigned: false }
          : p
      ));

      // Refresh progress data to ensure sync
      await fetchStudentProgress();

      toast.success(`已取消指派學生「${studentName}」`);
    } catch (error) {
      console.error('Failed to unassign student:', error);
      toast.error('取消指派失敗');
    }
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


  // Calculate statistics (only for assigned students)
  const assignedProgress = studentProgress.filter(p => p.status !== 'unassigned');
  const stats = {
    total: assignedProgress.length,
    notStarted: assignedProgress.filter(p => p.status === 'NOT_STARTED').length,
    inProgress: assignedProgress.filter(p => p.status === 'IN_PROGRESS').length,
    submitted: assignedProgress.filter(p => p.status === 'SUBMITTED').length,
    returned: assignedProgress.filter(p => p.status === 'RETURNED').length,
    resubmitted: assignedProgress.filter(p => p.status === 'RESUBMITTED').length,
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
            {/* 批改作業按鈕 */}
            <Button
              onClick={() => navigate(`/teacher/classroom/${classroomId}/assignment/${assignmentId}/grading`)}
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              批改作業
            </Button>
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
                    // Only use progress data - count students with is_assigned = true
                    const assignedCount = studentProgress.filter(p => p.is_assigned === true).length;

                    // Progress stats updated

                    return `${assignedCount} 人`;
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
                <div className="text-xs text-gray-400">{stats.total} 人</div>
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

              {/* 已提交 */}
              <div className="flex flex-col items-center flex-1">
                <div className={`w-16 h-16 rounded-full ${stats.submitted > 0 ? 'bg-orange-100' : 'bg-gray-50'} border-4 border-white shadow-sm flex items-center justify-center relative z-10`}>
                  <div className={`text-xl font-bold ${stats.submitted > 0 ? 'text-orange-600' : 'text-gray-300'}`}>
                    {stats.submitted}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">已提交</div>
              </div>

              {/* Arrow */}
              <div className="flex-shrink-0 flex items-center pt-6">
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              {/* 待訂正 */}
              <div className="flex flex-col items-center flex-1">
                <div className={`w-16 h-16 rounded-full ${stats.returned > 0 ? 'bg-red-100' : 'bg-gray-50'} border-4 border-white shadow-sm flex items-center justify-center relative z-10`}>
                  <div className={`text-xl font-bold ${stats.returned > 0 ? 'text-red-600' : 'text-gray-300'}`}>
                    {stats.returned}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">待訂正</div>
              </div>

              {/* Arrow */}
              <div className="flex-shrink-0 flex items-center pt-6">
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

              {/* 重新提交 */}
              <div className="flex flex-col items-center flex-1">
                <div className={`w-16 h-16 rounded-full ${stats.resubmitted > 0 ? 'bg-purple-100' : 'bg-gray-50'} border-4 border-white shadow-sm flex items-center justify-center relative z-10`}>
                  <div className={`text-xl font-bold ${stats.resubmitted > 0 ? 'text-purple-600' : 'text-gray-300'}`}>
                    {stats.resubmitted}
                  </div>
                </div>
                <div className="text-xs text-gray-600 mt-2 font-medium">重新提交</div>
              </div>

              {/* Arrow */}
              <div className="flex-shrink-0 flex items-center pt-6">
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>

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
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-gray-600">已完成</span>
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
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">已提交</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">待訂正</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">重新提交</th>
                  <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 w-20">已完成</th>
                  <th className="px-3 py-3 text-center text-sm font-medium text-gray-700 w-20">分數</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 min-w-[120px]">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredProgress.length > 0 ? (
                  filteredProgress.map((progress) => {
                    // 簡化邏輯：直接使用 is_assigned 欄位
                    const isAssigned = progress.is_assigned === true;
                    const currentStatus = progress.status?.toUpperCase() || 'NOT_STARTED';

                    // Status indicator function
                    const getStatusIndicator = (statusName: string) => {
                      const timestamps = progress.timestamps;

                      // 🔥 重新設計：根據當前狀態和時間戳決定每個圓點狀態
                      let isActive = false;  // 當前狀態
                      let isPassed = false;   // 已經過的狀態

                      // Debug for specific students
                      if (progress.student_name === '蔡雅芳' || progress.student_name === '謝志偉') {
                        // Debug: student status check
                        // currentStatus,
                        // timestamps,
                        // returned_at: timestamps?.returned_at,
                        // resubmitted_at: timestamps?.resubmitted_at
                      }

                      // 根據 currentStatus 和時間戳判斷
                      switch (statusName) {
                        case 'ASSIGNED':
                          // 已指派：只有已指派的學生才會顯示這個狀態
                          // Rendered assignment indicator
                          isPassed = isAssigned;
                          isActive = isAssigned && currentStatus === 'NOT_STARTED';
                          break;

                        case 'NOT_STARTED':
                          // 未開始
                          isActive = currentStatus === 'NOT_STARTED';
                          isPassed = ['IN_PROGRESS', 'SUBMITTED', 'GRADED', 'RETURNED', 'RESUBMITTED'].includes(currentStatus);
                          break;

                        case 'IN_PROGRESS':
                          // 進行中
                          isActive = currentStatus === 'IN_PROGRESS';
                          isPassed = ['SUBMITTED', 'GRADED', 'RETURNED', 'RESUBMITTED'].includes(currentStatus);
                          break;

                        case 'SUBMITTED':
                          // 已提交
                          isActive = currentStatus === 'SUBMITTED';
                          isPassed = ['GRADED', 'RETURNED', 'RESUBMITTED'].includes(currentStatus);
                          break;

                        case 'RETURNED':
                          // 🔥 待訂正：根據當前狀態和時間戳判斷
                          if (currentStatus === 'RETURNED') {
                            // 當前狀態就是 RETURNED
                            isActive = true;
                            isPassed = false;
                          } else if (currentStatus === 'RESUBMITTED') {
                            // 如果當前是 RESUBMITTED，表示已經過 RETURNED
                            isActive = false;
                            isPassed = true;
                          } else if (currentStatus === 'GRADED' && timestamps?.returned_at) {
                            // 如果已完成且有 returned_at，表示經過訂正流程
                            isActive = false;
                            isPassed = true;
                          } else {
                            isActive = false;
                            isPassed = false;
                          }
                          break;

                        case 'RESUBMITTED':
                          // 🔥 重新提交：當前狀態是 RESUBMITTED
                          if (currentStatus === 'RESUBMITTED') {
                            isActive = true;
                            isPassed = false;
                          } else if (timestamps?.resubmitted_at && timestamps?.returned_at) {
                            const returnedTime = new Date(timestamps.returned_at).getTime();
                            const resubmittedTime = new Date(timestamps.resubmitted_at).getTime();
                            if (resubmittedTime > returnedTime && currentStatus === 'GRADED') {
                              // 已經批改完成，RESUBMITTED 是過去式
                              isActive = false;
                              isPassed = true;
                            } else {
                              isActive = false;
                              isPassed = false;
                            }
                          } else {
                            isActive = false;
                            isPassed = false;
                          }
                          break;

                        case 'GRADED':
                          // 已完成
                          isActive = currentStatus === 'GRADED';
                          isPassed = false;
                          break;

                        default:
                          isActive = false;
                          isPassed = false;
                      }

                      let actuallyPassed = isPassed;

                      if (!isAssigned && statusName !== 'ASSIGNED') {
                        return <div className="w-3 h-3 rounded-full bg-gray-200 mx-auto" />;
                      }

                      if (statusName === 'ASSIGNED') {
                        return isAssigned ?
                          <div className="w-3 h-3 rounded-full bg-green-500 mx-auto" /> :
                          <div className="w-3 h-3 rounded-full bg-gray-200 mx-auto" />;
                      }

                      if (isActive) {
                        // Current status - special handling for GRADED (completed)
                        if (statusName === 'GRADED') {
                          // Completed status - static green circle
                          return <div className="w-3 h-3 rounded-full bg-green-500 mx-auto" />;
                        } else {
                          // Other current statuses - animated pulse
                          return (
                            <div className="relative w-3 h-3 mx-auto">
                              <div className="absolute inset-0 w-3 h-3 rounded-full bg-blue-500" />
                              <div className="absolute inset-0 w-3 h-3 rounded-full bg-blue-400 animate-ping" />
                            </div>
                          );
                        }
                      }

                      if (actuallyPassed) {
                        // Actually passed through this status
                        return <div className="w-3 h-3 rounded-full bg-green-400 mx-auto" />;
                      }

                      // Not reached yet or skipped
                      return <div className="w-3 h-3 rounded-full bg-gray-200 mx-auto" />;
                    };

                    return (
                      <tr
                        key={progress.student_id || `student-${progress.student_name}`}
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
                          {getStatusIndicator('RESUBMITTED')}
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
                        <td className="px-4 py-3 text-center">
                          <div className="flex gap-2 justify-center">
                            {isAssigned ? (
                              <>
                                {(() => {
                                  // 使用大寫的狀態值進行比較
                                  const upperStatus = progress.status?.toUpperCase();

                                  // 如果是已提交、已批改、待訂正或重新提交，顯示批改按鈕
                                  if (upperStatus === 'SUBMITTED' || upperStatus === 'RESUBMITTED' || upperStatus === 'GRADED' || upperStatus === 'RETURNED') {
                                    return (
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        className="text-orange-600 border-orange-600 hover:bg-orange-50 transition-colors"
                                        onClick={() => {
                                          // 導向到批改頁面
                                          navigate(`/teacher/classroom/${classroomId}/assignment/${assignmentId}/grading`);
                                        }}
                                      >
                                        批改
                                      </Button>
                                    );
                                  }

                                  // 只有未開始或進行中的才能取消指派
                                  if (upperStatus === 'NOT_STARTED' || upperStatus === 'IN_PROGRESS') {
                                    return (
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        className="text-red-600 border-red-600 hover:bg-red-50 transition-colors"
                                        onClick={() => handleUnassignStudent(progress.student_id, progress.student_name, progress.status)}
                                      >
                                        取消指派
                                      </Button>
                                    );
                                  }

                                  // 其他狀態不顯示任何按鈕
                                  return null;
                                })()}
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
