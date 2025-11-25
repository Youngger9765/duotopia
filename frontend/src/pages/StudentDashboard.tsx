import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
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
  Loader2,
} from "lucide-react";
import { Assignment } from "@/types";

export default function StudentDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, token } = useStudentAuthStore();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [stats, setStats] = useState({
    completedAssignments: 0,
    averageScore: 0,
    totalPracticeTime: 0,
    practiceDays: 0,
  });
  const [showEmailPrompt, setShowEmailPrompt] = useState(false);
  const [showEmailSetup, setShowEmailSetup] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [emailInitialized, setEmailInitialized] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [currentEmail, setCurrentEmail] = useState("");
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  useEffect(() => {
    if (!user || !token) {
      navigate("/student/login");
      return;
    }
    loadAssignments();
    loadStats();
    loadEmailStatus();
  }, [user, token, navigate]);

  const loadAssignments = async () => {
    try {
      // Directly use fetch with student token
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(`${apiUrl}/api/students/assignments`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAssignments(data as Assignment[]);
    } catch (error) {
      console.error("Failed to load assignments:", error);
      toast.error(t("studentDashboard.errors.loadAssignments"));
      // Use mock data as fallback
      setAssignments([
        {
          id: 1,
          title: "Unit 1: Greetings 問候語練習",
          content_id: 1,
          content: {
            type: "reading_assessment",
            title: "Greetings",
          },
          status: "NOT_STARTED",
          due_date: "2025-09-01",
          created_at: new Date().toISOString(),
        },
        {
          id: 2,
          title: "Unit 2: Numbers 數字練習",
          content_id: 2,
          content: {
            type: "reading_assessment",
            title: "Numbers",
          },
          status: "NOT_STARTED",
          due_date: "2025-09-05",
          created_at: new Date().toISOString(),
        },
        {
          id: 3,
          title: "Daily Conversation 日常對話",
          content_id: 3,
          content: {
            type: "speaking_scenario",
            title: "Daily Conversation",
          },
          status: "GRADED",
          due_date: "2025-08-28",
          score: 85,
          created_at: new Date().toISOString(),
        },
      ]);
    }
  };

  const loadStats = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(`${apiUrl}/api/students/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setStats({
        completedAssignments: data.completedAssignments || 0,
        averageScore: data.averageScore || 0,
        totalPracticeTime: data.totalPracticeTime || 0,
        practiceDays: data.practiceDays || 0,
      });
    } catch (error) {
      console.error("Failed to load stats:", error);
      // Fallback to zero if API fails
      setStats({
        completedAssignments: 0,
        averageScore: 0,
        totalPracticeTime: 0,
        practiceDays: 0,
      });
    }
  };

  const loadEmailStatus = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      // 使用 /me 端點來獲取當前學生資訊
      const response = await fetch(`${apiUrl}/api/students/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
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
      console.error("Failed to load email status:", error);
    }
  };

  const handleStartAssignment = (assignmentId: number) => {
    // Navigate directly to activity page, skipping the confirmation screen (Issue #28)
    navigate(`/student/assignment/${assignmentId}/activity`);
  };

  const handleViewAllAssignments = () => {
    navigate("/student/assignments");
  };

  const handleEmailPromptClose = () => {
    setShowEmailPrompt(false);
    // 不記錄，下次登入還是會顯示
  };

  const handleEmailUpdate = async () => {
    if (!newEmail || !newEmail.includes("@")) {
      toast.error(t("studentDashboard.errors.invalidEmail"));
      return;
    }

    setIsSendingEmail(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      // 使用正確的 update-email 端點
      const response = await fetch(`${apiUrl}/api/students/update-email`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: newEmail }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.verification_sent) {
          toast.success(t("studentDashboard.success.verificationSent"));
        } else {
          toast.success(t("studentDashboard.success.emailUpdated"));
        }
        setShowEmailPrompt(false);
        setShowEmailSetup(false);
        // 重新載入 email 狀態
        loadEmailStatus();
      } else {
        const error = await response.text();
        toast.error(
          `${t("studentDashboard.errors.updateEmailFailed")}: ${error}`,
        );
      }
    } catch (error) {
      console.error("Failed to update email:", error);
      toast.error(t("studentDashboard.errors.updateEmailFailed"));
    } finally {
      setIsSendingEmail(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "GRADED":
      case "RETURNED":
        return "bg-green-100 text-green-800";
      case "SUBMITTED":
        return "bg-yellow-100 text-yellow-800";
      case "IN_PROGRESS":
        return "bg-blue-100 text-blue-800";
      case "NOT_STARTED":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "NOT_STARTED":
        return t("studentDashboard.status.notStarted");
      case "IN_PROGRESS":
        return t("studentDashboard.status.inProgress");
      case "SUBMITTED":
        return t("studentDashboard.status.submitted");
      case "GRADED":
        return t("studentDashboard.status.graded");
      case "RETURNED":
        return t("studentDashboard.status.returned");
      default:
        return status;
    }
  };

  return (
    <div className="p-3 sm:p-4 lg:p-6">
      <div className="max-w-full mx-auto">
        {/* Welcome Message */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            {t("studentDashboard.welcome.greeting", {
              name: user?.name || "同學",
            })}
          </h1>
          <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
            {t("studentDashboard.welcome.subtitle")}
          </p>

          {/* Email 狀態顯示 */}
          {currentEmail && (
            <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
              <div className="flex items-center gap-2 text-sm bg-gray-50 dark:bg-gray-800 px-3 py-2 rounded-lg border dark:border-gray-700">
                <Mail className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                <span className="text-gray-700 dark:text-gray-300 text-sm sm:text-base">
                  {currentEmail}
                </span>
                {emailVerified ? (
                  <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-xs font-medium">
                      {t("studentDashboard.email.verified")}
                    </span>
                  </div>
                ) : (
                  <Badge
                    variant="outline"
                    className="text-xs text-orange-600 dark:text-orange-400 border-orange-300 dark:border-orange-600"
                  >
                    {t("studentDashboard.email.unverified")}
                  </Badge>
                )}
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => navigate("/student/profile")}
                className="text-xs sm:text-sm flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-700 h-10 min-h-10 dark:text-gray-300"
              >
                <User className="h-4 w-4" />
                {t("studentDashboard.email.profile")}
              </Button>
            </div>
          )}
        </div>

        {/* Email Setup Form */}
        {(showEmailPrompt || showEmailSetup) && (
          <Card className="mb-6 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-start gap-2 sm:gap-3">
                <div className="hidden sm:block bg-blue-100 dark:bg-blue-900 p-2 rounded-full flex-shrink-0">
                  <Mail className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <h3 className="font-medium text-blue-900 dark:text-blue-100 text-base sm:text-lg">
                      {t("studentDashboard.email.setupTitle")}
                    </h3>
                    <Button
                      variant="ghost"
                      onClick={handleEmailPromptClose}
                      className="text-blue-400 hover:text-blue-600 hover:bg-blue-100 dark:text-blue-300 dark:hover:text-blue-100 dark:hover:bg-blue-900 h-8 w-8 p-0 flex-shrink-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs sm:text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
                        {t("studentDashboard.email.yourEmail")}
                      </label>
                      <Input
                        type="email"
                        value={newEmail}
                        onChange={(e) => setNewEmail(e.target.value)}
                        placeholder={t(
                          "studentDashboard.email.emailPlaceholder",
                        )}
                        className="w-full border-blue-300 dark:border-blue-700 focus:border-blue-500 focus:ring-blue-500 dark:bg-blue-950/50 dark:text-gray-100 text-sm sm:text-base"
                      />
                    </div>

                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                      <div className="flex-1 text-xs sm:text-sm text-blue-600 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/50 p-2 sm:p-3 rounded">
                        <p>{t("studentDashboard.email.note")}</p>
                      </div>
                      <Button
                        onClick={handleEmailUpdate}
                        disabled={
                          isSendingEmail || !newEmail || !newEmail.includes("@")
                        }
                        className="bg-gray-800 hover:bg-gray-900 text-white disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:hover:bg-gray-600 h-12 min-h-12 px-4 sm:px-6 w-full sm:w-auto whitespace-nowrap"
                      >
                        {isSendingEmail ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            {t("studentDashboard.email.sending")}
                          </>
                        ) : (
                          t("studentDashboard.email.verifyButton")
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
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
                  <p className="text-xs sm:text-sm text-gray-600 truncate">
                    {t("studentDashboard.stats.completedAssignments")}
                  </p>
                  <p className="text-lg sm:text-2xl font-bold">
                    {stats.completedAssignments}
                  </p>
                </div>
                <BookOpen className="h-6 w-6 sm:h-8 sm:w-8 text-blue-500 flex-shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">
                    {t("studentDashboard.stats.averageScore")}
                  </p>
                  <p className="text-lg sm:text-2xl font-bold">
                    {stats.averageScore}
                    {t("studentDashboard.stats.scoreUnit")}
                  </p>
                </div>
                <Trophy className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-500 flex-shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">
                    {t("studentDashboard.stats.practiceTime")}
                  </p>
                  <p className="text-lg sm:text-2xl font-bold">
                    {stats.totalPracticeTime}
                    {t("studentDashboard.stats.minutesUnit")}
                  </p>
                </div>
                <Clock className="h-6 w-6 sm:h-8 sm:w-8 text-green-500 flex-shrink-0" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-gray-600 truncate">
                    {t("studentDashboard.stats.practiceDays")}
                  </p>
                  <p className="text-lg sm:text-2xl font-bold">
                    {stats.practiceDays}
                    {t("studentDashboard.stats.daysUnit")}
                  </p>
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
                {t("studentDashboard.assignments.title")}
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={handleViewAllAssignments}
                className="flex items-center gap-2 h-12 min-h-12 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
              >
                {t("studentDashboard.assignments.viewAll")}
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 sm:space-y-4">
              {assignments.map((assignment) => (
                <div
                  key={assignment.id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors gap-3 sm:gap-4"
                >
                  <div className="flex-1 min-w-0 space-y-2 sm:space-y-2">
                    {/* Title and Badge Row */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-base sm:text-lg">
                        {assignment.title}
                      </h3>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          className={getStatusColor(assignment.status || "")}
                        >
                          {getStatusText(assignment.status || "")}
                        </Badge>
                        {assignment.content && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            (
                            {assignment.content.type === "reading_assessment"
                              ? t(
                                  "studentDashboard.assignments.readingAssessment",
                                )
                              : assignment.content.type}
                            )
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Due Date and Score - Stack on mobile */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-gray-600 dark:text-gray-300">
                      {assignment.due_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4 flex-shrink-0" />
                          <span className="truncate">
                            {t("studentDashboard.assignments.dueDate")}
                            {new Date(assignment.due_date).toLocaleDateString(
                              "zh-TW",
                            )}
                          </span>
                        </span>
                      )}
                      {assignment.score !== undefined && (
                        <span className="flex items-center gap-1">
                          <Trophy className="h-4 w-4 flex-shrink-0" />
                          {t("studentDashboard.assignments.score")}
                          {assignment.score}
                          {t("studentDashboard.stats.scoreUnit")}
                        </span>
                      )}
                    </div>

                    {assignment.instructions && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                        {assignment.instructions}
                      </p>
                    )}
                  </div>

                  {/* Action Button - Full width on mobile */}
                  <div className="flex-shrink-0 sm:ml-4">
                    {(assignment.status === "NOT_STARTED" ||
                      assignment.status === "IN_PROGRESS") && (
                      <Button
                        onClick={() => handleStartAssignment(assignment.id)}
                        className="w-full sm:w-auto h-12 min-h-12"
                      >
                        {t("studentDashboard.assignments.startPractice")}
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    )}

                    {(assignment.status === "SUBMITTED" ||
                      assignment.status === "GRADED" ||
                      assignment.status === "RETURNED") && (
                      <Button
                        variant="outline"
                        onClick={() => handleStartAssignment(assignment.id)}
                        className="w-full sm:w-auto h-12 min-h-12 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                      >
                        {t("studentDashboard.assignments.viewResults")}
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
