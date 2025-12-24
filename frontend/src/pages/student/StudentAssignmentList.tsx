import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { toast } from "sonner";
import {
  BookOpen,
  Clock,
  Calendar,
  CheckCircle,
  AlertCircle,
  BarChart3,
  ChevronRight,
  ArrowRight,
} from "lucide-react";
import { StudentAssignmentCard, AssignmentStatusEnum } from "@/types";
import { useTranslation } from "react-i18next";

export default function StudentAssignmentList() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { token, user } = useStudentAuthStore();

  const [assignments, setAssignments] = useState<StudentAssignmentCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("todo"); // Changed from "not_started" to "todo"
  const [stats, setStats] = useState({
    totalAssignments: 0,
    todo: 0, // Merged NOT_STARTED + IN_PROGRESS
    submitted: 0,
    graded: 0,
    returned: 0,
    resubmitted: 0,
    averageScore: 0,
  });

  useEffect(() => {
    if (!user || !token) {
      navigate("/student/login");
      return;
    }
    loadAssignments();
  }, [user, token, navigate]);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";

      // 🔍 DEBUG: 檢查基本資訊
      console.log(token ? `${token.substring(0, 20)}...` : "null");
      console.log(`${apiUrl}/api/students/assignments`);

      const response = await fetch(`${apiUrl}/api/students/assignments`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      console.log(Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `HTTP error! status: ${response.status}, body: ${errorText}`,
        );
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
        content_type?: string;
        practice_mode?: string;
      }
      const assignmentCards: StudentAssignmentCard[] = data.map(
        (assignment: AssignmentData) => ({
          id: assignment.id,
          title: assignment.title,
          status: assignment.status || "NOT_STARTED",
          due_date: assignment.due_date,
          assigned_at: assignment.assigned_at,
          submitted_at: assignment.submitted_at,
          score: assignment.score,
          feedback: assignment.feedback,
          content_id: assignment.content_id,
          classroom_id: assignment.classroom_id,
          content_type: assignment.content_type,
          practice_mode: assignment.practice_mode,
          progress_percentage: 0,
          total_contents: 1,
          completed_contents:
            assignment.status === "GRADED" || assignment.status === "SUBMITTED"
              ? 1
              : 0,
        }),
      );

      console.log(assignmentCards.length);

      setAssignments(assignmentCards);

      // Calculate stats for each status
      // Merge NOT_STARTED and IN_PROGRESS into TODO
      const todo = assignmentCards.filter(
        (a) => a.status === "NOT_STARTED" || a.status === "IN_PROGRESS",
      ).length;
      const submitted = assignmentCards.filter(
        (a) => a.status === "SUBMITTED",
      ).length;
      const graded = assignmentCards.filter(
        (a) => a.status === "GRADED",
      ).length;
      const returned = assignmentCards.filter(
        (a) => a.status === "RETURNED",
      ).length;
      const resubmitted = assignmentCards.filter(
        (a) => a.status === "RESUBMITTED",
      ).length;

      const scores = assignmentCards
        .filter((a) => a.score)
        .map((a) => a.score || 0);
      const avgScore =
        scores.length > 0
          ? scores.reduce((a, b) => a + b, 0) / scores.length
          : 0;

      setStats({
        totalAssignments: assignmentCards.length,
        todo: todo, // Combined NOT_STARTED + IN_PROGRESS
        submitted: submitted,
        graded: graded,
        returned: returned,
        resubmitted: resubmitted,
        averageScore: Math.round(avgScore),
      });
    } catch (error) {
      console.error("🔥 [ERROR] Failed to load assignments:", error);
      console.error("🔥 [ERROR] Error details:", {
        message: (error as Error).message,
        stack: (error as Error).stack,
      });
      toast.error(t("studentAssignmentList.errors.loadFailed"));
    } finally {
      setLoading(false);
    }
  };

  const getStatusDisplay = (status: AssignmentStatusEnum) => {
    switch (status) {
      case "NOT_STARTED":
      case "IN_PROGRESS":
        return {
          text: t("studentAssignmentList.status.inProgress"),
          color: "bg-blue-100 text-blue-800",
        };
      case "SUBMITTED":
        return {
          text: t("studentAssignmentList.status.submitted"),
          color: "bg-yellow-100 text-yellow-800",
        };
      case "GRADED":
        return {
          text: t("studentAssignmentList.status.graded"),
          color: "bg-green-100 text-green-800",
        };
      case "RETURNED":
        return {
          text: t("studentAssignmentList.status.returned"),
          color: "bg-orange-100 text-orange-800",
        };
      case "RESUBMITTED":
        return {
          text: t("studentAssignmentList.status.resubmitted"),
          color: "bg-purple-100 text-purple-800",
        };
      default:
        return { text: status, color: "bg-gray-100 text-gray-800" };
    }
  };

  const getStatusIcon = (status: AssignmentStatusEnum) => {
    switch (status) {
      case "NOT_STARTED":
      case "IN_PROGRESS":
        return <Clock className="h-4 w-4" />;
      case "SUBMITTED":
      case "RESUBMITTED":
        return <CheckCircle className="h-4 w-4" />;
      case "GRADED":
        return <BarChart3 className="h-4 w-4" />;
      case "RETURNED":
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
      return {
        text: t("studentAssignmentList.dueDate.overdue", {
          days: Math.abs(diffDays),
        }),
        isOverdue: true,
      };
    } else if (diffDays === 0) {
      return {
        text: t("studentAssignmentList.dueDate.today"),
        isOverdue: false,
      };
    } else if (diffDays <= 3) {
      return {
        text: t("studentAssignmentList.dueDate.remaining", { days: diffDays }),
        isOverdue: false,
      };
    } else {
      return { text: due.toLocaleDateString("zh-TW"), isOverdue: false };
    }
  };

  const handleStartAssignment = (assignmentId: number) => {
    // Navigate directly to activity page, skipping the confirmation screen (Issue #28)
    navigate(`/student/assignment/${assignmentId}/activity`);
  };

  const renderAssignmentCard = (assignment: StudentAssignmentCard) => {
    const statusDisplay = getStatusDisplay(assignment.status);
    const statusIcon = getStatusIcon(assignment.status);
    const dueDateInfo = formatDueDate(assignment.due_date);
    const canStart =
      assignment.status === "NOT_STARTED" ||
      assignment.status === "IN_PROGRESS";

    return (
      <Card
        key={assignment.id}
        className="hover:shadow-lg transition-all duration-200 border-gray-200"
        data-testid="assignment-card"
      >
        <CardHeader className="p-4 sm:p-5">
          <div className="flex flex-col gap-3">
            <div className="flex-1">
              <CardTitle className="text-base sm:text-lg lg:text-xl font-semibold text-gray-900 leading-relaxed">
                {assignment.title}
              </CardTitle>
              {assignment.classroom_name && (
                <p className="text-xs sm:text-sm text-gray-500 mt-2">
                  {assignment.classroom_name}{" "}
                  {assignment.teacher_name && `• ${assignment.teacher_name}`}
                </p>
              )}
            </div>
            <div className="flex items-start">
              <Badge
                className={`${statusDisplay.color} flex items-center gap-1 px-3 py-1.5 text-xs sm:text-sm whitespace-nowrap`}
              >
                {statusIcon}
                <span className="font-medium">{statusDisplay.text}</span>
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-4 sm:p-5 pt-0 space-y-4">
          {/* Progress */}
          {assignment.status !== "NOT_STARTED" && (
            <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                <span className="text-sm sm:text-base text-gray-600 font-medium">
                  {t("studentAssignmentList.progress.title")}
                </span>
                <span className="text-sm sm:text-base font-semibold text-gray-900">
                  {t("studentAssignmentList.progress.activities", {
                    completed: assignment.completed_count || 0,
                    total: assignment.content_count || 1,
                  })}
                </span>
              </div>
              <Progress
                value={assignment.progress_percentage || 0}
                className="h-2.5 bg-gray-200"
              />
            </div>
          )}

          {/* Details */}
          <div className="flex flex-col sm:flex-row flex-wrap gap-3">
            <div className="flex items-center gap-2 text-sm sm:text-base text-gray-600">
              <BookOpen className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 flex-shrink-0" />
              <span>
                {/* 🎯 Issue #118: 根據 content_type + practice_mode 顯示正確標籤 */}
                {(() => {
                  const contentType = assignment.content_type?.toUpperCase();
                  const practiceMode = assignment.practice_mode;

                  // VOCABULARY_SET 或 SENTENCE_MAKING → 顯示「單字集」
                  if (
                    contentType === "VOCABULARY_SET" ||
                    contentType === "SENTENCE_MAKING"
                  ) {
                    return t(
                      "studentAssignmentList.contentTypes.VOCABULARY_SET",
                    );
                  }

                  // EXAMPLE_SENTENCES 或 READING_ASSESSMENT → 根據 practice_mode 區分
                  if (
                    contentType === "EXAMPLE_SENTENCES" ||
                    contentType === "READING_ASSESSMENT"
                  ) {
                    return practiceMode === "rearrangement"
                      ? t("studentAssignmentList.contentTypes.REARRANGEMENT")
                      : t("studentAssignmentList.contentTypes.SPEAKING");
                  }

                  // 預設
                  return t("studentAssignmentList.contentType.default");
                })()}
              </span>
            </div>
            {assignment.estimated_time && (
              <div className="flex items-center gap-2 text-sm sm:text-base text-gray-600">
                <Clock className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 flex-shrink-0" />
                <span>{assignment.estimated_time}</span>
              </div>
            )}
            {dueDateInfo && (
              <div
                className={`flex items-center gap-2 text-sm sm:text-base font-medium ${
                  dueDateInfo.isOverdue ? "text-red-600" : "text-gray-700"
                }`}
              >
                <Calendar
                  className={`h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0 ${dueDateInfo.isOverdue ? "text-red-500" : "text-gray-400"}`}
                />
                <span>{dueDateInfo.text}</span>
              </div>
            )}
          </div>

          {/* Score */}
          {assignment.score !== undefined && assignment.status === "GRADED" && (
            <div className="flex items-center gap-2 pt-2">
              <BarChart3 className="h-4 w-4 sm:h-5 sm:w-5 text-green-600 flex-shrink-0" />
              <span className="text-sm sm:text-base font-medium text-green-600">
                {t("studentAssignmentList.score.label", {
                  score: assignment.score,
                })}
              </span>
            </div>
          )}

          {/* Action Button */}
          <div className="pt-4 mt-3 border-t border-gray-100">
            <Button
              onClick={() => handleStartAssignment(assignment.id)}
              disabled={
                !canStart &&
                assignment.status !== "GRADED" &&
                assignment.status !== "SUBMITTED" &&
                assignment.status !== "RETURNED"
              }
              className={`w-full py-2.5 sm:py-3 text-sm sm:text-base font-medium transition-all ${
                canStart || assignment.status === "RETURNED"
                  ? "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white shadow-sm hover:shadow-md"
                  : "bg-gray-100 hover:bg-gray-200 text-gray-700"
              }`}
              data-testid="assignment-action-button"
            >
              {assignment.status === "NOT_STARTED" && (
                <>
                  {t("studentAssignmentList.buttons.start")}{" "}
                  <ChevronRight className="ml-1 h-4 w-4 inline" />
                </>
              )}
              {assignment.status === "IN_PROGRESS" && (
                <>
                  {t("studentAssignmentList.buttons.continue")}{" "}
                  <ChevronRight className="ml-1 h-4 w-4 inline" />
                </>
              )}
              {assignment.status === "SUBMITTED" &&
                t("studentAssignmentList.buttons.view")}
              {assignment.status === "GRADED" &&
                t("studentAssignmentList.buttons.viewResults")}
              {assignment.status === "RETURNED" && (
                <>
                  {t("studentAssignmentList.buttons.resubmit")}{" "}
                  <AlertCircle className="ml-1 h-4 w-4 inline" />
                </>
              )}
              {assignment.status === "RESUBMITTED" &&
                t("studentAssignmentList.buttons.view")}
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
          <p className="mt-4 text-gray-600">
            {t("studentAssignmentList.loading")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Assignment Flow Status */}
        <Card className="mb-8 overflow-visible">
          <CardContent className="p-4 sm:p-6 overflow-visible">
            <h3 className="text-lg font-semibold mb-4">
              {t("studentAssignmentList.flowStatus.title")}
            </h3>
            <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto pb-4 pt-2 justify-start sm:justify-center flex-nowrap">
              {/* 待完成 (Merged: NOT_STARTED + IN_PROGRESS) */}
              <button
                onClick={() => setActiveTab("todo")}
                className={`flex flex-col items-center min-w-[60px] sm:min-w-[80px] transition-all ${
                  activeTab === "todo"
                    ? "scale-105"
                    : "opacity-70 hover:opacity-100"
                }`}
              >
                <div className="relative">
                  <div
                    className={`w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center border-2 sm:border-3 ${
                      activeTab === "todo"
                        ? "bg-blue-600 border-blue-600 text-white"
                        : "bg-white border-gray-300 text-blue-600"
                    }`}
                  >
                    <Clock className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />
                  </div>
                  {stats.todo > 0 && (
                    <div className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] sm:text-xs rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center font-bold z-10">
                      {stats.todo}
                    </div>
                  )}
                </div>
                <span
                  className={`mt-0.5 sm:mt-1 text-[10px] sm:text-xs md:text-sm font-medium ${
                    activeTab === "todo" ? "text-gray-900" : "text-gray-600"
                  }`}
                >
                  {t("studentAssignmentList.flowStatus.todo")}
                </span>
              </button>

              <ArrowRight className="text-gray-400 mx-0.5 sm:mx-1 flex-shrink-0 h-3 w-3 sm:h-4 sm:w-4" />

              {/* 已提交 */}
              <button
                onClick={() => setActiveTab("submitted")}
                className={`flex flex-col items-center min-w-[60px] sm:min-w-[80px] transition-all ${
                  activeTab === "submitted"
                    ? "scale-110"
                    : "opacity-70 hover:opacity-100"
                }`}
              >
                <div className="relative">
                  <div
                    className={`w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center border-2 sm:border-3 ${
                      activeTab === "submitted"
                        ? "bg-yellow-600 border-yellow-600 text-white"
                        : "bg-white border-gray-300 text-yellow-600"
                    }`}
                  >
                    <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />
                  </div>
                  {stats.submitted > 0 && (
                    <div className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] sm:text-xs rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center font-bold z-10">
                      {stats.submitted}
                    </div>
                  )}
                </div>
                <span
                  className={`mt-0.5 sm:mt-1 text-[10px] sm:text-xs md:text-sm font-medium ${
                    activeTab === "submitted"
                      ? "text-gray-900"
                      : "text-gray-600"
                  }`}
                >
                  {t("studentAssignmentList.flowStatus.submitted")}
                </span>
              </button>

              <ArrowRight className="text-gray-400 mx-0.5 sm:mx-1 flex-shrink-0 h-3 w-3 sm:h-4 sm:w-4" />

              {/* 退回訂正 (分支) */}
              <button
                onClick={() => setActiveTab("returned")}
                className={`flex flex-col items-center min-w-[60px] sm:min-w-[80px] transition-all ${
                  activeTab === "returned"
                    ? "scale-110"
                    : "opacity-70 hover:opacity-100"
                }`}
              >
                <div className="relative">
                  <div
                    className={`w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center border-2 sm:border-3 ${
                      activeTab === "returned"
                        ? "bg-orange-600 border-orange-600 text-white"
                        : "bg-white border-gray-300 text-orange-600"
                    }`}
                  >
                    <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />
                  </div>
                  {stats.returned > 0 && (
                    <div className="absolute -top-1 -right-1 bg-orange-500 text-white text-[10px] sm:text-xs rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center font-bold z-10">
                      {stats.returned}
                    </div>
                  )}
                </div>
                <span
                  className={`mt-0.5 sm:mt-1 text-[10px] sm:text-xs md:text-sm font-medium ${
                    activeTab === "returned" ? "text-gray-900" : "text-gray-600"
                  }`}
                >
                  {t("studentAssignmentList.flowStatus.returned")}
                </span>
              </button>

              <ArrowRight className="text-gray-400 mx-0.5 sm:mx-1 flex-shrink-0 h-3 w-3 sm:h-4 sm:w-4" />

              {/* 重新提交 */}
              <button
                onClick={() => setActiveTab("resubmitted")}
                className={`flex flex-col items-center min-w-[60px] sm:min-w-[80px] transition-all ${
                  activeTab === "resubmitted"
                    ? "scale-110"
                    : "opacity-70 hover:opacity-100"
                }`}
              >
                <div className="relative">
                  <div
                    className={`w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center border-2 sm:border-3 ${
                      activeTab === "resubmitted"
                        ? "bg-purple-600 border-purple-600 text-white"
                        : "bg-white border-gray-300 text-purple-600"
                    }`}
                  >
                    <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />
                  </div>
                  {stats.resubmitted > 0 && (
                    <div className="absolute -top-1 -right-1 bg-purple-500 text-white text-[10px] sm:text-xs rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center font-bold z-10">
                      {stats.resubmitted}
                    </div>
                  )}
                </div>
                <span
                  className={`mt-0.5 sm:mt-1 text-[10px] sm:text-xs md:text-sm font-medium ${
                    activeTab === "resubmitted"
                      ? "text-gray-900"
                      : "text-gray-600"
                  }`}
                >
                  {t("studentAssignmentList.flowStatus.resubmitted")}
                </span>
              </button>

              <ArrowRight className="text-gray-400 mx-0.5 sm:mx-1 flex-shrink-0 h-3 w-3 sm:h-4 sm:w-4" />

              {/* 已完成 */}
              <button
                onClick={() => setActiveTab("graded")}
                className={`flex flex-col items-center min-w-[60px] sm:min-w-[80px] transition-all ${
                  activeTab === "graded"
                    ? "scale-110"
                    : "opacity-70 hover:opacity-100"
                }`}
              >
                <div className="relative">
                  <div
                    className={`w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center border-2 sm:border-3 ${
                      activeTab === "graded"
                        ? "bg-green-600 border-green-600 text-white"
                        : "bg-white border-gray-300 text-green-600"
                    }`}
                  >
                    <BarChart3 className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />
                  </div>
                  {stats.graded > 0 && (
                    <div className="absolute -top-1 -right-1 bg-green-500 text-white text-[10px] sm:text-xs rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center font-bold z-10">
                      {stats.graded}
                    </div>
                  )}
                </div>
                <span
                  className={`mt-0.5 sm:mt-1 text-[10px] sm:text-xs md:text-sm font-medium ${
                    activeTab === "graded" ? "text-gray-900" : "text-gray-600"
                  }`}
                >
                  {t("studentAssignmentList.flowStatus.graded")}
                </span>
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Assignment Lists by Status */}
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          <TabsList className="hidden">
            <TabsTrigger value="todo" />
            <TabsTrigger value="submitted" />
            <TabsTrigger value="returned" />
            <TabsTrigger value="resubmitted" />
            <TabsTrigger value="graded" />
          </TabsList>

          {/* TODO Tab (Merged: NOT_STARTED + IN_PROGRESS) */}
          <TabsContent value="todo" className="space-y-4">
            {(() => {
              const todoAssignments = assignments.filter(
                (a) => a.status === "NOT_STARTED" || a.status === "IN_PROGRESS",
              );
              return todoAssignments.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12">
                    <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">
                      {t("studentAssignmentList.emptyStates.todo.title")}
                    </h3>
                    <p className="text-gray-500">
                      {t("studentAssignmentList.emptyStates.todo.description")}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  {todoAssignments.map(renderAssignmentCard)}
                </div>
              );
            })()}
          </TabsContent>

          {/* SUBMITTED Tab */}
          <TabsContent value="submitted" className="space-y-4">
            {(() => {
              const submittedAssignments = assignments.filter(
                (a) => a.status === "SUBMITTED",
              );
              return submittedAssignments.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12">
                    <CheckCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">
                      {t("studentAssignmentList.emptyStates.submitted.title")}
                    </h3>
                    <p className="text-gray-500">
                      {t(
                        "studentAssignmentList.emptyStates.submitted.description",
                      )}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  {submittedAssignments.map(renderAssignmentCard)}
                </div>
              );
            })()}
          </TabsContent>

          {/* GRADED Tab - 已完成 */}
          <TabsContent value="graded" className="space-y-4">
            {(() => {
              const gradedAssignments = assignments.filter(
                (a) => a.status === "GRADED",
              );
              return gradedAssignments.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">
                      {t("studentAssignmentList.emptyStates.graded.title")}
                    </h3>
                    <p className="text-gray-500">
                      {t(
                        "studentAssignmentList.emptyStates.graded.description",
                      )}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  {gradedAssignments.map(renderAssignmentCard)}
                </div>
              );
            })()}
          </TabsContent>

          {/* RETURNED Tab */}
          <TabsContent value="returned" className="space-y-4">
            {(() => {
              const returnedAssignments = assignments.filter(
                (a) => a.status === "RETURNED",
              );
              return returnedAssignments.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12">
                    <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">
                      {t("studentAssignmentList.emptyStates.returned.title")}
                    </h3>
                    <p className="text-gray-500">
                      {t(
                        "studentAssignmentList.emptyStates.returned.description",
                      )}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  {returnedAssignments.map(renderAssignmentCard)}
                </div>
              );
            })()}
          </TabsContent>

          {/* RESUBMITTED Tab */}
          <TabsContent value="resubmitted" className="space-y-4">
            {(() => {
              const resubmittedAssignments = assignments.filter(
                (a) => a.status === "RESUBMITTED",
              );
              return resubmittedAssignments.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12">
                    <CheckCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 mb-2">
                      {t("studentAssignmentList.emptyStates.resubmitted.title")}
                    </h3>
                    <p className="text-gray-500">
                      {t(
                        "studentAssignmentList.emptyStates.resubmitted.description",
                      )}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  {resubmittedAssignments.map(renderAssignmentCard)}
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
