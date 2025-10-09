import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import AIScoreDisplay from "@/components/shared/AIScoreDisplay";
import AudioRecorder from "@/components/shared/AudioRecorder";
import {
  User,
  Clock,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  Volume2,
  CheckCircle,
  AlertCircle,
  Users,
  X,
  Mic,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Search,
} from "lucide-react";
import { Assignment } from "@/types";

interface AssignmentInfo extends Assignment {
  title: string;
}

interface StudentInfo {
  student_id: number;
  student_name: string;
  status: string;
}

interface StudentsResponse {
  students: StudentInfo[];
}

interface SubmissionItem {
  question_text: string;
  question_translation?: string;
  audio_url?: string;
  question_audio_url?: string;
  student_answer?: string;
  transcript?: string;
  duration?: number;
  content_title?: string;
  feedback?: string;
  passed?: boolean | null;
  ai_scores?: {
    accuracy_score: number;
    fluency_score: number;
    pronunciation_score: number;
    completeness_score: number;
    overall_score: number;
    word_details?: Array<{
      word: string;
      accuracy_score: number;
      error_type?: string;
    }>;
  };
}

interface StudentSubmission {
  student_number: number;
  student_name: string;
  student_email: string;
  status: string;
  submitted_at?: string;
  content_type: string;
  submissions: SubmissionItem[];
  content_groups?: Array<{
    content_id: number;
    content_title: string;
    content_type?: string;
    submissions: SubmissionItem[];
  }>;
  current_score?: number;
  current_feedback?: string;
}

interface ItemFeedback {
  [key: number]: {
    feedback: string;
    passed: boolean | null;
  };
}

interface StudentListItem {
  student_id: number;
  student_name: string;
  status: string;
}

type SaveStatus = "idle" | "saving" | "saved" | "error";

