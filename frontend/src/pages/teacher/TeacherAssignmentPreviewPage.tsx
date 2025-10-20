/**
 * 老師作業預覽頁面
 *
 * 完全重用 StudentActivityPage 元件
 * 只是從老師 preview API 載入資料，不儲存進度
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Eye, Info } from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

// 導入學生元件
import StudentActivityPageContent from "../student/StudentActivityPageContent";

interface ActivityResponse {
  assignment_id: number;
  title: string;
  status?: string;
  total_activities: number;
  activities: any[];
}

export default function TeacherAssignmentPreviewPage() {
  const { classroomId, assignmentId } = useParams<{
    classroomId: string;
    assignmentId: string;
  }>();
  const navigate = useNavigate();
  const { token } = useTeacherAuthStore();

  const [activityData, setActivityData] = useState<ActivityResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPreviewData();
  }, [assignmentId]);

  const fetchPreviewData = async () => {
    try {
      setLoading(true);

      const response = await apiClient.get<ActivityResponse>(
        `/api/teachers/assignments/${assignmentId}/preview`
      );

      setActivityData(response);
    } catch (error) {
      console.error("Failed to fetch preview data:", error);
      toast.error("載入預覽失敗");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">載入預覽中...</p>
        </div>
      </div>
    );
  }

  if (!activityData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">無法載入預覽資料</p>
          <Button onClick={() => navigate(-1)}>返回</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Preview Mode Header */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/teacher/classroom/${classroomId}?tab=assignments`)}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              返回作業列表
            </Button>

            <Badge
              variant="outline"
              className="gap-2 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 border-yellow-300 dark:border-yellow-700 px-4 py-2"
            >
              <Eye className="h-4 w-4" />
              預覽示範模式
            </Badge>
          </div>

          {/* Info Banner */}
          <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-start gap-2">
            <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-blue-700 dark:text-blue-300">
              這是預覽示範模式，您看到的畫面與學生完全相同。所有操作（包括錄音）都可正常使用，但不會儲存到資料庫。
            </p>
          </div>
        </div>
      </div>

      {/* 使用學生的完整 Activity Page 內容 */}
      <StudentActivityPageContent
        activities={activityData.activities}
        assignmentTitle={activityData.title}
        assignmentId={parseInt(assignmentId!)}
        isPreviewMode={true}
        authToken={token || undefined}
        onBack={() => navigate(`/teacher/classroom/${classroomId}?tab=assignments`)}
      />
    </div>
  );
}
