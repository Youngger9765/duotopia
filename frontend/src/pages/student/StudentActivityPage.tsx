/**
 * 學生作業活動頁面
 *
 * 從 API 載入資料，然後使用共用的 StudentActivityPageContent 元件顯示
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { toast } from "sonner";
import { Loader2, BookOpen } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  setErrorLoggingContext,
  clearErrorLoggingContext,
} from "@/contexts/ErrorLoggingContext";
import StudentActivityPageContent from "./StudentActivityPageContent";

// Activity type from API
interface Activity {
  id: number;
  content_id: number;
  order: number;
  type: string;
  title: string;
  content: string;
  target_text: string;
  duration: number;
  points: number;
  status: string;
  score: number | null;
  audio_url?: string | null;
  completed_at: string | null;
  items?: Array<{
    id?: number;
    text?: string;
    translation?: string;
    audio_url?: string;
    recording_url?: string;
    [key: string]: unknown;
  }>;
  item_count?: number;
  answers?: string[];
  blanks?: string[];
  prompts?: string[];
  example_audio_url?: string;
  ai_scores?: {
    accuracy_score?: number;
    fluency_score?: number;
    completeness_score?: number;
    pronunciation_score?: number;
    word_details?: Array<{
      word: string;
      accuracy_score: number;
      error_type: string;
    }>;
    items?: Record<
      number,
      {
        accuracy_score?: number;
        fluency_score?: number;
        completeness_score?: number;
        pronunciation_score?: number;
        prosody_score?: number;
        word_details?: Array<{
          word: string;
          accuracy_score: number;
          error_type: string;
        }>;
        detailed_words?: unknown[];
        reference_text?: string;
        recognized_text?: string;
        analysis_summary?: unknown;
      }
    >;
  };
}

interface ActivityResponse {
  assignment_id: number;
  title: string;
  status?: string;
  total_activities: number;
  activities: Activity[];
}

export default function StudentActivityPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const navigate = useNavigate();
  const { token, user } = useStudentAuthStore();
  const { t } = useTranslation();

  // State management
  const [activities, setActivities] = useState<Activity[]>([]);
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [assignmentStatus, setAssignmentStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);

  // Set error logging context for audio error tracking
  useEffect(() => {
    if (assignmentId) {
      setErrorLoggingContext({
        assignmentId: parseInt(assignmentId),
        studentId: user?.id,
      });
    }

    return () => {
      clearErrorLoggingContext();
    };
  }, [assignmentId, user]);

  // Load activities from API
  useEffect(() => {
    if (assignmentId && token) {
      loadActivities();
    }
  }, [assignmentId, token]);

  const loadActivities = async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/activities`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to load activities: ${response.status}`);
      }

      const data: ActivityResponse = await response.json();
      console.log("Loaded activities from API:", data.activities);

      setActivities(data.activities);
      setAssignmentTitle(data.title);
      setAssignmentStatus(data.status || "");
    } catch (error) {
      console.error("Failed to load activities:", error);
      toast.error(t("studentActivityPage.errors.loadFailed"));
      navigate("/student/assignments");
    } finally {
      setLoading(false);
    }
  };

  // Handle final submission
  const handleSubmit = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/submit`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error("Failed to submit assignment");
      }

      toast.success(t("studentActivityPage.messages.submitSuccess"));
      setTimeout(() => {
        window.location.href = "/student/assignments";
      }, 500);
    } catch (error) {
      console.error("Failed to submit:", error);
      toast.error(t("studentActivityPage.errors.submitFailed"));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="text-center">
          <div className="relative">
            <div className="absolute inset-0 animate-ping">
              <div className="h-16 w-16 rounded-full border-4 border-blue-200 opacity-75"></div>
            </div>
            <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto relative" />
          </div>
          <p className="mt-6 text-lg font-medium text-gray-700">
            {t("studentActivityPage.loading.title")}
          </p>
          <p className="mt-2 text-sm text-gray-500">
            {t("studentActivityPage.loading.subtitle")}
          </p>
        </div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">
            {t("studentActivityPage.messages.noActivities")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <StudentActivityPageContent
      activities={activities}
      assignmentTitle={assignmentTitle}
      assignmentId={parseInt(assignmentId!)}
      assignmentStatus={assignmentStatus}
      onBack={() => navigate("/student/assignments")}
      onSubmit={handleSubmit}
    />
  );
}