export default function GradingPage() {
  const { classroomId, assignmentId } = useParams<{
    classroomId: string;
    assignmentId: string;
  }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const studentId = searchParams.get("studentId");

  const [submission, setSubmission] = useState<StudentSubmission | null>(null);
  const [loading, setLoading] = useState(true);
  const [score, setScore] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [itemFeedbacks, setItemFeedbacks] = useState<ItemFeedback>({});

  // 新增狀態
  const [selectedGroupIndex, setSelectedGroupIndex] = useState(0);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [lastSavedTime, setLastSavedTime] = useState<Date | null>(null);

  // 學生列表相關
  const [studentList, setStudentList] = useState<StudentListItem[]>([]);
  const [assignmentTitle, setAssignmentTitle] = useState("");

  // 自動儲存 debounce
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 載入作業資訊和學生列表
  useEffect(() => {
    if (assignmentId) {
      loadAssignmentInfo();
      loadStudentList();
    }
  }, [assignmentId]);

  // 載入學生提交內容
  useEffect(() => {
    if (assignmentId && studentId) {
      loadSubmission();
    } else if (assignmentId && studentList.length > 0 && !studentId) {
      const firstStudent = studentList[0];
      if (firstStudent && firstStudent.student_id) {
        setSearchParams({ studentId: firstStudent.student_id.toString() });
      }
    }
  }, [assignmentId, studentId, studentList]);

  // 當提交資料載入後，同步更新學生列表狀態
  useEffect(() => {
    if (submission && studentId) {
      setStudentList((prev) =>
        prev.map((student) =>
          student.student_id === parseInt(studentId)
            ? { ...student, status: submission.status }
            : student,
        ),
      );
    }
  }, [submission?.status, studentId]);

  const loadAssignmentInfo = async () => {
    try {
      const response = (await apiClient.get(
        `/api/teachers/assignments/${assignmentId}`,
      )) as AssignmentInfo;
      setAssignmentTitle(response.title || `作業 #${assignmentId}`);
    } catch (error) {
      console.error("Failed to load assignment info:", error);
    }
  };

  const loadStudentList = async () => {
    try {
      const response = (await apiClient.get(
        `/api/teachers/assignments/${assignmentId}/students`,
      )) as StudentsResponse;

      const statusPriority: Record<string, number> = {
        IN_PROGRESS: 1,
        RETURNED: 1,
        SUBMITTED: 2,
        RESUBMITTED: 2,
        NOT_STARTED: 3,
        GRADED: 4,
        NOT_ASSIGNED: 99,
      };

      const sortedStudents = (response.students || []).sort((a, b) => {
        const aPriority = statusPriority[a.status] || 50;
        const bPriority = statusPriority[b.status] || 50;

        if (aPriority !== bPriority) {
          return aPriority - bPriority;
        }

        return a.student_id - b.student_id;
      });

      setStudentList(sortedStudents);
    } catch (error) {
      console.error("Failed to load student list:", error);
    }
  };

  const loadSubmission = async () => {
    try {
      setLoading(true);
      const response = (await apiClient.get(
        `/api/teachers/assignments/${assignmentId}/submissions/${studentId}`,
      )) as StudentSubmission;

      setSubmission(response);

      if (
        response.current_score !== undefined &&
        response.current_score !== null
      ) {
        setScore(response.current_score);

        const feedbackText = response.current_feedback || "";

        if (feedbackText.includes("題目 ") && feedbackText.includes("總評:")) {
          const totalFeedbackMatch = feedbackText.match(/總評:\s*([\s\S]*?)$/);
          setFeedback(totalFeedbackMatch ? totalFeedbackMatch[1].trim() : "");
        } else if (feedbackText.includes("題目 ")) {
          setFeedback("");
        } else {
          setFeedback(feedbackText);
        }
      } else {
        setScore(80);
        setFeedback("");
      }

      // 載入個別題目的評語和通過狀態
      const loadedFeedbacks: ItemFeedback = {};
      if (response.content_groups) {
        let globalIndex = 0;
        response.content_groups.forEach((group) => {
          group.submissions.forEach((sub) => {
            // 只要有 feedback 或 passed 欄位存在（不管是什麼值），都載入
            if (sub.feedback !== undefined || sub.passed !== undefined) {
              loadedFeedbacks[globalIndex] = {
                feedback: sub.feedback || "",
                passed: sub.passed ?? null,
              };
            }
            globalIndex++;
          });
        });
      } else if (response.submissions) {
        response.submissions.forEach((sub, index) => {
          // 只要有 feedback 或 passed 欄位存在（不管是什麼值），都載入
          if (sub.feedback !== undefined || sub.passed !== undefined) {
            loadedFeedbacks[index] = {
              feedback: sub.feedback || "",
              passed: sub.passed ?? null,
            };
          }
        });
      }
      setItemFeedbacks(loadedFeedbacks);
      setSelectedGroupIndex(0);
      setExpandedRows(new Set());
    } catch (error) {
      console.error("Failed to load submission:", error);
      toast.error("無法載入學生作業");
    } finally {
      setLoading(false);
    }
  };

  // 自動儲存功能
  const triggerAutoSave = useCallback(() => {
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    autoSaveTimerRef.current = setTimeout(async () => {
      await performAutoSave();
    }, 2000);
  }, []);

  const performAutoSave = async (feedbacksToSave?: typeof itemFeedbacks) => {
    if (!submission || submitting) return;

    setSaveStatus("saving");
    try {
      const feedbacks = feedbacksToSave || itemFeedbacks;
      const itemResults: Array<{
        item_index: number;
        feedback: string;
        passed: boolean | null;
        score: number;
      }> = [];
      Object.entries(feedbacks).forEach(([index, fb]) => {
        itemResults.push({
          item_index: parseInt(index),
          feedback: fb.feedback || "",
          passed: fb.passed,
          score: fb.passed === true ? 100 : fb.passed === false ? 60 : 80,
        });
      });

      const payload = {
        student_id: parseInt(studentId!),
        score: score ?? 0,
        feedback: feedback || "",
        item_results: itemResults,
        update_status: false,
      };

      await apiClient.post(`/api/teachers/assignments/${assignmentId}/grade`, payload);

      setSaveStatus("saved");
      setLastSavedTime(new Date());

      // 3 秒後清除「已儲存」狀態
      setTimeout(() => {
        setSaveStatus("idle");
      }, 3000);
    } catch (error) {
      console.error("Auto-save failed:", error);
      setSaveStatus("error");
    }
  };

  // 檢查錄音狀態（根據錄音有無 + AI 評分自動標記）- 處理所有題目
  const handleCheckRecordings = async () => {
    if (!submission) return;

    const newFeedbacks = { ...itemFeedbacks };
    let passedCount = 0;
    let failedCount = 0;
    const failedItems: string[] = [];
    let totalQuestions = 0;

    // 處理所有題組
    if (submission.content_groups) {
      let globalIndex = 0;
      submission.content_groups.forEach((group) => {
        group.submissions.forEach((item) => {
          totalQuestions++;
          const hasRecording = !!item.audio_url;
          const aiScore = item.ai_scores?.overall_score;

          // 優先級：沒錄音 > AI 評分低 > 通過
          if (!hasRecording) {
            // 情況 1: 沒錄音 → ✗
            newFeedbacks[globalIndex] = {
              passed: false,
              feedback: newFeedbacks[globalIndex]?.feedback || "你尚未上傳錄音，請補交作業",
            };
            failedCount++;
            failedItems.push(`題目 ${globalIndex + 1} (無錄音)`);
          } else if (aiScore !== undefined && aiScore < 75) {
            // 情況 2: 有錄音但 AI 評分 < 75 → ✗
            newFeedbacks[globalIndex] = {
              passed: false,
              feedback: newFeedbacks[globalIndex]?.feedback || `你的 AI 評分 ${aiScore} 分，需要加強練習`,
            };
            failedCount++;
            failedItems.push(`題目 ${globalIndex + 1} (AI ${aiScore}分)`);
          } else {
            // 情況 3: 有錄音且 (沒有 AI 分數 或 AI >= 75) → ✓
            newFeedbacks[globalIndex] = {
              passed: true,
              feedback: newFeedbacks[globalIndex]?.feedback || "做得很好！",
            };
            passedCount++;
          }
          globalIndex++;
        });
      });
    } else if (submission.submissions) {
      // 處理沒有分組的情況
      submission.submissions.forEach((item, index) => {
        totalQuestions++;
        const hasRecording = !!item.audio_url;
        const aiScore = item.ai_scores?.overall_score;

        if (!hasRecording) {
          newFeedbacks[index] = {
            passed: false,
            feedback: newFeedbacks[index]?.feedback || "你尚未上傳錄音，請補交作業",
          };
          failedCount++;
          failedItems.push(`題目 ${index + 1} (無錄音)`);
        } else if (aiScore !== undefined && aiScore < 75) {
          newFeedbacks[index] = {
            passed: false,
            feedback: newFeedbacks[index]?.feedback || `你的 AI 評分 ${aiScore} 分，需要加強練習`,
          };
          failedCount++;
          failedItems.push(`題目 ${index + 1} (AI ${aiScore}分)`);
        } else {
          newFeedbacks[index] = {
            passed: true,
            feedback: newFeedbacks[index]?.feedback || "做得很好！",
          };
          passedCount++;
        }
      });
    }

    setItemFeedbacks(newFeedbacks);

    // 立即儲存 - 傳入最新的 feedbacks
    await performAutoSave(newFeedbacks);

    // 顯示結果
    if (failedCount === 0) {
      toast.success(`✅ 全部通過 (${passedCount}題)`, { duration: 3000 });
    } else {
      toast.success(
        `✓ 通過 ${passedCount}題 / ✗ 需訂正 ${failedCount}題`,
        { duration: 3000 }
      );
    }
  };

  // 套用 AI 建議（門檻 75 分）- 處理所有題目
  const handleApplyAISuggestions = async () => {
    if (!submission) return;

    let appliedCount = 0;
    let needReviewCount = 0;

    const newFeedbacks = { ...itemFeedbacks };

    // 處理所有題組
    if (submission.content_groups) {
      let globalIndex = 0;
      submission.content_groups.forEach((group) => {
        group.submissions.forEach((item) => {
          const aiScores = item.ai_scores;
          const aiScore = aiScores?.overall_score;

          if (aiScore !== undefined) {
            if (aiScore >= 75) {
              // 生成具體的通過評語
              const strengths = [];
              if (aiScores?.pronunciation_score && aiScores.pronunciation_score >= 80) {
                strengths.push("發音清晰");
              }
              if (aiScores?.fluency_score && aiScores.fluency_score >= 80) {
                strengths.push("流暢度佳");
              }
              if (aiScores?.accuracy_score && aiScores.accuracy_score >= 80) {
                strengths.push("準確度高");
              }
              if (aiScores?.completeness_score && aiScores.completeness_score >= 80) {
                strengths.push("完整度好");
              }

              let feedback = "";
              if (strengths.length > 0) {
                feedback = `表現優秀！${strengths.join("、")}。(AI 評分: ${Math.round(aiScore)})`;
              } else {
                feedback = `表現不錯！整體達標。(AI 評分: ${Math.round(aiScore)})`;
              }

              newFeedbacks[globalIndex] = {
                feedback,
                passed: true,
              };
              appliedCount++;
            } else {
              newFeedbacks[globalIndex] = {
                feedback: "請多練習發音和流暢度",
                passed: false,
              };
              appliedCount++;
            }
          } else {
            needReviewCount++;
          }
          globalIndex++;
        });
      });
    } else if (submission.submissions) {
      // 處理沒有分組的情況
      submission.submissions.forEach((item, index) => {
        const aiScores = item.ai_scores;
        const aiScore = aiScores?.overall_score;

        if (aiScore !== undefined) {
          if (aiScore >= 75) {
            const strengths = [];
            if (aiScores?.pronunciation_score && aiScores.pronunciation_score >= 80) {
              strengths.push("發音清晰");
            }
            if (aiScores?.fluency_score && aiScores.fluency_score >= 80) {
              strengths.push("流暢度佳");
            }
            if (aiScores?.accuracy_score && aiScores.accuracy_score >= 80) {
              strengths.push("準確度高");
            }
            if (aiScores?.completeness_score && aiScores.completeness_score >= 80) {
              strengths.push("完整度好");
            }

            let feedback = "";
            if (strengths.length > 0) {
              feedback = `表現優秀！${strengths.join("、")}。(AI 評分: ${Math.round(aiScore)})`;
            } else {
              feedback = `表現不錯！整體達標。(AI 評分: ${Math.round(aiScore)})`;
            }

            newFeedbacks[index] = {
              feedback,
              passed: true,
            };
            appliedCount++;
          } else {
            newFeedbacks[index] = {
              feedback: "請多練習發音和流暢度",
              passed: false,
            };
            appliedCount++;
          }
        } else {
          needReviewCount++;
        }
      });
    }

    setItemFeedbacks(newFeedbacks);

    // 立即儲存 - 傳入最新的 feedbacks
    await performAutoSave(newFeedbacks);

    toast.success(`已批改 ${appliedCount} 題`, { duration: 3000 });
  };

  const handleCompleteGrading = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      const itemResults: Array<{
        item_index: number;
        feedback: string;
        passed: boolean | null;
        score: number;
      }> = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        itemResults.push({
          item_index: parseInt(index),
          feedback: fb.feedback || "",
          passed: fb.passed,
          score: fb.passed === true ? 100 : fb.passed === false ? 60 : 80,
        });
      });

      await apiClient.post(`/api/teachers/assignments/${assignmentId}/grade`, {
        student_id: parseInt(studentId!),
        score: score ?? 0,
        feedback: feedback || "",
        item_results: itemResults,
        update_status: true,
      });

      toast.success("批改完成！");

      if (submission) {
        submission.status = "GRADED";
      }

      setStudentList((prev) =>
        prev.map((student) =>
          student.student_id === parseInt(studentId!)
            ? { ...student, status: "GRADED" }
            : student,
        ),
      );

      const assignedStudents = studentList.filter(
        (s) => s.status && s.status !== "NOT_ASSIGNED",
      );
      const currentAssignedIndex = assignedStudents.findIndex(
        (s) => s.student_id === parseInt(studentId!),
      );

      if (currentAssignedIndex < assignedStudents.length - 1) {
        await handleNextStudent();
      }
    } catch (error) {
      console.error("Failed to complete grading:", error);
      toast.error("批改失敗，請稍後再試");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRequestRevision = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      await apiClient.post(
        `/api/teachers/assignments/${assignmentId}/return-for-revision`,
        {
          student_id: parseInt(studentId!),
          message: "請依照評語修改後重新提交",
        },
      );

      toast.success("已要求學生訂正");

      if (submission) {
        submission.status = "RETURNED";
      }

      setStudentList((prev) =>
        prev.map((student) =>
          student.student_id === parseInt(studentId!)
            ? { ...student, status: "RETURNED" }
            : student,
        ),
      );

      await loadSubmission();
    } catch (error) {
      console.error("Failed to request revision:", error);
      toast.error("要求訂正失敗，請稍後再試");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePreviousStudent = async () => {
    const assignedStudents = studentList.filter(
      (s) => s.status && s.status !== "NOT_ASSIGNED",
    );
    const currentAssignedIndex = assignedStudents.findIndex(
      (s) => s.student_id === parseInt(studentId || "0"),
    );

    if (currentAssignedIndex > 0) {
      const prevStudent = assignedStudents[currentAssignedIndex - 1];
      setSearchParams({ studentId: (prevStudent.student_id || 0).toString() });
    }
  };

  const handleNextStudent = async () => {
    const assignedStudents = studentList.filter(
      (s) => s.status && s.status !== "NOT_ASSIGNED",
    );
    const currentAssignedIndex = assignedStudents.findIndex(
      (s) => s.student_id === parseInt(studentId || "0"),
    );

    if (currentAssignedIndex < assignedStudents.length - 1) {
      const nextStudent = assignedStudents[currentAssignedIndex + 1];
      setSearchParams({ studentId: (nextStudent.student_id || 0).toString() });
    }
  };

  const handleStudentSelect = async (student: StudentListItem) => {
    setSearchParams({ studentId: (student.student_id || 0).toString() });
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      NOT_STARTED: { label: "未開始", className: "bg-gray-100 text-gray-600" },
      IN_PROGRESS: { label: "進行中", className: "bg-blue-100 text-blue-600" },
      SUBMITTED: { label: "已提交", className: "bg-green-100 text-green-600" },
      GRADED: { label: "已批改", className: "bg-purple-100 text-purple-600" },
      RETURNED: { label: "已發還", className: "bg-yellow-100 text-yellow-600" },
      RESUBMITTED: {
        label: "重新提交",
        className: "bg-orange-100 text-orange-600",
      },
    };

    const config = statusMap[status] || {
      label: status,
      className: "bg-gray-100 text-gray-600",
    };
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  // 取得當前題組
  const getCurrentGroup = () => {
    if (!submission?.content_groups) return null;
    return submission.content_groups[selectedGroupIndex];
  };

  // 計算題組的起始 global index
  const getGroupBaseIndex = (groupIndex: number) => {
    if (!submission?.content_groups) return 0;
    let baseIndex = 0;
    for (let i = 0; i < groupIndex; i++) {
      baseIndex += submission.content_groups[i].submissions.length;
    }
    return baseIndex;
  };

  // 切換行展開/收合
  const toggleRowExpanded = (rowIndex: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(rowIndex)) {
      newExpanded.delete(rowIndex);
    } else {
      newExpanded.add(rowIndex);
    }
    setExpandedRows(newExpanded);
  };

  // 計算總題數
  const getTotalQuestions = () => {
    if (submission?.content_groups && submission.content_groups.length > 0) {
      return submission.content_groups.reduce(
        (sum, group) => sum + group.submissions.length,
        0,
      );
    }
    return submission?.submissions?.length || 0;
  };

  const totalQuestions = getTotalQuestions();
  const currentGroup = getCurrentGroup();
  const baseGlobalIndex = getGroupBaseIndex(selectedGroupIndex);

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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  navigate(
                    `/teacher/classroom/${classroomId}/assignment/${assignmentId}`,
                  )
                }
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回
              </Button>
              <div className="border-l h-8 mx-2"></div>
              <h1 className="text-xl font-semibold">
                批改作業: {assignmentTitle}
              </h1>

              {/* 儲存狀態指示器 */}
              {saveStatus !== "idle" && (
                <div className="ml-4">
                  {saveStatus === "saving" && (
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <div className="animate-spin rounded-full h-3 w-3 border-b border-gray-500"></div>
                      儲存中...
                    </span>
                  )}
                  {saveStatus === "saved" && lastSavedTime && (
                    <span className="text-xs text-green-600 flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      已儲存 {lastSavedTime.toLocaleTimeString("zh-TW")}
                    </span>
                  )}
                  {saveStatus === "error" && (
                    <span className="text-xs text-red-600 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      儲存失敗
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* 學生切換導航 */}
            <div className="flex items-center gap-4">
              {(() => {
                const assignedStudents = studentList.filter(
                  (s) => s.status && s.status !== "NOT_ASSIGNED",
                );
                const currentAssignedIndex = assignedStudents.findIndex(
                  (s) => s.student_id === parseInt(studentId || "0"),
                );
                const isCurrentStudentAssigned = currentAssignedIndex !== -1;

                return (
                  <>
                    <span className="text-sm text-gray-500">
                      {isCurrentStudentAssigned
                        ? `${currentAssignedIndex + 1} / ${assignedStudents.length} 位已指派學生`
                        : `未指派學生 (${assignedStudents.length} 位已指派)`}
                    </span>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handlePreviousStudent}
                        disabled={
                          !isCurrentStudentAssigned ||
                          currentAssignedIndex === 0
                        }
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleNextStudent}
                        disabled={
                          !isCurrentStudentAssigned ||
                          currentAssignedIndex === assignedStudents.length - 1
                        }
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-12 gap-4">
          {/* 左側 - 學生列表 */}
          <div className="col-span-2">
            <Card className="p-3">
              <h3 className="text-sm font-medium mb-3 flex items-center justify-between text-gray-700">
                <div className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  <span>學生</span>
                </div>
                <span className="text-xs text-gray-500">
                  (
                  {
                    studentList.filter(
                      (s) => s.status && s.status !== "NOT_ASSIGNED",
                    ).length
                  }
                  /{studentList.length})
                </span>
              </h3>
              <div className="space-y-1">
                {studentList.map((student) => {
                  const isAssigned =
                    student.status && student.status !== "NOT_ASSIGNED";

                  const getStatusLabel = (status: string) => {
                    const statusLabelMap: Record<string, string> = {
                      NOT_STARTED: "未開始",
                      IN_PROGRESS: "進行中",
                      SUBMITTED: "已提交",
                      GRADED: "已批改",
                      RETURNED: "待訂正",
                      RESUBMITTED: "重交",
                      NOT_ASSIGNED: "未指派",
                    };
                    return statusLabelMap[status] || "";
                  };

                  return (
                    <button
                      key={student.student_id}
                      onClick={() => isAssigned && handleStudentSelect(student)}
                      disabled={!isAssigned}
                      className={`w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors ${
                        !isAssigned
                          ? "opacity-50 cursor-not-allowed bg-gray-50"
                          : student.student_id === parseInt(studentId!)
                            ? "bg-blue-100 text-blue-700"
                            : "hover:bg-gray-100"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="truncate font-medium">
                              {student.student_name}
                            </span>
                            <Badge
                              className={`text-xs px-1.5 py-0.5 ${
                                student.status === "GRADED"
                                  ? "bg-green-100 text-green-700 border-green-200"
                                  : student.status === "RETURNED"
                                    ? "bg-orange-100 text-orange-700 border-orange-200"
                                    : student.status === "SUBMITTED" ||
                                        student.status === "RESUBMITTED"
                                      ? "bg-blue-100 text-blue-700 border-blue-200"
                                      : student.status === "IN_PROGRESS"
                                        ? "bg-yellow-100 text-yellow-700 border-yellow-200"
                                        : student.status === "NOT_ASSIGNED"
                                          ? "bg-red-50 text-red-600 border-red-200"
                                          : "bg-gray-100 text-gray-600 border-gray-200"
                              }`}
                            >
                              {getStatusLabel(student.status)}
                            </Badge>
                          </div>
                        </div>
                        {student.status === "GRADED" && (
                          <CheckCircle className="h-3 w-3 text-green-600 flex-shrink-0" />
                        )}
                        {student.status === "RETURNED" && (
                          <AlertCircle className="h-3 w-3 text-orange-600 flex-shrink-0" />
                        )}
                        {(student.status === "SUBMITTED" ||
                          student.status === "RESUBMITTED") && (
                          <div className="h-2 w-2 bg-blue-600 rounded-full flex-shrink-0" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </Card>
          </div>

          {/* 中間 - 題組 Table */}
          <div className="col-span-6">
            {submission ? (
              <div className="space-y-3">
                {/* 學生資訊卡片 */}
                <Card className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-sm">
                          {submission.student_name}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {submission.student_email}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(submission.status)}
                      {submission.submitted_at && (
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Clock className="h-3 w-3" />
                          {new Date(submission.submitted_at).toLocaleDateString(
                            "zh-TW",
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>

                {/* 操作按鈕與題組選擇器 */}
                <Card className="p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        onClick={handleCheckRecordings}
                        className="flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        <Search className="h-4 w-4" />
                        檢查錄音
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleApplyAISuggestions}
                        className="flex items-center gap-1 bg-purple-600 hover:bg-purple-700 text-white"
                      >
                        <Sparkles className="h-4 w-4" />
                        套用 AI 建議
                      </Button>
                    </div>
                    {submission.content_groups &&
                      submission.content_groups.length > 1 && (
                        <>
                          <div className="border-l h-8"></div>
                          <div className="flex items-center gap-2 flex-1">
                            <span className="text-sm font-medium">題組:</span>
                            <select
                              value={selectedGroupIndex}
                              onChange={(e) =>
                                setSelectedGroupIndex(parseInt(e.target.value))
                              }
                              className="flex-1 border rounded-md px-3 py-1.5 text-sm"
                            >
                              {submission.content_groups.map((group, index) => (
                                <option key={group.content_id} value={index}>
                                  {group.content_title} ({group.submissions.length}
                                  題)
                                </option>
                              ))}
                            </select>
                          </div>
                        </>
                      )}
                  </div>
                </Card>

                {/* 題目 Table */}
                {currentGroup && (
                  <Card className="p-4">
                    <div className="space-y-0 divide-y">
                      {currentGroup.submissions.map((item, localIndex) => {
                        const globalIndex = baseGlobalIndex + localIndex;
                        const isExpanded = expandedRows.has(globalIndex);
                        const itemFeedback = itemFeedbacks[globalIndex];

                        return (
                          <div key={globalIndex} className="py-4">
                            {/* 主要行 */}
                            <div className="grid grid-cols-12 gap-3 items-start">
                              {/* 通過狀態 */}
                              <div className="col-span-1 flex flex-col gap-1">
                                <Button
                                  size="sm"
                                  variant={
                                    itemFeedback?.passed === true
                                      ? "default"
                                      : "outline"
                                  }
                                  className={`w-full p-1 h-7 ${
                                    itemFeedback?.passed === true
                                      ? "bg-green-600 hover:bg-green-700"
                                      : ""
                                  }`}
                                  onClick={() => {
                                    setItemFeedbacks({
                                      ...itemFeedbacks,
                                      [globalIndex]: {
                                        ...itemFeedbacks[globalIndex],
                                        feedback:
                                          itemFeedbacks[globalIndex]
                                            ?.feedback || "",
                                        passed: true,
                                      },
                                    });
                                    triggerAutoSave();
                                  }}
                                  disabled={submission?.status === "GRADED"}
                                >
                                  <CheckCircle className="h-3 w-3" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant={
                                    itemFeedback?.passed === false
                                      ? "default"
                                      : "outline"
                                  }
                                  className={`w-full p-1 h-7 ${
                                    itemFeedback?.passed === false
                                      ? "bg-red-600 hover:bg-red-700"
                                      : ""
                                  }`}
                                  onClick={() => {
                                    setItemFeedbacks({
                                      ...itemFeedbacks,
                                      [globalIndex]: {
                                        ...itemFeedbacks[globalIndex],
                                        feedback:
                                          itemFeedbacks[globalIndex]
                                            ?.feedback || "",
                                        passed: false,
                                      },
                                    });
                                    triggerAutoSave();
                                  }}
                                  disabled={submission?.status === "GRADED"}
                                >
                                  <X className="h-3 w-3" />
                                </Button>
                              </div>

                              {/* 題目 */}
                              <div className="col-span-4">
                                <div className="flex items-start gap-2">
                                  <span className="text-xs font-semibold text-gray-500 mt-1">
                                    {localIndex + 1}.
                                  </span>
                                  <div className="flex-1">
                                    <p className="font-medium text-sm">
                                      {item.question_text}
                                    </p>
                                    {item.question_translation && (
                                      <p className="text-xs text-gray-500 mt-1">
                                        {item.question_translation}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* 學生錄音 */}
                              <div className="col-span-2">
                                {item.audio_url ? (
                                  <AudioRecorder
                                    variant="compact"
                                    title=""
                                    existingAudioUrl={item.audio_url}
                                    readOnly={true}
                                    disabled={false}
                                    className="border-0 p-0 shadow-none bg-white dark:bg-white"
                                  />
                                ) : (
                                  <div className="flex items-center gap-2 text-xs text-gray-400">
                                    <Mic className="h-4 w-4" />
                                    <span>未錄音</span>
                                  </div>
                                )}
                              </div>

                              {/* 評語 */}
                              <div className="col-span-4">
                                <Textarea
                                  value={itemFeedback?.feedback || ""}
                                  onChange={(e) => {
                                    setItemFeedbacks({
                                      ...itemFeedbacks,
                                      [globalIndex]: {
                                        ...itemFeedbacks[globalIndex],
                                        feedback: e.target.value,
                                        passed:
                                          itemFeedbacks[globalIndex]?.passed ??
                                          null,
                                      },
                                    });
                                    triggerAutoSave();
                                  }}
                                  placeholder="評語..."
                                  className="min-h-[60px] resize-none text-xs bg-white dark:bg-white"
                                  readOnly={submission?.status === "GRADED"}
                                  disabled={submission?.status === "GRADED"}
                                />
                              </div>

                              {/* 展開按鈕 */}
                              <div className="col-span-1 flex justify-center">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleRowExpanded(globalIndex)}
                                  className="p-1 h-7"
                                >
                                  {isExpanded ? (
                                    <ChevronUp className="h-4 w-4" />
                                  ) : (
                                    <ChevronDown className="h-4 w-4" />
                                  )}
                                </Button>
                              </div>
                            </div>

                            {/* 展開的詳細資訊 */}
                            {isExpanded && (
                              <div className="mt-3 pl-8 space-y-3">
                                {/* 參考音檔 */}
                                {item.question_audio_url && (
                                  <div>
                                    <label className="text-xs font-semibold text-gray-600 mb-1 block">
                                      參考音檔
                                    </label>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => {
                                        const audio = new Audio(
                                          item.question_audio_url!,
                                        );
                                        audio.play().catch((err) => {
                                          console.error(
                                            "Failed to play audio:",
                                            err,
                                          );
                                          toast.error("無法播放參考音檔");
                                        });
                                      }}
                                    >
                                      <Volume2 className="h-3 w-3 mr-1" />
                                      播放參考音檔
                                    </Button>
                                  </div>
                                )}

                                {/* 語音辨識結果 */}
                                {item.transcript && (
                                  <div>
                                    <label className="text-xs font-semibold text-gray-600 mb-1 block">
                                      語音辨識結果
                                    </label>
                                    <div className="p-2 bg-green-50 border border-green-200 rounded text-xs">
                                      {item.transcript}
                                    </div>
                                  </div>
                                )}

                                {/* AI 評分 */}
                                <div>
                                  <label className="text-xs font-semibold text-gray-600 mb-1 block">
                                    AI 自動評分
                                  </label>
                                  {item.ai_scores ? (
                                    <AIScoreDisplay
                                      scores={item.ai_scores}
                                      hasRecording={!!item.audio_url}
                                      title=""
                                    />
                                  ) : (
                                    <div className="p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-500 text-center">
                                      尚無 AI 評分資料
                                      {!item.audio_url && " (缺少錄音檔案)"}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </Card>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500">找不到學生作業</div>
            )}
          </div>

          {/* 右側 - 評分面板 */}
          <div className="col-span-4">
            <Card className="p-4 sticky top-24">
              <h4 className="font-medium text-sm mb-3">批改評分</h4>

              <div className="space-y-3">
                {/* 逐題燈號（分題組） */}
                {submission && submission.content_groups && (
                  <div className="pb-3 border-b space-y-3">
                    <label className="text-xs font-medium block">
                      逐題狀態 ({totalQuestions} 題)
                    </label>
                    {submission.content_groups.map((group, groupIndex) => {
                      // Calculate base index for this group
                      let groupBaseIndex = 0;
                      for (let i = 0; i < groupIndex; i++) {
                        groupBaseIndex += submission.content_groups![i].submissions.length;
                      }

                      return (
                        <div key={group.content_id} className="space-y-1">
                          <div className="text-xs text-gray-600 font-medium">
                            {group.content_title} ({group.submissions.length} 題)
                          </div>
                          <div className="grid grid-cols-10 gap-1">
                            {group.submissions.map((item, localIndex) => {
                              const globalIndex = groupBaseIndex + localIndex;
                              const result = itemFeedbacks[globalIndex];
                              const isPassed = result?.passed === true;
                              const isFailed = result?.passed === false;
                              const hasRecording = item.audio_url;

                              return (
                                <div
                                  key={localIndex}
                                  className={`
                                    w-8 h-8 rounded-md flex items-center justify-center text-xs font-medium
                                    transition-all cursor-default
                                    ${
                                      isPassed
                                        ? "bg-green-500 text-white shadow-sm"
                                        : isFailed
                                          ? "bg-red-500 text-white shadow-sm"
                                          : hasRecording
                                            ? "bg-gray-200 text-gray-600 hover:bg-gray-300"
                                            : "bg-gray-100 text-gray-400 border border-dashed border-gray-300"
                                    }
                                  `}
                                  title={`題目 ${localIndex + 1}: ${isPassed ? "通過" : isFailed ? "需訂正" : hasRecording ? "有錄音" : "無錄音"}`}
                                >
                                  {isPassed ? "✓" : isFailed ? "✗" : localIndex + 1}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* 分數評定 */}
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <input
                      type="checkbox"
                      checked={score !== null}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setScore(80);
                        } else {
                          setScore(null);
                        }
                        triggerAutoSave();
                      }}
                      className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                    <label className="text-sm font-medium">給分</label>
                  </div>
                  <div className="mt-2">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={score ?? ""}
                      onChange={(e) => {
                        const value = parseInt(e.target.value) || 0;
                        setScore(value);
                        triggerAutoSave();
                      }}
                      disabled={score === null}
                      placeholder="輸入分數"
                      className={`w-full px-3 py-2 text-lg font-bold border-2 rounded focus:outline-none focus:ring-2 text-center ${
                        score === null
                          ? "bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed"
                          : "bg-white border-blue-500 text-blue-600 focus:ring-blue-500"
                      }`}
                    />
                    <div className="text-xs text-gray-500 text-center mt-1">
                      0-100 分
                    </div>
                  </div>
                </div>

                {/* 總評語回饋 */}
                <div>
                  <label className="text-xs font-medium mb-2 block">
                    總評語回饋
                  </label>
                  <Textarea
                    value={feedback}
                    onChange={(e) => {
                      setFeedback(e.target.value);
                      triggerAutoSave();
                    }}
                    placeholder="給學生的總體鼓勵和建議..."
                    rows={4}
                    className="resize-none text-sm bg-white dark:bg-white"
                  />
                </div>

                {/* 操作按鈕 */}
                <div className="space-y-4 pt-4 border-t">
                  {/* 狀態流程提示 */}
                  <div className="text-center text-xs text-gray-500">
                    選擇批改狀態
                  </div>

                  {/* 狀態選擇按鈕 */}
                  <div className="flex gap-2">
                    {/* 要求訂正 */}
                    <Button
                      onClick={handleRequestRevision}
                      disabled={submitting || !submission}
                      variant={
                        submission?.status === "RETURNED"
                          ? "default"
                          : "outline"
                      }
                      className={`flex-1 ${
                        submission?.status === "RETURNED"
                          ? "bg-orange-600 hover:bg-orange-700 text-white"
                          : "border-orange-600 text-orange-600 hover:bg-orange-50"
                      }`}
                    >
                      <X className="h-4 w-4 mr-2" />
                      要求訂正
                    </Button>

                    {/* 已完成 */}
                    <Button
                      onClick={handleCompleteGrading}
                      disabled={submitting || !submission}
                      variant={
                        submission?.status === "GRADED" ? "default" : "outline"
                      }
                      className={`flex-1 ${
                        submission?.status === "GRADED"
                          ? "bg-green-600 hover:bg-green-700 text-white"
                          : "border-green-600 text-green-600 hover:bg-green-50"
                      }`}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      完成批改
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
